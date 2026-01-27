"""
포트폴리오 서비스 모듈

이 모듈은 포트폴리오 통계 계산 로직을 제공합니다.
- DailyStats 테이블에서 데이터 집계
- 누적 수익률, 승률, MDD 계산
- 입금/출금 자동 감지 및 추적
"""

from datetime import date, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities import AdjustmentType, BalanceAdjustment, DailyStats
from src.modules.portfolio.schemas import PortfolioSummaryResponse, ProfitDataPoint

# 입금/출금 감지 임계값 (원)
ADJUSTMENT_THRESHOLD = Decimal("1000")


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
        all_stats = list(result.scalars().all())

        # 입금/출금 내역 조회
        adj_stmt = select(BalanceAdjustment).order_by(BalanceAdjustment.date.asc())
        adj_result = await self.session.execute(adj_stmt)
        adjustments = list(adj_result.scalars().all())

        # 데이터가 없는 경우 빈 응답 반환
        if not all_stats:
            return PortfolioSummaryResponse(
                total_deposit=current_balance,
                current_value=current_balance,
                cumulative_return_pct=0.0,
                total_realized_pnl=Decimal("0"),
                today_return_pct=0.0,
                today_realized_pnl=Decimal("0"),
                total_trades=0,
                win_count=0,
                win_rate=0.0,
                average_return_pct=0.0,
                max_drawdown_pct=0.0,
                profit_chart_data=[],
            )

        # 초기 투자금 계산 (첫 starting_balance + 누적 입금 - 누적 출금)
        first_stat = all_stats[0]
        initial_balance = first_stat.starting_balance

        total_deposits = sum(adj.amount for adj in adjustments if adj.amount > 0)
        total_withdrawals = sum(
            abs(adj.amount) for adj in adjustments if adj.amount < 0
        )
        total_invested = initial_balance + total_deposits - total_withdrawals

        # 누적 통계 계산
        total_trades = sum(stat.trade_count for stat in all_stats)
        win_count = sum(stat.win_count for stat in all_stats)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0

        # 누적 실현 손익
        total_pnl = sum(stat.realized_pnl for stat in all_stats)

        # 누적 수익률 (실현 손익 기준)
        if total_invested > 0:
            cumulative_return_pct = float(total_pnl / total_invested * 100)
        else:
            cumulative_return_pct = 0.0

        # 평균 수익률 (거래당)
        average_return_pct = (
            float(total_pnl / total_trades / total_invested * 100)
            if total_trades > 0 and total_invested > 0
            else 0.0
        )

        # 오늘 통계 (DailyStats 없을 때 전일 ending_balance 기준 fallback)
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
        else:
            # 오늘 DailyStats가 없을 때: 가장 최근 ending_balance 기준으로 오늘 수익률 계산
            last_stat = all_stats[-1]
            if last_stat.ending_balance > 0:
                today_return_pct = float(
                    (current_balance - last_stat.ending_balance)
                    / last_stat.ending_balance
                    * 100
                )

        # MDD (Maximum Drawdown) 계산 - 누적 실현 손익 기준
        max_drawdown_pct = self._calculate_mdd_from_pnl(all_stats)

        # 최근 30일 수익 차트 데이터 (누적 실현 손익 + 오늘 포인트)
        profit_chart_data = self._generate_chart_data(all_stats, current_balance)

        return PortfolioSummaryResponse(
            total_deposit=total_invested,  # 입금/출금 반영된 총 투자금
            current_value=current_balance,
            cumulative_return_pct=cumulative_return_pct,
            total_realized_pnl=total_pnl,
            today_return_pct=today_return_pct,
            today_realized_pnl=today_realized_pnl,
            total_trades=total_trades,
            win_count=win_count,
            win_rate=win_rate,
            average_return_pct=average_return_pct,
            max_drawdown_pct=max_drawdown_pct,
            profit_chart_data=profit_chart_data,
        )

    async def detect_and_record_adjustment(
        self,
        prev_ending_balance: Decimal,
        current_starting_balance: Decimal,
        target_date: date,
    ) -> BalanceAdjustment | None:
        """
        잔고 변화에서 입금/출금 감지 및 기록

        Args:
            prev_ending_balance: 전일 종료 잔고
            current_starting_balance: 오늘 시작 잔고
            target_date: 조정 날짜

        Returns:
            BalanceAdjustment | None: 감지된 조정 내역 (없으면 None)
        """
        # 잔고 차이 계산
        diff = current_starting_balance - prev_ending_balance

        # 임계값 미만이면 무시
        if abs(diff) < ADJUSTMENT_THRESHOLD:
            return None

        # 입금/출금 타입 결정
        if diff > 0:
            adj_type = AdjustmentType.DEPOSIT
            logger.info(f"입금 감지: {diff:,.0f}원 ({target_date})")
        else:
            adj_type = AdjustmentType.WITHDRAWAL
            logger.info(f"출금 감지: {abs(diff):,.0f}원 ({target_date})")

        # 이미 기록된 조정인지 확인
        existing_stmt = select(BalanceAdjustment).where(
            BalanceAdjustment.date == target_date,
            BalanceAdjustment.amount == diff,
        )
        existing_result = await self.session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            logger.debug(f"이미 기록된 조정: {target_date}, {diff:,.0f}원")
            return None

        # 새 조정 기록
        adjustment = BalanceAdjustment(
            date=target_date,
            amount=diff,
            adjustment_type=adj_type.value,
            balance_before=prev_ending_balance,
            balance_after=current_starting_balance,
            notes=f"자동 감지 ({adj_type.value})",
        )
        self.session.add(adjustment)
        await self.session.flush()

        logger.info(
            f"잔고 조정 기록: {adj_type.value} {diff:,.0f}원 "
            f"({prev_ending_balance:,.0f} → {current_starting_balance:,.0f})"
        )

        return adjustment

    def _calculate_mdd_from_pnl(self, stats: list[DailyStats]) -> float:
        """
        MDD (Maximum Drawdown) 계산 - 누적 실현 손익 기준

        Args:
            stats: DailyStats 리스트 (날짜 오름차순)

        Returns:
            float: MDD 비율 (%)
        """
        if not stats:
            return 0.0

        # 누적 손익으로 MDD 계산
        cumulative_pnl = Decimal("0")
        peak_pnl = Decimal("0")
        max_drawdown = Decimal("0")

        for stat in stats:
            cumulative_pnl += stat.realized_pnl

            if cumulative_pnl > peak_pnl:
                peak_pnl = cumulative_pnl

            if peak_pnl > 0:
                drawdown = (peak_pnl - cumulative_pnl) / peak_pnl * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return float(max_drawdown)

    def _generate_chart_data(
        self,
        stats: list[DailyStats],
        current_balance: Decimal | None = None,
    ) -> list[ProfitDataPoint]:
        """
        수익 차트 데이터 생성 (최근 30일, 누적 실현 손익 + 오늘 포인트)

        Args:
            stats: DailyStats 리스트 (날짜 오름차순)
            current_balance: 현재 Upbit 총 잔고 (오늘 포인트 추가용)

        Returns:
            list[ProfitDataPoint]: 차트 데이터 포인트 리스트
        """
        # 최근 30일 필터링
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        recent_stats = [s for s in stats if s.date >= thirty_days_ago]

        # 30일 이전까지의 누적 손익 계산 (시작점)
        prior_pnl = sum(s.realized_pnl for s in stats if s.date < thirty_days_ago)

        # 차트 데이터 생성 (누적 실현 손익)
        chart_data: list[ProfitDataPoint] = []
        cumulative_pnl = prior_pnl

        for stat in recent_stats:
            cumulative_pnl += stat.realized_pnl
            chart_data.append(
                ProfitDataPoint(
                    date=stat.date.isoformat(),
                    value=cumulative_pnl,
                )
            )

        # 오늘 DailyStats가 없으면 current_balance 기반 미실현 손익 포인트 추가
        has_today = any(s.date == today for s in recent_stats)
        if not has_today and current_balance is not None and stats:
            # 미실현 손익 = current_balance - 최근 ending_balance + 누적 실현 손익
            last_stat = stats[-1]
            unrealized_change = current_balance - last_stat.ending_balance
            chart_data.append(
                ProfitDataPoint(
                    date=today.isoformat(),
                    value=cumulative_pnl + unrealized_change,
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
