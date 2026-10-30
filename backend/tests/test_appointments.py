"""5단계(예약) 테스트: 예약하기·중복 예약 방지·취소·진료 내역·초진/재진 (I-2, I-3, I-7~I-10)."""

from datetime import datetime, time, timedelta

import pytest

from app.core.security import create_access_token
from app.models import Appointment, Department, DoctorProfile, DoctorSchedule, User


def signup(client, email, birth_year=1994):
    body = {"email": email, "password": "medion1234", "nickname": "환자" + email[0], "birth_year": birth_year,
            "agree_terms": True, "agree_privacy": True}
    return {"Authorization": "Bearer " + client.post("/api/auth/signup", json=body).json()["access_token"]}


@pytest.fixture
def doctor_id(session_factory):
    """매일 00:00~23:30 진료하는 의사. 언제 테스트해도 7일 안에 빈 시간이 있다."""
    with session_factory() as db:
        db.add(Department(code="01", name="내과", sort_order=0))
        user = User(email="doc@x.com", password_hash="x", nickname="김도윤", role="doctor")
        db.add(user)
        db.flush()
        db.add(DoctorProfile(user_id=user.id, name="김도윤", department_code="01", hospital_name="가온내과의원",
                             license_number="0", verification_status="approved"))
        for weekday in range(7):
            db.add(DoctorSchedule(doctor_id=user.id, weekday=weekday, start_time=time(0), end_time=time(23, 30)))
        db.commit()
        return user.id


def free_slots(client, doctor_id):
    """내일 날짜의 예약 가능한 슬롯 (오늘은 시각에 따라 남은 슬롯이 없을 수 있어서)."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    days = client.get(f"/api/doctors/{doctor_id}/slots", params={"date": tomorrow}).json()
    return [s["start_at"] for s in days["slots"] if s["available"]]


def book(client, headers, doctor_id, start_at, **extra):
    return client.post("/api/appointments", headers=headers, json={"doctor_id": doctor_id, "start_at": start_at, **extra})


def test_book_success_marks_slot_taken(client, doctor_id):
    patient = signup(client, "a@x.com")
    slot = free_slots(client, doctor_id)[0]
    res = book(client, patient, doctor_id, slot, symptom_note="  목이 아파요  ")
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "booked" and body["visit_type"] == "first"
    assert body["symptom_note"] == "목이 아파요"
    assert body["doctor"]["name"] == "김도윤"
    assert slot not in free_slots(client, doctor_id)


def test_same_slot_twice_is_409(client, doctor_id):
    slot = free_slots(client, doctor_id)[0]
    assert book(client, signup(client, "a@x.com"), doctor_id, slot).status_code == 201
    res = book(client, signup(client, "b@x.com"), doctor_id, slot)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "SLOT_TAKEN"


def test_invalid_slot_times_are_400(client, doctor_id):
    patient = signup(client, "a@x.com")
    slot = datetime.fromisoformat(free_slots(client, doctor_id)[0])
    for bad in [slot + timedelta(minutes=15), datetime.now().astimezone() - timedelta(days=1), slot + timedelta(days=30)]:
        res = book(client, patient, doctor_id, bad.isoformat())
        assert res.status_code == 400, bad
        assert res.json()["error"]["code"] == "INVALID_SLOT"


def test_doctor_cannot_book(client, doctor_id):
    headers = {"Authorization": "Bearer " + create_access_token(doctor_id, "doctor")}
    assert book(client, headers, doctor_id, free_slots(client, doctor_id)[0]).status_code == 403


def test_birth_year_required_then_saved(client, doctor_id):
    patient = signup(client, "a@x.com", birth_year=None)
    slot = free_slots(client, doctor_id)[0]
    res = book(client, patient, doctor_id, slot)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BIRTH_YEAR_REQUIRED"
    res = book(client, patient, doctor_id, slot, birth_year=1961)
    assert res.status_code == 201
    assert res.json()["subject_birth_year"] == 1961
    assert client.get("/api/auth/me", headers=patient).json()["birth_year"] == 1961


def test_cancel_reopens_slot_and_only_once(client, doctor_id):
    a, b = signup(client, "a@x.com"), signup(client, "b@x.com")
    slot = free_slots(client, doctor_id)[0]
    appointment_id = book(client, a, doctor_id, slot).json()["id"]

    # 남의 예약은 보이지도, 취소되지도 않는다
    assert client.get(f"/api/appointments/{appointment_id}", headers=b).status_code == 404
    assert client.post(f"/api/appointments/{appointment_id}/cancel", headers=b, json={"reason": "x"}).status_code == 404

    res = client.post(f"/api/appointments/{appointment_id}/cancel", headers=a, json={"reason": "일정이 바뀌었어요"})
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"
    assert slot in free_slots(client, doctor_id)
    assert book(client, b, doctor_id, slot).status_code == 201  # 취소된 시간은 다른 사람이 예약 가능

    again = client.post(f"/api/appointments/{appointment_id}/cancel", headers=a, json={"reason": "x"})
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "INVALID_STATUS"


def test_tabs(client, doctor_id):
    a = signup(client, "a@x.com")
    slots = free_slots(client, doctor_id)
    keep = book(client, a, doctor_id, slots[0]).json()["id"]
    gone = book(client, a, doctor_id, slots[1]).json()["id"]
    client.post(f"/api/appointments/{gone}/cancel", headers=a, json={"reason": "x"})
    ids = lambda tab: [x["id"] for x in client.get("/api/appointments", headers=a, params={"tab": tab}).json()]
    assert ids("upcoming") == [keep]
    assert ids("cancelled") == [gone]
    assert ids("past") == []


def test_return_visit_after_completed(client, doctor_id, session_factory):
    a = signup(client, "a@x.com")
    slots = free_slots(client, doctor_id)
    first = book(client, a, doctor_id, slots[0]).json()["id"]
    with session_factory() as db:  # 진료 완료는 6단계 기능이라 DB 에서 직접 바꾼다
        db.get(Appointment, first).status = "completed"
        db.commit()
    assert book(client, a, doctor_id, slots[1]).json()["visit_type"] == "return"
