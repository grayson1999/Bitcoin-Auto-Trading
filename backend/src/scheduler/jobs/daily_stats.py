"""
일일 통계(DailyStats) 자동 생성 스케줄러 작업

거래가 없는 날에도 DailyStats 레코드를 생성하여
포트폴리오 차트 및 수익률 계산의 데이터 연속성을 보장합니다.

동작:
- 서버 시작 시 및 매일 00:05 KST에 실행
- 오늘 DailyStats가 없으면 Upbit 잔고 기반으로 자동 생성
- 전일 ending_balance도 최신화
"""

from datetime import date, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import select

from src.clients.upbit import (
    UpbitPrivateAPIError,
    UpbitPublicAPIError,
    get_upbit_private_api,
    get_upbit_public_api,
)
from src.config import settings
from src.entities import DailyStats
from src.scheduler.metrics import track_job
from src.utils.database import async_session_factory


async def ensure_daily_stats_job() -> None:
    """
    오늘의 DailyStats 레코드 존재를 보장하는 작업

    거래가 없는 날에도 DailyStats를 생성하여:
    - 포트폴리오 차트에 오늘 데이터 포인트 추가
    - 전일 ending_balance를 최신 잔고로 갱신
    - 입금/출금 감지의 기준 데이터 확보
    """
    async with track_job("ensure_daily_stats"), async_session_factory() as session:
        try:
            today = date.today()

            # 오늘 DailyStats 존재 여부 확인
            stmt = select(DailyStats).where(DailyStats.date == today)
            result = await session.execute(stmt)
            today_stats = result.scalar_one_or_none()

            if today_stats:
                logger.debug("오늘 DailyStats 이미 존재함, 잔고 갱신만 수행")
                await _update_ending_balance(session, today_stats)
                await session.commit()
                return

            # 현재 Upbit 총 잔고 조회
            current_balance = await _get_current_total_balance()
            if current_balance is None:
                logger.warning("Upbit 잔고 조회 실패, DailyStats 생성 건너뜀")
                return

            # 전일 DailyStats ending_balance 갱신
            yesterday = today - timedelta(days=1)
            prev_stmt = select(DailyStats).where(DailyStats.date == yesterday)
            prev_result = await session.execute(prev_stmt)
            prev_stats = prev_result.scalar_one_or_none()

            if prev_stats:
                prev_stats.ending_balance = current_balance
                logger.info(
                    f"전일 ending_balance 갱신: {prev_stats.ending_balance:,.0f}"
                )

            # 가장 최근 DailyStats의 user_id 가져오기
            latest_stmt = select(DailyStats).order_by(DailyStats.date.desc()).limit(1)
            latest_result = await session.execute(latest_stmt)
            latest_stats = latest_result.scalar_one_or_none()
            user_id = latest_stats.user_id if latest_stats else 1

            # 오늘 DailyStats 생성 (거래 없음 상태)
            new_stats = DailyStats(
                user_id=user_id,
                date=today,
                starting_balance=current_balance,
                ending_balance=current_balance,
                realized_pnl=Decimal("0"),
                trade_count=0,
                win_count=0,
                loss_count=0,
                is_trading_halted=False,
                halt_reason=None,
            )
            session.add(new_stats)
            await session.commit()

            logger.info(
                f"오늘 DailyStats 자동 생성: "
                f"date={today}, balance={current_balance:,.0f}"
            )

        except Exception as e:
            await session.rollback()
            logger.exception(f"DailyStats 자동 생성 오류: {e}")
            raise


async def _get_current_total_balance() -> Decimal | None:
    """Upbit에서 현재 총 잔고(KRW + 코인평가) 조회"""
    try:
        private_api = get_upbit_private_api()
        accounts = await private_api.get_accounts()

        krw_balance = Decimal("0")
        coin_balance = Decimal("0")

        for acc in accounts:
            if acc.currency == "KRW":
                krw_balance = acc.balance + acc.locked
            elif acc.currency == settings.trading_currency:
                coin_balance = acc.balance + acc.locked

        current_price = Decimal("0")
        if coin_balance > 0:
            public_api = get_upbit_public_api()
            ticker = await public_api.get_ticker()
            current_price = ticker.trade_price

        return krw_balance + (coin_balance * current_price)

    except (UpbitPrivateAPIError, UpbitPublicAPIError) as e:
        logger.warning(f"잔고 조회 실패: {e}")
        return None
    except Exception as e:
        logger.warning(f"잔고 조회 중 오류: {e}")
        return None


async def _update_ending_balance(session, stats: DailyStats) -> None:
    """기존 DailyStats의 ending_balance를 최신 잔고로 갱신"""
    current_balance = await _get_current_total_balance()
    if current_balance is not None:
        stats.ending_balance = current_balance
