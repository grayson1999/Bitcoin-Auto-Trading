"""
Signal module - AI trading signal generation, performance tracking, and retrieval.

Structure:
    signal/
    ├── classifier/     # 코인 유형 분류
    ├── parser/         # AI 응답 파싱
    ├── prompt/         # 프롬프트 생성
    ├── tracker/        # 성과 추적
    ├── sampler.py      # 시장 데이터 샘플링
    ├── routes.py       # API 엔드포인트
    ├── schemas.py      # Pydantic 스키마
    └── service.py      # 메인 서비스
"""

from src.modules.signal.classifier import CoinType, get_coin_type
from src.modules.signal.parser import ParsedSignal, SignalResponseParser
from src.modules.signal.prompt import PromptConfig, SignalPromptBuilder
from src.modules.signal.routes import router
from src.modules.signal.sampler import MarketDataSampler
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
from src.modules.signal.tracker import (
    PerformanceSummary,
    SignalOutcome,
    SignalPerformanceTracker,
)

__all__ = [
    # Classifier
    "CoinType",
    "get_coin_type",
    # Parser
    "ParsedSignal",
    "SignalResponseParser",
    # Prompt
    "PromptConfig",
    "SignalPromptBuilder",
    # Sampler
    "MarketDataSampler",
    # Tracker
    "PerformanceSummary",
    "SignalOutcome",
    "SignalPerformanceTracker",
    # Service
    "SignalService",
    "SignalServiceError",
    "get_signal_service",
    # Schemas
    "GenerateSignalResponse",
    "SignalErrorResponse",
    "SignalFilterParams",
    "SignalStatsResponse",
    "TradingSignalListResponse",
    "TradingSignalResponse",
    # Router
    "router",
]
