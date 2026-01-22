"""add_signal_performance_fields

trading_signals 테이블에 성과 추적 필드 추가

Revision ID: 004
Revises: eac701d922f9
Create Date: 2026-01-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "eac701d922f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """trading_signals 테이블에 성과 추적 필드 추가."""
    # 신호 생성 시 가격
    op.add_column(
        "trading_signals",
        sa.Column(
            "price_at_signal",
            sa.Numeric(18, 8),
            nullable=True,
            comment="신호 생성 시 가격",
        ),
    )

    # 4시간 후 가격
    op.add_column(
        "trading_signals",
        sa.Column(
            "price_after_4h",
            sa.Numeric(18, 8),
            nullable=True,
            comment="4시간 후 가격",
        ),
    )

    # 24시간 후 가격
    op.add_column(
        "trading_signals",
        sa.Column(
            "price_after_24h",
            sa.Numeric(18, 8),
            nullable=True,
            comment="24시간 후 가격",
        ),
    )

    # 성과 평가 완료 여부
    op.add_column(
        "trading_signals",
        sa.Column(
            "outcome_evaluated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="성과 평가 완료 여부",
        ),
    )

    # 신호 정확성
    op.add_column(
        "trading_signals",
        sa.Column(
            "outcome_correct",
            sa.Boolean(),
            nullable=True,
            comment="신호 정확성 (방향 일치 여부)",
        ),
    )

    # 기술적 지표 스냅샷
    op.add_column(
        "trading_signals",
        sa.Column(
            "technical_snapshot",
            sa.Text(),
            nullable=True,
            comment="기술적 지표 스냅샷 (JSON)",
        ),
    )


def downgrade() -> None:
    """성과 추적 필드 제거."""
    op.drop_column("trading_signals", "technical_snapshot")
    op.drop_column("trading_signals", "outcome_correct")
    op.drop_column("trading_signals", "outcome_evaluated")
    op.drop_column("trading_signals", "price_after_24h")
    op.drop_column("trading_signals", "price_after_4h")
    op.drop_column("trading_signals", "price_at_signal")
