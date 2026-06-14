"""
실제 24h 등락률 (M12) 단위 테스트

parse_ticker가 prev_closing_price / signed_change_rate를 추출하는지,
누락 시 None으로 처리하는지 검증한다.
"""

from decimal import Decimal

from src.clients.upbit.common import parse_ticker


def _base_ticker() -> dict:
    return {
        "market": "KRW-BTC",
        "trade_price": 101000000,
        "acc_trade_volume_24h": 1234.5,
        "high_price": 102000000,
        "low_price": 100000000,
        "timestamp": 1700000000000,
    }


def test_parse_ticker_extracts_change_fields() -> None:
    """prev_closing_price / signed_change_rate가 응답에 있으면 추출."""
    data = _base_ticker()
    data["prev_closing_price"] = 100000000
    data["signed_change_rate"] = 0.01  # +1%

    ticker = parse_ticker(data)

    assert ticker.prev_closing_price == Decimal("100000000")
    assert ticker.signed_change_rate == Decimal("0.01")


def test_parse_ticker_change_fields_default_none() -> None:
    """필드 누락 시 None (하위호환)."""
    ticker = parse_ticker(_base_ticker())
    assert ticker.prev_closing_price is None
    assert ticker.signed_change_rate is None
