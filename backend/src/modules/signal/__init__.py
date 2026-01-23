"""Signal module - AI trading signal generation, performance tracking, and retrieval."""

from src.modules.signal.performance_tracker import (
    PerformanceSummary,
    SignalOutcome,
    SignalPerformanceTracker,
)
from src.modules.signal.prompt_builder import SignalPromptBuilder
from src.modules.signal.response_parser import ParsedSignal, SignalResponseParser
from src.modules.signal.routes import router
from src.modules.signal.schemas import (
    GenerateSignalResponse,
    SignalErrorResponse,
    SignalFilterParams,
    SignalStatsResponse,
    TradingSignalListResponse,
    TradingSignalResponse,
)
from src.modules.signal.service import (
    SignalService,
    SignalServiceError,
    get_signal_service,
)

__all__ = [
    # Schemas
    "TradingSignalResponse",
    "TradingSignalListResponse",
    "SignalFilterParams",
    "GenerateSignalResponse",
    "SignalErrorResponse",
    "SignalStatsResponse",
    # Service
    "SignalService",
    "SignalServiceError",
    "get_signal_service",
    # Prompt Builder
    "SignalPromptBuilder",
    # Response Parser
    "SignalResponseParser",
    "ParsedSignal",
    # Performance Tracker
    "SignalPerformanceTracker",
    "SignalOutcome",
    "PerformanceSummary",
    # Router
    "router",
]
