from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
import app.models  # noqa: F401  모델을 불러와야 autogenerate 가 테이블을 인식한다
from app.core.config import settings
from app.db.base import Base
from app.db.types import UTCDateTime

config = context.config
# ConfigParser 는 % 를 특수문자로 보므로 비밀번호에 % 가 있어도 깨지지 않게 이스케이프
config.set_main_option("sqlalchemy.url", settings.sqlalchemy_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    """UTCDateTime 은 DB 에서는 그냥 DATETIME 이므로 마이그레이션에는 sa.DateTime() 으로 적는다."""
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime()"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_item=render_item,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
