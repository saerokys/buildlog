import re

EMAIL_MAX_LENGTH = 254
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64
NICKNAME_MIN_LENGTH = 2
NICKNAME_MAX_LENGTH = 20

# 일반적인 이메일 형식: 공백과 @가 없는 앞부분 @ 점이 들어간 도메인
_EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
# 한글(완성형), 영문, 숫자, 밑줄
_NICKNAME_PATTERN = re.compile(r"[가-힣A-Za-z0-9_]+")

EMAIL_INVALID = "올바른 이메일 주소를 입력해 주세요."
PASSWORD_INVALID = f"비밀번호는 {PASSWORD_MIN_LENGTH}~{PASSWORD_MAX_LENGTH}자로 입력해 주세요."
NICKNAME_INVALID = (
    f"닉네임은 {NICKNAME_MIN_LENGTH}~{NICKNAME_MAX_LENGTH}자의 한글, 영문, 숫자, 밑줄(_)만 사용할 수 있습니다."
)


def normalize_email(email: str) -> str:
    # 이메일은 대소문자를 구분하므로 앞뒤 공백만 지우고 입력한 그대로 저장합니다.
    return email.strip()


def normalize_nickname(nickname: str) -> str:
    return nickname.strip()


def email_error(email: str) -> str | None:
    if len(email) > EMAIL_MAX_LENGTH or not _EMAIL_PATTERN.fullmatch(email):
        return EMAIL_INVALID
    return None


def password_error(password: str) -> str | None:
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        return PASSWORD_INVALID
    return None


def nickname_error(nickname: str) -> str | None:
    if not NICKNAME_MIN_LENGTH <= len(nickname) <= NICKNAME_MAX_LENGTH:
        return NICKNAME_INVALID
    if not _NICKNAME_PATTERN.fullmatch(nickname):
        return NICKNAME_INVALID
    return None
