"""
APScheduler 스케줄러 설정 모듈

이 모듈은 APScheduler를 설정하고 관리하는 기능을 제공합니다.
실제 작업 로직은 jobs/ 패키지에 분리되어 있습니다.
"""

from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from src.config import settings
from src.config.constants import (
    DATA_CLEANUP_INTERVAL_HOURS,
    DATA_COLLECTION_INTERVAL_SECONDS,
    PENDING_ORDER_SYNC_MINUTES,
    SIGNAL_PERFORMANCE_EVAL_HOURS,
    VOLATILITY_CHECK_INTERVAL_SECONDS,
)
from src.scheduler.jobs import (
    check_volatility_job,
    cleanup_old_data_job,
    collect_market_data_job,
    evaluate_signal_performance_job,
    generate_trading_signal_job,
    sync_pending_orders_job,
)
from src.utils import UTC

# === 스케줄러 인스턴스 (비동기) ===
scheduler = AsyncIOScheduler()


def setup_scheduler() -> AsyncIOScheduler:
    """
    스케줄러 설정

    모든 예약 작업을 등록하고 설정된 스케줄러를 반환합니다.

    등록되는 작업:
        - collect_market_data: DATA_COLLECTION_INTERVAL_SECONDS마다 시세 수집
        - check_volatility: 30초마다 변동성 체크 및 자동 거래 중단
        - generate_trading_signal: 설정된 주기(기본 1시간)마다 AI 신호 생성
          → AI가 모든 기술적 지표 종합 분석하여 판단
          → 신뢰도 기반 포지션 사이징 (0.5=1%, 0.9+=3%)
        - cleanup_old_data: 24시간마다 오래된 데이터 삭제

    AI 자동 매매 흐름:
        1. generate_trading_signal_job에서 AI 신호 생성
        2. AI가 BUY/SELL/HOLD 결정 + 신뢰도 출력
        3. BUY/SELL 신호 시 신뢰도 기반 포지션 크기로 자동 매매
        4. 리스크 체크 → 잔고 확인 → 주문 실행 → 포지션 업데이트

    변동성 모니터링:
        1. 30초마다 최근 5분간의 가격 변동률 계산
        2. 임계값(기본 3%) 초과 시 자동 거래 중단
        3. 거래 재개는 수동으로 필요

    설정 옵션:
        - replace_existing: 기존 작업 교체
        - max_instances: 동시 실행 인스턴스 수 (1개)
        - coalesce: 놓친 실행 병합 (스킵)

    Returns:
        AsyncIOScheduler: 설정된 스케줄러 인스턴스
    """
    # 시장 데이터 수집 작업
    scheduler.add_job(
        collect_market_data_job,
        trigger=IntervalTrigger(seconds=DATA_COLLECTION_INTERVAL_SECONDS),
        id="collect_market_data",
        name="시장 데이터 수집",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # AI 신호 생성 작업 (설정된 간격, 기본 1시간)
    signal_interval_hours = settings.signal_interval_hours
    scheduler.add_job(
        generate_trading_signal_job,
        trigger=IntervalTrigger(hours=signal_interval_hours),
        id="generate_trading_signal",
        name="AI 매매 신호 생성",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # 데이터 정리 작업
    scheduler.add_job(
        cleanup_old_data_job,
        trigger=IntervalTrigger(hours=DATA_CLEANUP_INTERVAL_HOURS),
        id="cleanup_old_data",
        name="오래된 데이터 정리",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # 변동성 모니터링 작업
    scheduler.add_job(
        check_volatility_job,
        trigger=IntervalTrigger(seconds=VOLATILITY_CHECK_INTERVAL_SECONDS),
        id="check_volatility",
        name="변동성 모니터링",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # 신호 성과 평가 작업
    scheduler.add_job(
        evaluate_signal_performance_job,
        trigger=IntervalTrigger(hours=SIGNAL_PERFORMANCE_EVAL_HOURS),
        id="evaluate_signal_performance",
        name="신호 성과 평가",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # PENDING 주문 동기화 작업
    scheduler.add_job(
        sync_pending_orders_job,
        trigger=IntervalTrigger(minutes=PENDING_ORDER_SYNC_MINUTES),
        id="sync_pending_orders",
        name="PENDING 주문 동기화",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        f"스케줄러 설정 완료: "
        f"데이터 수집 ({DATA_COLLECTION_INTERVAL_SECONDS}초), "
        f"변동성 체크 ({VOLATILITY_CHECK_INTERVAL_SECONDS}초), "
        f"AI 신호 생성 ({signal_interval_hours}시간), "
        f"성과 평가 ({SIGNAL_PERFORMANCE_EVAL_HOURS}시간), "
        f"PENDING 동기화 ({PENDING_ORDER_SYNC_MINUTES}분), "
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
        scheduler.shutdown(wait=False)
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
