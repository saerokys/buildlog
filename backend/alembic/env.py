from logging.config import fileConfig

from alembic import context

from app.core.config import SettingsError, get_settings

try:
    from app.core.database import make_engine
    from app.models import Base
except SettingsError as error:
    # backend/.env 설정이 없거나 잘못되면 긴 오류 대신 확인할 내용만 보여줍니다.
    raise SystemExit(str(error)) from None

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    # 테스트처럼 주소를 직접 넘긴 경우를 먼저 사용하고, 없으면 backend/.env 설정을 사용합니다.
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url.get_secret_value()


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = make_engine(get_database_url())

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite는 열 변경을 직접 지원하지 않으므로 표를 새로 만들어 옮기는 방식을 씁니다.
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
