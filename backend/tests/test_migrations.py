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
