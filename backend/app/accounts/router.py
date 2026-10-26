from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.accounts import service
from app.accounts.dependencies import CurrentUser
from app.accounts.schemas import (
    LoginRequest,
    NicknameUpdateRequest,
    SignupRequest,
    UserResponse,
)
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import ACCESS_TOKEN_COOKIE, create_access_token

router = APIRouter(prefix="/api")

DbSession = Annotated[Session, Depends(get_db)]


def _to_response(user) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, nickname=user.nickname, is_admin=user.is_admin)


@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: DbSession) -> UserResponse:
    user = service.signup(db, body.email, body.password, body.nickname)
    return _to_response(user)


@router.post("/auth/login")
def login(body: LoginRequest, response: Response, db: DbSession) -> UserResponse:
    user = service.authenticate(db, body.email, body.password)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=create_access_token(user.id),
        max_age=get_settings().access_token_expire_minutes * 60,
        httponly=True,  # 화면의 JavaScript가 토큰을 읽지 못하게 합니다.
        samesite="lax",  # 다른 사이트에서 보낸 요청에는 쿠키를 붙이지 않습니다.
        path="/",
    )
    return _to_response(user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    # 로그인 쿠키를 지웁니다. 이미 로그아웃한 상태여도 같은 결과를 돌려줍니다.
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/", httponly=True, samesite="lax")


@router.get("/auth/me")
def me(user: CurrentUser) -> UserResponse:
    return _to_response(user)


@router.patch("/account/nickname")
def change_nickname(body: NicknameUpdateRequest, user: CurrentUser, db: DbSession) -> UserResponse:
    # 로그인한 본인의 닉네임만 바꿉니다. 다른 사용자를 지정하는 방법은 없습니다.
    return _to_response(service.change_nickname(db, user, body.nickname))
