"""인증·계정 요청/응답 스키마 (A-7, A-8, G-1)."""

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 이메일 형식은 간단히만 확인한다 (실제 메일 발송이 없는 데모라서 인증 메일은 생략)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    """앞뒤 공백을 지우고 소문자로 맞춘다. 대소문자만 다른 이메일로 중복 가입하는 것을 막는다."""
    return value.strip().lower()


class SignupRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=64)
    nickname: str
    birth_year: int | None = None
    gender: Literal["M", "F"] | None = None
    agree_terms: bool = False
    agree_privacy: bool = False

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        value = normalize_email(value)
        if not EMAIL_PATTERN.match(value):
            raise ValueError("이메일 형식을 확인해주세요")
        return value

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        has_letter = re.search(r"[A-Za-z]", value)
        has_digit = re.search(r"\d", value)
        if len(value) < 8 or not has_letter or not has_digit:
            raise ValueError("비밀번호는 8자 이상, 영문과 숫자를 섞어주세요")
        return value

    @field_validator("nickname")
    @classmethod
    def check_nickname(cls, value: str) -> str:
        value = value.strip()
        if not 2 <= len(value) <= 20:
            raise ValueError("닉네임은 2~20자로 입력해주세요")
        return value

    @field_validator("birth_year")
    @classmethod
    def check_birth_year(cls, value: int | None) -> int | None:
        if value is not None and not 1900 <= value <= date.today().year:
            raise ValueError("출생연도를 확인해주세요")
        return value


class DoctorSignupRequest(SignupRequest):
    """의사 회원가입 신청 (A-9). multipart 폼으로 받는다 (서류 파일은 라우터에서 따로). 닉네임은 이름으로 정한다."""

    nickname: str | None = None
    name: str
    license_number: str
    department_code: str = Field(max_length=2)
    hospital_name: str

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        value = value.strip()
        if not 2 <= len(value) <= 20:
            raise ValueError("이름은 2~20자로 입력해주세요")
        return value

    @field_validator("license_number")
    @classmethod
    def check_license(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"\d{1,10}", value):
            raise ValueError("면허번호는 숫자로 입력해주세요")
        return value

    @field_validator("hospital_name")
    @classmethod
    def check_hospital(cls, value: str) -> str:
        value = value.strip()
        if not 2 <= len(value) <= 50:
            raise ValueError("소속 병원은 2~50자로 입력해주세요")
        return value


class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=64)

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: str) -> str:
        return normalize_email(value)


class DoctorProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    department_code: str
    hospital_name: str
    bio: str | None
    verification_status: str  # pending | approved | rejected
    rejected_reason: str | None
    submitted_at: datetime | None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nickname: str
    role: str  # patient | doctor | admin
    birth_year: int | None
    gender: str | None
    doctor_profile: DoctorProfileOut | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
