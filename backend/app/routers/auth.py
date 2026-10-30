"""인증·계정 API (tech-spec 6. 인증 · 마이)

- A-7  POST  /auth/signup          일반 회원가입 (가입 후 바로 로그인)
- A-8  POST  /auth/login           이메일 로그인
- A-9  POST  /auth/signup/doctor   의사 회원가입 신청 (multipart: 폼 + 서류 파일). 심사 중으로 만들고 바로 로그인
- G-1  GET   /auth/me              내 정보 (의사면 프로필·인증 상태 포함)

TODO
- G-3  PATCH /auth/me              프로필 수정
- G-1  GET   /me/summary           마이 활동 요약 (예약 기능이 생기는 5단계 이후)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import User
from app.db.types import utcnow
from app.schemas.auth import AuthResponse, DoctorSignupRequest, LoginRequest, SignupRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return auth_service.signup(db, body)


@router.post("/signup/doctor", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup_doctor(
    body: Annotated[DoctorSignupRequest, Form()],
    license: UploadFile | None = File(None),
    specialist: UploadFile | None = File(None),
    employment: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> AuthResponse:
    documents = {"license": license, "specialist": specialist, "employment": employment}
    return auth_service.signup_doctor(db, body, documents, utcnow())


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return auth_service.login(db, body)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
