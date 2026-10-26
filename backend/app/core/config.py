from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# buildlog/ 프로젝트 최상위 폴더
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATABASE_URL = "sqlite:///" + (PROJECT_ROOT / "database" / "buildlog.sqlite3").as_posix()


class Settings(BaseSettings):
    """환경 변수와 프로젝트 최상위 .env 파일에서 설정을 읽습니다."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    database_url: str = DEFAULT_DATABASE_URL
    secret_key: SecretStr
    access_token_expire_minutes: int = 1440


@lru_cache
def get_settings() -> Settings:
    return Settings()
