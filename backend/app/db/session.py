from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def engine_options(database_url: str) -> dict:
    options: dict = {"pool_pre_ping": True}
    if make_url(database_url).get_backend_name() == "mysql":
        # MySQL 은 오래 쉰 연결을 끊으므로(wait_timeout) 1시간마다 연결을 새로 만든다
        options["pool_recycle"] = 3600
        # 모든 시간은 UTC 로 저장한다. NOW() 등 DB 기본값도 UTC 가 되도록 세션 시간대를 고정
        options["connect_args"] = {"init_command": "SET time_zone = '+00:00'"}
    return options


engine = create_engine(settings.sqlalchemy_url, **engine_options(settings.sqlalchemy_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
