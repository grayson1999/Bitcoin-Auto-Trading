"""
포트폴리오 서비스 모듈

이 모듈은 포트폴리오 통계 계산 로직을 제공합니다.
- DailyStats 테이블에서 데이터 집계
- 누적 수익률, 승률, MDD 계산
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities import DailyStats
from src.modules.portfolio.schemas import PortfolioSummaryResponse, ProfitDataPoint


class PortfolioService:
    """포트폴리오 서비스"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_portfolio_summary(
        self, current_balance: Decimal
    ) -> PortfolioSummaryResponse:
        """
        포트폴리오 요약 정보 조회

        Args:
            current_balance: 현재 Upbit 총 잔고 (KRW)

        Returns:
            PortfolioSummaryResponse: 포트폴리오 요약 정보
        """
        # 전체 DailyStats 조회 (날짜 오름차순)
        stmt = select(DailyStats).order_by(DailyStats.date.asc())
        result = await self.session.execute(stmt)
        all_stats = result.scalars().all()

        # 데이터가 없는 경우 빈 응답 반환
        if not all_stats:
            return PortfolioSummaryResponse(
                total_deposit=current_balance,
                current_value=current_balance,
                cumulative_return_pct=0.0,
                today_return_pct=0.0,
                today_realized_pnl=Decimal("0"),
                total_trades=0,
                win_count=0,
                win_rate=0.0,
                average_return_pct=0.0,
                max_drawdown_pct=0.0,
                profit_chart_data=[],
            )

        # 초기 투자금: 첫 번째 DailyStats의 starting_balance
        first_stat = all_stats[0]
        total_deposit = first_stat.starting_balance

        # 누적 통계 계산
        total_trades = sum(stat.trade_count for stat in all_stats)
        win_count = sum(stat.win_count for stat in all_stats)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0

        # 누적 손익
        total_pnl = sum(stat.realized_pnl for stat in all_stats)

        # 누적 수익률
        if total_deposit > 0:
            cumulative_return_pct = float(
                (current_balance - total_deposit) / total_deposit * 100
            )
        else:
            cumulative_return_pct = 0.0

        # 평균 수익률 (거래당)
        average_return_pct = (
            float(total_pnl / total_trades / total_deposit * 100)
            if total_trades > 0 and total_deposit > 0
            else 0.0
        )

        # 오늘 통계
        today = date.today()
        today_stat = next((s for s in all_stats if s.date == today), None)

        today_return_pct = 0.0
        today_realized_pnl = Decimal("0")

        if today_stat:
            today_realized_pnl = today_stat.realized_pnl
            if today_stat.starting_balance > 0:
                today_return_pct = float(
                    today_stat.realized_pnl / today_stat.starting_balance * 100
                )

        # MDD (Maximum Drawdown) 계산
        max_drawdown_pct = self._calculate_mdd(all_stats)

        # 최근 30일 수익 차트 데이터
        profit_chart_data = self._generate_chart_data(all_stats, total_deposit)

        return PortfolioSummaryResponse(
            total_deposit=total_deposit,
            current_value=current_balance,
            cumulative_return_pct=cumulative_return_pct,
            today_return_pct=today_return_pct,
            today_realized_pnl=today_realized_pnl,
            total_trades=total_trades,
            win_count=win_count,
            win_rate=win_rate,
            average_return_pct=average_return_pct,
            max_drawdown_pct=max_drawdown_pct,
            profit_chart_data=profit_chart_data,
        )

    def _calculate_mdd(self, stats: list[DailyStats]) -> float:
        """
        MDD (Maximum Drawdown) 계산

        Args:
            stats: DailyStats 리스트 (날짜 오름차순)

        Returns:
            float: MDD 비율 (%)
        """
        if not stats:
            return 0.0

        peak = stats[0].ending_balance
        max_drawdown = Decimal("0")

        for stat in stats:
            if stat.ending_balance > peak:
                peak = stat.ending_balance

            if peak > 0:
                drawdown = (peak - stat.ending_balance) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return float(max_drawdown)

    def _generate_chart_data(
        self, stats: list[DailyStats], initial_balance: Decimal
    ) -> list[ProfitDataPoint]:
        """
        수익 차트 데이터 생성 (최근 30일)

        Args:
            stats: DailyStats 리스트 (날짜 오름차순)
            initial_balance: 초기 잔고

        Returns:
            list[ProfitDataPoint]: 차트 데이터 포인트 리스트
        """
        # 최근 30일 필터링
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        recent_stats = [s for s in stats if s.date >= thirty_days_ago]

        # 차트 데이터 생성
        chart_data: list[ProfitDataPoint] = []

        for stat in recent_stats:
            chart_data.append(
                ProfitDataPoint(
                    date=stat.date.isoformat(),
                    value=stat.ending_balance,
                )
            )

        return chart_data


async def get_portfolio_service(session: AsyncSession) -> PortfolioService:
    """
    PortfolioService 인스턴스 생성

    Args:
        session: 데이터베이스 세션

    Returns:
        PortfolioService: 포트폴리오 서비스 인스턴스
    """
    return PortfolioService(session)
