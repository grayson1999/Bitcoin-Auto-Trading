import pytest
import time

# src 디렉토리가 PYTHONPATH에 올라가 있다는 가정 하에 import
from src.trading.signal_generation.chatgpt_wrapper import send_signal_request, MAX_RETRIES, client

# 더미 응답 객체: model_dump()를 호출하면 dict를 리턴
class 더미응답:
    def __init__(self, data):
        self._data = data

    def model_dump(self):
        return self._data

def test_정상적으로_신호_요청을_보내고_응답을_반환한다(monkeypatch):
    호출파라미터 = {}
    # create를 모킹: 호출 파라미터를 저장하고, 더미 응답 리턴
    def fake_create(**kwargs):
        호출파라미터.update(kwargs)
        return 더미응답({"signal": "BUY", "reason": "상승 추세 확인", "confidence": 0.95})

    monkeypatch.setattr(client.chat.completions, "create", fake_create)
    monkeypatch.setattr(time, "sleep", lambda _: None)

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "비트코인 매수 신호 줘"}],
        "timeout": 3
    }
    result = send_signal_request(payload)

    # 반환값 검증
    assert result == {"signal": "BUY", "reason": "상승 추세 확인", "confidence": 0.95}
    # 내부 호출에 payload가 그대로 전달됐는지 확인
    assert 호출파라미터["model"] == "gpt-3.5-turbo"
    assert 호출파라미터["messages"][0]["content"] == "비트코인 매수 신호 줘"
    assert 호출파라미터["timeout"] == 3

def test_API_오류가_발생하면_재시도_후_예외를_던진다(monkeypatch):
    호출횟수 = {"count": 0}
    # 매 호출마다 예외 발생
    def fake_create_raise(**kwargs):
        호출횟수["count"] += 1
        raise Exception("강제 오류")

    monkeypatch.setattr(client.chat.completions, "create", fake_create_raise)
    monkeypatch.setattr(time, "sleep", lambda _: None)

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "테스트"}]
    }
    with pytest.raises(Exception) as excinfo:
        send_signal_request(payload)

    # MAX_RETRIES번 재시도했는지 확인
    assert 호출횟수["count"] == MAX_RETRIES
    assert "강제 오류" in str(excinfo.value)
