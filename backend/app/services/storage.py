"""인증 서류 파일 저장 (A-9). 비공개 저장: 정적 파일로 공개하지 않고, 관리자 API 로만 내려준다.

shortcut: 개발용 로컬 폴더(backend/uploads)에만 저장한다. 배포(10단계) 때 Cloudinary 비공개 업로드를 붙인다
"""

import secrets
from pathlib import Path

from fastapi import UploadFile

from app.core.errors import AppError

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "doctor-docs"
MAX_BYTES = 5 * 1024 * 1024

# 파일 앞부분(매직 넘버)으로 종류를 판단한다. 확장자·Content-Type 은 브라우저가 보낸 값이라 믿지 않는다
SIGNATURES = [
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
    (b"%PDF-", "pdf", "application/pdf"),
]
MEDIA_TYPES = {ext: media for _, ext, media in SIGNATURES} | {"webp": "image/webp"}


def _detect(head: bytes) -> str | None:
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return next((ext for sig, ext, _ in SIGNATURES if head.startswith(sig)), None)


def read_document(upload: UploadFile) -> tuple[bytes, str]:
    """업로드 파일을 검사해서 (내용, 확장자)를 돌려준다. 아직 저장하지 않는다."""
    content = upload.file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise AppError(400, "FILE_TOO_LARGE", "서류 파일은 5MB 이하로 올려주세요")
    ext = _detect(content[:16])
    if ext is None:
        raise AppError(400, "INVALID_FILE", "서류는 JPG, PNG, WEBP, PDF 파일만 올릴 수 있어요")
    return content, ext


def save(content: bytes, ext: str) -> str:
    """저장하고 file_key(추측할 수 없는 파일 이름)를 돌려준다."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    key = f"{secrets.token_hex(16)}.{ext}"
    (UPLOAD_DIR / key).write_bytes(content)
    return key


def delete(key: str) -> None:
    (UPLOAD_DIR / key).unlink(missing_ok=True)


def path_for(key: str) -> tuple[Path, str]:
    """(파일 경로, Content-Type). 파일이 없으면 404."""
    path = UPLOAD_DIR / Path(key).name  # 경로 조작 방지
    if not path.is_file():
        raise AppError(404, "NOT_FOUND", "서류 파일을 찾을 수 없어요")
    return path, MEDIA_TYPES.get(path.suffix.lstrip("."), "application/octet-stream")
