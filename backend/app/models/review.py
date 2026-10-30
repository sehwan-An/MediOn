from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class Review(Base):
    """진료 후기 (N). 결제까지 끝난 진료 1건에 1개."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), unique=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    wants_revisit: Mapped[bool] = mapped_column(Boolean)
    tag_kind: Mapped[bool] = mapped_column(Boolean, default=False)  # 친절한 진료
    tag_detailed: Mapped[bool] = mapped_column(Boolean, default=False)  # 자세한 설명
    tag_punctual: Mapped[bool] = mapped_column(Boolean, default=False)  # 예약 시간 준수
    body: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
