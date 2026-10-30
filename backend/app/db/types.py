"""MySQL DATETIME 은 시간대 정보를 저장하지 않는다.

규칙: DB 에는 항상 UTC(시간대 없는 값)로 저장하고, 읽을 때는 UTC 시간대를 붙여서 돌려준다.
그래야 API 응답이 "2026-10-30T00:20:00+00:00" 처럼 나가서 브라우저가 한국 시간으로 바르게 바꿔 보여준다.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(UTC)
        return value.replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


def utcnow() -> datetime:
    return datetime.now(UTC)
