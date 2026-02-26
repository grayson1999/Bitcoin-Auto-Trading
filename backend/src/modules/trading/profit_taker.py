"""
룰 기반 익절 엔진

5분마다 포지션 수익률을 체크하고 단계적 부분 매도를 실행합니다.
- 티어별 부분 매도 (+2%, +5%, +8%)
- 트레일링 스탑 (최고가 대비 -2.5%)
- 최소 주문금액(5,000원) 미달 시 전량 매도
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import (
    UpbitPrivateAPI,
    UpbitPrivateAPIError,
    UpbitPublicAPI,
    UpbitPublicAPIError,
)
from src.config import settings
from src.config.constants import UPBIT_MIN_ORDER_KRW
from src.entities import (
    DailyStats,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    TradingSignal,
)
from src.utils import UTC

if TYPE_CHECKING:
    pass


class ProfitTaker:
    """
    룰 기반 익절 엔진

    포지션 수익률에 따라 단계적 부분 매도 및 트레일링 스탑을 실행합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        private_api: UpbitPrivateAPI,
        public_api: UpbitPublicAPI,
        user_id: int,
    ) -> None:
        self._session = session
        self._private_api = private_api
        self._public_api = public_api
        self._user_id = user_id

    async def check_and_execute(self) -> None:
        """메인 진입점: 포지션 체크 후 익절/트레일링 스탑 실행"""
        if not settings.profit_take_enabled:
            return

        position = await self._get_position()
        if not position or position.quantity <= 0 or position.avg_buy_price <= 0:
            return

        # 현재가 조회
        try:
            ticker = await self._public_api.get_ticker(settings.trading_ticker)
            current_price = ticker.trade_price
        except (UpbitPublicAPIError, Exception) as e:
            logger.warning(f"[ProfitTaker] 현재가 조회 실패: {e}")
            return

        # Dust 포지션 정리: 포지션 가치 < 최소 주문금액
        position_value = position.quantity * current_price
        if position_value < UPBIT_MIN_ORDER_KRW:
            logger.info(
                f"[ProfitTaker] Dust 포지션 정리: "
                f"quantity={position.quantity}, value={position_value:,.0f}원"
            )
            position.quantity = Decimal("0")
            position.avg_buy_price = Decimal("0")
            position.profit_tier_reached = 0
            position.peak_price = None
            position.trailing_stop_active = False
            position.original_quantity = None
            await self._session.commit()
            return

        # 미실현 손익률 계산
        pnl_pct = float(
            (current_price - position.avg_buy_price) / position.avg_buy_price * 100
        )

        # original_quantity 초기화 (최초 진입 시)
        if position.original_quantity is None or position.original_quantity <= 0:
            position.original_quantity = position.quantity
            logger.info(
                f"[ProfitTaker] original_quantity 설정: {position.original_quantity}"
            )

        # peak_price 업데이트
        if position.peak_price is None or current_price > position.peak_price:
            position.peak_price = current_price

        # 트레일링 스탑 활성화 체크
        if not position.trailing_stop_active and pnl_pct >= settings.trailing_stop_activation_pct:
            position.trailing_stop_active = True
            logger.info(
                f"[ProfitTaker] 트레일링 스탑 활성화: "
                f"PnL={pnl_pct:+.2f}% >= {settings.trailing_stop_activation_pct}%"
            )

        # 1. 트레일링 스탑 체크 (활성 시)
        if position.trailing_stop_active:
            triggered = await self._check_trailing_stop(position, current_price)
            if triggered:
                await self._session.commit()
                return

        # 2. 익절 티어 체크
        await self._check_profit_tiers(position, current_price, pnl_pct)
        await self._session.commit()

    async def _check_profit_tiers(
        self,
        position: Position,
        current_price: Decimal,
        pnl_pct: float,
    ) -> None:
        """티어별 부분 매도 실행"""
        tiers = [
            (1, settings.profit_tier_1_pct, settings.profit_tier_1_sell_pct),
            (2, settings.profit_tier_2_pct, settings.profit_tier_2_sell_pct),
            (3, settings.profit_tier_3_pct, settings.profit_tier_3_sell_pct),
        ]

        for tier_num, profit_pct, sell_pct in tiers:
            if position.profit_tier_reached >= tier_num:
                continue

            if pnl_pct < profit_pct:
                break

            # 티어 조건 충족
            sell_volume = self._calculate_sell_volume(
                position, sell_pct, current_price
            )
            if sell_volume <= 0:
                continue

            logger.info(
                f"[ProfitTaker] 익절 Tier {tier_num} 실행: "
                f"PnL={pnl_pct:+.2f}% >= {profit_pct}%, "
                f"매도 {sell_pct}% = {sell_volume} ({sell_volume * current_price:,.0f}원)"
            )

            success = await self._execute_partial_sell(
                position, sell_volume, current_price,
                reason=f"profit-take-tier-{tier_num}",
            )
            if success:
                position.profit_tier_reached = tier_num

    async def _check_trailing_stop(
        self,
        position: Position,
        current_price: Decimal,
    ) -> bool:
        """트레일링 스탑 발동 체크 → 나머지 전량 매도"""
        if not position.peak_price or position.peak_price <= 0:
            return False

        drop_from_peak_pct = float(
            (position.peak_price - current_price) / position.peak_price * 100
        )

        if drop_from_peak_pct >= settings.trailing_stop_distance_pct:
            logger.info(
                f"[ProfitTaker] 트레일링 스탑 발동: "
                f"최고가 {position.peak_price:,.0f} → 현재가 {current_price:,.0f} "
                f"({drop_from_peak_pct:+.2f}% >= {settings.trailing_stop_distance_pct}%)"
            )

            sell_volume = position.quantity
            success = await self._execute_partial_sell(
                position, sell_volume, current_price,
                reason="trailing-stop",
            )
            if not success:
                logger.warning("[ProfitTaker] 트레일링 스탑 매도 실패")
                return False
            return True

        return False

    def _calculate_sell_volume(
        self,
        position: Position,
        sell_pct: int,
        current_price: Decimal,
    ) -> Decimal:
        """
        매도 수량 계산 (original_quantity 기준)

        최소 주문금액(5,000원) 미달 시 남은 전량 매도로 전환.
        """
        if not position.original_quantity or position.original_quantity <= 0:
            return Decimal("0")

        target_volume = position.original_quantity * Decimal(str(sell_pct)) / Decimal("100")

        # 남은 수량보다 많으면 전량
        if target_volume >= position.quantity:
            target_volume = position.quantity

        # 최소 주문금액 체크
        order_value = target_volume * current_price
        if order_value < UPBIT_MIN_ORDER_KRW:
            # 남은 전량이 최소 금액 이상이면 전량 매도
            remaining_value = position.quantity * current_price
            if remaining_value >= UPBIT_MIN_ORDER_KRW:
                logger.info(
                    f"[ProfitTaker] 부분 매도 금액 {order_value:,.0f}원 < "
                    f"최소 {UPBIT_MIN_ORDER_KRW}원 → 전량 매도"
                )
                return position.quantity
            # 전량도 최소 미달이면 스킵
            logger.debug(
                f"[ProfitTaker] 전량 매도도 최소 미달 ({remaining_value:,.0f}원) → 스킵"
            )
            return Decimal("0")

        return target_volume

    async def _execute_partial_sell(
        self,
        position: Position,
        sell_volume: Decimal,
        current_price: Decimal,
        reason: str,
    ) -> bool:
        """
        부분 매도 실행

        TradingSignal 생성 + Upbit 시장가 매도 + 포지션/통계 업데이트
        """
        try:
            # 1. TradingSignal 생성 (룰 기반)
            signal = TradingSignal(
                signal_type="SELL",
                confidence=Decimal("0.90"),
                reasoning=f"[시스템] 자동 익절 ({reason}): {sell_volume} BTC ({sell_volume * current_price:,.0f}원) 매도",
                created_at=datetime.now(UTC),
                model_name=f"rule-{reason}",
                input_tokens=0,
                output_tokens=0,
                price_at_signal=current_price,
                action_score=-0.8,
            )
            self._session.add(signal)
            await self._session.flush()

            # 2. Order 레코드 생성
            order = Order(
                user_id=self._user_id,
                signal_id=signal.id,
                order_type=OrderType.MARKET.value,
                side=OrderSide.SELL.value,
                market=settings.trading_ticker,
                amount=sell_volume,
                status=OrderStatus.PENDING.value,
                created_at=datetime.now(UTC),
                idempotency_key=str(uuid.uuid4()),
                avg_cost_at_order=position.avg_buy_price,
            )
            self._session.add(order)
            await self._session.flush()

            # 3. Upbit 시장가 매도
            upbit_response = await self._private_api.place_order(
                market=settings.trading_ticker,
                side="ask",
                volume=sell_volume,
                ord_type="market",
            )

            order.upbit_uuid = upbit_response.uuid
            order.status = OrderStatus.EXECUTED.value
            order.executed_price = current_price
            order.executed_amount = sell_volume

            # 4. 포지션 업데이트
            position.quantity = max(
                Decimal("0"), position.quantity - sell_volume
            )
            if position.quantity == 0:
                # 전량 청산 시 초기화
                position.avg_buy_price = Decimal("0")
                position.profit_tier_reached = 0
                position.peak_price = None
                position.trailing_stop_active = False
                position.original_quantity = None

            position.update_value(current_price)
            position.updated_at = datetime.now(UTC)

            # 5. DailyStats 업데이트
            await self._update_daily_stats(order)

            logger.info(
                f"[ProfitTaker] 매도 완료: {reason}, "
                f"volume={sell_volume} ({sell_volume * current_price:,.0f}원), "
                f"price={current_price:,.0f}, remaining={position.quantity}"
            )
            return True

        except (UpbitPrivateAPIError, UpbitPublicAPIError) as e:
            logger.error(f"[ProfitTaker] Upbit 매도 실패: {e.message}")
            return False
        except Exception as e:
            logger.exception(f"[ProfitTaker] 매도 예외: {e}")
            return False

    async def _get_position(self) -> Position | None:
        """현재 포지션 조회"""
        stmt = select(Position).where(
            Position.symbol == settings.trading_ticker,
            Position.user_id == self._user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _update_daily_stats(self, order: Order) -> None:
        """일일 통계 업데이트 (매도 체결)"""
        today = date.today()
        stmt = select(DailyStats).where(DailyStats.date == today)
        result = await self._session.execute(stmt)
        daily_stats = result.scalar_one_or_none()

        if daily_stats is None:
            logger.warning("[ProfitTaker] DailyStats 미존재 → 통계 업데이트 스킵")
            return

        daily_stats.trade_count += 1

        if order.executed_amount and order.executed_price and order.avg_cost_at_order:
            pnl = (order.executed_price - order.avg_cost_at_order) * order.executed_amount
            daily_stats.realized_pnl += pnl
            if pnl >= 0:
                daily_stats.win_count += 1
            else:
                daily_stats.loss_count += 1

            logger.info(
                f"[ProfitTaker] 실현 손익: {pnl:,.0f}원 "
                f"(체결가={order.executed_price:,.0f}, "
                f"매수가={order.avg_cost_at_order:,.0f}, "
                f"수량={order.executed_amount})"
            )
