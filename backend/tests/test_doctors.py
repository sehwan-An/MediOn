"""4단계(의사 찾기) 테스트: 슬롯 계산, 의사 목록·상세, 날짜 범위 (H-1, H-2, H-5, H-6, I-1)."""

from datetime import UTC, date, datetime, time

import pytest

from app.models import Department, DoctorProfile, DoctorSchedule, User
from app.services.slot_service import next_available, slots_for_day

# 2026-10-30(금) 11:20 KST = 02:20 UTC
NOW = datetime(2026, 10, 30, 2, 20, tzinfo=UTC)
FRIDAY = date(2026, 10, 30)


def schedule(weekday, start="09:00", end="18:00", lunch=("13:00", "14:00")):
    return DoctorSchedule(
        weekday=weekday, start_time=time.fromisoformat(start), end_time=time.fromisoformat(end),
        lunch_start=time.fromisoformat(lunch[0]) if lunch else None,
        lunch_end=time.fromisoformat(lunch[1]) if lunch else None,
    )


# ---------- 슬롯 계산 (서비스 직접)


def test_slots_skip_lunch_and_mark_past_unavailable():
    slots = slots_for_day([schedule(4)], FRIDAY, NOW)
    labels = [s["label"] for s in slots]
    assert labels[0] == "09:00" and labels[-1] == "17:30"
    assert "13:00" not in labels and "13:30" not in labels  # 점심시간
    assert len(labels) == 16  # 9~18시 18칸 - 점심 2칸
    available = {s["label"]: s["available"] for s in slots}
    assert available["11:00"] is False  # 이미 지난 시간
    assert available["11:30"] is True


def test_slot_start_is_returned_in_utc():
    first = slots_for_day([schedule(4)], FRIDAY, NOW)[0]
    assert first["start_at"] == datetime(2026, 10, 30, 0, 0, tzinfo=UTC)  # 09:00 KST


def test_closed_weekday_has_no_slots():
    assert slots_for_day([schedule(0)], FRIDAY, NOW) == []


def test_next_available_skips_to_next_open_day():
    # 금요일 진료가 이미 끝난 저녁 → 다음 진료일(월) 09:00
    evening = datetime(2026, 10, 30, 10, 0, tzinfo=UTC)  # 19:00 KST
    assert next_available([schedule(0), schedule(4)], evening) == datetime(2026, 11, 2, 0, 0, tzinfo=UTC)


def test_next_available_none_without_schedule():
    assert next_available([], NOW) is None


def test_kst_midnight_boundary():
    # UTC 로는 아직 29일이지만 한국은 30일(금) 00:30. 금요일 시간표를 써야 한다
    just_after_midnight = datetime(2026, 10, 29, 15, 30, tzinfo=UTC)
    first = next_available([schedule(4)], just_after_midnight)
    assert first == datetime(2026, 10, 30, 0, 0, tzinfo=UTC)


# ---------- API


@pytest.fixture
def seeded(session_factory):
    with session_factory() as db:
        db.add_all([Department(code="01", name="내과", sort_order=0), Department(code="14", name="피부과", sort_order=1)])
        ids = {}
        for email, dept, status in [("a@x.com", "01", "approved"), ("b@x.com", "14", "approved"), ("c@x.com", "01", "pending")]:
            user = User(email=email, password_hash="x", nickname=email[0], role="doctor")
            db.add(user)
            db.flush()
            db.add(DoctorProfile(user_id=user.id, name=email[0], department_code=dept, hospital_name="병원",
                                 license_number="0", verification_status=status))
            for weekday in range(7):
                db.add(DoctorSchedule(doctor_id=user.id, weekday=weekday, start_time=time(9), end_time=time(18),
                                      lunch_start=time(13), lunch_end=time(14)))
            ids[email[0]] = user.id
        db.commit()
    return ids


def test_categories(client):
    res = client.get("/api/categories")
    assert res.status_code == 200
    cold = next(c for c in res.json() if c["code"] == "cold")
    assert cold == {"code": "cold", "name": "감기·몸살", "departments": ["01", "23", "13"]}


def test_list_shows_only_approved_doctors_in_category(client, seeded):
    res = client.get("/api/doctors", params={"category": "cold"})
    assert res.status_code == 200
    assert [d["id"] for d in res.json()] == [seeded["a"]]  # 피부과·심사 중 의사 제외
    assert res.json()[0]["next_available_at"] is not None


def test_list_unknown_category_is_404(client, seeded):
    assert client.get("/api/doctors", params={"category": "nope"}).status_code == 404


def test_detail_has_schedules_and_fees(client, seeded):
    body = client.get(f"/api/doctors/{seeded['a']}").json()
    assert len(body["schedules"]) == 7
    assert body["fees"][1] == {"label": "1세 ~ 64세", "first_visit": 6800, "return_visit": 5100}


def test_pending_doctor_detail_is_hidden(client, seeded):
    assert client.get(f"/api/doctors/{seeded['c']}").status_code == 404


def test_slots_endpoint_rejects_dates_outside_7_days(client, seeded):
    res = client.get(f"/api/doctors/{seeded['a']}/slots", params={"date": "2020-01-01"})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_DATE"
