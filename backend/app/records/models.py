from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.accounts.models import User
from app.core.database import Base
from app.core.types import UTCDateTime, utc_now
from app.records.validators import CONTENT_MAX_LENGTH, TITLE_MAX_LENGTH, text_error

# 데이터베이스에서도 빈 제목·내용을 막습니다. (trim, length는 SQLite와 PostgreSQL 모두 지원)
_NOT_BLANK = "length(trim({column})) >= 1"


class _RecordColumns:
    """세 가지 기록이 함께 쓰는 열입니다."""

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, onupdate=utc_now)


def _check_text(value: str, label: str, max_length: int) -> str:
    if error := text_error(value, label, max_length):
        raise ValueError(error)
    return value


class StudyRecord(_RecordColumns, Base):
    __tablename__ = "study_records"
    __table_args__ = (
        CheckConstraint(_NOT_BLANK.format(column="title"), name="title_not_blank"),
        CheckConstraint(_NOT_BLANK.format(column="content"), name="content_not_blank"),
    )

    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    content: Mapped[str] = mapped_column(String(CONTENT_MAX_LENGTH))

    author: Mapped[User] = relationship()

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        return _check_text(value, "제목", TITLE_MAX_LENGTH)

    @validates("content")
    def _validate_content(self, _key: str, value: str) -> str:
        return _check_text(value, "내용", CONTENT_MAX_LENGTH)


class Todo(_RecordColumns, Base):
    __tablename__ = "todos"
    __table_args__ = (
        CheckConstraint(_NOT_BLANK.format(column="title"), name="title_not_blank"),
        # 완료 상태와 완료 날짜·시간이 항상 함께 맞도록 합니다.
        CheckConstraint(
            "(is_done AND completed_at IS NOT NULL) OR (NOT is_done AND completed_at IS NULL)",
            name="completed_at_matches_status",
        ),
    )

    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    author: Mapped[User] = relationship()

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        return _check_text(value, "제목", TITLE_MAX_LENGTH)


class ErrorRecord(_RecordColumns, Base):
    __tablename__ = "error_records"
    __table_args__ = (
        CheckConstraint(_NOT_BLANK.format(column="title"), name="title_not_blank"),
        CheckConstraint(_NOT_BLANK.format(column="content"), name="content_not_blank"),
        # 해결 방법은 비워둘 수 있지만, 입력했다면 공백만 있으면 안 됩니다.
        CheckConstraint(
            "solution IS NULL OR " + _NOT_BLANK.format(column="solution"),
            name="solution_not_blank",
        ),
        # 해결 상태라면 해결 방법이 반드시 있어야 합니다.
        CheckConstraint("NOT is_resolved OR solution IS NOT NULL", name="resolved_requires_solution"),
        CheckConstraint(
            "(is_resolved AND resolved_at IS NOT NULL) OR (NOT is_resolved AND resolved_at IS NULL)",
            name="resolved_at_matches_status",
        ),
    )

    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    content: Mapped[str] = mapped_column(String(CONTENT_MAX_LENGTH))
    solution: Mapped[str | None] = mapped_column(String(CONTENT_MAX_LENGTH))
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    author: Mapped[User] = relationship()

    @validates("title")
    def _validate_title(self, _key: str, value: str) -> str:
        return _check_text(value, "오류 제목", TITLE_MAX_LENGTH)

    @validates("content")
    def _validate_content(self, _key: str, value: str) -> str:
        return _check_text(value, "오류 내용", CONTENT_MAX_LENGTH)

    @validates("solution")
    def _validate_solution(self, _key: str, value: str | None) -> str | None:
        if value is None:
            return None
        return _check_text(value, "해결 방법", CONTENT_MAX_LENGTH)
