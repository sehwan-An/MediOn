"""라우터에서 쓰는 의존성: DB 세션, 로그인 사용자, 역할 권한 (tech-spec 5)."""

from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """게스트도 접근 가능한 API용. 토큰이 없으면 None."""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise AppError(401, "INVALID_TOKEN", "다시 로그인해주세요")
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise AppError(401, "UNAUTHORIZED", "로그인이 필요해요")
    return user


def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppError(403, "FORBIDDEN", "권한이 없어요")
        return user

    return checker


def require_verified_doctor(user: User = Depends(require_role("doctor"))) -> User:
    """진료 시작·처방처럼 인증 승인된 의사만 가능한 API용 (A-10)."""
    profile = user.doctor_profile
    if profile is None or profile.verification_status != "approved":
        raise AppError(403, "DOCTOR_NOT_VERIFIED", "인증이 끝난 뒤에 진료할 수 있어요")
    return user
