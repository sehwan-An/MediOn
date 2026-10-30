from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_status_created", "status", "created_at"),
        Index("ix_questions_department_created", "department_code", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    department_code: Mapped[str | None] = mapped_column(ForeignKey("departments.code"))  # None = 잘 모르겠어요
    title: Mapped[str] = mapped_column(String(100))
    body: Mapped[str] = mapped_column(Text)
    body_part: Mapped[str | None] = mapped_column(String(30))
    duration: Mapped[str] = mapped_column(String(10))  # today | 1-2w | 1m | longer
    visibility: Mapped[str] = mapped_column(String(10), default="public")  # public | private
    status: Mapped[str] = mapped_column(String(10), default="waiting")  # waiting | answered
    answer_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), onupdate=func.now()
    )

    images: Mapped[list["QuestionImage"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", order_by="QuestionImage.sort_order"
    )


class QuestionImage(Base):
    __tablename__ = "question_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)

    question: Mapped[Question] = relationship(back_populates="images")
