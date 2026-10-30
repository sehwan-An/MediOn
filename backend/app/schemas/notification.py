"""알림 응답 스키마 (F-1, F-2)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    message: str
    appointment_id: int | None
    question_id: int | None  # 답변 도착 알림 (F-3)
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    count: int
