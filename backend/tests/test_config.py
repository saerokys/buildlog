import pytest
from pydantic import ValidationError

from app.core.config import PROJECT_ROOT, Settings


def test_default_database_is_sqlite_file_in_database_folder(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)

    expected = (PROJECT_ROOT / "database" / "buildlog.sqlite3").as_posix()
    assert settings.database_url == f"sqlite:///{expected}"
    assert settings.access_token_expire_minutes == 1440


def test_empty_database_url_uses_default(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")

    settings = Settings(_env_file=None)

    assert settings.database_url.endswith("/database/buildlog.sqlite3")


def test_secret_key_is_required(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_secret_key_is_hidden_when_printed():
    settings = Settings(_env_file=None)

    assert "test-secret-key" not in repr(settings)
