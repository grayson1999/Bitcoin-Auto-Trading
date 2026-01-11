"""Pydantic schemas for market data API responses."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MarketDataResponse(BaseModel):
    """Response schema for a single market data record."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier")
    timestamp: datetime = Field(description="Data collection timestamp (UTC)")
    price: Decimal = Field(description="Current price in KRW")
    volume: Decimal = Field(description="24-hour trading volume")
    high_price: Decimal = Field(description="24-hour high price")
    low_price: Decimal = Field(description="24-hour low price")
    trade_count: int = Field(description="Number of trades")


class MarketDataListResponse(BaseModel):
    """Response schema for list of market data records."""

    items: list[MarketDataResponse] = Field(description="List of market data records")
    total: int = Field(description="Total number of records")


class MarketSummaryResponse(BaseModel):
    """Response schema for market data summary statistics."""

    count: int = Field(description="Number of data points in period")
    period_hours: int = Field(description="Summary period in hours")
    latest_price: float | None = Field(description="Most recent price")
    high: float | None = Field(description="Highest price in period")
    low: float | None = Field(description="Lowest price in period")
    price_change_pct: float | None = Field(description="Price change percentage")
    first_timestamp: str | None = Field(
        default=None, description="First data point timestamp"
    )
    last_timestamp: str | None = Field(
        default=None, description="Last data point timestamp"
    )


class CurrentMarketResponse(BaseModel):
    """Response schema for current market status."""

    market: str = Field(default="KRW-BTC", description="Market code")
    price: Decimal = Field(description="Current price in KRW")
    volume_24h: Decimal = Field(description="24-hour trading volume")
    high_24h: Decimal = Field(description="24-hour high price")
    low_24h: Decimal = Field(description="24-hour low price")
    trade_count_24h: int = Field(description="24-hour trade count")
    timestamp: datetime = Field(description="Data timestamp")
    change_24h_pct: float | None = Field(
        default=None, description="24-hour price change percentage"
    )


class CollectorStatsResponse(BaseModel):
    """Response schema for data collector statistics."""

    is_running: bool = Field(description="Whether collector is running")
    consecutive_failures: int = Field(description="Number of consecutive failures")
    last_success: str | None = Field(description="Last successful collection timestamp")
    total_collected: int = Field(description="Total records collected this session")
    market: str = Field(description="Market being collected")
