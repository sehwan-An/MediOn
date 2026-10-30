"""의사 진료 콘솔 스키마 (J-1~J-4, L-1, L-2)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DrugOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    maker: str
    form: str


class PrescriptionItemIn(BaseModel):
    drug_id: int
    dose: str = Field(min_length=1, max_length=20)  # "1정"
    times_per_day: int = Field(ge=1, le=6)
    days: int = Field(ge=1, le=90)
    instruction: str | None = Field(default=None, max_length=100)


class PrescriptionIn(BaseModel):
    note: str | None = Field(default=None, max_length=300)
    items: list[PrescriptionItemIn] = Field(min_length=1, max_length=10)


class CompleteRequest(BaseModel):
    summary: str = Field(min_length=1, max_length=1000)
    prescription: PrescriptionIn | None = None  # 처방 없이 완료 가능


class PrescriptionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    drug: DrugOut
    dose: str
    times_per_day: int
    days: int
    instruction: str | None


class PrescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    issued_at: datetime
    note: str | None
    items: list[PrescriptionItemOut]


class DoctorAppointmentOut(BaseModel):
    """의사가 보는 예약. 환자 연락처 등은 주지 않고 진료에 필요한 정보만."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    status: str
    visit_type: str
    start_at: datetime
    end_at: datetime
    subject_name: str
    subject_birth_year: int
    subject_gender: str | None
    symptom_note: str | None
    doctor_summary: str | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_by: str | None
    cancel_reason: str | None


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_at: datetime
    doctor_summary: str | None


class DoctorAppointmentDetail(DoctorAppointmentOut):
    history: list[HistoryItem]  # 이 환자와의 이전 진료 (J-2)
    prescription: PrescriptionOut | None
