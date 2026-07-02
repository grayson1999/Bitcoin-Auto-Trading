"""
포트폴리오 서비스 모듈

이 모듈은 포트폴리오 통계 계산 로직을 제공합니다.
- DailyStats 테이블에서 데이터 집계
- 누적 수익률, 승률, MDD 계산
- 입금/출금 자동 감지 및 추적
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import UpbitPrivateAPIError, get_upbit_private_api
from src.entities import AdjustmentType, BalanceAdjustment, DailyStats, Order
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
                net_realized_pnl=Decimal("0"),
                today_return_pct=0.0,
                today_realized_pnl=Decimal("0"),
                total_trades=0,
                win_count=0,
                loss_count=0,
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
        # trade_count 는 매수+매도 모든 체결을 세므로 승률 분모로 부적절.
        # 승/패는 매도 청산에서만 집계되므로 청산 거래 수(win+loss)를 분모로 사용.
        total_trades = sum(stat.trade_count for stat in all_stats)
        win_count = sum(stat.win_count for stat in all_stats)
        loss_count = sum(stat.loss_count for stat in all_stats)
        closed_trades = win_count + loss_count
        win_rate = (win_count / closed_trades * 100) if closed_trades > 0 else 0.0

        # 누적 실현 손익 (gross) 및 순손익 (수수료 차감)
        total_pnl = sum(stat.realized_pnl for stat in all_stats)
        total_fees_paid = await self._calculate_total_fees_paid()
        net_pnl = total_pnl - total_fees_paid

        # 누적 수익률 (순손익=실현손익-수수료 기준)
        if total_invested > 0:
            cumulative_return_pct = float(net_pnl / total_invested * 100)
        else:
            cumulative_return_pct = 0.0

        # 평균 수익률 (청산 거래당, 순손익 기준)
        average_return_pct = (
            float(net_pnl / closed_trades / total_invested * 100)
            if closed_trades > 0 and total_invested > 0
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
            net_realized_pnl=net_pnl,
            today_return_pct=today_return_pct,
            today_realized_pnl=today_realized_pnl,
            total_trades=total_trades,
            win_count=win_count,
            loss_count=loss_count,
            win_rate=win_rate,
            average_return_pct=average_return_pct,
            max_drawdown_pct=max_drawdown_pct,
            total_fees_paid=total_fees_paid,
            profit_chart_data=profit_chart_data,
        )

    async def _calculate_total_fees_paid(self) -> Decimal:
        """체결된 주문의 누적 수수료 합계 (KRW)."""
        stmt = select(func.sum(Order.fee)).where(Order.fee.isnot(None))
        result = await self.session.execute(stmt)
        return result.scalar() or Decimal("0")

    async def get_deposit_history(self, limit: int = 50) -> list[BalanceAdjustment]:
        """입출금(BalanceAdjustment) 내역 조회 (최신순)."""
        stmt = (
            select(BalanceAdjustment)
            .where(
                BalanceAdjustment.adjustment_type.in_(
                    [AdjustmentType.DEPOSIT.value, AdjustmentType.WITHDRAWAL.value]
                )
            )
            .order_by(BalanceAdjustment.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def sync_deposits_from_upbit(self) -> int:
        """
        Upbit 입금 원장(/v1/deposits)을 BalanceAdjustment로 동기화한다.

        잔고 차이 추정과 달리 실제 입금만 정확히 반영(코인 평가변동에 오염 안 됨).
        봇 운영 기간 손익 기준을 위해, 봇 시작일(첫 DailyStats.date) "이후"의
        입금만 기록한다(시작일·이전 입금은 initial_balance에 이미 포함).

        Returns:
            int: 새로 기록한 입금 건수
        """
        # 봇 시작일 조회
        first_stmt = select(DailyStats).order_by(DailyStats.date.asc()).limit(1)
        first_stats = (await self.session.execute(first_stmt)).scalar_one_or_none()
        if first_stats is None:
            logger.info("DailyStats 없음 - 입금 동기화 건너뜀")
            return 0
        start_date = first_stats.date
        user_id = first_stats.user_id

        # Upbit 입금 원장 조회
        try:
            deposits = await get_upbit_private_api().get_krw_deposits(limit=100)
        except UpbitPrivateAPIError as e:
            logger.warning(f"Upbit 입금 원장 조회 실패: {e.message}")
            return 0

        recorded = 0
        for dep in deposits:
            # created_at(ISO8601) → date. 봇 시작일 '이후'만 대상.
            try:
                dep_date = datetime.fromisoformat(dep.created_at).date()
            except ValueError:
                dep_date = date.fromisoformat(dep.created_at[:10])
            if dep_date <= start_date:
                continue

            # 중복 방지: 같은 date + amount 기록이 있으면 스킵
            exists_stmt = select(BalanceAdjustment).where(
                BalanceAdjustment.date == dep_date,
                BalanceAdjustment.amount == dep.amount,
            )
            if (await self.session.execute(exists_stmt)).scalar_one_or_none():
                continue

            self.session.add(
                BalanceAdjustment(
                    user_id=user_id,
                    date=dep_date,
                    amount=dep.amount,
                    adjustment_type=AdjustmentType.DEPOSIT.value,
                    balance_before=Decimal("0"),
                    balance_after=Decimal("0"),
                    notes=f"Upbit 원장 동기화 (uuid={dep.uuid})",
                )
            )
            recorded += 1
            logger.info(f"입금 기록: {dep_date} {float(dep.amount):,.0f}원")

        if recorded:
            await self.session.flush()
            logger.info(f"Upbit 입금 동기화 완료: {recorded}건 신규 기록")
        return recorded

    async def sync_withdrawals_from_upbit(self) -> int:
        """
        Upbit 출금 원장(/v1/withdraws)을 BalanceAdjustment로 동기화한다.

        입금과 동일 골격이나 완료 상태값이 "DONE"이고, 계좌에서 실제 빠져나간
        총액(amount+fee)을 음수 amount로 기록해 원금에서 정확히 차감되게 한다.
        봇 시작일(첫 DailyStats.date) "이후"의 출금만 기록한다.

        Returns:
            int: 새로 기록한 출금 건수
        """
        # 봇 시작일 조회
        first_stmt = select(DailyStats).order_by(DailyStats.date.asc()).limit(1)
        first_stats = (await self.session.execute(first_stmt)).scalar_one_or_none()
        if first_stats is None:
            logger.info("DailyStats 없음 - 출금 동기화 건너뜀")
            return 0
        start_date = first_stats.date
        user_id = first_stats.user_id

        # Upbit 출금 원장 조회
        try:
            withdraws = await get_upbit_private_api().get_krw_withdraws(limit=100)
        except UpbitPrivateAPIError as e:
            logger.warning(f"Upbit 출금 원장 조회 실패: {e.message}")
            return 0

        recorded = 0
        for wd in withdraws:
            # created_at(ISO8601) → date. 봇 시작일 '이후'만 대상.
            try:
                wd_date = datetime.fromisoformat(wd.created_at).date()
            except ValueError:
                wd_date = date.fromisoformat(wd.created_at[:10])
            if wd_date <= start_date:
                continue

            # 계좌에서 실제 빠져나간 총액 = amount + fee (음수로 기록)
            total_out = -(wd.amount + wd.fee)

            # 중복 방지: 같은 date + amount 기록이 있으면 스킵
            exists_stmt = select(BalanceAdjustment).where(
                BalanceAdjustment.date == wd_date,
                BalanceAdjustment.amount == total_out,
            )
            if (await self.session.execute(exists_stmt)).scalar_one_or_none():
                continue

            self.session.add(
                BalanceAdjustment(
                    user_id=user_id,
                    date=wd_date,
                    amount=total_out,
                    adjustment_type=AdjustmentType.WITHDRAWAL.value,
                    balance_before=Decimal("0"),
                    balance_after=Decimal("0"),
                    notes=f"Upbit 출금 원장 동기화 (uuid={wd.uuid})",
                )
            )
            recorded += 1
            logger.info(
                f"출금 기록: {wd_date} {float(total_out):,.0f}원 "
                f"(amount={float(wd.amount):,.0f}, fee={float(wd.fee):,.0f})"
            )

        if recorded:
            await self.session.flush()
            logger.info(f"Upbit 출금 동기화 완료: {recorded}건 신규 기록")
        return recorded

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
