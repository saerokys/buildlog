from collections.abc import Iterator

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

# 제약 조건 이름을 일정하게 만들어 SQLite와 PostgreSQL 마이그레이션이 같은 이름을 쓰게 합니다.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def engine_options(database_url: str) -> dict:
    url = make_url(database_url)
    if url.get_backend_name() == "sqlite":
        # FastAPI는 요청을 여러 스레드에서 처리하므로 SQLite 스레드 검사를 끕니다.
        return {"connect_args": {"check_same_thread": False}}

    # 서버가 응답하지 않을 때 오래 멈춰 있지 않도록 연결 대기 시간을 제한합니다(초).
    connect_args = {"connect_timeout": 10}
    if "sslmode" not in url.query:
        # Supabase에는 암호화된 연결로만 접속합니다.
        connect_args["sslmode"] = "require"
    # 연결 풀(pooler)이 오래 쉬는 연결을 끊을 수 있으므로 사용 전에 살아 있는지 확인합니다.
    return {"connect_args": connect_args, "pool_pre_ping": True}


def make_engine(database_url: str) -> Engine:
    engine = create_engine(database_url, **engine_options(database_url))

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _record):
            # SQLite는 기본적으로 외래 키 검사를 하지 않으므로 연결마다 켭니다.
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = make_engine(get_settings().database_url.get_secret_value())
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
