"""Upbit API client with JWT authentication.

This module provides async HTTP client for Upbit exchange API.
Supports market data retrieval and order execution.
"""

import asyncio
import hashlib
import time
import uuid
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from loguru import logger
from pydantic import BaseModel

from src.config import settings

# Upbit API constants
UPBIT_API_URL = "https://api.upbit.com/v1"
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# JWT/Hash constants
JWT_ALGORITHM = "HS256"
HASH_ALGORITHM = "SHA512"


class UpbitTickerData(BaseModel):
    """Ticker data from Upbit API."""

    market: str
    trade_price: Decimal
    acc_trade_volume_24h: Decimal
    high_price: Decimal
    low_price: Decimal
    acc_trade_count_24h: int
    timestamp: int


class UpbitBalance(BaseModel):
    """Account balance from Upbit API."""

    currency: str
    balance: Decimal
    locked: Decimal
    avg_buy_price: Decimal


class UpbitOrderResponse(BaseModel):
    """Order response from Upbit API."""

    uuid: str
    side: str
    ord_type: str
    price: Decimal | None
    state: str
    market: str
    volume: Decimal
    remaining_volume: Decimal
    executed_volume: Decimal
    trades_count: int


class UpbitError(Exception):
    """Exception for Upbit API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UpbitClient:
    """Async HTTP client for Upbit exchange API.

    Provides methods for:
    - Getting market ticker data
    - Querying account balances
    - Placing and querying orders

    Uses JWT authentication for private endpoints.
    """

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
    ):
        """Initialize Upbit client.

        Args:
            access_key: Upbit API access key. Defaults to settings.
            secret_key: Upbit API secret key. Defaults to settings.
        """
        self.access_key = access_key or settings.upbit_access_key
        self.secret_key = secret_key or settings.upbit_secret_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
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

    def _generate_jwt_token(self, query_params: dict[str, Any] | None = None) -> str:
        """Generate JWT token for authenticated requests.

        Args:
            query_params: Query parameters to include in token hash.

        Returns:
            JWT token string.
        """
        payload: dict[str, Any] = {
            "access_key": self.access_key,
            "nonce": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
        }

        if query_params:
            query_string = urlencode(query_params)
            query_hash = hashlib.sha512(query_string.encode()).hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = HASH_ALGORITHM

        return jwt.encode(payload, self.secret_key, algorithm=JWT_ALGORITHM)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make HTTP request to Upbit API.

        Args:
            method: HTTP method (GET, POST, DELETE).
            endpoint: API endpoint path.
            params: Query parameters.
            json_data: JSON body data.
            authenticated: Whether to include JWT auth.

        Returns:
            API response data.

        Raises:
            UpbitError: On API error or network failure.
        """
        client = await self._get_client()
        headers: dict[str, str] = {}

        if authenticated:
            token = self._generate_jwt_token(params or json_data)
            headers["Authorization"] = f"Bearer {token}"

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json_data,
                    headers=headers,
                )

                if response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = RETRY_DELAY * (2**attempt)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                    await self._sleep(wait_time)
                    continue

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get(
                        "message", response.text
                    )
                    raise UpbitError(
                        f"Upbit API error: {error_msg}",
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
                await self._sleep(RETRY_DELAY)

            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                )
                await self._sleep(RETRY_DELAY)

        raise UpbitError(f"Request failed after {MAX_RETRIES} attempts: {last_error}")

    async def _sleep(self, seconds: float) -> None:
        """Async sleep helper."""
        await asyncio.sleep(seconds)

    def _parse_order_response(self, response: dict[str, Any]) -> UpbitOrderResponse:
        """Parse order response from Upbit API.

        Args:
            response: Raw API response dictionary.

        Returns:
            Parsed UpbitOrderResponse.
        """
        return UpbitOrderResponse(
            uuid=response["uuid"],
            side=response["side"],
            ord_type=response["ord_type"],
            price=Decimal(str(response["price"])) if response.get("price") else None,
            state=response["state"],
            market=response["market"],
            volume=Decimal(str(response["volume"])),
            remaining_volume=Decimal(str(response["remaining_volume"])),
            executed_volume=Decimal(str(response["executed_volume"])),
            trades_count=response["trades_count"],
        )

    # ==================== Public Endpoints ====================

    async def get_ticker(self, market: str = "KRW-BTC") -> UpbitTickerData:
        """Get current ticker data for a market.

        Args:
            market: Market code (default: KRW-BTC).

        Returns:
            Ticker data with price, volume, etc.
        """
        response = await self._request(
            method="GET",
            endpoint="/ticker",
            params={"markets": market},
        )

        if not response or not isinstance(response, list):
            raise UpbitError("Invalid ticker response")

        data = response[0]
        return UpbitTickerData(
            market=data["market"],
            trade_price=Decimal(str(data["trade_price"])),
            acc_trade_volume_24h=Decimal(str(data["acc_trade_volume_24h"])),
            high_price=Decimal(str(data["high_price"])),
            low_price=Decimal(str(data["low_price"])),
            acc_trade_count_24h=data["acc_trade_count_24h"],
            timestamp=data["timestamp"],
        )

    async def get_orderbook(self, market: str = "KRW-BTC") -> dict[str, Any]:
        """Get orderbook for a market.

        Args:
            market: Market code.

        Returns:
            Orderbook data with bids and asks.
        """
        response = await self._request(
            method="GET",
            endpoint="/orderbook",
            params={"markets": market},
        )
        return response[0] if response else {}

    # ==================== Private Endpoints ====================

    async def get_accounts(self) -> list[UpbitBalance]:
        """Get account balances.

        Returns:
            List of account balances.
        """
        response = await self._request(
            method="GET",
            endpoint="/accounts",
            authenticated=True,
        )

        if not isinstance(response, list):
            raise UpbitError("Invalid accounts response")

        return [
            UpbitBalance(
                currency=acc["currency"],
                balance=Decimal(str(acc["balance"])),
                locked=Decimal(str(acc["locked"])),
                avg_buy_price=Decimal(str(acc["avg_buy_price"])),
            )
            for acc in response
        ]

    async def get_balance(self, currency: str = "KRW") -> Decimal:
        """Get balance for a specific currency.

        Args:
            currency: Currency code (KRW, BTC, etc.).

        Returns:
            Available balance.
        """
        accounts = await self.get_accounts()
        for acc in accounts:
            if acc.currency == currency:
                return acc.balance
        return Decimal("0")

    async def place_order(
        self,
        market: str,
        side: str,
        volume: Decimal | None = None,
        price: Decimal | None = None,
        ord_type: str = "limit",
    ) -> UpbitOrderResponse:
        """Place a new order.

        Args:
            market: Market code (e.g., KRW-BTC).
            side: Order side (bid=buy, ask=sell).
            volume: Order volume (for limit/market sell).
            price: Order price (for limit/market buy).
            ord_type: Order type (limit, price, market).

        Returns:
            Order response with UUID and status.
        """
        params: dict[str, Any] = {
            "market": market,
            "side": side,
            "ord_type": ord_type,
        }

        if volume is not None:
            params["volume"] = str(volume)
        if price is not None:
            params["price"] = str(price)

        logger.info(f"Placing order: {params}")

        response = await self._request(
            method="POST",
            endpoint="/orders",
            json_data=params,
            authenticated=True,
        )

        if not isinstance(response, dict):
            raise UpbitError("Invalid order response")

        return self._parse_order_response(response)

    async def get_order(self, uuid: str) -> UpbitOrderResponse:
        """Get order status by UUID.

        Args:
            uuid: Order UUID.

        Returns:
            Order details.
        """
        response = await self._request(
            method="GET",
            endpoint="/order",
            params={"uuid": uuid},
            authenticated=True,
        )

        if not isinstance(response, dict):
            raise UpbitError("Invalid order response")

        return self._parse_order_response(response)

    async def cancel_order(self, uuid: str) -> UpbitOrderResponse:
        """Cancel an order.

        Args:
            uuid: Order UUID to cancel.

        Returns:
            Cancelled order details.
        """
        response = await self._request(
            method="DELETE",
            endpoint="/order",
            params={"uuid": uuid},
            authenticated=True,
        )

        if not isinstance(response, dict):
            raise UpbitError("Invalid cancel response")

        return self._parse_order_response(response)


# Singleton instance
_upbit_client: UpbitClient | None = None


def get_upbit_client() -> UpbitClient:
    """Get singleton Upbit client instance."""
    global _upbit_client
    if _upbit_client is None:
        _upbit_client = UpbitClient()
    return _upbit_client
