"""Dashboard API endpoints for market data."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.market import (
    CollectorStatsResponse,
    CurrentMarketResponse,
    MarketDataListResponse,
    MarketDataResponse,
    MarketSummaryResponse,
)
from src.database import get_session
from src.services.data_collector import get_data_collector
from src.services.upbit_client import UpbitError, get_upbit_client

router = APIRouter(prefix="/dashboard")


@router.get(
    "/market",
    response_model=CurrentMarketResponse,
    summary="Get current market data",
    description="Fetches the current BTC/KRW market data directly from Upbit.",
)
async def get_current_market() -> CurrentMarketResponse:
    """Get current market data from Upbit.

    Returns:
        Current market status including price, volume, and 24h stats.

    Raises:
        HTTPException: On API error.
    """
    client = get_upbit_client()

    try:
        ticker = await client.get_ticker("KRW-BTC")

        # Calculate 24h change percentage
        change_24h_pct = None
        if ticker.low_price > 0:
            # Approximate change using high/low range
            mid_price = (ticker.high_price + ticker.low_price) / 2
            if mid_price > 0:
                change_24h_pct = float(
                    (ticker.trade_price - mid_price) / mid_price * 100
                )

        return CurrentMarketResponse(
            market="KRW-BTC",
            price=ticker.trade_price,
            volume_24h=ticker.acc_trade_volume_24h,
            high_24h=ticker.high_price,
            low_24h=ticker.low_price,
            trade_count_24h=ticker.acc_trade_count_24h,
            timestamp=datetime.fromtimestamp(ticker.timestamp / 1000, tz=UTC),
            change_24h_pct=change_24h_pct,
        )

    except UpbitError as e:
        raise HTTPException(
            status_code=e.status_code or 503,
            detail=f"Failed to fetch market data: {e.message}",
        ) from e


@router.get(
    "/market/history",
    response_model=MarketDataListResponse,
    summary="Get market data history",
    description="Get historical market data from the database.",
)
async def get_market_history(
    session: Annotated[AsyncSession, Depends(get_session)],
    hours: Annotated[
        int, Query(ge=1, le=168, description="Hours of history to retrieve")
    ] = 24,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum records to return")
    ] = 100,
) -> MarketDataListResponse:
    """Get historical market data.

    Args:
        session: Database session.
        hours: Number of hours of history (1-168).
        limit: Maximum number of records.

    Returns:
        List of market data records.
    """
    collector = get_data_collector()
    start_time = datetime.now(UTC) - timedelta(hours=hours)

    data = await collector.get_data_range(session, start_time)
    data = data[-limit:] if len(data) > limit else data

    return MarketDataListResponse(
        items=[MarketDataResponse.model_validate(d) for d in data],
        total=len(data),
    )


@router.get(
    "/market/summary",
    response_model=MarketSummaryResponse,
    summary="Get market data summary",
    description="Get summary statistics for market data over a time period.",
)
async def get_market_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    hours: Annotated[int, Query(ge=1, le=168, description="Hours to summarize")] = 24,
) -> MarketSummaryResponse:
    """Get market data summary statistics.

    Args:
        session: Database session.
        hours: Number of hours to summarize.

    Returns:
        Summary statistics including high, low, change percentage.
    """
    collector = get_data_collector()
    summary = await collector.get_hourly_summary(session, hours)
    return MarketSummaryResponse(**summary)


@router.get(
    "/market/latest",
    response_model=list[MarketDataResponse],
    summary="Get latest market data records",
    description="Get the most recent market data records from the database.",
)
async def get_latest_market_data(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records")] = 10,
) -> list[MarketDataResponse]:
    """Get latest market data records.

    Args:
        session: Database session.
        limit: Number of records to return.

    Returns:
        List of latest market data records.
    """
    collector = get_data_collector()
    data = await collector.get_latest(session, limit)
    return [MarketDataResponse.model_validate(d) for d in data]


@router.get(
    "/collector/stats",
    response_model=CollectorStatsResponse,
    summary="Get data collector statistics",
    description="Get statistics about the data collector service.",
)
async def get_collector_stats() -> CollectorStatsResponse:
    """Get data collector statistics.

    Returns:
        Collector statistics including running status and counts.
    """
    collector = get_data_collector()
    stats = collector.stats
    return CollectorStatsResponse(**stats)
