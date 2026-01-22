"""
External API clients module

Clients for external service communication.
- Upbit: Exchange API (public/private)
- AI: Gemini, OpenAI clients
- Slack: Notification service
- Auth: Authentication server client
"""

# Common constants
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
from src.clients.common import (
    DEFAULT_TIMEOUT,
    HTTP_BAD_REQUEST,
    HTTP_OK,
    HTTP_RATE_LIMIT,
    HTTP_SERVICE_UNAVAILABLE,
    HTTP_UNAUTHORIZED,
    MAX_RETRIES,
    RETRY_DELAY,
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
    get_upbit_private_api,
    get_upbit_public_api,
)

__all__ = [
    # Common constants
    "DEFAULT_TIMEOUT",
    "HTTP_BAD_REQUEST",
    "HTTP_OK",
    "HTTP_RATE_LIMIT",
    "HTTP_SERVICE_UNAVAILABLE",
    "HTTP_UNAUTHORIZED",
    "MAX_RETRIES",
    "RETRY_DELAY",
    # Upbit - Public API
    "UpbitPublicAPI",
    "UpbitPublicAPIError",
    "UpbitTickerData",
    "UpbitCandleData",
    "get_upbit_public_api",
    # Upbit - Private API
    "UpbitPrivateAPI",
    "UpbitPrivateAPIError",
    "UpbitBalance",
    "UpbitOrderResponse",
    "get_upbit_private_api",
    # AI - Base
    "AIClientError",
    "AIResponse",
    "BaseAIClient",
    # AI - Gemini
    "GeminiClient",
    "get_gemini_client",
    # AI - OpenAI
    "OpenAIClient",
    "get_openai_client",
    # AI - Unified Client
    "AIClient",
    "get_ai_client",
    # Slack
    "AlertLevel",
    "AlertMessage",
    "SlackClient",
    "SlackClientError",
    "get_slack_client",
    # Slack - backward compatibility
    "Notifier",
    "NotifierError",
    "get_notifier",
    # Auth
    "AuthClient",
    "AuthError",
    "AuthUser",
    "get_auth_client",
    "close_auth_client",
]
