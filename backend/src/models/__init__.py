"""
SQLAlchemy 모델 패키지 (하위 호환성 레이어)

[DEPRECATED] 이 패키지는 하위 호환성을 위해 유지됩니다.
새 코드에서는 `src.entities`를 직접 사용하세요.

마이그레이션 예시:
    # Before
    from src.models import MarketData, TradingSignal

    # After
    from src.entities import MarketData, TradingSignal
"""

# Re-export from entities for backward compatibility
from src.entities import (
    BacktestResult,
    BacktestStatus,
    Base,
    DailyStats,
    MarketData,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    RiskEvent,
    RiskEventType,
    SignalType,
    SystemConfig,
    TimestampMixin,
    TradingSignal,
)
from src.entities.system_config import DEFAULT_CONFIGS

__all__ = [
    "Base",
    "TimestampMixin",
    "MarketData",
    "TradingSignal",
    "SignalType",
    "RiskEvent",
    "RiskEventType",
    "DailyStats",
    "Position",
    "SystemConfig",
    "DEFAULT_CONFIGS",
    "Order",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "BacktestResult",
    "BacktestStatus",
]
