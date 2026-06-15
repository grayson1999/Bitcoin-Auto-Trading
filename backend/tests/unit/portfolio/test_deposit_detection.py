"""
Upbit 원장 입금 동기화 단위 테스트

sync_deposits_from_upbit가 봇 시작일 이후 입금만 기록하고(중복 회피),
user_id를 세팅하며(NOT NULL 회귀가드), date+amount로 중복을 방지하는지 검증한다.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.portfolio.service import PortfolioService


def _dep(amount: str, created_at: str, uuid: str = "u") -> SimpleNamespace:
    """UpbitDeposit 유사 객체."""
    return SimpleNamespace(
        amount=Decimal(amount),
        created_at=created_at,
        uuid=uuid,
        txid=None,
        currency="KRW",
        state="ACCEPTED",
    )


def _service(first_stats, existing_amounts=None):
    """봇 시작일 + 기존 BalanceAdjustment(date+amount) 중복 조회를 mock."""
    existing_amounts = existing_amounts or set()
    session = MagicMock()
    added = []
    session.add = MagicMock(side_effect=lambda obj: added.append(obj))
    session.flush = AsyncMock()

    # 첫 execute() = 봇 시작일 조회, 이후 = 중복 조회
    first_result = MagicMock()
    first_result.scalar_one_or_none = MagicMock(return_value=first_stats)

    def make_dedup(amount):
        r = MagicMock()
        r.scalar_one_or_none = MagicMock(
            return_value=object() if amount in existing_amounts else None
        )
        return r

    # execute 호출 순서: [0]=봇시작일, 그 다음은 각 입금의 dedup 조회
    calls = {"n": 0}
    dedup_amounts = []

    async def execute_side(stmt):
        if calls["n"] == 0:
            calls["n"] += 1
            return first_result
        amt = dedup_amounts.pop(0) if dedup_amounts else None
        return make_dedup(amt)

    session.execute = AsyncMock(side_effect=execute_side)
    svc = PortfolioService(session)
    return svc, added, dedup_amounts


@pytest.mark.asyncio
async def test_records_only_deposits_after_bot_start() -> None:
    """봇 시작일(1/25) 이후 입금만 기록, 시작일·이전은 제외."""
    first = SimpleNamespace(date=date(2026, 1, 25), user_id=3)
    svc, added, dedup_amounts = _service(first)
    # dedup 조회는 '이후' 입금 2건에 대해서만 일어남
    dedup_amounts.extend([Decimal("30000"), Decimal("30000")])

    deposits = [
        _dep("30000", "2026-01-20T10:00:00+09:00"),  # 시작 전 → 제외
        _dep("30000", "2026-01-25T10:00:00+09:00"),  # 시작 당일 → 제외
        _dep("30000", "2026-04-27T10:00:00+09:00"),  # 이후 → 기록
        _dep("30000", "2026-06-15T10:00:00+09:00"),  # 이후 → 기록
    ]
    with patch("src.modules.portfolio.service.get_upbit_private_api") as mock_api:
        mock_api.return_value.get_krw_deposits = AsyncMock(return_value=deposits)
        recorded = await svc.sync_deposits_from_upbit()

    assert recorded == 2
    assert all(a.user_id == 3 for a in added)  # NOT NULL 회귀가드
    assert all(a.adjustment_type == "deposit" for a in added)


@pytest.mark.asyncio
async def test_dedup_skips_existing() -> None:
    """이미 기록된(date+amount) 입금은 스킵."""
    first = SimpleNamespace(date=date(2026, 1, 25), user_id=1)
    svc, added, dedup_amounts = _service(first, existing_amounts={Decimal("30000")})
    dedup_amounts.append(Decimal("30000"))

    deposits = [_dep("30000", "2026-04-27T10:00:00+09:00")]
    with patch("src.modules.portfolio.service.get_upbit_private_api") as mock_api:
        mock_api.return_value.get_krw_deposits = AsyncMock(return_value=deposits)
        recorded = await svc.sync_deposits_from_upbit()

    assert recorded == 0
    assert added == []


@pytest.mark.asyncio
async def test_no_daily_stats_returns_zero() -> None:
    """봇 시작 DailyStats 없으면 0 반환(안전)."""
    svc, _added, _ = _service(None)
    recorded = await svc.sync_deposits_from_upbit()
    assert recorded == 0
