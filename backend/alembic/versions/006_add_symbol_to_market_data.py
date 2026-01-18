"""Add symbol column to market_data table.

Revision ID: 006
Revises: 005
Create Date: 2026-01-18

Changes:
- Add symbol column to market_data table
- Delete existing data (mixed BTC/XRP data cannot be distinguished)
- Add composite index for symbol + timestamp queries
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add symbol column to market_data table."""
    # 1. 기존 데이터 삭제 (BTC/XRP 데이터가 섞여있어 구분 불가)
    op.execute("DELETE FROM market_data")

    # 2. symbol 컬럼 추가
    op.add_column(
        "market_data",
        sa.Column(
            "symbol",
            sa.String(20),
            nullable=False,
            comment="마켓 심볼 (예: KRW-BTC)",
        ),
    )

    # 3. symbol 컬럼에 인덱스 추가
    op.create_index(
        "idx_market_data_symbol",
        "market_data",
        ["symbol"],
    )

    # 4. symbol + timestamp 복합 인덱스 추가
    op.create_index(
        "idx_market_data_symbol_timestamp",
        "market_data",
        ["symbol", sa.text("timestamp DESC")],
    )


def downgrade() -> None:
    """Remove symbol column from market_data table."""
    # 인덱스 삭제
    op.drop_index("idx_market_data_symbol_timestamp", table_name="market_data")
    op.drop_index("idx_market_data_symbol", table_name="market_data")

    # 컬럼 삭제
    op.drop_column("market_data", "symbol")
