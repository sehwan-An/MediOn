"""예약 요청/응답 스키마 (I-2, I-7~I-10)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookRequest(BaseModel):
    doctor_id: int
    start_at: datetime
    symptom_note: str | None = Field(default=None, max_length=500)
    # 회원가입 때 출생연도를 안 넣은 환자만 보낸다. 진료비 계산(나이대)에 필요해서 함께 저장한다
    birth_year: int | None = None

    @field_validator("start_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("예약 시간을 확인해주세요")
        return value

    @field_validator("symptom_note")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @field_validator("birth_year")
    @classmethod
    def check_birth_year(cls, value: int | None) -> int | None:
        if value is not None and not 1900 <= value <= date.today().year:
            raise ValueError("출생연도를 확인해주세요")
        return value


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=200)


class DoctorBrief(BaseModel):
    id: int
    name: str
    department_code: str
    hospital_name: str


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str  # booked | in_progress | completed | cancelled
    visit_type: str  # first | return
    start_at: datetime
    end_at: datetime
    subject_name: str
    subject_birth_year: int
    subject_gender: str | None
    symptom_note: str | None
    doctor_summary: str | None  # 진료 완료 후 의사가 남긴 안내
    started_at: datetime | None
    completed_at: datetime | None
    has_prescription: bool = False  # 처방전 내용은 결제 후에 본다 (L-3)
    payment_status: str | None = None  # ready | paid | failed (진료 완료 후 생김)
    payment_amount: int | None = None
    pharmacy_order: "PharmacyOrderOut | None" = None
    has_review: bool = False  # 후기 작성 여부 (N-1)
    cancelled_by: str | None
    cancel_reason: str | None
    cancelled_at: datetime | None
    created_at: datetime
    doctor: DoctorBrief


from app.schemas.payment import PharmacyOrderOut  # noqa: E402

AppointmentOut.model_rebuild()

Tab = Literal["upcoming", "past", "cancelled"]
