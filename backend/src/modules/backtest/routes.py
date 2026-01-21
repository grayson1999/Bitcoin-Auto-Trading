"""
백테스트 API 엔드포인트 모듈

이 모듈은 백테스트 관련 API를 제공합니다.
- 백테스트 실행 (POST /backtest/run)
- 결과 목록 조회 (GET /backtest/results)
- 결과 상세 조회 (GET /backtest/results/{result_id})
"""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser
from src.config.constants import (
    API_PAGINATION_DEFAULT_LIMIT,
    API_PAGINATION_MAX_LIMIT,
    API_PAGINATION_MIN_LIMIT,
)
from src.database import get_session
from src.modules.backtest.schemas import (
    BacktestRequest,
    BacktestResultDetailResponse,
    BacktestResultListResponse,
    BacktestResultResponse,
    BacktestRunResponse,
    BacktestStatusEnum,
    TradeRecord,
)
from src.modules.backtest.service import (
    BacktestServiceError,
    get_backtest_service,
)

router = APIRouter(prefix="/backtest")


@router.post(
    "/run",
    response_model=BacktestRunResponse,
    summary="백테스트 실행",
    description="과거 데이터로 AI 전략을 시뮬레이션합니다.",
    responses={
        400: {"description": "잘못된 요청 (기간 오류 등)"},
        503: {"description": "백테스트 실행 실패"},
    },
)
async def run_backtest(
    request: BacktestRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> BacktestRunResponse:
    """
    백테스트 실행

    지정된 기간의 과거 데이터로 AI 전략을 시뮬레이션하고
    수익률, MDD, 승률 등의 성과 지표를 계산합니다.

    Args:
        request: 백테스트 요청 데이터
        session: 데이터베이스 세션

    Returns:
        BacktestRunResponse: 백테스트 결과

    Raises:
        HTTPException:
            - 400: 잘못된 요청
            - 503: 실행 실패
    """
    service = get_backtest_service(session)

    try:
        result = await service.run_backtest(
            name=request.name,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
        )

        logger.info(
            f"백테스트 완료: {request.name} - 수익률 {result.total_return_pct:.2f}%"
        )

        return BacktestRunResponse(
            result=BacktestResultResponse.model_validate(result),
            message="백테스트가 완료되었습니다",
        )

    except BacktestServiceError as e:
        error_msg = str(e)

        # 신호 없음 오류
        if "신호가 없습니다" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=error_msg,
            ) from e

        # 시장 데이터 없음
        if "시장 데이터가 없습니다" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="해당 기간의 시장 데이터가 없습니다",
            ) from e

        # 기타 오류
        logger.error(f"백테스트 실행 실패: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"백테스트 실행 실패: {error_msg}",
        ) from e


@router.get(
    "/results",
    response_model=BacktestResultListResponse,
    summary="백테스트 결과 목록 조회",
    description="저장된 백테스트 결과 목록을 조회합니다.",
)
async def get_backtest_results(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    limit: Annotated[
        int,
        Query(ge=API_PAGINATION_MIN_LIMIT, le=API_PAGINATION_MAX_LIMIT, description="최대 조회 개수 (1-100)"),
    ] = API_PAGINATION_DEFAULT_LIMIT,
    status: Annotated[
        BacktestStatusEnum | None,
        Query(description="상태 필터 (PENDING/RUNNING/COMPLETED/FAILED)"),
    ] = None,
) -> BacktestResultListResponse:
    """
    백테스트 결과 목록 조회

    저장된 모든 백테스트 결과를 조회합니다.
    상태로 필터링할 수 있습니다.

    Args:
        session: 데이터베이스 세션
        limit: 최대 조회 개수 (기본: 20)
        status: 상태 필터 (선택)

    Returns:
        BacktestResultListResponse: 결과 목록과 총 개수
    """
    service = get_backtest_service(session)

    results = await service.get_results(
        limit=limit,
        status=status.value if status else None,
    )

    return BacktestResultListResponse(
        items=[BacktestResultResponse.model_validate(r) for r in results],
        total=len(results),
    )


@router.get(
    "/results/{result_id}",
    response_model=BacktestResultDetailResponse,
    summary="백테스트 결과 상세 조회",
    description="특정 백테스트 결과의 상세 정보를 조회합니다.",
    responses={
        404: {"description": "결과 없음"},
    },
)
async def get_backtest_result(
    result_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> BacktestResultDetailResponse:
    """
    백테스트 결과 상세 조회

    특정 백테스트 결과의 상세 정보와 거래 내역을 조회합니다.

    Args:
        result_id: 결과 ID
        session: 데이터베이스 세션

    Returns:
        BacktestResultDetailResponse: 결과 상세 정보

    Raises:
        HTTPException: 결과가 없는 경우 404
    """
    service = get_backtest_service(session)
    result = await service.get_result(result_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"백테스트 결과를 찾을 수 없습니다: {result_id}",
        )

    # 기본 응답 생성
    response_data = BacktestResultResponse.model_validate(result).model_dump()

    # 거래 내역 파싱
    trade_history = None
    if result.trade_history:
        try:
            trade_list = json.loads(result.trade_history)
            trade_history = [TradeRecord(**t) for t in trade_list]
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"거래 내역 파싱 실패: {e}")

    return BacktestResultDetailResponse(
        **response_data,
        trade_history=trade_history,
    )
