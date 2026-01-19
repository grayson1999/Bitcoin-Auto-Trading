"""
AI 매매 신호 API 응답 스키마 모듈

이 모듈은 매매 신호 관련 API의 요청/응답 스키마를 정의합니다.
- Pydantic v2 BaseModel 기반
- SQLAlchemy 모델과의 자동 변환 지원 (from_attributes=True)
- OpenAPI 문서에 표시될 필드 설명 포함
"""

import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TradingSignalResponse(BaseModel):
    """
    매매 신호 응답 스키마

    AI가 생성한 개별 매매 신호 정보입니다.
    """

    model_config = ConfigDict(from_attributes=True)

    # 기본 필드
    id: int = Field(description="고유 식별자")
    signal_type: str = Field(description="신호 타입 (BUY/HOLD/SELL)")
    confidence: Decimal = Field(description="신뢰도 점수 (0~1)")
    reasoning: str = Field(description="AI 분석 근거")
    created_at: datetime = Field(description="신호 생성 시간")
    model_name: str = Field(description="사용된 AI 모델명")
    input_tokens: int = Field(description="입력 토큰 수")
    output_tokens: int = Field(description="출력 토큰 수")

    # 성과 추적 필드
    price_at_signal: Decimal | None = Field(default=None, description="신호 생성 시 가격")
    price_after_4h: Decimal | None = Field(default=None, description="4시간 후 가격")
    price_after_24h: Decimal | None = Field(default=None, description="24시간 후 가격")
    outcome_evaluated: bool = Field(default=False, description="성과 평가 완료 여부")
    outcome_correct: bool | None = Field(default=None, description="신호 정확성")

    # 기술적 스냅샷 (JSON 파싱)
    technical_snapshot: dict[str, Any] | None = Field(
        default=None, description="기술적 지표 스냅샷"
    )

    @field_validator("technical_snapshot", mode="before")
    @classmethod
    def parse_technical_snapshot(cls, v: Any) -> dict[str, Any] | None:
        """JSON 문자열을 dict로 파싱"""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return None


class TradingSignalListResponse(BaseModel):
    """
    매매 신호 목록 응답 스키마

    여러 매매 신호를 포함하는 목록 응답입니다.

    Attributes:
        items: 매매 신호 목록
        total: 총 신호 수
    """

    items: list[TradingSignalResponse] = Field(description="매매 신호 목록")
    total: int = Field(description="총 신호 수")


class SignalFilterParams(str, Enum):
    """
    신호 필터 파라미터

    신호 목록 조회 시 사용하는 필터 옵션.
    """

    ALL = "all"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class GenerateSignalResponse(BaseModel):
    """
    신호 생성 응답 스키마

    수동으로 신호를 생성했을 때의 응답입니다.

    Attributes:
        signal: 생성된 신호 정보
        message: 응답 메시지
    """

    signal: TradingSignalResponse = Field(description="생성된 신호")
    message: str = Field(
        default="신호가 성공적으로 생성되었습니다",
        description="응답 메시지",
    )


class SignalErrorResponse(BaseModel):
    """
    신호 생성 오류 응답 스키마

    신호 생성 실패 시의 응답입니다.

    Attributes:
        error: 오류 메시지
        detail: 상세 오류 정보 (선택)
    """

    error: str = Field(description="오류 메시지")
    detail: str | None = Field(default=None, description="상세 오류 정보")


class SignalStatsResponse(BaseModel):
    """
    신호 통계 응답 스키마

    최근 신호 생성 통계 정보입니다.

    Attributes:
        total_signals: 총 신호 수
        buy_count: 매수 신호 수
        hold_count: 홀드 신호 수
        sell_count: 매도 신호 수
        avg_confidence: 평균 신뢰도
        last_signal_at: 마지막 신호 생성 시간
    """

    total_signals: int = Field(description="총 신호 수")
    buy_count: int = Field(default=0, description="매수 신호 수")
    hold_count: int = Field(default=0, description="홀드 신호 수")
    sell_count: int = Field(default=0, description="매도 신호 수")
    avg_confidence: float | None = Field(default=None, description="평균 신뢰도")
    last_signal_at: datetime | None = Field(
        default=None, description="마지막 신호 생성 시간"
    )
