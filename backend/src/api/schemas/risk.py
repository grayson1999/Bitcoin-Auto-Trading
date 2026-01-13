"""
리스크 관리 API 응답 스키마 모듈

이 모듈은 리스크 관리 관련 API의 요청/응답 스키마를 정의합니다.
- RiskEvent 응답
- RiskStatus 응답
- 거래 중단/재개 요청/응답
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RiskEventTypeEnum(str, Enum):
    """
    리스크 이벤트 유형 열거형

    API 응답에서 사용되는 이벤트 타입 정의.
    """

    STOP_LOSS = "STOP_LOSS"
    DAILY_LIMIT = "DAILY_LIMIT"
    POSITION_LIMIT = "POSITION_LIMIT"
    VOLATILITY_HALT = "VOLATILITY_HALT"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class RiskEventResponse(BaseModel):
    """
    리스크 이벤트 응답 스키마

    리스크 관리 시스템이 기록한 개별 이벤트 정보입니다.

    Attributes:
        id: 이벤트 고유 식별자
        order_id: 연관 주문 ID (없을 수 있음)
        event_type: 이벤트 유형
        trigger_value: 발동 기준값 (%)
        action_taken: 수행된 조치
        created_at: 발생 시간
        notified: 알림 전송 여부
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="고유 식별자")
    order_id: int | None = Field(default=None, description="연관 주문 ID")
    event_type: str = Field(description="이벤트 유형")
    trigger_value: Decimal = Field(description="발동 기준값 (%)")
    action_taken: str = Field(description="수행된 조치")
    created_at: datetime = Field(description="발생 시간")
    notified: bool = Field(description="알림 전송 여부")


class RiskEventListResponse(BaseModel):
    """
    리스크 이벤트 목록 응답 스키마

    여러 리스크 이벤트를 포함하는 목록 응답입니다.

    Attributes:
        items: 이벤트 목록
        total: 총 이벤트 수
    """

    items: list[RiskEventResponse] = Field(description="이벤트 목록")
    total: int = Field(description="총 이벤트 수")


class RiskStatusResponse(BaseModel):
    """
    리스크 상태 응답 스키마

    현재 리스크 관리 시스템의 상태 정보입니다.

    Attributes:
        trading_enabled: 거래 가능 여부
        daily_loss_pct: 오늘 손실률 (%)
        daily_loss_limit_pct: 일일 손실 한도 (%)
        position_size_pct: 포지션 크기 제한 (%)
        stop_loss_pct: 손절 임계값 (%)
        volatility_threshold_pct: 변동성 임계값 (%)
        current_volatility_pct: 현재 변동성 (%)
        is_halted: 거래 중단 상태
        halt_reason: 중단 사유
        last_check_at: 마지막 체크 시간
    """

    model_config = ConfigDict(from_attributes=True)

    trading_enabled: bool = Field(description="거래 가능 여부")
    daily_loss_pct: float = Field(description="오늘 손실률 (%)")
    daily_loss_limit_pct: float = Field(description="일일 손실 한도 (%)")
    position_size_pct: float = Field(description="포지션 크기 제한 (%)")
    stop_loss_pct: float = Field(description="손절 임계값 (%)")
    volatility_threshold_pct: float = Field(description="변동성 임계값 (%)")
    current_volatility_pct: float = Field(description="현재 변동성 (%)")
    is_halted: bool = Field(description="거래 중단 상태")
    halt_reason: str | None = Field(default=None, description="중단 사유")
    last_check_at: datetime = Field(description="마지막 체크 시간")


class HaltTradingRequest(BaseModel):
    """
    거래 중단 요청 스키마

    Attributes:
        reason: 중단 사유
    """

    reason: str = Field(
        description="중단 사유",
        min_length=1,
        max_length=100,
    )


class HaltTradingResponse(BaseModel):
    """
    거래 중단 응답 스키마

    Attributes:
        success: 성공 여부
        message: 응답 메시지
        halted_at: 중단 시간
    """

    success: bool = Field(description="성공 여부")
    message: str = Field(description="응답 메시지")
    halted_at: datetime = Field(description="중단 시간")


class ResumeTradingResponse(BaseModel):
    """
    거래 재개 응답 스키마

    Attributes:
        success: 성공 여부
        message: 응답 메시지
        resumed_at: 재개 시간
    """

    success: bool = Field(description="성공 여부")
    message: str = Field(description="응답 메시지")
    resumed_at: datetime = Field(description="재개 시간")


class RiskCheckResultEnum(str, Enum):
    """리스크 체크 결과 열거형"""

    PASS = "PASS"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"


class PositionCheckResponse(BaseModel):
    """
    포지션 크기 검증 응답 스키마

    Attributes:
        result: 검증 결과
        max_amount: 최대 허용 금액
        requested_amount: 요청 금액
        message: 상세 메시지
    """

    result: RiskCheckResultEnum = Field(description="검증 결과")
    max_amount: Decimal = Field(description="최대 허용 금액")
    requested_amount: Decimal = Field(description="요청 금액")
    message: str = Field(description="상세 메시지")


class StopLossCheckResponse(BaseModel):
    """
    손절 체크 응답 스키마

    Attributes:
        result: 체크 결과
        current_loss_pct: 현재 손실률 (%)
        stop_loss_threshold_pct: 손절 임계값 (%)
        should_close: 포지션 청산 필요 여부
        message: 상세 메시지
    """

    result: RiskCheckResultEnum = Field(description="체크 결과")
    current_loss_pct: float = Field(description="현재 손실률 (%)")
    stop_loss_threshold_pct: float = Field(description="손절 임계값 (%)")
    should_close: bool = Field(description="포지션 청산 필요 여부")
    message: str = Field(description="상세 메시지")


class VolatilityCheckResponse(BaseModel):
    """
    변동성 체크 응답 스키마

    Attributes:
        result: 체크 결과
        current_volatility_pct: 현재 변동성 (%)
        threshold_pct: 임계값 (%)
        message: 상세 메시지
    """

    result: RiskCheckResultEnum = Field(description="체크 결과")
    current_volatility_pct: float = Field(description="현재 변동성 (%)")
    threshold_pct: float = Field(description="임계값 (%)")
    message: str = Field(description="상세 메시지")


class RiskErrorResponse(BaseModel):
    """
    리스크 관리 오류 응답 스키마

    Attributes:
        error: 오류 메시지
        detail: 상세 오류 정보 (선택)
    """

    error: str = Field(description="오류 메시지")
    detail: str | None = Field(default=None, description="상세 오류 정보")
