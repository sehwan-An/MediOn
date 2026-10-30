from datetime import datetime

from sqlalchemy import ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class Appointment(Base):
    """비대면 진료 예약 (I, tech-spec 4. appointments).

    slot_key: 활성 예약이면 start_at 과 같은 값, 취소되면 NULL.
    (doctor_id, slot_key) 유니크 → 같은 의사·같은 시간에 활성 예약은 하나뿐 (I-3).
    유니크 인덱스는 NULL 을 여러 개 허용하므로 취소된 예약끼리는 겹쳐도 된다.
    """

    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("doctor_id", "slot_key", name="uq_appointments_doctor_slot"),
        Index("ix_appointments_patient_start", "patient_id", "start_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # 진료받는 사람 (예약 시점 값 복사). 가족 예약(I-5)이 생기면 family_member_id 가 추가된다
    subject_name: Mapped[str] = mapped_column(String(30))
    subject_birth_year: Mapped[int] = mapped_column(SmallInteger)
    subject_gender: Mapped[str | None] = mapped_column(String(1))
    start_at: Mapped[datetime] = mapped_column(UTCDateTime())
    end_at: Mapped[datetime] = mapped_column(UTCDateTime())
    slot_key: Mapped[datetime | None] = mapped_column(UTCDateTime())
    status: Mapped[str] = mapped_column(String(12), default="booked")  # booked | in_progress | completed | cancelled
    visit_type: Mapped[str] = mapped_column(String(6))  # first | return
    symptom_note: Mapped[str | None] = mapped_column(String(500))
    doctor_summary: Mapped[str | None] = mapped_column(Text)  # 진료 요약 (환자에게 보이는 안내, J-4)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    cancelled_by: Mapped[str | None] = mapped_column(String(8))  # patient | doctor
    cancel_reason: Mapped[str | None] = mapped_column(String(200))
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
