"""6단계(진료 진행·처방전) 테스트: 진료 일정·시작·완료·처방전·초진 7일 제한 (J-1~J-4, L-1, L-2)."""

from datetime import datetime

import pytest

from app.core.security import create_access_token
from app.models import Drug, DoctorProfile, Prescription, User
from app.services.slot_service import KST
from tests.test_appointments import book, doctor_id, free_slots, signup  # noqa: F401  (doctor_id 는 fixture)


@pytest.fixture
def drug_ids(session_factory):
    with session_factory() as db:
        drugs = [Drug(name="데모해열정 500mg", maker="데모제약", form="정"), Drug(name="데모기침시럽", maker="가상약품", form="시럽")]
        db.add_all(drugs)
        db.commit()
        return [d.id for d in drugs]


@pytest.fixture
def setup(client, doctor_id):  # noqa: F811
    patient = signup(client, "p@x.com")
    slot = free_slots(client, doctor_id)[0]
    appointment = book(client, patient, doctor_id, slot, symptom_note="목이 아파요").json()
    doctor = {"Authorization": "Bearer " + create_access_token(doctor_id, "doctor")}
    return {"patient": patient, "doctor": doctor, "id": appointment["id"], "slot": slot}


def post(client, s, action, **json):
    return client.post(f"/api/doctor/appointments/{s['id']}/{action}", headers=s["doctor"], json=json or None)


def rx(drug_id, days):
    return {"note": "식후 30분", "items": [{"drug_id": drug_id, "dose": "1정", "times_per_day": 3, "days": days}]}


def test_schedule_lists_the_day(client, setup):
    day = datetime.fromisoformat(setup["slot"]).astimezone(KST).date()
    res = client.get("/api/doctor/appointments", headers=setup["doctor"], params={"date": day.isoformat()})
    assert res.status_code == 200
    assert [a["id"] for a in res.json()] == [setup["id"]]
    assert res.json()[0]["symptom_note"] == "목이 아파요"


def test_start_then_complete_with_prescription(client, setup, drug_ids):
    assert post(client, setup, "complete", summary="x").status_code == 409  # 시작 전에는 완료 불가
    res = post(client, setup, "start")
    assert res.status_code == 200 and res.json()["status"] == "in_progress"
    assert post(client, setup, "start").status_code == 409

    res = post(client, setup, "complete", summary="  충분히 쉬세요  ", prescription=rx(drug_ids[0], 3))
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "completed" and body["doctor_summary"] == "충분히 쉬세요"
    assert body["prescription"]["code"].startswith("RX-")
    assert body["prescription"]["items"][0]["drug"]["name"] == "데모해열정 500mg"

    mine = client.get(f"/api/appointments/{setup['id']}", headers=setup["patient"]).json()
    assert mine["status"] == "completed" and mine["has_prescription"] is True
    assert [a["id"] for a in client.get("/api/appointments", headers=setup["patient"], params={"tab": "past"}).json()] == [setup["id"]]


def test_complete_without_prescription(client, setup):
    post(client, setup, "start")
    res = post(client, setup, "complete", summary="대면 진료를 권해요")
    assert res.status_code == 200 and res.json()["prescription"] is None


def test_first_visit_over_7_days_saves_nothing(client, setup, drug_ids, session_factory):
    post(client, setup, "start")
    res = post(client, setup, "complete", summary="x", prescription=rx(drug_ids[0], 8))
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "DAYS_LIMIT"
    # 하나의 트랜잭션: 진료 상태도 처방전도 바뀌지 않았다
    assert client.get(f"/api/doctor/appointments/{setup['id']}", headers=setup["doctor"]).json()["status"] == "in_progress"
    with session_factory() as db:
        assert db.query(Prescription).count() == 0


def test_unknown_drug_is_rejected(client, setup):
    post(client, setup, "start")
    assert post(client, setup, "complete", summary="x", prescription=rx(99999, 3)).status_code == 400


def test_other_doctor_and_roles(client, setup, session_factory):
    with session_factory() as db:
        other = User(email="o@x.com", password_hash="x", nickname="다른의사", role="doctor")
        pending = User(email="pd@x.com", password_hash="x", nickname="심사중", role="doctor")
        db.add_all([other, pending])
        db.flush()
        db.add_all([
            DoctorProfile(user_id=other.id, name="다른", department_code="01", hospital_name="병원", license_number="0", verification_status="approved"),
            DoctorProfile(user_id=pending.id, name="심사", department_code="01", hospital_name="병원", license_number="0", verification_status="pending"),
        ])
        db.commit()
        other_id, pending_id = other.id, pending.id
    url = f"/api/doctor/appointments/{setup['id']}"
    as_other = {"Authorization": "Bearer " + create_access_token(other_id, "doctor")}
    as_pending = {"Authorization": "Bearer " + create_access_token(pending_id, "doctor")}
    assert client.get(url, headers=as_other).status_code == 404  # 남의 예약은 숨긴다
    assert client.get(url, headers=as_pending).status_code == 403
    assert client.get(url, headers=setup["patient"]).status_code == 403


def test_history_and_return_visit(client, setup, doctor_id):  # noqa: F811
    post(client, setup, "start")
    post(client, setup, "complete", summary="첫 진료 요약")
    second = book(client, setup["patient"], doctor_id, free_slots(client, doctor_id)[0]).json()
    assert second["visit_type"] == "return"
    detail = client.get(f"/api/doctor/appointments/{second['id']}", headers=setup["doctor"]).json()
    assert [h["doctor_summary"] for h in detail["history"]] == ["첫 진료 요약"]


def test_drug_search(client, setup, drug_ids):
    res = client.get("/api/drugs", headers=setup["doctor"], params={"q": "기침"})
    assert [d["name"] for d in res.json()] == ["데모기침시럽"]
    assert client.get("/api/drugs", headers=setup["patient"], params={"q": "기침"}).status_code == 403
