"""Backtest module - backtesting execution and result retrieval."""

from src.modules.backtest.engine import (
    BacktestEngine,
    BacktestState,
    CandlePriceData,
    Trade,
)
from src.modules.backtest.reporter import BacktestMetrics, BacktestReporter
from src.modules.backtest.routes import router
from src.modules.backtest.schemas import (
    BacktestErrorResponse,
    BacktestRequest,
    BacktestResultDetailResponse,
    BacktestResultListResponse,
    BacktestResultResponse,
    BacktestRunResponse,
    BacktestStatusEnum,
    TradeRecord,
)
from src.modules.backtest.service import (
    BacktestService,
    BacktestServiceError,
    get_backtest_service,
)

__all__ = [
    # Schemas
    "BacktestStatusEnum",
    "BacktestRequest",
    "TradeRecord",
    "BacktestResultResponse",
    "BacktestResultDetailResponse",
    "BacktestResultListResponse",
    "BacktestRunResponse",
    "BacktestErrorResponse",
    # Service
    "BacktestService",
    "BacktestServiceError",
    "get_backtest_service",
    # Engine
    "BacktestEngine",
    "BacktestState",
    "CandlePriceData",
    "Trade",
    # Reporter
    "BacktestReporter",
    "BacktestMetrics",
    # Router
    "router",
]
