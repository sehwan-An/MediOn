"""관리자 의사 인증 심사 스키마 (A-11)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str  # license | specialist | employment


class DoctorApplication(BaseModel):
    user_id: int
    email: str
    name: str
    department_code: str
    hospital_name: str
    license_number: str
    verification_status: str
    rejected_reason: str | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    documents: list[DocumentBrief]


class ReviewDoctorRequest(BaseModel):
    action: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=200)


VerificationStatus = Literal["pending", "approved", "rejected"]
