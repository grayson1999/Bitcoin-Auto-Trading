"""
Upbit Public API client module

Provides public API access without authentication.
- Ticker (current price)
- Orderbook
- Candle data (minute, day, week)
"""

import asyncio
from typing import Any

import httpx
from loguru import logger

from src.clients.upbit.common import (
    FIRST_ITEM,
    HTTP_BAD_REQUEST,
    HTTP_RATE_LIMIT,
    MAX_RETRIES,
    RETRY_DELAY,
    REQUEST_TIMEOUT,
    UPBIT_API_URL,
    UpbitCandleData,
    UpbitTickerData,
    parse_candle,
    parse_ticker,
)
from src.config import settings

# === Error messages ===
ERROR_INVALID_TICKER = "Invalid ticker response"


class UpbitPublicAPIError(Exception):
    """Upbit Public API error exception."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UpbitPublicAPI:
    """
    Upbit Public API client

    Provides ticker, candle, and orderbook queries without authentication.

    Usage:
        api = UpbitPublicAPI()
        ticker = await api.get_ticker()
        print(f"Current price: {ticker.trade_price}")
    """

    def __init__(self):
        """Initialize Upbit Public API client."""
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client (lazy initialization)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=UPBIT_API_URL,
                timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Perform Upbit Public API HTTP request with retry logic.

        Args:
            method: HTTP method (GET)
            endpoint: API endpoint path
            params: URL query parameters

        Returns:
            API response data (dict or list)

        Raises:
            UpbitPublicAPIError: On API error or network failure
        """
        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                )

                if response.status_code == HTTP_RATE_LIMIT:
                    wait_time = RETRY_DELAY * (2**attempt)
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

                if response.status_code >= HTTP_BAD_REQUEST:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get(
                        "message", response.text
                    )
                    raise UpbitPublicAPIError(
                        f"Upbit API error: {error_msg}",
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(RETRY_DELAY)

            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                await asyncio.sleep(RETRY_DELAY)

        raise UpbitPublicAPIError(f"Request failed after {MAX_RETRIES} retries: {last_error}")

    async def get_ticker(self, market: str | None = None) -> UpbitTickerData:
        """
        Get current ticker data.

        Args:
            market: Market code (default: settings.trading_ticker)

        Returns:
            UpbitTickerData: Ticker data (price, volume, etc.)
        """
        market = market or settings.trading_ticker
        response = await self._request(
            method="GET",
            endpoint="/ticker",
            params={"markets": market},
        )

        if not response or not isinstance(response, list):
            raise UpbitPublicAPIError(ERROR_INVALID_TICKER)

        return parse_ticker(response[FIRST_ITEM])

    async def get_orderbook(self, market: str | None = None) -> dict[str, Any]:
        """
        Get orderbook data.

        Args:
            market: Market code (default: settings.trading_ticker)

        Returns:
            dict: Orderbook data (bid/ask prices)
        """
        market = market or settings.trading_ticker
        response = await self._request(
            method="GET",
            endpoint="/orderbook",
            params={"markets": market},
        )
        return response[FIRST_ITEM] if response else {}

    async def get_minute_candles(
        self,
        market: str | None = None,
        unit: int = 60,
        count: int = 200,
    ) -> list[UpbitCandleData]:
        """
        Get minute candle data.

        Args:
            market: Market code (default: settings.trading_ticker)
            unit: Minute unit (1, 3, 5, 10, 15, 30, 60, 240)
            count: Number of candles (max 200)

        Returns:
            list[UpbitCandleData]: Candle data list (newest first)
        """
        market = market or settings.trading_ticker
        response = await self._request(
            method="GET",
            endpoint=f"/candles/minutes/{unit}",
            params={"market": market, "count": min(count, 200)},
        )

        if not isinstance(response, list):
            return []

        return [parse_candle(candle) for candle in response]

    async def get_day_candles(
        self,
        market: str | None = None,
        count: int = 200,
    ) -> list[UpbitCandleData]:
        """
        Get daily candle data.

        Args:
            market: Market code (default: settings.trading_ticker)
            count: Number of candles (max 200)

        Returns:
            list[UpbitCandleData]: Candle data list (newest first)
        """
        market = market or settings.trading_ticker
        response = await self._request(
            method="GET",
            endpoint="/candles/days",
            params={"market": market, "count": min(count, 200)},
        )

        if not isinstance(response, list):
            return []

        return [parse_candle(candle) for candle in response]

    async def get_week_candles(
        self,
        market: str | None = None,
        count: int = 52,
    ) -> list[UpbitCandleData]:
        """
        Get weekly candle data.

        Args:
            market: Market code (default: settings.trading_ticker)
            count: Number of candles (max 200)

        Returns:
            list[UpbitCandleData]: Candle data list (newest first)
        """
        market = market or settings.trading_ticker
        response = await self._request(
            method="GET",
            endpoint="/candles/weeks",
            params={"market": market, "count": min(count, 200)},
        )

        if not isinstance(response, list):
            return []

        return [parse_candle(candle) for candle in response]


# === Singleton instance ===
_public_api: UpbitPublicAPI | None = None


def get_upbit_public_api() -> UpbitPublicAPI:
    """
    Get Upbit Public API singleton.

    Returns:
        UpbitPublicAPI: Singleton instance
    """
    global _public_api
    if _public_api is None:
        _public_api = UpbitPublicAPI()
    return _public_api
