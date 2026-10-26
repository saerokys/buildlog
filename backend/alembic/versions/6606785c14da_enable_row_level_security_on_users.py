"""enable row level security on users

Supabase는 public 스키마의 테이블을 자동 API(Data API)로 공개합니다.
행 단위 보안(RLS)을 켜고 허용 규칙을 만들지 않으면, 공개 키(anon key)로는
users 테이블을 읽거나 쓸 수 없습니다. 백엔드는 테이블 소유자로 접속하므로
이 설정의 영향을 받지 않습니다. SQLite에는 이 기능이 없으므로 건너뜁니다.

Revision ID: 6606785c14da
Revises: 204b404e2459
Create Date: 2026-10-26 16:37:48.342522

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6606785c14da'
down_revision: Union[str, Sequence[str], None] = '204b404e2459'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_context().dialect.name == "postgresql":
        op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_context().dialect.name == "postgresql":
        op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
