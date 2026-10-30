"""처방전 열람 · 약국 전송 · 약 수령 상태 (L-3, M-2~M-5). 실제 약국에는 아무것도 전송되지 않는 데모."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Appointment, DoctorProfile, Payment, PharmacyOrder, Prescription, User
from app.schemas.payment import PatientPrescriptionOut, PharmacyOrderIn
from app.schemas.consultation import PrescriptionOut
from app.services.notification_service import notify

# 데모 상태 진행 순서 (M-4). 방문은 수령 대기, 배송은 배송 중을 거친다
NEXT_STATUS = {
    "pickup": {"sent": "preparing", "preparing": "ready", "ready": "received"},
    "delivery": {"sent": "preparing", "preparing": "shipping", "shipping": "received"},
}
STATUS_MESSAGE = {
    "preparing": "약을 조제하고 있어요",
    "ready": "약이 준비됐어요. 약국에 방문해 받아주세요",
    "shipping": "약을 보냈어요",
    "received": "약 수령이 완료됐어요",
}


def _paid_prescription(db: Session, patient: User, appointment_id: int) -> tuple[Appointment, Prescription]:
    a = db.get(Appointment, appointment_id)
    if a is None or a.patient_id != patient.id:
        raise AppError(404, "NOT_FOUND", "예약을 찾을 수 없어요")
    prescription = db.scalar(select(Prescription).where(Prescription.appointment_id == a.id))
    if prescription is None:
        raise AppError(404, "NOT_FOUND", "이 진료에는 처방전이 없어요")
    paid = db.scalar(select(Payment.id).where(Payment.appointment_id == a.id, Payment.status == "paid"))
    if paid is None:
        raise AppError(403, "PAYMENT_REQUIRED", "진료비를 결제하면 처방전을 볼 수 있어요")
    return a, prescription


def get_prescription(db: Session, patient: User, appointment_id: int) -> PatientPrescriptionOut:
    a, prescription = _paid_prescription(db, patient, appointment_id)
    doctor = db.get(DoctorProfile, a.doctor_id)
    return PatientPrescriptionOut(
        **PrescriptionOut.model_validate(prescription).model_dump(),
        patient_name=a.subject_name, patient_birth_year=a.subject_birth_year, visit_type=a.visit_type,
        doctor_name=doctor.name, department_code=doctor.department_code, hospital_name=doctor.hospital_name,
    )


def create_order(db: Session, patient: User, appointment_id: int, data: PharmacyOrderIn, now: datetime) -> PharmacyOrder:
    """약국에 처방전 전송 (M-2, M-3). 한 처방전은 한 약국에만. 배송은 제도상 대상자만 (M-2)."""
    a, _ = _paid_prescription(db, patient, appointment_id)
    if db.scalar(select(PharmacyOrder.id).where(PharmacyOrder.appointment_id == a.id)):
        raise AppError(409, "ALREADY_SENT", "이미 약국에 보낸 처방전이에요")
    if data.receive_method == "delivery" and not (data.delivery_reason and (data.delivery_address or "").strip()):
        raise AppError(400, "DELIVERY_REASON_REQUIRED", "배송은 대상자만 받을 수 있어요. 대상 여부와 배송지를 입력해주세요")
    p = data.pharmacy
    order = PharmacyOrder(
        appointment_id=a.id, pharmacy_ext_id=p.ext_id, pharmacy_name=p.name, pharmacy_address=p.address,
        pharmacy_tel=p.tel, pharmacy_lat=p.lat, pharmacy_lng=p.lng, receive_method=data.receive_method,
        delivery_reason=data.delivery_reason if data.receive_method == "delivery" else None,
        delivery_address=data.delivery_address.strip() if data.receive_method == "delivery" else None,
        status="sent", status_changed_at=now,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def advance(db: Session, patient: User, appointment_id: int, now: datetime) -> PharmacyOrder:
    """데모: 약국 쪽 화면이 없어서 환자 화면 버튼으로 다음 상태로 넘긴다 (M-5). 바뀔 때마다 알림 (F-1)."""
    a, _ = _paid_prescription(db, patient, appointment_id)
    order = db.scalar(select(PharmacyOrder).where(PharmacyOrder.appointment_id == a.id))
    if order is None:
        raise AppError(404, "NOT_FOUND", "아직 약국에 보내지 않았어요")
    next_status = NEXT_STATUS[order.receive_method].get(order.status)
    if next_status is None:
        raise AppError(409, "INVALID_STATUS", "이미 약을 받았어요")
    order.status = next_status
    order.status_changed_at = now
    notify(db, a.patient_id, "pharmacy_status", f"{order.pharmacy_name}: {STATUS_MESSAGE[next_status]}", a)
    db.commit()
    db.refresh(order)
    return order
