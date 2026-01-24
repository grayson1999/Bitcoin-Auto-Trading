"""add_avg_cost_at_order_to_orders

주문 시점 평균 매수가 컬럼 추가 - 매도 손익 계산용

Revision ID: 013
Revises: 012
Create Date: 2026-01-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # orders 테이블에 avg_cost_at_order 컬럼 추가
    op.add_column(
        "orders",
        sa.Column(
            "avg_cost_at_order",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
            comment="주문 시점 평균 매수가 (매도 손익 계산용)",
        ),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column("orders", "avg_cost_at_order")
