import pytest
from pydantic import ValidationError

from app.core import config
from app.core.config import ENV_FILE, BACKEND_DIR, Settings, SettingsError, get_settings
from app.core.database import engine_options

SUPABASE_URL = "postgresql://postgres.abcdef:my-db-pass@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres"


def test_settings_are_read_from_backend_env_file():
    assert ENV_FILE == BACKEND_DIR / ".env"
    assert BACKEND_DIR.name == "backend"


def test_supabase_url_uses_psycopg_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", SUPABASE_URL)

    settings = Settings(_env_file=None)

    url = settings.database_url.get_secret_value()
    assert url.startswith("postgresql+psycopg://postgres.abcdef:my-db-pass@")
    assert url.endswith("pooler.supabase.com:5432/postgres")
    assert settings.access_token_expire_minutes == 1440


def test_url_encoded_password_is_kept(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", SUPABASE_URL.replace("my-db-pass", "p%40ss%23word"))

    url = Settings(_env_file=None).database_url.get_secret_value()

    assert ":p%40ss%23word@" in url


@pytest.mark.parametrize("value", [None, ""])
def test_database_url_is_required_and_does_not_fall_back_to_sqlite(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    "value",
    [
        "postgresql://postgres.abcdef:[YOUR-PASSWORD]@aws-0-x.pooler.supabase.com:5432/postgres",
        "not a url",
        "mysql://user:pass@localhost/db",
        "postgresql://aws-0-x.pooler.supabase.com:5432/postgres",
    ],
)
def test_wrong_database_url_is_rejected(monkeypatch, value):
    monkeypatch.setenv("DATABASE_URL", value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_secret_key_is_required(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_secrets_are_hidden_when_printed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", SUPABASE_URL)

    printed = repr(Settings(_env_file=None))

    assert "test-secret-key" not in printed
    assert "my-db-pass" not in printed
    assert "pooler.supabase.com" not in printed


def _settings_error(monkeypatch, **env) -> str:
    for name, value in env.items():
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    monkeypatch.setattr(config.Settings, "model_config", {**config.Settings.model_config, "env_file": None})
    get_settings.cache_clear()
    try:
        with pytest.raises(SettingsError) as error:
            get_settings()
    finally:
        get_settings.cache_clear()
    return str(error.value)


def test_missing_database_url_explains_what_to_check(monkeypatch):
    message = _settings_error(monkeypatch, DATABASE_URL=None)

    assert "DATABASE_URL이 없습니다" in message
    assert "Session pooler" in message


def test_settings_error_never_shows_password_or_url(monkeypatch):
    bad = "postgresql://postgres.abcdef:Sup3rSecret@:not-a-port/postgres"
    message = _settings_error(monkeypatch, DATABASE_URL=bad, SECRET_KEY=None)

    assert "Sup3rSecret" not in message
    assert "postgres.abcdef" not in message
    assert "SECRET_KEY가 없습니다" in message


def test_placeholder_password_explains_what_to_fix(monkeypatch):
    message = _settings_error(
        monkeypatch,
        DATABASE_URL="postgresql://postgres.abcdef:[YOUR-PASSWORD]@aws-0-x.pooler.supabase.com:5432/postgres",
    )

    assert "[YOUR-PASSWORD]" in message
    assert "postgres.abcdef" not in message


def test_postgres_engine_requires_ssl_and_checks_connections():
    options = engine_options("postgresql+psycopg://u:p@host:5432/postgres")

    assert options["connect_args"] == {"sslmode": "require", "connect_timeout": 10}
    assert options["pool_pre_ping"] is True


def test_postgres_engine_keeps_sslmode_from_url():
    options = engine_options("postgresql+psycopg://u:p@host:5432/postgres?sslmode=verify-full")

    assert options["connect_args"] == {"connect_timeout": 10}
