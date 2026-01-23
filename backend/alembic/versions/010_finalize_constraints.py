"""Finalize constraints - make user_id NOT NULL and add foreign keys.

Revision ID: 010
Revises: 009
Create Date: 2026-01-24

Actions:
- Make user_id NOT NULL on all tables
- Add foreign key constraints
- Update unique constraints (positions, daily_stats)
- Add indexes for user-based queries
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Finalize constraints and foreign keys."""

    # === orders 테이블 ===
    # user_id NOT NULL
    op.alter_column("orders", "user_id", existing_type=sa.BigInteger(), nullable=False)
    # updated_at NOT NULL (기존 값 업데이트)
    op.execute("UPDATE orders SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column(
        "orders", "updated_at", existing_type=sa.DateTime(timezone=True), nullable=False
    )
    # FK 생성
    op.create_foreign_key(
        "fk_orders_user_id", "orders", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_orders_created_by",
        "orders",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_orders_updated_by",
        "orders",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    # 인덱스 추가
    op.create_index("idx_order_user_id", "orders", ["user_id"])
    op.create_index(
        "idx_order_user_created", "orders", ["user_id", sa.text("created_at DESC")]
    )

    # === trading_signals 테이블 ===
    op.alter_column(
        "trading_signals", "user_id", existing_type=sa.BigInteger(), nullable=False
    )
    op.execute(
        "UPDATE trading_signals SET updated_at = created_at WHERE updated_at IS NULL"
    )
    op.alter_column(
        "trading_signals",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_signals_user_id",
        "trading_signals",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_signals_created_by",
        "trading_signals",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_signals_updated_by",
        "trading_signals",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_signal_user_id", "trading_signals", ["user_id"])
    op.create_index(
        "idx_signal_user_created",
        "trading_signals",
        ["user_id", sa.text("created_at DESC")],
    )

    # === positions 테이블 ===
    op.alter_column(
        "positions", "user_id", existing_type=sa.BigInteger(), nullable=False
    )
    op.execute("UPDATE positions SET created_at = updated_at WHERE created_at IS NULL")
    op.alter_column(
        "positions",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_positions_user_id",
        "positions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_positions_created_by",
        "positions",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_positions_updated_by",
        "positions",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    # UNIQUE 제약 변경: symbol -> (user_id, symbol)
    # Note: a97d74808344에서 positions_symbol_key 대신 ix_positions_symbol(unique=True)로 변경됨
    op.drop_index("ix_positions_symbol", "positions")
    op.create_unique_constraint(
        "uq_positions_user_symbol", "positions", ["user_id", "symbol"]
    )
    op.create_index("idx_position_user_symbol", "positions", ["user_id", "symbol"])

    # === daily_stats 테이블 ===
    op.alter_column(
        "daily_stats", "user_id", existing_type=sa.BigInteger(), nullable=False
    )
    op.execute("UPDATE daily_stats SET created_at = NOW() WHERE created_at IS NULL")
    op.execute("UPDATE daily_stats SET updated_at = NOW() WHERE updated_at IS NULL")
    op.alter_column(
        "daily_stats",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "daily_stats",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_daily_stats_user_id",
        "daily_stats",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_daily_stats_created_by",
        "daily_stats",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_daily_stats_updated_by",
        "daily_stats",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    # UNIQUE 제약 변경: date -> (user_id, date)
    op.drop_index("ix_daily_stats_date", "daily_stats")
    op.create_unique_constraint(
        "uq_daily_stats_user_date", "daily_stats", ["user_id", "date"]
    )
    op.create_index(
        "idx_daily_stats_user_date", "daily_stats", ["user_id", sa.text("date DESC")]
    )

    # === risk_events 테이블 ===
    op.alter_column(
        "risk_events", "user_id", existing_type=sa.BigInteger(), nullable=False
    )
    op.execute(
        "UPDATE risk_events SET updated_at = created_at WHERE updated_at IS NULL"
    )
    op.alter_column(
        "risk_events",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_risk_events_user_id",
        "risk_events",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_risk_events_created_by",
        "risk_events",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_risk_events_updated_by",
        "risk_events",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_risk_event_user_id", "risk_events", ["user_id"])
    op.create_index(
        "idx_risk_event_user_created",
        "risk_events",
        ["user_id", sa.text("created_at DESC")],
    )

    # === system_configs 테이블 ===
    op.execute(
        "UPDATE system_configs SET created_at = updated_at WHERE created_at IS NULL"
    )
    op.alter_column(
        "system_configs",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_system_configs_created_by",
        "system_configs",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_system_configs_updated_by",
        "system_configs",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Revert constraints and foreign keys."""
    # system_configs
    op.drop_constraint(
        "fk_system_configs_updated_by", "system_configs", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_system_configs_created_by", "system_configs", type_="foreignkey"
    )
    op.alter_column(
        "system_configs",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )

    # risk_events
    op.drop_index("idx_risk_event_user_created", "risk_events")
    op.drop_index("idx_risk_event_user_id", "risk_events")
    op.drop_constraint("fk_risk_events_updated_by", "risk_events", type_="foreignkey")
    op.drop_constraint("fk_risk_events_created_by", "risk_events", type_="foreignkey")
    op.drop_constraint("fk_risk_events_user_id", "risk_events", type_="foreignkey")
    op.alter_column(
        "risk_events",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "risk_events", "user_id", existing_type=sa.BigInteger(), nullable=True
    )

    # daily_stats
    op.drop_index("idx_daily_stats_user_date", "daily_stats")
    op.drop_constraint("uq_daily_stats_user_date", "daily_stats", type_="unique")
    op.create_index("ix_daily_stats_date", "daily_stats", ["date"], unique=True)
    op.drop_constraint("fk_daily_stats_updated_by", "daily_stats", type_="foreignkey")
    op.drop_constraint("fk_daily_stats_created_by", "daily_stats", type_="foreignkey")
    op.drop_constraint("fk_daily_stats_user_id", "daily_stats", type_="foreignkey")
    op.alter_column(
        "daily_stats",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "daily_stats",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "daily_stats", "user_id", existing_type=sa.BigInteger(), nullable=True
    )

    # positions
    op.drop_index("idx_position_user_symbol", "positions")
    op.drop_constraint("uq_positions_user_symbol", "positions", type_="unique")
    # Note: a97d74808344에서 ix_positions_symbol(unique=True)가 사용됨
    op.create_index("ix_positions_symbol", "positions", ["symbol"], unique=True)
    op.drop_constraint("fk_positions_updated_by", "positions", type_="foreignkey")
    op.drop_constraint("fk_positions_created_by", "positions", type_="foreignkey")
    op.drop_constraint("fk_positions_user_id", "positions", type_="foreignkey")
    op.alter_column(
        "positions",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "positions", "user_id", existing_type=sa.BigInteger(), nullable=True
    )

    # trading_signals
    op.drop_index("idx_signal_user_created", "trading_signals")
    op.drop_index("idx_signal_user_id", "trading_signals")
    op.drop_constraint("fk_signals_updated_by", "trading_signals", type_="foreignkey")
    op.drop_constraint("fk_signals_created_by", "trading_signals", type_="foreignkey")
    op.drop_constraint("fk_signals_user_id", "trading_signals", type_="foreignkey")
    op.alter_column(
        "trading_signals",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "trading_signals", "user_id", existing_type=sa.BigInteger(), nullable=True
    )

    # orders
    op.drop_index("idx_order_user_created", "orders")
    op.drop_index("idx_order_user_id", "orders")
    op.drop_constraint("fk_orders_updated_by", "orders", type_="foreignkey")
    op.drop_constraint("fk_orders_created_by", "orders", type_="foreignkey")
    op.drop_constraint("fk_orders_user_id", "orders", type_="foreignkey")
    op.alter_column(
        "orders", "updated_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    op.alter_column("orders", "user_id", existing_type=sa.BigInteger(), nullable=True)
