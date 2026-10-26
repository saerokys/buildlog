from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.accounts.validators import (
    email_error,
    nickname_error,
    normalize_email,
    normalize_nickname,
    password_error,
)
from app.core.errors import AppError
from app.core.security import hash_password, verify_password

EMAIL_TAKEN = "이미 사용 중인 이메일입니다. 다른 이메일을 입력해 주세요."
NICKNAME_TAKEN = "이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요."
SIGNUP_INVALID = "입력한 내용을 다시 확인해 주세요."
LOGIN_FAILED = "이메일 또는 비밀번호가 맞지 않습니다."
NICKNAME_UPDATE_INVALID = "닉네임을 변경하지 못했습니다. 입력한 내용을 확인해 주세요."


def _email_exists(db: Session, email: str) -> bool:
    return db.scalar(select(User.id).where(User.email == email)) is not None


def _nickname_owner(db: Session, nickname: str) -> int | None:
    return db.scalar(select(User.id).where(User.nickname == nickname))


def signup(db: Session, email: str, password: str, nickname: str) -> User:
    email = normalize_email(email)
    nickname = normalize_nickname(nickname)

    errors = {}
    if error := email_error(email):
        errors["email"] = error
    if error := password_error(password):
        errors["password"] = error
    if error := nickname_error(nickname):
        errors["nickname"] = error
    if errors:
        raise AppError(400, SIGNUP_INVALID, errors)

    if _email_exists(db, email):
        errors["email"] = EMAIL_TAKEN
    if _nickname_owner(db, nickname) is not None:
        errors["nickname"] = NICKNAME_TAKEN
    if errors:
        raise AppError(409, SIGNUP_INVALID, errors)

    user = User(email=email, nickname=nickname, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # 거의 동시에 같은 이메일이나 닉네임으로 가입한 경우입니다.
        db.rollback()
        errors = {}
        if _email_exists(db, email):
            errors["email"] = EMAIL_TAKEN
        if _nickname_owner(db, nickname) is not None:
            errors["nickname"] = NICKNAME_TAKEN
        raise AppError(409, SIGNUP_INVALID, errors) from None
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    # 이메일이 없을 때도 비밀번호 확인을 똑같이 수행해 응답 시간으로 가입 여부를 알 수 없게 합니다.
    password_ok = verify_password(password, user.password_hash if user else None)
    if user is None or not password_ok:
        raise AppError(401, LOGIN_FAILED)
    return user


def change_nickname(db: Session, user: User, nickname: str) -> User:
    nickname = normalize_nickname(nickname)

    if error := nickname_error(nickname):
        raise AppError(400, NICKNAME_UPDATE_INVALID, {"nickname": error})

    owner_id = _nickname_owner(db, nickname)
    if owner_id is not None and owner_id != user.id:
        raise AppError(409, NICKNAME_UPDATE_INVALID, {"nickname": NICKNAME_TAKEN})

    user.nickname = nickname
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, NICKNAME_UPDATE_INVALID, {"nickname": NICKNAME_TAKEN}) from None
    db.refresh(user)
    return user
