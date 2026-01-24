"""
상세 헬스체크 스키마

6개 구성요소의 상태를 보고하는 상세 헬스체크 응답 스키마입니다.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.config import APP_VERSION


class ComponentHealth(BaseModel):
    """
    개별 구성요소 상태

    Attributes:
        name: 구성요소 이름
        status: 상태 (healthy/unhealthy/warning)
        latency_ms: 응답 시간 (밀리초)
        message: 상세 메시지 (오류 시)
    """

    name: str
    status: Literal["healthy", "unhealthy", "warning"]
    latency_ms: float | None = None
    message: str | None = None


class DetailedHealthResponse(BaseModel):
    """
    상세 헬스체크 응답

    Attributes:
        status: 전체 시스템 상태
            - healthy: 모든 구성요소 정상
            - degraded: 일부 구성요소 경고/비정상
            - unhealthy: 핵심 구성요소 비정상
        timestamp: 체크 시간 (UTC)
        version: API 버전
        components: 6개 구성요소 상태 목록
    """

    status: Literal["healthy", "unhealthy", "degraded"]
    timestamp: datetime
    version: str = Field(default=APP_VERSION)
    components: list[ComponentHealth]
