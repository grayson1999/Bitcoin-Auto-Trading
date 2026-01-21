"""
AI client module

AI API clients.
- Gemini client: Google Gemini AI
- OpenAI client: OpenAI API (Fallback)
- Unified client: Gemini first, OpenAI Fallback
"""

from src.clients.ai.base import (
    AIClientError,
    AIResponse,
    BaseAIClient,
    COST_CONFIG,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    TOKENS_PER_M,
)
from src.clients.ai.client import AIClient, get_ai_client
from src.clients.ai.gemini_client import GeminiClient, get_gemini_client
from src.clients.ai.openai_client import OpenAIClient, get_openai_client

__all__ = [
    # Base
    "AIClientError",
    "AIResponse",
    "BaseAIClient",
    "COST_CONFIG",
    "DEFAULT_TIMEOUT",
    "MAX_RETRIES",
    "RETRY_DELAY",
    "TOKENS_PER_M",
    # Gemini
    "GeminiClient",
    "get_gemini_client",
    # OpenAI
    "OpenAIClient",
    "get_openai_client",
    # Unified Client (with fallback)
    "AIClient",
    "get_ai_client",
]
