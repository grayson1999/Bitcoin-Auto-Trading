"""Create risk management tables.

Revision ID: 003
Revises: 002
Create Date: 2026-01-13

Tables created:
- risk_events: 리스크 이벤트 기록
- daily_stats: 일별 통계
- positions: 포지션 상태
- system_configs: 시스템 설정
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create risk management tables."""
    # === positions 테이블 ===
    op.create_table(
        "positions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "symbol",
            sa.String(20),
            nullable=False,
            comment="심볼 (BTC-KRW)",
        ),
        sa.Column(
            "quantity",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            server_default="0",
            comment="보유 수량",
        ),
        sa.Column(
            "avg_buy_price",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            server_default="0",
            comment="평균 매수가",
        ),
        sa.Column(
            "current_value",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            server_default="0",
            comment="현재 평가금액",
        ),
        sa.Column(
            "unrealized_pnl",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            server_default="0",
            comment="미실현 손익",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="최종 업데이트 시간",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index(
        "idx_position_symbol",
        "positions",
        ["symbol"],
        unique=True,
    )
    op.create_index(
        "idx_position_updated",
        "positions",
        [sa.text("updated_at DESC")],
    )

    # === daily_stats 테이블 ===
    op.create_table(
        "daily_stats",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "date",
            sa.Date(),
            nullable=False,
            comment="거래일",
        ),
        sa.Column(
            "starting_balance",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            comment="시작 잔고 (KRW)",
        ),
        sa.Column(
            "ending_balance",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            comment="종료 잔고 (KRW)",
        ),
        sa.Column(
            "realized_pnl",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            server_default="0",
            comment="실현 손익 (KRW)",
        ),
        sa.Column(
            "trade_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="거래 횟수",
        ),
        sa.Column(
            "win_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="수익 거래 수",
        ),
        sa.Column(
            "loss_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="손실 거래 수",
        ),
        sa.Column(
            "is_trading_halted",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="거래 중단 여부",
        ),
        sa.Column(
            "halt_reason",
            sa.String(100),
            nullable=True,
            comment="중단 사유",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )
    op.create_index(
        "idx_daily_stats_date",
        "daily_stats",
        ["date"],
        unique=True,
    )
    op.create_index(
        "idx_daily_stats_date_desc",
        "daily_stats",
        [sa.text("date DESC")],
    )

    # === system_configs 테이블 ===
    op.create_table(
        "system_configs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "key",
            sa.String(50),
            nullable=False,
            comment="설정 키",
        ),
        sa.Column(
            "value",
            sa.Text(),
            nullable=False,
            comment="설정 값 (JSON)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="최종 수정 시간",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(
        "idx_system_config_key",
        "system_configs",
        ["key"],
        unique=True,
    )
    op.create_index(
        "idx_system_config_updated",
        "system_configs",
        [sa.text("updated_at DESC")],
    )

    # === risk_events 테이블 ===
    # Note: orders 테이블이 아직 없으므로 FK는 나중에 추가
    op.create_table(
        "risk_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "order_id",
            sa.BigInteger(),
            nullable=True,
            comment="연관 주문 ID (orders 테이블 생성 후 FK 추가)",
        ),
        sa.Column(
            "event_type",
            sa.String(20),
            nullable=False,
            comment="이벤트 유형",
        ),
        sa.Column(
            "trigger_value",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
            comment="발동 기준값 (%)",
        ),
        sa.Column(
            "action_taken",
            sa.String(100),
            nullable=False,
            comment="수행된 조치",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="발생 시간",
        ),
        sa.Column(
            "notified",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="슬랙 알림 전송 여부",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_risk_event_order_id",
        "risk_events",
        ["order_id"],
    )
    op.create_index(
        "idx_risk_event_created_at",
        "risk_events",
        ["created_at"],
    )
    op.create_index(
        "idx_risk_event_created_desc",
        "risk_events",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_risk_event_type_created",
        "risk_events",
        ["event_type", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Drop risk management tables."""
    # risk_events
    op.drop_index("idx_risk_event_type_created", table_name="risk_events")
    op.drop_index("idx_risk_event_created_desc", table_name="risk_events")
    op.drop_index("idx_risk_event_created_at", table_name="risk_events")
    op.drop_index("idx_risk_event_order_id", table_name="risk_events")
    op.drop_table("risk_events")

    # system_configs
    op.drop_index("idx_system_config_updated", table_name="system_configs")
    op.drop_index("idx_system_config_key", table_name="system_configs")
    op.drop_table("system_configs")

    # daily_stats
    op.drop_index("idx_daily_stats_date_desc", table_name="daily_stats")
    op.drop_index("idx_daily_stats_date", table_name="daily_stats")
    op.drop_table("daily_stats")

    # positions
    op.drop_index("idx_position_updated", table_name="positions")
    op.drop_index("idx_position_symbol", table_name="positions")
    op.drop_table("positions")
