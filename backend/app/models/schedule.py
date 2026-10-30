from datetime import time

from sqlalchemy import ForeignKey, SmallInteger, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DoctorSchedule(Base):
    """의사 요일별 진료 시간 (I-1). 시간은 한국 시간 기준 벽시계 값이다."""

    __tablename__ = "doctor_schedules"
    __table_args__ = (UniqueConstraint("doctor_id", "weekday", name="uq_doctor_schedules_doctor_weekday"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(SmallInteger)  # 0=월 … 6=일
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    lunch_start: Mapped[time | None] = mapped_column(Time)
    lunch_end: Mapped[time | None] = mapped_column(Time)
