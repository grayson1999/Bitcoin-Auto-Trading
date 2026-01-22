"""
시스템 설정 API 엔드포인트 모듈

이 모듈은 시스템 설정 관련 API를 제공합니다.
- 설정 조회 (GET /config)
- 설정 수정 (PATCH /config)
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser
from src.api.schemas.config import SystemConfigResponse, SystemConfigUpdateRequest
from src.database import get_session
from src.entities import DEFAULT_CONFIGS, SystemConfig

router = APIRouter(prefix="/config")

# 유효한 AI 모델 목록
VALID_AI_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gpt-4o-mini",
    "claude-3-haiku",
]


async def _get_config_value(
    session: AsyncSession,
    key: str,
    default: str,
) -> str:
    """
    설정값 조회 헬퍼

    Args:
        session: 데이터베이스 세션
        key: 설정 키
        default: 기본값

    Returns:
        str: 설정값 문자열
    """
    stmt = select(SystemConfig).where(SystemConfig.key == key)
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()

    if config is None:
        return default

    return config.value


async def _set_config_value(
    session: AsyncSession,
    key: str,
    value: str,
) -> None:
    """
    설정값 저장 헬퍼

    Args:
        session: 데이터베이스 세션
        key: 설정 키
        value: 설정값 문자열
    """
    now = datetime.now(UTC)
    stmt = select(SystemConfig).where(SystemConfig.key == key)
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()

    if config is None:
        config = SystemConfig(key=key, value=value, updated_at=now)
        session.add(config)
    else:
        config.value = value
        config.updated_at = now


# ==========================================================================
# T072: GET /config - 시스템 설정 조회
# ==========================================================================


@router.get(
    "",
    response_model=SystemConfigResponse,
    summary="시스템 설정 조회",
    description="현재 시스템 설정값을 조회합니다.",
)
async def get_config(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> SystemConfigResponse:
    """
    시스템 설정 조회

    포지션 크기, 손절, 일일 손실 한도, AI 모델 등
    현재 설정된 시스템 파라미터를 반환합니다.

    Args:
        session: 데이터베이스 세션

    Returns:
        SystemConfigResponse: 현재 시스템 설정
    """
    # 각 설정값 조회
    position_size_min_pct = float(
        await _get_config_value(
            session, "position_size_min_pct", DEFAULT_CONFIGS["position_size_min_pct"]
        )
    )
    position_size_max_pct = float(
        await _get_config_value(
            session, "position_size_max_pct", DEFAULT_CONFIGS["position_size_max_pct"]
        )
    )
    position_size_pct = float(
        await _get_config_value(
            session, "position_size_pct", DEFAULT_CONFIGS["position_size_pct"]
        )
    )
    stop_loss_pct = float(
        await _get_config_value(
            session, "stop_loss_pct", DEFAULT_CONFIGS["stop_loss_pct"]
        )
    )
    daily_loss_limit_pct = float(
        await _get_config_value(
            session, "daily_loss_limit_pct", DEFAULT_CONFIGS["daily_loss_limit_pct"]
        )
    )
    signal_interval_hours = int(
        await _get_config_value(
            session, "signal_interval_hours", DEFAULT_CONFIGS["signal_interval_hours"]
        )
    )
    ai_model_raw = await _get_config_value(
        session, "ai_model", DEFAULT_CONFIGS["ai_model"]
    )
    # 따옴표 제거
    ai_model = ai_model_raw.strip('"')

    volatility_threshold_pct = float(
        await _get_config_value(
            session,
            "volatility_threshold_pct",
            DEFAULT_CONFIGS["volatility_threshold_pct"],
        )
    )
    trading_enabled_raw = await _get_config_value(
        session, "trading_enabled", DEFAULT_CONFIGS["trading_enabled"]
    )
    trading_enabled = trading_enabled_raw.lower() == "true"

    return SystemConfigResponse(
        position_size_min_pct=position_size_min_pct,
        position_size_max_pct=position_size_max_pct,
        position_size_pct=position_size_pct,
        stop_loss_pct=stop_loss_pct,
        daily_loss_limit_pct=daily_loss_limit_pct,
        signal_interval_hours=signal_interval_hours,
        ai_model=ai_model,
        volatility_threshold_pct=volatility_threshold_pct,
        trading_enabled=trading_enabled,
    )


# ==========================================================================
# T073: PATCH /config - 시스템 설정 수정
# ==========================================================================


@router.patch(
    "",
    response_model=SystemConfigResponse,
    summary="시스템 설정 수정",
    description="시스템 설정값을 수정합니다. 제공된 필드만 업데이트됩니다.",
    responses={
        400: {"description": "유효하지 않은 설정값"},
    },
)
async def update_config(
    request: SystemConfigUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
) -> SystemConfigResponse:
    """
    시스템 설정 수정

    제공된 설정값만 업데이트합니다.
    null인 필드는 기존 값을 유지합니다.

    Args:
        request: 수정할 설정값
        session: 데이터베이스 세션

    Returns:
        SystemConfigResponse: 수정된 설정

    Raises:
        HTTPException: 유효하지 않은 AI 모델 지정 시 400
    """
    # AI 모델 검증
    if request.ai_model is not None and request.ai_model not in VALID_AI_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 AI 모델입니다. 허용: {VALID_AI_MODELS}",
        )

    # 각 필드 업데이트
    if request.position_size_min_pct is not None:
        await _set_config_value(
            session, "position_size_min_pct", str(request.position_size_min_pct)
        )
        logger.info(
            f"설정 변경: position_size_min_pct = {request.position_size_min_pct}"
        )

    if request.position_size_max_pct is not None:
        await _set_config_value(
            session, "position_size_max_pct", str(request.position_size_max_pct)
        )
        logger.info(
            f"설정 변경: position_size_max_pct = {request.position_size_max_pct}"
        )

    if request.position_size_pct is not None:
        await _set_config_value(
            session, "position_size_pct", str(request.position_size_pct)
        )
        logger.info(f"설정 변경: position_size_pct = {request.position_size_pct}")

    if request.stop_loss_pct is not None:
        await _set_config_value(session, "stop_loss_pct", str(request.stop_loss_pct))
        logger.info(f"설정 변경: stop_loss_pct = {request.stop_loss_pct}")

    if request.daily_loss_limit_pct is not None:
        await _set_config_value(
            session, "daily_loss_limit_pct", str(request.daily_loss_limit_pct)
        )
        logger.info(f"설정 변경: daily_loss_limit_pct = {request.daily_loss_limit_pct}")

    if request.signal_interval_hours is not None:
        await _set_config_value(
            session, "signal_interval_hours", str(request.signal_interval_hours)
        )
        logger.info(
            f"설정 변경: signal_interval_hours = {request.signal_interval_hours}"
        )

    if request.ai_model is not None:
        await _set_config_value(session, "ai_model", f'"{request.ai_model}"')
        logger.info(f"설정 변경: ai_model = {request.ai_model}")

    if request.volatility_threshold_pct is not None:
        await _set_config_value(
            session, "volatility_threshold_pct", str(request.volatility_threshold_pct)
        )
        logger.info(
            f"설정 변경: volatility_threshold_pct = {request.volatility_threshold_pct}"
        )

    # 변경사항 커밋
    await session.commit()

    # 업데이트된 설정 반환
    return await get_config(session, current_user)
