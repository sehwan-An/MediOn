from datetime import datetime

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class HospitalCache(Base):
    """심평원 API 응답 캐시. 같은 키가 24시간 안이면 재사용한다 (tech-spec 8)."""

    __tablename__ = "hospitals_cache"

    cache_key: Mapped[str] = mapped_column(String(100), primary_key=True)  # dept:05:lat:35.16:lng:126.85
    payload: Mapped[list] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(UTCDateTime())
