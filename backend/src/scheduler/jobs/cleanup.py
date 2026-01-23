"""
데이터 정리 스케줄러 작업

오래된 시장 데이터 정리 작업을 정의합니다.
"""

from loguru import logger

from src.modules.market import get_market_service
from src.utils.database import async_session_factory


async def cleanup_old_data_job() -> None:
    """
    오래된 데이터 정리 작업

    매일 실행되어 보관 기간이 지난 시장 데이터를 삭제합니다.
    DATA_RETENTION_DAYS 상수 값을 기준으로 삭제합니다.
    """
    async with async_session_factory() as session:
        try:
            service = get_market_service(session)
            deleted_count = await service.cleanup_old_data()

            if deleted_count > 0:
                logger.info(f"데이터 정리 완료: {deleted_count}건 삭제")

        except Exception as e:
            await session.rollback()
            logger.exception(f"데이터 정리 작업 오류: {e}")
