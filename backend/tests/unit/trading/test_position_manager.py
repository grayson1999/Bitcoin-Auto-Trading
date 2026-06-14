"""
PositionManager 회계 로직 단위 테스트

매수/매도 체결 후 포지션 수량·평균매수가 계산을 검증한다.
특히 C4 회귀 방지: order.executed_amount는 항상 '체결 코인 수량'이며
KRW 금액이 아니다 (order_monitor가 Upbit executed_volume을 저장).
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.entities import Order, OrderSide, OrderStatus, OrderType, Position
from src.modules.trading.position import PositionManager


def _make_order(side: OrderSide, coin_qty: Decimal, price: Decimal) -> Order:
    """체결된 주문 객체 생성 (executed_amount = 코인 수량)."""
    order = Order(
        user_id=1,
        side=side.value,
        order_type=OrderType.MARKET.value,
        market="KRW-BTC",
        status=OrderStatus.EXECUTED.value,
        executed_price=price,
        executed_amount=coin_qty,  # 코인 수량 (NOT KRW)
    )
    return order


def _make_manager(position: Position | None) -> PositionManager:
    """get_position과 public_api를 모킹한 PositionManager."""
    session = MagicMock()
    session.add = MagicMock()
    public_api = MagicMock()
    # update_value가 네트워크를 타지 않도록 get_ticker mock
    ticker = MagicMock()
    ticker.trade_price = Decimal("100000000")
    public_api.get_ticker = AsyncMock(return_value=ticker)
    validator = MagicMock()

    manager = PositionManager(
        session=session,
        public_api=public_api,
        validator=validator,
        user_id=1,
    )
    manager.get_position = AsyncMock(return_value=position)
    return manager


def _empty_position() -> Position:
    return Position(
        user_id=1,
        symbol="KRW-BTC",
        quantity=Decimal("0"),
        avg_buy_price=Decimal("0"),
        current_value=Decimal("0"),
        unrealized_pnl=Decimal("0"),
    )


@pytest.mark.asyncio
async def test_new_buy_sets_quantity_and_avg_price() -> None:
    """신규 매수: 코인 수량과 평단가가 정확히 기록된다 (더스트 손상 없음)."""
    position = _empty_position()
    manager = _make_manager(position)
    order = _make_order(OrderSide.BUY, Decimal("0.01"), Decimal("100000000"))

    await manager.update_position_after_order(order)

    assert position.quantity == Decimal("0.01")
    assert position.avg_buy_price == Decimal("100000000")
    assert position.original_quantity == Decimal("0.01")
    assert position.profit_tier_reached == 0
    assert position.peak_price is None
    assert position.trailing_stop_active is False


@pytest.mark.asyncio
async def test_add_buy_recomputes_weighted_avg() -> None:
    """분할 매수: 가중 평균 매수가가 정확히 계산된다."""
    position = _empty_position()
    position.quantity = Decimal("0.01")
    position.avg_buy_price = Decimal("100000000")
    position.original_quantity = Decimal("0.01")
    manager = _make_manager(position)
    order = _make_order(OrderSide.BUY, Decimal("0.01"), Decimal("120000000"))

    await manager.update_position_after_order(order)

    assert position.quantity == Decimal("0.02")
    # (0.01*1억 + 0.01*1.2억) / 0.02 = 1.1억
    assert position.avg_buy_price == Decimal("110000000")
    assert position.original_quantity == Decimal("0.02")


@pytest.mark.asyncio
async def test_partial_sell_reduces_quantity_keeps_avg() -> None:
    """부분 매도: 수량만 줄고 평단가는 유지된다."""
    position = _empty_position()
    position.quantity = Decimal("0.02")
    position.avg_buy_price = Decimal("110000000")
    manager = _make_manager(position)
    order = _make_order(OrderSide.SELL, Decimal("0.01"), Decimal("130000000"))

    await manager.update_position_after_order(order)

    assert position.quantity == Decimal("0.01")
    assert position.avg_buy_price == Decimal("110000000")


@pytest.mark.asyncio
async def test_full_sell_resets_position() -> None:
    """전량 매도: 포지션이 완전히 초기화된다."""
    position = _empty_position()
    position.quantity = Decimal("0.01")
    position.avg_buy_price = Decimal("110000000")
    position.profit_tier_reached = 2
    position.original_quantity = Decimal("0.01")
    manager = _make_manager(position)
    order = _make_order(OrderSide.SELL, Decimal("0.01"), Decimal("130000000"))

    await manager.update_position_after_order(order)

    assert position.quantity == Decimal("0")
    assert position.avg_buy_price == Decimal("0")
    assert position.profit_tier_reached == 0
    assert position.peak_price is None
    assert position.trailing_stop_active is False
    assert position.original_quantity is None
