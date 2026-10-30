"""진료비 결제 (K-1~K-5, tech-spec 7. 결제 승인).

브라우저가 보낸 금액은 믿지 않는다. 진료가 끝날 때 서버가 계산해 저장한 금액으로만 승인한다.
"""

import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.fees import fee_for
from app.core.errors import AppError
from app.models import Appointment, DoctorProfile, Payment, User
from app.services import toss_client
from app.services.slot_service import KST


def _new_order_id(appointment_id: int) -> str:
    # 토스 orderId 규칙: 6~64자, 영문·숫자·-_= 만, 결제마다 달라야 한다
    return f"medion-apt-{appointment_id}-{secrets.token_hex(4)}"


def ensure_payment(db: Session, appointment: Appointment, now: datetime) -> Payment:
    """진료 완료 때 결제 요청(ready)을 만든다 (J-4 와 같은 트랜잭션, 커밋은 호출한 쪽에서)."""
    payment = db.scalar(select(Payment).where(Payment.appointment_id == appointment.id))
    if payment:
        return payment
    age = now.astimezone(KST).year - appointment.subject_birth_year
    _, amount = fee_for(age, appointment.visit_type)
    doctor = db.get(DoctorProfile, appointment.doctor_id)
    visit = "초진" if appointment.visit_type == "first" else "재진"
    payment = Payment(
        appointment_id=appointment.id, patient_id=appointment.patient_id, order_id=_new_order_id(appointment.id),
        order_name=f"{doctor.name} 의사 비대면 진료 ({visit})", amount=amount, status="ready",
    )
    db.add(payment)
    return payment


def _my_appointment(db: Session, patient: User, appointment_id: int) -> Appointment:
    a = db.get(Appointment, appointment_id)
    if a is None or a.patient_id != patient.id:
        raise AppError(404, "NOT_FOUND", "예약을 찾을 수 없어요")
    return a


def get_for_appointment(db: Session, patient: User, appointment_id: int, now: datetime) -> Payment:
    """결제 화면용 정보 (K-1). 실패했던 결제는 새 주문번호로 다시 결제할 수 있게 준비한다 (K-4)."""
    a = _my_appointment(db, patient, appointment_id)
    if a.status != "completed":
        raise AppError(409, "INVALID_STATUS", "진료가 끝난 뒤에 결제할 수 있어요")
    payment = ensure_payment(db, a, now)  # 결제 기능 전에 완료된 진료도 결제할 수 있게
    if payment.status == "failed":
        payment.status = "ready"
        payment.order_id = _new_order_id(a.id)
    db.commit()
    return payment


def confirm(db: Session, patient: User, payment_key: str, order_id: str, amount: int, now: datetime) -> Payment:
    """결제 승인 (K-3)."""
    payment = db.scalar(select(Payment).where(Payment.order_id == order_id))
    if payment is None or payment.patient_id != patient.id:
        raise AppError(404, "NOT_FOUND", "결제 정보를 찾을 수 없어요")
    if payment.status == "paid":
        if payment.payment_key == payment_key:
            return payment  # 새로고침·중복 요청: 이미 처리된 결과를 그대로 돌려준다
        raise AppError(409, "ALREADY_PAID", "이미 결제가 끝난 진료예요")
    if amount != payment.amount:
        # 주소창의 amount 를 바꿔도 서버에 저장된 금액과 다르면 토스 승인을 아예 부르지 않는다
        raise AppError(400, "AMOUNT_MISMATCH", "결제 금액이 맞지 않아요. 다시 결제해주세요")

    try:
        result = toss_client.confirm(payment_key, order_id, amount)
    except toss_client.TossError as exc:
        db.refresh(payment)
        if payment.status == "paid":  # 동시에 들어온 다른 요청이 먼저 승인했으면 성공으로 본다
            return payment
        payment.status = "failed"
        payment.fail_code, payment.fail_message = exc.code[:60], exc.message[:300]
        db.commit()
        raise AppError(400, "PAYMENT_FAILED", exc.message) from exc

    payment.status = "paid"
    payment.payment_key = payment_key
    payment.method = (result.get("method") or "")[:30] or None
    payment.receipt_url = ((result.get("receipt") or {}).get("url") or "")[:500] or None
    payment.approved_at = now
    payment.fail_code = payment.fail_message = None
    db.commit()
    return payment


def demo_pay(db: Session, patient: User, appointment_id: int, now: datetime) -> Payment:
    """데모 결제 (K-2 기본 모드). 토스 결제창·인증 없이 서버에 저장된 금액으로 바로 결제 완료 처리한다."""
    payment = get_for_appointment(db, patient, appointment_id, now)
    if payment.status == "paid":
        return payment  # 두 번 눌러도 한 번만
    payment.status = "paid"
    payment.method = "데모 결제"
    payment.approved_at = now
    payment.fail_code = payment.fail_message = None
    db.commit()
    return payment


def fail(db: Session, patient: User, order_id: str, code: str, message: str) -> Payment:
    """결제창에서 실패·취소하고 돌아왔을 때 기록 (K-4). 승인 API 는 부르지 않는다."""
    payment = db.scalar(select(Payment).where(Payment.order_id == order_id))
    if payment is None or payment.patient_id != patient.id:
        raise AppError(404, "NOT_FOUND", "결제 정보를 찾을 수 없어요")
    if payment.status != "paid":
        payment.status = "failed"
        payment.fail_code, payment.fail_message = code[:60], message[:300]
        db.commit()
    return payment


def list_paid(db: Session, patient: User) -> list[Payment]:
    return list(db.scalars(select(Payment).where(Payment.patient_id == patient.id, Payment.status == "paid")
                           .order_by(Payment.approved_at.desc())))
