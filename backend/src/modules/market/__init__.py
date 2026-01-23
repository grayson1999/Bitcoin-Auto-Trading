"""
Market module - market data collection, technical analysis, and retrieval.

Structure:
    market/
    ├── collector/      # 시세 데이터 수집
    ├── analysis/       # 기술적 분석
    ├── routes.py       # API 엔드포인트
    ├── schemas.py      # Pydantic 스키마
    └── service.py      # 메인 서비스
"""

from src.modules.market.analysis import (
    IndicatorResult,
    MultiTimeframeAnalyzer,
    MultiTimeframeResult,
    TechnicalIndicatorCalculator,
    TimeframeAnalysis,
    get_multi_timeframe_analyzer,
    get_technical_calculator,
)
from src.modules.market.collector import (
    DataCollector,
    DataCollectorError,
    get_data_collector,
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
    # Schemas
    "BalanceResponse",
    "CollectorStatsResponse",
    "CurrentMarketResponse",
    # Collector
    "DataCollector",
    "DataCollectorError",
    # Analysis - Indicators
    "IndicatorResult",
    "MarketDataListResponse",
    "MarketDataResponse",
    # Service
    "MarketService",
    "MarketServiceError",
    "MarketSummaryResponse",
    # Analysis - Multi-Timeframe
    "MultiTimeframeAnalyzer",
    "MultiTimeframeResult",
    "PositionResponse",
    "TechnicalIndicatorCalculator",
    "TimeframeAnalysis",
    "get_data_collector",
    "get_market_service",
    "get_multi_timeframe_analyzer",
    "get_technical_calculator",
    # Router
    "router",
]
