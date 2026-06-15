"""
입금/출금 자동 감지 (user_id 버그 수정) 단위 테스트

detect_and_record_adjustment가 user_id를 세팅하고(NOT NULL 회귀가드),
임계값으로 코인 평가변동을 거르며, 출금/중복을 올바로 처리하는지 검증한다.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.portfolio.service import ADJUSTMENT_THRESHOLD, PortfolioService


def _service(existing=None) -> PortfolioService:
    """dedup 조회 결과를 제어할 수 있는 mock 세션 기반 서비스."""
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=existing)
    session.execute = AsyncMock(return_value=result)
    session.add = MagicMock()
    session.flush = AsyncMock()
    return PortfolioService(session)


def test_threshold_is_20000() -> None:
    """임계값이 2만원으로 상향됐는지 (코인 평가변동 오탐 억제)."""
    assert ADJUSTMENT_THRESHOLD == Decimal("20000")


@pytest.mark.asyncio
async def test_deposit_above_threshold_sets_user_id() -> None:
    """3만원 입금 → DEPOSIT 기록, user_id 세팅(회귀가드)."""
    service = _service()
    adj = await service.detect_and_record_adjustment(
        prev_ending_balance=Decimal("132930"),
        current_starting_balance=Decimal("162930"),
        target_date=date(2026, 6, 15),
        user_id=7,
    )
    assert adj is not None
    assert adj.user_id == 7  # NOT NULL - 이 누락이 영구 insert 실패의 원인이었음
    assert adj.amount == Decimal("30000")
    assert adj.adjustment_type == "deposit"


@pytest.mark.asyncio
async def test_coin_swing_below_threshold_ignored() -> None:
    """1.5만원 변동(<2만) → 코인 평가변동으로 보고 무시(None)."""
    service = _service()
    adj = await service.detect_and_record_adjustment(
        prev_ending_balance=Decimal("150000"),
        current_starting_balance=Decimal("165000"),
        target_date=date(2026, 6, 15),
        user_id=1,
    )
    assert adj is None


@pytest.mark.asyncio
async def test_withdrawal_negative() -> None:
    """2.5만원 감소 → WITHDRAWAL 기록."""
    service = _service()
    adj = await service.detect_and_record_adjustment(
        prev_ending_balance=Decimal("160000"),
        current_starting_balance=Decimal("135000"),
        target_date=date(2026, 6, 15),
        user_id=1,
    )
    assert adj is not None
    assert adj.amount == Decimal("-25000")
    assert adj.adjustment_type == "withdrawal"


@pytest.mark.asyncio
async def test_dedup_existing_returns_none() -> None:
    """이미 같은 date+amount 기록 존재 → None(중복 방지)."""
    service = _service(existing=MagicMock())  # 기존 레코드 있음
    adj = await service.detect_and_record_adjustment(
        prev_ending_balance=Decimal("132930"),
        current_starting_balance=Decimal("162930"),
        target_date=date(2026, 6, 15),
        user_id=1,
    )
    assert adj is None
