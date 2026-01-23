"""Add audit columns to existing tables.

Revision ID: 008
Revises: 007
Create Date: 2026-01-24

Columns added:
- user_id, created_by, updated_by to: orders, trading_signals, positions, daily_stats, risk_events
- created_at, created_by, updated_by to: system_configs
- updated_at to: orders, trading_signals, risk_events
- created_at to: positions, daily_stats
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add audit columns to all tables (nullable initially)."""

    # === orders 테이블 ===
    op.add_column(
        "orders",
        sa.Column(
            "user_id", sa.BigInteger(), nullable=True, comment="소유자 사용자 ID"
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
            comment="주문 수정 시간",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "created_by", sa.BigInteger(), nullable=True, comment="생성자 사용자 ID"
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "updated_by", sa.BigInteger(), nullable=True, comment="수정자 사용자 ID"
        ),
    )

    # === trading_signals 테이블 ===
    op.add_column(
        "trading_signals",
        sa.Column(
            "user_id", sa.BigInteger(), nullable=True, comment="소유자 사용자 ID"
        ),
    )
    op.add_column(
        "trading_signals",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
            comment="신호 수정 시간",
        ),
    )
    op.add_column(
        "trading_signals",
        sa.Column(
            "created_by", sa.BigInteger(), nullable=True, comment="생성자 사용자 ID"
        ),
    )
    op.add_column(
        "trading_signals",
        sa.Column(
            "updated_by", sa.BigInteger(), nullable=True, comment="수정자 사용자 ID"
        ),
    )

    # === positions 테이블 ===
    op.add_column(
        "positions",
        sa.Column(
            "user_id", sa.BigInteger(), nullable=True, comment="소유자 사용자 ID"
        ),
    )
    op.add_column(
        "positions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
            comment="생성 시간",
        ),
    )
    op.add_column(
        "positions",
        sa.Column(
            "created_by", sa.BigInteger(), nullable=True, comment="생성자 사용자 ID"
        ),
    )
    op.add_column(
        "positions",
        sa.Column(
            "updated_by", sa.BigInteger(), nullable=True, comment="수정자 사용자 ID"
        ),
    )

    # === daily_stats 테이블 ===
    op.add_column(
        "daily_stats",
        sa.Column(
            "user_id", sa.BigInteger(), nullable=True, comment="소유자 사용자 ID"
        ),
    )
    op.add_column(
        "daily_stats",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
            comment="생성 시간",
        ),
    )
    op.add_column(
        "daily_stats",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
            comment="수정 시간",
        ),
    )
    op.add_column(
        "daily_stats",
        sa.Column(
            "created_by", sa.BigInteger(), nullable=True, comment="생성자 사용자 ID"
        ),
    )
    op.add_column(
        "daily_stats",
        sa.Column(
            "updated_by", sa.BigInteger(), nullable=True, comment="수정자 사용자 ID"
        ),
    )

    # === risk_events 테이블 ===
    op.add_column(
        "risk_events",
        sa.Column(
            "user_id", sa.BigInteger(), nullable=True, comment="소유자 사용자 ID"
        ),
    )
    op.add_column(
        "risk_events",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
            comment="수정 시간",
        ),
    )
    op.add_column(
        "risk_events",
        sa.Column(
            "created_by", sa.BigInteger(), nullable=True, comment="생성자 사용자 ID"
        ),
    )
    op.add_column(
        "risk_events",
        sa.Column(
            "updated_by", sa.BigInteger(), nullable=True, comment="수정자 사용자 ID"
        ),
    )

    # === system_configs 테이블 ===
    op.add_column(
        "system_configs",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
            comment="생성 시간",
        ),
    )
    op.add_column(
        "system_configs",
        sa.Column(
            "created_by", sa.BigInteger(), nullable=True, comment="생성자 사용자 ID"
        ),
    )
    op.add_column(
        "system_configs",
        sa.Column(
            "updated_by", sa.BigInteger(), nullable=True, comment="수정자 사용자 ID"
        ),
    )


def downgrade() -> None:
    """Remove audit columns from all tables."""
    # system_configs
    op.drop_column("system_configs", "updated_by")
    op.drop_column("system_configs", "created_by")
    op.drop_column("system_configs", "created_at")

    # risk_events
    op.drop_column("risk_events", "updated_by")
    op.drop_column("risk_events", "created_by")
    op.drop_column("risk_events", "updated_at")
    op.drop_column("risk_events", "user_id")

    # daily_stats
    op.drop_column("daily_stats", "updated_by")
    op.drop_column("daily_stats", "created_by")
    op.drop_column("daily_stats", "updated_at")
    op.drop_column("daily_stats", "created_at")
    op.drop_column("daily_stats", "user_id")

    # positions
    op.drop_column("positions", "updated_by")
    op.drop_column("positions", "created_by")
    op.drop_column("positions", "created_at")
    op.drop_column("positions", "user_id")

    # trading_signals
    op.drop_column("trading_signals", "updated_by")
    op.drop_column("trading_signals", "created_by")
    op.drop_column("trading_signals", "updated_at")
    op.drop_column("trading_signals", "user_id")

    # orders
    op.drop_column("orders", "updated_by")
    op.drop_column("orders", "created_by")
    op.drop_column("orders", "updated_at")
    op.drop_column("orders", "user_id")
