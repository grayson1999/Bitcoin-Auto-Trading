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
    "GenerateSignalResponse",
    "ParsedSignal",
    "PerformanceSummary",
    "SignalErrorResponse",
    "SignalFilterParams",
    "SignalOutcome",
    # Performance Tracker
    "SignalPerformanceTracker",
    # Prompt Builder
    "SignalPromptBuilder",
    # Response Parser
    "SignalResponseParser",
    # Service
    "SignalService",
    "SignalServiceError",
    "SignalStatsResponse",
    "TradingSignalListResponse",
    # Schemas
    "TradingSignalResponse",
    "get_signal_service",
    # Router
    "router",
]
