"""
회계 정합성 (M11/M1/M4) 단위 테스트

- M11: execute_from_signal 멱등성 (동일 signal에 주문 있으면 스킵)
- M1: sync_pending_orders가 체결 전환 주문 리스트 반환
- M4: ProfitTaker 클램프 매도 후 Upbit 실잔고로 재동기화
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.entities import Order, OrderStatus, Position

# === M4: 클램프 후 재동기화 ===


def _clamp_position(quantity: Decimal) -> Position:
    return Position(
        user_id=1,
        symbol="KRW-BTC",
        quantity=quantity,
        avg_buy_price=Decimal("100000000"),
        current_value=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        original_quantity=quantity,
    )


@pytest.mark.asyncio
async def test_profit_taker_resyncs_on_clamp() -> None:
    """DB 보유량 > Upbit 실잔고(유령 수량) → 매도 후 실잔고로 재동기화."""
    from src.modules.trading.profit_taker import ProfitTaker

    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    private_api = MagicMock()
    # DB는 1.0 BTC인데 Upbit 실잔고는 0.5 (유령 0.5)
    # 매도 전 잔고 0.5, 매도 후 잔고 0.0 (전량 체결)
    private_api.get_balance = AsyncMock(side_effect=[Decimal("0.5"), Decimal("0.0")])
    resp = MagicMock()
    resp.uuid = "uuid-1"
    private_api.place_order = AsyncMock(return_value=resp)

    monitor = MagicMock()

    def _exec(order, upbit_response):
        order.mark_executed(
            executed_price=Decimal("130000000"),
            executed_amount=Decimal("0.5"),
            fee=Decimal("0"),
        )

    monitor.update_order_status = AsyncMock(side_effect=_exec)
    monitor.poll_order_completion = AsyncMock()

    taker = ProfitTaker(
        session=session,
        private_api=private_api,
        public_api=MagicMock(),
        user_id=1,
        event_manager=MagicMock(),
        order_monitor=monitor,
    )
    taker._update_daily_stats = AsyncMock()

    position = _clamp_position(Decimal("1.0"))  # DB 1.0, Upbit 0.5
    ok = await taker._execute_partial_sell(
        position, Decimal("1.0"), Decimal("125000000"), reason="hard-stoploss"
    )

    assert ok is True
    # 유령 수량(1.0 - 0.5 = 0.5)이 남지 않고 Upbit 실잔고 0.0으로 재동기화
    assert position.quantity == Decimal("0")


# === M11: execute_from_signal 멱등성 ===


@pytest.mark.asyncio
async def test_execute_from_signal_skips_when_order_exists() -> None:
    """동일 signal_id에 EXECUTED/PENDING 주문이 있으면 중복 실행 스킵."""
    from src.modules.trading.service import TradingService

    existing_order = Order(
        id=99,
        user_id=1,
        signal_id=42,
        side="BUY",
        order_type="MARKET",
        market="KRW-BTC",
        status=OrderStatus.EXECUTED.value,
    )

    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=existing_order)
    session.execute = AsyncMock(return_value=exec_result)

    # TradingService를 최소 구성으로 생성 (검증 로직은 호출 전 멱등성에서 차단)
    service = TradingService.__new__(TradingService)
    service._session = session

    signal = MagicMock()
    signal.id = 42
    signal.signal_type = "BUY"
    signal.user_id = 1
    signal.confidence = Decimal("0.6")

    result = await service.execute_from_signal(signal)

    assert result.success is True
    assert "중복" in result.message or "이미" in result.message
    assert result.order is existing_order
