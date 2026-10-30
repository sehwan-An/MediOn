"""FastAPI 앱 진입점. 실행: uvicorn app.main:app --reload"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.errors import AppError, default_error
from app.routers import (
    admin, answers, appointments, auth, doctor, doctors, hospitals, medications, notifications, payments, questions,
)

app = FastAPI(title="MediON API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message)


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code, message = default_error(exc.status_code)
    return error_response(exc.status_code, code, message)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Pydantic 검증 실패도 공통 형식(400)으로 바꾼다.
    # 스키마에서 ValueError("한국어 문장")로 막은 경우에는 그 문장을 그대로 보여준다.
    message = "입력값을 확인해주세요"
    for error in exc.errors():
        if error.get("type") == "value_error" and error.get("ctx", {}).get("error"):
            message = str(error["ctx"]["error"])
            break
    return error_response(400, "VALIDATION_ERROR", message)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    """시작 화면에서 무료 서버를 깨우는 용도 (A-0)."""
    return {"status": "ok"}


for module in (auth, doctors, appointments, payments, medications, questions, answers, doctor, hospitals, notifications, admin):
    app.include_router(module.router, prefix="/api")
