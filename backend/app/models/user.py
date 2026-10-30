from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(30))
    role: Mapped[str] = mapped_column(String(10))  # patient | doctor | admin
    birth_year: Mapped[int | None] = mapped_column(SmallInteger)
    gender: Mapped[str | None] = mapped_column(String(1))  # M | F
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    doctor_profile: Mapped["DoctorProfile | None"] = relationship(back_populates="user", uselist=False)


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    department_code: Mapped[str] = mapped_column(ForeignKey("departments.code"))
    hospital_name: Mapped[str] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text)
    license_number: Mapped[str] = mapped_column(String(20))
    verification_status: Mapped[str] = mapped_column(String(10), default="pending")  # pending | approved | rejected
    rejected_reason: Mapped[str | None] = mapped_column(String(200))
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    user: Mapped[User] = relationship(back_populates="doctor_profile")

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "approved"


class DoctorDocument(Base):
    """의사 인증 서류. file_key 는 비공개 저장소 경로이며 공개 URL로 노출하지 않는다."""

    __tablename__ = "doctor_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(20))  # license | specialist | employment
    file_key: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
