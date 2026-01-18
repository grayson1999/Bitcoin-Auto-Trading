"""
주문 실행 서비스

이 모듈은 AI 신호에 따른 자동 주문 실행을 담당합니다.
- 리스크 사전 체크 (T059)
- 주문 재시도 로직 (T060)
- 잔고 검증 (T061)
- 포지션 업데이트 (T068)
- 주문 생명주기 로깅 (T069)
"""

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    DailyStats,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    SignalType,
    TradingSignal,
)
from src.services.risk_manager import RiskCheckResult, RiskManager
from src.services.upbit_client import UpbitClient, UpbitError

if TYPE_CHECKING:
    from src.services.notifier import Notifier

# === 상수 ===
DEFAULT_MARKET = "KRW-XRP"
MAX_ORDER_RETRIES = 3  # 주문 재시도 횟수
RETRY_DELAY_SECONDS = 1.0  # 재시도 대기 시간
MIN_ORDER_AMOUNT_KRW = Decimal("5000")  # 최소 주문 금액 (원)
UPBIT_FEE_RATE = Decimal("0.0005")  # Upbit 수수료율 (0.05%)
ORDER_POLL_INTERVAL = 0.5  # 주문 체결 확인 간격 (초)
ORDER_POLL_MAX_ATTEMPTS = 10  # 주문 체결 확인 최대 시도 횟수


class OrderExecutorError(Exception):
    """주문 실행 오류"""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class OrderBlockedReason(str, Enum):
    """주문 차단 사유"""

    TRADING_DISABLED = "TRADING_DISABLED"
    DAILY_LIMIT_REACHED = "DAILY_LIMIT_REACHED"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    POSITION_SIZE_EXCEEDED = "POSITION_SIZE_EXCEEDED"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    STOP_LOSS_TRIGGERED = "STOP_LOSS_TRIGGERED"
    RISK_CHECK_FAILED = "RISK_CHECK_FAILED"


@dataclass
class OrderResult:
    """주문 실행 결과"""

    success: bool
    order: Order | None
    message: str
    blocked_reason: OrderBlockedReason | None = None


@dataclass
class BalanceInfo:
    """잔고 정보"""

    krw_available: Decimal
    krw_locked: Decimal
    xrp_available: Decimal
    xrp_locked: Decimal
    xrp_avg_price: Decimal
    total_krw: Decimal  # 총 평가금액


