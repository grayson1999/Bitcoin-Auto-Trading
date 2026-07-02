"""
입출금 동기화 스케줄러 작업

Upbit 입금 원장(/v1/deposits)과 출금 원장(/v1/withdraws)을 BalanceAdjustment로
정기 동기화하여 포트폴리오 total_deposit(원금)이 실제 입출금을 정확히 반영하도록 한다.
잔고 차이 추정과 달리 코인 평가변동에 오염되지 않는다.
"""

from loguru import logger

from src.modules.portfolio.service import get_portfolio_service
from src.scheduler.metrics import track_job
from src.utils.database import async_session_factory


async def sync_deposits_job() -> None:
    """
    입출금 동기화 작업 (매일 1회 + 시작 백필)

    Upbit 입금/출금 원장을 조회해 봇 시작일 이후 신규 입출금을 BalanceAdjustment에
    기록한다. 중복은 date+amount로 방지. (잡 이름은 하위호환 위해 유지)
    """
    async with track_job("deposit_sync"), async_session_factory() as session:
        try:
            portfolio_service = await get_portfolio_service(session)
            deposits = await portfolio_service.sync_deposits_from_upbit()
            withdrawals = await portfolio_service.sync_withdrawals_from_upbit()
            await session.commit()

            if deposits > 0 or withdrawals > 0:
                logger.info(
                    f"입출금 동기화: 입금 {deposits}건, 출금 {withdrawals}건 신규 기록"
                )

        except Exception as e:
            await session.rollback()
            logger.exception(f"입출금 동기화 작업 오류: {e}")
            raise
