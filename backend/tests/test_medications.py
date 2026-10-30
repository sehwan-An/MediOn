"""오늘 복용표 테스트 (P-1, P-2)."""

from datetime import timedelta

from app.db.types import utcnow
from app.routers import medications
from tests.test_appointments import book, doctor_id, free_slots, signup  # noqa: F401
from tests.test_consultation import drug_ids  # noqa: F401
from tests.test_payments import PHARMACY, completed_visit, pay, toss  # noqa: F401


def received_visit(client, doctor_id, drug_id):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_id)  # 1정 · 하루 3번 · 3일
    pay(client, patient, aid)
    url = f"/api/appointments/{aid}/pharmacy-order"
    client.post(url, headers=patient, json={"pharmacy": PHARMACY, "receive_method": "pickup"})
    return patient, url


def test_plan_appears_after_receiving_and_check(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, url = received_visit(client, doctor_id, drug_ids[0])
    today = "/api/me/medications/today"
    for _ in range(2):
        client.post(url + "/advance", headers=patient)
    assert client.get(today, headers=patient).json() == []  # 아직 약을 안 받음
    client.post(url + "/advance", headers=patient)  # 수령 완료

    plan = client.get(today, headers=patient).json()[0]
    assert (plan["day"], plan["total_days"]) == (1, 3)
    assert [s["slot"] for s in plan["slots"]] == ["morning", "lunch", "evening"]
    assert plan["slots"][0]["drugs"][0] == {"name": "데모해열정 500mg", "dose": "1정", "instruction": None}

    body = {"prescription_id": plan["prescription_id"], "slot": "morning", "taken": True}
    res = client.post("/api/me/medications/check", headers=patient, json=body)
    assert res.json()[0]["slots"][0]["taken"] is True
    assert client.post("/api/me/medications/check", headers=patient, json=body).status_code == 200  # 두 번 눌러도 그대로
    res = client.post("/api/me/medications/check", headers=patient, json={**body, "taken": False})
    assert res.json()[0]["slots"][0]["taken"] is False
    assert client.post("/api/me/medications/check", headers=patient, json={**body, "slot": "bedtime"}).status_code == 400
    assert client.post("/api/me/medications/check", headers=signup(client, "s@x.com"), json=body).status_code == 404


def test_plan_ends_after_days(client, doctor_id, drug_ids, toss, monkeypatch):  # noqa: F811
    patient, url = received_visit(client, doctor_id, drug_ids[0])
    for _ in range(3):
        client.post(url + "/advance", headers=patient)
    monkeypatch.setattr(medications, "utcnow", lambda: utcnow() + timedelta(days=2))
    assert client.get("/api/me/medications/today", headers=patient).json()[0]["day"] == 3
    monkeypatch.setattr(medications, "utcnow", lambda: utcnow() + timedelta(days=3))
    assert client.get("/api/me/medications/today", headers=patient).json() == []
