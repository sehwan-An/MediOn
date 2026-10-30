"""진료 후기 (N-1~N-3)."""

from sqlalchemy import Integer, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Appointment, DoctorProfile, Payment, Review, User
from app.schemas.review import DoctorReviews, ReviewIn, ReviewOut

TAGS = ("kind", "detailed", "punctual")
LIST_LIMIT = 50


def mask(name: str) -> str:
    """닉네임 가운데를 가린다: 한지우 → 한*우, 민재 → 민*."""
    if len(name) <= 1:
        return "*"
    if len(name) == 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]


def _tags(r: Review) -> list[str]:
    return [t for t in TAGS if getattr(r, f"tag_{t}")]


def create(db: Session, patient: User, appointment_id: int, data: ReviewIn) -> ReviewOut:
    """후기 작성 (N-1). 결제까지 끝난 내 진료에 한 번만."""
    a = db.get(Appointment, appointment_id)
    if a is None or a.patient_id != patient.id:
        raise AppError(404, "NOT_FOUND", "예약을 찾을 수 없어요")
    paid = db.scalar(select(Payment.id).where(Payment.appointment_id == a.id, Payment.status == "paid"))
    if a.status != "completed" or paid is None:
        raise AppError(409, "INVALID_STATUS", "진료와 결제가 끝난 뒤에 후기를 남길 수 있어요")
    review = Review(appointment_id=a.id, patient_id=patient.id, doctor_id=a.doctor_id, wants_revisit=data.wants_revisit,
                    body=data.body, **{f"tag_{t}": t in data.tags for t in TAGS})
    db.add(review)
    try:
        db.commit()
    except IntegrityError as exc:  # 진료 1건에 후기 1개 (유니크 제약으로 최종 판정)
        db.rollback()
        raise AppError(409, "ALREADY_REVIEWED", "이미 후기를 남긴 진료예요") from exc
    db.refresh(review)
    return ReviewOut(id=review.id, author=mask(patient.nickname), wants_revisit=review.wants_revisit,
                     tags=_tags(review), body=review.body, created_at=review.created_at)


def stats(db: Session, doctor_ids: list[int]) -> dict[int, tuple[int | None, int]]:
    """의사별 (재진 희망률 %, 후기 수) (N-3). 후기가 없는 의사는 빠진다."""
    if not doctor_ids:
        return {}
    rows = db.execute(select(Review.doctor_id, func.count(), func.sum(Review.wants_revisit.cast(Integer)))
                      .where(Review.doctor_id.in_(doctor_ids)).group_by(Review.doctor_id))
    return {doctor_id: (round(100 * (yes or 0) / count), count) for doctor_id, count, yes in rows}


def for_doctor(db: Session, doctor_id: int) -> DoctorReviews:
    """의사 상세 후기 탭 (N-2): 재진 희망률, 태그별 인원, 최근 후기."""
    profile = db.get(DoctorProfile, doctor_id)
    if profile is None or profile.verification_status != "approved":
        raise AppError(404, "NOT_FOUND", "의사를 찾을 수 없어요")
    rate, count = stats(db, [doctor_id]).get(doctor_id, (None, 0))
    tag_counts = {t: db.scalar(select(func.count()).where(Review.doctor_id == doctor_id, getattr(Review, f"tag_{t}")))
                  for t in TAGS}
    # shortcut: 최근 50개만. 후기가 많아지면 페이지네이션
    rows = db.execute(select(Review, User.nickname).join(User, User.id == Review.patient_id)
                      .where(Review.doctor_id == doctor_id).order_by(Review.id.desc()).limit(LIST_LIMIT))
    items = [ReviewOut(id=r.id, author=mask(nickname), wants_revisit=r.wants_revisit, tags=_tags(r), body=r.body,
                       created_at=r.created_at) for r, nickname in rows]
    return DoctorReviews(revisit_rate=rate, review_count=count, tag_counts=tag_counts, items=items)
