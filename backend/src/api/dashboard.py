"""
대시보드 API 엔드포인트 모듈

이 모듈은 대시보드에서 사용하는 시장 데이터 관련 API를 제공합니다.
- 대시보드 요약 정보 (현재가, 포지션, 잔고, 일일 손익 등)
- 실시간 시세 조회 (Upbit API 직접 호출)
- 과거 데이터 조회 (DB에서 조회)
- 통계 요약 정보
- 데이터 수집기 상태 조회
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser
from src.api.schemas.dashboard import DashboardSummaryResponse
from src.api.schemas.market import (
    CollectorStatsResponse,
    CurrentMarketResponse,
    MarketDataListResponse,
    MarketDataResponse,
    MarketSummaryResponse,
)
from src.api.schemas.order import BalanceResponse, PositionResponse
from src.api.schemas.signal import TradingSignalResponse
from src.database import get_session
from src.models import (
    DailyStats,
    MarketData,
    Order,
    OrderStatus,
    Position,
    TradingSignal,
)
from src.config import settings
from src.services.data_collector import get_data_collector
from src.services.order_executor import get_order_executor
from src.services.risk_manager import get_risk_manager
from src.services.upbit_client import UpbitError, get_upbit_client

# === 상수 ===
MS_TO_SECONDS = 1000  # 밀리초 → 초 변환 상수
MIN_HOURS = 1  # 최소 조회 시간 (시간)
MAX_HOURS = 168  # 최대 조회 시간 (7일 = 168시간)
MIN_LIMIT = 1  # 최소 레코드 수
MAX_LIMIT_HISTORY = 1000  # 히스토리 최대 레코드 수
MAX_LIMIT_LATEST = 100  # 최신 데이터 최대 레코드 수
DEFAULT_HOURS = 24  # 기본 조회 시간
DEFAULT_LIMIT_HISTORY = 100  # 히스토리 기본 레코드 수
DEFAULT_LIMIT_LATEST = 10  # 최신 데이터 기본 레코드 수

router = APIRouter(prefix="/dashboard")


# ==========================================================================
# T070: GET /dashboard/summary - 대시보드 요약 정보
# ==========================================================================


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
    client = get_upbit_client()
    try:
        ticker = await client.get_ticker()
        current_price = ticker.trade_price

        # 24시간 변동률 계산
        change_24h_pct = None
        if ticker.low_price > 0:
            mid_price = (ticker.high_price + ticker.low_price) / 2
            if mid_price > 0:
                change_24h_pct = float(
                    (ticker.trade_price - mid_price) / mid_price * 100
                )
    except UpbitError as e:
        logger.error(f"시세 조회 실패: {e.message}")
        raise HTTPException(
            status_code=503,
            detail=f"시세 조회 실패: {e.message}",
        ) from e

    # === 2. 포지션 정보 조회 (Upbit 잔고와 동기화) ===
    position_response: PositionResponse | None = None

    # Upbit 실제 잔고와 Position 테이블 동기화
    try:
        executor = await get_order_executor(session)
        position = await executor.sync_position_from_upbit()
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
        accounts = await client.get_accounts()
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
    except UpbitError as e:
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
    risk_manager = await get_risk_manager(session)
    is_trading_active = await risk_manager.is_trading_enabled()

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


@router.get(
    "/market",
    response_model=CurrentMarketResponse,
    summary="현재 시세 조회",
    description="Upbit API에서 실시간 시세를 조회합니다.",
)
async def get_current_market(
    current_user: CurrentUser,
) -> CurrentMarketResponse:
    """
    현재 시세 조회

    Upbit API를 직접 호출하여 실시간 시세 정보를 반환합니다.
    DB에 저장된 데이터가 아닌 실시간 데이터입니다.

    Returns:
        CurrentMarketResponse: 현재가, 거래량, 24시간 통계

    Raises:
        HTTPException: Upbit API 오류 시 503 반환
    """
    client = get_upbit_client()

    try:
        ticker = await client.get_ticker()

        # 24시간 변동률 계산 (고가/저가 중간값 기준)
        change_24h_pct = None
        if ticker.low_price > 0:
            # 고가/저가의 중간값을 기준으로 변동률 근사치 계산
            mid_price = (ticker.high_price + ticker.low_price) / 2
            if mid_price > 0:
                change_24h_pct = float(
                    (ticker.trade_price - mid_price) / mid_price * 100
                )

        return CurrentMarketResponse(
            market=settings.trading_ticker,
            price=ticker.trade_price,
            volume_24h=ticker.acc_trade_volume_24h,
            high_24h=ticker.high_price,
            low_24h=ticker.low_price,
            timestamp=datetime.fromtimestamp(ticker.timestamp / MS_TO_SECONDS, tz=UTC),
            change_24h_pct=change_24h_pct,
        )

    except UpbitError as e:
        raise HTTPException(
            status_code=e.status_code or 503,
            detail=f"시세 조회 실패: {e.message}",
        ) from e


@router.get(
    "/market/history",
    response_model=MarketDataListResponse,
    summary="과거 시세 조회",
    description="데이터베이스에 저장된 과거 시세 데이터를 조회합니다.",
)
async def get_market_history(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    hours: Annotated[
        int,
        Query(ge=MIN_HOURS, le=MAX_HOURS, description="조회할 시간 범위 (1-168시간)"),
    ] = DEFAULT_HOURS,
    limit: Annotated[
        int,
        Query(
            ge=MIN_LIMIT, le=MAX_LIMIT_HISTORY, description="최대 레코드 수 (1-1000)"
        ),
    ] = DEFAULT_LIMIT_HISTORY,
    interval: Annotated[
        int | None,
        Query(ge=1, le=60, description="샘플링 간격 (분, 1-60). 지정 시 균등 간격으로 데이터 반환"),
    ] = None,
) -> MarketDataListResponse:
    """
    과거 시세 데이터 조회

    데이터베이스에 저장된 과거 시세 데이터를 시간 범위로 조회합니다.
    interval 파라미터로 시간당 N개 데이터를 균등 간격으로 가져올 수 있습니다.

    Args:
        session: 데이터베이스 세션
        hours: 조회할 시간 범위 (1-168시간, 기본값: 24)
        limit: 최대 반환 레코드 수 (1-1000, 기본값: 100)
        interval: 샘플링 간격 (분). 지정 시 해당 간격으로 데이터 샘플링

    Returns:
        MarketDataListResponse: 시세 데이터 목록과 총 개수
    """
    collector = get_data_collector()
    start_time = datetime.now(UTC) - timedelta(hours=hours)

    # 시간 범위 내 데이터 조회
    data = await collector.get_data_range(session, start_time)

    if interval and len(data) > 0:
        # interval 분 간격으로 데이터 샘플링 (시간대별 마지막 데이터 사용)
        sampled: dict[str, MarketData] = {}
        for d in data:
            # interval 분 단위로 시간 키 생성
            minute_bucket = (d.timestamp.minute // interval) * interval
            time_key = d.timestamp.replace(
                minute=minute_bucket, second=0, microsecond=0
            ).isoformat()
            sampled[time_key] = d  # 같은 버킷의 마지막 데이터 사용

        # 시간순 정렬
        data = sorted(sampled.values(), key=lambda x: x.timestamp)

    # limit 초과 시 최근 데이터만 반환
    data = data[-limit:] if len(data) > limit else data

    return MarketDataListResponse(
        items=[MarketDataResponse.model_validate(d) for d in data],
        total=len(data),
    )


@router.get(
    "/market/summary",
    response_model=MarketSummaryResponse,
    summary="시세 요약 통계",
    description="지정된 시간 동안의 시세 통계를 요약합니다.",
)
async def get_market_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    hours: Annotated[
        int,
        Query(ge=MIN_HOURS, le=MAX_HOURS, description="통계 기간 (1-168시간)"),
    ] = DEFAULT_HOURS,
) -> MarketSummaryResponse:
    """
    시세 요약 통계 조회

    지정된 시간 동안의 가격 변동 통계를 계산하여 반환합니다.

    Args:
        session: 데이터베이스 세션
        hours: 통계 기간 (1-168시간, 기본값: 24)

    Returns:
        MarketSummaryResponse: 최고가, 최저가, 변동률 등 통계
    """
    collector = get_data_collector()
    summary = await collector.get_hourly_summary(session, hours)
    return MarketSummaryResponse(**summary)


@router.get(
    "/market/latest",
    response_model=list[MarketDataResponse],
    summary="최신 시세 레코드 조회",
    description="데이터베이스에서 가장 최근에 저장된 시세 레코드를 조회합니다.",
)
async def get_latest_market_data(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    limit: Annotated[
        int,
        Query(ge=MIN_LIMIT, le=MAX_LIMIT_LATEST, description="레코드 수 (1-100)"),
    ] = DEFAULT_LIMIT_LATEST,
) -> list[MarketDataResponse]:
    """
    최신 시세 레코드 조회

    가장 최근에 수집된 시세 데이터를 조회합니다.

    Args:
        session: 데이터베이스 세션
        limit: 조회할 레코드 수 (1-100, 기본값: 10)

    Returns:
        list[MarketDataResponse]: 최신 시세 레코드 목록 (최신순)
    """
    collector = get_data_collector()
    data = await collector.get_latest(session, limit)
    return [MarketDataResponse.model_validate(d) for d in data]


@router.get(
    "/collector/stats",
    response_model=CollectorStatsResponse,
    summary="데이터 수집기 상태 조회",
    description="시장 데이터 수집기의 현재 상태와 통계를 조회합니다.",
)
async def get_collector_stats(
    current_user: CurrentUser,
) -> CollectorStatsResponse:
    """
    데이터 수집기 상태 조회

    시장 데이터 수집기의 실행 상태, 연속 실패 횟수,
    총 수집 건수 등의 통계를 반환합니다.

    Returns:
        CollectorStatsResponse: 수집기 상태 및 통계 정보
    """
    collector = get_data_collector()
    stats = collector.stats
    return CollectorStatsResponse(**stats)
