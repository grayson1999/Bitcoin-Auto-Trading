"""
Upbit client module

Upbit exchange API clients.
- Public API: ticker, candle, orderbook
- Private API: account, order
"""

from src.clients.upbit.common import (
    REQUEST_TIMEOUT,
    # Constants
    UPBIT_API_URL,
    # Models
    UpbitBalance,
    UpbitCandleData,
    UpbitOrderResponse,
    UpbitTickerData,
    # Parsers
    parse_balance,
    parse_candle,
    parse_order_response,
    parse_ticker,
    to_decimal,
)
from src.clients.upbit.private_api import (
    UpbitPrivateAPI,
    UpbitPrivateAPIError,
    close_upbit_private_api,
    get_upbit_private_api,
)
from src.clients.upbit.public_api import (
    UpbitPublicAPI,
    UpbitPublicAPIError,
    close_upbit_public_api,
    get_upbit_public_api,
)

__all__ = [
    "REQUEST_TIMEOUT",
    # Constants
    "UPBIT_API_URL",
    # Models
    "UpbitBalance",
    "UpbitCandleData",
    "UpbitOrderResponse",
    # Private API
    "UpbitPrivateAPI",
    "UpbitPrivateAPIError",
    # Public API
    "UpbitPublicAPI",
    "UpbitPublicAPIError",
    "UpbitTickerData",
    # Singleton getters/closers
    "close_upbit_private_api",
    "close_upbit_public_api",
    "get_upbit_private_api",
    "get_upbit_public_api",
    # Parsers
    "parse_balance",
    "parse_candle",
    "parse_order_response",
    "parse_ticker",
    "to_decimal",
]
