"""create record tables

공부 기록(study_records), 할 일(todos), 오류 기록(error_records) 테이블을 만듭니다.
PostgreSQL(Supabase)에서는 users와 같이 행 단위 보안(RLS)을 켜서
Supabase 공개 키로 테이블을 읽거나 쓸 수 없게 합니다.

Revision ID: 3137a74e3777
Revises: 6606785c14da
Create Date: 2026-10-27 09:21:09.618987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3137a74e3777'
down_revision: Union[str, Sequence[str], None] = '6606785c14da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RECORD_TABLES = ("study_records", "todos", "error_records")


def _common_columns() -> list[sa.Column]:
    return [
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('study_records',
    *_common_columns(),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.String(length=5000), nullable=False),
    sa.CheckConstraint('length(trim(content)) >= 1', name=op.f('ck_study_records_content_not_blank')),
    sa.CheckConstraint('length(trim(title)) >= 1', name=op.f('ck_study_records_title_not_blank')),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_study_records_author_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_study_records'))
    )
    with op.batch_alter_table('study_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_study_records_author_id'), ['author_id'], unique=False)

    op.create_table('todos',
    *_common_columns(),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('is_done', sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('(is_done AND completed_at IS NOT NULL) OR (NOT is_done AND completed_at IS NULL)', name=op.f('ck_todos_completed_at_matches_status')),
    sa.CheckConstraint('length(trim(title)) >= 1', name=op.f('ck_todos_title_not_blank')),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_todos_author_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_todos'))
    )
    with op.batch_alter_table('todos', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_todos_author_id'), ['author_id'], unique=False)

    op.create_table('error_records',
    *_common_columns(),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.String(length=5000), nullable=False),
    sa.Column('solution', sa.String(length=5000), nullable=True),
    sa.Column('is_resolved', sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('(is_resolved AND resolved_at IS NOT NULL) OR (NOT is_resolved AND resolved_at IS NULL)', name=op.f('ck_error_records_resolved_at_matches_status')),
    sa.CheckConstraint('NOT is_resolved OR solution IS NOT NULL', name=op.f('ck_error_records_resolved_requires_solution')),
    sa.CheckConstraint('length(trim(content)) >= 1', name=op.f('ck_error_records_content_not_blank')),
    sa.CheckConstraint('length(trim(title)) >= 1', name=op.f('ck_error_records_title_not_blank')),
    sa.CheckConstraint('solution IS NULL OR length(trim(solution)) >= 1', name=op.f('ck_error_records_solution_not_blank')),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_error_records_author_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_error_records'))
    )
    with op.batch_alter_table('error_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_error_records_author_id'), ['author_id'], unique=False)

    if op.get_context().dialect.name == "postgresql":
        for table in RECORD_TABLES:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Downgrade schema."""
    # 테이블을 지우면 RLS 설정도 함께 사라집니다.
    with op.batch_alter_table('error_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_error_records_author_id'))
    op.drop_table('error_records')

    with op.batch_alter_table('todos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_todos_author_id'))
    op.drop_table('todos')

    with op.batch_alter_table('study_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_study_records_author_id'))
    op.drop_table('study_records')
