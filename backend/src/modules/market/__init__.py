"""Market module - market data collection and retrieval."""

from src.modules.market.schemas import (
    BalanceResponse,
    CollectorStatsResponse,
    CurrentMarketResponse,
    MarketDataListResponse,
    MarketDataResponse,
    MarketSummaryResponse,
    PositionResponse,
)
from src.modules.market.service import (
    MarketService,
    MarketServiceError,
    get_market_service,
)

__all__ = [
    # Service
    "MarketService",
    "MarketServiceError",
    "get_market_service",
    # Schemas
    "MarketDataResponse",
    "MarketDataListResponse",
    "MarketSummaryResponse",
    "CurrentMarketResponse",
    "CollectorStatsResponse",
    "PositionResponse",
    "BalanceResponse",
]
