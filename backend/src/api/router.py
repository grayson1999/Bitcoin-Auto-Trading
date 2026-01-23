"""
API 라우터 등록 모듈

모든 도메인 모듈의 라우터를 통합하여 버전별 API 라우터를 생성합니다.
"""

from fastapi import APIRouter

from src.modules.config import router as config_router
from src.modules.dashboard import router as dashboard_router
from src.modules.health import router as health_router
from src.modules.market import router as market_router
from src.modules.risk import router as risk_router
from src.modules.signal import router as signals_router
from src.modules.trading import router as trading_router


def create_api_router() -> APIRouter:
    """
    API v1 라우터 생성

    모든 도메인 라우터를 /api/v1 접두사로 통합합니다.

    Returns:
        APIRouter: 통합된 API 라우터
    """
    router = APIRouter(prefix="/api/v1")

    router.include_router(health_router, tags=["Health"])
    router.include_router(market_router, tags=["Market"])
    router.include_router(dashboard_router, tags=["Dashboard"])
    router.include_router(signals_router, tags=["Signals"])
    router.include_router(risk_router, tags=["Risk"])
    router.include_router(trading_router, tags=["Trading"])
    router.include_router(config_router, tags=["Config"])

    return router
