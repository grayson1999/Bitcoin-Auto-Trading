# tests/trading/data_collection/test_archiving.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from src.trading.data_collection.archiving import _bucket_1h, aggregate_1h_ohlcv, archive_1h
from src.database.models import TickData, OneHourOHLCV

@pytest.fixture
def sample_ticks():
    """테스트용 TickData 리스트를 생성합니다."""
    base_time = datetime(2023, 1, 1, 12, 0, 0)
    ticks = []
    # 12:00 ~ 13:59 (2시간 동안 매분 틱 데이터 생성)
    for h in range(2):
        for m in range(60):
            ticks.append(TickData(
                market="KRW-BTC",
                trade_price=100 + h * 100 + m,
                trade_volume=10 + h * 10 + m,
                created_at=base_time + timedelta(hours=h, minutes=m)
            ))
    return ticks

def test_1시간단위_버킷팅():
    """_bucket_1h 함수가 시간을 1시간 단위로 올바르게 버킷팅하는지 테스트합니다."""
    dt1 = datetime(2023, 1, 1, 12, 30, 45)
    assert _bucket_1h(dt1) == datetime(2023, 1, 1, 12, 0, 0)

    dt2 = datetime(2023, 1, 1, 13, 59, 15)
    assert _bucket_1h(dt2) == datetime(2023, 1, 1, 13, 0, 0)

    dt3 = datetime(2023, 1, 1, 14, 0, 0)
    assert _bucket_1h(dt3) == datetime(2023, 1, 1, 14, 0, 0)

def test_1시간_OHLCV_집계(sample_ticks):
    """aggregate_1h_ohlcv 함수가 틱 데이터를 1시간 OHLCV로 정확하게 집계하는지 테스트합니다."""
    ohlcv_list = aggregate_1h_ohlcv("KRW-BTC", sample_ticks)

    assert len(ohlcv_list) == 2

    # First bucket (12:00)
    assert ohlcv_list[0]["timestamp"] == datetime(2023, 1, 1, 12, 0, 0)
    assert ohlcv_list[0]["market"] == "KRW-BTC"
    assert ohlcv_list[0]["open"] == 100
    assert ohlcv_list[0]["high"] == 100 + 59 # 12:59의 trade_price
    assert ohlcv_list[0]["low"] == 100
    assert ohlcv_list[0]["close"] == 100 + 59
    assert ohlcv_list[0]["volume"] == sum(range(10, 10 + 60)) # 12:00 ~ 12:59의 trade_volume 합

    # Second bucket (13:00)
    assert ohlcv_list[1]["timestamp"] == datetime(2023, 1, 1, 13, 0, 0)
    assert ohlcv_list[1]["market"] == "KRW-BTC"
    assert ohlcv_list[1]["open"] == 200
    assert ohlcv_list[1]["high"] == 200 + 59 # 13:59의 trade_price
    assert ohlcv_list[1]["low"] == 200
    assert ohlcv_list[1]["close"] == 200 + 59
    assert ohlcv_list[1]["volume"] == sum(range(20, 20 + 60)) # 13:00 ~ 13:59의 trade_volume 합

@patch('src.trading.data_collection.archiving.get_realtime_db')
@patch('src.trading.data_collection.archiving.get_history_db')
def test_아카이빙_성공(mock_get_history_db, mock_get_realtime_db, sample_ticks):
    """archive_1h 함수가 전체 아카이빙 프로세스를 성공적으로 수행하는지 테스트합니다."""
    # 1) Mock DB 세션 설정
    mock_realtime_session = MagicMock()
    mock_history_session = MagicMock()
    mock_get_realtime_db.return_value = iter([mock_realtime_session])
    mock_get_history_db.return_value = iter([mock_history_session])

    # 2) Mock 쿼리 결과 설정
    mock_realtime_session.query.return_value.filter.return_value \
        .order_by.return_value.all.return_value = sample_ticks
    mock_realtime_session.query.return_value.filter.return_value.delete.return_value = len(sample_ticks)

    # 3) 함수 실행
    archive_1h()

    # 4) 검증: merge()가 OHLCV 레코드 수만큼 호출됐는지 (이 예제에서는 2개)
    #    실제 aggregate_1h_ohlcv 구현에 따라 이 숫자를 맞춰주세요.
    expected_ohlcv_count = 2
    assert mock_history_session.merge.call_count == expected_ohlcv_count

    # merge에 전달된 인스턴스가 OneHourOHLCV 타입인지 확인
    for call_args in mock_history_session.merge.call_args_list:
        instance = call_args[0][0]
        assert isinstance(instance, OneHourOHLCV)

    # 5) 커밋이 한 번 호출되었는지
    mock_history_session.commit.assert_called_once()

    # 6) realtime DB 쪽 삭제 로직 검증
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

    archive_1h()

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
        archive_1h()

    mock_history_session.rollback.assert_called_once()
    mock_realtime_session.rollback.assert_called_once()
