"""Create backtest_results table.

Revision ID: 005
Revises: 004
Create Date: 2026-01-16

Tables created:
- backtest_results: 백테스트 결과
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create backtest_results table."""
    op.create_table(
        "backtest_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
            comment="백테스트 이름",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="PENDING",
            comment="백테스트 상태 (PENDING/RUNNING/COMPLETED/FAILED)",
        ),
        # 기간 설정
        sa.Column(
            "start_date",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="백테스트 시작 날짜",
        ),
        sa.Column(
            "end_date",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="백테스트 종료 날짜",
        ),
        # 자본금
        sa.Column(
            "initial_capital",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            comment="초기 자본금 (KRW)",
        ),
        sa.Column(
            "final_capital",
            sa.Numeric(precision=18, scale=2),
            nullable=True,
            comment="최종 자본금 (KRW)",
        ),
        # 성과 지표
        sa.Column(
            "total_return_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="총 수익률 (%)",
        ),
        sa.Column(
            "max_drawdown_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="최대 낙폭 MDD (%)",
        ),
        sa.Column(
            "win_rate_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="승률 (%)",
        ),
        sa.Column(
            "profit_factor",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="손익비 (총이익/총손실)",
        ),
        # 거래 통계
        sa.Column(
            "total_trades",
            sa.Integer(),
            nullable=True,
            server_default="0",
            comment="총 거래 횟수",
        ),
        sa.Column(
            "winning_trades",
            sa.Integer(),
            nullable=True,
            server_default="0",
            comment="승리 거래 횟수",
        ),
        sa.Column(
            "losing_trades",
            sa.Integer(),
            nullable=True,
            server_default="0",
            comment="패배 거래 횟수",
        ),
        # 추가 지표
        sa.Column(
            "avg_profit_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="평균 수익 거래 수익률 (%)",
        ),
        sa.Column(
            "avg_loss_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="평균 손실 거래 손실률 (%)",
        ),
        sa.Column(
            "sharpe_ratio",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="샤프 비율 (위험 조정 수익률)",
        ),
        # 거래 내역
        sa.Column(
            "trade_history",
            sa.Text(),
            nullable=True,
            comment="거래 내역 (JSON)",
        ),
        # 오류 정보
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="실패 시 오류 메시지",
        ),
        # 시간 정보
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="생성 시간",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="완료 시간",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 인덱스 생성
    op.create_index(
        "idx_backtest_created_desc",
        "backtest_results",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_backtest_status",
        "backtest_results",
        ["status"],
    )


def downgrade() -> None:
    """Drop backtest_results table."""
    op.drop_index("idx_backtest_status", table_name="backtest_results")
    op.drop_index("idx_backtest_created_desc", table_name="backtest_results")
    op.drop_table("backtest_results")
