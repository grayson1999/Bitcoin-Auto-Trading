"""
주문/거래 모듈 스키마

이 모듈은 주문 관련 API의 요청/응답 스키마를 정의합니다.
- Pydantic v2 BaseModel 기반
- SQLAlchemy 모델과의 자동 변환 지원 (from_attributes=True)
- OpenAPI 문서에 표시될 필드 설명 포함

기존 파일: api/schemas/order.py
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OrderTypeEnum(str, Enum):
    """
    주문 타입 열거형

    API 요청/응답에서 사용되는 주문 타입 정의.
    """

    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderSideEnum(str, Enum):
    """
    주문 방향 열거형

    API 요청/응답에서 사용되는 주문 방향 정의.
    """

    BUY = "BUY"
    SELL = "SELL"


class OrderStatusEnum(str, Enum):
    """
    주문 상태 열거형

    API 요청/응답에서 사용되는 주문 상태 정의.
    """

    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class OrderStatusFilterEnum(str, Enum):
    """
    주문 상태 필터 열거형

    주문 목록 조회 시 사용하는 필터 옵션.
    """

    ALL = "all"
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderResponse(BaseModel):
    """
    주문 응답 스키마

    개별 주문 정보입니다.

    Attributes:
        id: 주문 고유 식별자
        signal_id: 연관 AI 신호 ID (없으면 null)
        order_type: 주문 타입 (MARKET/LIMIT)
        side: 주문 방향 (BUY/SELL)
        market: 마켓 코드
        amount: 주문 금액/수량
        price: 지정가 (시장가 시 null)
        status: 주문 상태
        executed_price: 체결 가격
        executed_amount: 체결 금액/수량
        fee: 수수료
        upbit_uuid: Upbit 주문 UUID
        error_message: 실패 시 오류 메시지
        created_at: 주문 생성 시간
        executed_at: 체결 시간
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="고유 식별자")
    signal_id: int | None = Field(default=None, description="연관 AI 신호 ID")
    order_type: str = Field(description="주문 타입 (MARKET/LIMIT)")
    side: str = Field(description="주문 방향 (BUY/SELL)")
    market: str = Field(description="마켓 코드")
    amount: Decimal = Field(description="주문 금액/수량")
    price: Decimal | None = Field(default=None, description="지정가 (시장가 시 null)")
    status: str = Field(description="주문 상태")
    executed_price: Decimal | None = Field(default=None, description="체결 가격")
    executed_amount: Decimal | None = Field(default=None, description="체결 금액/수량")
    fee: Decimal | None = Field(default=None, description="수수료")
    upbit_uuid: str | None = Field(default=None, description="Upbit 주문 UUID")
    error_message: str | None = Field(default=None, description="실패 시 오류 메시지")
    created_at: datetime = Field(description="주문 생성 시간")
    executed_at: datetime | None = Field(default=None, description="체결 시간")


class OrderListResponse(BaseModel):
    """
    주문 목록 응답 스키마

    여러 주문을 포함하는 목록 응답입니다.

    Attributes:
        items: 주문 목록
        total: 총 주문 수
        limit: 요청된 제한 수
        offset: 요청된 오프셋
    """

    items: list[OrderResponse] = Field(description="주문 목록")
    total: int = Field(description="총 주문 수")
    limit: int = Field(description="요청된 제한 수")
    offset: int = Field(description="요청된 오프셋")


class ExecuteOrderRequest(BaseModel):
    """
    수동 주문 실행 요청 스키마

    수동으로 주문을 실행할 때 사용합니다.

    Attributes:
        side: 주문 방향 (BUY/SELL)
        amount: 주문 금액 (KRW 기준)
        order_type: 주문 타입 (기본: MARKET)
        price: 지정가 (LIMIT 주문 시 필수)
    """

    side: OrderSideEnum = Field(description="주문 방향 (BUY/SELL)")
    amount: Decimal = Field(gt=0, description="주문 금액 (KRW)")
    order_type: OrderTypeEnum = Field(
        default=OrderTypeEnum.MARKET,
        description="주문 타입 (기본: MARKET)",
    )
    price: Decimal | None = Field(
        default=None,
        gt=0,
        description="지정가 (LIMIT 주문 시 필수)",
    )


class ExecuteOrderResponse(BaseModel):
    """
    주문 실행 응답 스키마

    주문 실행 결과입니다.

    Attributes:
        success: 성공 여부
        order: 생성된 주문 정보 (성공 시)
        message: 응답 메시지
    """

    success: bool = Field(description="성공 여부")
    order: OrderResponse | None = Field(default=None, description="생성된 주문")
    message: str = Field(description="응답 메시지")


class PositionResponse(BaseModel):
    """
    포지션 응답 스키마

    현재 거래 코인의 포지션 정보입니다.

    Attributes:
        symbol: 마켓 심볼 (예: KRW-SOL)
        quantity: 보유 수량
        avg_buy_price: 평균 매수가
        current_value: 현재 평가금액
        unrealized_pnl: 미실현 손익
        unrealized_pnl_pct: 미실현 손익률 (%)
        updated_at: 최종 업데이트 시간
    """

    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(description="심볼")
    quantity: Decimal = Field(description="보유 수량")
    avg_buy_price: Decimal = Field(description="평균 매수가")
    current_value: Decimal = Field(description="현재 평가금액")
    unrealized_pnl: Decimal = Field(description="미실현 손익")
    unrealized_pnl_pct: float = Field(description="미실현 손익률 (%)")
    updated_at: datetime = Field(description="최종 업데이트 시간")


class BalanceResponse(BaseModel):
    """
    계좌 잔고 응답 스키마

    Upbit 계좌 잔고 정보입니다.

    Attributes:
        krw: KRW 잔고
        krw_locked: KRW 잠금 금액 (주문 중)
        coin: 거래 코인 잔고
        coin_locked: 거래 코인 잠금 수량 (주문 중)
        coin_avg_buy_price: 거래 코인 평균 매수가
        total_krw: 총 평가금액 (KRW 환산)
    """

    krw: Decimal = Field(description="KRW 가용 잔고")
    krw_locked: Decimal = Field(default=Decimal("0"), description="KRW 잠금")
    coin: Decimal = Field(description="거래 코인 가용 잔고")
    coin_locked: Decimal = Field(default=Decimal("0"), description="거래 코인 잠금")
    coin_avg_buy_price: Decimal = Field(description="거래 코인 평균 매수가")
    total_krw: Decimal = Field(description="총 평가금액 (KRW 환산)")


class OrderErrorResponse(BaseModel):
    """
    주문 오류 응답 스키마

    주문 실패 시의 응답입니다.

    Attributes:
        error: 오류 메시지
        detail: 상세 오류 정보 (선택)
    """

    error: str = Field(description="오류 메시지")
    detail: str | None = Field(default=None, description="상세 오류 정보")
