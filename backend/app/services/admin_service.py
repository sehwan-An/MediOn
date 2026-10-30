"""의사 인증 심사 (A-11). 서류는 관리자만, 공개 URL 없이 API 로만 내려준다."""

from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import DoctorDocument, DoctorProfile
from app.schemas.admin import DoctorApplication, DocumentBrief
from app.services import storage
from app.services.notification_service import notify


def _application(db: Session, profile: DoctorProfile) -> DoctorApplication:
    docs = db.scalars(select(DoctorDocument).where(DoctorDocument.doctor_id == profile.user_id).order_by(DoctorDocument.id))
    return DoctorApplication(
        user_id=profile.user_id, email=profile.user.email, name=profile.name, department_code=profile.department_code,
        hospital_name=profile.hospital_name, license_number=profile.license_number,
        verification_status=profile.verification_status, rejected_reason=profile.rejected_reason,
        submitted_at=profile.submitted_at, reviewed_at=profile.reviewed_at,
        documents=[DocumentBrief.model_validate(d) for d in docs],
    )


def list_applications(db: Session, status: str) -> list[DoctorApplication]:
    order = DoctorProfile.submitted_at if status == "pending" else DoctorProfile.reviewed_at.desc()  # 오래 기다린 신청 먼저
    profiles = db.scalars(select(DoctorProfile).where(DoctorProfile.verification_status == status).order_by(order))
    return [_application(db, p) for p in profiles]


def document(db: Session, doctor_id: int, document_id: int) -> tuple[Path, str]:
    doc = db.get(DoctorDocument, document_id)
    if doc is None or doc.doctor_id != doctor_id:
        raise AppError(404, "NOT_FOUND", "서류를 찾을 수 없어요")
    return storage.path_for(doc.file_key)


def review(db: Session, doctor_id: int, action: str, reason: str | None, now: datetime) -> DoctorApplication:
    """승인/반려 + 의사에게 알림 (같은 트랜잭션). 심사 중인 신청만 처리한다."""
    profile = db.get(DoctorProfile, doctor_id)
    if profile is None:
        raise AppError(404, "NOT_FOUND", "의사 신청을 찾을 수 없어요")
    if profile.verification_status != "pending":
        raise AppError(409, "INVALID_STATUS", "이미 심사가 끝난 신청이에요")
    reason = (reason or "").strip()
    if action == "reject" and not reason:
        raise AppError(400, "REASON_REQUIRED", "반려 사유를 입력해주세요")

    profile.reviewed_at = now
    if action == "approve":
        profile.verification_status = "approved"
        profile.rejected_reason = None
        notify(db, doctor_id, "doctor_approved", "의사 인증이 승인됐어요. 이제 예약을 받을 수 있어요")
    else:
        profile.verification_status = "rejected"
        profile.rejected_reason = reason
        notify(db, doctor_id, "doctor_rejected", f"의사 인증이 반려됐어요: {reason}")
    db.commit()
    return _application(db, profile)
