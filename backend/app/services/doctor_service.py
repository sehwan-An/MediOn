"""의사 찾기 (H-2, H-5, H-6). 인증 승인된 의사만 공개한다."""

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.categories import CATEGORY_BY_CODE
from app.constants.fees import FEES
from app.core.errors import AppError
from app.models import Appointment, DoctorProfile, DoctorSchedule
from app.schemas.doctor import DaySlots, DoctorDetail, DoctorSummary, FeeOut, ScheduleOut
from app.services import review_service, slot_service


def _schedules_by_doctor(db: Session, doctor_ids: list[int]) -> dict[int, list[DoctorSchedule]]:
    grouped: dict[int, list[DoctorSchedule]] = defaultdict(list)
    if doctor_ids:
        for s in db.scalars(select(DoctorSchedule).where(DoctorSchedule.doctor_id.in_(doctor_ids))):
            grouped[s.doctor_id].append(s)
    return grouped


def booked_slots(db: Session, doctor_ids: list[int], now: datetime) -> dict[int, set[datetime]]:
    """의사별 앞으로 남은 활성 예약 시각 (취소된 예약은 slot_key 가 NULL 이라 빠진다)."""
    grouped: dict[int, set[datetime]] = defaultdict(set)
    if doctor_ids:
        rows = db.execute(select(Appointment.doctor_id, Appointment.slot_key)
                          .where(Appointment.doctor_id.in_(doctor_ids), Appointment.slot_key >= now))
        for doctor_id, slot_key in rows:
            grouped[doctor_id].add(slot_key)
    return grouped


def _summary(profile: DoctorProfile, schedules: list[DoctorSchedule], now: datetime, booked: set[datetime],
             review_stats: tuple[int | None, int] = (None, 0)) -> dict:
    return {
        "id": profile.user_id,
        "name": profile.name,
        "department_code": profile.department_code,
        "hospital_name": profile.hospital_name,
        "next_available_at": slot_service.next_available(schedules, now, booked),
        "revisit_rate": review_stats[0],
        "review_count": review_stats[1],
    }


def list_doctors(db: Session, now: datetime, category: str | None, department: str | None) -> list[DoctorSummary]:
    query = select(DoctorProfile).where(DoctorProfile.verification_status == "approved")
    if category:
        if category not in CATEGORY_BY_CODE:
            raise AppError(404, "NOT_FOUND", "없는 증상 카테고리예요")
        query = query.where(DoctorProfile.department_code.in_(CATEGORY_BY_CODE[category]["departments"]))
    if department:
        query = query.where(DoctorProfile.department_code == department)
    profiles = list(db.scalars(query.order_by(DoctorProfile.user_id)))
    ids = [p.user_id for p in profiles]
    schedules = _schedules_by_doctor(db, ids)
    booked = booked_slots(db, ids, now)
    reviews = review_service.stats(db, ids)
    doctors = [DoctorSummary(**_summary(p, schedules[p.user_id], now, booked[p.user_id], reviews.get(p.user_id, (None, 0))))
               for p in profiles]
    # 기본순: 가장 빨리 예약할 수 있는 의사 먼저, 7일 안에 빈 시간이 없으면 맨 뒤
    return sorted(doctors, key=lambda d: (d.next_available_at is None, d.next_available_at or now))


def _approved_profile(db: Session, doctor_id: int) -> DoctorProfile:
    profile = db.get(DoctorProfile, doctor_id)
    if profile is None or profile.verification_status != "approved":
        raise AppError(404, "NOT_FOUND", "의사를 찾을 수 없어요")
    return profile


def get_doctor(db: Session, doctor_id: int, now: datetime) -> DoctorDetail:
    profile = _approved_profile(db, doctor_id)
    schedules = sorted(_schedules_by_doctor(db, [doctor_id])[doctor_id], key=lambda s: s.weekday)
    return DoctorDetail(
        **_summary(profile, schedules, now, booked_slots(db, [doctor_id], now)[doctor_id],
                   review_service.stats(db, [doctor_id]).get(doctor_id, (None, 0))),
        bio=profile.bio,
        schedules=[ScheduleOut.model_validate(s) for s in schedules],
        fees=[FeeOut(label=label, first_visit=first, return_visit=ret) for label, _, first, ret in FEES],
    )


def get_slots(db: Session, doctor_id: int, day: date, now: datetime) -> DaySlots:
    _approved_profile(db, doctor_id)
    today = slot_service.kst_today(now)
    if not today <= day < today + timedelta(days=slot_service.BOOKING_DAYS):
        raise AppError(400, "INVALID_DATE", "오늘부터 7일 안의 날짜만 예약할 수 있어요")
    schedules = _schedules_by_doctor(db, [doctor_id])[doctor_id]
    slots = slot_service.slots_for_day(schedules, day, now, booked_slots(db, [doctor_id], now)[doctor_id])
    closed = not any(s.weekday == day.weekday() for s in schedules)
    return DaySlots(date=day, closed=closed, slots=slots)
