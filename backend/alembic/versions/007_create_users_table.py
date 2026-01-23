"""Create users table.

Revision ID: 007
Revises: a97d74808344
Create Date: 2026-01-24

Tables created:
- users: Auth Server 사용자 매핑
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "a97d74808344"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users table."""
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "auth_user_id",
            sa.String(36),
            nullable=False,
            comment="Auth Server UUID",
        ),
        sa.Column(
            "email",
            sa.String(255),
            nullable=False,
            comment="사용자 이메일",
        ),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
            comment="사용자 이름",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="생성 시간",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="수정 시간",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 인덱스 생성
    op.create_index(
        "idx_users_auth_user_id",
        "users",
        ["auth_user_id"],
        unique=True,
    )
    op.create_index(
        "idx_users_email",
        "users",
        ["email"],
    )


def downgrade() -> None:
    """Drop users table."""
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_users_auth_user_id", table_name="users")
    op.drop_table("users")
