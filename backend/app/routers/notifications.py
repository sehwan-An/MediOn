"""알림 API (tech-spec 6. 알림). 로그인한 모든 역할, 자기 알림만.

- F-2  GET   /notifications                ?unread=true, 최근 50개
- F-1  GET   /notifications/unread-count   알림 배지용 (프론트에서 30초마다 조회)
- F-2  PATCH /notifications/{id}/read      읽음 처리
- F-2  POST  /notifications/read-all       모두 읽음
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.notification import NotificationOut, UnreadCount
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def notifications(unread: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return notification_service.list_mine(db, user, unread)


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return UnreadCount(count=notification_service.unread_count(db, user))


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def read(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return notification_service.mark_read(db, user, notification_id)


@router.post("/read-all", status_code=204)
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    notification_service.mark_all_read(db, user)
