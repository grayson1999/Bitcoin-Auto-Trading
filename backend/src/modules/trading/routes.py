"""
거래 API 엔드포인트 모듈

이 모듈은 거래 관련 API를 제공합니다.
- 주문 목록 조회 (GET /trading/orders)
- 주문 상세 조회 (GET /trading/orders/{order_id})
- 포지션 조회 (GET /trading/position)
- 잔고 조회 (GET /trading/balance)
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import (
    UpbitPrivateAPIError,
    UpbitPublicAPIError,
    get_upbit_public_api,
)
from src.config import settings
from src.config.constants import (
    API_PAGINATION_DEFAULT_LIMIT,
    API_PAGINATION_MAX_LIMIT,
    API_PAGINATION_MIN_LIMIT,
)
from src.utils.database import get_session
from src.entities import OrderStatus, Position
from src.modules.auth import CurrentUser
from src.modules.trading.schemas import (
    BalanceResponse,
    OrderListResponse,
    OrderResponse,
    OrderStatusFilterEnum,
    PositionResponse,
)
from src.modules.trading.service import get_trading_service
from src.utils import UTC

router = APIRouter(prefix="/trading")


# ==========================================================================
# GET /trading/orders - 주문 목록 조회
# ==========================================================================


@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="주문 내역 조회",
    description="주문 목록을 조회합니다. 상태별 필터링 가능합니다.",
)
async def get_orders(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    status: Annotated[
        OrderStatusFilterEnum,
        Query(description="주문 상태 필터"),
    ] = OrderStatusFilterEnum.ALL,
    limit: Annotated[
        int,
        Query(
            ge=API_PAGINATION_MIN_LIMIT,
            le=API_PAGINATION_MAX_LIMIT,
            description="최대 조회 개수 (1-100)",
        ),
    ] = API_PAGINATION_DEFAULT_LIMIT,
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
    service = await get_trading_service(session)

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

    orders, total = await service.get_orders(
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
# GET /trading/orders/{order_id} - 주문 상세 조회
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
    current_user: CurrentUser,
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
    service = await get_trading_service(session)
    order = await service.get_order_by_id(order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail=f"주문을 찾을 수 없습니다: {order_id}",
        )

    return OrderResponse.model_validate(order)


# ==========================================================================
# GET /trading/position - 포지션 조회
# ==========================================================================


@router.get(
    "/position",
    response_model=PositionResponse,
    summary="현재 포지션 조회",
    description="현재 거래 코인의 포지션 정보를 조회합니다.",
    responses={
        404: {"description": "포지션 없음"},
    },
)
async def get_position(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> PositionResponse:
    """
    현재 포지션 조회

    현재 거래 코인의 포지션 정보를 반환합니다.
    포지션이 없는 경우 빈 포지션을 반환합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        PositionResponse: 포지션 정보
    """
    stmt = select(Position).where(Position.symbol == settings.trading_ticker)
    result = await session.execute(stmt)
    position = result.scalar_one_or_none()

    if position is None:
        # 빈 포지션 반환
        return PositionResponse(
            symbol=settings.trading_ticker,
            quantity=Decimal("0"),
            avg_buy_price=Decimal("0"),
            current_value=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            unrealized_pnl_pct=0.0,
            updated_at=datetime.now(UTC),
        )

    # 현재가로 평가금액 업데이트
    try:
        public_api = get_upbit_public_api()
        ticker = await public_api.get_ticker()
        position.update_value(ticker.trade_price)
    except UpbitPublicAPIError as e:
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
# GET /trading/balance - 잔고 조회
# ==========================================================================


@router.get(
    "/balance",
    response_model=BalanceResponse,
    summary="계좌 잔고 조회",
    description="Upbit 계좌 잔고(KRW, 거래 코인)를 실시간 조회합니다.",
    responses={
        503: {"description": "Upbit API 오류"},
    },
)
async def get_balance(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> BalanceResponse:
    """
    계좌 잔고 조회

    Upbit 계좌의 KRW, 거래 코인 잔고를 실시간으로 조회합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        BalanceResponse: 잔고 정보

    Raises:
        HTTPException: Upbit API 오류 시 503
    """
    try:
        service = await get_trading_service(session)
        balance_info = await service.get_balance_info()
    except (UpbitPrivateAPIError, UpbitPublicAPIError) as e:
        logger.error(f"잔고 조회 실패: {e.message}")
        raise HTTPException(
            status_code=503,
            detail=f"Upbit API 오류: {e.message}",
        ) from e

    return BalanceResponse(
        krw=balance_info.krw_available,
        krw_locked=balance_info.krw_locked,
        coin=balance_info.coin_available,
        coin_locked=balance_info.coin_locked,
        coin_avg_buy_price=balance_info.coin_avg_price,
        total_krw=balance_info.total_krw,
    )


# ==========================================================================
# POST /trading/orders/sync - 대기 주문 동기화
# ==========================================================================


@router.post(
    "/orders/sync",
    summary="대기 주문 상태 동기화",
    description="PENDING 상태의 주문을 Upbit API로 확인하여 상태를 동기화합니다.",
)
async def sync_pending_orders(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> dict:
    """
    대기 주문 상태 동기화

    PENDING 상태의 모든 주문을 Upbit API로 조회하여
    실제 체결/취소 상태로 업데이트합니다.

    Returns:
        dict: 동기화 결과 (synced_count, message)
    """
    service = await get_trading_service(session)
    synced_count = await service.sync_pending_orders()

    if synced_count == 0:
        return {
            "synced_count": 0,
            "message": "대기 중인 주문 없음",
        }

    return {
        "synced_count": synced_count,
        "message": f"{synced_count}건의 주문 상태가 동기화되었습니다",
    }
