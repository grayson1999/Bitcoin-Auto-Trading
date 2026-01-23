"""
설정 API 라우터

설정 조회/수정 API 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import DB_OVERRIDABLE_KEYS
from src.utils.database import get_session
from src.modules.config.schemas import (
    ConfigBatchUpdateRequest,
    ConfigBatchUpdateResponse,
    ConfigItemResponse,
    ConfigListResponse,
    ConfigUpdateRequest,
    OverridableKeysResponse,
    RiskParamsResponse,
    TradingStatusResponse,
)
from src.modules.config.service import ConfigService

router = APIRouter(prefix="/config", tags=["config"])


async def get_config_service(
    session: AsyncSession = Depends(get_session),
) -> ConfigService:
    """설정 서비스 의존성"""
    return ConfigService(session)


@router.get("", response_model=ConfigListResponse)
async def get_all_configs(
    service: ConfigService = Depends(get_config_service),
) -> ConfigListResponse:
    """
    모든 설정 조회

    DB 오버라이드 가능한 모든 설정을 반환합니다.
    DB 값이 있으면 DB 값을, 없으면 환경변수 값을 반환합니다.
    """
    configs = await service.get_all()
    return ConfigListResponse(configs=configs, count=len(configs))


@router.get("/keys", response_model=OverridableKeysResponse)
async def get_overridable_keys() -> OverridableKeysResponse:
    """
    DB 오버라이드 가능한 키 목록 조회

    DB에 저장할 수 있는 설정 키 목록을 반환합니다.
    """
    return OverridableKeysResponse(keys=sorted(DB_OVERRIDABLE_KEYS))


@router.get("/db", response_model=ConfigListResponse)
async def get_db_configs(
    service: ConfigService = Depends(get_config_service),
) -> ConfigListResponse:
    """
    DB에 저장된 설정만 조회

    환경변수를 제외하고 DB에 명시적으로 저장된 설정만 반환합니다.
    """
    configs = await service.get_db_configs()
    return ConfigListResponse(configs=configs, count=len(configs))


@router.get("/trading-status", response_model=TradingStatusResponse)
async def get_trading_status(
    service: ConfigService = Depends(get_config_service),
) -> TradingStatusResponse:
    """
    거래 상태 조회

    거래 활성화 여부와 거래 대상 마켓을 반환합니다.
    """
    trading_enabled = await service.is_trading_enabled()
    ticker = await service.get("trading_ticker", default="KRW-BTC")
    return TradingStatusResponse(
        trading_enabled=trading_enabled,
        ticker=str(ticker),
    )


@router.get("/risk-params", response_model=RiskParamsResponse)
async def get_risk_params(
    service: ConfigService = Depends(get_config_service),
) -> RiskParamsResponse:
    """
    리스크 파라미터 조회

    손절, 일일 손실 한도, 변동성 임계값, 포지션 크기 범위를 반환합니다.
    """
    risk_params = await service.get_risk_params()
    min_pct, max_pct = await service.get_position_size_range()
    return RiskParamsResponse(
        **risk_params,
        position_size_min_pct=min_pct,
        position_size_max_pct=max_pct,
    )


@router.get("/{key}", response_model=ConfigItemResponse)
async def get_config(
    key: str,
    service: ConfigService = Depends(get_config_service),
) -> ConfigItemResponse:
    """
    단일 설정 조회

    지정된 키의 설정값을 반환합니다.
    DB에 값이 있으면 DB 값을, 없으면 환경변수 값을 반환합니다.
    """
    if key not in DB_OVERRIDABLE_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{key}'는 조회 가능한 설정 키가 아닙니다",
        )

    value, source, updated_at = await service.get_config_with_source(key)
    return ConfigItemResponse(
        key=key,
        value=value,
        source=source,
        updated_at=updated_at,
    )


@router.patch("/{key}", response_model=ConfigItemResponse)
async def update_config(
    key: str,
    request: ConfigUpdateRequest,
    service: ConfigService = Depends(get_config_service),
) -> ConfigItemResponse:
    """
    단일 설정 수정

    지정된 키의 설정값을 DB에 저장합니다.
    DB 오버라이드 가능한 키만 수정할 수 있습니다.
    """
    if key not in DB_OVERRIDABLE_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{key}'는 DB에 저장할 수 없는 설정 키입니다",
        )

    try:
        value, updated_at = await service.set_and_get(key, request.value)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return ConfigItemResponse(
        key=key,
        value=value,
        source="db",
        updated_at=updated_at,
    )


@router.patch("", response_model=ConfigBatchUpdateResponse)
async def batch_update_configs(
    request: ConfigBatchUpdateRequest,
    service: ConfigService = Depends(get_config_service),
) -> ConfigBatchUpdateResponse:
    """
    설정 일괄 수정

    여러 설정을 한 번에 DB에 저장합니다.
    DB 오버라이드 가능한 키만 수정되며, 불가능한 키는 실패 목록에 포함됩니다.
    """
    updated: list[str] = []
    failed: list[str] = []

    for key, value in request.configs.items():
        if key not in DB_OVERRIDABLE_KEYS:
            failed.append(key)
            continue

        success = await service.set(key, value)
        if success:
            updated.append(key)
        else:
            failed.append(key)

    return ConfigBatchUpdateResponse(updated=updated, failed=failed)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    key: str,
    service: ConfigService = Depends(get_config_service),
) -> None:
    """
    설정 삭제

    DB에서 설정을 삭제합니다.
    삭제 후 해당 키는 환경변수 값으로 폴백됩니다.
    """
    if key not in DB_OVERRIDABLE_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{key}'는 삭제 가능한 설정 키가 아닙니다",
        )

    success = await service.delete(key)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{key}' 설정이 DB에 존재하지 않습니다",
        )
