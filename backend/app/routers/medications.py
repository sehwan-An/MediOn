"""오늘 복용표 API (P-1, P-2). 환자만, 자기 처방만.

- P-1  GET  /me/medications/today     약을 받은 처방전으로 만든 오늘 복용 시간대
- P-2  POST /me/medications/check     { prescription_id, slot, taken } 오늘 시간대 체크/해제 → 오늘 복용표
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.types import utcnow
from app.models import User
from app.schemas.medication import CheckIn, MedicationPlan
from app.services import medication_service

router = APIRouter(prefix="/me/medications", tags=["medications"])
patient_only = require_role("patient")


@router.get("/today", response_model=list[MedicationPlan])
def today(user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return medication_service.today(db, user, utcnow())


@router.post("/check", response_model=list[MedicationPlan])
def check(body: CheckIn, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return medication_service.check(db, user, body.prescription_id, body.slot, body.taken, utcnow())
