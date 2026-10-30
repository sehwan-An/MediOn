"""회원가입·로그인 비즈니스 로직 (A-7, A-8, A-9)."""

from datetime import datetime

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Department, DoctorDocument, DoctorProfile, User
from app.schemas.auth import AuthResponse, DoctorSignupRequest, LoginRequest, SignupRequest, UserOut
from app.services import storage

# 없는 이메일로 로그인할 때도 비밀번호 확인과 비슷한 시간이 걸리게 하는 가짜 해시.
# 응답 시간 차이로 "가입된 이메일인지" 알아내는 것을 어렵게 한다.
_DUMMY_HASH = hash_password("medion-dummy-password-0")


def _auth_response(user: User) -> AuthResponse:
    token = create_access_token(user.id, user.role)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


def signup(db: Session, data: SignupRequest) -> AuthResponse:
    """일반 회원가입. 가입하면 바로 로그인된 상태로 토큰을 돌려준다."""
    if not (data.agree_terms and data.agree_privacy):
        raise AppError(400, "AGREEMENT_REQUIRED", "필수 약관에 동의해주세요")

    if db.scalar(select(User.id).where(User.email == data.email)) is not None:
        raise AppError(409, "EMAIL_TAKEN", "이미 가입된 이메일이에요")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        nickname=data.nickname,
        role="patient",
        birth_year=data.birth_year,
        gender=data.gender,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # 같은 이메일로 거의 동시에 가입하면 위 조회를 둘 다 통과할 수 있다. 최종 판정은 DB 유니크 제약.
        db.rollback()
        raise AppError(409, "EMAIL_TAKEN", "이미 가입된 이메일이에요") from exc
    db.refresh(user)
    return _auth_response(user)


def signup_doctor(db: Session, data: DoctorSignupRequest, documents: dict[str, UploadFile | None],
                  now: datetime) -> AuthResponse:
    """의사 회원가입 신청 (A-9). 심사 중(pending)으로 만들고 바로 로그인시킨다 → 심사 중 화면(A-10).

    documents: {"license": 면허증(필수), "specialist": 전문의 자격증, "employment": 재직 증명서}
    """
    if not (data.agree_terms and data.agree_privacy):
        raise AppError(400, "AGREEMENT_REQUIRED", "필수 약관에 동의해주세요")
    if documents.get("license") is None:
        raise AppError(400, "LICENSE_REQUIRED", "의사 면허증을 올려주세요")
    if db.get(Department, data.department_code) is None:
        raise AppError(400, "VALIDATION_ERROR", "전문과를 선택해주세요")
    if db.scalar(select(User.id).where(User.email == data.email)) is not None:
        raise AppError(409, "EMAIL_TAKEN", "이미 가입된 이메일이에요")

    # 파일을 모두 검사한 뒤에 저장한다 (하나라도 잘못되면 아무것도 남기지 않음)
    files = {kind: storage.read_document(f) for kind, f in documents.items() if f is not None}
    keys: list[str] = []
    try:
        user = User(email=data.email, password_hash=hash_password(data.password), nickname=data.name, role="doctor",
                    birth_year=data.birth_year, gender=data.gender)
        db.add(user)
        db.flush()
        db.add(DoctorProfile(user_id=user.id, name=data.name, department_code=data.department_code,
                             hospital_name=data.hospital_name, license_number=data.license_number,
                             verification_status="pending", submitted_at=now))
        for kind, (content, ext) in files.items():
            keys.append(storage.save(content, ext))
            db.add(DoctorDocument(doctor_id=user.id, type=kind, file_key=keys[-1]))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        for key in keys:
            storage.delete(key)
        raise AppError(409, "EMAIL_TAKEN", "이미 가입된 이메일이에요") from exc
    except Exception:
        db.rollback()
        for key in keys:  # DB 에 안 남은 파일은 지운다
            storage.delete(key)
        raise
    db.refresh(user)
    return _auth_response(user)


def login(db: Session, data: LoginRequest) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == data.email))
    # 이메일이 없는지, 비밀번호가 틀렸는지 구분하지 않고 같은 메시지를 준다
    password_ok = verify_password(data.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not password_ok:
        raise AppError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 맞지 않아요")
    return _auth_response(user)
