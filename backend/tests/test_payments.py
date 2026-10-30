"""7·8단계 테스트: 결제(서버 금액 검증·중복 승인) · 처방전 열람 · 약국 전송·상태 (K-1~K-5, L-3, M-1~M-5).

토스 승인 API 는 진짜로 부르지 않고 가짜 함수로 바꿔서 확인한다.
"""

import pytest

from app.core.config import settings
from app.core.security import create_access_token
from app.services import toss_client
from tests.test_appointments import book, doctor_id, free_slots, signup  # noqa: F401
from tests.test_consultation import drug_ids  # noqa: F401


@pytest.fixture
def toss(monkeypatch):
    """토스 승인 호출 기록. fail 에 값을 넣으면 그 에러로 거절한다."""
    calls = {"count": 0, "fail": None}

    def fake_confirm(payment_key, order_id, amount):
        calls["count"] += 1
        if calls["fail"]:
            raise toss_client.TossError(*calls["fail"])
        return {"method": "카드", "receipt": {"url": "https://example.com/receipt"}}

    monkeypatch.setattr(toss_client, "confirm", fake_confirm)
    return calls


def completed_visit(client, doctor_id, drug_id, birth_year=1994, email="p@x.com", with_rx=True):  # noqa: F811
    patient = signup(client, email, birth_year)
    appointment_id = book(client, patient, doctor_id, free_slots(client, doctor_id)[0]).json()["id"]
    doctor = {"Authorization": "Bearer " + create_access_token(doctor_id, "doctor")}
    client.post(f"/api/doctor/appointments/{appointment_id}/start", headers=doctor)
    rx = {"items": [{"drug_id": drug_id, "dose": "1정", "times_per_day": 3, "days": 3}]} if with_rx else None
    client.post(f"/api/doctor/appointments/{appointment_id}/complete", headers=doctor, json={"summary": "요약", "prescription": rx})
    return patient, appointment_id


def pay(client, patient, appointment_id, key="pk_1", amount=None):
    info = client.get(f"/api/appointments/{appointment_id}/payment", headers=patient).json()
    body = {"payment_key": key, "order_id": info["order_id"], "amount": info["amount"] if amount is None else amount}
    return client.post("/api/payments/confirm", headers=patient, json=body)


# ---------- 결제 (K)


def test_completion_creates_payment_with_server_amount(client, doctor_id, drug_ids):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    info = client.get(f"/api/appointments/{aid}/payment", headers=patient).json()
    assert info["status"] == "ready" and info["amount"] == 6800  # 1~64세 초진
    assert info["order_name"].endswith("(초진)") and info["customer_key"].startswith("medion-user-")
    assert client.get(f"/api/appointments/{aid}", headers=patient).json()["payment_status"] == "ready"


def test_fee_for_65_plus(client, doctor_id, drug_ids):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0], birth_year=1950)
    assert client.get(f"/api/appointments/{aid}/payment", headers=patient).json()["amount"] == 4500


