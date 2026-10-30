"""의사 진료 콘솔 API (tech-spec 6. 진료). 인증 승인된 의사만, 자기 예약만 (남의 예약은 404).

- J-1  GET  /doctor/appointments?date=2026-10-30   그날 진료 일정 (한국 날짜, 없으면 오늘)
- J-2  GET  /doctor/appointments/{id}              예약 상세 + 이 환자의 이전 진료 + 처방전
- J-3  POST /doctor/appointments/{id}/start        booked → in_progress
- J-4  POST /doctor/appointments/{id}/complete     진료 완료 + 처방전 (한 트랜잭션)
- L-1  GET  /drugs?q=                              약 검색 (시드 데모 약)

TODO
- J-5  POST /doctor/appointments/{id}/cancel (의사 취소)
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_verified_doctor
from app.db.types import utcnow
from app.models import User
from app.schemas.consultation import CompleteRequest, DoctorAppointmentDetail, DoctorAppointmentOut, DrugOut
from app.services import consultation_service
from app.services.slot_service import kst_today

router = APIRouter(tags=["doctor"])


@router.get("/doctor/appointments", response_model=list[DoctorAppointmentOut])
def schedule(date: date | None = None, doctor: User = Depends(require_verified_doctor), db: Session = Depends(get_db)):
    return consultation_service.list_for_day(db, doctor, date or kst_today(utcnow()))


@router.get("/doctor/appointments/{appointment_id}", response_model=DoctorAppointmentDetail)
def detail(appointment_id: int, doctor: User = Depends(require_verified_doctor), db: Session = Depends(get_db)):
    return consultation_service.get_detail(db, doctor, appointment_id)


@router.post("/doctor/appointments/{appointment_id}/start", response_model=DoctorAppointmentDetail)
def start(appointment_id: int, doctor: User = Depends(require_verified_doctor), db: Session = Depends(get_db)):
    return consultation_service.start(db, doctor, appointment_id, utcnow())


@router.post("/doctor/appointments/{appointment_id}/complete", response_model=DoctorAppointmentDetail)
def complete(appointment_id: int, body: CompleteRequest, doctor: User = Depends(require_verified_doctor),
             db: Session = Depends(get_db)):
    return consultation_service.complete(db, doctor, appointment_id, body, utcnow())


@router.get("/drugs", response_model=list[DrugOut])
def drugs(q: str = "", _: User = Depends(require_verified_doctor), db: Session = Depends(get_db)):
    return consultation_service.search_drugs(db, q)
