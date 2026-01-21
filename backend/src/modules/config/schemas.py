"""
설정 API 스키마

설정 관련 API 요청/응답 Pydantic 모델을 정의합니다.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConfigItemResponse(BaseModel):
    """단일 설정 항목 응답"""

    key: str = Field(..., description="설정 키")
    value: Any = Field(..., description="설정 값")
    source: str = Field(..., description="값 출처 (db/env/default)")
    updated_at: datetime | None = Field(
        None, description="마지막 수정 시간 (DB 값인 경우)"
    )

    model_config = {"from_attributes": True}


class ConfigListResponse(BaseModel):
    """설정 목록 응답"""

    configs: dict[str, Any] = Field(..., description="설정 키-값 딕셔너리")
    count: int = Field(..., description="설정 개수")


class ConfigUpdateRequest(BaseModel):
    """설정 수정 요청"""

    value: Any = Field(..., description="새 설정 값")


class ConfigBatchUpdateRequest(BaseModel):
    """설정 일괄 수정 요청"""

    configs: dict[str, Any] = Field(
        ...,
        description="수정할 설정 딕셔너리",
        examples=[{"position_size_min_pct": 30.0, "trading_enabled": True}],
    )


class ConfigBatchUpdateResponse(BaseModel):
    """설정 일괄 수정 응답"""

    updated: list[str] = Field(..., description="수정된 키 목록")
    failed: list[str] = Field(..., description="실패한 키 목록")


class TradingStatusResponse(BaseModel):
    """거래 상태 응답"""

    trading_enabled: bool = Field(..., description="거래 활성화 여부")
    ticker: str = Field(..., description="거래 대상 마켓")


class RiskParamsResponse(BaseModel):
    """리스크 파라미터 응답"""

    stop_loss_pct: float = Field(..., description="손절 비율 (%)")
    daily_loss_limit_pct: float = Field(..., description="일일 손실 한도 (%)")
    volatility_threshold_pct: float = Field(..., description="변동성 임계값 (%)")
    position_size_min_pct: float = Field(..., description="최소 포지션 크기 (%)")
    position_size_max_pct: float = Field(..., description="최대 포지션 크기 (%)")


class OverridableKeysResponse(BaseModel):
    """DB 오버라이드 가능한 키 목록 응답"""

    keys: list[str] = Field(..., description="DB 오버라이드 가능한 키 목록")
