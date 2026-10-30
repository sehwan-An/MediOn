"""1단계(세팅) 확인용 테스트: 앱 실행, 에러 형식, 보안 유틸, 모델 정의."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from app.core.errors import AppError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.base import Base
from app.main import app
from app.models import DoctorProfile

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_not_found_uses_common_error_format():
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    assert res.json() == {"error": {"code": "NOT_FOUND", "message": "찾을 수 없어요"}}


def test_password_hash_roundtrip():
    hashed = hash_password("medion1234")
    assert hashed != "medion1234"
    assert verify_password("medion1234", hashed)
    assert not verify_password("wrong", hashed)


def test_token_roundtrip():
    token = create_access_token(7, "doctor")
    payload = decode_access_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "doctor"


def test_invalid_token_is_401():
    with pytest.raises(AppError) as exc:
        decode_access_token("not-a-token")
    assert exc.value.status_code == 401


def test_models_create_all_tables():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())
    assert {
        "users", "doctor_profiles", "doctor_documents", "departments", "questions", "question_images",
        "answers", "answer_recommended_departments", "helpful_votes", "notifications", "hospitals_cache",
    } <= tables


def test_doctor_is_verified_only_when_approved():
    assert DoctorProfile(verification_status="approved").is_verified
    assert not DoctorProfile(verification_status="pending").is_verified
