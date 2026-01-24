"""add_balance_adjustments_table

입금/출금 추적을 위한 balance_adjustments 테이블 추가

Revision ID: 014
Revises: 013
Create Date: 2026-01-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "balance_adjustments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
            comment="소유자 사용자 ID",
        ),
        sa.Column("date", sa.Date(), nullable=False, comment="조정일"),
        sa.Column(
            "amount",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            comment="조정 금액 (입금: 양수, 출금: 음수)",
        ),
        sa.Column(
            "adjustment_type",
            sa.String(length=20),
            nullable=False,
            comment="조정 타입 (deposit/withdrawal/manual)",
        ),
        sa.Column(
            "balance_before",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            comment="조정 전 잔고",
        ),
        sa.Column(
            "balance_after",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            comment="조정 후 잔고",
        ),
        sa.Column("notes", sa.Text(), nullable=True, comment="메모"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="생성 시간",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="수정 시간",
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="수정자"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )

    # 인덱스 생성
    op.create_index(
        "ix_balance_adjustments_date",
        "balance_adjustments",
        ["date"],
        unique=False,
    )
    op.create_index(
        "idx_balance_adjustment_user_date",
        "balance_adjustments",
        ["user_id", sa.text("date DESC")],
        unique=False,
    )
    op.create_index(
        "idx_balance_adjustment_date_desc",
        "balance_adjustments",
        [sa.text("date DESC")],
        unique=False,
    )
    op.create_index(
        "ix_balance_adjustments_user_id",
        "balance_adjustments",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index("ix_balance_adjustments_user_id", table_name="balance_adjustments")
    op.drop_index("idx_balance_adjustment_date_desc", table_name="balance_adjustments")
    op.drop_index("idx_balance_adjustment_user_date", table_name="balance_adjustments")
    op.drop_index("ix_balance_adjustments_date", table_name="balance_adjustments")
    op.drop_table("balance_adjustments")
