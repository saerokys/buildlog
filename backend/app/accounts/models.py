from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, false
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.accounts.validators import (
    EMAIL_MAX_LENGTH,
    NICKNAME_MAX_LENGTH,
    email_error,
    nickname_error,
)
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(NICKNAME_MAX_LENGTH), unique=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @validates("email")
    def _validate_email(self, _key: str, email: str) -> str:
        if error := email_error(email):
            raise ValueError(error)
        return email

    @validates("nickname")
    def _validate_nickname(self, _key: str, nickname: str) -> str:
        if error := nickname_error(nickname):
            raise ValueError(error)
        return nickname
