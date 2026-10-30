from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class Notification(Base):
    """알림 (F-1, F-2). 누르면 appointment_id 의 예약 상세로 이동한다. 같은 트랜잭션에서 notification_service.notify 로 만든다."""

    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read", "user_id", "is_read"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # appointment_booked | appointment_cancelled | consultation_started | payment_requested | pharmacy_status
    # | doctor_approved | doctor_rejected | [2차] answer_arrived
    type: Mapped[str] = mapped_column(String(30))
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"))
    question_id: Mapped[int | None] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    message: Mapped[str] = mapped_column(String(200))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
