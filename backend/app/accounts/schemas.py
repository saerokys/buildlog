from pydantic import BaseModel


class SignupRequest(BaseModel):
    email: str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    email: str
    password: str


class NicknameUpdateRequest(BaseModel):
    nickname: str


class UserResponse(BaseModel):
    """화면에 돌려주는 사용자 정보입니다. 비밀번호는 절대 포함하지 않습니다."""

    id: int
    email: str
    nickname: str
    is_admin: bool
