"""
익절 체크 스케줄러 작업

5분마다 포지션 수익률을 체크하고 단계적 부분 매도를 실행합니다.
"""

from loguru import logger

from src.scheduler.metrics import track_job
from src.utils.database import async_session_factory


async def profit_taking_check_job() -> None:
    """
    익절 체크 작업 (5분 간격)

    포지션 수익률을 확인하고 티어별 부분 매도 및 트레일링 스탑을 실행합니다.

    처리 흐름:
        1. 현재 포지션 조회
        2. 현재가 대비 수익률 계산
        3. 익절 티어 조건 충족 시 부분 매도
        4. 트레일링 스탑 조건 충족 시 나머지 전량 매도
    """
    from src.clients.upbit import get_upbit_private_api, get_upbit_public_api
    from src.entities import User
    from src.modules.trading.profit_taker import ProfitTaker

    async with track_job("profit_taking"), async_session_factory() as session:
        try:
            from sqlalchemy import select

            # 첫 번째 사용자 ID 조회
            result = await session.execute(
                select(User.id).order_by(User.id).limit(1)
            )
            user_id = result.scalar_one_or_none()
            if user_id is None:
                return

            profit_taker = ProfitTaker(
                session=session,
                private_api=get_upbit_private_api(),
                public_api=get_upbit_public_api(),
                user_id=user_id,
            )
            await profit_taker.check_and_execute()

        except Exception as e:
            await session.rollback()
            logger.exception(f"익절 체크 작업 오류: {e}")
            raise
