import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import time

from src.trading.signal_generation.service import SignalGenerationService
from src.trading.signal_generation.chatgpt_wrapper import SignalResponse
from src.trading.data_collection.dto import RealtimeData, RealtimeTickData, RealtimeAccountData

@pytest.fixture
def mock_realtime_data() -> RealtimeData:
    """테스트용 RealtimeData 객체를 생성하는 Fixture"""
    return RealtimeData(
        ticks=[
            RealtimeTickData(
                market='KRW-BTC', trade_price=90500000, prev_closing_price=90000000, 
                opening_price=90100000, high_price=90800000, low_price=89900000,
                change_type='RISE', change_rate=0.0055, trade_volume=0.1, 
                acc_trade_volume_24h=1500, data_timestamp=int(time.time() * 1000)
            )
        ],
        accounts=[
            RealtimeAccountData(
                currency='KRW', balance=1000000, locked=0, avg_buy_price=None, 
                data_timestamp=int(time.time() * 1000)
            )
        ]
    )

def test_generate_signal_성공적으로_신호를_생성하고_DB에_저장한다(mock_realtime_data):
    """
    Given: RealtimeData 객체
    When: generate_signal 메서드 호출
    Then: SignalResponse 객체를 반환하고, 데이터베이스에 시그널 이력을 저장한다.
    """
    # Mock chatgpt_wrapper.send_signal_request
    mock_signal_response = SignalResponse(
        signal="BUY",
        reason="Test reason",
        confidence=0.9,
        timestamp=datetime.now()
    )
    with patch('src.trading.signal_generation.chatgpt_wrapper.send_signal_request', return_value=mock_signal_response) as mock_send_request:
        # Mock get_db
        with patch('src.trading.signal_generation.service.get_history_db') as mock_get_db:
            mock_db_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db_session

            # 서비스 생성 및 메서드 호출
            service = SignalGenerationService()
            result = service.generate_signal(mock_realtime_data)

            # 검증
            mock_send_request.assert_called_once_with(realtime_data=mock_realtime_data, options={})
            mock_get_db.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

            assert result == mock_signal_response
