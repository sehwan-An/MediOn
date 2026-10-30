"""실제 DB 에서 확인하는 테스트. 개발 DB(MariaDB 11.4)와 배포 DB(MySQL 8) 모두에서 통과해야 한다.

TEST_DATABASE_URL 이 있을 때만 실행된다. 개발용 DB 를 지우지 않도록 반드시 테스트 전용 DB 를 쓴다.

  1) HeidiSQL 에서 medion_test DB 를 utf8mb4 로 만든다
  2) Windows PowerShell:
     $env:TEST_DATABASE_URL="mysql+pymysql://root:비밀번호@localhost:3306/medion_test?charset=utf8mb4"
     pytest
"""

import os
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine_options
from app.models import Answer, Appointment, Department, DoctorProfile, HelpfulVote, HospitalCache, Question, User

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL 이 없어서 MySQL 테스트를 건너뜀")

KST = timezone(timedelta(hours=9))


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(TEST_DATABASE_URL, **engine_options(TEST_DATABASE_URL))
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


def make_user(db: Session, email: str, role: str = "patient") -> User:
    user = User(email=email, password_hash="x", nickname="홍길동", role=role)
    db.add(user)
    db.flush()
    return user


def test_korean_and_emoji_roundtrip(db):
    db.add(Department(code="05", name="정형외과", sort_order=0))
    author = make_user(db, "ko@example.com")
    q = Question(author_id=author.id, department_code="05", title="무릎이 시큰해요 😢", body="계단을 내려갈 때 아파요", duration="1m")
    db.add(q)
    db.commit()
    db.expire_all()
    saved = db.scalar(select(Question).where(Question.id == q.id))
    assert saved.title == "무릎이 시큰해요 😢"
    assert saved.body == "계단을 내려갈 때 아파요"


def test_db_default_time_is_utc(db):
    # MySQL 서버 시간대가 한국(+09:00)이어도 세션 시간대를 UTC 로 고정했으므로 NOW() 가 UTC 여야 한다
    user = make_user(db, "time@example.com")
    db.commit()
    db.expire_all()
    created = db.get(User, user.id).created_at
    assert created.tzinfo == UTC
    assert abs(datetime.now(UTC) - created) < timedelta(minutes=5)


def test_aware_kst_datetime_is_stored_as_utc(db):
    db.merge(Department(code="05", name="정형외과", sort_order=0))
    doctor = make_user(db, "kst@example.com", role="doctor")
    profile = DoctorProfile(
        user_id=doctor.id, name="김도윤", department_code="05", hospital_name="하늘숲정형외과의원",
        license_number="12345", submitted_at=datetime(2026, 10, 30, 9, 0, tzinfo=KST),
    )
    db.add(profile)
    db.commit()
    db.expire_all()
    saved = db.get(DoctorProfile, doctor.id)
    assert saved.submitted_at == datetime(2026, 10, 30, 0, 0, tzinfo=UTC)


def test_one_answer_per_doctor_per_question(db):
    db.merge(Department(code="05", name="정형외과", sort_order=0))
    author = make_user(db, "q@example.com")
    doctor = make_user(db, "d@example.com", role="doctor")
    q = Question(author_id=author.id, title="질문", body="내용", duration="today")
    db.add(q)
    db.flush()
    db.add(Answer(question_id=q.id, doctor_id=doctor.id, body="첫 답변"))
    db.flush()
    db.add(Answer(question_id=q.id, doctor_id=doctor.id, body="두 번째 답변"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_helpful_vote_once_per_user(db):
    author = make_user(db, "v1@example.com")
    doctor = make_user(db, "v2@example.com", role="doctor")
    q = Question(author_id=author.id, title="질문", body="내용", duration="today")
    db.add(q)
    db.flush()
    a = Answer(question_id=q.id, doctor_id=doctor.id, body="답변")
    db.add(a)
    db.flush()
    db.add(HelpfulVote(user_id=author.id, answer_id=a.id))
    db.flush()
    db.add(HelpfulVote(user_id=author.id, answer_id=a.id))
    with pytest.raises(IntegrityError):
        db.flush()


def test_json_payload_roundtrip(db):
    payload = [{"name": "하늘숲정형외과의원", "lat": 35.15, "lng": 126.85, "distance_m": 420}]
    db.add(HospitalCache(cache_key="dept:05:lat:35.15:lng:126.85", payload=payload, fetched_at=datetime.now(UTC)))
    db.commit()
    db.expire_all()
    assert db.get(HospitalCache, "dept:05:lat:35.15:lng:126.85").payload == payload


def test_concurrent_booking_only_one_wins(engine):
    """I-3: 같은 의사·같은 시간을 두 요청이 거의 동시에 저장해도 DB 유니크 제약으로 하나만 성공한다."""
    import threading

    with Session(engine) as db:
        doctor = make_user(db, "race-doc@example.com", role="doctor")
        patients = [make_user(db, f"race{i}@example.com") for i in range(2)]
        db.commit()
        doctor_id, patient_ids = doctor.id, [p.id for p in patients]

    slot = datetime(2026, 11, 2, 1, 0, tzinfo=UTC)
    barrier = threading.Barrier(2)
    results = []

    def try_book(patient_id):
        with Session(engine) as db:
            db.add(Appointment(patient_id=patient_id, doctor_id=doctor_id, subject_name="환자", subject_birth_year=1994,
                               start_at=slot, end_at=slot + timedelta(minutes=30), slot_key=slot,
                               status="booked", visit_type="first"))
            barrier.wait()  # 두 스레드가 같은 순간에 저장
            try:
                db.commit()
                results.append("ok")
            except IntegrityError:
                db.rollback()
                results.append("taken")

    threads = [threading.Thread(target=try_book, args=(pid,)) for pid in patient_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["ok", "taken"]

    # 취소(slot_key=NULL)한 예약은 여러 개여도 된다
    with Session(engine) as db:
        for pid in patient_ids:
            db.add(Appointment(patient_id=pid, doctor_id=doctor_id, subject_name="환자", subject_birth_year=1994,
                               start_at=slot, end_at=slot, slot_key=None, status="cancelled", visit_type="first"))
        db.commit()
