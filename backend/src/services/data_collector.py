"""Data collector service for market data.

This module provides the DataCollector service that:
- Collects real-time market data from Upbit
- Stores data in the database
- Handles network failures with auto-reconnect
- Logs all collection events
"""

import asyncio
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.market_data import MarketData
from src.services.upbit_client import UpbitClient, UpbitError, get_upbit_client

# Collection constants
DEFAULT_MARKET = "KRW-BTC"
RECONNECT_BASE_DELAY = 1.0
RECONNECT_MAX_DELAY = 60.0
RECONNECT_MAX_ATTEMPTS = 10
MS_TO_SECONDS = 1000


class DataCollectorError(Exception):
    """Exception for data collection errors."""

    pass


class DataCollector:
    """Service for collecting and storing market data.

    Collects BTC/KRW market data from Upbit and stores it in the database.
    Includes auto-reconnect logic for network failures.
    """

    def __init__(
        self,
        upbit_client: UpbitClient | None = None,
        market: str = DEFAULT_MARKET,
    ):
        """Initialize data collector.

        Args:
            upbit_client: Upbit API client instance.
            market: Market to collect data for.
        """
        self._client = upbit_client or get_upbit_client()
        self._market = market
        self._is_running = False
        self._consecutive_failures = 0
        self._last_success: datetime | None = None
        self._total_collected = 0

    @property
    def is_running(self) -> bool:
        """Check if collector is running."""
        return self._is_running

    @property
    def stats(self) -> dict[str, Any]:
        """Get collector statistics."""
        return {
            "is_running": self._is_running,
            "consecutive_failures": self._consecutive_failures,
            "last_success": self._last_success.isoformat()
            if self._last_success
            else None,
            "total_collected": self._total_collected,
            "market": self._market,
        }

    async def collect_once(self, session: AsyncSession) -> MarketData | None:
        """Collect market data once and store it.

        Args:
            session: Database session.

        Returns:
            MarketData instance if successful, None otherwise.
        """
        try:
            ticker = await self._client.get_ticker(self._market)

            market_data = MarketData(
                timestamp=datetime.fromtimestamp(
                    ticker.timestamp / MS_TO_SECONDS, tz=UTC
                ),
                price=ticker.trade_price,
                volume=ticker.acc_trade_volume_24h,
                high_price=ticker.high_price,
                low_price=ticker.low_price,
                trade_count=ticker.acc_trade_count_24h,
            )

            session.add(market_data)
            await session.flush()

            self._consecutive_failures = 0
            self._last_success = datetime.now(UTC)
            self._total_collected += 1

            logger.debug(
                f"Collected market data: price={ticker.trade_price}, "
                f"volume={ticker.acc_trade_volume_24h}"
            )

            return market_data

        except UpbitError as e:
            self._consecutive_failures += 1
            logger.error(
                f"Failed to collect market data: {e.message} "
                f"(attempt {self._consecutive_failures})"
            )
            raise DataCollectorError(f"Upbit API error: {e.message}") from e

        except Exception as e:
            self._consecutive_failures += 1
            logger.exception(
                f"Unexpected error collecting market data "
                f"(attempt {self._consecutive_failures})"
            )
            raise DataCollectorError(f"Collection error: {e}") from e

    async def collect_with_retry(
        self,
        session: AsyncSession,
        max_attempts: int = RECONNECT_MAX_ATTEMPTS,
    ) -> MarketData | None:
        """Collect market data with auto-retry on failure.

        Implements exponential backoff for network failures.

        Args:
            session: Database session.
            max_attempts: Maximum retry attempts.

        Returns:
            MarketData instance if successful, None if all retries failed.
        """
        delay = RECONNECT_BASE_DELAY

        for attempt in range(max_attempts):
            try:
                return await self.collect_once(session)

            except DataCollectorError as e:
                if attempt == max_attempts - 1:
                    logger.error(
                        f"Data collection failed after {max_attempts} attempts: {e}"
                    )
                    return None

                # Exponential backoff with jitter
                jitter = random.uniform(0, delay * 0.1)
                wait_time = min(delay + jitter, RECONNECT_MAX_DELAY)

                logger.warning(
                    f"Retrying data collection in {wait_time:.1f}s "
                    f"(attempt {attempt + 1}/{max_attempts})"
                )

                await asyncio.sleep(wait_time)
                delay = min(delay * 2, RECONNECT_MAX_DELAY)

        return None

    async def get_latest(
        self,
        session: AsyncSession,
        limit: int = 1,
    ) -> list[MarketData]:
        """Get latest market data from database.

        Args:
            session: Database session.
            limit: Number of records to return.

        Returns:
            List of MarketData records.
        """
        result = await session.execute(
            select(MarketData).order_by(MarketData.timestamp.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_data_range(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> list[MarketData]:
        """Get market data within a time range.

        Args:
            session: Database session.
            start_time: Start of time range.
            end_time: End of time range (default: now).

        Returns:
            List of MarketData records.
        """
        if end_time is None:
            end_time = datetime.now(UTC)

        result = await session.execute(
            select(MarketData)
            .where(MarketData.timestamp >= start_time)
            .where(MarketData.timestamp <= end_time)
            .order_by(MarketData.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_hourly_summary(
        self,
        session: AsyncSession,
        hours: int = 24,
    ) -> dict[str, Any]:
        """Get summary statistics for the last N hours.

        Args:
            session: Database session.
            hours: Number of hours to summarize.

        Returns:
            Dictionary with summary statistics.
        """
        start_time = datetime.now(UTC) - timedelta(hours=hours)
        data = await self.get_data_range(session, start_time)

        if not data:
            return {
                "count": 0,
                "period_hours": hours,
                "latest_price": None,
                "high": None,
                "low": None,
                "price_change_pct": None,
            }

        prices = [d.price for d in data]
        first_price = prices[0]
        last_price = prices[-1]
        price_change_pct = (
            ((last_price - first_price) / first_price * 100)
            if first_price > 0
            else Decimal("0")
        )

        return {
            "count": len(data),
            "period_hours": hours,
            "latest_price": float(last_price),
            "high": float(max(prices)),
            "low": float(min(prices)),
            "price_change_pct": float(price_change_pct),
            "first_timestamp": data[0].timestamp.isoformat(),
            "last_timestamp": data[-1].timestamp.isoformat(),
        }

    async def cleanup_old_data(
        self,
        session: AsyncSession,
        retention_days: int | None = None,
    ) -> int:
        """Delete market data older than retention period.

        Args:
            session: Database session.
            retention_days: Days to keep (default: from settings).

        Returns:
            Number of deleted records.
        """
        if retention_days is None:
            retention_days = settings.data_retention_days

        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

        result = await session.execute(
            delete(MarketData).where(MarketData.timestamp < cutoff_date)
        )

        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(
                f"Cleaned up {deleted_count} market data records "
                f"older than {retention_days} days"
            )

        return deleted_count


# Singleton instance
_data_collector: DataCollector | None = None


def get_data_collector() -> DataCollector:
    """Get singleton DataCollector instance."""
    global _data_collector
    if _data_collector is None:
        _data_collector = DataCollector()
    return _data_collector
