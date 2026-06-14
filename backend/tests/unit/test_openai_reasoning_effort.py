"""
AI 비용 최적화 (M8/M9) 단위 테스트

nano/gpt-5 모델에 reasoning_effort='minimal'을 설정하고 temperature를
넘기지 않는지 검증한다 (숨은 추론 토큰 비용 절감).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.clients.ai.openai_client import OpenAIClient


def _mock_openai_response() -> MagicMock:
    """OpenAI chat.completions.create 응답 mock."""
    msg = MagicMock()
    msg.content = '{"signal": "HOLD", "confidence": 0.5}'
    msg.refusal = None  # OpenAI safety filter 미발동
    choice = MagicMock()
    choice.message = msg
    choice.finish_reason = "stop"
    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50
    usage.total_tokens = 150
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def _client_with_capture(model: str):
    """create() 호출 인자를 캡처하는 OpenAIClient."""
    client = OpenAIClient(api_key="test-key", model=model)
    mock_create = AsyncMock(return_value=_mock_openai_response())
    fake_openai = MagicMock()
    fake_openai.chat.completions.create = mock_create
    client._get_client = MagicMock(return_value=fake_openai)
    return client, mock_create


@pytest.mark.asyncio
async def test_nano_sets_reasoning_effort_minimal() -> None:
    """nano 모델 → reasoning_effort='minimal', temperature 미전달."""
    client, mock_create = _client_with_capture("gpt-5-nano")

    await client.generate(prompt="test")

    _, kwargs = mock_create.call_args
    assert kwargs.get("reasoning_effort") == "minimal"
    assert "temperature" not in kwargs


@pytest.mark.asyncio
async def test_gpt5_sets_reasoning_effort_minimal() -> None:
    """gpt-5 계열 → reasoning_effort='minimal'."""
    client, mock_create = _client_with_capture("gpt-5-mini")

    await client.generate(prompt="test")

    _, kwargs = mock_create.call_args
    assert kwargs.get("reasoning_effort") == "minimal"


@pytest.mark.asyncio
async def test_non_reasoning_model_uses_temperature() -> None:
    """비-reasoning 모델 → temperature 전달, reasoning_effort 없음."""
    client, mock_create = _client_with_capture("gpt-4o-mini")

    await client.generate(prompt="test", temperature=0.7)

    _, kwargs = mock_create.call_args
    assert kwargs.get("temperature") == 0.7
    assert "reasoning_effort" not in kwargs
