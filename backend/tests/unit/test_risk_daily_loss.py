"""
일일 손실 한도 평가액 기준 (H1) 단위 테스트

current_equity(평가자산)가 주어지면 실현+미실현을 모두 반영해
realized_pnl이 0이어도 평가손실로 halt가 걸리는지 검증한다.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.entities import DailyStats
from src.modules.risk.service import RiskCheckResult, RiskService


def _make_service(daily_stats: DailyStats) -> RiskService:
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=daily_stats)
    db.execute = AsyncMock(return_value=result)

    service = RiskService(db=db)
    service._get_config_value = AsyncMock(return_value=3.0)  # daily_loss_limit_pct
    service._create_risk_event = AsyncMock()
    return service


def _daily_stats() -> DailyStats:
    return DailyStats(
        starting_balance=Decimal("1000000"),
        realized_pnl=Decimal("0"),  # 실현손익 0 (매도 안 함)
        is_trading_halted=False,
    )


@pytest.mark.asyncio
async def test_equity_loss_triggers_halt_when_realized_zero() -> None:
    """평가자산 -4% (실현 0)인데도 평가손실로 halt 발동."""
    stats = _daily_stats()
    service = _make_service(stats)

    result, _msg = await service.check_daily_loss_limit(
        current_equity=Decimal("960000")  # -4%
    )

    assert result == RiskCheckResult.BLOCKED
    assert stats.is_trading_halted is True


@pytest.mark.asyncio
async def test_realized_only_fallback_when_no_equity() -> None:
    """current_equity 미제공 → 실현 전용 폴백 (realized 0 → PASS)."""
    stats = _daily_stats()
    service = _make_service(stats)

    result, _msg = await service.check_daily_loss_limit()

    assert result == RiskCheckResult.PASS
    assert stats.is_trading_halted is False


@pytest.mark.asyncio
async def test_equity_profit_passes() -> None:
    """평가자산 +2% → PASS."""
    stats = _daily_stats()
    service = _make_service(stats)

    result, _msg = await service.check_daily_loss_limit(
        current_equity=Decimal("1020000")  # +2%
    )

    assert result == RiskCheckResult.PASS
    assert stats.is_trading_halted is False
