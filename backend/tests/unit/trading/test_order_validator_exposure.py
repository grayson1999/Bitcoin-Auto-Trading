"""
누적 노출 한도 가드 (H2) 단위 테스트

이미 포지션을 보유한 상태에서 반복 BUY가 max_pct를 초과 누적하지 못하도록
validate_buy_order가 차단하는지 검증한다.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.entities import TradingSignal
from src.modules.risk.service import PositionCheckResult, RiskCheckResult
from src.modules.trading.validator.order_validator import (
    BalanceInfo,
    OrderBlockedReason,
    OrderValidator,
)


def _make_validator() -> OrderValidator:
    risk_service = MagicMock()
    # 단일 주문 한도(check_position_size)는 항상 PASS로 둬서
    # 누적 노출 가드가 단독으로 동작하는지 본다
    risk_service.check_position_size = AsyncMock(
        return_value=PositionCheckResult(
            result=RiskCheckResult.PASS,
            max_amount=Decimal("1000000"),
            requested_amount=Decimal("0"),
            message="ok",
        )
    )
    return OrderValidator(
        private_api=MagicMock(),
        public_api=MagicMock(),
        risk_service=risk_service,
    )


def _signal(confidence: str = "0.6") -> TradingSignal:
    return TradingSignal(
        signal_type="BUY",
        confidence=Decimal(confidence),
        reasoning="test",
    )


@pytest.mark.asyncio
async def test_buy_blocked_when_exposure_exceeds_max() -> None:
    """기존 코인이 이미 ~8%인데 추가 BUY → 누적 한도 초과 차단."""
    # total 1,000,000 / krw 80,000 / coin_value = 920,000 (92%)
    balance = BalanceInfo(
        krw_available=Decimal("80000"),
        krw_locked=Decimal("0"),
        coin_available=Decimal("0.0092"),
        coin_locked=Decimal("0"),
        coin_avg_price=Decimal("100000000"),
        total_krw=Decimal("1000000"),
    )
    validator = _make_validator()

    result = await validator.validate_buy_order(_signal(), balance)

    assert result.is_valid is False
    assert result.blocked_reason == OrderBlockedReason.POSITION_SIZE_EXCEEDED
    assert "누적 포지션 한도" in result.message


@pytest.mark.asyncio
async def test_buy_allowed_when_no_existing_position() -> None:
    """코인 0 + 소액 주문 → 누적 노출 한도 내 → 통과."""
    # total 1,000,000 / 전액 krw → coin_value 0, order ~ max 8%
    balance = BalanceInfo(
        krw_available=Decimal("1000000"),
        krw_locked=Decimal("0"),
        coin_available=Decimal("0"),
        coin_locked=Decimal("0"),
        coin_avg_price=Decimal("0"),
        total_krw=Decimal("1000000"),
    )
    validator = _make_validator()

    result = await validator.validate_buy_order(_signal("0.6"), balance)

    assert result.is_valid is True
    assert result.order_amount is not None
    assert result.order_amount > 0
