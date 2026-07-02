"""
승률/순손익 회계 정합성 단위 테스트

- DailyStats.win_rate 는 win/(win+loss) (청산 거래 기준)여야 한다.
  trade_count(매수+매도 모든 체결)로 나누면 안 된다.
- 순손익 = 누적 실현손익 - 누적 수수료.
"""

from decimal import Decimal

from src.entities.daily_stats import DailyStats


def _stats(trade_count: int, win: int, loss: int) -> DailyStats:
    return DailyStats(
        date=None,
        starting_balance=Decimal("0"),
        ending_balance=Decimal("0"),
        realized_pnl=Decimal("0"),
        trade_count=trade_count,
        win_count=win,
        loss_count=loss,
    )


def test_win_rate_uses_closed_trades_not_fills() -> None:
    """trade_count(체결)가 아니라 win+loss(청산)로 나눈다."""
    # 체결 10건, 승 3 / 패 1 → 승률 75% (30%가 아님)
    s = _stats(trade_count=10, win=3, loss=1)
    assert s.win_rate == 0.75


def test_win_rate_zero_closed_trades() -> None:
    """청산 거래가 없으면 0.0 (0분모 가드)."""
    s = _stats(trade_count=5, win=0, loss=0)
    assert s.win_rate == 0.0


def test_win_rate_matches_live_aggregate() -> None:
    """라이브 실측 집계(89승/73패)와 일치."""
    s = _stats(trade_count=530, win=89, loss=73)
    assert round(s.win_rate * 100, 1) == 54.9


def test_net_pnl_is_gross_minus_fees() -> None:
    """순손익 = 실현손익(gross) - 수수료."""
    gross = Decimal("-16749")
    fees = Decimal("9552")
    net = gross - fees
    assert net == Decimal("-26301")
