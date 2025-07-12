# tests/trading/data_collection/test_service.py

import pytest
from unittest.mock import MagicMock
from src.trading.data_collection.service import DataCollectionService

@pytest.fixture(autouse=True)
def db_초기화_비활성화(monkeypatch):
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

def test_아카이빙_호출(monkeypatch):
    """Service의 archive_5min 메소드가 archiving 모듈의 archive_5min_ohlcv를 올바르게 호출하는지 테스트합니다."""
    mock_archive = MagicMock()
    monkeypatch.setattr("src.trading.data_collection.archiving.archive_5min_ohlcv", mock_archive)

    service = DataCollectionService()
    service.archive_5min(days=15)

    mock_archive.assert_called_once_with(days=15, keep_hours=12)


from unittest.mock import patch
from src.database.models import TickData, AccountData

def test_get_realtime_data_성공(monkeypatch, fake_session):
    """get_realtime_data 호출 시 DB에서 시세, API에서 계좌 정보를 가져오는지 테스트"""
    # --- Mock 데이터 설정 ---
    # 1. DB에서 반환될 Mock 시세 데이터
    mock_tick = TickData(market="KRW-BTC", trade_price=5000, data_timestamp=12345)
    fake_session.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_tick]

    # 2. API에서 반환될 Mock 계좌 데이터
    mock_api_accounts = [
        {'currency': 'KRW', 'balance': '10000', 'locked': '0', 'avg_buy_price': '0'},
        {'currency': 'BTC', 'balance': '0.1', 'locked': '0', 'avg_buy_price': '4000'}
    ]
    # 3. 파서가 반환할 Mock 파싱된 계좌 데이터
    mock_parsed_krw = {'currency': 'KRW', 'balance': 10000.0, 'locked': 0.0, 'avg_buy_price': 0.0, 'data_timestamp': 999}
    mock_parsed_btc = {'currency': 'BTC', 'balance': 0.1, 'locked': 0.0, 'avg_buy_price': 4000.0, 'data_timestamp': 998}

    # --- Mocking 설정 ---
    # UpbitAPI.fetch_accounts가 mock_api_accounts를 반환하도록 설정
    mock_fetch_accounts = MagicMock(return_value=mock_api_accounts)
    monkeypatch.setattr("src.trading.data_collection.service.UpbitAPI.fetch_accounts", mock_fetch_accounts)
    
    # parse_account가 통화에 따라 다른 mock 데이터를 반환하도록 설정
    def mock_parse(raw, currency):
        if currency == 'KRW': return mock_parsed_krw
        if currency == 'BTC': return mock_parsed_btc
        return None
    monkeypatch.setattr("src.trading.data_collection.service.parse_account", mock_parse)

    # --- 테스트 실행 ---
    service = DataCollectionService()
    result = service.get_realtime_data(market="KRW-BTC", count=1)

    # --- 검증 ---
    # 1. API 함수가 정확히 1번 호출되었는가?
    mock_fetch_accounts.assert_called_once()

    # 2. DB 쿼리가 TickData에 대해 실행되었는가?
    fake_session.query.assert_any_call(TickData)
    # 3. DB 쿼리가 AccountData에 대해 실행되지 않았는가?
    # query.call_args_list를 확인하여 AccountData 호출이 없는지 확인
    for call in fake_session.query.call_args_list:
        assert call.args[0] is not AccountData

    # 4. 결과 데이터 검증
    assert len(result.ticks) == 1
    assert result.ticks[0].trade_price == 5000
    assert len(result.accounts) == 2
    assert result.accounts[0].currency == 'KRW'
    assert result.accounts[0].balance == 10000.0
    assert result.accounts[1].currency == 'BTC'
    assert result.accounts[1].balance == 0.1
