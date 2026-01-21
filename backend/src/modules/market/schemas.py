"""
시장 데이터 모듈 스키마

이 모듈은 시장 데이터 관련 API의 응답 스키마를 정의합니다.
- Pydantic v2 BaseModel 기반
- SQLAlchemy 모델과의 자동 변환 지원 (from_attributes=True)
- OpenAPI 문서에 표시될 필드 설명 포함

기존 파일:
- api/schemas/market.py
- api/schemas/dashboard.py (market 관련 부분)
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MarketDataResponse(BaseModel):
    """
    시장 데이터 레코드 응답 스키마

    DB에 저장된 개별 시장 데이터 레코드를 나타냅니다.

    Attributes:
        id: 레코드 고유 식별자
        symbol: 마켓 심볼 (예: KRW-BTC, KRW-SOL)
        timestamp: 데이터 수집 시간 (UTC)
        price: 현재 가격 (KRW)
        volume: 24시간 거래량
        high_price: 24시간 최고가
        low_price: 24시간 최저가
        trade_count: 거래 건수
    """

    # SQLAlchemy 모델에서 자동 변환 허용
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="고유 식별자")
    symbol: str = Field(description="마켓 심볼 (예: KRW-BTC)")
    timestamp: datetime = Field(description="데이터 수집 시간 (UTC)")
    price: Decimal = Field(description="현재 가격 (KRW)")
    volume: Decimal = Field(description="24시간 거래량")
    high_price: Decimal = Field(description="24시간 최고가")
    low_price: Decimal = Field(description="24시간 최저가")
    trade_count: int = Field(description="거래 건수")


class MarketDataListResponse(BaseModel):
    """
    시장 데이터 목록 응답 스키마

    여러 시장 데이터 레코드를 포함하는 목록 응답입니다.

    Attributes:
        items: 시장 데이터 레코드 목록
        total: 총 레코드 수
    """

    items: list[MarketDataResponse] = Field(description="시장 데이터 레코드 목록")
    total: int = Field(description="총 레코드 수")


class MarketSummaryResponse(BaseModel):
    """
    시장 데이터 요약 통계 응답 스키마

    특정 기간 동안의 시세 통계를 요약합니다.

    Attributes:
        count: 기간 내 데이터 포인트 수
        period_hours: 요약 기간 (시간)
        latest_price: 최신 가격
        high: 기간 내 최고가
        low: 기간 내 최저가
        price_change_pct: 가격 변동률 (%)
        first_timestamp: 첫 데이터 시간
        last_timestamp: 마지막 데이터 시간
    """

    count: int = Field(description="기간 내 데이터 포인트 수")
    period_hours: int = Field(description="요약 기간 (시간)")
    latest_price: float | None = Field(description="최신 가격")
    high: float | None = Field(description="기간 내 최고가")
    low: float | None = Field(description="기간 내 최저가")
    price_change_pct: float | None = Field(description="가격 변동률 (%)")
    first_timestamp: str | None = Field(default=None, description="첫 데이터 시간")
    last_timestamp: str | None = Field(default=None, description="마지막 데이터 시간")


class CurrentMarketResponse(BaseModel):
    """
    현재 시세 응답 스키마

    Upbit API에서 직접 조회한 실시간 시세 정보입니다.

    Attributes:
        market: 마켓 코드 (예: KRW-SOL)
        price: 현재 가격 (KRW)
        volume_24h: 24시간 거래량
        high_24h: 24시간 최고가
        low_24h: 24시간 최저가
        timestamp: 시세 데이터 시간
        change_24h_pct: 24시간 변동률 (%)
    """

    market: str = Field(description="마켓 코드")
    price: Decimal = Field(description="현재 가격 (KRW)")
    volume_24h: Decimal = Field(description="24시간 거래량")
    high_24h: Decimal = Field(description="24시간 최고가")
    low_24h: Decimal = Field(description="24시간 최저가")
    timestamp: datetime = Field(description="시세 데이터 시간")
    change_24h_pct: float | None = Field(default=None, description="24시간 변동률 (%)")


class CollectorStatsResponse(BaseModel):
    """
    데이터 수집기 상태 응답 스키마

    시장 데이터 수집기의 현재 상태와 통계 정보입니다.

    Attributes:
        is_running: 수집기 실행 중 여부
        consecutive_failures: 연속 실패 횟수
        last_success: 마지막 성공 시간 (ISO 형식)
        total_collected: 이 세션에서 수집된 총 레코드 수
        market: 수집 중인 마켓
    """

    is_running: bool = Field(description="수집기 실행 중 여부")
    consecutive_failures: int = Field(description="연속 실패 횟수")
    last_success: str | None = Field(description="마지막 성공 시간")
    total_collected: int = Field(description="총 수집 레코드 수")
    market: str = Field(description="수집 중인 마켓")


# Dashboard 관련 스키마 (market 모듈에서 사용)
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
