"""질문·답변 스키마 (B, C, D)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.appointment import DoctorBrief

Duration = Literal["today", "1-2w", "1m", "longer"]  # 오늘 · 1~2주 · 한 달쯤 · 그보다 오래
Visibility = Literal["public", "private"]


def _strip(value: str, message: str, max_len: int) -> str:
    value = value.strip()
    if not value:
        raise ValueError(message)
    if len(value) > max_len:
        raise ValueError(f"{max_len:,}자까지 입력할 수 있어요")
    return value


class QuestionIn(BaseModel):
    department_code: str | None = Field(default=None, max_length=2)  # None = 잘 모르겠어요
    title: str
    body: str
    body_part: str | None = Field(default=None, max_length=30)
    duration: Duration
    visibility: Visibility = "public"

    @field_validator("title")
    @classmethod
    def check_title(cls, value: str) -> str:
        return _strip(value, "제목을 입력해주세요", 100)

    @field_validator("body")
    @classmethod
    def check_body(cls, value: str) -> str:
        return _strip(value, "증상 설명을 입력해주세요", 1000)

    @field_validator("body_part")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class QuestionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    department_code: str | None
    visibility: str
    status: str  # waiting | answered
    answer_count: int
    created_at: datetime


class AnswerOut(BaseModel):
    id: int
    doctor: DoctorBrief
    body: str
    recommends_visit: bool
    recommended_departments: list[str]
    helpful_count: int
    helped: bool  # 내가 도움돼요를 눌렀는지
    created_at: datetime


class QuestionDetail(QuestionBrief):
    body_part: str | None
    duration: str
    author_birth_year: int | None  # 화면에는 나이대로만
    author_gender: str | None
    is_mine: bool
    answered_by_me: bool  # 의사: 이미 답변했는지
    answers: list[AnswerOut]


class StatusCounts(BaseModel):
    all: int
    waiting: int
    answered: int


class MyQuestions(BaseModel):
    counts: StatusCounts
    items: list[QuestionBrief]


class AnswerIn(BaseModel):
    body: str
    recommends_visit: bool = False
    recommended_departments: list[str] = Field(default_factory=list, max_length=3)

    @field_validator("body")
    @classmethod
    def check_body(cls, value: str) -> str:
        return _strip(value, "답변을 입력해주세요", 2000)


class HelpfulOut(BaseModel):
    helpful_count: int
    helped: bool


class DoctorAnswerItem(BaseModel):
    answer_id: int
    question_id: int
    question_title: str
    helpful_count: int
    created_at: datetime
