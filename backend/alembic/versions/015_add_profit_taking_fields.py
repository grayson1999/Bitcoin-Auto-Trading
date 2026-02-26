"""add_profit_taking_fields

Position: profit_tier_reached, peak_price, trailing_stop_active, original_quantity
TradingSignal: action_score

Revision ID: 015
Revises: 014
Create Date: 2026-02-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "015"
down_revision: str | None = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Position: 익절 추적 필드
    op.add_column(
        "positions",
        sa.Column(
            "profit_tier_reached",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="최고 익절 단계 (0=미실행, 1/2/3)",
        ),
    )
    op.add_column(
        "positions",
        sa.Column(
            "peak_price",
            sa.Numeric(18, 8),
            nullable=True,
            comment="진입 후 최고가 (트레일링 스탑용)",
        ),
    )
    op.add_column(
        "positions",
        sa.Column(
            "trailing_stop_active",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="트레일링 스탑 활성 여부",
        ),
    )
    op.add_column(
        "positions",
        sa.Column(
            "original_quantity",
            sa.Numeric(18, 8),
            nullable=True,
            comment="진입 시 원래 수량 (부분 매도 기준)",
        ),
    )

    # TradingSignal: action_score
    op.add_column(
        "trading_signals",
        sa.Column(
            "action_score",
            sa.Float(),
            nullable=True,
            comment="AI action_score (-1.0~+1.0)",
        ),
    )


def downgrade() -> None:
    op.drop_column("trading_signals", "action_score")
    op.drop_column("positions", "original_quantity")
    op.drop_column("positions", "trailing_stop_active")
    op.drop_column("positions", "peak_price")
    op.drop_column("positions", "profit_tier_reached")
