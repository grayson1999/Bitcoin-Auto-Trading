"""Trading module - order execution and management."""

from src.modules.trading.order_monitor import OrderMonitor
from src.modules.trading.order_validator import (
    BalanceInfo,
    OrderBlockedReason,
    OrderValidator,
    ValidationResult,
)
from src.modules.trading.routes import router
from src.modules.trading.schemas import (
    BalanceResponse,
    ExecuteOrderRequest,
    ExecuteOrderResponse,
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

__all__ = [
    # Schemas
    "OrderTypeEnum",
    "OrderSideEnum",
    "OrderStatusEnum",
    "OrderStatusFilterEnum",
    "OrderResponse",
    "OrderListResponse",
    "ExecuteOrderRequest",
    "ExecuteOrderResponse",
    "PositionResponse",
    "BalanceResponse",
    "OrderErrorResponse",
    # Service
    "TradingService",
    "TradingServiceError",
    "get_trading_service",
    "OrderResult",
    # Validator
    "OrderValidator",
    "OrderBlockedReason",
    "ValidationResult",
    "BalanceInfo",
    # Monitor
    "OrderMonitor",
    # Router
    "router",
]
