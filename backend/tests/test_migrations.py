import io
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.core.database import make_engine
from app.models import Base

BACKEND_DIR = Path(__file__).resolve().parents[1]


def alembic_config(database_url: str) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migrations_create_tables_matching_models(tmp_path):
    database_url = "sqlite:///" + (tmp_path / "migrate.sqlite3").as_posix()

    command.upgrade(alembic_config(database_url), "head")

    engine = make_engine(database_url)
    try:
        assert "users" in inspect(engine).get_table_names()
        with engine.connect() as connection:
            differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert differences == [], "모델과 마이그레이션이 다릅니다. 새 마이그레이션이 필요합니다."
    finally:
        engine.dispose()


def test_postgresql_migration_sql_creates_tables_and_enables_rls():
    # 실제 Supabase에 접속하지 않고, PostgreSQL에 보낼 SQL만 만들어 확인합니다.
    output = io.StringIO()
    config = alembic_config("postgresql+psycopg://user:pass@localhost:5432/postgres")
    config.output_buffer = output

    command.upgrade(config, "head", sql=True)

    sql = output.getvalue()
    assert "CREATE TABLE users" in sql
    assert "is_admin BOOLEAN DEFAULT false NOT NULL" in sql
    assert "ALTER TABLE users ENABLE ROW LEVEL SECURITY" in sql
    # 이미 적용한 변경을 기록하는 표도 함께 만듭니다.
    assert "CREATE TABLE alembic_version" in sql


def test_upgrade_twice_does_not_reapply(tmp_path):
    database_url = "sqlite:///" + (tmp_path / "migrate.sqlite3").as_posix()
    config = alembic_config(database_url)

    command.upgrade(config, "head")
    command.upgrade(config, "head")

    engine = make_engine(database_url)
    try:
        with engine.connect() as connection:
            assert MigrationContext.configure(connection).get_current_revision() is not None
    finally:
        engine.dispose()


def test_migrations_can_be_reverted(tmp_path):
    database_url = "sqlite:///" + (tmp_path / "migrate.sqlite3").as_posix()
    config = alembic_config(database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = make_engine(database_url)
    try:
        assert "users" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()
