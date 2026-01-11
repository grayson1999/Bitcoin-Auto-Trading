"""
헬스체크 엔드포인트 모듈

이 모듈은 API 서버의 상태를 확인하는 헬스체크 엔드포인트를 제공합니다.
- 로드 밸런서 및 모니터링 시스템에서 서버 상태 확인에 사용
- 현재 시간과 버전 정보 반환
"""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import APP_VERSION

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
