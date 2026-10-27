import time
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from app.accounts.models import User
from app.core.security import hash_password
from app.records.models import ErrorRecord, StudyRecord, Todo
from app.records.service import resolve_error, set_todo_done, unresolve_error

KST = timezone(timedelta(hours=9))


@pytest.fixture
def author(db):
    user = User(email="writer@example.com", nickname="writer", password_hash=hash_password("password123"))
    db.add(user)
    db.commit()
    return user


def is_utc(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() == timedelta(0)


# ---------- 저장과 기본값 ----------


def test_study_record_is_saved_with_defaults(db, author):
    db.add(StudyRecord(author=author, title="파이썬 공부", content="리스트와 딕셔너리"))
    db.commit()
    db.expire_all()

    record = db.scalar(select(StudyRecord))
    assert (record.title, record.content) == ("파이썬 공부", "리스트와 딕셔너리")
    assert record.is_public is False
    assert record.author.nickname == "writer"
    assert is_utc(record.created_at) and is_utc(record.updated_at)


def test_todo_is_saved_as_private_and_not_done(db, author):
    db.add(Todo(author=author, title="저장 버튼 만들기"))
    db.commit()
    db.expire_all()

    todo = db.scalar(select(Todo))
    assert todo.is_public is False
    assert todo.is_done is False
    assert todo.completed_at is None
    assert is_utc(todo.created_at)


def test_error_record_is_saved_as_private_and_unresolved_without_solution(db, author):
    db.add(ErrorRecord(author=author, title="ImportError", content="모듈을 찾을 수 없음"))
    db.commit()
    db.expire_all()

    record = db.scalar(select(ErrorRecord))
    assert record.is_public is False
    assert record.is_resolved is False
    assert record.solution is None
    assert record.resolved_at is None


def test_error_record_can_keep_solution_while_unresolved(db, author):
    db.add(ErrorRecord(author=author, title="오류", content="내용", solution="시도해 본 방법"))
    db.commit()

    assert db.scalar(select(ErrorRecord.is_resolved)) is False


def test_record_can_be_made_public(db, author):
    db.add(StudyRecord(author=author, title="공개 기록", content="내용", is_public=True))
    db.commit()

    assert db.scalar(select(StudyRecord.is_public)) is True


def test_updated_at_changes_when_record_is_edited(db, author):
    record = StudyRecord(author=author, title="처음 제목", content="내용")
    db.add(record)
    db.commit()
    created_at, first_updated_at = record.created_at, record.updated_at

    time.sleep(0.01)
    record.title = "바꾼 제목"
    db.commit()
    db.expire_all()

    assert record.created_at == created_at
    assert record.updated_at > first_updated_at


def test_times_are_stored_in_utc(db, author):
    korea_time = datetime(2026, 10, 27, 9, 0, tzinfo=KST)
    db.add(StudyRecord(author=author, title="제목", content="내용", created_at=korea_time))
    db.commit()
    db.expire_all()

    saved = db.scalar(select(StudyRecord.created_at))
    assert saved == datetime(2026, 10, 27, 0, 0, tzinfo=UTC)
    assert is_utc(saved)


def test_time_without_timezone_is_rejected(db, author):
    db.add(StudyRecord(author=author, title="제목", content="내용", created_at=datetime(2026, 10, 27, 9, 0)))

    with pytest.raises(Exception, match="시간대 정보가 없는"):
        db.commit()


# ---------- 길이 조건 ----------


@pytest.mark.parametrize("model", [StudyRecord, Todo, ErrorRecord])
@pytest.mark.parametrize("length", [1, 100])
def test_title_length_boundaries_are_accepted(model, length):
    assert len(model(title="t" * length).title) == length


@pytest.mark.parametrize("model", [StudyRecord, Todo, ErrorRecord])
@pytest.mark.parametrize("title", ["", "   ", "t" * 101])
def test_invalid_titles_are_rejected(model, title):
    with pytest.raises(ValueError, match="1~100자"):
        model(title=title)


@pytest.mark.parametrize("model", [StudyRecord, ErrorRecord])
@pytest.mark.parametrize("length", [1, 5000])
def test_content_length_boundaries_are_accepted(model, length):
    assert len(model(content="c" * length).content) == length


@pytest.mark.parametrize("model", [StudyRecord, ErrorRecord])
@pytest.mark.parametrize("content", ["", "  \n ", "c" * 5001])
def test_invalid_contents_are_rejected(model, content):
    with pytest.raises(ValueError, match="1~5,000자"):
        model(content=content)


@pytest.mark.parametrize("length", [1, 5000])
def test_solution_length_boundaries_are_accepted(length):
    assert len(ErrorRecord(solution="s" * length).solution) == length


@pytest.mark.parametrize("solution", ["", "   ", "s" * 5001])
def test_invalid_solutions_are_rejected(solution):
    with pytest.raises(ValueError, match="해결 방법은 1~5,000자"):
        ErrorRecord(solution=solution)


def test_middle_spaces_are_kept(db, author):
    db.add(StudyRecord(author=author, title="중간  띄어쓰기", content="첫 줄\n둘째 줄"))
    db.commit()

    assert db.scalar(select(StudyRecord.title)) == "중간  띄어쓰기"


# ---------- 데이터베이스 제약 (화면·API 검사를 거치지 않아도 막히는지) ----------


def _now():
    return datetime.now(UTC)


@pytest.mark.parametrize(
    "table, values",
    [
        (StudyRecord, {"title": "   ", "content": "내용"}),
        (StudyRecord, {"title": "제목", "content": ""}),
        (Todo, {"title": " "}),
        (ErrorRecord, {"title": "제목", "content": "내용", "solution": "  "}),
    ],
)
def test_database_rejects_blank_text(db, author, table, values):
    with pytest.raises(IntegrityError):
        db.execute(insert(table).values(author_id=author.id, **values))
        db.commit()


def test_database_rejects_resolved_error_without_solution(db, author):
    with pytest.raises(IntegrityError):
        db.execute(
            insert(ErrorRecord).values(
                author_id=author.id, title="제목", content="내용", is_resolved=True, resolved_at=_now()
            )
        )
        db.commit()


@pytest.mark.parametrize(
    "table, values",
    [
        (Todo, {"title": "할 일", "is_done": True}),
        (Todo, {"title": "할 일", "completed_at": datetime(2026, 1, 1, tzinfo=UTC)}),
        (ErrorRecord, {"title": "제목", "content": "내용", "solution": "방법", "is_resolved": True}),
        (ErrorRecord, {"title": "제목", "content": "내용", "resolved_at": datetime(2026, 1, 1, tzinfo=UTC)}),
    ],
)
def test_database_keeps_status_and_time_together(db, author, table, values):
    with pytest.raises(IntegrityError):
        db.execute(insert(table).values(author_id=author.id, **values))
        db.commit()


def test_record_needs_existing_author(db):
    db.add(StudyRecord(author_id=9999, title="제목", content="내용"))

    with pytest.raises(IntegrityError):
        db.commit()


# ---------- 할 일 완료·취소 ----------


def test_completing_todo_saves_completed_time(db, author):
    todo = Todo(author=author, title="할 일")
    db.add(todo)
    db.commit()

    set_todo_done(todo, True)
    db.commit()
    db.expire_all()

    assert todo.is_done is True
    assert is_utc(todo.completed_at)


def test_completing_todo_again_keeps_first_completed_time(db, author):
    todo = Todo(author=author, title="할 일")
    db.add(todo)
    first = datetime(2026, 10, 1, tzinfo=UTC)
    set_todo_done(todo, True, now=first)

    set_todo_done(todo, True, now=datetime(2026, 10, 2, tzinfo=UTC))
    db.commit()

    assert todo.completed_at == first


def test_cancelling_todo_clears_completed_time(db, author):
    todo = Todo(author=author, title="할 일")
    db.add(todo)
    set_todo_done(todo, True)
    db.commit()

    set_todo_done(todo, False)
    db.commit()
    db.expire_all()

    assert todo.is_done is False
    assert todo.completed_at is None


# ---------- 오류 해결·미해결 ----------


def test_resolving_error_with_solution_saves_resolved_time(db, author):
    record = ErrorRecord(author=author, title="오류", content="내용")
    db.add(record)
    db.commit()

    resolve_error(record, solution="패키지를 다시 설치함")
    db.commit()
    db.expire_all()

    assert record.is_resolved is True
    assert record.solution == "패키지를 다시 설치함"
    assert is_utc(record.resolved_at)


def test_resolving_error_uses_existing_solution(db, author):
    record = ErrorRecord(author=author, title="오류", content="내용", solution="이미 적은 방법")
    db.add(record)

    resolve_error(record)
    db.commit()

    assert record.is_resolved is True


def test_error_cannot_be_resolved_without_solution(db, author):
    record = ErrorRecord(author=author, title="오류", content="내용")
    db.add(record)
    db.commit()

    with pytest.raises(ValueError, match="해결 방법을 입력해 주세요"):
        resolve_error(record)

    assert record.is_resolved is False
    assert record.resolved_at is None


def test_unresolving_error_keeps_solution_and_clears_resolved_time(db, author):
    record = ErrorRecord(author=author, title="오류", content="내용")
    db.add(record)
    resolve_error(record, solution="해결 방법")
    db.commit()

    unresolve_error(record)
    db.commit()
    db.expire_all()

    assert record.is_resolved is False
    assert record.resolved_at is None
    assert record.solution == "해결 방법"


def test_resolving_again_keeps_first_resolved_time(db, author):
    record = ErrorRecord(author=author, title="오류", content="내용")
    db.add(record)
    first = datetime(2026, 10, 1, tzinfo=UTC)
    resolve_error(record, solution="방법", now=first)

    resolve_error(record, now=datetime(2026, 10, 2, tzinfo=UTC))
    db.commit()

    assert record.resolved_at == first


# ---------- 다시 연결해도 데이터 유지 ----------


def test_records_remain_after_reconnecting(engine, session_factory):
    with session_factory() as session:
        user = User(email="keep@example.com", nickname="keeper", password_hash=hash_password("password123"))
        session.add_all(
            [
                StudyRecord(author=user, title="공부", content="내용"),
                Todo(author=user, title="할 일"),
                ErrorRecord(author=user, title="오류", content="내용"),
            ]
        )
        session.commit()

    engine.dispose()
    with session_factory() as session:
        assert session.scalar(select(StudyRecord.title)) == "공부"
        assert session.scalar(select(Todo.title)) == "할 일"
        assert session.scalar(select(ErrorRecord.title)) == "오류"
