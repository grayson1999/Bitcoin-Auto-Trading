# -*- coding: utf-8 -*-
# tests/trading/data_collection/test_parser.py

import time
import pytest
from trading.data_collection.parser import parse_ticker, parse_account

FULL_RAW_TICKER = {
    "market": "KRW-ETH",
    "trade_price": 2000000.0,
    "prev_closing_price": 1990000.0,
    "opening_price": 1980000.0,
    "high_price": 2010000.0,
    "low_price": 1970000.0,
    "change": "RISE",
    "change_rate": 0.005,
    "trade_volume": 5.0,
    "acc_trade_volume_24h": 100.0,
    "timestamp": 1620000000000,
}

def test_모든_주요_필드가_올바르게_매핑되는지():
    """모든 주요 필드가 올바르게 매핑되고, 불필요 필드는 제거되는지 검증"""
    out = parse_ticker(FULL_RAW_TICKER)
    expected_keys = {
        "market", "trade_price", "prev_closing_price", "opening_price",
        "high_price", "low_price", "change_type", "change_rate",
        "trade_volume", "acc_trade_volume_24h", "data_timestamp"
    }
    assert set(out.keys()) == expected_keys
    assert out["market"] == "KRW-ETH"
    # ... 이하 생략

def test_일부_필드만_주어졌을_때_나머지가_None인지():
    """일부 필드만 주어졌을 때, 없는 필드는 None으로 채워지는지 검증"""
    raw = {"market": "KRW-XYZ", "trade_price": 123.45, "timestamp": 1111}
    out = parse_ticker(raw)
    assert out["market"] == "KRW-XYZ"
    assert out["trade_price"] == 123.45
    for key in {"prev_closing_price","opening_price","high_price","low_price",
                "change_type","change_rate","trade_volume","acc_trade_volume_24h"}:
        assert out[key] is None

@pytest.mark.parametrize("input_raw", [None, {}])
def test_raw이_None이거나_빈딕셔너리일때_None반환(input_raw):
    """raw가 None 또는 빈 dict이면 None 반환"""
    assert parse_ticker(input_raw) is None

FULL_ACCOUNTS = [
    {"currency": "ABC", "balance": "1", "locked": "0.1", "avg_buy_price": "100"},
    {"currency": "DEF", "balance": "3", "locked": "0.3", "avg_buy_price": None},
]

def test_중복된_통화가_있으면_첫번째만_반환(monkeypatch):
    """중복된 통화가 있을 때, 첫 번째 항목만 반환하는지 검증"""
    fixed = 1000.0
    monkeypatch.setattr(time, "time", lambda: fixed)
    out = parse_account(FULL_ACCOUNTS + FULL_ACCOUNTS, currency="ABC")
    assert out["currency"] == "ABC"
    assert out["balance"] == 1.0

def test_누락된_필드는_기본값_및_타입변환(monkeypatch):
    """locked나 avg_buy_price 누락 시 기본값(0) 적용, 타입 변환 확인"""
    monkeypatch.setattr(time, "time", lambda: 55.5)
    out = parse_account([{"currency": "XYZ"}], currency="XYZ")
    assert out["balance"] == 0.0
    assert out["locked"] == 0.0
    assert out["avg_buy_price"] == 0.0

@pytest.mark.parametrize("input_list", [None, []])
def test_raw_list이_None이거나_빈리스트일때_None반환(input_list):
    """raw_list가 None 또는 빈 리스트일 때 None 반환"""
    assert parse_account(input_list, currency="DEF") is None
