"""비대면 진료비 표 (K-1). 목업 기준 데모 금액이며 실제 수가가 아니다."""

# (나이대 이름, 최소 만 나이, 초진, 재진). 결제(7단계)에서 진료받는 사람 나이로 금액을 고를 때도 이 표를 쓴다.
FEES = [
    ("1세 미만", 0, 1200, 800),
    ("1세 ~ 64세", 1, 6800, 5100),
    ("65세 이상", 65, 4500, 1700),
]


def fee_for(age: int, visit_type: str) -> tuple[str, int]:
    """만 나이·초진/재진 → (나이대 이름, 금액). 나이는 출생연도만 알아서 '올해 - 출생연도'로 계산한다."""
    label, _, first, ret = [row for row in FEES if age >= row[1]][-1]
    return label, first if visit_type == "first" else ret
