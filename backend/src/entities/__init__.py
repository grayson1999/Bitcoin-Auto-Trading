"""
Entity 패키지

SQLAlchemy ORM 모델(Entity)을 정의합니다.
기존 models/ 폴더에서 이동된 엔티티들을 포함합니다.

Phase 2에서는 Base, TimestampMixin만 구현됩니다.
Phase 4 (User Story 2)에서 도메인별 Entity가 추가됩니다:
- MarketData
- TradingSignal, SignalType
- Order, OrderType, OrderSide, OrderStatus
- Position
- DailyStats
- RiskEvent, RiskEventType
- BacktestResult, BacktestStatus
- SystemConfig
"""

from src.entities.base import Base, TimestampMixin

__all__ = [
    "Base",
    "TimestampMixin",
]
