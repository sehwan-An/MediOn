"""9단계 테스트: 진료 알림 · 알림 목록/읽음 · 후기 · 재진 희망률 (F-1, F-2, N-1~N-3)."""

from app.core.security import create_access_token
from tests.test_appointments import book, doctor_id, free_slots, signup  # noqa: F401
from tests.test_consultation import drug_ids  # noqa: F401
from tests.test_payments import completed_visit, pay, toss  # noqa: F401


def doctor_headers(doctor_id):  # noqa: F811
    return {"Authorization": "Bearer " + create_access_token(doctor_id, "doctor")}


def types(client, headers):
    return [n["type"] for n in client.get("/api/notifications", headers=headers).json()]


# ---------- 알림 (F)


def test_visit_flow_creates_notifications(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    doctor = doctor_headers(doctor_id)
    assert types(client, doctor) == ["appointment_booked"]
    assert types(client, patient) == ["payment_requested", "consultation_started"]  # 최신순

    pay(client, patient, aid)
    client.post(f"/api/appointments/{aid}/pharmacy-order", headers=patient, json={"pharmacy": {
        "ext_id": "S1", "name": "봄빛약국", "address": "광주", "tel": None, "lat": 35.1, "lng": 126.8}, "receive_method": "pickup"})
    client.post(f"/api/appointments/{aid}/pharmacy-order/advance", headers=patient)
    latest = client.get("/api/notifications", headers=patient).json()[0]
    assert latest["type"] == "pharmacy_status" and latest["message"].startswith("봄빛약국:") and latest["appointment_id"] == aid


def test_cancel_notifies_doctor(client, doctor_id):  # noqa: F811
    patient = signup(client, "p@x.com")
    aid = book(client, patient, doctor_id, free_slots(client, doctor_id)[0]).json()["id"]
    client.post(f"/api/appointments/{aid}/cancel", headers=patient, json={"reason": "일정 변경"})
    assert types(client, doctor_headers(doctor_id)) == ["appointment_cancelled", "appointment_booked"]


def test_read_and_read_all(client, doctor_id):  # noqa: F811
    patient = signup(client, "p@x.com")
    for slot in free_slots(client, doctor_id)[:2]:
        book(client, patient, doctor_id, slot)
    doctor = doctor_headers(doctor_id)
    assert client.get("/api/notifications/unread-count", headers=doctor).json() == {"count": 2}

    first = client.get("/api/notifications", headers=doctor).json()[0]
    assert client.patch(f"/api/notifications/{first['id']}/read", headers=doctor).json()["is_read"] is True
    assert client.get("/api/notifications/unread-count", headers=doctor).json() == {"count": 1}
    assert len(client.get("/api/notifications", headers=doctor, params={"unread": True}).json()) == 1
    # 남의 알림은 404
    assert client.patch(f"/api/notifications/{first['id']}/read", headers=patient).status_code == 404

    assert client.post("/api/notifications/read-all", headers=doctor).status_code == 204
    assert client.get("/api/notifications/unread-count", headers=doctor).json() == {"count": 0}
    assert client.get("/api/notifications/unread-count").status_code == 401


# ---------- 후기 (N)


def test_review_once_after_payment_and_stats(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    url = f"/api/appointments/{aid}/review"
    body = {"wants_revisit": True, "tags": ["kind", "detailed"], "body": " 친절했어요 "}
    assert client.post(url, headers=patient, json=body).status_code == 409  # 결제 전
    pay(client, patient, aid)

    res = client.post(url, headers=patient, json=body)
    assert res.status_code == 201 and res.json()["author"] == "환*p" and res.json()["body"] == "친절했어요"
    assert client.post(url, headers=patient, json=body).json()["error"]["code"] == "ALREADY_REVIEWED"
    assert client.get(f"/api/appointments/{aid}", headers=patient).json()["has_review"] is True
    stranger = signup(client, "s@x.com")
    assert client.post(url, headers=stranger, json=body).status_code == 404

    # 두 번째 환자는 재진 희망 안 함 → 50%
    other, aid2 = completed_visit(client, doctor_id, drug_ids[0], email="q@x.com")
    pay(client, other, aid2, key="pk_2")
    client.post(f"/api/appointments/{aid2}/review", headers=other, json={"wants_revisit": False, "tags": ["kind"]})

    reviews = client.get(f"/api/doctors/{doctor_id}/reviews").json()  # 로그인 없이 볼 수 있다
    assert reviews["revisit_rate"] == 50 and reviews["review_count"] == 2
    assert reviews["tag_counts"] == {"kind": 2, "detailed": 1, "punctual": 0}
    listed = client.get("/api/doctors").json()[0]
    assert (listed["revisit_rate"], listed["review_count"]) == (50, 2)
    assert client.get(f"/api/doctors/{doctor_id}").json()["revisit_rate"] == 50


def test_review_validation(client, doctor_id, drug_ids, toss):  # noqa: F811
    patient, aid = completed_visit(client, doctor_id, drug_ids[0])
    pay(client, patient, aid)
    res = client.post(f"/api/appointments/{aid}/review", headers=patient, json={"wants_revisit": True, "tags": ["fast"]})
    assert res.status_code == 400
    assert client.get(f"/api/doctors/{doctor_id}/reviews").json()["revisit_rate"] is None
