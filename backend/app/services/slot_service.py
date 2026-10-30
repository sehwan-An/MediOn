"""예약 가능 시간 계산 (H-6, tech-spec 7. 예약 가능 시간 계산).

진료 시간표는 한국 시간 기준이다. 한국은 서머타임이 없어서 +09:00 고정 시간대로 충분하다 (tzdata 불필요).
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime, time, timedelta, timezone

from app.models import DoctorSchedule

KST = timezone(timedelta(hours=9))
SLOT_MINUTES = 30
BOOKING_DAYS = 7  # 오늘부터 7일까지 예약 가능


def kst_today(now: datetime) -> date:
    return now.astimezone(KST).date()


def _in_lunch(t: time, schedule: DoctorSchedule) -> bool:
    return bool(schedule.lunch_start and schedule.lunch_end and schedule.lunch_start <= t < schedule.lunch_end)


def day_slots(schedule: DoctorSchedule, day: date) -> Iterator[datetime]:
    """그날의 30분 단위 슬롯 시작 시각 (한국 시간). 점심시간은 뺀다."""
    step = timedelta(minutes=SLOT_MINUTES)
    t = datetime.combine(day, schedule.start_time, KST)
    end = datetime.combine(day, schedule.end_time, KST)
    while t + step <= end:
        if not _in_lunch(t.time(), schedule):
            yield t
        t += step


def slots_for_day(
    schedules: list[DoctorSchedule], day: date, now: datetime, booked: set[datetime] = frozenset()
) -> list[dict]:
    """한 날짜의 슬롯 목록. 진료가 없는 요일이면 빈 목록. booked: 이미 예약된 시각(UTC, slot_key)"""
    schedule = next((s for s in schedules if s.weekday == day.weekday()), None)
    if schedule is None:
        return []
    return [
        {"start_at": t.astimezone(UTC), "label": t.strftime("%H:%M"), "available": t > now and t not in booked}
        for t in day_slots(schedule, day)
    ]


def next_available(
    schedules: list[DoctorSchedule], now: datetime, booked: set[datetime] = frozenset()
) -> datetime | None:
    """오늘부터 7일 안에서 가장 빠른 예약 가능 시각 (UTC). 없으면 None."""
    today = kst_today(now)
    for offset in range(BOOKING_DAYS):
        for slot in slots_for_day(schedules, today + timedelta(days=offset), now, booked):
            if slot["available"]:
                return slot["start_at"]
    return None
