from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

# buildlog/backend 폴더
BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

# 오류 안내 문구. 입력한 값(비밀번호, 연결 주소)은 절대 넣지 않습니다.
DATABASE_URL_MISSING = (
    "DATABASE_URL이 없습니다. backend/.env에 Supabase Session pooler 연결 주소를 넣어 주세요."
)
DATABASE_URL_PLACEHOLDER = (
    "DATABASE_URL에 [YOUR-PASSWORD]가 남아 있습니다. Supabase 데이터베이스 비밀번호로 바꿔 주세요."
)
DATABASE_URL_INVALID = (
    "DATABASE_URL 형식이 올바르지 않습니다. "
    "postgresql://로 시작하는 Supabase Session pooler 주소를 그대로 붙여 넣었는지, "
    "비밀번호에 @ : / # 같은 특수문자가 있다면 URL 인코딩했는지 확인해 주세요."
)
DATABASE_URL_UNSUPPORTED = "DATABASE_URL은 postgresql:// 주소여야 합니다."
SECRET_KEY_MISSING = "SECRET_KEY가 없습니다. backend/.env에 SECRET_KEY를 넣어 주세요."

# 직접 지정한 경우에만 허용하는 드라이버. SQLite는 자동 테스트에서만 사용합니다.
_SUPPORTED_DRIVERS = {"postgresql+psycopg", "sqlite"}


class SettingsError(RuntimeError):
    """설정이 없거나 잘못됐을 때 무엇을 확인할지 알려주는 오류입니다."""


def normalize_database_url(value: str) -> str:
    """Supabase가 주는 postgresql:// 주소를 psycopg 드라이버 주소로 바꿉니다."""
    value = value.strip()
    if "[YOUR-PASSWORD]" in value or "YOUR-PASSWORD" in value:
        raise ValueError(DATABASE_URL_PLACEHOLDER)

    try:
        url = make_url(value)
    except ArgumentError:
        raise ValueError(DATABASE_URL_INVALID) from None

    if url.drivername in ("postgresql", "postgres"):
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername not in _SUPPORTED_DRIVERS:
        raise ValueError(DATABASE_URL_UNSUPPORTED)
    if url.drivername.startswith("postgresql") and not (url.host and url.username and url.password):
        raise ValueError(DATABASE_URL_INVALID)

    return url.render_as_string(hide_password=False)


class Settings(BaseSettings):
    """환경 변수와 backend/.env 파일에서 설정을 읽습니다."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # 기본값이 없으므로 설정하지 않으면 서버가 시작되지 않습니다. (SQLite로 자동 연결하지 않음)
    database_url: SecretStr
    secret_key: SecretStr
    access_token_expire_minutes: int = 1440

    @field_validator("database_url", mode="before")
    @classmethod
    def _check_database_url(cls, value):
        if isinstance(value, str):
            return normalize_database_url(value)
        return value


_MISSING_MESSAGES = {"database_url": DATABASE_URL_MISSING, "secret_key": SECRET_KEY_MISSING}


def _explain(error: ValidationError) -> str:
    """검증 오류를 입력값 없이 안내 문구로만 바꿉니다."""
    lines = []
    for item in error.errors(include_input=False, include_url=False):
        field = str(item["loc"][0]) if item["loc"] else ""
        if item["type"] == "missing":
            lines.append(_MISSING_MESSAGES.get(field, f"{field.upper()}가 없습니다."))
        elif item["type"] == "value_error":
            lines.append(str(item["ctx"]["error"]))
        else:
            lines.append(f"{field.upper()} 값을 확인해 주세요.")
    return "설정을 확인해 주세요.\n- " + "\n- ".join(lines)


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as error:
        # 원래 오류에는 입력한 연결 주소가 들어 있으므로 숨기고 안내 문구만 보여줍니다.
        raise SettingsError(_explain(error)) from None
