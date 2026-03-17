"""
External API clients module

Clients for external service communication.
- Upbit: Exchange API (public/private)
- AI: OpenAI GPT-5 Nano client
- Telegram: Notification service
- Auth: Authentication server client
"""

# AI clients
from src.clients.ai import (
    AIClient,
    AIClientError,
    AIResponse,
    BaseAIClient,
    OpenAIClient,
    get_ai_client,
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

# Telegram client
from src.clients.telegram_client import (
    AlertLevel,
    AlertMessage,
    # Backward compatibility aliases
    Notifier,
    NotifierError,
    TelegramClient,
    TelegramClientError,
    close_telegram_client,
    get_notifier,
    get_telegram_client,
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
    # Telegram
    "AlertLevel",
    "AlertMessage",
    # Auth
    "AuthClient",
    "AuthError",
    "AuthUser",
    "BaseAIClient",
    # Backward compatibility
    "Notifier",
    "NotifierError",
    # AI - OpenAI
    "OpenAIClient",
    "TelegramClient",
    "TelegramClientError",
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
    "close_telegram_client",
    "close_upbit_private_api",
    "close_upbit_public_api",
    # Singleton getters
    "get_ai_client",
    "get_auth_client",
    "get_notifier",
    "get_openai_client",
    "get_telegram_client",
    "get_upbit_private_api",
    "get_upbit_public_api",
]
