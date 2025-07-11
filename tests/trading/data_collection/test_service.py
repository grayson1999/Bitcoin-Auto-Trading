# tests/trading/data_collection/test_service.py

import pytest
from unittest.mock import MagicMock
from src.trading.data_collection.service import DataCollectionService

@pytest.fixture(autouse=True)
def disable_db_init(monkeypatch):
    """init_db 호출 무력화"""
    monkeypatch.setattr("src.trading.data_collection.service.init_db", lambda: None)

@pytest.fixture
def fake_session(monkeypatch):
    """
    세션 대체용 MagicMock 생성
    .add, .commit, .rollback, .close 호출을 기록
    """
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    monkeypatch.setattr("src.trading.data_collection.service.SessionRealtime", lambda: session)
    return session

def test_티커저장_성공(monkeypatch, fake_session):
    """티커 수집 성공 시 DB 저장 및 커밋 호출"""
    raw = {"market": "KRW-TEST", "trade_price": 1000}
    parsed = {"market": "KRW-TEST", "trade_price": 1000}
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_ticker", lambda m: raw)
    monkeypatch.setattr("src.trading.data_collection.service.parse_ticker", lambda r: parsed)

    service = DataCollectionService()
    service.collect_ticker("KRW-TEST")

    fake_session.add.assert_called_once()
    fake_session.commit.assert_called_once()
    fake_session.rollback.assert_not_called()

def test_티커데이터_없을때_저장안함(monkeypatch, fake_session):
    """fetch_ticker가 None 반환 시 저장과 커밋이 호출되지 않음"""
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_ticker", lambda m: None)

    service = DataCollectionService()
    service.collect_ticker("KRW-TEST")

    fake_session.add.assert_not_called()
    fake_session.commit.assert_not_called()

def test_티커파싱실패_실행안함(monkeypatch, fake_session):
    """파싱 결과 None 시 저장과 커밋이 호출되지 않음"""
    raw = {"dummy": "value"}
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_ticker", lambda m: raw)
    monkeypatch.setattr("src.trading.data_collection.service.parse_ticker", lambda r: None)

    service = DataCollectionService()
    service.collect_ticker("KRW-TEST")

    fake_session.add.assert_not_called()
    fake_session.commit.assert_not_called()

def test_티커저장예외_롤백실행(monkeypatch, fake_session):
    """DB 저장 중 예외 발생 시 rollback 호출"""
    raw = {"market": "KRW-TEST", "trade_price": 1000}
    parsed = {"market": "KRW-TEST", "trade_price": 1000}
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_ticker", lambda m: raw)
    monkeypatch.setattr("src.trading.data_collection.service.parse_ticker", lambda r: parsed)
    fake_session.commit.side_effect = Exception("DB error")

    service = DataCollectionService()
    service.collect_ticker("KRW-TEST")

    fake_session.rollback.assert_called_once()

def test_계좌저장_성공(monkeypatch, fake_session):
    """계좌 수집 성공 시 DB 저장 및 커밋 호출"""
    raw_list = [{"currency": "BTC", "balance": "1.23", "locked": "0", "avg_buy_price": "100"}]
    parsed = {"currency": "BTC", "balance": 1.23, "locked": 0.0, "avg_buy_price": 100.0, "data_timestamp": 999}
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_accounts", lambda: raw_list)
    monkeypatch.setattr("src.trading.data_collection.service.parse_account", lambda lst, cur="BTC": parsed)

    service = DataCollectionService()
    service.collect_account("BTC")

    fake_session.add.assert_called_once()
    fake_session.commit.assert_called_once()
    fake_session.rollback.assert_not_called()

def test_계좌데이터_없을때_저장안함(monkeypatch, fake_session):
    """fetch_accounts가 None 반환 시 저장과 커밋이 호출되지 않음"""
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_accounts", lambda: None)

    service = DataCollectionService()
    service.collect_account("BTC")

    fake_session.add.assert_not_called()
    fake_session.commit.assert_not_called()

def test_계좌파싱실패_실행안함(monkeypatch, fake_session):
    """파싱 결과 None 시 저장과 커밋이 호출되지 않음"""
    raw_list = [{"currency": "ETH"}]
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_accounts", lambda: raw_list)
    monkeypatch.setattr("src.trading.data_collection.service.parse_account", lambda lst, cur="BTC": None)

    service = DataCollectionService()
    service.collect_account("BTC")

    fake_session.add.assert_not_called()
    fake_session.commit.assert_not_called()

def test_계좌저장예외_롤백실행(monkeypatch, fake_session):
    """DB 저장 중 예외 발생 시 rollback 호출"""
    raw_list = [{"currency": "BTC", "balance": "1.23", "locked": "0", "avg_buy_price": "100"}]
    parsed = {"currency": "BTC", "balance": 1.23, "locked": 0.0, "avg_buy_price": 100.0, "data_timestamp": 999}
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_accounts", lambda: raw_list)
    monkeypatch.setattr("src.trading.data_collection.service.parse_account", lambda lst, cur="BTC": parsed)
    fake_session.commit.side_effect = Exception("DB error")

    service = DataCollectionService()
    service.collect_account("BTC")

    fake_session.rollback.assert_called_once()
