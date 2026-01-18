"""
대시보드 API 응답 스키마 모듈

이 모듈은 대시보드 관련 API의 응답 스키마를 정의합니다.
- DashboardSummary: 대시보드 요약 정보
- Pydantic v2 BaseModel 기반
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.api.schemas.order import BalanceResponse, PositionResponse
from src.api.schemas.signal import TradingSignalResponse


class DashboardSummaryResponse(BaseModel):
    """
    대시보드 요약 응답 스키마

    현재 가격, 포지션, 잔고, 일일 손익 등 대시보드에 필요한 전체 요약 정보입니다.

    Attributes:
        market: 현재 거래 마켓 (예: KRW-SOL)
        current_price: 현재 가격 (KRW)
        price_change_24h: 24시간 가격 변동률 (%)
        position: 현재 포지션 정보
        balance: 계좌 잔고 정보
        daily_pnl: 오늘 실현 손익 (KRW)
        daily_pnl_pct: 오늘 손익률 (%)
        latest_signal: 최신 AI 신호
        is_trading_active: 거래 활성화 여부
        today_trade_count: 오늘 거래 횟수
        updated_at: 데이터 갱신 시간
    """

    market: str = Field(description="현재 거래 마켓 (예: KRW-SOL)")
    current_price: Decimal = Field(description="현재 가격 (KRW)")
    price_change_24h: float | None = Field(
        default=None, description="24시간 가격 변동률 (%)"
    )
    position: PositionResponse | None = Field(
        default=None, description="현재 포지션 정보"
    )
    balance: BalanceResponse | None = Field(default=None, description="계좌 잔고 정보")
    daily_pnl: Decimal = Field(default=Decimal("0"), description="오늘 실현 손익 (KRW)")
    daily_pnl_pct: float = Field(default=0.0, description="오늘 손익률 (%)")
    latest_signal: TradingSignalResponse | None = Field(
        default=None, description="최신 AI 신호"
    )
    is_trading_active: bool = Field(default=True, description="거래 활성화 여부")
    today_trade_count: int = Field(default=0, description="오늘 거래 횟수")
    updated_at: datetime = Field(description="데이터 갱신 시간")
