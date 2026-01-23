"""Market module - market data collection, technical analysis, and retrieval."""

from src.modules.market.analyzer import (
    MultiTimeframeAnalyzer,
    MultiTimeframeResult,
    TimeframeAnalysis,
    get_multi_timeframe_analyzer,
)
from src.modules.market.data_collector import (
    DataCollector,
    DataCollectorError,
    get_data_collector,
)
from src.modules.market.indicators import (
    IndicatorResult,
    TechnicalIndicatorCalculator,
    get_technical_calculator,
)
from src.modules.market.routes import router
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
    "BalanceResponse",
    "CollectorStatsResponse",
    "CurrentMarketResponse",
    # Data Collector
    "DataCollector",
    "DataCollectorError",
    "IndicatorResult",
    "MarketDataListResponse",
    # Schemas
    "MarketDataResponse",
    # Service
    "MarketService",
    "MarketServiceError",
    "MarketSummaryResponse",
    # Multi-Timeframe Analyzer
    "MultiTimeframeAnalyzer",
    "MultiTimeframeResult",
    "PositionResponse",
    # Technical Indicators
    "TechnicalIndicatorCalculator",
    "TimeframeAnalysis",
    "get_data_collector",
    "get_market_service",
    "get_multi_timeframe_analyzer",
    "get_technical_calculator",
    # Router
    "router",
]
