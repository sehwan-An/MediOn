from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class Payment(Base):
    """진료비 결제 (K). 진료 1건에 결제 1건. 금액은 서버가 계산해서 저장하고, 승인 때 이 금액만 믿는다."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), unique=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[str] = mapped_column(String(64), unique=True)  # 결제 시도마다 새로 만든다 (실패 후 재시도)
    order_name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="ready")  # ready | paid | failed
    payment_key: Mapped[str | None] = mapped_column(String(200), unique=True)
    method: Mapped[str | None] = mapped_column(String(30))
    receipt_url: Mapped[str | None] = mapped_column(String(500))
    fail_code: Mapped[str | None] = mapped_column(String(60))
    fail_message: Mapped[str | None] = mapped_column(String(300))
    approved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class PharmacyOrder(Base):
    """처방전을 보낸 약국과 약 수령 상태 (M). 실제 약국에는 전송되지 않는 데모. 진료 1건에 약국 1곳."""

    __tablename__ = "pharmacy_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), unique=True)
    # 약국 정보는 전송 시점 값 복사 (공공데이터가 바뀌어도 기록 유지)
    pharmacy_ext_id: Mapped[str] = mapped_column(String(20))
    pharmacy_name: Mapped[str] = mapped_column(String(100))
    pharmacy_address: Mapped[str] = mapped_column(String(200))
    pharmacy_tel: Mapped[str | None] = mapped_column(String(20))
    pharmacy_lat: Mapped[float | None] = mapped_column(Numeric(9, 6, asdecimal=False))
    pharmacy_lng: Mapped[float | None] = mapped_column(Numeric(9, 6, asdecimal=False))
    receive_method: Mapped[str] = mapped_column(String(10))  # pickup | delivery
    delivery_reason: Mapped[str | None] = mapped_column(String(20))  # remote_area | long_term_care | disability | rare_disease
    delivery_address: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(10), default="sent")  # sent → preparing → ready|shipping → received
    status_changed_at: Mapped[datetime] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
