"""
백테스트 API 스키마 모듈

이 모듈은 백테스트 관련 API의 요청/응답 스키마를 정의합니다.
- Pydantic v2 BaseModel 기반
- SQLAlchemy 모델과의 자동 변환 지원 (from_attributes=True)
- OpenAPI 문서에 표시될 필드 설명 포함
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BacktestStatusEnum(str, Enum):
    """
    백테스트 상태 열거형

    API 응답에서 사용되는 상태 정의.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BacktestRequest(BaseModel):
    """
    백테스트 실행 요청 스키마

    백테스트를 실행하기 위한 요청 데이터입니다.

    Attributes:
        name: 백테스트 이름
        start_date: 시작 날짜
        end_date: 종료 날짜
        initial_capital: 초기 자본금 (기본값: 1,000,000 KRW)
    """

    name: str = Field(
        min_length=1,
        max_length=100,
        description="백테스트 이름",
        examples=["6개월 전략 테스트"],
    )
    start_date: datetime = Field(
        description="백테스트 시작 날짜",
        examples=["2024-07-01T00:00:00Z"],
    )
    end_date: datetime = Field(
        description="백테스트 종료 날짜",
        examples=["2025-01-01T00:00:00Z"],
    )
    initial_capital: Decimal = Field(
        default=Decimal("1000000"),
        ge=Decimal("100000"),
        le=Decimal("1000000000"),
        description="초기 자본금 (KRW)",
        examples=[1000000],
    )

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        """종료 날짜가 시작 날짜 이후인지 검증"""
        start_date = info.data.get("start_date")
        if start_date and v <= start_date:
            raise ValueError("종료 날짜는 시작 날짜 이후여야 합니다")
        return v


class TradeRecord(BaseModel):
    """
    거래 기록 스키마

    백테스트 중 발생한 개별 거래 기록입니다.

    Attributes:
        timestamp: 거래 시간
        signal_type: 신호 타입 (BUY/SELL)
        price: 체결 가격
        quantity: 거래 수량
        amount: 거래 금액
        fee: 수수료
        pnl: 손익 (SELL 시에만)
        pnl_pct: 손익률 (SELL 시에만)
        balance_after: 거래 후 잔고
    """

    timestamp: datetime = Field(description="거래 시간")
    signal_type: str = Field(description="신호 타입 (BUY/SELL)")
    price: float = Field(description="체결 가격")
    quantity: float = Field(description="거래 수량")
    amount: float = Field(description="거래 금액")
    fee: float = Field(description="수수료")
    pnl: float = Field(default=0, description="손익 (SELL 시)")
    pnl_pct: float = Field(default=0, description="손익률 (SELL 시)")
    balance_after: float = Field(description="거래 후 잔고")


class BacktestResultResponse(BaseModel):
    """
    백테스트 결과 응답 스키마

    백테스트 실행 결과 정보입니다.

    Attributes:
        id: 결과 고유 식별자
        name: 백테스트 이름
        status: 백테스트 상태
        start_date: 시작 날짜
        end_date: 종료 날짜
        initial_capital: 초기 자본금
        final_capital: 최종 자본금
        total_return_pct: 총 수익률 (%)
        max_drawdown_pct: 최대 낙폭 MDD (%)
        win_rate_pct: 승률 (%)
        profit_factor: 손익비
        sharpe_ratio: 샤프 비율
        total_trades: 총 거래 횟수
        winning_trades: 승리 거래 횟수
        losing_trades: 패배 거래 횟수
        avg_profit_pct: 평균 수익 거래 수익률 (%)
        avg_loss_pct: 평균 손실 거래 손실률 (%)
        error_message: 실패 시 오류 메시지
        created_at: 생성 시간
        completed_at: 완료 시간
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="고유 식별자")
    name: str = Field(description="백테스트 이름")
    status: str = Field(description="백테스트 상태")
    start_date: datetime = Field(description="시작 날짜")
    end_date: datetime = Field(description="종료 날짜")
    initial_capital: Decimal = Field(description="초기 자본금 (KRW)")
    final_capital: Decimal | None = Field(
        default=None, description="최종 자본금 (KRW)"
    )
    total_return_pct: Decimal | None = Field(
        default=None, description="총 수익률 (%)"
    )
    max_drawdown_pct: Decimal | None = Field(
        default=None, description="최대 낙폭 MDD (%)"
    )
    win_rate_pct: Decimal | None = Field(default=None, description="승률 (%)")
    profit_factor: Decimal | None = Field(default=None, description="손익비")
    sharpe_ratio: Decimal | None = Field(default=None, description="샤프 비율")
    total_trades: int | None = Field(default=0, description="총 거래 횟수")
    winning_trades: int | None = Field(default=0, description="승리 거래 횟수")
    losing_trades: int | None = Field(default=0, description="패배 거래 횟수")
    avg_profit_pct: Decimal | None = Field(
        default=None, description="평균 수익 거래 수익률 (%)"
    )
    avg_loss_pct: Decimal | None = Field(
        default=None, description="평균 손실 거래 손실률 (%)"
    )
    error_message: str | None = Field(
        default=None, description="실패 시 오류 메시지"
    )
    created_at: datetime = Field(description="생성 시간")
    completed_at: datetime | None = Field(default=None, description="완료 시간")


class BacktestResultDetailResponse(BacktestResultResponse):
    """
    백테스트 결과 상세 응답 스키마

    거래 내역을 포함한 상세 결과 정보입니다.

    Attributes:
        trade_history: 거래 내역 목록
    """

    trade_history: list[TradeRecord] | None = Field(
        default=None, description="거래 내역 목록"
    )


class BacktestResultListResponse(BaseModel):
    """
    백테스트 결과 목록 응답 스키마

    여러 백테스트 결과를 포함하는 목록 응답입니다.

    Attributes:
        items: 백테스트 결과 목록
        total: 총 결과 수
    """

    items: list[BacktestResultResponse] = Field(description="백테스트 결과 목록")
    total: int = Field(description="총 결과 수")


class BacktestRunResponse(BaseModel):
    """
    백테스트 실행 응답 스키마

    백테스트 실행 요청에 대한 응답입니다.

    Attributes:
        result: 백테스트 결과
        message: 응답 메시지
    """

    result: BacktestResultResponse = Field(description="백테스트 결과")
    message: str = Field(
        default="백테스트가 완료되었습니다",
        description="응답 메시지",
    )


class BacktestErrorResponse(BaseModel):
    """
    백테스트 오류 응답 스키마

    백테스트 실패 시의 응답입니다.

    Attributes:
        error: 오류 메시지
        detail: 상세 오류 정보 (선택)
    """

    error: str = Field(description="오류 메시지")
    detail: str | None = Field(default=None, description="상세 오류 정보")
