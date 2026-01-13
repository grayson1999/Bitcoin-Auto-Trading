"""Create trading_signals table.

Revision ID: 002
Revises: 001
Create Date: 2026-01-13

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create trading_signals table for storing AI-generated trading signals."""
    op.create_table(
        "trading_signals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "market_data_id",
            sa.BigInteger(),
            nullable=True,
            comment="Reference to market data used for analysis",
        ),
        sa.Column(
            "signal_type",
            sa.String(10),
            nullable=False,
            comment="Signal type (BUY/HOLD/SELL)",
        ),
        sa.Column(
            "confidence",
            sa.Numeric(precision=3, scale=2),
            nullable=False,
            comment="Confidence score (0-1)",
        ),
        sa.Column(
            "reasoning",
            sa.Text(),
            nullable=False,
            comment="AI analysis reasoning",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Signal creation time",
        ),
        sa.Column(
            "model_name",
            sa.String(50),
            nullable=False,
            comment="AI model name used",
        ),
        sa.Column(
            "input_tokens",
            sa.Integer(),
            nullable=False,
            default=0,
            comment="Input tokens count",
        ),
        sa.Column(
            "output_tokens",
            sa.Integer(),
            nullable=False,
            default=0,
            comment="Output tokens count",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["market_data_id"],
            ["market_data.id"],
            ondelete="SET NULL",
        ),
    )

    # Create indexes for efficient querying
    op.create_index(
        "idx_signal_market_data_id",
        "trading_signals",
        ["market_data_id"],
    )
    op.create_index(
        "idx_signal_created_at",
        "trading_signals",
        ["created_at"],
    )
    op.create_index(
        "idx_signal_created_desc",
        "trading_signals",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_signal_type_created",
        "trading_signals",
        ["signal_type", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Drop trading_signals table."""
    op.drop_index("idx_signal_type_created", table_name="trading_signals")
    op.drop_index("idx_signal_created_desc", table_name="trading_signals")
    op.drop_index("idx_signal_created_at", table_name="trading_signals")
    op.drop_index("idx_signal_market_data_id", table_name="trading_signals")
    op.drop_table("trading_signals")
