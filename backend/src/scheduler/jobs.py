"""
APScheduler 작업 정의 모듈

이 모듈은 백그라운드에서 실행되는 예약 작업을 정의합니다.
- 시장 데이터 수집 (1초 간격)
- 오래된 데이터 정리 (24시간 간격)
"""

from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from src.database import async_session_factory
from src.services.data_collector import get_data_collector

# 스케줄러 인스턴스 (비동기)
scheduler = AsyncIOScheduler()

# === 작업 설정 상수 ===
DATA_COLLECTION_INTERVAL_SECONDS = 1  # 데이터 수집 주기 (초)
DATA_CLEANUP_INTERVAL_HOURS = 24  # 데이터 정리 주기 (시간)
JOB_MAX_RETRY_ATTEMPTS = 3  # 작업 최대 재시도 횟수


async def collect_market_data_job() -> None:
    """
    시장 데이터 수집 작업

    1초마다 실행되어 Upbit에서 실시간 시세를 수집합니다.
    네트워크 오류 시 자동 재시도를 수행합니다.

    처리 흐름:
        1. DataCollector 싱글톤 획득
        2. 새 DB 세션 생성
        3. 재시도 로직으로 데이터 수집
        4. 성공 시 커밋, 실패 시 롤백
    """
    collector = get_data_collector()

    async with async_session_factory() as session:
        try:
            # 재시도 로직 포함 데이터 수집
            result = await collector.collect_with_retry(
                session, max_attempts=JOB_MAX_RETRY_ATTEMPTS
            )

            if result:
                await session.commit()
                logger.debug(
                    f"시장 데이터 수집 완료: 가격={result.price}, "
                    f"시간={result.timestamp}"
                )
            else:
                logger.warning("재시도 후에도 시장 데이터 수집 실패")

        except Exception as e:
            await session.rollback()
            logger.exception(f"데이터 수집 작업 오류: {e}")


async def cleanup_old_data_job() -> None:
    """
    오래된 데이터 정리 작업

    매일 실행되어 보관 기간이 지난 시장 데이터를 삭제합니다.
    설정의 data_retention_days 값을 기준으로 삭제합니다.
    """
    collector = get_data_collector()

    async with async_session_factory() as session:
        try:
            # 오래된 데이터 삭제
            deleted_count = await collector.cleanup_old_data(session)
            await session.commit()

            if deleted_count > 0:
                logger.info(f"데이터 정리 완료: {deleted_count}건 삭제")

        except Exception as e:
            await session.rollback()
            logger.exception(f"데이터 정리 작업 오류: {e}")


def setup_scheduler() -> AsyncIOScheduler:
    """
    스케줄러 설정

    모든 예약 작업을 등록하고 설정된 스케줄러를 반환합니다.

    등록되는 작업:
        - collect_market_data: 1초마다 시세 수집
        - cleanup_old_data: 24시간마다 오래된 데이터 삭제

    설정 옵션:
        - replace_existing: 기존 작업 교체
        - max_instances: 동시 실행 인스턴스 수 (1개)
        - coalesce: 놓친 실행 병합 (스킵)

    Returns:
        AsyncIOScheduler: 설정된 스케줄러 인스턴스
    """
    # 시장 데이터 수집 작업 (1초 간격)
    scheduler.add_job(
        collect_market_data_job,
        trigger=IntervalTrigger(seconds=DATA_COLLECTION_INTERVAL_SECONDS),
        id="collect_market_data",
        name="시장 데이터 수집",
        replace_existing=True,  # 기존 작업 교체
        max_instances=1,  # 동시 1개만 실행
        coalesce=True,  # 놓친 실행은 스킵
    )

    # 데이터 정리 작업 (24시간 간격)
    scheduler.add_job(
        cleanup_old_data_job,
        trigger=IntervalTrigger(hours=DATA_CLEANUP_INTERVAL_HOURS),
        id="cleanup_old_data",
        name="오래된 데이터 정리",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        f"스케줄러 설정 완료: "
        f"데이터 수집 ({DATA_COLLECTION_INTERVAL_SECONDS}초), "
        f"데이터 정리 ({DATA_CLEANUP_INTERVAL_HOURS}시간)"
    )

    return scheduler


def start_scheduler() -> None:
    """
    스케줄러 시작

    스케줄러가 실행 중이 아니면 시작합니다.
    이미 실행 중이면 아무 작업도 수행하지 않습니다.
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("스케줄러 시작됨")


def stop_scheduler() -> None:
    """
    스케줄러 중지

    스케줄러가 실행 중이면 중지합니다.
    wait=False로 즉시 종료합니다.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)  # 즉시 종료
        logger.info("스케줄러 중지됨")


def get_scheduler_status() -> dict[str, Any]:
    """
    스케줄러 상태 조회

    현재 스케줄러 상태와 등록된 작업 정보를 반환합니다.

    Returns:
        dict: 스케줄러 상태 정보
            - running: 실행 중 여부
            - jobs: 등록된 작업 목록
                - id: 작업 ID
                - name: 작업 이름
                - next_run_time: 다음 실행 시간
                - pending: 대기 중 여부
            - timestamp: 조회 시간
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat()
                if job.next_run_time
                else None,
                "pending": job.pending,
            }
        )

    return {
        "running": scheduler.running,
        "jobs": jobs,
        "timestamp": datetime.now(UTC).isoformat(),
    }
