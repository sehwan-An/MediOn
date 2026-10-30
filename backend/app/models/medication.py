from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class MedicationCheck(Base):
    """오늘 약 먹었어요 체크 (P-2). 처방전 · 한국 날짜 · 복용 시간대마다 1개."""

    __tablename__ = "medication_checks"
    __table_args__ = (UniqueConstraint("prescription_id", "taken_on", "slot", name="uq_medication_checks_slot"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id", ondelete="CASCADE"))
    taken_on: Mapped[date] = mapped_column(Date)  # 한국 날짜
    slot: Mapped[str] = mapped_column(String(10))  # morning | lunch | evening | bedtime
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
