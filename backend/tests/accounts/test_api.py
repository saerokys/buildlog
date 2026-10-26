import pytest
from sqlalchemy import select

from app.accounts.models import User
from app.core.security import ACCESS_TOKEN_COOKIE

SIGNUP_URL = "/api/auth/signup"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/auth/me"
LOGOUT_URL = "/api/auth/logout"
NICKNAME_URL = "/api/account/nickname"


def signup(client, email="user1@example.com", password="password123", nickname="user_1"):
    return client.post(SIGNUP_URL, json={"email": email, "password": password, "nickname": nickname})


def login(client, email="user1@example.com", password="password123"):
    return client.post(LOGIN_URL, json={"email": email, "password": password})


# ---------- 회원가입 ----------


def test_signup_creates_account(client, db):
    response = signup(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user1@example.com"
    assert body["nickname"] == "user_1"
    assert body["is_admin"] is False
    assert "password" not in str(body).lower()
    assert db.scalar(select(User.email)) == "user1@example.com"


def test_signup_with_different_email_and_nickname(client):
    assert signup(client).status_code == 201
    assert signup(client, email="user2@example.com", nickname="user_2").status_code == 201


def test_signup_rejects_same_email_twice(client):
    signup(client)

    response = signup(client, nickname="other")

    assert response.status_code == 409
    assert "email" in response.json()["errors"]


def test_signup_treats_different_case_email_as_different_account(client):
    signup(client)

    response = signup(client, email="USER1@Example.com", nickname="other")

    assert response.status_code == 201
    assert response.json()["email"] == "USER1@Example.com"


def test_signup_rejects_nickname_in_use(client):
    signup(client)

    response = signup(client, email="user2@example.com")

    assert response.status_code == 409
    assert response.json()["errors"] == {"nickname": "이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요."}


@pytest.mark.parametrize("email", ["not-an-email", "a@b", "a b@example.com", ""])
def test_signup_rejects_invalid_email(client, email):
    response = signup(client, email=email)

    assert response.status_code == 400
    assert response.json()["errors"]["email"] == "올바른 이메일 주소를 입력해 주세요."


@pytest.mark.parametrize("length", [8, 64])
def test_signup_accepts_password_length_boundaries(client, length):
    assert signup(client, password="p" * length).status_code == 201


@pytest.mark.parametrize("length", [7, 65, 0])
def test_signup_rejects_password_length_out_of_range(client, length):
    response = signup(client, password="p" * length)

    assert response.status_code == 400
    assert "8~64자" in response.json()["errors"]["password"]


def test_signup_keeps_password_as_entered(client):
    # 비밀번호는 앞뒤 공백을 지우지 않고 입력한 그대로 사용합니다.
    signup(client, password="  space-pass  ")

    assert login(client, password="  space-pass  ").status_code == 200
    assert login(client, password="space-pass").status_code == 401


@pytest.mark.parametrize("nickname", ["ab", "a" * 20, "한글닉", "Mix_한글_9"])
def test_signup_accepts_valid_nicknames(client, nickname):
    assert signup(client, nickname=nickname).status_code == 201


@pytest.mark.parametrize("nickname", ["a", "a" * 21, "has space", "dash-name", "name!", "   "])
def test_signup_rejects_invalid_nicknames(client, nickname):
    response = signup(client, nickname=nickname)

    assert response.status_code == 400
    assert "nickname" in response.json()["errors"]


def test_signup_trims_email_and_nickname(client):
    response = signup(client, email="  user1@example.com  ", nickname="  user_1  ")

    assert response.status_code == 201
    assert response.json()["email"] == "user1@example.com"
    assert response.json()["nickname"] == "user_1"


def test_signup_reports_all_invalid_fields_at_once(client):
    response = signup(client, email="bad", password="short", nickname="!")

    assert set(response.json()["errors"]) == {"email", "password", "nickname"}


def test_signup_with_missing_field_is_rejected(client):
    response = client.post(SIGNUP_URL, json={"email": "user1@example.com"})

    assert response.status_code == 400
    assert {"password", "nickname"} <= set(response.json()["errors"])


# ---------- 로그인 ----------


def test_login_with_correct_information(client):
    signup(client)

    response = login(client)

    assert response.status_code == 200
    assert response.json()["nickname"] == "user_1"
    cookie_header = response.headers["set-cookie"]
    assert ACCESS_TOKEN_COOKIE in cookie_header
    assert "HttpOnly" in cookie_header
    assert "samesite=lax" in cookie_header.lower()


def test_login_email_is_trimmed(client):
    signup(client)

    assert login(client, email="  user1@example.com ").status_code == 200


def test_login_email_is_case_sensitive(client):
    signup(client)

    assert login(client, email="USER1@example.com").status_code == 401


def test_login_with_wrong_password_or_unknown_email_gives_same_message(client):
    signup(client)

    wrong_password = login(client, password="wrong-password")
    unknown_email = login(client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["message"] == "이메일 또는 비밀번호가 맞지 않습니다."
    assert ACCESS_TOKEN_COOKIE not in wrong_password.headers.get("set-cookie", "")


def test_me_returns_logged_in_user(client):
    signup(client)
    login(client)

    response = client.get(ME_URL)

    assert response.status_code == 200
    assert response.json()["email"] == "user1@example.com"


def test_me_requires_login(client):
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["message"] == "로그인이 필요합니다."


def test_me_rejects_forged_token(client):
    signup(client)
    client.cookies.set(ACCESS_TOKEN_COOKIE, "forged.token.value")

    assert client.get(ME_URL).status_code == 401


# ---------- 로그아웃 ----------


def test_logout_removes_login(client):
    signup(client)
    login(client)
    assert client.get(ME_URL).status_code == 200

    response = client.post(LOGOUT_URL)

    assert response.status_code == 204
    cookie_header = response.headers["set-cookie"]
    assert ACCESS_TOKEN_COOKIE in cookie_header
    assert "Max-Age=0" in cookie_header
    assert client.get(ME_URL).status_code == 401


def test_logout_without_login_is_allowed(client):
    assert client.post(LOGOUT_URL).status_code == 204


def test_can_login_again_after_logout(client):
    signup(client)
    login(client)
    client.post(LOGOUT_URL)

    assert login(client).status_code == 200
    assert client.get(ME_URL).status_code == 200


# ---------- 닉네임 변경 ----------


def test_change_nickname(client):
    signup(client)
    login(client)

    response = client.patch(NICKNAME_URL, json={"nickname": "  새닉네임  "})

    assert response.status_code == 200
    assert response.json()["nickname"] == "새닉네임"
    assert client.get(ME_URL).json()["nickname"] == "새닉네임"


def test_change_nickname_to_own_current_nickname_is_allowed(client):
    signup(client)
    login(client)

    assert client.patch(NICKNAME_URL, json={"nickname": "user_1"}).status_code == 200


def test_change_nickname_rejects_nickname_in_use(client):
    signup(client, email="other@example.com", nickname="taken")
    signup(client)
    login(client)

    response = client.patch(NICKNAME_URL, json={"nickname": "taken"})

    assert response.status_code == 409
    assert response.json()["errors"]["nickname"] == "이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요."
    assert client.get(ME_URL).json()["nickname"] == "user_1"


@pytest.mark.parametrize("nickname", ["a", "a" * 21, "bad name", "   "])
def test_change_nickname_applies_rules(client, nickname):
    signup(client)
    login(client)

    response = client.patch(NICKNAME_URL, json={"nickname": nickname})

    assert response.status_code == 400
    assert "nickname" in response.json()["errors"]


def test_change_nickname_requires_login(client):
    signup(client)

    assert client.patch(NICKNAME_URL, json={"nickname": "new_name"}).status_code == 401


def test_change_nickname_only_changes_own_account(client, db):
    signup(client, email="a@example.com", nickname="user_a")
    signup(client, email="b@example.com", nickname="user_b")
    login(client, email="b@example.com")

    # 요청에 다른 사용자 정보를 넣어도 로그인한 본인만 바뀝니다.
    client.patch(NICKNAME_URL, json={"nickname": "changed", "id": 1, "email": "a@example.com"})

    nicknames = dict(db.execute(select(User.email, User.nickname)).all())
    assert nicknames == {"a@example.com": "user_a", "b@example.com": "changed"}
