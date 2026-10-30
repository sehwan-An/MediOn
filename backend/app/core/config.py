"""환경 변수 설정. 값은 backend/.env 에서 읽는다 (.env.example 참고)."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 1. DB 접속 정보 (HeidiSQL 접속 정보와 같게)
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "medion"
    # 배포용: 접속 주소 한 줄을 통째로 넣으면 위 DB_* 값 대신 이걸 쓴다
    database_url: str = ""

    # 2. 로그인 보안
    jwt_secret: str = "change-me"
    jwt_expire_hours: int = 12

    # 3. 프론트엔드 주소
    cors_origins: str = "http://localhost:5173"

    # 4. 외부 API (.env.example 4·5번)
    toss_secret_key: str = ""  # 토스페이먼츠 테스트 시크릿 키 test_sk_…
    data_go_kr_service_key: str = ""  # 공공데이터포털 일반 인증키(Decoding). 약국(8단계)·병원(2차) 공용

    # 5. 파일 업로드
    upload_backend: str = "local"
    cloudinary_url: str = ""

    @property
    def sqlalchemy_url(self) -> str:
        """SQLAlchemy 접속 주소. 비밀번호에 특수문자가 있어도 자동으로 처리된다."""
        if self.database_url:
            return self.database_url
        url = URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )
        return url.render_as_string(hide_password=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
