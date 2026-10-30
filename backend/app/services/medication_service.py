"""오늘 복용표 (P-1, P-2). 약국에서 약을 받은 날(수령 완료)을 1일째로, 처방의 1일 횟수·투약 일수로 시간대를 만든다.

데모 안내용이다. 실제 복용 시각은 처방전의 복용 안내와 약사 설명을 따른다 (화면에 표시).
"""

from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Appointment, DoctorProfile, MedicationCheck, PharmacyOrder, Prescription, User
from app.schemas.medication import DoseDrug, DoseSlot, MedicationPlan
from app.services.slot_service import KST, kst_today

SLOTS = {"morning": ("아침", "08:00"), "lunch": ("점심", "12:30"), "evening": ("저녁", "18:30"), "bedtime": ("자기 전", "22:00")}
# 1일 횟수 → 시간대. 5번 이상은 네 시간대로 묶는다
SLOTS_BY_TIMES = {1: ["morning"], 2: ["morning", "evening"], 3: ["morning", "lunch", "evening"]}
ALL_SLOTS = list(SLOTS)


def slots_for(times_per_day: int) -> list[str]:
    return SLOTS_BY_TIMES.get(times_per_day, ALL_SLOTS)


def _plans(db: Session, patient: User, today: date) -> list[MedicationPlan]:
    rows = db.execute(
        select(Prescription, PharmacyOrder, Appointment)
        .join(Appointment, Appointment.id == Prescription.appointment_id)
        .join(PharmacyOrder, PharmacyOrder.appointment_id == Appointment.id)
        .where(Appointment.patient_id == patient.id, PharmacyOrder.status == "received")
        .order_by(PharmacyOrder.status_changed_at.desc())
    ).all()
    plans = []
    for rx, order, a in rows:
        day_index = (today - order.status_changed_at.astimezone(KST).date()).days
        active = [i for i in rx.items if 0 <= day_index < i.days]
        if not active:
            continue
        taken = set(db.scalars(select(MedicationCheck.slot).where(
            MedicationCheck.prescription_id == rx.id, MedicationCheck.taken_on == today)))
        slots = []
        for key in ALL_SLOTS:
            drugs = [DoseDrug(name=i.drug.name, dose=i.dose, instruction=i.instruction)
                     for i in active if key in slots_for(i.times_per_day)]
            if drugs:
                label, time = SLOTS[key]
                slots.append(DoseSlot(slot=key, label=label, time=time, taken=key in taken, drugs=drugs))
        plans.append(MedicationPlan(
            prescription_id=rx.id, appointment_id=a.id, doctor_name=db.get(DoctorProfile, a.doctor_id).name,
            note=rx.note, day=day_index + 1, total_days=max(i.days for i in rx.items), slots=slots,
        ))
    return plans


def today(db: Session, patient: User, now: datetime) -> list[MedicationPlan]:
    """오늘 복용표 (P-1). 복용 기간이 끝난 처방은 빠진다."""
    return _plans(db, patient, kst_today(now))


def check(db: Session, patient: User, prescription_id: int, slot: str, taken: bool, now: datetime) -> list[MedicationPlan]:
    """오늘 시간대 체크/해제 (P-2). 오늘 복용표에 있는 시간대만."""
    day = kst_today(now)
    plan = next((p for p in _plans(db, patient, day) if p.prescription_id == prescription_id), None)
    if plan is None:
        raise AppError(404, "NOT_FOUND", "오늘 복용할 약이 아니에요")
    if slot not in {s.slot for s in plan.slots}:
        raise AppError(400, "VALIDATION_ERROR", "오늘 복용 시간이 아니에요")
    if taken:
        db.add(MedicationCheck(patient_id=patient.id, prescription_id=prescription_id, taken_on=day, slot=slot))
    else:
        db.execute(delete(MedicationCheck).where(MedicationCheck.prescription_id == prescription_id,
                                                 MedicationCheck.taken_on == day, MedicationCheck.slot == slot))
    try:
        db.commit()
    except IntegrityError:  # 이미 체크돼 있으면 그대로 둔다
        db.rollback()
    return _plans(db, patient, day)
