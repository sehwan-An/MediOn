"""알림 (F-1, F-2). notify 는 커밋하지 않는다 → 알림을 만든 작업과 같은 트랜잭션으로 저장된다."""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Appointment, Notification, User
from app.services.slot_service import KST

LIST_LIMIT = 50


def when(start_at: datetime) -> str:
    """알림 문구용 한국 시간 '11월 3일 14:30'."""
    t = start_at.astimezone(KST)
    return f"{t.month}월 {t.day}일 {t:%H:%M}"


def notify(db: Session, user_id: int, type_: str, message: str, appointment: Appointment | None = None,
           question_id: int | None = None) -> None:
    db.add(Notification(user_id=user_id, type=type_, message=message[:200], question_id=question_id,
                        appointment_id=appointment.id if appointment else None))


def list_mine(db: Session, user: User, unread: bool) -> list[Notification]:
    # shortcut: 최근 50개만 보여준다. 알림이 많아지면 페이지네이션
    query = select(Notification).where(Notification.user_id == user.id)
    if unread:
        query = query.where(Notification.is_read.is_(False))
    return list(db.scalars(query.order_by(Notification.id.desc()).limit(LIST_LIMIT)))


def unread_count(db: Session, user: User) -> int:
    return db.scalar(select(func.count()).where(Notification.user_id == user.id, Notification.is_read.is_(False)))


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "알림을 찾을 수 없어요")
    n.is_read = True
    db.commit()
    return n


def mark_all_read(db: Session, user: User) -> None:
    db.execute(update(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))
               .values(is_read=True))
    db.commit()