def test_amount_mismatch_never_calls_toss(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    res = pay(client, patient, aid, amount=100)
    assert res.status_code == 400 and res.json()["error"]["code"] == "AMOUNT_MISMATCH"
    assert toss["count"] == 0


def test_confirm_is_idempotent(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    first = pay(client, patient, aid)
    assert first.status_code == 200 and first.json()["status"] == "paid" and first.json()["method"] == "카드"
    again = client.post("/api/payments/confirm", headers=patient,
                        json={"payment_key": "pk_1", "order_id": first.json()["order_id"], "amount": 6800})
    assert again.status_code == 200 and toss["count"] == 1  # 새로고침해도 한 번만 승인
    other = client.post("/api/payments/confirm", headers=patient,
                        json={"payment_key": "pk_2", "order_id": first.json()["order_id"], "amount": 6800})
    assert other.status_code == 409


def test_demo_pay_without_toss(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    url = f"/api/appointments/{aid}/payment/demo"
    assert client.post(url, headers=signup(client, "s@x.com")).status_code == 404  # 남의 진료
    res = client.post(url, headers=patient)
    assert res.status_code == 200 and res.json()["status"] == "paid" and res.json()["amount"] == 6800
    assert client.post(url, headers=patient).json()["approved_at"] == res.json()["approved_at"]  # 두 번 눌러도 그대로
    assert toss["count"] == 0
    assert client.get(f"/api/appointments/{aid}/prescription", headers=patient).status_code == 200


def test_others_payment_is_hidden(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    order_id = client.get(f"/api/appointments/{aid}/payment", headers=patient).json()["order_id"]
    stranger = signup(client, "s@x.com")
    assert client.get(f"/api/appointments/{aid}/payment", headers=stranger).status_code == 404
    res = client.post("/api/payments/confirm", headers=stranger, json={"payment_key": "pk", "order_id": order_id, "amount": 6800})
    assert res.status_code == 404 and toss["count"] == 0


def test_toss_rejection_then_retry_with_new_order(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    toss["fail"] = ("REJECT_CARD_COMPANY", "카드사에서 거절했어요")
    res = pay(client, patient, aid)
    assert res.status_code == 400 and res.json()["error"]["message"] == "카드사에서 거절했어요"
    first_order = client.get(f"/api/appointments/{aid}/payment", headers=patient).json()
    toss["fail"] = None
    retry = pay(client, patient, aid, key="pk_retry")
    assert retry.status_code == 200 and retry.json()["status"] == "paid"
    assert retry.json()["order_id"] == first_order["order_id"]


def test_fail_endpoint_and_new_order_id(client, doctor_id, drug_ids):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    order_id = client.get(f"/api/appointments/{aid}/payment", headers=patient).json()["order_id"]
    res = client.post("/api/payments/fail", headers=patient, json={"order_id": order_id, "code": "PAY_PROCESS_CANCELED", "message": "취소"})
    assert res.json()["status"] == "failed"
    renewed = client.get(f"/api/appointments/{aid}/payment", headers=patient).json()
    assert renewed["status"] == "ready" and renewed["order_id"] != order_id


def test_missing_toss_key_is_503(client, doctor_id, drug_ids, monkeypatch):  # noqa: F811
    monkeypatch.setattr(settings, "toss_secret_key", "")
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    res = pay(client, patient, aid)
    assert res.status_code == 503 and res.json()["error"]["code"] == "PAYMENT_NOT_CONFIGURED"


def test_payment_before_completion_is_409(client, doctor_id):  # noqa: F811
    patient = signup(client, "p@x.com")
    aid = book(client, patient, doctor_id, free_slots(client, doctor_id)[0]).json()["id"]
    assert client.get(f"/api/appointments/{aid}/payment", headers=patient).status_code == 409


# ---------- 처방전 (L-3)


def test_prescription_locked_until_paid(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    res = client.get(f"/api/appointments/{aid}/prescription", headers=patient)
    assert res.status_code == 403 and res.json()["error"]["code"] == "PAYMENT_REQUIRED"
    pay(client, patient, aid)
    body = client.get(f"/api/appointments/{aid}/prescription", headers=patient).json()
    assert body["is_demo"] is True and body["code"].startswith("RX-")
    assert body["items"][0]["drug"]["name"] == "데모해열정 500mg" and body["doctor_name"] == "김도윤"
    assert [p["status"] for p in client.get("/api/me/payments", headers=patient).json()] == ["paid"]


def test_no_prescription_is_404(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0], with_rx=False)
    pay(client, patient, aid)
    assert client.get(f"/api/appointments/{aid}/prescription", headers=patient).status_code == 404


# ---------- 약국 (M)


def test_pharmacies_fall_back_to_samples_without_key(client, doctor_id, monkeypatch):  # noqa: F811
    monkeypatch.setattr(settings, "data_go_kr_service_key", "")
    patient = signup(client, "p@x.com")
    res = client.get("/api/pharmacies", headers=patient, params={"lat": 35.1601, "lng": 126.8514})
    rows = res.json()
    assert res.status_code == 200 and len(rows) == 5 and all(r["is_sample"] for r in rows)
    assert [r["distance_m"] for r in rows] == sorted(r["distance_m"] for r in rows)  # 거리순
    assert client.get("/api/pharmacies", headers=patient, params={"lat": 0, "lng": 0}).status_code == 400  # 국외 좌표


PHARMACY = {"ext_id": "SAMPLE1", "name": "봄빛약국", "address": "광주 서구", "tel": None, "lat": 35.16, "lng": 126.85}


def test_pickup_order_and_demo_advance(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    url = f"/api/appointments/{aid}/pharmacy-order"
    assert client.post(url, headers=patient, json={"pharmacy": PHARMACY, "receive_method": "pickup"}).status_code == 403  # 결제 전
    pay(client, patient, aid)
    res = client.post(url, headers=patient, json={"pharmacy": PHARMACY, "receive_method": "pickup"})
    assert res.status_code == 201 and res.json()["status"] == "sent"
    assert client.post(url, headers=patient, json={"pharmacy": PHARMACY, "receive_method": "pickup"}).status_code == 409
    statuses = [client.post(url + "/advance", headers=patient).json()["status"] for _ in range(3)]
    assert statuses == ["preparing", "ready", "received"]
    assert client.post(url + "/advance", headers=patient).status_code == 409
    order = client.get(f"/api/appointments/{aid}", headers=patient).json()["pharmacy_order"]
    assert order["status"] == "received" and order["pharmacy_name"] == "봄빛약국"


def test_delivery_requires_reason_and_goes_through_shipping(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    pay(client, patient, aid)
    url = f"/api/appointments/{aid}/pharmacy-order"
    res = client.post(url, headers=patient, json={"pharmacy": PHARMACY, "receive_method": "delivery"})
    assert res.status_code == 400 and res.json()["error"]["code"] == "DELIVERY_REASON_REQUIRED"
    res = client.post(url, headers=patient, json={"pharmacy": PHARMACY, "receive_method": "delivery",
                                                   "delivery_reason": "long_term_care", "delivery_address": "광주 서구 00"})
    assert res.status_code == 201
    assert [client.post(url + "/advance", headers=patient).json()["status"] for _ in range(3)] == ["preparing", "shipping", "received"]
