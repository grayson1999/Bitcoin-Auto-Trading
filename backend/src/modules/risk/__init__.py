"""Risk module - risk management and trading controls."""

from src.modules.risk.event_manager import RiskEventManager
from src.modules.risk.routes import router
from src.modules.risk.schemas import (
    HaltTradingRequest,
    HaltTradingResponse,
    PositionCheckResponse,
    ResumeTradingResponse,
    RiskCheckResultEnum,
    RiskErrorResponse,
    RiskEventListResponse,
    RiskEventResponse,
    RiskEventTypeEnum,
    RiskStatusResponse,
    StopLossCheckResponse,
    VolatilityCheckResponse,
)
from src.modules.risk.service import (
    PositionCheckResult,
    RiskCheckResult,
    RiskService,
    RiskServiceError,
    RiskStatus,
    StopLossCheckResult,
    get_risk_service,
)

__all__ = [
    "HaltTradingRequest",
    "HaltTradingResponse",
    "PositionCheckResponse",
    "PositionCheckResult",
    "ResumeTradingResponse",
    "RiskCheckResult",
    "RiskCheckResultEnum",
    "RiskErrorResponse",
    "RiskEventListResponse",
    # Event Manager
    "RiskEventManager",
    "RiskEventResponse",
    # Schemas
    "RiskEventTypeEnum",
    # Service
    "RiskService",
    "RiskServiceError",
    "RiskStatus",
    "RiskStatusResponse",
    "StopLossCheckResponse",
    "StopLossCheckResult",
    "VolatilityCheckResponse",
    "get_risk_service",
    # Router
    "router",
]
