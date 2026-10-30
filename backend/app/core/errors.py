"""공통 에러. 모든 에러 응답은 { "error": { "code", "message" } } 형식 (tech-spec 9)."""


class AppError(Exception):
    """서비스 로직에서 던지는 에러. message 는 사용자에게 그대로 보여줄 한국어 문장."""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


DEFAULT_ERRORS: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "입력값을 확인해주세요"),
    401: ("UNAUTHORIZED", "로그인이 필요해요"),
    403: ("FORBIDDEN", "권한이 없어요"),
    404: ("NOT_FOUND", "찾을 수 없어요"),
    405: ("METHOD_NOT_ALLOWED", "지원하지 않는 요청이에요"),
    409: ("CONFLICT", "이미 처리된 요청이에요"),
    503: ("SERVICE_UNAVAILABLE", "잠시 후 다시 시도해주세요"),
}


def default_error(status_code: int) -> tuple[str, str]:
    return DEFAULT_ERRORS.get(status_code, ("ERROR", "문제가 생겼어요. 잠시 후 다시 시도해주세요"))
