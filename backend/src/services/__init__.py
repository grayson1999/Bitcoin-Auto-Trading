"""
공유 인프라 서비스 패키지

이 패키지는 모듈에서 공유하는 인프라 서비스를 제공합니다.
- UpbitClient: Upbit 거래소 API 클라이언트
- DataCollector: 실시간 시장 데이터 수집기
- AIClient: Gemini AI API 클라이언트
- TechnicalIndicatorCalculator: 기술적 지표 계산기
- MultiTimeframeAnalyzer: 멀티 타임프레임 분석기
- SignalPerformanceTracker: 신호 성과 추적기
- Notifier: 알림 서비스
- SlackLogHandler: ERROR 레벨 로그 자동 Slack 알림

도메인 서비스는 modules/로 이동:
- SignalService (modules/signal/service.py)
- TradingService (modules/trading/service.py)
- RiskService (modules/risk/service.py)
"""

from src.services.ai_client import AIClient, AIClientError, AIResponse, get_ai_client
from src.services.data_collector import DataCollector, get_data_collector
from src.services.multi_timeframe_analyzer import (
    MultiTimeframeAnalyzer,
    MultiTimeframeResult,
    TimeframeAnalysis,
    get_multi_timeframe_analyzer,
)
from src.services.notifier import (
    AlertLevel,
    AlertMessage,
    Notifier,
    NotifierError,
    get_notifier,
)
from src.services.signal_performance_tracker import (
    PerformanceSummary,
    SignalOutcome,
    SignalPerformanceTracker,
)
from src.services.slack_log_handler import SlackLogHandler, get_slack_log_handler
from src.services.technical_indicators import (
    IndicatorResult,
    TechnicalIndicatorCalculator,
    get_technical_calculator,
)
from src.services.upbit_client import UpbitClient, get_upbit_client

__all__ = [
    # Upbit
    "UpbitClient",
    "get_upbit_client",
    # Data Collector
    "DataCollector",
    "get_data_collector",
    # AI
    "AIClient",
    "AIClientError",
    "AIResponse",
    "get_ai_client",
    # Technical Indicators
    "TechnicalIndicatorCalculator",
    "IndicatorResult",
    "get_technical_calculator",
    # Multi-Timeframe Analyzer
    "MultiTimeframeAnalyzer",
    "MultiTimeframeResult",
    "TimeframeAnalysis",
    "get_multi_timeframe_analyzer",
    # Signal Performance Tracker
    "SignalPerformanceTracker",
    "SignalOutcome",
    "PerformanceSummary",
    # Notifier
    "Notifier",
    "NotifierError",
    "AlertLevel",
    "AlertMessage",
    "get_notifier",
    # Slack Log Handler
    "SlackLogHandler",
    "get_slack_log_handler",
]
