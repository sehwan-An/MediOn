from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Department(Base):
    """진료과. code 는 심평원 진료과목 코드와 같은 값을 쓴다."""

    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
