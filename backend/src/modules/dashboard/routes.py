"""
대시보드 API 엔드포인트 모듈

이 모듈은 대시보드 요약 정보를 제공합니다.
- 대시보드 요약 정보 (현재가, 포지션, 잔고, 일일 손익 등)

Market 관련 엔드포인트는 modules/market/routes.py로 이동:
- GET /market - 현재 시세 조회
- GET /market/history - 과거 시세 조회
- GET /market/summary - 시세 요약 통계
- GET /market/latest - 최신 시세 레코드 조회
- GET /market/collector/stats - 데이터 수집기 상태 조회
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import (
    UpbitPrivateAPIError,
    UpbitPublicAPIError,
    get_upbit_private_api,
    get_upbit_public_api,
)
from src.config import settings
from src.database import get_session
from src.entities import (
    DailyStats,
    Order,
    OrderStatus,
    Position,
    TradingSignal,
)
from src.modules.auth import CurrentUser
from src.modules.dashboard.schemas import DashboardSummaryResponse
from src.modules.risk.service import get_risk_service
from src.modules.signal import TradingSignalResponse
from src.modules.trading import BalanceResponse, PositionResponse
from src.modules.trading.service import get_trading_service
from src.utils import UTC

router = APIRouter(prefix="/dashboard")


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="대시보드 요약 정보",
    description="현재 가격, 포지션, 잔고, 일일 손익 등 대시보드에 필요한 전체 요약 정보를 조회합니다.",
)
async def get_dashboard_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> DashboardSummaryResponse:
    """
    대시보드 요약 정보 조회

    현재 시세, 포지션, 잔고, 일일 손익, 최신 AI 신호 등
    대시보드에 표시할 전체 요약 정보를 반환합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        DashboardSummaryResponse: 대시보드 요약 정보

    Raises:
        HTTPException: Upbit API 오류 시 503 반환
    """
    now = datetime.now(UTC)

    # === 1. 현재 시세 조회 ===
    public_api = get_upbit_public_api()
    try:
        ticker = await public_api.get_ticker()
        current_price = ticker.trade_price

        # 24시간 변동률 계산
        change_24h_pct = None
        if ticker.low_price > 0:
            mid_price = (ticker.high_price + ticker.low_price) / 2
            if mid_price > 0:
                change_24h_pct = float(
                    (ticker.trade_price - mid_price) / mid_price * 100
                )
    except UpbitPublicAPIError as e:
        logger.error(f"시세 조회 실패: {e.message}")
        raise HTTPException(
            status_code=503,
            detail=f"시세 조회 실패: {e.message}",
        ) from e

    # === 2. 포지션 정보 조회 (Upbit 잔고와 동기화) ===
    position_response: PositionResponse | None = None

    # Upbit 실제 잔고와 Position 테이블 동기화
    try:
        trading_service = await get_trading_service(session)
        position = await trading_service.sync_position_from_upbit()
        await session.commit()
    except Exception as e:
        logger.warning(f"포지션 동기화 실패: {e}")
        # 동기화 실패 시 기존 DB 데이터 조회
        stmt = select(Position).where(Position.symbol == settings.trading_ticker)
        result = await session.execute(stmt)
        position = result.scalar_one_or_none()

    if position is not None and position.quantity > 0:
        position.update_value(current_price)
        position_response = PositionResponse(
            symbol=position.symbol,
            quantity=position.quantity,
            avg_buy_price=position.avg_buy_price,
            current_value=position.current_value,
            unrealized_pnl=position.unrealized_pnl,
            unrealized_pnl_pct=position.pnl_pct,
            updated_at=position.updated_at,
        )

    # === 3. 잔고 정보 조회 ===
    balance_response: BalanceResponse | None = None
    try:
        private_api = get_upbit_private_api()
        accounts = await private_api.get_accounts()
        krw_balance = Decimal("0")
        krw_locked = Decimal("0")
        coin_balance = Decimal("0")
        coin_locked = Decimal("0")
        coin_avg_price = Decimal("0")

        for acc in accounts:
            if acc.currency == "KRW":
                krw_balance = acc.balance
                krw_locked = acc.locked
            elif acc.currency == settings.trading_currency:
                coin_balance = acc.balance
                coin_locked = acc.locked
                coin_avg_price = acc.avg_buy_price

        total_krw = (
            krw_balance + krw_locked + (coin_balance + coin_locked) * current_price
        )

        balance_response = BalanceResponse(
            krw=krw_balance,
            krw_locked=krw_locked,
            coin=coin_balance,
            coin_locked=coin_locked,
            coin_avg_buy_price=coin_avg_price,
            total_krw=total_krw,
        )
    except UpbitPrivateAPIError as e:
        logger.warning(f"잔고 조회 실패: {e.message}")

    # === 4. 일일 손익 조회 ===
    daily_pnl = Decimal("0")
    daily_pnl_pct = 0.0
    today = date.today()
    stmt_daily = select(DailyStats).where(DailyStats.date == today)
    result_daily = await session.execute(stmt_daily)
    daily_stats = result_daily.scalar_one_or_none()

    if daily_stats:
        daily_pnl = daily_stats.realized_pnl
        daily_pnl_pct = daily_stats.loss_pct

    # === 5. 최신 AI 신호 조회 ===
    latest_signal_response: TradingSignalResponse | None = None
    stmt_signal = (
        select(TradingSignal).order_by(TradingSignal.created_at.desc()).limit(1)
    )
    result_signal = await session.execute(stmt_signal)
    latest_signal = result_signal.scalar_one_or_none()

    if latest_signal:
        latest_signal_response = TradingSignalResponse.model_validate(latest_signal)

    # === 6. 거래 활성화 여부 조회 ===
    risk_service = get_risk_service(session)
    is_trading_active = await risk_service.is_trading_enabled()

    # === 7. 오늘 거래 횟수 조회 ===
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=UTC)
    stmt_orders = (
        select(func.count(Order.id))
        .where(Order.created_at >= today_start)
        .where(Order.status == OrderStatus.EXECUTED.value)
    )
    result_orders = await session.execute(stmt_orders)
    today_trade_count = result_orders.scalar() or 0

    return DashboardSummaryResponse(
        market=settings.trading_ticker,
        current_price=current_price,
        price_change_24h=change_24h_pct,
        position=position_response,
        balance=balance_response,
        daily_pnl=daily_pnl,
        daily_pnl_pct=daily_pnl_pct,
        latest_signal=latest_signal_response,
        is_trading_active=is_trading_active,
        today_trade_count=today_trade_count,
        updated_at=now,
    )
