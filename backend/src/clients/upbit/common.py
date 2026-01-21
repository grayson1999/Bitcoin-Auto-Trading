"""
Upbit API common utilities

Shared constants, types, and helper functions for Upbit API clients.
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.clients.common import (
    HTTP_BAD_REQUEST,
    HTTP_RATE_LIMIT,
    MAX_RETRIES,
    RETRY_DELAY,
)

# === Upbit API constants ===
UPBIT_API_URL = "https://api.upbit.com/v1"
REQUEST_TIMEOUT = 10.0  # seconds

# === JWT/Hash algorithm constants ===
JWT_ALGORITHM = "HS256"
HASH_ALGORITHM = "SHA512"

# === Response index constants ===
FIRST_ITEM = 0

# Re-export for backward compatibility
__all__ = ["HTTP_BAD_REQUEST", "HTTP_RATE_LIMIT", "MAX_RETRIES", "RETRY_DELAY"]


def to_decimal(value: str | int | float | None) -> Decimal | None:
    """
    Convert value to Decimal.

    Args:
        value: Value to convert (string, int, float, or None)

    Returns:
        Decimal | None: Converted Decimal value or None
    """
    if value is None:
        return None
    return Decimal(str(value))


class UpbitTickerData(BaseModel):
    """Upbit ticker data model."""

    market: str
    trade_price: Decimal
    acc_trade_volume_24h: Decimal
    high_price: Decimal
    low_price: Decimal
    timestamp: int


class UpbitCandleData(BaseModel):
    """Upbit candle (OHLCV) data model."""

    market: str
    candle_date_time_utc: str
    candle_date_time_kst: str
    opening_price: Decimal
    high_price: Decimal
    low_price: Decimal
    trade_price: Decimal
    candle_acc_trade_volume: Decimal
    candle_acc_trade_price: Decimal


class UpbitBalance(BaseModel):
    """Upbit account balance model."""

    currency: str
    balance: Decimal
    locked: Decimal
    avg_buy_price: Decimal


class UpbitOrderResponse(BaseModel):
    """Upbit order response model."""

    uuid: str
    side: str
    ord_type: str
    price: Decimal | None
    state: str
    market: str
    volume: Decimal | None = None
    remaining_volume: Decimal | None = None
    executed_volume: Decimal | None = None
    avg_price: Decimal | None = None
    executed_funds: Decimal | None = None
    trades_count: int = 0


def parse_candle(candle: dict[str, Any]) -> UpbitCandleData:
    """
    Parse candle data from API response.

    Args:
        candle: Raw candle data from API

    Returns:
        UpbitCandleData: Parsed candle data
    """
    return UpbitCandleData(
        market=candle["market"],
        candle_date_time_utc=candle["candle_date_time_utc"],
        candle_date_time_kst=candle["candle_date_time_kst"],
        opening_price=to_decimal(candle["opening_price"]),
        high_price=to_decimal(candle["high_price"]),
        low_price=to_decimal(candle["low_price"]),
        trade_price=to_decimal(candle["trade_price"]),
        candle_acc_trade_volume=to_decimal(candle["candle_acc_trade_volume"]),
        candle_acc_trade_price=to_decimal(candle["candle_acc_trade_price"]),
    )


def parse_ticker(data: dict[str, Any]) -> UpbitTickerData:
    """
    Parse ticker data from API response.

    Args:
        data: Raw ticker data from API

    Returns:
        UpbitTickerData: Parsed ticker data
    """
    return UpbitTickerData(
        market=data["market"],
        trade_price=to_decimal(data["trade_price"]),
        acc_trade_volume_24h=to_decimal(data["acc_trade_volume_24h"]),
        high_price=to_decimal(data["high_price"]),
        low_price=to_decimal(data["low_price"]),
        timestamp=data["timestamp"],
    )


def parse_balance(acc: dict[str, Any]) -> UpbitBalance:
    """
    Parse balance data from API response.

    Args:
        acc: Raw account data from API

    Returns:
        UpbitBalance: Parsed balance data
    """
    return UpbitBalance(
        currency=acc["currency"],
        balance=to_decimal(acc["balance"]),
        locked=to_decimal(acc["locked"]),
        avg_buy_price=to_decimal(acc["avg_buy_price"]),
    )


def parse_order_response(response: dict[str, Any]) -> UpbitOrderResponse:
    """
    Parse order response from API.

    Args:
        response: Raw order response from API

    Returns:
        UpbitOrderResponse: Parsed order response
    """
    return UpbitOrderResponse(
        uuid=response["uuid"],
        side=response["side"],
        ord_type=response["ord_type"],
        price=to_decimal(response.get("price")),
        state=response["state"],
        market=response["market"],
        volume=to_decimal(response.get("volume")),
        remaining_volume=to_decimal(response.get("remaining_volume")),
        executed_volume=to_decimal(response.get("executed_volume")),
        avg_price=to_decimal(response.get("avg_price")),
        executed_funds=to_decimal(response.get("executed_funds")),
        trades_count=response.get("trades_count", 0),
    )
