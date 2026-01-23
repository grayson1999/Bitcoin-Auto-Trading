"""Create user_configs table.

Revision ID: 011
Revises: 010
Create Date: 2026-01-24

Tables created:
- user_configs: 사용자별 설정 오버라이드
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create user_configs table."""
    op.create_table(
        "user_configs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
            comment="사용자 ID",
        ),
        sa.Column(
            "key",
            sa.String(50),
            nullable=False,
            comment="설정 키",
        ),
        sa.Column(
            "value",
            sa.Text(),
            nullable=False,
            comment="설정 값 (JSON)",
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
        sa.Column(
            "created_by",
            sa.BigInteger(),
            nullable=True,
            comment="생성자 ID",
        ),
        sa.Column(
            "updated_by",
            sa.BigInteger(),
            nullable=True,
            comment="수정자 ID",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )

    # 인덱스 생성
    op.create_unique_constraint(
        "uq_user_configs_user_key",
        "user_configs",
        ["user_id", "key"],
    )
    op.create_index(
        "idx_user_configs_user_id",
        "user_configs",
        ["user_id"],
    )
    op.create_index(
        "idx_user_configs_updated",
        "user_configs",
        [sa.text("updated_at DESC")],
    )


def downgrade() -> None:
    """Drop user_configs table."""
    op.drop_index("idx_user_configs_updated", table_name="user_configs")
    op.drop_index("idx_user_configs_user_id", table_name="user_configs")
    op.drop_constraint("uq_user_configs_user_key", "user_configs", type_="unique")
    op.drop_table("user_configs")
