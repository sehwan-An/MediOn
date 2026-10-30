from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (UniqueConstraint("question_id", "doctor_id", name="uq_answers_question_doctor"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)
    recommends_visit: Mapped[bool] = mapped_column(Boolean, default=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class AnswerRecommendedDepartment(Base):
    __tablename__ = "answer_recommended_departments"

    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.id", ondelete="CASCADE"), primary_key=True)
    department_code: Mapped[str] = mapped_column(String(2), ForeignKey("departments.code"), primary_key=True)


class HelpfulVote(Base):
    """도움돼요. 복합 PK 로 같은 사람이 두 번 누르는 것을 DB 에서 막는다."""

    __tablename__ = "helpful_votes"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
