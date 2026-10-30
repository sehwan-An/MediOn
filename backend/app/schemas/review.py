"""진료 후기 스키마 (N-1~N-3)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Tag = Literal["kind", "detailed", "punctual"]  # 친절한 진료 · 자세한 설명 · 예약 시간 준수


class ReviewIn(BaseModel):
    wants_revisit: bool
    tags: list[Tag] = Field(default_factory=list, max_length=3)
    body: str | None = Field(default=None, max_length=500)

    @field_validator("body")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class ReviewOut(BaseModel):
    id: int
    author: str  # 가운데를 가린 닉네임 "한*우"
    wants_revisit: bool
    tags: list[Tag]
    body: str | None
    created_at: datetime


class DoctorReviews(BaseModel):
    revisit_rate: int | None  # 재진 희망률 %, 후기가 없으면 None
    review_count: int
    tag_counts: dict[Tag, int]
    items: list[ReviewOut]
