"""의사 찾기 응답 스키마 (H-1, H-2, H-5, H-6)."""

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    code: str
    name: str
    departments: list[str]


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weekday: int  # 0=월 … 6=일
    start_time: time
    end_time: time
    lunch_start: time | None
    lunch_end: time | None


class FeeOut(BaseModel):
    label: str
    first_visit: int
    return_visit: int


class DoctorSummary(BaseModel):
    id: int
    name: str
    department_code: str
    hospital_name: str
    next_available_at: datetime | None
    # 재진 희망률 % (N-3). 후기가 없으면 None
    revisit_rate: int | None = None
    review_count: int = 0


class DoctorDetail(DoctorSummary):
    bio: str | None
    schedules: list[ScheduleOut]
    fees: list[FeeOut]


class SlotOut(BaseModel):
    start_at: datetime
    label: str  # 한국 시간 "09:30"
    available: bool


class DaySlots(BaseModel):
    date: date
    closed: bool  # 진료 없는 요일
    slots: list[SlotOut]
