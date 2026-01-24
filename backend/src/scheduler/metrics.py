"""
스케줄러 작업 메트릭 수집

구조화된 JSON 로그로 작업별 실행 시간, 성공률을 수집합니다.
journalctl에서 metric_type="job"으로 필터링하여 분석 가능합니다.

사용 예시:
    async with track_job("data_collection"):
        await collect_market_data()

로그 형식:
    {"metric_type": "job", "job_name": "...", "duration_ms": ..., "success": true, ...}

메트릭 로그 파일:
    logs/metrics.jsonl - JSON Lines 형식으로 메트릭 저장
"""

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

# 메트릭 전용 logger 바인딩
metrics_logger = logger.bind(metric_type="job")

# 메트릭 로그 파일 경로
METRICS_LOG_PATH = Path("logs/metrics.jsonl")


def _ensure_metrics_log_dir() -> None:
    """메트릭 로그 디렉토리 생성"""
    METRICS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _write_metric_json(metric_data: dict) -> None:
    """메트릭을 JSON Lines 형식으로 파일에 기록"""
    _ensure_metrics_log_dir()
    with METRICS_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(metric_data, ensure_ascii=False) + "\n")


@asynccontextmanager
async def track_job(job_name: str) -> AsyncGenerator[None, None]:
    """
    작업 실행 시간과 성공 여부를 추적하는 컨텍스트 매니저

    Args:
        job_name: 추적할 작업 이름 (예: "data_collection", "signal_generation")

    Yields:
        None: 작업 실행 컨텍스트 제공

    Example:
        async with track_job("data_collection"):
            await collect_market_data()

    로그 필드:
        - metric_type: "job" (고정)
        - job_name: 작업 이름
        - duration_ms: 실행 시간 (밀리초)
        - success: 성공 여부 (True/False)
        - error: 에러 메시지 (실패 시)
        - timestamp: 완료 시각 (ISO 8601)
    """
    import time

    start = time.perf_counter()
    success = True
    error_msg: str | None = None

    try:
        yield
    except Exception as e:
        success = False
        error_msg = str(e)
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        timestamp = datetime.now(UTC).isoformat()

        # 구조화된 메트릭 데이터
        metric_data = {
            "metric_type": "job",
            "job_name": job_name,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "error": error_msg,
            "timestamp": timestamp,
        }

        # JSON Lines 파일에 메트릭 저장 (분석용)
        # 메트릭 저장 실패해도 작업은 계속 진행 (파일 I/O 오류만 무시)
        with suppress(OSError):
            _write_metric_json(metric_data)

        # 콘솔/파일 로그에도 기록
        metrics_logger.bind(
            job_name=job_name,
            duration_ms=round(duration_ms, 2),
            success=success,
            error=error_msg,
            timestamp=timestamp,
        ).info(f"Job {job_name} {'completed' if success else 'failed'}")
