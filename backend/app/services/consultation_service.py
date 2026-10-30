"""의사 진료 진행 (J-1~J-4, L-1, L-2, tech-spec 7. 진료 완료 — 하나의 트랜잭션).

화상통화는 보류라서 진료는 의사가 상태만 바꾼다: booked → in_progress → completed
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Appointment, Drug, Prescription, PrescriptionItem, User
from app.schemas.consultation import CompleteRequest, DoctorAppointmentDetail, DoctorAppointmentOut, HistoryItem, PrescriptionOut
from app.services.notification_service import notify
from app.services.payment_service import ensure_payment
from app.services.slot_service import KST

FIRST_VISIT_MAX_DAYS = 7  # 초진 처방 최대 일수 (L-2, 제도 세부 기준 확정 시 다시 확인)


def list_for_day(db: Session, doctor: User, day: date) -> list[DoctorAppointmentOut]:
    """그날(한국 날짜)의 내 예약, 시간순 (J-1). 취소된 예약도 보여준다."""
    start = datetime.combine(day, time(0), KST)
    rows = db.scalars(select(Appointment).where(
        Appointment.doctor_id == doctor.id, Appointment.start_at >= start, Appointment.start_at < start + timedelta(days=1),
    ).order_by(Appointment.start_at, Appointment.id))
    return [DoctorAppointmentOut.model_validate(a) for a in rows]


def _mine(db: Session, doctor: User, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or appointment.doctor_id != doctor.id:
        raise AppError(404, "NOT_FOUND", "예약을 찾을 수 없어요")
    return appointment


def _prescription(db: Session, appointment_id: int) -> Prescription | None:
    return db.scalar(select(Prescription).where(Prescription.appointment_id == appointment_id))


def get_detail(db: Session, doctor: User, appointment_id: int) -> DoctorAppointmentDetail:
    a = _mine(db, doctor, appointment_id)
    history = db.scalars(select(Appointment).where(
        Appointment.doctor_id == doctor.id, Appointment.patient_id == a.patient_id,
        Appointment.status == "completed", Appointment.id != a.id,
    ).order_by(Appointment.start_at.desc()))
    prescription = _prescription(db, a.id)
    return DoctorAppointmentDetail(
        **DoctorAppointmentOut.model_validate(a).model_dump(),
        history=[HistoryItem.model_validate(h) for h in history],
        prescription=PrescriptionOut.model_validate(prescription) if prescription else None,
    )


def start(db: Session, doctor: User, appointment_id: int, now: datetime) -> DoctorAppointmentDetail:
    """진료 시작 (J-3). 데모라서 예약 시간 전에도 시작할 수 있다."""
    a = _mine(db, doctor, appointment_id)
    if a.status != "booked":
        raise AppError(409, "INVALID_STATUS", "예약됨 상태에서만 진료를 시작할 수 있어요")
    a.status = "in_progress"
    a.started_at = now
    notify(db, a.patient_id, "consultation_started", f"{doctor.doctor_profile.name} 의사가 진료를 시작했어요", a)
    db.commit()
    return get_detail(db, doctor, appointment_id)


def complete(db: Session, doctor: User, appointment_id: int, data: CompleteRequest, now: datetime) -> DoctorAppointmentDetail:
    """진료 완료 (J-4) = 상태 변경 + 진료 요약 + 처방전 + 결제 요청 + 알림을 한 번에 커밋. 하나라도 실패하면 아무것도 저장하지 않는다."""
    a = _mine(db, doctor, appointment_id)
    if a.status != "in_progress":
        raise AppError(409, "INVALID_STATUS", "진료 중인 예약만 완료할 수 있어요")

    if data.prescription:
        items = data.prescription.items
        if a.visit_type == "first" and any(i.days > FIRST_VISIT_MAX_DAYS for i in items):
            raise AppError(400, "DAYS_LIMIT", f"초진은 투약 일수를 최대 {FIRST_VISIT_MAX_DAYS}일까지 입력할 수 있어요")
        drug_ids = {i.drug_id for i in items}
        if len(set(db.scalars(select(Drug.id).where(Drug.id.in_(drug_ids))))) != len(drug_ids):
            raise AppError(400, "VALIDATION_ERROR", "약 목록에 없는 약이 있어요")
        prescription = Prescription(
            appointment_id=a.id, code=f"RX-{now.astimezone(KST):%Y%m%d}-{a.id:04d}", issued_at=now, note=data.prescription.note,
            items=[PrescriptionItem(drug_id=i.drug_id, dose=i.dose, times_per_day=i.times_per_day, days=i.days,
                                    instruction=i.instruction) for i in items],
        )
        db.add(prescription)

    a.status = "completed"
    a.doctor_summary = data.summary.strip()
    a.completed_at = now
    payment = ensure_payment(db, a, now)
    notify(db, a.patient_id, "payment_requested", f"진료가 끝났어요. 진료비 {payment.amount:,}원을 결제해주세요", a)
    db.commit()
    return get_detail(db, doctor, appointment_id)


def search_drugs(db: Session, q: str) -> list[Drug]:
    query = select(Drug).order_by(Drug.name).limit(20)
    if q.strip():
        query = query.where(Drug.name.contains(q.strip(), autoescape=True))
    return list(db.scalars(query))
