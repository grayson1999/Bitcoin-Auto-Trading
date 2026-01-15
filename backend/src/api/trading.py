"""
거래 API 엔드포인트 모듈

이 모듈은 거래 관련 API를 제공합니다.
- 주문 목록 조회 (GET /trading/orders)
- 주문 상세 조회 (GET /trading/orders/{order_id})
- 포지션 조회 (GET /trading/position)
- 잔고 조회 (GET /trading/balance)
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.order import (
    BalanceResponse,
    OrderListResponse,
    OrderResponse,
    OrderStatusFilterEnum,
    PositionResponse,
)
from src.database import get_session
from src.models import OrderStatus, Position
from src.services.order_executor import get_order_executor
from src.services.upbit_client import UpbitError, get_upbit_client

# 화폐 코드 상수
CURRENCY_KRW = "KRW"
CURRENCY_XRP = "XRP"

# === 상수 ===
DEFAULT_MARKET = "KRW-XRP"
MIN_LIMIT = 1  # 최소 조회 개수
MAX_LIMIT = 100  # 최대 조회 개수
DEFAULT_LIMIT = 50  # 기본 조회 개수

router = APIRouter(prefix="/trading")


# ==========================================================================
# T063: GET /trading/orders - 주문 목록 조회
# ==========================================================================


@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="주문 내역 조회",
    description="주문 목록을 조회합니다. 상태별 필터링 가능합니다.",
)
async def get_orders(
    session: Annotated[AsyncSession, Depends(get_session)],
    status: Annotated[
        OrderStatusFilterEnum,
        Query(description="주문 상태 필터"),
    ] = OrderStatusFilterEnum.ALL,
    limit: Annotated[
        int,
        Query(ge=MIN_LIMIT, le=MAX_LIMIT, description="최대 조회 개수 (1-100)"),
    ] = DEFAULT_LIMIT,
    offset: Annotated[
        int,
        Query(ge=0, description="시작 위치"),
    ] = 0,
) -> OrderListResponse:
    """
    주문 내역 조회

    생성된 모든 주문을 조회합니다.
    상태별로 필터링할 수 있습니다.

    Args:
        session: 데이터베이스 세션
        status: 주문 상태 필터 (all/pending/executed/cancelled/failed)
        limit: 최대 조회 개수 (기본: 50)
        offset: 시작 위치 (기본: 0)

    Returns:
        OrderListResponse: 주문 목록, 총 개수, limit, offset
    """
    executor = await get_order_executor(session)

    # 상태 필터 변환
    order_status = None
    if status != OrderStatusFilterEnum.ALL:
        status_map = {
            OrderStatusFilterEnum.PENDING: OrderStatus.PENDING,
            OrderStatusFilterEnum.EXECUTED: OrderStatus.EXECUTED,
            OrderStatusFilterEnum.CANCELLED: OrderStatus.CANCELLED,
            OrderStatusFilterEnum.FAILED: OrderStatus.FAILED,
        }
        order_status = status_map.get(status)

    orders, total = await executor.get_orders(
        status=order_status,
        limit=limit,
        offset=offset,
    )

    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        limit=limit,
        offset=offset,
    )


# ==========================================================================
# T064: GET /trading/orders/{order_id} - 주문 상세 조회
# ==========================================================================


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="주문 상세 조회",
    description="특정 주문의 상세 정보를 조회합니다.",
    responses={
        404: {"description": "주문 없음"},
    },
)
async def get_order(
    order_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderResponse:
    """
    주문 상세 조회

    특정 주문의 상세 정보를 반환합니다.
    주문이 없는 경우 404 오류를 반환합니다.

    Args:
        order_id: 주문 ID
        session: 데이터베이스 세션

    Returns:
        OrderResponse: 주문 상세 정보

    Raises:
        HTTPException: 주문이 없는 경우 404
    """
    executor = await get_order_executor(session)
    order = await executor.get_order_by_id(order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail=f"주문을 찾을 수 없습니다: {order_id}",
        )

    return OrderResponse.model_validate(order)


# ==========================================================================
# T065: GET /trading/position - 포지션 조회
# ==========================================================================


@router.get(
    "/position",
    response_model=PositionResponse,
    summary="현재 포지션 조회",
    description="현재 XRP 포지션 정보를 조회합니다.",
    responses={
        404: {"description": "포지션 없음"},
    },
)
async def get_position(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PositionResponse:
    """
    현재 포지션 조회

    현재 XRP-KRW 포지션 정보를 반환합니다.
    포지션이 없는 경우 빈 포지션을 반환합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        PositionResponse: 포지션 정보
    """
    stmt = select(Position).where(Position.symbol == DEFAULT_MARKET)
    result = await session.execute(stmt)
    position = result.scalar_one_or_none()

    if position is None:
        # 빈 포지션 반환
        from datetime import UTC, datetime

        return PositionResponse(
            symbol=DEFAULT_MARKET,
            quantity=Decimal("0"),
            avg_buy_price=Decimal("0"),
            current_value=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            unrealized_pnl_pct=0.0,
            updated_at=datetime.now(UTC),
        )

    # 현재가로 평가금액 업데이트
    try:
        upbit_client = get_upbit_client()
        ticker = await upbit_client.get_ticker(DEFAULT_MARKET)
        position.update_value(ticker.trade_price)
    except UpbitError as e:
        logger.warning(f"현재가 조회 실패, 마지막 평가금액 사용: {e.message}")

    return PositionResponse(
        symbol=position.symbol,
        quantity=position.quantity,
        avg_buy_price=position.avg_buy_price,
        current_value=position.current_value,
        unrealized_pnl=position.unrealized_pnl,
        unrealized_pnl_pct=position.pnl_pct,
        updated_at=position.updated_at,
    )


# ==========================================================================
# T066: GET /trading/balance - 잔고 조회
# ==========================================================================


@router.get(
    "/balance",
    response_model=BalanceResponse,
    summary="계좌 잔고 조회",
    description="Upbit 계좌 잔고(KRW, XRP)를 실시간 조회합니다.",
    responses={
        503: {"description": "Upbit API 오류"},
    },
)
async def get_balance(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BalanceResponse:
    """
    계좌 잔고 조회

    Upbit 계좌의 KRW, XRP 잔고를 실시간으로 조회합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        BalanceResponse: 잔고 정보

    Raises:
        HTTPException: Upbit API 오류 시 503
    """
    try:
        executor = await get_order_executor(session)
        balance_info = await executor._get_balance_info()
    except UpbitError as e:
        logger.error(f"잔고 조회 실패: {e.message}")
        raise HTTPException(
            status_code=503,
            detail=f"Upbit API 오류: {e.message}",
        ) from e

    return BalanceResponse(
        krw=balance_info.krw_available,
        krw_locked=balance_info.krw_locked,
        xrp=balance_info.xrp_available,
        xrp_locked=balance_info.xrp_locked,
        xrp_avg_buy_price=balance_info.xrp_avg_price,
        total_krw=balance_info.total_krw,
    )