class OrderExecutor:
    """
    주문 실행 서비스

    AI 신호에 따라 리스크 체크 후 Upbit에 주문을 실행합니다.

    Attributes:
        _session: SQLAlchemy 비동기 세션
        _upbit_client: Upbit API 클라이언트
        _risk_manager: 리스크 관리 서비스
        _notifier: 알림 서비스 (선택)
    """

    def __init__(
        self,
        session: AsyncSession,
        upbit_client: UpbitClient,
        risk_manager: RiskManager,
        notifier: "Notifier | None" = None,
    ) -> None:
        """
        OrderExecutor 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            upbit_client: Upbit API 클라이언트
            risk_manager: 리스크 관리 서비스
            notifier: 알림 서비스 (선택)
        """
        self._session = session
        self._upbit_client = upbit_client
        self._risk_manager = risk_manager
        self._notifier = notifier

    # ==========================================================================
    # T059: 리스크 사전 체크가 포함된 주문 실행
    # ==========================================================================

    async def execute_from_signal(self, signal: TradingSignal) -> OrderResult:
        """
        AI 신호에 따른 주문 실행

        Args:
            signal: AI 매매 신호

        Returns:
            OrderResult: 실행 결과
        """
        logger.info(
            f"주문 실행 시작: signal_id={signal.id}, "
            f"type={signal.signal_type}, confidence={signal.confidence}"
        )

        # HOLD 신호는 주문 실행하지 않음
        if signal.signal_type == SignalType.HOLD.value:
            logger.info("HOLD 신호 - 주문 실행 건너뜀")
            return OrderResult(
                success=True,
                order=None,
                message="HOLD 신호 - 주문 없음",
            )

        # 1. 거래 활성화 상태 확인
        if not await self._risk_manager.is_trading_enabled():
            logger.warning("거래 비활성화 상태 - 주문 실행 불가")
            return OrderResult(
                success=False,
                order=None,
                message="거래가 비활성화되어 있습니다",
                blocked_reason=OrderBlockedReason.TRADING_DISABLED,
            )

        # 2. 일일 손실 한도 체크
        daily_result, daily_msg = await self._risk_manager.check_daily_loss_limit()
        if daily_result == RiskCheckResult.BLOCKED:
            logger.warning(f"일일 손실 한도 도달: {daily_msg}")
            return OrderResult(
                success=False,
                order=None,
                message=daily_msg,
                blocked_reason=OrderBlockedReason.DAILY_LIMIT_REACHED,
            )

        # 3. 변동성 체크
        vol_result, _vol_pct, vol_msg = await self._risk_manager.check_volatility()
        if vol_result == RiskCheckResult.BLOCKED:
            logger.warning(f"고변동성 감지: {vol_msg}")
            return OrderResult(
                success=False,
                order=None,
                message=vol_msg,
                blocked_reason=OrderBlockedReason.HIGH_VOLATILITY,
            )

        # 4. 잔고 조회 (T061)
        try:
            balance_info = await self._get_balance_info()
        except UpbitError as e:
            logger.error(f"잔고 조회 실패: {e.message}")
            return OrderResult(
                success=False,
                order=None,
                message=f"잔고 조회 실패: {e.message}",
            )

        # 5. 주문 방향에 따른 처리
        if signal.signal_type == SignalType.BUY.value:
            return await self._execute_buy_order(signal, balance_info)
        elif signal.signal_type == SignalType.SELL.value:
            return await self._execute_sell_order(signal, balance_info)

        return OrderResult(
            success=False,
            order=None,
            message=f"알 수 없는 신호 타입: {signal.signal_type}",
        )

    async def _execute_buy_order(
        self,
        signal: TradingSignal,
        balance_info: BalanceInfo,
    ) -> OrderResult:
        """매수 주문 실행"""
        logger.info("매수 주문 처리 시작")

        # 포지션 크기 계산 (총 자산의 N%)
        from src.config import settings

        position_pct = Decimal(str(settings.position_size_pct))
        order_amount = balance_info.total_krw * position_pct / Decimal("100")

        # 최소 주문 금액 확인
        if order_amount < MIN_ORDER_AMOUNT_KRW:
            logger.warning(
                f"주문 금액 부족: {order_amount:,.0f}원 < {MIN_ORDER_AMOUNT_KRW:,.0f}원"
            )
            return OrderResult(
                success=False,
                order=None,
                message=f"주문 금액 부족: {order_amount:,.0f}원",
                blocked_reason=OrderBlockedReason.INSUFFICIENT_BALANCE,
            )

        # 가용 잔고 확인
        if order_amount > balance_info.krw_available:
            order_amount = balance_info.krw_available
            logger.info(f"가용 잔고로 주문 금액 조정: {order_amount:,.0f}원")

        if order_amount < MIN_ORDER_AMOUNT_KRW:
            logger.warning(f"가용 잔고 부족: {balance_info.krw_available:,.0f}원")
            return OrderResult(
                success=False,
                order=None,
                message=f"가용 잔고 부족: {balance_info.krw_available:,.0f}원",
                blocked_reason=OrderBlockedReason.INSUFFICIENT_BALANCE,
            )

        # 포지션 크기 검증
        pos_result = await self._risk_manager.check_position_size(
            order_amount, balance_info.total_krw
        )
        if pos_result.result == RiskCheckResult.BLOCKED:
            logger.warning(f"포지션 크기 초과: {pos_result.message}")
            return OrderResult(
                success=False,
                order=None,
                message=pos_result.message,
                blocked_reason=OrderBlockedReason.POSITION_SIZE_EXCEEDED,
            )

        # 주문 실행 (T060: 재시도 로직)
        return await self._place_order_with_retry(
            side=OrderSide.BUY,
            amount=order_amount,
            signal_id=signal.id,
        )

    async def _execute_sell_order(
        self,
        signal: TradingSignal,
        balance_info: BalanceInfo,
    ) -> OrderResult:
        """매도 주문 실행"""
        logger.info("매도 주문 처리 시작")

        # 보유 XRP 확인
        if balance_info.xrp_available <= 0:
            logger.warning("보유 XRP 없음 - 매도 불가")
            return OrderResult(
                success=False,
                order=None,
                message="보유 XRP가 없습니다",
                blocked_reason=OrderBlockedReason.INSUFFICIENT_BALANCE,
            )

        # 현재 포지션 조회
        position = await self._get_position()
        if position is None:
            logger.warning("포지션 정보 없음")
            return OrderResult(
                success=False,
                order=None,
                message="포지션 정보가 없습니다",
            )

        # 현재가 조회
        try:
            ticker = await self._upbit_client.get_ticker(DEFAULT_MARKET)
            current_price = ticker.trade_price
        except UpbitError as e:
            logger.error(f"현재가 조회 실패: {e.message}")
            return OrderResult(
                success=False,
                order=None,
                message=f"현재가 조회 실패: {e.message}",
            )

        # 손절 체크
        stop_loss_result = await self._risk_manager.check_stop_loss(
            position, current_price
        )
        if stop_loss_result.result == RiskCheckResult.BLOCKED:
            logger.warning(f"손절 발동: {stop_loss_result.message}")
            # 손절 시에도 매도 진행 (should_close=True인 경우)
            if not stop_loss_result.should_close:
                return OrderResult(
                    success=False,
                    order=None,
                    message=stop_loss_result.message,
                    blocked_reason=OrderBlockedReason.STOP_LOSS_TRIGGERED,
                )

        # 전량 매도 (보유 XRP 전체)
        sell_volume = balance_info.xrp_available

        # 주문 실행 (T060: 재시도 로직)
        return await self._place_order_with_retry(
            side=OrderSide.SELL,
            amount=sell_volume,
            signal_id=signal.id,
        )

    # ==========================================================================
    # T060: 주문 재시도 로직
    # ==========================================================================

    async def _place_order_with_retry(
        self,
        side: OrderSide,
        amount: Decimal,
        signal_id: int | None = None,
    ) -> OrderResult:
        """
        재시도 로직이 포함된 주문 실행

        Args:
            side: 주문 방향 (BUY/SELL)
            amount: 주문 금액(매수) 또는 수량(매도)
            signal_id: 연관 신호 ID

        Returns:
            OrderResult: 실행 결과
        """
        order = await self._create_order_record(
            side=side,
            amount=amount,
            signal_id=signal_id,
        )

        logger.info(
            f"주문 생성: order_id={order.id}, side={side.value}, amount={amount}"
        )

        last_error: Exception | None = None

        for attempt in range(1, MAX_ORDER_RETRIES + 1):
            try:
                logger.info(f"주문 시도 {attempt}/{MAX_ORDER_RETRIES}")

                # Upbit 주문 실행
                if side == OrderSide.BUY:
                    # 시장가 매수: price에 총액 지정
                    upbit_response = await self._upbit_client.place_order(
                        market=DEFAULT_MARKET,
                        side="bid",
                        price=amount,
                        ord_type="price",  # 시장가 매수
                    )
                else:
                    # 시장가 매도: volume에 수량 지정
                    upbit_response = await self._upbit_client.place_order(
                        market=DEFAULT_MARKET,
                        side="ask",
                        volume=amount,
                        ord_type="market",  # 시장가 매도
                    )

                # 주문 성공
                order.upbit_uuid = upbit_response.uuid
                order.status = OrderStatus.PENDING.value

                logger.info(
                    f"주문 제출 성공: upbit_uuid={upbit_response.uuid}, "
                    f"state={upbit_response.state}"
                )

                # 주문 상태 확인 및 체결 정보 업데이트
                await self._update_order_status(order, upbit_response)

                # 시장가 주문이 대기 상태면 폴링하여 체결 확인
                if not order.is_executed and upbit_response.uuid:
                    await self._poll_order_completion(order, upbit_response.uuid)

                # T068: 포지션 업데이트 (순서 중요: 통계 먼저, 그 다음 포지션)
                if order.is_executed:
                    # 실현 손익은 포지션 변경 전에 계산해야 함
                    await self._update_daily_stats(order)
                    await self._update_position_after_order(order)

                    # 알림 전송
                    if self._notifier:
                        await self._send_order_notification(order)

                await self._session.commit()

                return OrderResult(
                    success=True,
                    order=order,
                    message=f"주문 체결 완료: {order.executed_amount}",
                )

            except UpbitError as e:
                last_error = e
                logger.warning(
                    f"주문 실패 (시도 {attempt}/{MAX_ORDER_RETRIES}): {e.message}"
                )

                # 클라이언트 오류 (4xx)는 재시도하지 않음
                if e.status_code and 400 <= e.status_code < 500:
                    order.mark_failed(e.message)
                    await self._session.commit()

                    logger.error(f"주문 실패 (클라이언트 오류): {e.message}")
                    return OrderResult(
                        success=False,
                        order=order,
                        message=f"주문 실패: {e.message}",
                    )

                # 재시도 대기
                if attempt < MAX_ORDER_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)

            except Exception as e:
                last_error = e
                logger.exception(f"주문 중 예외 발생: {e}")

                if attempt < MAX_ORDER_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)

        # 모든 재시도 실패
        error_msg = str(last_error) if last_error else "알 수 없는 오류"
        order.mark_failed(f"재시도 {MAX_ORDER_RETRIES}회 실패: {error_msg}")
        await self._session.commit()

        logger.error(f"주문 최종 실패: {error_msg}")
        return OrderResult(
            success=False,
            order=order,
            message=f"주문 실패: {error_msg}",
        )

    # ==========================================================================
    # T061: 잔고 검증
    # ==========================================================================

    async def _get_balance_info(self) -> BalanceInfo:
        """
        Upbit 계좌 잔고 조회

        Returns:
            BalanceInfo: 잔고 정보
        """
        accounts = await self._upbit_client.get_accounts()

        krw_available = Decimal("0")
        krw_locked = Decimal("0")
        xrp_available = Decimal("0")
        xrp_locked = Decimal("0")
        xrp_avg_price = Decimal("0")

        for acc in accounts:
            if acc.currency == "KRW":
                krw_available = acc.balance
                krw_locked = acc.locked
            elif acc.currency == "XRP":
                xrp_available = acc.balance
                xrp_locked = acc.locked
                xrp_avg_price = acc.avg_buy_price

        # 현재가 조회
        try:
            ticker = await self._upbit_client.get_ticker(DEFAULT_MARKET)
            current_price = ticker.trade_price
        except UpbitError:
            current_price = xrp_avg_price  # 조회 실패 시 평균 매수가 사용

        # 총 평가금액 계산
        xrp_value = (xrp_available + xrp_locked) * current_price
        total_krw = krw_available + krw_locked + xrp_value

        return BalanceInfo(
            krw_available=krw_available,
            krw_locked=krw_locked,
            xrp_available=xrp_available,
            xrp_locked=xrp_locked,
            xrp_avg_price=xrp_avg_price,
            total_krw=total_krw,
        )

    # ==========================================================================
    # T068: 포지션 업데이트
    # ==========================================================================

    async def _update_position_after_order(self, order: Order) -> None:
        """
        주문 체결 후 포지션 업데이트

        Args:
            order: 체결된 주문
        """
        position = await self._get_position()

        if position is None:
            # 포지션 생성
            position = Position(
                symbol=DEFAULT_MARKET,
                quantity=Decimal("0"),
                avg_buy_price=Decimal("0"),
                current_value=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                updated_at=datetime.now(UTC),
            )
            self._session.add(position)

        if order.is_buy:
            # 매수: 수량 증가, 평균 매수가 재계산
            if order.executed_amount and order.executed_price:
                # 시장가 매수의 경우 executed_amount는 KRW, 실제 XRP 수량 계산 필요
                xrp_quantity = order.executed_amount / order.executed_price
                new_quantity = position.quantity + xrp_quantity

                if new_quantity > 0:
                    # 가중 평균 매수가 계산
                    old_cost = position.quantity * position.avg_buy_price
                    new_cost = order.executed_amount
                    position.avg_buy_price = (old_cost + new_cost) / new_quantity

                position.quantity = new_quantity

        elif order.is_sell:
            # 매도: 수량 감소 (평균 매수가는 유지)
            if order.executed_amount:
                position.quantity = max(
                    Decimal("0"), position.quantity - order.executed_amount
                )

                # 수량이 0이면 평균 매수가 초기화
                if position.quantity == 0:
                    position.avg_buy_price = Decimal("0")

        # 현재가로 평가금액 업데이트
        try:
            ticker = await self._upbit_client.get_ticker(DEFAULT_MARKET)
            position.update_value(ticker.trade_price)
        except UpbitError:
            pass

        position.updated_at = datetime.now(UTC)

        logger.info(
            f"포지션 업데이트: quantity={position.quantity}, "
            f"avg_price={position.avg_buy_price}, pnl={position.unrealized_pnl}"
        )

    async def _update_daily_stats(self, order: Order) -> None:
        """
        일일 통계 업데이트

        Args:
            order: 체결된 주문
        """
        today = date.today()
        stmt = select(DailyStats).where(DailyStats.date == today)
        result = await self._session.execute(stmt)
        daily_stats = result.scalar_one_or_none()

        if daily_stats is None:
            # 오늘 통계 생성
            balance_info = await self._get_balance_info()
            daily_stats = DailyStats(
                date=today,
                starting_balance=balance_info.total_krw,
                ending_balance=balance_info.total_krw,
                realized_pnl=Decimal("0"),
                trade_count=0,
                win_count=0,
                loss_count=0,
                is_trading_halted=False,
                halt_reason=None,
            )
            self._session.add(daily_stats)

        # 거래 횟수 증가
        daily_stats.trade_count += 1

        # 매도 완료 시 실현 손익 계산 (간단한 방식)
        if order.is_sell and order.executed_amount and order.executed_price:
            position = await self._get_position()
            if position and position.avg_buy_price > 0:
                # 실현 손익 = (체결가 - 평균매수가) * 체결수량
                pnl = (
                    order.executed_price - position.avg_buy_price
                ) * order.executed_amount
                daily_stats.realized_pnl += pnl

                if pnl >= 0:
                    daily_stats.win_count += 1
                else:
                    daily_stats.loss_count += 1

        # 잔고 업데이트
        try:
            balance_info = await self._get_balance_info()
            daily_stats.ending_balance = balance_info.total_krw
        except UpbitError:
            pass

        logger.info(
            f"일일 통계 업데이트: trade_count={daily_stats.trade_count}, "
            f"realized_pnl={daily_stats.realized_pnl}"
        )

    # ==========================================================================
    # T069: 주문 생명주기 로깅
    # ==========================================================================

    async def _create_order_record(
        self,
        side: OrderSide,
        amount: Decimal,
        signal_id: int | None = None,
        order_type: OrderType = OrderType.MARKET,
        price: Decimal | None = None,
    ) -> Order:
        """주문 레코드 생성"""
        order = Order(
            signal_id=signal_id,
            order_type=order_type.value,
            side=side.value,
            market=DEFAULT_MARKET,
            amount=amount,
            price=price,
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(UTC),
        )
        self._session.add(order)
        await self._session.flush()  # ID 생성

        logger.info(
            f"[주문 생성] order_id={order.id}, side={side.value}, "
            f"amount={amount}, signal_id={signal_id}"
        )

        return order

    async def _update_order_status(self, order: Order, upbit_response) -> None:
        """Upbit 응답으로 주문 상태 업데이트"""
        # 체결 상태 확인
        if upbit_response.state == "done":
            order.mark_executed(
                executed_price=upbit_response.price or Decimal("0"),
                executed_amount=upbit_response.executed_volume,
                fee=upbit_response.executed_volume * UPBIT_FEE_RATE,
            )

            logger.info(
                f"[주문 체결] order_id={order.id}, "
                f"upbit_uuid={order.upbit_uuid}, "
                f"executed_price={order.executed_price}, "
                f"executed_amount={order.executed_amount}, "
                f"fee={order.fee}"
            )

        elif upbit_response.state == "cancel":
            order.mark_cancelled()
            logger.info(f"[주문 취소] order_id={order.id}")

        elif upbit_response.state == "wait":
            # 대기 상태 - 체결 완료 대기
            order.status = OrderStatus.PENDING.value
            logger.info(f"[주문 대기] order_id={order.id}, state=wait")

    async def _poll_order_completion(self, order: Order, uuid: str) -> None:
        """
        주문 체결 상태 폴링

        시장가 주문이 대기 상태일 때 체결될 때까지 폴링합니다.

        Args:
            order: 주문 객체
            uuid: Upbit 주문 UUID
        """
        for attempt in range(ORDER_POLL_MAX_ATTEMPTS):
            await asyncio.sleep(ORDER_POLL_INTERVAL)

            try:
                upbit_response = await self._upbit_client.get_order(uuid)

                logger.debug(
                    f"[주문 상태 확인] attempt={attempt + 1}, "
                    f"uuid={uuid}, state={upbit_response.state}"
                )

                if upbit_response.state == "done":
                    # 체결 완료
                    order.mark_executed(
                        executed_price=upbit_response.price or Decimal("0"),
                        executed_amount=upbit_response.executed_volume,
                        fee=upbit_response.executed_volume * UPBIT_FEE_RATE,
                    )
                    logger.info(
                        f"[주문 체결 확인] order_id={order.id}, "
                        f"executed_price={order.executed_price}, "
                        f"executed_amount={order.executed_amount}"
                    )
                    return

                elif upbit_response.state == "cancel":
                    order.mark_cancelled()
                    logger.warning(f"[주문 취소됨] order_id={order.id}")
                    return

                # state == "wait" 계속 폴링

            except UpbitError as e:
                logger.warning(f"주문 상태 조회 실패: {e.message}")
                continue

        # 최대 시도 횟수 초과
        logger.warning(
            f"주문 체결 확인 타임아웃: order_id={order.id}, uuid={uuid}, "
            f"attempts={ORDER_POLL_MAX_ATTEMPTS}"
        )

    async def _send_order_notification(self, order: Order) -> None:
        """주문 체결 알림 전송"""
        if not self._notifier:
            return

        side_text = "매수" if order.is_buy else "매도"
        await self._notifier.send_alert(
            title=f"✅ {side_text} 주문 체결",
            message=(
                f"금액: {order.executed_amount:,.0f}\n"
                f"가격: {order.executed_price:,.0f}원\n"
                f"수수료: {order.fee:,.0f}원"
            ),
        )

    # ==========================================================================
    # 주문 조회
    # ==========================================================================

    async def get_orders(
        self,
        status: OrderStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Order], int]:
        """
        주문 목록 조회

        Args:
            status: 상태 필터 (선택)
            limit: 조회 개수
            offset: 시작 위치

        Returns:
            tuple[list[Order], int]: (주문 목록, 총 개수)
        """
        # 총 개수 조회
        count_stmt = select(func.count(Order.id))
        if status:
            count_stmt = count_stmt.where(Order.status == status.value)
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # 주문 목록 조회
        stmt = (
            select(Order).order_by(Order.created_at.desc()).limit(limit).offset(offset)
        )
        if status:
            stmt = stmt.where(Order.status == status.value)

        result = await self._session.execute(stmt)
        orders = list(result.scalars().all())

        return orders, total

    async def get_order_by_id(self, order_id: int) -> Order | None:
        """주문 상세 조회"""
        stmt = select(Order).where(Order.id == order_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_position(self) -> Position | None:
        """현재 포지션 조회"""
        stmt = select(Position).where(Position.symbol == DEFAULT_MARKET)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ==========================================================================
    # Upbit 잔고와 Position 동기화
    # ==========================================================================

    async def sync_position_from_upbit(self) -> Position | None:
        """
        Upbit 실제 잔고와 Position 테이블 동기화

        Upbit API에서 실제 XRP 잔고를 조회하여 Position 테이블에 반영합니다.
        외부에서 직접 거래한 내역도 Position에 반영됩니다.

        Returns:
            Position | None: 동기화된 포지션 (XRP가 없으면 None)
        """
        try:
            balance_info = await self._get_balance_info()
        except UpbitError as e:
            logger.warning(f"포지션 동기화 실패 - 잔고 조회 오류: {e.message}")
            return None

        # XRP 보유량이 없으면 포지션 삭제 또는 0으로 설정
        position = await self._get_position()

        if balance_info.xrp_available <= 0 and balance_info.xrp_locked <= 0:
            if position:
                position.quantity = Decimal("0")
                position.current_value = Decimal("0")
                position.unrealized_pnl = Decimal("0")
                position.updated_at = datetime.now(UTC)
                logger.info("포지션 동기화: XRP 보유량 없음 - 포지션 초기화")
            return position

        # 포지션이 없으면 새로 생성
        if position is None:
            position = Position(
                symbol=DEFAULT_MARKET,
                quantity=Decimal("0"),
                avg_buy_price=Decimal("0"),
                current_value=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                updated_at=datetime.now(UTC),
            )
            self._session.add(position)

        # Upbit 잔고로 포지션 업데이트
        total_xrp = balance_info.xrp_available + balance_info.xrp_locked
        position.quantity = total_xrp
        position.avg_buy_price = balance_info.xrp_avg_price

        # 현재가로 평가금액 및 손익 계산
        try:
            ticker = await self._upbit_client.get_ticker(DEFAULT_MARKET)
            position.update_value(ticker.trade_price)
        except UpbitError:
            # 현재가 조회 실패 시 평균 매수가로 계산
            position.current_value = total_xrp * balance_info.xrp_avg_price
            position.unrealized_pnl = Decimal("0")

        position.updated_at = datetime.now(UTC)
        await self._session.flush()

        logger.info(
            f"포지션 동기화 완료: quantity={position.quantity:.4f} XRP, "
            f"avg_price={position.avg_buy_price:,.0f}, "
            f"unrealized_pnl={position.unrealized_pnl:,.0f}"
        )

        return position

    async def get_balance_info(self) -> BalanceInfo:
        """
        Upbit 계좌 잔고 조회 (public 접근용)

        Returns:
            BalanceInfo: 잔고 정보
        """
        return await self._get_balance_info()


async def get_order_executor(
    session: AsyncSession,
    upbit_client: UpbitClient | None = None,
    risk_manager: RiskManager | None = None,
    notifier: "Notifier | None" = None,
) -> OrderExecutor:
    """
    OrderExecutor 인스턴스 반환

    Args:
        session: SQLAlchemy 비동기 세션
        upbit_client: Upbit API 클라이언트 (기본: 싱글톤)
        risk_manager: 리스크 관리 서비스 (기본: 새 인스턴스)
        notifier: 알림 서비스 (선택)

    Returns:
        OrderExecutor: 주문 실행 서비스
    """
    from src.services.risk_manager import RiskManager
    from src.services.upbit_client import get_upbit_client

    if upbit_client is None:
        upbit_client = get_upbit_client()

    if risk_manager is None:
        risk_manager = RiskManager(session, notifier)

    return OrderExecutor(session, upbit_client, risk_manager, notifier)
