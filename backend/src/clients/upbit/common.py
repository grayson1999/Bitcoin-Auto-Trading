"""
Upbit API common utilities

Shared constants, types, and helper functions for Upbit API clients.
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel

# === Upbit API constants ===
UPBIT_API_URL = "https://api.upbit.com/v1"
REQUEST_TIMEOUT = 10.0  # seconds

# === JWT/Hash algorithm constants ===
JWT_ALGORITHM = "HS256"
HASH_ALGORITHM = "SHA512"

# === Response index constants ===
FIRST_ITEM = 0


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
    # 전일 종가 및 부호 있는 24h 등락률 (실제 24h 변동 계산용)
    prev_closing_price: Decimal | None = None
    signed_change_rate: Decimal | None = None


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


class UpbitDeposit(BaseModel):
    """Upbit 입금 내역 (원장) 모델."""

    uuid: str
    txid: str | None = None
    currency: str
    amount: Decimal
    state: str  # ACCEPTED=완료
    created_at: str  # ISO 8601


class UpbitWithdrawal(BaseModel):
    """Upbit 출금 내역 (원장) 모델. (/v1/withdraws)"""

    uuid: str
    txid: str | None = None
    currency: str
    amount: Decimal
    fee: Decimal = Decimal("0")
    state: str  # DONE=완료
    created_at: str  # ISO 8601
    done_at: str | None = None


class UpbitTrade(BaseModel):
    """Upbit individual trade model."""

    market: str
    uuid: str
    price: Decimal
    volume: Decimal
    funds: Decimal
    side: str


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
    trades: list[UpbitTrade] = []


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
        prev_closing_price=(
            to_decimal(data["prev_closing_price"])
            if data.get("prev_closing_price") is not None
            else None
        ),
        signed_change_rate=(
            to_decimal(data["signed_change_rate"])
            if data.get("signed_change_rate") is not None
            else None
        ),
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


def parse_deposit(data: dict[str, Any]) -> UpbitDeposit:
    """
    Parse deposit ledger entry from Upbit /v1/deposits response.

    Args:
        data: Raw deposit data from API

    Returns:
        UpbitDeposit: Parsed deposit
    """
    return UpbitDeposit(
        uuid=data["uuid"],
        txid=data.get("txid"),
        currency=data["currency"],
        amount=to_decimal(data["amount"]),
        state=data["state"],
        created_at=data["created_at"],
    )


def parse_withdrawal(data: dict[str, Any]) -> UpbitWithdrawal:
    """
    Parse withdrawal ledger entry from Upbit /v1/withdraws response.

    KRW 출금 시 계좌에서 실제 빠져나간 금액 = amount + fee.

    Args:
        data: Raw withdrawal data from API

    Returns:
        UpbitWithdrawal: Parsed withdrawal
    """
    return UpbitWithdrawal(
        uuid=data["uuid"],
        txid=data.get("txid"),
        currency=data["currency"],
        amount=to_decimal(data["amount"]),
        fee=to_decimal(data.get("fee", "0")),
        state=data["state"],
        created_at=data["created_at"],
        done_at=data.get("done_at"),
    )


def parse_trade(trade: dict[str, Any]) -> UpbitTrade:
    """
    Parse individual trade from API response.

    Args:
        trade: Raw trade data from API

    Returns:
        UpbitTrade: Parsed trade
    """
    return UpbitTrade(
        market=trade["market"],
        uuid=trade["uuid"],
        price=to_decimal(trade["price"]) or Decimal("0"),
        volume=to_decimal(trade["volume"]) or Decimal("0"),
        funds=to_decimal(trade["funds"]) or Decimal("0"),
        side=trade["side"],
    )


def parse_order_response(response: dict[str, Any]) -> UpbitOrderResponse:
    """
    Parse order response from API.

    Args:
        response: Raw order response from API

    Returns:
        UpbitOrderResponse: Parsed order response
    """
    # Parse trades if present
    trades_raw = response.get("trades", [])
    trades = [parse_trade(t) for t in trades_raw] if trades_raw else []

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
        trades=trades,
    )
