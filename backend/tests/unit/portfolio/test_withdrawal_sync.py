"""
Upbit 원장 출금 동기화 단위 테스트

sync_withdrawals_from_upbit가 봇 시작일 이후 출금만 기록하고,
계좌에서 실제 빠져나간 총액(amount+fee)을 음수로 기록하며,
date+amount로 중복을 방지하는지 검증한다.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.portfolio.service import PortfolioService


def _wd(amount: str, fee: str, created_at: str, uuid: str = "w") -> SimpleNamespace:
    """UpbitWithdrawal 유사 객체."""
    return SimpleNamespace(
        amount=Decimal(amount),
        fee=Decimal(fee),
        created_at=created_at,
        uuid=uuid,
        txid=None,
        currency="KRW",
        state="DONE",
        done_at=created_at,
    )


def _service(first_stats, existing_amounts=None):
    """봇 시작일 + 기존 BalanceAdjustment(date+amount) 중복 조회를 mock."""
    existing_amounts = existing_amounts or set()
    session = MagicMock()
    added = []
    session.add = MagicMock(side_effect=lambda obj: added.append(obj))
    session.flush = AsyncMock()

    first_result = MagicMock()
    first_result.scalar_one_or_none = MagicMock(return_value=first_stats)

    def make_dedup(amount):
        r = MagicMock()
        r.scalar_one_or_none = MagicMock(
            return_value=object() if amount in existing_amounts else None
        )
        return r

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
async def test_records_withdrawal_with_fee_as_negative() -> None:
    """출금은 -(amount+fee) 음수로 기록되고 봇 시작일 이후만 대상."""
    first = SimpleNamespace(date=date(2026, 1, 25), user_id=7)
    svc, added, dedup_amounts = _service(first)
    # 이후 출금 1건 → dedup 조회 1회 (기록될 음수 금액)
    dedup_amounts.append(Decimal("-11000"))

    withdraws = [
        _wd("10000", "1000", "2026-01-20T10:00:00+09:00"),  # 시작 전 → 제외
        _wd("10000", "1000", "2026-05-01T10:00:00+09:00"),  # 이후 → 기록
    ]
    with patch("src.modules.portfolio.service.get_upbit_private_api") as mock_api:
        mock_api.return_value.get_krw_withdraws = AsyncMock(return_value=withdraws)
        recorded = await svc.sync_withdrawals_from_upbit()

    assert recorded == 1
    assert added[0].amount == Decimal("-11000")  # -(amount + fee)
    assert added[0].user_id == 7
    assert added[0].adjustment_type == "withdrawal"


@pytest.mark.asyncio
async def test_dedup_skips_existing_withdrawal() -> None:
    """이미 기록된(date+amount) 출금은 스킵."""
    first = SimpleNamespace(date=date(2026, 1, 25), user_id=1)
    svc, added, dedup_amounts = _service(
        first, existing_amounts={Decimal("-11000")}
    )
    dedup_amounts.append(Decimal("-11000"))

    withdraws = [_wd("10000", "1000", "2026-05-01T10:00:00+09:00")]
    with patch("src.modules.portfolio.service.get_upbit_private_api") as mock_api:
        mock_api.return_value.get_krw_withdraws = AsyncMock(return_value=withdraws)
        recorded = await svc.sync_withdrawals_from_upbit()

    assert recorded == 0
    assert added == []


@pytest.mark.asyncio
async def test_no_daily_stats_returns_zero() -> None:
    """봇 시작 DailyStats 없으면 0 반환(안전)."""
    svc, _added, _ = _service(None)
    recorded = await svc.sync_withdrawals_from_upbit()
    assert recorded == 0
