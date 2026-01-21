"""
Upbit client module

Upbit exchange API clients.
- Public API: ticker, candle, orderbook
- Private API: account, order
"""

from src.clients.upbit.common import (
    # Constants
    UPBIT_API_URL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
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
    get_upbit_private_api,
)
from src.clients.upbit.public_api import (
    UpbitPublicAPI,
    UpbitPublicAPIError,
    get_upbit_public_api,
)

__all__ = [
    # Constants
    "UPBIT_API_URL",
    "REQUEST_TIMEOUT",
    "MAX_RETRIES",
    "RETRY_DELAY",
    # Models
    "UpbitBalance",
    "UpbitCandleData",
    "UpbitOrderResponse",
    "UpbitTickerData",
    # Parsers
    "parse_balance",
    "parse_candle",
    "parse_order_response",
    "parse_ticker",
    "to_decimal",
    # Public API
    "UpbitPublicAPI",
    "UpbitPublicAPIError",
    "get_upbit_public_api",
    # Private API
    "UpbitPrivateAPI",
    "UpbitPrivateAPIError",
    "get_upbit_private_api",
]
