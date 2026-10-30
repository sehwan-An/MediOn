"""결제·처방전 열람·약국 스키마 (K, L-3, M)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.consultation import PrescriptionOut


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appointment_id: int
    patient_id: int
    order_id: str
    order_name: str
    amount: int  # 서버가 계산한 금액. 결제창도 이 값으로 연다
    status: str  # ready | paid | failed
    method: str | None
    receipt_url: str | None
    approved_at: datetime | None
    fail_message: str | None

    @computed_field
    @property
    def customer_key(self) -> str:
        """토스 결제창에 넘기는 구매자 식별값 (개인정보가 아닌 내부 번호)."""
        return f"medion-user-{self.patient_id}"


class ConfirmRequest(BaseModel):
    payment_key: str = Field(min_length=1, max_length=200)
    order_id: str = Field(min_length=6, max_length=64)
    amount: int = Field(ge=0)


class FailRequest(BaseModel):
    order_id: str = Field(min_length=6, max_length=64)
    code: str = Field(default="UNKNOWN", max_length=60)
    message: str = Field(default="결제를 완료하지 못했어요", max_length=300)


class PharmacyOut(BaseModel):
    ext_id: str
    name: str
    address: str
    tel: str | None
    lat: float
    lng: float
    open_hours: str | None
    distance_m: int
    is_sample: bool  # 공공데이터 키가 없어서 보여주는 가상 약국


class PharmacyIn(BaseModel):
    ext_id: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    address: str = Field(max_length=200)
    tel: str | None = Field(default=None, max_length=20)
    lat: float | None = None
    lng: float | None = None


class PharmacyOrderIn(BaseModel):
    pharmacy: PharmacyIn
    receive_method: Literal["pickup", "delivery"]
    delivery_reason: Literal["remote_area", "long_term_care", "disability", "rare_disease"] | None = None
    delivery_address: str | None = Field(default=None, max_length=200)


class PharmacyOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pharmacy_name: str
    pharmacy_address: str
    pharmacy_tel: str | None
    receive_method: str
    delivery_reason: str | None
    status: str  # sent → preparing → ready(방문) | shipping(배송) → received
    status_changed_at: datetime
    created_at: datetime


class PatientPrescriptionOut(PrescriptionOut):
    """환자가 보는 처방전 (L-3). 결제 후에만 열린다."""

    is_demo: bool = True  # 화면에 "데모 처방전" 워터마크
    patient_name: str
    patient_birth_year: int
    doctor_name: str
    department_code: str
    hospital_name: str
    visit_type: str
