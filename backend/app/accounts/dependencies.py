from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import ACCESS_TOKEN_COOKIE, read_access_token

LOGIN_REQUIRED = "로그인이 필요합니다."


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE)] = None,
) -> User:
    """로그인이 필요한 모든 API에서 사용합니다. 로그인하지 않았으면 401을 돌려줍니다."""
    user_id = read_access_token(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise AppError(401, LOGIN_REQUIRED)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
