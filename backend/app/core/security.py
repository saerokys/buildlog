from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

ACCESS_TOKEN_COOKIE = "buildlog_access_token"
JWT_ALGORITHM = "HS256"

_password_hash = PasswordHash.recommended()  # Argon2

# 없는 이메일로 로그인할 때도 비밀번호 확인 시간을 똑같이 쓰기 위한 값입니다.
_DUMMY_HASH = _password_hash.hash("buildlog-dummy-password")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _password_hash.verify(password, _DUMMY_HASH)
        return False
    return _password_hash.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm=JWT_ALGORITHM)


def read_access_token(token: str) -> int | None:
    """토큰이 올바르면 사용자 번호를, 아니면 None을 돌려줍니다."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None
