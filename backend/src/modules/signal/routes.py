"""
AI 매매 신호 API 엔드포인트 모듈

이 모듈은 AI 매매 신호 관련 API를 제공합니다.
- 신호 목록 조회 (GET /signals)
- 최신 신호 조회 (GET /signals/latest)
- 수동 신호 생성 (POST /signals/generate)
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constants import (
    API_PAGINATION_DEFAULT_LIMIT,
    API_PAGINATION_MAX_LIMIT,
    API_PAGINATION_MIN_LIMIT,
)
from src.entities import SignalType
from src.modules.auth import CurrentUser, ResolvedUser
from src.modules.signal.schemas import (
    GenerateSignalResponse,
    SignalFilterParams,
    TradingSignalListResponse,
    TradingSignalResponse,
)
from src.modules.signal.service import SignalServiceError, get_signal_service
from src.scheduler.jobs.signal_generation import execute_trading_from_signal_job
from src.utils.database import get_session

router = APIRouter(prefix="/signals")


@router.get(
    "",
    response_model=TradingSignalListResponse,
    summary="AI 신호 내역 조회",
    description="생성된 AI 매매 신호 목록을 조회합니다.",
)
async def get_signals(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    limit: Annotated[
        int,
        Query(
            ge=API_PAGINATION_MIN_LIMIT,
            le=API_PAGINATION_MAX_LIMIT,
            description="최대 조회 개수 (1-100)",
        ),
    ] = API_PAGINATION_DEFAULT_LIMIT,
    page: Annotated[
        int,
        Query(ge=1, description="페이지 번호 (기본: 1)"),
    ] = 1,
    signal_type: Annotated[
        SignalFilterParams,
        Query(description="신호 타입 필터 (all/BUY/HOLD/SELL)"),
    ] = SignalFilterParams.ALL,
) -> TradingSignalListResponse:
    """
    AI 신호 내역 조회

    생성된 모든 AI 매매 신호를 조회합니다.
    신호 타입으로 필터링할 수 있습니다.

    Args:
        session: 데이터베이스 세션
        limit: 최대 조회 개수 (기본: 50)
        page: 페이지 번호 (기본: 1)
        signal_type: 신호 타입 필터 (기본: all)

    Returns:
        TradingSignalListResponse: 신호 목록과 총 개수
    """
    service = get_signal_service(session)

    offset = (page - 1) * limit
    signal_type_val = (
        signal_type.value if signal_type != SignalFilterParams.ALL else None
    )

    signals = await service.get_signals(
        limit=limit,
        offset=offset,
        signal_type=signal_type_val,
    )

    total_count = await service.get_signals_count(signal_type=signal_type_val)

    return TradingSignalListResponse(
        items=[TradingSignalResponse.model_validate(s) for s in signals],
        total=total_count,
    )


@router.get(
    "/latest",
    response_model=TradingSignalResponse,
    summary="최신 AI 신호 조회",
    description="가장 최근에 생성된 AI 매매 신호를 조회합니다.",
    responses={
        404: {"description": "신호 없음"},
    },
)
async def get_latest_signal(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> TradingSignalResponse:
    """
    최신 AI 신호 조회

    가장 최근에 생성된 매매 신호를 반환합니다.
    신호가 없는 경우 404 오류를 반환합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        TradingSignalResponse: 최신 신호 정보

    Raises:
        HTTPException: 신호가 없는 경우 404
    """
    service = get_signal_service(session)
    signal = await service.get_latest_signal()

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="생성된 신호가 없습니다",
        )

    return TradingSignalResponse.model_validate(signal)


@router.post(
    "/generate",
    response_model=GenerateSignalResponse,
    summary="AI 신호 수동 생성",
    description="스케줄과 별개로 즉시 AI 신호를 생성합니다.",
    responses={
        429: {"description": "쿨다운 중 (5분 내 재요청)"},
        503: {"description": "AI API 오류"},
    },
)
async def generate_signal(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    resolved_user: ResolvedUser,
) -> GenerateSignalResponse:
    """
    AI 신호 수동 생성

    스케줄러와 별개로 즉시 새로운 매매 신호를 생성합니다.
    마지막 신호 생성 후 5분이 지나지 않았으면 429 오류를 반환합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        GenerateSignalResponse: 생성된 신호와 메시지

    Raises:
        HTTPException:
            - 429: 쿨다운 기간 내 재요청
            - 503: AI API 오류
    """
    service = get_signal_service(session)

    try:
        signal = await service.generate_signal(force=False, user_id=resolved_user.id)

        logger.info(
            f"수동 신호 생성 완료: {signal.signal_type} (신뢰도: {signal.confidence})"
        )

        # BUY/SELL 신호면 자동 매매 실행
        if signal.signal_type in (SignalType.BUY.value, SignalType.SELL.value):
            logger.info(f"자동 매매 트리거: signal_id={signal.id}")
            await execute_trading_from_signal_job(signal.id)

        return GenerateSignalResponse(
            signal=TradingSignalResponse.model_validate(signal),
            message="신호가 성공적으로 생성되었습니다",
        )

    except SignalServiceError as e:
        error_msg = str(e)

        # 쿨다운 오류
        if "쿨다운" in error_msg:
            raise HTTPException(
                status_code=429,
                detail=error_msg,
            ) from e

        # 시장 데이터 없음
        if "시장 데이터" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="분석할 시장 데이터가 없습니다. 데이터 수집을 확인하세요.",
            ) from e

        # AI Rate Limit 오류
        if "Rate Limit" in error_msg or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="AI API 요청 한도 초과. 잠시 후 다시 시도해주세요.",
            ) from e

        # AI API 오류
        logger.error(f"신호 생성 실패: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"신호 생성 실패: {error_msg}",
        ) from e


@router.post(
    "/generate-manual",
    response_model=GenerateSignalResponse,
    summary="테스트용 수동 신호 생성",
    description="AI를 거치지 않고 직접 매매 신호를 생성합니다 (테스트용).",
    responses={
        503: {"description": "시장 데이터 없음"},
    },
)
async def generate_manual_signal(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    resolved_user: ResolvedUser,
    signal_type: Annotated[
        Literal["BUY", "HOLD", "SELL"],
        Query(description="신호 타입 (BUY/HOLD/SELL)"),
    ],
    confidence: Annotated[
        float,
        Query(ge=0.0, le=1.0, description="신뢰도 (0.0~1.0)"),
    ] = 0.85,
    reasoning: Annotated[
        str,
        Query(description="신호 근거"),
    ] = "테스트용 수동 생성 신호",
) -> GenerateSignalResponse:
    """
    테스트용 수동 신호 생성

    AI를 거치지 않고 직접 BUY/SELL/HOLD 신호를 생성합니다.
    BUY/SELL 신호 생성 시 자동 거래가 실행됩니다.

    Args:
        session: 데이터베이스 세션
        signal_type: 신호 타입 (BUY/HOLD/SELL)
        confidence: 신뢰도 (0.0~1.0, 기본값: 0.85)
        reasoning: 신호 근거

    Returns:
        GenerateSignalResponse: 생성된 신호와 메시지
    """
    service = get_signal_service(session)

    try:
        signal = await service.create_manual_signal(
            signal_type=signal_type,
            confidence=confidence,
            reasoning=reasoning,
            user_id=resolved_user.id,
        )

        logger.info(
            f"수동 신호 생성 완료: {signal.signal_type} (신뢰도: {signal.confidence})"
        )

        # BUY/SELL 신호면 자동 매매 실행
        if signal.signal_type in (SignalType.BUY.value, SignalType.SELL.value):
            logger.info(f"자동 매매 트리거: signal_id={signal.id}")
            await execute_trading_from_signal_job(signal.id)

        return GenerateSignalResponse(
            signal=TradingSignalResponse.model_validate(signal),
            message=f"수동 신호가 성공적으로 생성되었습니다 ({signal.signal_type})",
        )

    except SignalServiceError as e:
        error_msg = str(e)

        # 시장 데이터 없음
        if "시장 데이터" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="분석할 시장 데이터가 없습니다. 데이터 수집을 확인하세요.",
            ) from e

        logger.error(f"수동 신호 생성 실패: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"수동 신호 생성 실패: {error_msg}",
        ) from e
