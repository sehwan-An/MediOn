"""예약 API (tech-spec 6. 예약). 환자만.

- I-2, I-3  POST /appointments                예약하기. 같은 시간 선점 시 409 SLOT_TAKEN
- I-7       GET  /appointments?tab=upcoming|past|cancelled
- I-8       GET  /appointments/{id}
- I-9       POST /appointments/{id}/cancel     { reason }
- N-1       POST /appointments/{id}/review     후기 (결제까지 끝난 진료, 1회)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.types import utcnow
from app.models import User
from app.schemas.appointment import AppointmentOut, BookRequest, CancelRequest, Tab
from app.schemas.review import ReviewIn, ReviewOut
from app.services import appointment_service, review_service

router = APIRouter(prefix="/appointments", tags=["appointments"])
patient_only = require_role("patient")


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book(body: BookRequest, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return appointment_service.book(db, user, body, utcnow())


@router.get("", response_model=list[AppointmentOut])
def list_mine(tab: Tab = "upcoming", user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return appointment_service.list_mine(db, user, tab, utcnow())


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_mine(appointment_id: int, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return appointment_service.get_mine(db, user, appointment_id)


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(appointment_id: int, body: CancelRequest, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return appointment_service.cancel(db, user, appointment_id, body.reason, utcnow())


@router.post("/{appointment_id}/review", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def review(appointment_id: int, body: ReviewIn, user: User = Depends(patient_only), db: Session = Depends(get_db)):
    return review_service.create(db, user, appointment_id, body)
