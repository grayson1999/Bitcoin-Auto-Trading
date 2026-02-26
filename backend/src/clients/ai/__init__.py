"""
AI client module

OpenAI GPT-5 Nano AI 클라이언트.
- OpenAI client: GPT-5 Nano (Primary)
- Unified client: 앙상블 지원
"""

from src.clients.ai.base import (
    COST_CONFIG,
    TOKENS_PER_M,
    AIClientError,
    AIResponse,
    BaseAIClient,
)
from src.clients.ai.client import AIClient, get_ai_client
from src.clients.ai.openai_client import OpenAIClient, get_openai_client
from src.config.constants import DEFAULT_MAX_RETRIES as MAX_RETRIES
from src.config.constants import DEFAULT_RETRY_DELAY_SECONDS as RETRY_DELAY
from src.config.constants import DEFAULT_TIMEOUT_SECONDS as DEFAULT_TIMEOUT

__all__ = [
    "COST_CONFIG",
    "DEFAULT_TIMEOUT",
    "MAX_RETRIES",
    "RETRY_DELAY",
    "TOKENS_PER_M",
    # Unified Client (with ensemble)
    "AIClient",
    # Base
    "AIClientError",
    "AIResponse",
    "BaseAIClient",
    # OpenAI
    "OpenAIClient",
    "get_ai_client",
    "get_openai_client",
]
