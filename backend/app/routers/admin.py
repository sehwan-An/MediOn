"""관리자 API: 의사 인증 심사 (tech-spec 6. 관리자). 관리자만.

- A-11  GET   /admin/doctors?status=pending              인증 신청 목록 (pending | approved | rejected)
- A-11  GET   /admin/doctors/{id}/documents/{doc_id}     서류 파일 (공개 URL 없이 이 API 로만, 캐시 금지)
- A-11  PATCH /admin/doctors/{id}                        { action: approve | reject, reason } + 의사에게 알림
"""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.types import utcnow
from app.schemas.admin import DoctorApplication, ReviewDoctorRequest, VerificationStatus
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])


@router.get("/doctors", response_model=list[DoctorApplication])
def applications(status: VerificationStatus = "pending", db: Session = Depends(get_db)):
    return admin_service.list_applications(db, status)


@router.get("/doctors/{doctor_id}/documents/{document_id}")
def document(doctor_id: int, document_id: int, db: Session = Depends(get_db)) -> FileResponse:
    path, media_type = admin_service.document(db, doctor_id, document_id)
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "no-store"},
                        content_disposition_type="inline")


@router.patch("/doctors/{doctor_id}", response_model=DoctorApplication)
def review(doctor_id: int, body: ReviewDoctorRequest, db: Session = Depends(get_db)):
    return admin_service.review(db, doctor_id, body.action, body.reason, utcnow())
