import pytest
import time
import json
from unittest.mock import call, MagicMock
from datetime import datetime

from src.trading.signal_generation.chatgpt_wrapper import (
    send_signal_request, 
    SignalResponse, 
    MAX_RETRIES, 
    RETRY_DELAY_SECONDS,
    CONFIDENCE_THRESHOLD,
    client
)
from src.trading.data_collection.dto import RealtimeData, RealtimeTickData, RealtimeAccountData

# Mock response object that mimics openai.ChatCompletion
class MockChatCompletion:
    def __init__(self, content, is_json=True):
        if is_json:
            response_content = json.dumps(content)
        else:
            response_content = content  # For testing malformed responses

        self._data = {
            'choices': [{'message': {'content': response_content}}],
            'usage': {'total_tokens': 50} # Example metadata
        }

    def model_dump(self):
        return self._data

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

def test_정상적으로_신호_요청을_보내고_파싱된_객체를_반환한다(monkeypatch, mock_realtime_data):
    """
    Given a valid request payload,
    When send_signal_request is called,
    Then it should return a correctly parsed SignalResponse object.
    """
    call_params = {}
    
    def fake_create(**kwargs):
        call_params.update(kwargs)
        response_data = {"signal": "BUY", "reason": "Ascending trend confirmed", "confidence": 0.95}
        return MockChatCompletion(response_data)

    monkeypatch.setattr(client.chat.completions, "create", fake_create)

    result = send_signal_request(mock_realtime_data)

    assert isinstance(result, SignalResponse)
    assert result.signal == "BUY"
    assert result.confidence >= CONFIDENCE_THRESHOLD
    assert isinstance(result.timestamp, datetime)

def test_신뢰도가_낮으면_재시도_후_성공한다(monkeypatch, mock_realtime_data):
    """
    Given the API first returns a low-confidence response, then a high-confidence one,
    When send_signal_request is called,
    Then it should retry and return the high-confidence response.
    """
    low_confidence_response = MockChatCompletion({"signal": "HOLD", "reason": "Low volatility", "confidence": 0.3})
    high_confidence_response = MockChatCompletion({"signal": "BUY", "reason": "Breakout confirmed", "confidence": 0.8})
    
    mock_create = MagicMock(side_effect=[low_confidence_response, high_confidence_response])
    monkeypatch.setattr(client.chat.completions, "create", mock_create)
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    result = send_signal_request(mock_realtime_data)

    assert mock_create.call_count == 2
    mock_sleep.assert_called_once_with(RETRY_DELAY_SECONDS)
    assert result.signal == "BUY"
    assert result.confidence == 0.8

def test_응답_파싱에_실패하면_오류를_담은_객체를_반환한다(monkeypatch, mock_realtime_data):
    """
    Given a response with malformed content (not valid JSON),
    When send_signal_request is called,
    Then it should return a SignalResponse object indicating a parsing error.
    """
    def fake_create_malformed(**kwargs):
        return MockChatCompletion("This is not a valid JSON string.", is_json=False)

    monkeypatch.setattr(client.chat.completions, "create", fake_create_malformed)

    result = send_signal_request(mock_realtime_data)

    assert result.signal == 'parsing_error'
    assert result.confidence == 0.0

def test_API_오류가_발생하면_재시도_후_예외를_던진다(monkeypatch, mock_realtime_data):
    """
    Given that the API call consistently fails,
    When send_signal_request is called,
    Then it should retry MAX_RETRIES times and then raise the exception.
    """
    mock_create = MagicMock(side_effect=ConnectionError("Forced API error"))
    monkeypatch.setattr(client.chat.completions, "create", mock_create)
    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    with pytest.raises(ConnectionError):
        send_signal_request(mock_realtime_data)

    assert mock_create.call_count == MAX_RETRIES
    # Check that sleep was called with exponential backoff
    assert call(2) in mock_sleep.call_args_list
    assert call(4) in mock_sleep.call_args_list

def test_마크다운_코드_블록_제거_후_정상_파싱(monkeypatch, mock_realtime_data):
    """
    Given a response with JSON content wrapped in markdown code blocks,
    When send_signal_request is called,
    Then it should correctly parse the JSON content.
    """
    def fake_create_markdown_json(**kwargs):
        json_content = {
            "signal": "BUY",
            "reason": "Test reason with markdown",
            "confidence": 0.75
        }
        return MockChatCompletion(f"```json\n{json.dumps(json_content)}\n```", is_json=False)

    monkeypatch.setattr(client.chat.completions, "create", fake_create_markdown_json)

    result = send_signal_request(mock_realtime_data)

    assert isinstance(result, SignalResponse)
    assert result.signal == "BUY"
    assert result.reason == "Test reason with markdown"
    assert result.confidence == 0.75
    assert result.raw_response is not None
