"""3단계 테스트: 의사 회원가입 신청 · 심사 중 403 · 관리자 승인/반려 · 서류 비공개 (A-9~A-11)."""

import pytest

from app.core.security import create_access_token
from app.models import Department, User
from app.services import storage

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
PDF = b"%PDF-1.4\n" + b"\x00" * 32

FORM = {
    "email": "Newdoc@X.com",
    "password": "medion1234",
    "name": "새의사",
    "license_number": "12345",
    "department_code": "01",
    "hospital_name": "새봄가상의원",
    "agree_terms": "true",
    "agree_privacy": "true",
}


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch, session_factory):
    """서류는 임시 폴더에 저장하고, 진료과와 관리자를 만든다."""
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    with session_factory() as db:
        db.add(Department(code="01", name="내과", sort_order=0))
        db.add(User(email="admin@x.com", password_hash="x", nickname="관리자", role="admin"))
        db.commit()
    return tmp_path


@pytest.fixture
def admin(session_factory):
    with session_factory() as db:
        admin_id = db.query(User.id).filter(User.role == "admin").scalar()
    return {"Authorization": "Bearer " + create_access_token(admin_id, "admin")}


def apply(client, files=None, **form):
    files = files if files is not None else {"license": ("license.png", PNG, "image/png")}
    return client.post("/api/auth/signup/doctor", data={**FORM, **form}, files=files)


def test_signup_creates_pending_doctor_and_saves_files(client, upload_dir):
    res = apply(client, files={"license": ("a.png", PNG, "image/png"), "employment": ("b.pdf", PDF, "application/pdf")})
    assert res.status_code == 201
    user = res.json()["user"]
    assert user["role"] == "doctor" and user["email"] == "newdoc@x.com" and user["nickname"] == "새의사"
    assert user["doctor_profile"]["verification_status"] == "pending"
    saved = sorted(p.suffix for p in upload_dir.iterdir())
    assert saved == [".pdf", ".png"]  # 원래 파일 이름은 쓰지 않는다

    # 심사 중에는 진료 API 403 (A-10)
    token = {"Authorization": "Bearer " + res.json()["access_token"]}
    assert client.get("/api/doctor/appointments", headers=token).status_code == 403


@pytest.mark.parametrize(
    ("files", "form", "code"),
    [
        ({}, {}, "LICENSE_REQUIRED"),
        ({"license": ("a.txt", b"hello world", "image/png")}, {}, "INVALID_FILE"),  # Content-Type 을 속여도 내용으로 판단
        ({"license": ("a.png", PNG + b"\x00" * storage.MAX_BYTES, "image/png")}, {}, "FILE_TOO_LARGE"),
        (None, {"agree_privacy": "false"}, "AGREEMENT_REQUIRED"),
        (None, {"license_number": "12-34"}, "VALIDATION_ERROR"),
        (None, {"department_code": "99"}, "VALIDATION_ERROR"),
    ],
)
def test_signup_rejects_bad_input_and_saves_nothing(client, upload_dir, files, form, code):
    res = apply(client, files=files, **form)
    assert res.status_code == 400 and res.json()["error"]["code"] == code
    assert list(upload_dir.iterdir()) == []


def test_duplicate_email_is_409(client, upload_dir):
    apply(client)
    res = apply(client, email="NEWDOC@x.com")
    assert res.status_code == 409 and len(list(upload_dir.iterdir())) == 1


def test_admin_approves_and_doctor_is_notified(client, admin):
    doctor = apply(client).json()
    token = {"Authorization": "Bearer " + doctor["access_token"]}
    doctor_id = doctor["user"]["id"]

    pending = client.get("/api/admin/doctors", headers=admin).json()
    assert [d["user_id"] for d in pending] == [doctor_id] and pending[0]["documents"][0]["type"] == "license"

    res = client.patch(f"/api/admin/doctors/{doctor_id}", headers=admin, json={"action": "approve"})
    assert res.status_code == 200 and res.json()["verification_status"] == "approved"
    assert client.get("/api/auth/me", headers=token).json()["doctor_profile"]["verification_status"] == "approved"
    assert client.get("/api/doctor/appointments", headers=token).status_code == 200
    notes = client.get("/api/notifications", headers=token).json()
    assert notes[0]["type"] == "doctor_approved"
    # 이미 심사한 신청은 다시 처리하지 않는다
    assert client.patch(f"/api/admin/doctors/{doctor_id}", headers=admin, json={"action": "reject", "reason": "x"}).status_code == 409


def test_reject_requires_reason(client, admin):
    doctor_id = apply(client).json()["user"]["id"]
    url = f"/api/admin/doctors/{doctor_id}"
    assert client.patch(url, headers=admin, json={"action": "reject", "reason": " "}).json()["error"]["code"] == "REASON_REQUIRED"
    res = client.patch(url, headers=admin, json={"action": "reject", "reason": "면허증 사진이 흐려요"})
    assert res.json()["verification_status"] == "rejected" and res.json()["rejected_reason"] == "면허증 사진이 흐려요"
    assert client.get("/api/admin/doctors", headers=admin, params={"status": "rejected"}).json()[0]["user_id"] == doctor_id


def test_documents_are_admin_only(client, admin):
    doctor = apply(client).json()
    doctor_id = doctor["user"]["id"]
    doc_id = client.get("/api/admin/doctors", headers=admin).json()[0]["documents"][0]["id"]
    url = f"/api/admin/doctors/{doctor_id}/documents/{doc_id}"

    res = client.get(url, headers=admin)
    assert res.status_code == 200 and res.content == PNG
    assert res.headers["content-type"] == "image/png" and res.headers["cache-control"] == "no-store"
    assert client.get(url).status_code == 401
    assert client.get(url, headers={"Authorization": "Bearer " + doctor["access_token"]}).status_code == 403  # 본인 의사도 불가
    assert client.get(f"/api/admin/doctors/{doctor_id + 1}/documents/{doc_id}", headers=admin).status_code == 404
