"""
룰 기반 하드 손절 (C3) 단위 테스트

ProfitTaker.check_and_execute가 손실률이 stop_loss_pct를 초과하면
AI 신호와 무관하게 전량 매도하고 STOP_LOSS RiskEvent를 기록하는지 검증한다.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.entities import Position, RiskEventType
from src.modules.trading.profit_taker import ProfitTaker


def _position(avg_price: Decimal, quantity: Decimal) -> Position:
    return Position(
        user_id=1,
        symbol="KRW-BTC",
        quantity=quantity,
        avg_buy_price=avg_price,
        current_value=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        profit_tier_reached=0,
        original_quantity=quantity,
    )


def _make_taker(position: Position, current_price: Decimal) -> ProfitTaker:
    session = MagicMock()
    session.commit = AsyncMock()
    private_api = MagicMock()
    public_api = MagicMock()
    ticker = MagicMock()
    ticker.trade_price = current_price
    public_api.get_ticker = AsyncMock(return_value=ticker)

    event_manager = MagicMock()
    event_manager.get_config_value = AsyncMock(return_value=3.0)  # stop_loss_pct
    event_manager.create_risk_event = AsyncMock()

    taker = ProfitTaker(
        session=session,
        private_api=private_api,
        public_api=public_api,
        user_id=1,
        event_manager=event_manager,
    )
    taker._get_position = AsyncMock(return_value=position)
    taker._execute_partial_sell = AsyncMock(return_value=True)
    taker._check_profit_tiers = AsyncMock()
    taker._check_trailing_stop = AsyncMock(return_value=False)
    return taker


@pytest.mark.asyncio
async def test_hard_stoploss_triggers_full_sell() -> None:
    """손실률 -3.5% (손절 3.0% 초과) → 전량 매도 + STOP_LOSS 이벤트, 티어 미도달."""
    position = _position(Decimal("100000000"), Decimal("0.01"))
    current_price = Decimal("96500000")  # -3.5%
    taker = _make_taker(position, current_price)

    await taker.check_and_execute()

    # 전량 매도 1회 (sell_volume == quantity, reason="hard-stoploss")
    taker._execute_partial_sell.assert_awaited_once()
    args, kwargs = taker._execute_partial_sell.call_args
    assert args[0] is position
    assert args[1] == Decimal("0.01")  # 전량
    assert kwargs.get("reason", args[3] if len(args) > 3 else None) == "hard-stoploss"

    # STOP_LOSS RiskEvent 기록
    taker._event_manager.create_risk_event.assert_awaited_once()
    _, ev_kwargs = taker._event_manager.create_risk_event.call_args
    assert ev_kwargs["event_type"] == RiskEventType.STOP_LOSS

    # 손절 시 익절 티어 로직은 실행되지 않음 (early return)
    taker._check_profit_tiers.assert_not_awaited()


@pytest.mark.asyncio
async def test_no_stoploss_above_threshold() -> None:
    """손실률 -2.0% (손절 3.0% 미만) → 손절 매도 없음, 티어 로직 진행."""
    position = _position(Decimal("100000000"), Decimal("0.01"))
    current_price = Decimal("98000000")  # -2.0%
    taker = _make_taker(position, current_price)

    await taker.check_and_execute()

    taker._execute_partial_sell.assert_not_awaited()
    taker._event_manager.create_risk_event.assert_not_awaited()
    # 손절이 아니므로 익절 티어 로직까지 도달
    taker._check_profit_tiers.assert_awaited_once()


@pytest.mark.asyncio
async def test_stoploss_no_event_when_sell_fails() -> None:
    """손절 조건이나 매도 실패 시 RiskEvent를 기록하지 않는다."""
    position = _position(Decimal("100000000"), Decimal("0.01"))
    current_price = Decimal("95000000")  # -5%
    taker = _make_taker(position, current_price)
    taker._execute_partial_sell = AsyncMock(return_value=False)

    await taker.check_and_execute()

    taker._execute_partial_sell.assert_awaited_once()
    taker._event_manager.create_risk_event.assert_not_awaited()
