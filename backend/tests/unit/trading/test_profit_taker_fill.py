"""
ProfitTaker 실체결가 반영 (H4) 단위 테스트

매도 후 ticker가 아닌 실제 Upbit 체결가/체결수량으로 기록하고,
포지션을 실제 체결 수량만큼만 차감하는지 검증한다.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.entities import Position
from src.modules.trading.profit_taker import ProfitTaker


def _position(quantity: Decimal, avg: Decimal) -> Position:
    return Position(
        user_id=1,
        symbol="KRW-BTC",
        quantity=quantity,
        avg_buy_price=avg,
        current_value=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        original_quantity=quantity,
    )


def _make_taker(monitor: MagicMock) -> ProfitTaker:
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    private_api = MagicMock()
    private_api.get_balance = AsyncMock(return_value=Decimal("1"))  # 충분한 잔고
    resp = MagicMock()
    resp.uuid = "sell-uuid-1"
    private_api.place_order = AsyncMock(return_value=resp)

    public_api = MagicMock()

    taker = ProfitTaker(
        session=session,
        private_api=private_api,
        public_api=public_api,
        user_id=1,
        event_manager=MagicMock(),
        order_monitor=monitor,
    )
    taker._update_daily_stats = AsyncMock()
    return taker


@pytest.mark.asyncio
async def test_partial_sell_uses_real_fill_price_and_qty() -> None:
    """실체결가/수량으로 기록하고 실제 체결량(0.005)만 차감."""
    real_price = Decimal("130000000")
    real_filled = Decimal("0.005")  # 의도 0.01 중 실제 0.005만 체결

    def _update_status(order, upbit_response):
        order.mark_executed(
            executed_price=real_price,
            executed_amount=real_filled,
            fee=real_filled * real_price * Decimal("0.0005"),
        )

    monitor = MagicMock()
    monitor.update_order_status = AsyncMock(side_effect=_update_status)
    monitor.poll_order_completion = AsyncMock()

    taker = _make_taker(monitor)
    position = _position(Decimal("0.01"), Decimal("100000000"))

    ok = await taker._execute_partial_sell(
        position, Decimal("0.01"), Decimal("125000000"), reason="profit-take-tier-1"
    )

    assert ok is True
    # 실제 체결 수량(0.005)만 차감 (의도 0.01 아님)
    assert position.quantity == Decimal("0.005")


@pytest.mark.asyncio
async def test_partial_sell_timeout_does_not_adjust_position() -> None:
    """체결 미확인(타임아웃) 시 포지션 미조정 + False 반환."""
    monitor = MagicMock()
    monitor.update_order_status = AsyncMock()  # 체결 안 됨
    monitor.poll_order_completion = AsyncMock()  # 여전히 미체결

    taker = _make_taker(monitor)
    position = _position(Decimal("0.01"), Decimal("100000000"))

    ok = await taker._execute_partial_sell(
        position, Decimal("0.01"), Decimal("125000000"), reason="profit-take-tier-1"
    )

    assert ok is False
    assert position.quantity == Decimal("0.01")  # 미조정
