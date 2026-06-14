"""
변동성 데이터 신선도 가드 (M6) 단위 테스트

데이터 부재/부족/정체 시 PASS(fail-open) 대신 BLOCKED(fail-safe)를
반환하는지 검증한다.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.risk.service import RiskCheckResult, RiskService


def _row(min_p, max_p, count, latest_ts) -> MagicMock:
    row = MagicMock()
    row.min_price = min_p
    row.max_price = max_p
    row.row_count = count
    row.latest_ts = latest_ts
    return row


def _service_with_row(row) -> RiskService:
    db = MagicMock()
    result = MagicMock()
    result.one_or_none = MagicMock(return_value=row)
    db.execute = AsyncMock(return_value=result)
    service = RiskService(db=db)
    service._get_config_value = AsyncMock(return_value=3.0)  # volatility_threshold
    return service


@pytest.mark.asyncio
async def test_no_data_blocks() -> None:
    """데이터 부재 → BLOCKED (fail-safe)."""
    service = _service_with_row(_row(None, None, 0, None))
    result, _pct, msg = await service.check_volatility()
    assert result == RiskCheckResult.BLOCKED
    assert "부재" in msg


@pytest.mark.asyncio
async def test_insufficient_rows_blocks() -> None:
    """기대치 50% 미만 데이터 → BLOCKED."""
    # 5분 윈도우 = 기대 30건, 5건만 있음
    now_ts = datetime.now(UTC)
    service = _service_with_row(_row(Decimal("100"), Decimal("101"), 5, now_ts))
    result, _pct, msg = await service.check_volatility()
    assert result == RiskCheckResult.BLOCKED
    assert "부족" in msg


@pytest.mark.asyncio
async def test_stale_data_blocks() -> None:
    """최신 데이터가 정체(오래됨) → BLOCKED."""
    stale_ts = datetime.now(UTC) - timedelta(seconds=120)  # 2분 전
    service = _service_with_row(_row(Decimal("100"), Decimal("101"), 30, stale_ts))
    result, _pct, msg = await service.check_volatility()
    assert result == RiskCheckResult.BLOCKED
    assert "정체" in msg


@pytest.mark.asyncio
async def test_normal_data_within_threshold_passes() -> None:
    """충분·신선한 데이터 + 변동성 임계 이내 → PASS."""
    fresh_ts = datetime.now(UTC)
    service = _service_with_row(
        _row(Decimal("100"), Decimal("101"), 30, fresh_ts)  # 1% 변동
    )
    result, pct, _msg = await service.check_volatility()
    assert result == RiskCheckResult.PASS
    assert pct == pytest.approx(1.0, abs=0.01)


@pytest.mark.asyncio
async def test_high_volatility_blocks() -> None:
    """충분·신선한 데이터 + 변동성 임계 초과 → BLOCKED."""
    fresh_ts = datetime.now(UTC)
    service = _service_with_row(
        _row(Decimal("100"), Decimal("105"), 30, fresh_ts)  # 5% 변동 > 3%
    )
    service._create_risk_event = AsyncMock()
    service.halt_trading = AsyncMock()
    result, pct, _msg = await service.check_volatility()
    assert result == RiskCheckResult.BLOCKED
    assert pct == pytest.approx(5.0, abs=0.01)
