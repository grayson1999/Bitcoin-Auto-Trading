# tests/trading/data_collection/test_archiving.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from src.trading.data_collection.archiving import _bucket_5min, aggregate_5min_ohlcv, archive_5min_ohlcv
from src.database.models import TickData, FiveMinOHLCV

@pytest.fixture
def sample_ticks():
    """테스트용 TickData 리스트를 생성합니다."""
    base_time = datetime(2023, 1, 1, 12, 0, 0)
    ticks = []
    # 12:00 ~ 12:04
    for i in range(5):
        ticks.append(TickData(
            market="KRW-BTC",
            trade_price=100 + i,
            trade_volume=10 + i,
            created_at=base_time + timedelta(minutes=i)
        ))
    # 12:05 ~ 12:09
    for i in range(5):
        ticks.append(TickData(
            market="KRW-BTC",
            trade_price=200 + i,
            trade_volume=20 + i,
            created_at=base_time + timedelta(minutes=5+i)
        ))
    return ticks

def test_5분단위_버킷팅():
    """_bucket_5min 함수가 시간을 5분 단위로 올바르게 버킷팅하는지 테스트합니다."""
    dt1 = datetime(2023, 1, 1, 12, 3, 45)
    assert _bucket_5min(dt1) == datetime(2023, 1, 1, 12, 0, 0)

    dt2 = datetime(2023, 1, 1, 12, 8, 15)
    assert _bucket_5min(dt2) == datetime(2023, 1, 1, 12, 5, 0)

    dt3 = datetime(2023, 1, 1, 12, 5, 0)
    assert _bucket_5min(dt3) == datetime(2023, 1, 1, 12, 5, 0)

def test_5분_OHLCV_집계(sample_ticks):
    """aggregate_5min_ohlcv 함수가 틱 데이터를 5분 OHLCV로 정확하게 집계하는지 테스트합니다."""
    ohlcv_list = aggregate_5min_ohlcv(sample_ticks)

    assert len(ohlcv_list) == 2

    # First bucket (12:00)
    assert ohlcv_list[0]["timestamp"] == datetime(2023, 1, 1, 12, 0, 0)
    assert ohlcv_list[0]["open"] == 100
    assert ohlcv_list[0]["high"] == 104
    assert ohlcv_list[0]["low"] == 100
    assert ohlcv_list[0]["close"] == 104
    assert ohlcv_list[0]["volume"] == 10 + 11 + 12 + 13 + 14

    # Second bucket (12:05)
    assert ohlcv_list[1]["timestamp"] == datetime(2023, 1, 1, 12, 5, 0)
    assert ohlcv_list[1]["open"] == 200
    assert ohlcv_list[1]["high"] == 204
    assert ohlcv_list[1]["low"] == 200
    assert ohlcv_list[1]["close"] == 204
    assert ohlcv_list[1]["volume"] == 20 + 21 + 22 + 23 + 24

@patch('src.trading.data_collection.archiving.get_realtime_db')
@patch('src.trading.data_collection.archiving.get_history_db')
def test_아카이빙_성공(mock_get_history_db, mock_get_realtime_db, sample_ticks):
    """archive_5min_ohlcv 함수가 전체 아카이빙 프로세스를 성공적으로 수행하는지 테스트합니다."""
    # Mock DB 세션 설정
    mock_realtime_session = MagicMock()
    mock_history_session = MagicMock()
    mock_get_realtime_db.return_value = iter([mock_realtime_session])
    mock_get_history_db.return_value = iter([mock_history_session])

    # Mock 쿼리 결과 설정
    mock_realtime_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = sample_ticks
    mock_realtime_session.query.return_value.filter.return_value.delete.return_value = len(sample_ticks)

    # 함수 실행
    archive_5min_ohlcv(days=1, keep_hours=24)

    # 검증
    mock_history_session.bulk_insert_mappings.assert_called_once()
    args, _ = mock_history_session.bulk_insert_mappings.call_args
    assert args[0] == FiveMinOHLCV
    assert len(args[1]) == 2 # 2개의 OHLCV 데이터가 생성되었는지 확인
    mock_history_session.commit.assert_called_once()

    # filter 호출 검증
    # 첫 번째 filter 호출 (데이터 조회)
    # 두 번째 filter 호출 (데이터 삭제)
    # 정확한 datetime 객체를 예측하기 어려우므로, filter가 호출되었는지 여부만 확인
    assert mock_realtime_session.query.return_value.filter.call_count == 2
    mock_realtime_session.query.return_value.filter.return_value.delete.assert_called_once()
    mock_realtime_session.commit.assert_called_once()

@patch('src.trading.data_collection.archiving.get_realtime_db')
@patch('src.trading.data_collection.archiving.get_history_db')
def test_아카이빙_데이터_없음(mock_get_history_db, mock_get_realtime_db):
    """아카이빙할 데이터가 없을 때 정상적으로 종료되는지 테스트합니다."""
    mock_realtime_session = MagicMock()
    mock_history_session = MagicMock()
    mock_get_realtime_db.return_value = iter([mock_realtime_session])
    mock_get_history_db.return_value = iter([mock_history_session])

    mock_realtime_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    archive_5min_ohlcv(days=1)

    mock_history_session.bulk_insert_mappings.assert_not_called()
    mock_history_session.commit.assert_not_called()
    mock_realtime_session.query.return_value.filter.return_value.delete.assert_not_called()
    mock_realtime_session.commit.assert_not_called()

@patch('src.trading.data_collection.archiving.get_realtime_db')
@patch('src.trading.data_collection.archiving.get_history_db')
def test_아카이빙_실패시_롤백(mock_get_history_db, mock_get_realtime_db, sample_ticks):
    """아카이빙 중 예외 발생 시 롤백이 호출되는지 테스트합니다."""
    mock_realtime_session = MagicMock()
    mock_history_session = MagicMock()
    mock_get_realtime_db.return_value = iter([mock_realtime_session])
    mock_get_history_db.return_value = iter([mock_history_session])

    mock_realtime_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = sample_ticks
    mock_history_session.commit.side_effect = Exception("DB Error")

    with pytest.raises(Exception):
        archive_5min_ohlcv(days=1)

    mock_history_session.rollback.assert_called_once()
    mock_realtime_session.rollback.assert_called_once()
