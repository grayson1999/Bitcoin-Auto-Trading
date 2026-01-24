"""
헬스체크 모듈 라우터

이 모듈은 API 서버의 상태를 확인하는 헬스체크 엔드포인트를 제공합니다.
- /health: 기본 헬스체크 (로드 밸런서용)
- /health/detail: 상세 헬스체크 (6개 구성요소 상태)

기존 파일: api/health.py
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import APP_VERSION
from src.modules.health.schemas import DetailedHealthResponse
from src.modules.health.service import HealthService
from src.utils import UTC
from src.utils.database import get_session

router = APIRouter()


class HealthResponse(BaseModel):
    """
    헬스체크 응답 스키마

    Attributes:
        status: 서버 상태 (healthy/unhealthy)
        timestamp: 현재 서버 시간 (UTC)
        version: API 버전
    """

    status: str
    timestamp: datetime
    version: str = APP_VERSION


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    API 헬스체크

    서버가 정상 작동 중인지 확인합니다.
    로드 밸런서, 쿠버네티스, 모니터링 시스템에서 사용됩니다.

    Returns:
        HealthResponse: 상태, 타임스탬프, 버전 정보

    사용 예시:
        GET /api/v1/health
        응답: {"status": "healthy", "timestamp": "...", "version": "0.1.0"}
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
    )


@router.get("/health/detail", response_model=DetailedHealthResponse)
async def health_check_detail(
    session: AsyncSession = Depends(get_session),
) -> DetailedHealthResponse:
    """
    상세 헬스체크

    6개 핵심 구성요소의 상태를 확인합니다:
    1. database: DB 연결 (SELECT 1)
    2. upbit_api: Upbit API 연결
    3. gemini_api: Gemini AI API 연결
    4. scheduler: 스케줄러 상태
    5. recent_signal: 최근 1시간 내 신호 존재 여부
    6. recent_order: 활성 주문 상태

    Returns:
        DetailedHealthResponse: 전체 상태 및 구성요소별 상세 정보

    전체 상태 결정 규칙:
        - healthy: 모든 구성요소 정상
        - degraded: 일부 구성요소 warning 또는 비핵심 구성요소 unhealthy
        - unhealthy: 핵심 구성요소(DB, scheduler) unhealthy

    사용 예시:
        GET /api/v1/health/detail
        응답:
        {
            "status": "healthy",
            "timestamp": "2026-01-24T12:00:00Z",
            "version": "0.1.0",
            "components": [
                {"name": "database", "status": "healthy", "latency_ms": 1.2},
                ...
            ]
        }
    """
    service = HealthService(session)
    return await service.check_all()
