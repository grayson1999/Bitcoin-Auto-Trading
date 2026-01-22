"""
FastAPI 라우터 패키지

이 패키지는 버전별 API 라우터를 제공합니다.
- /api/v1 접두사로 모든 엔드포인트 관리
- 헬스체크, 대시보드, 신호, 리스크, 거래, 설정 라우터 통합

모든 도메인 라우터는 modules/<domain>/routes.py에서 import
(T085 라우터 마이그레이션 완료)
"""

from fastapi import APIRouter

# 모듈에서 라우터 import
from src.api.dashboard import router as dashboard_router
from src.modules.backtest import router as backtest_router
from src.modules.config import router as config_router
from src.modules.health import router as health_router
from src.modules.market import router as market_router
from src.modules.risk import router as risk_router
from src.modules.signal import router as signals_router
from src.modules.trading import router as trading_router

# API v1 라우터 생성
# 모든 엔드포인트는 /api/v1 접두사를 가짐
api_router = APIRouter(prefix="/api/v1")

# 하위 라우터 등록
api_router.include_router(health_router, tags=["Health"])  # 헬스체크
api_router.include_router(market_router, tags=["Market"])  # 시장 데이터
api_router.include_router(dashboard_router, tags=["Dashboard"])  # 대시보드
api_router.include_router(signals_router, tags=["Signals"])  # AI 신호
api_router.include_router(risk_router, tags=["Risk"])  # 리스크 관리
api_router.include_router(trading_router, tags=["Trading"])  # 거래
api_router.include_router(config_router, tags=["Config"])  # 설정
api_router.include_router(backtest_router, tags=["Backtest"])  # 백테스트

__all__ = ["api_router"]
