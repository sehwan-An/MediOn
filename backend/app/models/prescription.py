from datetime import datetime

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


class Drug(Base):
    """처방전 작성 때 검색하는 약 목록 (L-1). 모두 가상의 데모 약이다 (scripts/seed.py)."""

    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_code: Mapped[str | None] = mapped_column(String(20))  # 식약처 품목기준코드 (데모 약은 없음)
    name: Mapped[str] = mapped_column(String(100), index=True)
    maker: Mapped[str] = mapped_column(String(60))
    form: Mapped[str] = mapped_column(String(20))  # 정, 캡슐, 시럽, 연고 …


class Prescription(Base):
    """처방전 (L). 진료 1건에 최대 1장."""

    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # RX-20261030-0042
    issued_at: Mapped[datetime] = mapped_column(UTCDateTime())
    note: Mapped[str | None] = mapped_column(String(300))  # 전체 복용 안내

    items: Mapped[list["PrescriptionItem"]] = relationship(order_by="PrescriptionItem.id")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id", ondelete="CASCADE"), index=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"))
    dose: Mapped[str] = mapped_column(String(20))  # 1회 투약량 "1정"
    times_per_day: Mapped[int] = mapped_column(SmallInteger)
    days: Mapped[int] = mapped_column(SmallInteger)  # 초진은 최대 7일 (L-2)
    instruction: Mapped[str | None] = mapped_column(String(100))  # "식후 30분"

    drug: Mapped[Drug] = relationship()
