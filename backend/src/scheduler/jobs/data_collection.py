"""
데이터 수집 스케줄러 작업

시장 데이터 수집 작업을 정의합니다.
"""

from loguru import logger

from src.config.constants import DEFAULT_MAX_RETRIES
from src.utils.database import async_session_factory
from src.modules.market import get_data_collector


async def collect_market_data_job() -> None:
    """
    시장 데이터 수집 작업

    DATA_COLLECTION_INTERVAL_SECONDS 간격으로 Upbit에서 시세를 수집합니다.
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
            result = await collector.collect_with_retry(
                session, max_attempts=DEFAULT_MAX_RETRIES
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
