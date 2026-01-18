"""
리스크 관리 API 엔드포인트 모듈

이 모듈은 리스크 관리 관련 API를 제공합니다.
- 리스크 이벤트 조회 (GET /risk/events) - T050
- 리스크 상태 조회 (GET /risk/status) - T051
- 거래 중단 (POST /risk/halt) - T052
- 거래 재개 (POST /risk/resume) - T053
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser
from src.api.schemas.risk import (
    HaltTradingRequest,
    HaltTradingResponse,
    ResumeTradingResponse,
    RiskEventListResponse,
    RiskEventResponse,
    RiskEventTypeEnum,
    RiskStatusResponse,
)
from src.config import settings
from src.database import get_session
from src.models import RiskEventType
from src.services.risk_manager import RiskManagerError, get_risk_manager

# === 상수 ===
MIN_LIMIT = 1  # 최소 조회 개수
MAX_LIMIT = 100  # 최대 조회 개수
DEFAULT_LIMIT = 50  # 기본 조회 개수

router = APIRouter(prefix="/risk")


# =============================================================================
# T050: GET /risk/events - 리스크 이벤트 조회
# =============================================================================


@router.get(
    "/events",
    response_model=RiskEventListResponse,
    summary="리스크 이벤트 조회",
    description="최근 발생한 리스크 이벤트 목록을 조회합니다.",
)
async def get_risk_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    limit: Annotated[
        int,
        Query(ge=MIN_LIMIT, le=MAX_LIMIT, description="최대 조회 개수 (1-100)"),
    ] = DEFAULT_LIMIT,
    event_type: Annotated[
        RiskEventTypeEnum | None,
        Query(description="이벤트 타입 필터"),
    ] = None,
) -> RiskEventListResponse:
    """
    리스크 이벤트 조회

    최근 발생한 리스크 이벤트 목록을 조회합니다.
    이벤트 타입으로 필터링할 수 있습니다.

    Args:
        session: 데이터베이스 세션
        limit: 최대 조회 개수 (기본: 50)
        event_type: 이벤트 타입 필터 (선택)

    Returns:
        RiskEventListResponse: 이벤트 목록과 총 개수
    """
    risk_manager = await get_risk_manager(session)

    # 이벤트 타입 변환
    filter_type = None
    if event_type:
        filter_type = RiskEventType(event_type.value)

    events = await risk_manager.get_recent_events(
        limit=limit,
        event_type=filter_type,
    )

    return RiskEventListResponse(
        items=[RiskEventResponse.model_validate(e) for e in events],
        total=len(events),
    )


# =============================================================================
# T051: GET /risk/status - 리스크 상태 조회
# =============================================================================


@router.get(
    "/status",
    response_model=RiskStatusResponse,
    summary="리스크 상태 조회",
    description="현재 리스크 관리 시스템의 상태를 조회합니다.",
)
async def get_risk_status(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> RiskStatusResponse:
    """
    리스크 상태 조회

    현재 리스크 관리 시스템의 상태를 조회합니다.
    거래 가능 여부, 일일 손익률, 변동성 등의 정보를 포함합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        RiskStatusResponse: 현재 리스크 상태
    """
    risk_manager = await get_risk_manager(session)
    status = await risk_manager.get_risk_status()

    return RiskStatusResponse(
        trading_enabled=status.trading_enabled,
        daily_loss_pct=status.daily_loss_pct,
        daily_loss_limit_pct=status.daily_loss_limit_pct,
        position_size_pct=status.position_size_pct,
        stop_loss_pct=status.stop_loss_pct,
        volatility_threshold_pct=status.volatility_threshold_pct,
        current_volatility_pct=status.current_volatility_pct,
        is_halted=status.is_halted,
        halt_reason=status.halt_reason,
        last_check_at=status.last_check_at,
        # AI 신호 설정값 (환경변수에서 로드, 0.015 -> 1.5% 변환)
        signal_stop_loss_pct=settings.signal_stop_loss_pct * 100,
        signal_take_profit_pct=settings.signal_take_profit_pct * 100,
        signal_trailing_stop_pct=settings.signal_trailing_stop_pct * 100,
        signal_breakeven_pct=settings.signal_breakeven_pct * 100,
    )


# =============================================================================
# T052: POST /risk/halt - 거래 중단
# =============================================================================


@router.post(
    "/halt",
    response_model=HaltTradingResponse,
    summary="거래 중단",
    description="수동으로 거래를 중단합니다.",
    responses={
        400: {"description": "이미 중단 상태"},
    },
)
async def halt_trading(
    session: Annotated[AsyncSession, Depends(get_session)],
    request: HaltTradingRequest,
    current_user: CurrentUser,
) -> HaltTradingResponse:
    """
    거래 중단

    수동으로 거래를 중단합니다.
    이미 중단 상태인 경우 400 오류를 반환합니다.

    Args:
        session: 데이터베이스 세션
        request: 중단 요청 (사유 포함)

    Returns:
        HaltTradingResponse: 중단 결과

    Raises:
        HTTPException: 이미 중단 상태인 경우 400
    """
    risk_manager = await get_risk_manager(session)

    # 현재 상태 확인
    if not await risk_manager.is_trading_enabled():
        raise HTTPException(
            status_code=400,
            detail="이미 거래가 중단된 상태입니다",
        )

    try:
        await risk_manager.halt_trading(reason=request.reason)
        await session.commit()

        logger.info(f"수동 거래 중단: {request.reason}")

        return HaltTradingResponse(
            success=True,
            message=f"거래가 중단되었습니다: {request.reason}",
            halted_at=datetime.now(UTC),
        )

    except RiskManagerError as e:
        logger.error(f"거래 중단 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래 중단 실패: {e}",
        ) from e


# =============================================================================
# T053: POST /risk/resume - 거래 재개
# =============================================================================


@router.post(
    "/resume",
    response_model=ResumeTradingResponse,
    summary="거래 재개",
    description="중단된 거래를 재개합니다.",
    responses={
        400: {"description": "이미 활성 상태"},
    },
)
async def resume_trading(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> ResumeTradingResponse:
    """
    거래 재개

    중단된 거래를 재개합니다.
    이미 활성 상태인 경우 400 오류를 반환합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        ResumeTradingResponse: 재개 결과

    Raises:
        HTTPException: 이미 활성 상태인 경우 400
    """
    risk_manager = await get_risk_manager(session)

    # 현재 상태 확인
    if await risk_manager.is_trading_enabled():
        raise HTTPException(
            status_code=400,
            detail="거래가 이미 활성 상태입니다",
        )

    try:
        await risk_manager.resume_trading()
        await session.commit()

        logger.info("수동 거래 재개")

        return ResumeTradingResponse(
            success=True,
            message="거래가 재개되었습니다",
            resumed_at=datetime.now(UTC),
        )

    except RiskManagerError as e:
        logger.error(f"거래 재개 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래 재개 실패: {e}",
        ) from e
