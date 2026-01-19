"""
시스템 설정 API 스키마 모듈

이 모듈은 시스템 설정 관련 API의 요청/응답 스키마를 정의합니다.
- SystemConfig: 현재 설정 조회 응답
- SystemConfigUpdate: 설정 수정 요청
"""

from pydantic import BaseModel, Field


class SystemConfigResponse(BaseModel):
    """
    시스템 설정 응답 스키마

    현재 시스템 설정값을 반환합니다.

    Attributes:
        position_size_min_pct: 최소 포지션 크기 비율 (%)
        position_size_max_pct: 최대 포지션 크기 비율 (%)
        position_size_pct: 포지션 크기 비율 (%) - deprecated
        stop_loss_pct: 손절 임계값 (%)
        daily_loss_limit_pct: 일일 손실 한도 (%)
        signal_interval_hours: AI 신호 생성 주기 (시간)
        ai_model: 사용 중인 AI 모델
        volatility_threshold_pct: 변동성 임계값 (%)
        trading_enabled: 거래 활성화 여부
    """

    position_size_min_pct: float = Field(
        default=1.0,
        description="최소 포지션 크기 비율 (%, 신뢰도 낮을 때)",
    )
    position_size_max_pct: float = Field(
        default=3.0,
        description="최대 포지션 크기 비율 (%, 신뢰도 높을 때)",
    )
    position_size_pct: float = Field(
        default=2.0,
        description="포지션 크기 비율 (%) - deprecated",
    )
    stop_loss_pct: float = Field(
        default=5.0,
        description="손절 임계값 (%)",
    )
    daily_loss_limit_pct: float = Field(
        default=5.0,
        description="일일 손실 한도 (%)",
    )
    signal_interval_hours: int = Field(
        default=1,
        description="AI 신호 생성 주기 (시간)",
    )
    ai_model: str = Field(
        default="gemini-2.5-pro",
        description="사용 중인 AI 모델",
    )
    volatility_threshold_pct: float = Field(
        default=3.0,
        description="변동성 임계값 (%)",
    )
    trading_enabled: bool = Field(
        default=True,
        description="거래 활성화 여부",
    )


class SystemConfigUpdateRequest(BaseModel):
    """
    시스템 설정 수정 요청 스키마

    수정할 설정값만 포함합니다. null인 필드는 수정하지 않습니다.

    Attributes:
        position_size_min_pct: 최소 포지션 크기 비율 (0.5~5%)
        position_size_max_pct: 최대 포지션 크기 비율 (1~10%)
        position_size_pct: 포지션 크기 비율 (1~5%) - deprecated
        stop_loss_pct: 손절 임계값 (3~10%)
        daily_loss_limit_pct: 일일 손실 한도 (3~10%)
        signal_interval_hours: AI 신호 생성 주기 (1~4시간)
        ai_model: AI 모델 선택
        volatility_threshold_pct: 변동성 임계값 (1~10%)
    """

    position_size_min_pct: float | None = Field(
        default=None,
        ge=0.5,
        le=5.0,
        description="최소 포지션 크기 비율 (0.5~5%)",
    )
    position_size_max_pct: float | None = Field(
        default=None,
        ge=1.0,
        le=10.0,
        description="최대 포지션 크기 비율 (1~10%)",
    )
    position_size_pct: float | None = Field(
        default=None,
        ge=1.0,
        le=5.0,
        description="포지션 크기 비율 (1~5%) - deprecated",
    )
    stop_loss_pct: float | None = Field(
        default=None,
        ge=3.0,
        le=10.0,
        description="손절 임계값 (3~10%)",
    )
    daily_loss_limit_pct: float | None = Field(
        default=None,
        ge=3.0,
        le=10.0,
        description="일일 손실 한도 (3~10%)",
    )
    signal_interval_hours: int | None = Field(
        default=None,
        ge=1,
        le=4,
        description="AI 신호 생성 주기 (1~4시간)",
    )
    ai_model: str | None = Field(
        default=None,
        description="AI 모델 (gemini-2.5-pro, gemini-2.5-flash, gpt-4o-mini, claude-3-haiku)",
    )
    volatility_threshold_pct: float | None = Field(
        default=None,
        ge=1.0,
        le=10.0,
        description="변동성 임계값 (1~10%)",
    )
