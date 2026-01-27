"""
포트폴리오 API 응답 스키마 모듈

이 모듈은 포트폴리오 관련 API의 응답 스키마를 정의합니다.
- PortfolioSummary: 포트폴리오 요약 정보 (수익률, 승률, MDD 등)
- Pydantic v2 BaseModel 기반
"""

from decimal import Decimal

from pydantic import BaseModel, Field


class ProfitDataPoint(BaseModel):
    """
    수익 차트 데이터 포인트

    Attributes:
        date: 날짜 (YYYY-MM-DD)
        value: 해당 일자 잔고 (KRW)
    """

    date: str = Field(description="날짜 (YYYY-MM-DD)")
    value: Decimal = Field(description="해당 일자 잔고 (KRW)")


class PortfolioSummaryResponse(BaseModel):
    """
    포트폴리오 요약 응답 스키마

    투자 수익률, 거래 통계, 30일 수익 차트 데이터를 포함합니다.

    Attributes:
        total_deposit: 초기 투자금 (첫 DailyStats의 starting_balance)
        current_value: 현재 평가금 (KRW)
        cumulative_return_pct: 누적 수익률 (%)
        today_return_pct: 오늘 수익률 (%)
        today_realized_pnl: 오늘 실현 손익 (KRW)
        total_trades: 총 거래 횟수
        win_count: 승리 횟수
        win_rate: 승률 (%)
        average_return_pct: 평균 수익률 (%)
        max_drawdown_pct: 최대 낙폭 MDD (%)
        profit_chart_data: 30일 수익 차트 데이터
    """

    total_deposit: Decimal = Field(description="초기 투자금 (KRW)")
    current_value: Decimal = Field(description="현재 평가금 (KRW)")
    cumulative_return_pct: float = Field(description="누적 수익률 (%, 실현 손익 기준)")
    total_realized_pnl: Decimal = Field(description="누적 실현 손익 (KRW)")
    today_return_pct: float = Field(description="오늘 수익률 (%)")
    today_realized_pnl: Decimal = Field(description="오늘 실현 손익 (KRW)")
    total_trades: int = Field(description="총 거래 횟수")
    win_count: int = Field(description="승리 횟수")
    win_rate: float = Field(description="승률 (%)")
    average_return_pct: float = Field(description="평균 수익률 (%)")
    max_drawdown_pct: float = Field(description="최대 낙폭 MDD (%)")
    profit_chart_data: list[ProfitDataPoint] = Field(
        default_factory=list, description="30일 수익 차트 데이터"
    )
