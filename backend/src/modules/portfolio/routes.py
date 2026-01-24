"""
포트폴리오 API 엔드포인트 모듈

이 모듈은 포트폴리오 요약 정보를 제공합니다.
- 누적 수익률, 오늘 수익률
- 거래 통계 (승률, 총 거래 횟수)
- 30일 수익 차트 데이터
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import UpbitPrivateAPIError, get_upbit_private_api
from src.config import settings
from src.modules.auth import CurrentUser
from src.modules.portfolio.schemas import PortfolioSummaryResponse
from src.modules.portfolio.service import get_portfolio_service
from src.utils.database import get_session

router = APIRouter(prefix="/portfolio")


@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    summary="포트폴리오 요약 정보",
    description="누적 수익률, 거래 통계, 30일 수익 차트 등 포트폴리오 요약 정보를 조회합니다.",
)
async def get_portfolio_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> PortfolioSummaryResponse:
    """
    포트폴리오 요약 정보 조회

    DailyStats 테이블에서 거래 통계를 집계하고,
    Upbit API에서 현재 잔고를 조회하여 수익률을 계산합니다.

    Args:
        session: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        PortfolioSummaryResponse: 포트폴리오 요약 정보

    Raises:
        HTTPException: Upbit API 오류 시 503 반환
    """
    # 현재 Upbit 잔고 조회
    current_balance = Decimal("0")

    try:
        private_api = get_upbit_private_api()
        accounts = await private_api.get_accounts()

        krw_balance = Decimal("0")
        coin_balance = Decimal("0")
        current_price = Decimal("0")

        for acc in accounts:
            if acc.currency == "KRW":
                krw_balance = acc.balance + acc.locked
            elif acc.currency == settings.trading_currency:
                coin_balance = acc.balance + acc.locked

        # 현재 가격 조회 (코인 평가를 위해)
        if coin_balance > 0:
            from src.clients.upbit import get_upbit_public_api

            public_api = get_upbit_public_api()
            ticker = await public_api.get_ticker()
            current_price = ticker.trade_price

        current_balance = krw_balance + (coin_balance * current_price)

    except UpbitPrivateAPIError as e:
        logger.error(f"Upbit 잔고 조회 실패: {e.message}")
        raise HTTPException(
            status_code=503,
            detail=f"잔고 조회 실패: {e.message}",
        ) from e

    # 포트폴리오 서비스에서 요약 정보 계산
    portfolio_service = await get_portfolio_service(session)
    summary = await portfolio_service.get_portfolio_summary(current_balance)

    return summary
