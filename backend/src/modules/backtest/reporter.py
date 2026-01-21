"""
백테스트 리포터 모듈

이 모듈은 백테스트 결과의 분석 및 리포팅을 담당합니다.
- 성과 지표 계산 (수익률, MDD, 승률, 손익비, 샤프 비율)
- 거래 내역 직렬화
"""

import json
import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.config.constants import BACKTEST_RISK_FREE_RATE
from src.entities.trading_signal import SignalType
from src.modules.backtest.engine import BacktestState, Trade


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


class BacktestReporter:
    """
    백테스트 리포터

    백테스트 결과에서 성과 지표를 계산하고 리포트를 생성합니다.
    """

    def calculate_metrics(
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
        sell_trades = [
            t for t in state.trades if t.signal_type == SignalType.SELL.value
        ]
        metrics.total_trades = len(sell_trades)

        if sell_trades:
            winning = [t for t in sell_trades if t.pnl > 0]
            losing = [t for t in sell_trades if t.pnl < 0]

            metrics.winning_trades = len(winning)
            metrics.losing_trades = len(losing)

            # 승률
            metrics.win_rate_pct = Decimal(str(len(winning) / len(sell_trades) * 100))

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
        sharpe = (annualized_return - BACKTEST_RISK_FREE_RATE) / annualized_std

        return Decimal(str(round(sharpe, 4)))

    def serialize_trades(self, trades: list[Trade]) -> str:
        """
        거래 내역 JSON 직렬화

        Args:
            trades: 거래 목록

        Returns:
            str: JSON 문자열
        """
        trade_list = []
        for trade in trades:
            trade_list.append(
                {
                    "timestamp": trade.timestamp.isoformat(),
                    "signal_type": trade.signal_type,
                    "price": float(trade.price),
                    "quantity": float(trade.quantity),
                    "amount": float(trade.amount),
                    "fee": float(trade.fee),
                    "pnl": float(trade.pnl),
                    "pnl_pct": trade.pnl_pct,
                    "balance_after": float(trade.balance_after),
                }
            )

        return json.dumps(trade_list, ensure_ascii=False)
