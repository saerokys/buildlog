import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.accounts.models import User
from app.core.security import hash_password, verify_password


def make_user(email="user1@example.com", nickname="user_1", password="password123"):
    return User(email=email, nickname=nickname, password_hash=hash_password(password))


def test_save_users_with_different_email_and_nickname(db):
    db.add_all([make_user(), make_user(email="user2@example.com", nickname="사용자2")])
    db.commit()

    nicknames = db.scalars(select(User.nickname).order_by(User.id)).all()
    assert nicknames == ["user_1", "사용자2"]


def test_new_user_is_not_admin_and_has_created_at(db):
    user = make_user()
    db.add(user)
    db.commit()

    assert user.is_admin is False
    assert user.created_at is not None


def test_duplicate_email_is_rejected_by_database(db):
    db.add(make_user(nickname="first"))
    db.commit()

    db.add(make_user(nickname="second"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_duplicate_nickname_is_rejected_by_database(db):
    db.add(make_user(email="a@example.com"))
    db.commit()

    db.add(make_user(email="b@example.com"))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("nickname", ["ab", "가나", "a" * 20, "Abc_123", "홍길동_01"])
def test_valid_nicknames_are_accepted(nickname):
    assert make_user(nickname=nickname).nickname == nickname


@pytest.mark.parametrize(
    "nickname",
    ["a", "a" * 21, "", "has space", "dash-name", "emoji😀", "ㄱㄴ", "name!"],
)
def test_invalid_nicknames_are_rejected(nickname):
    with pytest.raises(ValueError):
        make_user(nickname=nickname)


@pytest.mark.parametrize("email", ["no-at-sign", "a@b", "a b@example.com", "@example.com"])
def test_invalid_emails_are_rejected(email):
    with pytest.raises(ValueError):
        make_user(email=email)


def test_password_is_stored_as_hash_not_plain_text(db):
    db.add(make_user(password="my-plain-password"))
    db.commit()

    stored = db.execute(text("SELECT password_hash FROM users")).scalar_one()
    assert "my-plain-password" not in stored
    assert stored.startswith("$argon2")
    assert verify_password("my-plain-password", stored)
    assert not verify_password("wrong-password", stored)


def test_data_remains_after_reconnecting(engine, session_factory):
    with session_factory() as session:
        session.add(make_user())
        session.commit()

    # 연결을 모두 끊었다가 다시 연결해도 데이터가 남아 있어야 합니다.
    engine.dispose()
    with session_factory() as session:
        assert session.scalar(select(User.email)) == "user1@example.com"
