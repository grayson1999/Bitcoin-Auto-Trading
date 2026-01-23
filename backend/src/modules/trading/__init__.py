"""
Trading module - order execution and management.

Structure:
    trading/
    ├── validator/      # 주문 검증
    ├── monitor/        # 주문 모니터링
    ├── position/       # 포지션 관리
    ├── routes.py       # API 엔드포인트
    ├── schemas.py      # Pydantic 스키마
    └── service.py      # 메인 서비스
"""

from src.modules.trading.monitor import OrderMonitor
from src.modules.trading.position import PositionManager
from src.modules.trading.routes import router
from src.modules.trading.schemas import (
    BalanceResponse,
    OrderErrorResponse,
    OrderListResponse,
    OrderResponse,
    OrderSideEnum,
    OrderStatusEnum,
    OrderStatusFilterEnum,
    OrderTypeEnum,
    PositionResponse,
)
from src.modules.trading.service import (
    OrderResult,
    TradingService,
    TradingServiceError,
    get_trading_service,
)
from src.modules.trading.validator import (
    BalanceInfo,
    OrderBlockedReason,
    OrderValidator,
    ValidationResult,
)

__all__ = [
    # Validator
    "BalanceInfo",
    # Schemas
    "BalanceResponse",
    "OrderBlockedReason",
    "OrderErrorResponse",
    "OrderListResponse",
    # Monitor
    "OrderMonitor",
    "OrderResponse",
    # Service
    "OrderResult",
    "OrderSideEnum",
    "OrderStatusEnum",
    "OrderStatusFilterEnum",
    "OrderTypeEnum",
    "OrderValidator",
    # Position
    "PositionManager",
    "PositionResponse",
    "TradingService",
    "TradingServiceError",
    "ValidationResult",
    "get_trading_service",
    # Router
    "router",
]
