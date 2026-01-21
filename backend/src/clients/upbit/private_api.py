"""
Upbit Private API client module

Provides authenticated API access.
- Account balance (accounts)
- Place order (place_order)
- Get order (get_order)
- Cancel order (cancel_order)
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

from src.clients.upbit.common import (
    HASH_ALGORITHM,
    HTTP_BAD_REQUEST,
    HTTP_RATE_LIMIT,
    JWT_ALGORITHM,
    MAX_RETRIES,
    RETRY_DELAY,
    REQUEST_TIMEOUT,
    UPBIT_API_URL,
    UpbitBalance,
    UpbitOrderResponse,
    parse_balance,
    parse_order_response,
)
from src.config import settings

# === Error messages ===
ERROR_INVALID_ACCOUNT = "Invalid account response"
ERROR_INVALID_ORDER = "Invalid order response"
ERROR_INVALID_CANCEL = "Invalid cancel response"


class UpbitPrivateAPIError(Exception):
    """Upbit Private API error exception."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UpbitPrivateAPI:
    """
    Upbit Private API client

    Provides authenticated API for account and order operations.

    Usage:
        api = UpbitPrivateAPI()
        accounts = await api.get_accounts()
        for acc in accounts:
            print(f"{acc.currency}: {acc.balance}")
    """

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
    ):
        """
        Initialize Upbit Private API client.

        Args:
            access_key: Upbit API access key (default: from settings)
            secret_key: Upbit API secret key (default: from settings)
        """
        self.access_key = access_key or settings.upbit_access_key
        self.secret_key = secret_key or settings.upbit_secret_key
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

    def _generate_jwt_token(self, query_params: dict[str, Any] | None = None) -> str:
        """
        Generate JWT authentication token.

        Args:
            query_params: Query parameters to include in hash

        Returns:
            str: Generated JWT token
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
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Perform Upbit Private API HTTP request with JWT auth.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            params: URL query parameters
            json_data: JSON request body

        Returns:
            API response data (dict or list)

        Raises:
            UpbitPrivateAPIError: On API error or network failure
        """
        client = await self._get_client()
        headers: dict[str, str] = {}

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
                    raise UpbitPrivateAPIError(
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

        raise UpbitPrivateAPIError(f"Request failed after {MAX_RETRIES} retries: {last_error}")

    async def get_accounts(self) -> list[UpbitBalance]:
        """
        Get account balances.

        Returns:
            list[UpbitBalance]: List of account balances

        Raises:
            UpbitPrivateAPIError: On API error
        """
        response = await self._request(
            method="GET",
            endpoint="/accounts",
        )

        if not isinstance(response, list):
            raise UpbitPrivateAPIError(ERROR_INVALID_ACCOUNT)

        return [parse_balance(acc) for acc in response]

    async def get_balance(self, currency: str = "KRW") -> Decimal:
        """
        Get balance for specific currency.

        Args:
            currency: Currency code (KRW, BTC, etc.)

        Returns:
            Decimal: Available balance (0 if not found)
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
        """
        Place an order.

        Args:
            market: Market code
            side: Order side (bid=buy, ask=sell)
            volume: Order volume (required for limit/market sell)
            price: Order price (required for limit/market buy)
            ord_type: Order type (limit, price, market)

        Returns:
            UpbitOrderResponse: Order response

        Raises:
            UpbitPrivateAPIError: On order failure
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

        logger.info(f"Order request: {params}")

        response = await self._request(
            method="POST",
            endpoint="/orders",
            json_data=params,
        )

        if not isinstance(response, dict):
            raise UpbitPrivateAPIError(ERROR_INVALID_ORDER)

        return parse_order_response(response)

    async def get_order(self, uuid: str) -> UpbitOrderResponse:
        """
        Get order status.

        Args:
            uuid: Order UUID

        Returns:
            UpbitOrderResponse: Order details

        Raises:
            UpbitPrivateAPIError: On query failure
        """
        response = await self._request(
            method="GET",
            endpoint="/order",
            params={"uuid": uuid},
        )

        if not isinstance(response, dict):
            raise UpbitPrivateAPIError(ERROR_INVALID_ORDER)

        return parse_order_response(response)

    async def cancel_order(self, uuid: str) -> UpbitOrderResponse:
        """
        Cancel an order.

        Args:
            uuid: Order UUID to cancel

        Returns:
            UpbitOrderResponse: Cancelled order details

        Raises:
            UpbitPrivateAPIError: On cancel failure
        """
        response = await self._request(
            method="DELETE",
            endpoint="/order",
            params={"uuid": uuid},
        )

        if not isinstance(response, dict):
            raise UpbitPrivateAPIError(ERROR_INVALID_CANCEL)

        return parse_order_response(response)


# === Singleton instance ===
_private_api: UpbitPrivateAPI | None = None


def get_upbit_private_api() -> UpbitPrivateAPI:
    """
    Get Upbit Private API singleton.

    Returns:
        UpbitPrivateAPI: Singleton instance
    """
    global _private_api
    if _private_api is None:
        _private_api = UpbitPrivateAPI()
    return _private_api
