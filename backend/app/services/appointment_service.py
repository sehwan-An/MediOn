"""예약·취소 (I-2, I-3, I-7~I-10, tech-spec 7. 예약하기 — 중복 예약 방지)."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Appointment, DoctorProfile, DoctorSchedule, Payment, PharmacyOrder, Prescription, Review, User
from app.schemas.appointment import AppointmentOut, BookRequest, DoctorBrief, Tab
from app.services import slot_service
from app.services.notification_service import notify, when

def _to_out(db: Session, appointments: list[Appointment]) -> list[AppointmentOut]:
    ids = {a.doctor_id for a in appointments}
    profiles = {p.user_id: p for p in db.scalars(select(DoctorProfile).where(DoctorProfile.user_id.in_(ids)))} if ids else {}
    appointment_ids = [a.id for a in appointments]
    with_rx = set(db.scalars(select(Prescription.appointment_id).where(Prescription.appointment_id.in_(appointment_ids)))) if appointment_ids else set()
    payments = {p.appointment_id: p for p in db.scalars(select(Payment).where(Payment.appointment_id.in_(appointment_ids)))} if appointment_ids else {}
    reviewed = set(db.scalars(select(Review.appointment_id).where(Review.appointment_id.in_(appointment_ids)))) if appointment_ids else set()
    orders = {o.appointment_id: o for o in db.scalars(select(PharmacyOrder).where(PharmacyOrder.appointment_id.in_(appointment_ids)))} if appointment_ids else {}
    out = []
    for a in appointments:
        p = profiles[a.doctor_id]
        doctor = DoctorBrief(id=p.user_id, name=p.name, department_code=p.department_code, hospital_name=p.hospital_name)
        pay = payments.get(a.id)
        out.append(AppointmentOut.model_validate({
            **a.__dict__, "doctor": doctor, "has_prescription": a.id in with_rx,
            "payment_status": pay.status if pay else None, "payment_amount": pay.amount if pay else None,
            "pharmacy_order": orders.get(a.id), "has_review": a.id in reviewed,
        }))
    return out


def book(db: Session, patient: User, data: BookRequest, now: datetime) -> AppointmentOut:
    profile = db.get(DoctorProfile, data.doctor_id)
    if profile is None or profile.verification_status != "approved":
        raise AppError(404, "NOT_FOUND", "의사를 찾을 수 없어요")

    # 1. 실제 진료 시간표 안의 미래 슬롯인지 확인 (예약 여부는 보지 않는다 → 최종 판정은 아래 DB 유니크 제약)
    start = data.start_at
    schedules = list(db.scalars(select(DoctorSchedule).where(DoctorSchedule.doctor_id == data.doctor_id)))
    today = slot_service.kst_today(now)
    day = slot_service.kst_today(start)
    if not today <= day < today + timedelta(days=slot_service.BOOKING_DAYS):
        raise AppError(400, "INVALID_SLOT", "예약할 수 없는 시간이에요. 다른 시간을 선택해주세요")
    valid = {s["start_at"] for s in slot_service.slots_for_day(schedules, day, now) if s["available"]}
    if start not in valid:
        raise AppError(400, "INVALID_SLOT", "예약할 수 없는 시간이에요. 다른 시간을 선택해주세요")

    # 2. 진료받는 사람: 지금은 본인만 (가족 예약 I-5 는 이후)
    if patient.birth_year is None:
        if data.birth_year is None:
            raise AppError(400, "BIRTH_YEAR_REQUIRED", "진료비 계산을 위해 출생연도를 입력해주세요")
        patient.birth_year = data.birth_year

    # 3. 초진·재진 (I-10): 같은 의사에게 끝난 진료가 있으면 재진
    has_completed = db.scalar(select(Appointment.id).where(
        Appointment.patient_id == patient.id, Appointment.doctor_id == data.doctor_id, Appointment.status == "completed",
    ).limit(1))

    appointment = Appointment(
        patient_id=patient.id, doctor_id=data.doctor_id,
        subject_name=patient.nickname, subject_birth_year=patient.birth_year, subject_gender=patient.gender,
        start_at=start, end_at=start + timedelta(minutes=slot_service.SLOT_MINUTES), slot_key=start,
        status="booked", visit_type="return" if has_completed else "first", symptom_note=data.symptom_note,
    )
    db.add(appointment)
    try:
        db.flush()  # 알림에 예약 번호가 필요하다. 중복 슬롯이면 여기서 IntegrityError
        notify(db, data.doctor_id, "appointment_booked", f"새 예약: {appointment.subject_name}님 {when(start)}", appointment)
        db.commit()
    except IntegrityError as exc:
        # 4. 같은 슬롯을 두 사람이 동시에 예약하면 (doctor_id, slot_key) 유니크 위반으로 한 명만 성공 (I-3)
        db.rollback()
        raise AppError(409, "SLOT_TAKEN", "이미 예약된 시간이에요. 다른 시간을 선택해주세요") from exc
    db.refresh(appointment)
    return _to_out(db, [appointment])[0]


def list_mine(db: Session, patient: User, tab: Tab, now: datetime) -> list[AppointmentOut]:
    query = select(Appointment).where(Appointment.patient_id == patient.id)
    if tab == "cancelled":
        query = query.where(Appointment.status == "cancelled").order_by(Appointment.start_at.desc())
    elif tab == "upcoming":
        # 진료 시간이 안 지났거나, 진료 중인 예약
        query = query.where(Appointment.status.in_(["booked", "in_progress"]), Appointment.end_at > now).order_by(Appointment.start_at)
    else:
        query = query.where(Appointment.status != "cancelled", (Appointment.status == "completed") | (Appointment.end_at <= now)).order_by(Appointment.start_at.desc())
    return _to_out(db, list(db.scalars(query)))


def _mine(db: Session, patient: User, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    # 남의 예약은 있다는 것도 알리지 않는다 (404)
    if appointment is None or appointment.patient_id != patient.id:
        raise AppError(404, "NOT_FOUND", "예약을 찾을 수 없어요")
    return appointment


def get_mine(db: Session, patient: User, appointment_id: int) -> AppointmentOut:
    return _to_out(db, [_mine(db, patient, appointment_id)])[0]


def cancel(db: Session, patient: User, appointment_id: int, reason: str, now: datetime) -> AppointmentOut:
    """환자 취소 (I-9). 진료 시작 전, 예약 시간 전까지만. 취소하면 slot_key 를 비워서 그 시간이 다시 열린다."""
    appointment = _mine(db, patient, appointment_id)
    if appointment.status != "booked" or appointment.start_at <= now:
        raise AppError(409, "INVALID_STATUS", "이미 시작했거나 끝난 진료는 취소할 수 없어요")
    appointment.status = "cancelled"
    appointment.slot_key = None
    appointment.cancelled_by = "patient"
    appointment.cancel_reason = reason
    appointment.cancelled_at = now
    notify(db, appointment.doctor_id, "appointment_cancelled",
           f"예약 취소: {appointment.subject_name}님 {when(appointment.start_at)} 예약이 취소됐어요", appointment)
    db.commit()
    db.refresh(appointment)
    return _to_out(db, [appointment])[0]
