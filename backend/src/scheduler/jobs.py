"""
APScheduler 작업 정의 모듈

이 모듈은 백그라운드에서 실행되는 예약 작업을 정의합니다.
- 시장 데이터 수집 (1초 간격)
- AI 신호 생성 (1시간 간격)
- 자동 매매 실행 (신호 생성 후)
- 오래된 데이터 정리 (24시간 간격)
"""

from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from src.config import settings
from src.database import async_session_factory
from src.models import SignalType
from src.services.data_collector import get_data_collector
from src.services.order_executor import OrderExecutorError, get_order_executor
from src.services.risk_manager import RiskCheckResult, get_risk_manager
from src.services.signal_generator import SignalGeneratorError, get_signal_generator

# 스케줄러 인스턴스 (비동기)
scheduler = AsyncIOScheduler()

# === 작업 설정 상수 ===
DATA_COLLECTION_INTERVAL_SECONDS = 1  # 데이터 수집 주기 (초)
DATA_CLEANUP_INTERVAL_HOURS = 24  # 데이터 정리 주기 (시간)
VOLATILITY_CHECK_INTERVAL_SECONDS = 30  # 변동성 체크 주기 (초)
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


async def check_volatility_job() -> None:
    """
    변동성 모니터링 작업

    30초마다 실행되어 시장 변동성을 체크하고,
    임계값을 초과하면 자동으로 거래를 중단합니다.

    처리 흐름:
        1. RiskManager 인스턴스 생성
        2. 최근 5분간의 변동성 계산
        3. 임계값 초과 시 거래 중단
        4. 변동성 정상화 시 별도 조치 없음 (수동 재개 필요)
    """
    async with async_session_factory() as session:
        try:
            risk_manager = await get_risk_manager(session)

            # 변동성 체크
            result, volatility_pct, message = await risk_manager.check_volatility()

            if result == RiskCheckResult.BLOCKED:
                # 고변동성 감지 - 거래 중단
                logger.warning(f"고변동성 감지로 거래 중단: {volatility_pct:.2f}%")
                await risk_manager.halt_trading(
                    f"고변동성 자동 감지: {volatility_pct:.2f}% (5분 내)"
                )
                await session.commit()

            elif result == RiskCheckResult.WARNING:
                # 경고 수준 - 로그만 기록
                logger.info(f"변동성 경고: {message}")

            # PASS는 로그 없음 (너무 많은 로그 방지)

        except Exception as e:
            await session.rollback()
            logger.exception(f"변동성 체크 작업 오류: {e}")


async def generate_trading_signal_job() -> None:
    """
    AI 매매 신호 생성 작업

    설정된 주기(기본 1시간)마다 실행되어 Gemini AI를 통해
    매매 신호를 생성합니다.

    처리 흐름:
        1. SignalGenerator 인스턴스 생성
        2. 최근 시장 데이터 분석
        3. AI 호출하여 신호 생성
        4. 결과 DB 저장
        5. 신호가 BUY/SELL이면 자동 매매 실행
    """
    async with async_session_factory() as session:
        try:
            generator = get_signal_generator(session)

            # 스케줄러에서 호출 시 쿨다운 무시 (force=True)
            signal = await generator.generate_signal(force=True)

            logger.info(
                f"AI 신호 생성 완료: {signal.signal_type} "
                f"(신뢰도: {signal.confidence}, 모델: {signal.model_name})"
            )

            # T067: 신호가 BUY 또는 SELL이면 자동 매매 실행
            if signal.signal_type in (SignalType.BUY.value, SignalType.SELL.value):
                await execute_trading_from_signal_job(signal.id)

        except SignalGeneratorError as e:
            logger.warning(f"AI 신호 생성 실패: {e}")

        except Exception as e:
            await session.rollback()
            logger.exception(f"AI 신호 생성 작업 오류: {e}")


