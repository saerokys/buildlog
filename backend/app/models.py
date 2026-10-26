"""Alembic이 모든 테이블을 찾을 수 있도록 각 앱의 모델을 한곳에서 불러옵니다."""

from app.accounts.models import User  # noqa: F401
from app.core.database import Base  # noqa: F401
