"""
Admin API 라우터

시스템 관리 관련 API 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter

from src.modules.admin.schemas import SystemMetricsResponse
from src.modules.admin.service import get_system_metrics

router = APIRouter(prefix="/admin")


@router.get(
    "/system",
    response_model=SystemMetricsResponse,
    summary="시스템 메트릭 조회",
    description="CPU, 메모리, 디스크 사용량과 스케줄러 작업 상태를 조회합니다.",
)
async def get_system_metrics_endpoint() -> SystemMetricsResponse:
    """
    시스템 메트릭 조회

    Returns:
        SystemMetricsResponse: 시스템 메트릭 (CPU, 메모리, 디스크, 스케줄러)
    """
    return get_system_metrics()
