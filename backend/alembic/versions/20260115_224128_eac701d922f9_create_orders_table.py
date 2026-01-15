"""create_orders_table

Revision ID: eac701d922f9
Revises: 003
Create Date: 2026-01-15 22:41:28.186887
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eac701d922f9'
down_revision: str | None = '003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('signal_id', sa.BigInteger(), nullable=True, comment='연관 AI 신호 ID'),
        sa.Column('order_type', sa.String(length=10), nullable=False, comment='주문 타입 (MARKET/LIMIT)'),
        sa.Column('side', sa.String(length=10), nullable=False, comment='주문 방향 (BUY/SELL)'),
        sa.Column('market', sa.String(length=20), nullable=False, comment='마켓 코드'),
        sa.Column('amount', sa.Numeric(precision=18, scale=8), nullable=False, comment='주문 금액/수량'),
        sa.Column('price', sa.Numeric(precision=18, scale=8), nullable=True, comment='지정가 (시장가 시 NULL)'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='주문 상태'),
        sa.Column('executed_price', sa.Numeric(precision=18, scale=8), nullable=True, comment='체결 가격'),
        sa.Column('executed_amount', sa.Numeric(precision=18, scale=8), nullable=True, comment='체결 금액/수량'),
        sa.Column('fee', sa.Numeric(precision=18, scale=8), nullable=True, comment='수수료'),
        sa.Column('upbit_uuid', sa.String(length=100), nullable=True, comment='Upbit 주문 UUID'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='실패 시 오류 메시지'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='주문 생성 시간'),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True, comment='체결 시간'),
        sa.ForeignKeyConstraint(['signal_id'], ['trading_signals.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('upbit_uuid')
    )

    # Create indexes for orders table
    op.create_index('idx_order_created_desc', 'orders', [sa.literal_column('created_at DESC')], unique=False)
    op.create_index('idx_order_status', 'orders', ['status'], unique=False)
    op.create_index('idx_order_upbit_uuid', 'orders', ['upbit_uuid'], unique=False)
    op.create_index(op.f('ix_orders_signal_id'), 'orders', ['signal_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index(op.f('ix_orders_signal_id'), table_name='orders')
    op.drop_index('idx_order_upbit_uuid', table_name='orders')
    op.drop_index('idx_order_status', table_name='orders')
    op.drop_index('idx_order_created_desc', table_name='orders')

    # Drop orders table
    op.drop_table('orders')
