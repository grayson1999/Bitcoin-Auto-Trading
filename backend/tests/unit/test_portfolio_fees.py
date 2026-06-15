"""
누적 수수료 집계 (UX) 단위 테스트

PortfolioService._calculate_total_fees_paid가 주문 fee 합계를 반환하고,
값이 없으면 0을 반환하는지 검증한다.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.portfolio.service import PortfolioService


def _service_with_fee_sum(value) -> PortfolioService:
    session = MagicMock()
    result = MagicMock()
    result.scalar = MagicMock(return_value=value)
    session.execute = AsyncMock(return_value=result)
    return PortfolioService(session)


@pytest.mark.asyncio
async def test_total_fees_sums() -> None:
    """fee 합계가 그대로 반환된다."""
    service = _service_with_fee_sum(Decimal("1234.56"))
    assert await service._calculate_total_fees_paid() == Decimal("1234.56")


@pytest.mark.asyncio
async def test_total_fees_none_returns_zero() -> None:
    """주문이 없어 SUM이 None이면 0을 반환."""
    service = _service_with_fee_sum(None)
    assert await service._calculate_total_fees_paid() == Decimal("0")
