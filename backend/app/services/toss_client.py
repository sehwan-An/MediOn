"""토스페이먼츠 결제 승인 API 호출 (K-3, tech-spec 8). 외부 결제 API 는 이 파일에서만 부른다.

테스트 시크릿 키(test_sk_…)만 쓴다. 실제 돈은 나가지 않는다.
"""

import base64

import httpx

from app.core.config import settings
from app.core.errors import AppError

CONFIRM_URL = "https://api.tosspayments.com/v1/payments/confirm"
TIMEOUT_SECONDS = 10


class TossError(Exception):
    """토스가 승인을 거절했을 때. code·message 는 토스가 준 값."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def confirm(payment_key: str, order_id: str, amount: int) -> dict:
    if not settings.toss_secret_key:
        raise AppError(503, "PAYMENT_NOT_CONFIGURED", "결제 테스트 키가 설정되지 않았어요. backend/.env 의 TOSS_SECRET_KEY 를 확인해주세요")
    if settings.toss_secret_key.startswith("live_"):
        raise AppError(503, "PAYMENT_NOT_CONFIGURED", "데모에서는 테스트 키(test_sk_)만 쓸 수 있어요")
    token = base64.b64encode(f"{settings.toss_secret_key}:".encode()).decode()
    try:
        res = httpx.post(
            CONFIRM_URL,
            headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
            json={"paymentKey": payment_key, "orderId": order_id, "amount": amount},
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise AppError(502, "PAYMENT_FAILED", "결제사에 연결하지 못했어요. 잠시 후 다시 시도해주세요") from exc
    body = res.json() if res.content else {}
    if res.status_code != 200:
        raise TossError(body.get("code", "UNKNOWN"), body.get("message", "결제를 승인하지 못했어요"))
    return body
