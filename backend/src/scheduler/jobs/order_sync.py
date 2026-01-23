"""
주문 동기화 스케줄러 작업

PENDING 상태의 주문을 Upbit와 동기화하는 작업을 정의합니다.
"""

from loguru import logger

from src.modules.trading.service import get_trading_service
from src.utils.database import async_session_factory


async def sync_pending_orders_job() -> None:
    """
    PENDING 주문 동기화 작업

    5분마다 실행되어 PENDING 상태로 남은 주문을 Upbit와 동기화합니다.
    체결 확인 타임아웃으로 PENDING 상태가 된 주문들을 복구합니다.

    처리 흐름:
        1. 24시간 이내의 PENDING 주문 조회
        2. 각 주문의 Upbit 상태 확인
        3. 체결 완료(done) → 포지션 및 통계 업데이트
        4. 취소(cancel) → CANCELLED로 변경
    """
    async with async_session_factory() as session:
        try:
            trading_service = await get_trading_service(session)
            synced_count = await trading_service.sync_pending_orders()

            if synced_count > 0:
                logger.info(f"PENDING 주문 동기화 완료: {synced_count}건")

        except Exception as e:
            await session.rollback()
            logger.exception(f"PENDING 주문 동기화 작업 오류: {e}")
