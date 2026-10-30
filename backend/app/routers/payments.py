"""결제 · 처방전 · 약국 API (tech-spec 6. 결제, 처방전 · 약국). 환자만, 자기 진료만.

- K-1  GET  /appointments/{id}/payment                결제 정보 (서버가 계산한 금액, 주문번호)
- K-2  POST /appointments/{id}/payment/demo           데모 결제: 토스 없이 바로 결제 완료 (기본 모드)
- K-3  POST /payments/confirm                         토스 결제 승인 (서버 금액 검증, 중복 요청 안전)
- K-4  POST /payments/fail                            결제 실패·취소 기록
- K-5  GET  /me/payments                              결제 내역
- L-3  GET  /appointments/{id}/prescription           처방전 (결제 후만, 아니면 403 PAYMENT_REQUIRED)
- M-1  GET  /pharmacies?lat=&lng=                     근처 약국 (키가 없으면 샘플)
- M-3  POST /appointments/{id}/pharmacy-order         약국에 처방전 전송 (데모)
- M-5  POST /appointments/{id}/pharmacy-order/advance 데모: 다음 수령 단계로
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.types import utcnow
from app.models import User
from app.schemas.payment import (
    ConfirmRequest, FailRequest, PatientPrescriptionOut, PaymentOut, PharmacyOrderIn, PharmacyOrderOut, PharmacyOut,
)
from app.services import payment_service, pharmacy_client, pharmacy_service

router = APIRouter(tags=["payments"])
patient_only = require_role("patient")


@router.get("/appointments/{appointment_id}/payment", response_model=PaymentOut)
def payment(appointment_id: int, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return payment_service.get_for_appointment(db, user, appointment_id, utcnow())


@router.post("/appointments/{appointment_id}/payment/demo", response_model=PaymentOut)
def demo_pay(appointment_id: int, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return payment_service.demo_pay(db, user, appointment_id, utcnow())


@router.post("/payments/confirm", response_model=PaymentOut)
def confirm(body: ConfirmRequest, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return payment_service.confirm(db, user, body.payment_key, body.order_id, body.amount, utcnow())


@router.post("/payments/fail", response_model=PaymentOut)
def fail(body: FailRequest, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return payment_service.fail(db, user, body.order_id, body.code, body.message)


@router.get("/me/payments", response_model=list[PaymentOut])
def my_payments(user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return payment_service.list_paid(db, user)


@router.get("/appointments/{appointment_id}/prescription", response_model=PatientPrescriptionOut)
def prescription(appointment_id: int, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return pharmacy_service.get_prescription(db, user, appointment_id)


@router.get("/pharmacies", response_model=list[PharmacyOut])
def pharmacies(lat: float = Query(ge=33, le=39), lng: float = Query(ge=124, le=132), _: User = Depends(patient_only)):
    # 국내 좌표 범위만 받는다
    return pharmacy_client.nearby(lat, lng)


@router.post("/appointments/{appointment_id}/pharmacy-order", response_model=PharmacyOrderOut, status_code=201)
def pharmacy_order(appointment_id: int, body: PharmacyOrderIn, user: User = Depends(patient_only),
                   db: Session = Depends(get_db)):
    return pharmacy_service.create_order(db, user, appointment_id, body, utcnow())


@router.post("/appointments/{appointment_id}/pharmacy-order/advance", response_model=PharmacyOrderOut)
def advance(appointment_id: int, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return pharmacy_service.advance(db, user, appointment_id, utcnow())
