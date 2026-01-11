"""
대시보드 API 엔드포인트 모듈

이 모듈은 대시보드에서 사용하는 시장 데이터 관련 API를 제공합니다.
- 실시간 시세 조회 (Upbit API 직접 호출)
- 과거 데이터 조회 (DB에서 조회)
- 통계 요약 정보
- 데이터 수집기 상태 조회
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.market import (
    CollectorStatsResponse,
    CurrentMarketResponse,
    MarketDataListResponse,
    MarketDataResponse,
    MarketSummaryResponse,
)
from src.database import get_session
from src.services.data_collector import get_data_collector
from src.services.upbit_client import UpbitError, get_upbit_client

# === 상수 ===
DEFAULT_MARKET = "KRW-BTC"  # 기본 마켓 코드
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


@router.get(
    "/market",
    response_model=CurrentMarketResponse,
    summary="현재 시세 조회",
    description="Upbit API에서 실시간 BTC/KRW 시세를 조회합니다.",
)
async def get_current_market() -> CurrentMarketResponse:
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
        ticker = await client.get_ticker(DEFAULT_MARKET)

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
            market=DEFAULT_MARKET,
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
) -> MarketDataListResponse:
    """
    과거 시세 데이터 조회

    데이터베이스에 저장된 과거 시세 데이터를 시간 범위로 조회합니다.

    Args:
        session: 데이터베이스 세션
        hours: 조회할 시간 범위 (1-168시간, 기본값: 24)
        limit: 최대 반환 레코드 수 (1-1000, 기본값: 100)

    Returns:
        MarketDataListResponse: 시세 데이터 목록과 총 개수
    """
    collector = get_data_collector()
    start_time = datetime.now(UTC) - timedelta(hours=hours)

    # 시간 범위 내 데이터 조회
    data = await collector.get_data_range(session, start_time)

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
async def get_collector_stats() -> CollectorStatsResponse:
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
