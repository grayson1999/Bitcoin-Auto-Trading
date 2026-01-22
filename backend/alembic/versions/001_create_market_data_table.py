"""Create market_data table.

Revision ID: 001
Revises:
Create Date: 2026-01-11

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create market_data table for storing real-time market data."""
    op.create_table(
        "market_data",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column(
            "price",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            comment="Current price in KRW",
        ),
        sa.Column(
            "volume",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            comment="24-hour trading volume",
        ),
        sa.Column(
            "high_price",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            comment="24-hour high price",
        ),
        sa.Column(
            "low_price",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            comment="24-hour low price",
        ),
        sa.Column(
            "trade_count",
            sa.Integer(),
            nullable=False,
            comment="Number of trades",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for efficient querying
    op.create_index(
        "idx_market_data_timestamp_desc",
        "market_data",
        [sa.text("timestamp DESC")],
    )
    op.create_index(
        "idx_market_data_date",
        "market_data",
        ["timestamp"],
    )


def downgrade() -> None:
    """Drop market_data table."""
    op.drop_index("idx_market_data_date", table_name="market_data")
    op.drop_index("idx_market_data_timestamp_desc", table_name="market_data")
    op.drop_table("market_data")
