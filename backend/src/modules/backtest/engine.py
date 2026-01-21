"""
백테스트 시뮬레이션 엔진 모듈

이 모듈은 백테스트의 거래 시뮬레이션을 담당합니다.
- 신호 기반 매수/매도 시뮬레이션
- 포지션 관리
- 거래 내역 기록
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from loguru import logger

from src.config.constants import (
    BACKTEST_MIN_TRADE_AMOUNT_PCT,
    BACKTEST_SLIPPAGE_PCT,
    BACKTEST_TRADING_FEE_PCT,
)
from src.entities import TradingSignal
from src.entities.trading_signal import SignalType

# 상수를 Decimal로 변환
TRADING_FEE_PCT = Decimal(str(BACKTEST_TRADING_FEE_PCT))
SLIPPAGE_PCT = Decimal(str(BACKTEST_SLIPPAGE_PCT))
MIN_TRADE_AMOUNT_PCT = Decimal(str(BACKTEST_MIN_TRADE_AMOUNT_PCT))


@dataclass
class CandlePriceData:
    """
    캔들 가격 데이터 (백테스트용)

    Upbit 캔들 API에서 가져온 데이터를 백테스트에서 사용하기 위한 구조체입니다.

    Attributes:
        timestamp: 캔들 시간 (UTC)
        price: 종가 (현재가)
        high_price: 고가
        low_price: 저가
        volume: 거래량
    """

    timestamp: datetime
    price: Decimal
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    volume: Decimal | None = None


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
class BacktestState:
    """
    백테스트 상태

    시뮬레이션 중 포지션 및 잔고 상태를 추적합니다.

    Attributes:
        cash: 현금 잔고 (KRW)
        position_quantity: 보유 수량
        avg_buy_price: 평균 매수가
        trades: 거래 내역
        equity_curve: 자산 곡선 (일별 자산 가치)
    """

    cash: Decimal = Decimal("0")
    position_quantity: Decimal = Decimal("0")
    avg_buy_price: Decimal = Decimal("0")
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[tuple[datetime, Decimal]] = field(default_factory=list)


class BacktestEngine:
    """
    백테스트 시뮬레이션 엔진

    과거 신호와 시장 데이터를 기반으로 거래를 시뮬레이션합니다.
    """

    async def simulate_trading(
        self,
        state: BacktestState,
        signals: list[TradingSignal],
        market_data: dict[datetime, CandlePriceData],
    ) -> BacktestState:
        """
        거래 시뮬레이션

        신호에 따라 매수/매도를 시뮬레이션합니다.

        Args:
            state: 현재 상태
            signals: 신호 목록
            market_data: 시장 데이터 (시간별 인덱싱, CandlePriceData)

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
        invest_pct = Decimal(
            str(MIN_TRADE_AMOUNT_PCT + Decimal("0.08") * Decimal(str(confidence)))
        )
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