async def execute_trading_from_signal_job(signal_id: int) -> None:
    """
    T067: 신호에 따른 자동 매매 실행 작업

    AI 신호가 BUY 또는 SELL인 경우 리스크 체크 후 주문을 실행합니다.

    처리 흐름:
        1. 신호 조회
        2. 거래 활성화 상태 확인
        3. 리스크 체크 (일일 손실 한도, 변동성, 포지션 크기)
        4. 잔고 확인
        5. 주문 실행
        6. 포지션 및 통계 업데이트

    Args:
        signal_id: 실행할 신호 ID
    """
    from sqlalchemy import select

    from src.models import TradingSignal

    async with async_session_factory() as session:
        try:
            # 1. 신호 조회
            stmt = select(TradingSignal).where(TradingSignal.id == signal_id)
            result = await session.execute(stmt)
            signal = result.scalar_one_or_none()

            if signal is None:
                logger.error(f"신호를 찾을 수 없음: signal_id={signal_id}")
                return

            logger.info(
                f"자동 매매 실행 시작: signal_id={signal_id}, "
                f"type={signal.signal_type}, confidence={signal.confidence}"
            )

            # 2. OrderExecutor 생성 및 주문 실행
            executor = await get_order_executor(session)
            order_result = await executor.execute_from_signal(signal)

            if order_result.success:
                if order_result.order:
                    logger.info(
                        f"자동 매매 완료: order_id={order_result.order.id}, "
                        f"status={order_result.order.status}, "
                        f"message={order_result.message}"
                    )
                else:
                    logger.info(f"자동 매매 결과: {order_result.message}")
            else:
                logger.warning(
                    f"자동 매매 실패: {order_result.message}, "
                    f"reason={order_result.blocked_reason}"
                )

        except OrderExecutorError as e:
            logger.error(f"자동 매매 오류: {e.message}")

        except Exception as e:
            await session.rollback()
            logger.exception(f"자동 매매 작업 오류: {e}")


def setup_scheduler() -> AsyncIOScheduler:
    """
    스케줄러 설정

    모든 예약 작업을 등록하고 설정된 스케줄러를 반환합니다.

    등록되는 작업:
        - collect_market_data: 1초마다 시세 수집
        - check_volatility: 30초마다 변동성 체크 및 자동 거래 중단
        - generate_trading_signal: 설정된 주기(기본 1시간)마다 AI 신호 생성
          → 신호가 BUY/SELL이면 자동으로 execute_trading_from_signal_job 호출
        - cleanup_old_data: 24시간마다 오래된 데이터 삭제

    자동 매매 흐름:
        1. generate_trading_signal_job에서 AI 신호 생성
        2. 신호가 BUY 또는 SELL인 경우 execute_trading_from_signal_job 호출
        3. 리스크 체크 → 잔고 확인 → 주문 실행 → 포지션 업데이트

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

    # AI 신호 생성 작업 (설정된 간격, 기본 1시간)
    signal_interval_hours = settings.signal_interval_hours
    scheduler.add_job(
        generate_trading_signal_job,
        trigger=IntervalTrigger(hours=signal_interval_hours),
        id="generate_trading_signal",
        name="AI 매매 신호 생성",
        replace_existing=True,
        max_instances=1,
        coalesce=True,  # 놓친 실행은 스킵 (AI 비용 절약)
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

    # 변동성 모니터링 작업 (30초 간격)
    scheduler.add_job(
        check_volatility_job,
        trigger=IntervalTrigger(seconds=VOLATILITY_CHECK_INTERVAL_SECONDS),
        id="check_volatility",
        name="변동성 모니터링",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        f"스케줄러 설정 완료: "
        f"데이터 수집 ({DATA_COLLECTION_INTERVAL_SECONDS}초), "
        f"변동성 체크 ({VOLATILITY_CHECK_INTERVAL_SECONDS}초), "
        f"AI 신호 생성 ({signal_interval_hours}시간), "
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
