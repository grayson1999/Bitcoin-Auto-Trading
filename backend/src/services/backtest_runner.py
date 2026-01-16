"""
백테스트 실행 서비스

이 모듈은 과거 데이터로 AI 전략을 시뮬레이션하는 서비스를 제공합니다.
- 신호 시뮬레이션 (과거 데이터 기반)
- 성과 지표 계산 (수익률, MDD, 승률, 손익비, 샤프 비율)
- 거래 내역 기록
"""

import json
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import BacktestResult, BacktestStatus, MarketData, TradingSignal
from src.models.trading_signal import SignalType

# === 백테스트 상수 ===
DEFAULT_INITIAL_CAPITAL = Decimal("1000000")  # 기본 초기 자본금 (100만원)
TRADING_FEE_PCT = Decimal("0.0005")  # 거래 수수료 0.05%
SLIPPAGE_PCT = Decimal("0.001")  # 슬리피지 0.1%
MIN_TRADE_AMOUNT_PCT = Decimal("0.02")  # 최소 거래 비율 2%
RISK_FREE_RATE = 0.035  # 무위험 수익률 (연 3.5%)


@dataclass
class Trade:
    """
    거래 기록

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

    timestamp: datetime
    signal_type: str
    price: Decimal
    quantity: Decimal
    amount: Decimal
    fee: Decimal
    pnl: Decimal = Decimal("0")
    pnl_pct: float = 0.0
    balance_after: Decimal = Decimal("0")


@dataclass
class BacktestMetrics:
    """
    백테스트 성과 지표

    Attributes:
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
        final_capital: 최종 자본금
    """

    total_return_pct: Decimal = Decimal("0")
    max_drawdown_pct: Decimal = Decimal("0")
    win_rate_pct: Decimal = Decimal("0")
    profit_factor: Decimal = Decimal("0")
    sharpe_ratio: Decimal = Decimal("0")
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_profit_pct: Decimal = Decimal("0")
    avg_loss_pct: Decimal = Decimal("0")
    final_capital: Decimal = Decimal("0")


@dataclass
class BacktestState:
    """
    백테스트 상태

    시뮬레이션 중 포지션 및 잔고 상태를 추적합니다.

    Attributes:
        cash: 현금 잔고 (KRW)
        position_quantity: 보유 수량 (XRP)
        avg_buy_price: 평균 매수가
        trades: 거래 내역
        equity_curve: 자산 곡선 (일별 자산 가치)
    """

    cash: Decimal = Decimal("0")
    position_quantity: Decimal = Decimal("0")
    avg_buy_price: Decimal = Decimal("0")
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[tuple[datetime, Decimal]] = field(default_factory=list)


class BacktestRunnerError(Exception):
    """백테스트 실행 오류"""

    pass


class BacktestRunner:
    """
    백테스트 실행 서비스

    과거 시장 데이터와 AI 신호를 기반으로 전략 성과를 시뮬레이션합니다.

    사용 예시:
        runner = BacktestRunner(db_session)
        result = await runner.run_backtest(
            name="6개월 테스트",
            start_date=datetime(2024, 7, 1),
            end_date=datetime(2025, 1, 1),
            initial_capital=Decimal("1000000"),
        )
        print(f"수익률: {result.total_return_pct}%")
    """

    def __init__(self, db: AsyncSession):
        """
        백테스트 러너 초기화

        Args:
            db: SQLAlchemy 비동기 세션
        """
        self.db = db

    async def run_backtest(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: Decimal = DEFAULT_INITIAL_CAPITAL,
    ) -> BacktestResult:
        """
        백테스트 실행

        지정된 기간의 과거 데이터로 전략을 시뮬레이션하고 결과를 저장합니다.

        Args:
            name: 백테스트 이름
            start_date: 시작 날짜
            end_date: 종료 날짜
            initial_capital: 초기 자본금

        Returns:
            BacktestResult: 백테스트 결과

        Raises:
            BacktestRunnerError: 실행 실패 시
        """
        logger.info(
            f"백테스트 시작: {name} ({start_date.date()} ~ {end_date.date()})"
        )

        # 1. 결과 레코드 생성 (RUNNING 상태)
        result = BacktestResult(
            name=name,
            status=BacktestStatus.RUNNING.value,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            created_at=datetime.now(UTC),
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)

        try:
            # 2. 과거 신호 조회
            signals = await self._get_signals_in_range(start_date, end_date)
            if not signals:
                raise BacktestRunnerError(
                    f"기간 내 신호가 없습니다: {start_date.date()} ~ {end_date.date()}"
                )

            logger.info(f"시뮬레이션 대상 신호: {len(signals)}개")

            # 3. 시장 데이터 조회 (신호 시점의 가격 확인용)
            market_data = await self._get_market_data_in_range(start_date, end_date)
            if not market_data:
                raise BacktestRunnerError("기간 내 시장 데이터가 없습니다")

            # 4. 시뮬레이션 실행
            state = BacktestState(cash=initial_capital)
            state = await self._simulate_trading(state, signals, market_data)

            # 5. 성과 지표 계산
            metrics = self._calculate_metrics(state, initial_capital)

            # 6. 결과 업데이트
            result.status = BacktestStatus.COMPLETED.value
            result.final_capital = metrics.final_capital
            result.total_return_pct = metrics.total_return_pct
            result.max_drawdown_pct = metrics.max_drawdown_pct
            result.win_rate_pct = metrics.win_rate_pct
            result.profit_factor = metrics.profit_factor
            result.sharpe_ratio = metrics.sharpe_ratio
            result.total_trades = metrics.total_trades
            result.winning_trades = metrics.winning_trades
            result.losing_trades = metrics.losing_trades
            result.avg_profit_pct = metrics.avg_profit_pct
            result.avg_loss_pct = metrics.avg_loss_pct
            result.trade_history = self._serialize_trades(state.trades)
            result.completed_at = datetime.now(UTC)

            await self.db.commit()
            await self.db.refresh(result)

            logger.info(
                f"백테스트 완료: {name} - "
                f"수익률 {metrics.total_return_pct:.2f}%, "
                f"MDD {metrics.max_drawdown_pct:.2f}%, "
                f"승률 {metrics.win_rate_pct:.2f}%"
            )

            return result

        except Exception as e:
            # 오류 발생 시 상태 업데이트
            result.status = BacktestStatus.FAILED.value
            result.error_message = str(e)
            result.completed_at = datetime.now(UTC)
            await self.db.commit()

            logger.error(f"백테스트 실패: {name} - {e}")
            raise BacktestRunnerError(f"백테스트 실행 실패: {e}") from e

    async def _get_signals_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[TradingSignal]:
        """
        기간 내 신호 조회

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            list[TradingSignal]: 신호 목록 (시간순)
        """
        stmt = (
            select(TradingSignal)
            .where(
                TradingSignal.created_at >= start_date,
                TradingSignal.created_at <= end_date,
            )
            .order_by(TradingSignal.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_market_data_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[datetime, MarketData]:
        """
        기간 내 시장 데이터 조회 (시간별 인덱싱)

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            dict[datetime, MarketData]: 시간대별 시장 데이터
        """
        stmt = (
            select(MarketData)
            .where(
                MarketData.timestamp >= start_date,
                MarketData.timestamp <= end_date,
            )
            .order_by(MarketData.timestamp)
        )
        result = await self.db.execute(stmt)
        data_list = list(result.scalars().all())

        # 시간대별로 인덱싱 (시간 단위로 그룹화)
        indexed: dict[datetime, MarketData] = {}
        for data in data_list:
            hour_key = data.timestamp.replace(minute=0, second=0, microsecond=0)
            indexed[hour_key] = data  # 각 시간대의 마지막 데이터 사용

        return indexed

    async def _simulate_trading(
        self,
        state: BacktestState,
        signals: list[TradingSignal],
        market_data: dict[datetime, MarketData],
    ) -> BacktestState:
        """
        거래 시뮬레이션

        신호에 따라 매수/매도를 시뮬레이션합니다.

        Args:
            state: 현재 상태
            signals: 신호 목록
            market_data: 시장 데이터 (시간별 인덱싱)

        Returns:
            BacktestState: 업데이트된 상태
        """
        for signal in signals:
            # 신호 시점의 가격 조회
            hour_key = signal.created_at.replace(minute=0, second=0, microsecond=0)
            if hour_key not in market_data:
                # 가장 가까운 데이터 찾기
                closest_key = min(
                    market_data.keys(),
                    key=lambda x: abs((x - hour_key).total_seconds()),
                    default=None,
                )
                if closest_key is None:
                    continue
                hour_key = closest_key

            data = market_data[hour_key]
            price = data.price

            # 신호 처리
            if signal.signal_type == SignalType.BUY.value:
                state = self._execute_buy(state, signal, price)
            elif signal.signal_type == SignalType.SELL.value:
                state = self._execute_sell(state, signal, price)

            # 자산 곡선 업데이트
            total_value = state.cash + (state.position_quantity * price)
            state.equity_curve.append((signal.created_at, total_value))

        return state

    def _execute_buy(
        self,
        state: BacktestState,
        signal: TradingSignal,
        price: Decimal,
    ) -> BacktestState:
        """
        매수 실행

        Args:
            state: 현재 상태
            signal: 매수 신호
            price: 현재 가격

        Returns:
            BacktestState: 업데이트된 상태
        """
        # 투자 금액 계산 (전체 현금의 일정 비율)
        # 신뢰도가 높을수록 더 많이 투자 (2% ~ 10%)
        confidence = float(signal.confidence)
        invest_pct = Decimal(str(MIN_TRADE_AMOUNT_PCT + Decimal("0.08") * Decimal(str(confidence))))
        invest_amount = state.cash * invest_pct

        if invest_amount <= 0 or state.cash < invest_amount:
            return state

        # 슬리피지 적용 (불리한 가격으로 체결)
        execution_price = price * (1 + SLIPPAGE_PCT)

        # 수량 계산
        quantity = invest_amount / execution_price

        # 수수료 계산
        fee = invest_amount * TRADING_FEE_PCT

        # 상태 업데이트
        total_cost = invest_amount + fee

        # 평균 매수가 업데이트
        if state.position_quantity > 0:
            total_position_value = (
                state.position_quantity * state.avg_buy_price + invest_amount
            )
            state.avg_buy_price = total_position_value / (
                state.position_quantity + quantity
            )
        else:
            state.avg_buy_price = execution_price

        state.cash -= total_cost
        state.position_quantity += quantity

        # 거래 기록
        trade = Trade(
            timestamp=signal.created_at,
            signal_type=SignalType.BUY.value,
            price=execution_price,
            quantity=quantity,
            amount=invest_amount,
            fee=fee,
            balance_after=state.cash,
        )
        state.trades.append(trade)

        logger.debug(
            f"BUY: {quantity:.4f} @ {execution_price:,.0f}, "
            f"금액: {invest_amount:,.0f}, 잔고: {state.cash:,.0f}"
        )

        return state

    def _execute_sell(
        self,
        state: BacktestState,
        signal: TradingSignal,
        price: Decimal,
    ) -> BacktestState:
        """
        매도 실행

        Args:
            state: 현재 상태
            signal: 매도 신호
            price: 현재 가격

        Returns:
            BacktestState: 업데이트된 상태
        """
        if state.position_quantity <= 0:
            return state

        # 슬리피지 적용 (불리한 가격으로 체결)
        execution_price = price * (1 - SLIPPAGE_PCT)

        # 전량 매도
        quantity = state.position_quantity
        sell_amount = quantity * execution_price

        # 수수료 계산
        fee = sell_amount * TRADING_FEE_PCT

        # 손익 계산
        cost_basis = quantity * state.avg_buy_price
        pnl = sell_amount - cost_basis - fee
        pnl_pct = float((pnl / cost_basis) * 100) if cost_basis > 0 else 0.0

        # 상태 업데이트
        state.cash += sell_amount - fee
        state.position_quantity = Decimal("0")
        state.avg_buy_price = Decimal("0")

        # 거래 기록
        trade = Trade(
            timestamp=signal.created_at,
            signal_type=SignalType.SELL.value,
            price=execution_price,
            quantity=quantity,
            amount=sell_amount,
            fee=fee,
            pnl=pnl,
            pnl_pct=pnl_pct,
            balance_after=state.cash,
        )
        state.trades.append(trade)

        logger.debug(
            f"SELL: {quantity:.4f} @ {execution_price:,.0f}, "
            f"금액: {sell_amount:,.0f}, 손익: {pnl:+,.0f} ({pnl_pct:+.2f}%), "
            f"잔고: {state.cash:,.0f}"
        )

        return state

    def _calculate_metrics(
        self,
        state: BacktestState,
        initial_capital: Decimal,
    ) -> BacktestMetrics:
        """
        성과 지표 계산

        Args:
            state: 최종 상태
            initial_capital: 초기 자본금

        Returns:
            BacktestMetrics: 계산된 지표
        """
        metrics = BacktestMetrics()

        # 최종 자본금 (포지션이 있으면 마지막 가격으로 평가)
        if state.equity_curve:
            _, last_equity = state.equity_curve[-1]
            metrics.final_capital = last_equity
        else:
            metrics.final_capital = state.cash

        # 총 수익률
        if initial_capital > 0:
            metrics.total_return_pct = (
                (metrics.final_capital - initial_capital) / initial_capital * 100
            )

        # 거래 통계
        sell_trades = [t for t in state.trades if t.signal_type == SignalType.SELL.value]
        metrics.total_trades = len(sell_trades)

        if sell_trades:
            winning = [t for t in sell_trades if t.pnl > 0]
            losing = [t for t in sell_trades if t.pnl < 0]

            metrics.winning_trades = len(winning)
            metrics.losing_trades = len(losing)

            # 승률
            metrics.win_rate_pct = Decimal(
                str(len(winning) / len(sell_trades) * 100)
            )

            # 평균 수익률/손실률
            if winning:
                metrics.avg_profit_pct = Decimal(
                    str(sum(t.pnl_pct for t in winning) / len(winning))
                )
            if losing:
                metrics.avg_loss_pct = Decimal(
                    str(abs(sum(t.pnl_pct for t in losing) / len(losing)))
                )

            # 손익비 (총이익/총손실)
            total_profit = sum(t.pnl for t in winning) if winning else Decimal("0")
            total_loss = abs(sum(t.pnl for t in losing)) if losing else Decimal("0")
            if total_loss > 0:
                metrics.profit_factor = total_profit / total_loss
            elif total_profit > 0:
                metrics.profit_factor = Decimal("999.99")  # 무한대 대신 큰 값

        # MDD 계산
        metrics.max_drawdown_pct = self._calculate_mdd(state.equity_curve)

        # 샤프 비율 계산
        metrics.sharpe_ratio = self._calculate_sharpe_ratio(state.equity_curve)

        return metrics

    def _calculate_mdd(
        self,
        equity_curve: list[tuple[datetime, Decimal]],
    ) -> Decimal:
        """
        최대 낙폭 (MDD) 계산

        자산 곡선에서 최고점 대비 최대 하락폭을 계산합니다.

        Args:
            equity_curve: 자산 곡선 [(시간, 자산가치), ...]

        Returns:
            Decimal: MDD (%)
        """
        if len(equity_curve) < 2:
            return Decimal("0")

        max_equity = Decimal("0")
        max_drawdown = Decimal("0")

        for _, equity in equity_curve:
            if equity > max_equity:
                max_equity = equity

            if max_equity > 0:
                drawdown = (max_equity - equity) / max_equity * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return max_drawdown

    def _calculate_sharpe_ratio(
        self,
        equity_curve: list[tuple[datetime, Decimal]],
    ) -> Decimal:
        """
        샤프 비율 계산

        위험 조정 수익률을 계산합니다.
        Sharpe = (평균 수익률 - 무위험 수익률) / 수익률 표준편차

        Args:
            equity_curve: 자산 곡선

        Returns:
            Decimal: 샤프 비율
        """
        if len(equity_curve) < 3:
            return Decimal("0")

        # 일별 수익률 계산
        returns: list[float] = []
        for i in range(1, len(equity_curve)):
            prev_equity = float(equity_curve[i - 1][1])
            curr_equity = float(equity_curve[i][1])
            if prev_equity > 0:
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)

        if len(returns) < 2:
            return Decimal("0")

        # 평균 수익률
        avg_return = sum(returns) / len(returns)

        # 표준편차
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance) if variance > 0 else 0

        if std_dev == 0:
            return Decimal("0")

        # 연환산 (시간 단위로 가정, 하루 24개 신호)
        annualized_return = avg_return * 24 * 365
        annualized_std = std_dev * math.sqrt(24 * 365)

        # 샤프 비율
        sharpe = (annualized_return - RISK_FREE_RATE) / annualized_std

        return Decimal(str(round(sharpe, 4)))

    def _serialize_trades(self, trades: list[Trade]) -> str:
        """
        거래 내역 JSON 직렬화

        Args:
            trades: 거래 목록

        Returns:
            str: JSON 문자열
        """
        trade_list = []
        for trade in trades:
            trade_list.append({
                "timestamp": trade.timestamp.isoformat(),
                "signal_type": trade.signal_type,
                "price": float(trade.price),
                "quantity": float(trade.quantity),
                "amount": float(trade.amount),
                "fee": float(trade.fee),
                "pnl": float(trade.pnl),
                "pnl_pct": trade.pnl_pct,
                "balance_after": float(trade.balance_after),
            })

        return json.dumps(trade_list, ensure_ascii=False)

    async def get_result(self, result_id: int) -> BacktestResult | None:
        """
        백테스트 결과 조회

        Args:
            result_id: 결과 ID

        Returns:
            BacktestResult | None: 결과 또는 None
        """
        stmt = select(BacktestResult).where(BacktestResult.id == result_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_results(
        self,
        limit: int = 20,
        status: str | None = None,
    ) -> list[BacktestResult]:
        """
        백테스트 결과 목록 조회

        Args:
            limit: 최대 조회 개수
            status: 상태 필터 (선택)

        Returns:
            list[BacktestResult]: 결과 목록 (최신순)
        """
        stmt = select(BacktestResult).order_by(desc(BacktestResult.created_at))

        if status:
            stmt = stmt.where(BacktestResult.status == status)

        stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())


# === 팩토리 함수 ===
def get_backtest_runner(db: AsyncSession) -> BacktestRunner:
    """
    BacktestRunner 인스턴스 생성

    Args:
        db: SQLAlchemy 비동기 세션

    Returns:
        BacktestRunner: 백테스트 러너 인스턴스
    """
    return BacktestRunner(db)
