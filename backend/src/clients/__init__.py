"""
External API clients module

Clients for external service communication.
- Upbit: Exchange API (public/private)
- AI: Gemini, OpenAI clients
- Slack: Notification service
- Auth: Authentication server client
"""

# AI clients
from src.clients.ai import (
    AIClient,
    AIClientError,
    AIResponse,
    BaseAIClient,
    GeminiClient,
    OpenAIClient,
    get_ai_client,
    get_gemini_client,
    get_openai_client,
)

# Auth client
from src.clients.auth_client import (
    AuthClient,
    AuthError,
    AuthUser,
    close_auth_client,
    get_auth_client,
)

# Slack client
from src.clients.slack_client import (
    AlertLevel,
    AlertMessage,
    # Backward compatibility aliases
    Notifier,
    NotifierError,
    SlackClient,
    SlackClientError,
    close_slack_client,
    get_notifier,
    get_slack_client,
)

# Upbit clients
from src.clients.upbit import (
    UpbitBalance,
    UpbitCandleData,
    UpbitOrderResponse,
    UpbitPrivateAPI,
    UpbitPrivateAPIError,
    UpbitPublicAPI,
    UpbitPublicAPIError,
    UpbitTickerData,
    close_upbit_private_api,
    close_upbit_public_api,
    get_upbit_private_api,
    get_upbit_public_api,
)

__all__ = [
    # AI - Unified Client
    "AIClient",
    # AI - Base
    "AIClientError",
    "AIResponse",
    # Slack
    "AlertLevel",
    "AlertMessage",
    # Auth
    "AuthClient",
    "AuthError",
    "AuthUser",
    "BaseAIClient",
    # AI - Gemini
    "GeminiClient",
    # Slack - backward compatibility
    "Notifier",
    "NotifierError",
    # AI - OpenAI
    "OpenAIClient",
    "SlackClient",
    "SlackClientError",
    "UpbitBalance",
    "UpbitCandleData",
    "UpbitOrderResponse",
    # Upbit - Private API
    "UpbitPrivateAPI",
    "UpbitPrivateAPIError",
    # Upbit - Public API
    "UpbitPublicAPI",
    "UpbitPublicAPIError",
    "UpbitTickerData",
    # Singleton closers
    "close_auth_client",
    "close_slack_client",
    "close_upbit_private_api",
    "close_upbit_public_api",
    # Singleton getters
    "get_ai_client",
    "get_auth_client",
    "get_gemini_client",
    "get_notifier",
    "get_openai_client",
    "get_slack_client",
    "get_upbit_private_api",
    "get_upbit_public_api",
]
