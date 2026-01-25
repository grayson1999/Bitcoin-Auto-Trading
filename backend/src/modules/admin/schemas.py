"""
Admin 모듈 스키마

시스템 메트릭 및 스케줄러 상태 응답 스키마를 정의합니다.
"""

from pydantic import BaseModel, Field


class SchedulerJobResponse(BaseModel):
    """스케줄러 작업 상태"""

    name: str = Field(..., description="작업 이름")
    status: str = Field(..., description="작업 상태 (running, stopped, error)")
    last_run: str | None = Field(None, description="마지막 실행 시간 (ISO 8601)")
    next_run: str | None = Field(None, description="다음 실행 예정 시간 (ISO 8601)")


class SystemMetricsResponse(BaseModel):
    """시스템 메트릭 응답"""

    cpu_percent: float = Field(..., description="CPU 사용률 (%)")
    memory_percent: float = Field(..., description="메모리 사용률 (%)")
    memory_used_mb: float = Field(..., description="사용 중인 메모리 (MB)")
    memory_total_mb: float = Field(..., description="전체 메모리 (MB)")
    disk_percent: float = Field(..., description="디스크 사용률 (%)")
    disk_used_gb: float = Field(..., description="사용 중인 디스크 (GB)")
    disk_total_gb: float = Field(..., description="전체 디스크 (GB)")
    scheduler_jobs: list[SchedulerJobResponse] = Field(
        default_factory=list, description="스케줄러 작업 목록"
    )
