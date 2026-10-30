"""2단계(인증과 역할) 테스트: 회원가입·로그인·내 정보·역할 권한 (A-3, A-7, A-8, G-1).

실제 DB 대신 메모리 SQLite(conftest.py)를 써서 PC 의 개발 DB 를 건드리지 않는다.
"""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.deps import get_db, require_role, require_verified_doctor
from app.core.errors import AppError
from app.core.security import create_access_token, hash_password
from app.main import handle_app_error
from app.models import Department, DoctorProfile, User

VALID_SIGNUP = {
    "email": "Jiwoo@Example.com ",
    "password": "medion1234",
    "nickname": "한지우",
    "birth_year": 1994,
    "gender": "F",
    "agree_terms": True,
    "agree_privacy": True,
}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- A-7 회원가입


def test_signup_returns_token_and_patient_user(client):
    res = client.post("/api/auth/signup", json=VALID_SIGNUP)
    assert res.status_code == 201
    body = res.json()
    assert body["access_token"]
    assert body["user"]["email"] == "jiwoo@example.com"  # 공백 제거 + 소문자
    assert body["user"]["role"] == "patient"
    assert body["user"]["doctor_profile"] is None
    assert "password_hash" not in body["user"]


def test_signup_duplicate_email_is_409_even_with_different_case(client):
    client.post("/api/auth/signup", json=VALID_SIGNUP)
    res = client.post("/api/auth/signup", json={**VALID_SIGNUP, "email": "JIWOO@example.com"})
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("password", "short1", "비밀번호는 8자 이상, 영문과 숫자를 섞어주세요"),
        ("password", "onlyletters", "비밀번호는 8자 이상, 영문과 숫자를 섞어주세요"),
        ("email", "not-an-email", "이메일 형식을 확인해주세요"),
        ("nickname", " 한 ", "닉네임은 2~20자로 입력해주세요"),
        ("birth_year", 1800, "출생연도를 확인해주세요"),
    ],
)
def test_signup_validation_shows_korean_message(client, field, value, message):
    res = client.post("/api/auth/signup", json={**VALID_SIGNUP, field: value})
    assert res.status_code == 400
    assert res.json() == {"error": {"code": "VALIDATION_ERROR", "message": message}}


def test_signup_requires_agreements(client):
    res = client.post("/api/auth/signup", json={**VALID_SIGNUP, "agree_privacy": False})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "AGREEMENT_REQUIRED"


def test_signup_cannot_choose_role(client):
    res = client.post("/api/auth/signup", json={**VALID_SIGNUP, "role": "admin"})
    assert res.status_code == 201
    assert res.json()["user"]["role"] == "patient"


# ---------- A-8 로그인


def test_login_success_with_any_email_case(client):
    client.post("/api/auth/signup", json=VALID_SIGNUP)
    res = client.post("/api/auth/login", json={"email": "JIWOO@EXAMPLE.COM", "password": "medion1234"})
    assert res.status_code == 200
    assert res.json()["user"]["nickname"] == "한지우"


@pytest.mark.parametrize("email", ["jiwoo@example.com", "nobody@example.com"])
def test_login_failure_hides_which_part_was_wrong(client, email):
    client.post("/api/auth/signup", json=VALID_SIGNUP)
    res = client.post("/api/auth/login", json={"email": email, "password": "wrong-pass1"})
    assert res.status_code == 401
    assert res.json()["error"] == {"code": "INVALID_CREDENTIALS", "message": "이메일 또는 비밀번호가 맞지 않아요"}


# ---------- G-1 내 정보


def test_me_requires_login(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_with_bad_token_is_401(client):
    res = client.get("/api/auth/me", headers=auth_header("not-a-token"))
    assert res.status_code == 401


def test_me_returns_signed_up_user(client):
    token = client.post("/api/auth/signup", json=VALID_SIGNUP).json()["access_token"]
    res = client.get("/api/auth/me", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["email"] == "jiwoo@example.com"


def test_me_includes_doctor_verification_status(client, session_factory):
    with session_factory() as db:
        db.add(Department(code="01", name="내과", sort_order=0))
        doctor = User(email="doc@example.com", password_hash=hash_password("medion1234"), nickname="김도윤", role="doctor")
        db.add(doctor)
        db.flush()
        db.add(DoctorProfile(user_id=doctor.id, name="김도윤", department_code="01", hospital_name="가온내과의원", license_number="00000"))
        db.commit()
        doctor_id = doctor.id
    res = client.get("/api/auth/me", headers=auth_header(create_access_token(doctor_id, "doctor")))
    assert res.status_code == 200
    assert res.json()["doctor_profile"]["verification_status"] == "pending"


# ---------- A-3 역할 권한 (실제 API 가 생기기 전이라 테스트용 엔드포인트로 확인)


@pytest.fixture
def guarded_client(session_factory):
    test_app = FastAPI()
    test_app.add_exception_handler(AppError, handle_app_error)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    test_app.dependency_overrides[get_db] = override_get_db

    @test_app.get("/patient-only")
    def patient_only(user: User = Depends(require_role("patient"))):
        return {"id": user.id}

    @test_app.get("/verified-doctor-only")
    def verified_doctor_only(user: User = Depends(require_verified_doctor)):
        return {"id": user.id}

    return TestClient(test_app)


def make_user(session_factory, email, role, status=None):
    with session_factory() as db:
        if status and db.get(Department, "01") is None:
            db.add(Department(code="01", name="내과", sort_order=0))
        user = User(email=email, password_hash="x", nickname="테스트", role=role)
        db.add(user)
        db.flush()
        if status:
            db.add(DoctorProfile(user_id=user.id, name="테스트", department_code="01", hospital_name="병원",
                                 license_number="00000", verification_status=status))
        db.commit()
        return create_access_token(user.id, role)


def test_doctor_cannot_call_patient_api(guarded_client, session_factory):
    token = make_user(session_factory, "d@example.com", "doctor", "approved")
    res = guarded_client.get("/patient-only", headers=auth_header(token))
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_patient_can_call_patient_api(guarded_client, session_factory):
    token = make_user(session_factory, "p@example.com", "patient")
    assert guarded_client.get("/patient-only", headers=auth_header(token)).status_code == 200


@pytest.mark.parametrize(("status", "expected"), [("pending", 403), ("rejected", 403), ("approved", 200)])
def test_only_approved_doctor_passes(guarded_client, session_factory, status, expected):
    token = make_user(session_factory, f"{status}@example.com", "doctor", status)
    res = guarded_client.get("/verified-doctor-only", headers=auth_header(token))
    assert res.status_code == expected
    if expected == 403:
        assert res.json()["error"]["code"] == "DOCTOR_NOT_VERIFIED"
