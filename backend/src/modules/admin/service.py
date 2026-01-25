"""
Admin 서비스 모듈

시스템 메트릭(CPU, 메모리, 디스크)과 스케줄러 상태를 조회합니다.
"""

import psutil

from src.modules.admin.schemas import SchedulerJobResponse, SystemMetricsResponse
from src.scheduler import get_scheduler_status

# 바이트 변환 상수
MB = 1024 * 1024
GB = 1024 * 1024 * 1024


def get_system_metrics() -> SystemMetricsResponse:
    """
    시스템 메트릭 조회

    CPU, 메모리, 디스크 사용량과 스케줄러 작업 상태를 반환합니다.

    Returns:
        SystemMetricsResponse: 시스템 메트릭
    """
    # CPU 사용률
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # 메모리 사용량
    memory = psutil.virtual_memory()
    memory_used_mb = memory.used / MB
    memory_total_mb = memory.total / MB

    # 디스크 사용량
    disk = psutil.disk_usage("/")
    disk_used_gb = disk.used / GB
    disk_total_gb = disk.total / GB

    # 스케줄러 작업 상태
    scheduler_status = get_scheduler_status()
    scheduler_jobs = []

    for job in scheduler_status.get("jobs", []):
        status = "running" if scheduler_status.get("running") else "stopped"
        if job.get("pending"):
            status = "stopped"

        scheduler_jobs.append(
            SchedulerJobResponse(
                name=job.get("name", job.get("id", "unknown")),
                status=status,
                last_run=None,  # APScheduler에서 last_run 정보 없음
                next_run=job.get("next_run_time"),
            )
        )

    return SystemMetricsResponse(
        cpu_percent=round(cpu_percent, 1),
        memory_percent=round(memory.percent, 1),
        memory_used_mb=round(memory_used_mb, 1),
        memory_total_mb=round(memory_total_mb, 1),
        disk_percent=round(disk.percent, 1),
        disk_used_gb=round(disk_used_gb, 1),
        disk_total_gb=round(disk_total_gb, 1),
        scheduler_jobs=scheduler_jobs,
    )
