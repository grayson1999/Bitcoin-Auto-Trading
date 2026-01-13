"""
FastAPI 라우터 패키지

이 패키지는 버전별 API 라우터를 제공합니다.
- /api/v1 접두사로 모든 엔드포인트 관리
- 헬스체크, 대시보드, 신호 라우터 통합
"""

from fastapi import APIRouter

from src.api.dashboard import router as dashboard_router
from src.api.health import router as health_router
from src.api.signals import router as signals_router

# API v1 라우터 생성
# 모든 엔드포인트는 /api/v1 접두사를 가짐
api_router = APIRouter(prefix="/api/v1")

# 하위 라우터 등록
api_router.include_router(health_router, tags=["Health"])  # 헬스체크
api_router.include_router(dashboard_router, tags=["Dashboard"])  # 대시보드
api_router.include_router(signals_router, tags=["Signals"])  # AI 신호

__all__ = ["api_router"]
