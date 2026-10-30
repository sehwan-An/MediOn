"""의사 찾기 API (tech-spec 6. 의사 찾기). 로그인 없이 누구나 볼 수 있다.

- H-1  GET /categories                증상 카테고리와 연결 진료과
-      GET /departments               진료과 목록
- H-2  GET /doctors                   ?category=cold 또는 ?department=01
- H-5  GET /doctors/{id}              의사 상세 + 진료 시간표 + 진료비 표
- H-6  GET /doctors/{id}/slots        ?date=2026-10-30 (한국 날짜) 30분 단위 슬롯
- N-2  GET /doctors/{id}/reviews      후기 + 재진 희망률·태그 통계

TODO
- H-3  오늘 진료 가능·재진 희망률순 필터/정렬, H-4 검색
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.categories import CATEGORIES
from app.core.deps import get_db
from app.db.types import utcnow
from app.models import Department
from app.schemas.doctor import CategoryOut, DaySlots, DepartmentOut, DoctorDetail, DoctorSummary
from app.schemas.review import DoctorReviews
from app.services import doctor_service, review_service

router = APIRouter(tags=["doctors"])


@router.get("/categories", response_model=list[CategoryOut])
def categories() -> list[dict]:
    return CATEGORIES


@router.get("/departments", response_model=list[DepartmentOut])
def departments(db: Session = Depends(get_db)) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.sort_order)))


@router.get("/doctors", response_model=list[DoctorSummary])
def doctors(category: str | None = None, department: str | None = None, db: Session = Depends(get_db)):
    return doctor_service.list_doctors(db, utcnow(), category, department)


@router.get("/doctors/{doctor_id}", response_model=DoctorDetail)
def doctor(doctor_id: int, db: Session = Depends(get_db)):
    return doctor_service.get_doctor(db, doctor_id, utcnow())


@router.get("/doctors/{doctor_id}/slots", response_model=DaySlots)
def slots(doctor_id: int, date: date, db: Session = Depends(get_db)):
    return doctor_service.get_slots(db, doctor_id, date, utcnow())


@router.get("/doctors/{doctor_id}/reviews", response_model=DoctorReviews)
def reviews(doctor_id: int, db: Session = Depends(get_db)):
    return review_service.for_doctor(db, doctor_id)
