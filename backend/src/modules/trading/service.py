"""
거래 서비스 모듈

이 모듈은 AI 신호에 따른 자동 주문 실행을 담당합니다.
- 리스크 사전 체크
- 주문 재시도 로직
- 잔고 검증
- 포지션 업데이트
- 주문 생명주기 로깅
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import (
    UpbitPrivateAPI,
    UpbitPrivateAPIError,
    UpbitPublicAPI,
    UpbitPublicAPIError,
)
from src.config import settings
from src.config.constants import ORDER_MAX_RETRIES, ORDER_RETRY_DELAY_SECONDS
from src.entities import (
    AdjustmentType,
    BalanceAdjustment,
    DailyStats,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    SignalType,
    TradingSignal,
)
from src.modules.risk.service import RiskService
from src.modules.trading.monitor import OrderMonitor
from src.modules.trading.position import PositionManager
from src.modules.trading.validator import (
    BalanceInfo,
    OrderBlockedReason,
    OrderValidator,
)
from src.utils import UTC

if TYPE_CHECKING:
    from src.modules.notification import Notifier


class TradingServiceError(Exception):
    """거래 서비스 오류"""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


@dataclass
class OrderResult:
    """주문 실행 결과"""

    success: bool
    order: Order | None
    message: str
    blocked_reason: OrderBlockedReason | None = None


class TradingService:
    """
    거래 서비스

    AI 신호에 따라 리스크 체크 후 Upbit에 주문을 실행합니다.

    Attributes:
        _session: SQLAlchemy 비동기 세션
        _upbit_client: Upbit API 클라이언트
        _validator: 주문 검증기
        _monitor: 주문 모니터
        _risk_service: 리스크 관리 서비스
        _notifier: 알림 서비스 (선택)
    """

    def __init__(
        self,
        session: AsyncSession,
        private_api: UpbitPrivateAPI,
        public_api: UpbitPublicAPI,
        risk_service: RiskService,
        user_id: int,
        notifier: "Notifier | None" = None,
    ) -> None:
        """
        TradingService 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            private_api: Upbit Private API 클라이언트
            public_api: Upbit Public API 클라이언트
            risk_service: 리스크 관리 서비스
            user_id: 거래 소유자 ID
            notifier: 알림 서비스 (선택)
        """
        self._session = session
        self._private_api = private_api
        self._public_api = public_api
        self._risk_service = risk_service
        self._user_id = user_id
        self._notifier = notifier

        # 검증기, 모니터, 포지션 관리자 초기화
        self._validator = OrderValidator(private_api, public_api, risk_service)
        self._monitor = OrderMonitor(session, private_api)
        self._position_manager = PositionManager(
            session, public_api, self._validator, user_id
        )

    async def execute_from_signal(
        self,
        signal: TradingSignal,
        user_id: int | None = None,
    ) -> OrderResult:
        """
        AI 신호에 따른 주문 실행

        Args:
            signal: AI 매매 신호
            user_id: 주문 생성자 ID (기본값: signal.user_id)

        Returns:
            OrderResult: 실행 결과
        """
        # user_id가 없으면 signal.user_id 사용
        order_user_id = user_id or signal.user_id
        logger.info(
            f"주문 실행 시작: signal_id={signal.id}, "
            f"type={signal.signal_type}, confidence={signal.confidence}"
        )

        # 1. 신호 검증 (리스크 체크 포함)
        validation_result, balance_info = await self._validator.validate_signal(signal)

        # HOLD 신호 또는 검증 통과
        if signal.signal_type == SignalType.HOLD.value:
            return OrderResult(
                success=True,
                order=None,
                message="HOLD 신호 - 주문 없음",
            )

        if not validation_result.is_valid:
            return OrderResult(
                success=False,
                order=None,
                message=validation_result.message,
                blocked_reason=validation_result.blocked_reason,
            )

        # 2. 주문 방향에 따른 처리
        if signal.signal_type == SignalType.BUY.value:
            return await self._execute_buy_order(signal, balance_info, order_user_id)
        elif signal.signal_type == SignalType.SELL.value:
            return await self._execute_sell_order(signal, balance_info, order_user_id)

        return OrderResult(
            success=False,
            order=None,
            message=f"알 수 없는 신호 타입: {signal.signal_type}",
        )

    async def _execute_buy_order(
        self,
        signal: TradingSignal,
        balance_info: BalanceInfo,
        user_id: int | None = None,
    ) -> OrderResult:
        """매수 주문 실행"""
        logger.info("매수 주문 처리 시작")

        # 매수 주문 검증
        buy_validation = await self._validator.validate_buy_order(signal, balance_info)
        if not buy_validation.is_valid:
            return OrderResult(
                success=False,
                order=None,
                message=buy_validation.message,
                blocked_reason=buy_validation.blocked_reason,
            )

        # 주문 실행
        return await self._place_order_with_retry(
            side=OrderSide.BUY,
            amount=buy_validation.order_amount,
            signal_id=signal.id,
            user_id=user_id,
        )

    async def _execute_sell_order(
        self,
        signal: TradingSignal,
        balance_info: BalanceInfo,
        user_id: int | None = None,
    ) -> OrderResult:
        """매도 주문 실행"""
        logger.info("매도 주문 처리 시작")

        # 포지션 조회
        position = await self._get_position()

        # 매도 주문 검증
        sell_validation = await self._validator.validate_sell_order(
            signal, balance_info, position
        )
        if not sell_validation.is_valid:
            return OrderResult(
                success=False,
                order=None,
                message=sell_validation.message,
                blocked_reason=sell_validation.blocked_reason,
            )

        # 전량 매도
        sell_volume = balance_info.coin_available

        # 주문 실행
        return await self._place_order_with_retry(
            side=OrderSide.SELL,
            amount=sell_volume,
            signal_id=signal.id,
            user_id=user_id,
        )

    async def _place_order_with_retry(
        self,
        side: OrderSide,
        amount: Decimal,
        signal_id: int | None = None,
        user_id: int | None = None,
    ) -> OrderResult:
        """
        재시도 로직이 포함된 주문 실행 (중복 주문 방지 포함)

        Args:
            side: 주문 방향 (BUY/SELL)
            amount: 주문 금액(매수) 또는 수량(매도)
            signal_id: 연관 신호 ID
            user_id: 주문 생성자 ID

        Returns:
            OrderResult: 실행 결과
        """
        # 중복 주문 방지를 위한 idempotency key 생성
        idempotency_key = str(uuid.uuid4())
        order: Order | None = None
        last_error: Exception | None = None

        for attempt in range(1, ORDER_MAX_RETRIES + 1):
            try:
                logger.info(f"주문 시도 {attempt}/{ORDER_MAX_RETRIES}")

                # 재시도 시: 기존 주문 상태 확인
                if await self._monitor.check_and_update_existing_order(order):
                    break  # 이미 주문이 있으므로 새 주문 안 함

                # Upbit 주문 실행
                if side == OrderSide.BUY:
                    upbit_response = await self._private_api.place_order(
                        market=settings.trading_ticker,
                        side="bid",
                        price=amount,
                        ord_type="price",
                    )
                else:
                    upbit_response = await self._private_api.place_order(
                        market=settings.trading_ticker,
                        side="ask",
                        volume=amount,
                        ord_type="market",
                    )

                # API 성공 후에만 Order 레코드 생성 (첫 시도 시)
                if order is None:
                    order = await self._create_order_record(
                        side=side,
                        amount=amount,
                        signal_id=signal_id,
                        user_id=user_id,
                        idempotency_key=idempotency_key,
                    )
                    logger.info(
                        f"주문 생성: order_id={order.id}, side={side.value}, "
                        f"amount={amount}, idempotency_key={idempotency_key}"
                    )

                # 주문 성공
                order.upbit_uuid = upbit_response.uuid
                order.status = OrderStatus.PENDING.value

                logger.info(
                    f"주문 제출 성공: upbit_uuid={upbit_response.uuid}, "
                    f"state={upbit_response.state}"
                )

                # 주문 상태 확인 및 체결 정보 업데이트
                await self._monitor.update_order_status(order, upbit_response)

                # 시장가 주문이 대기 상태면 폴링하여 체결 확인
                if not order.is_executed and upbit_response.uuid:
                    await self._monitor.poll_order_completion(
                        order, upbit_response.uuid
                    )

                break  # 성공 시 루프 종료

            except (UpbitPrivateAPIError, UpbitPublicAPIError) as e:
                last_error = e
                logger.warning(
                    f"주문 실패 (시도 {attempt}/{ORDER_MAX_RETRIES}): {e.message}"
                )

                # 클라이언트 오류 (4xx)는 재시도하지 않음
                if e.status_code and 400 <= e.status_code < 500:
                    if order is None:
                        order = await self._create_order_record(
                            side=side,
                            amount=amount,
                            signal_id=signal_id,
                            user_id=user_id,
                            idempotency_key=idempotency_key,
                        )
                    order.mark_failed(e.message)
                    await self._session.commit()

                    logger.error(f"주문 실패 (클라이언트 오류): {e.message}")
                    return OrderResult(
                        success=False,
                        order=order,
                        message=f"주문 실패: {e.message}",
                    )

                # 재시도 대기
                if attempt < ORDER_MAX_RETRIES:
                    await asyncio.sleep(ORDER_RETRY_DELAY_SECONDS * attempt)

            except Exception as e:
                last_error = e
                logger.exception(f"주문 중 예외 발생: {e}")

                if attempt < ORDER_MAX_RETRIES:
                    await asyncio.sleep(ORDER_RETRY_DELAY_SECONDS * attempt)

        # 루프 종료 후 처리
        if order is None:
            # Order 생성조차 못 한 경우 (모든 시도 실패)
            order = await self._create_order_record(
                side=side,
                amount=amount,
                signal_id=signal_id,
                user_id=user_id,
                idempotency_key=idempotency_key,
            )
            error_msg = str(last_error) if last_error else "알 수 없는 오류"
            order.mark_failed(f"재시도 {ORDER_MAX_RETRIES}회 실패: {error_msg}")
            await self._session.commit()
            logger.error(f"주문 최종 실패: {error_msg}")
            return OrderResult(
                success=False,
                order=order,
                message=f"주문 실패: {error_msg}",
            )

        # 포지션 업데이트 (체결 시에만)
        if order.is_executed:
            await self._update_daily_stats(order)
            await self._update_position_after_order(order)
            if self._notifier:
                await self._send_order_notification(order)

        await self._session.commit()

        if order.is_executed:
            return OrderResult(
                success=True,
                order=order,
                message=f"주문 체결 완료: {order.executed_amount}",
            )
        elif order.is_failed:
            return OrderResult(
                success=False,
                order=order,
                message=f"주문 실패: {order.error_message}",
            )
        else:
            # PENDING 상태로 종료 (타임아웃)
            logger.warning(f"주문 체결 타임아웃: order_id={order.id}")
            return OrderResult(
                success=False,
                order=order,
                message="주문 체결 타임아웃 - 나중에 동기화 필요",
            )

    async def _create_order_record(
        self,
        side: OrderSide,
        amount: Decimal,
        signal_id: int | None = None,
        user_id: int | None = None,
        order_type: OrderType = OrderType.MARKET,
        price: Decimal | None = None,
        idempotency_key: str | None = None,
    ) -> Order:
        """주문 레코드 생성"""
        # user_id가 없으면 시스템 기본 사용자 ID 사용 (스케줄러 자동 주문)
        effective_user_id = user_id or 1

        # 매도 주문 시 현재 평균 매수가 저장 (손익 계산용)
        avg_cost_at_order: Decimal | None = None
        if side == OrderSide.SELL:
            position = await self._get_position()
            if position and position.avg_buy_price > 0:
                avg_cost_at_order = position.avg_buy_price
                logger.info(
                    f"[매도 주문] 평균 매수가 스냅샷 저장: {avg_cost_at_order:,.2f}"
                )

        order = Order(
            user_id=effective_user_id,
            signal_id=signal_id,
            order_type=order_type.value,
            side=side.value,
            market=settings.trading_ticker,
            amount=amount,
            price=price,
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(UTC),
            idempotency_key=idempotency_key,
            avg_cost_at_order=avg_cost_at_order,
        )
        self._session.add(order)
        await self._session.flush()  # ID 생성

        logger.info(
            f"[주문 생성] order_id={order.id}, side={side.value}, "
            f"amount={amount}, signal_id={signal_id}, "
            f"idempotency_key={idempotency_key}"
        )

        return order

    async def _update_position_after_order(self, order: Order) -> None:
        """주문 체결 후 포지션 업데이트 (PositionManager에 위임)"""
        await self._position_manager.update_position_after_order(order)

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
            balance_info = await self._validator.get_balance_info()
            current_balance = balance_info.total_krw

            # 전일 DailyStats 조회하여 입금/출금 감지
            yesterday = today - timedelta(days=1)
            prev_stmt = select(DailyStats).where(DailyStats.date == yesterday)
            prev_result = await self._session.execute(prev_stmt)
            prev_stats = prev_result.scalar_one_or_none()

            if prev_stats:
                await self._detect_balance_adjustment(
                    prev_stats.ending_balance,
                    current_balance,
                    today,
                )

            daily_stats = DailyStats(
                user_id=order.user_id,
                date=today,
                starting_balance=current_balance,
                ending_balance=current_balance,
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

        # 매도 완료 시 실현 손익 계산
        # 주문 생성 시 저장한 avg_cost_at_order 사용 (포지션 변경 전 값)
        if order.is_sell and order.executed_amount and order.executed_price:
            avg_cost = order.avg_cost_at_order
            if avg_cost and avg_cost > 0:
                # 실현 손익 = (체결가 - 주문시점 평균매수가) * 체결수량
                pnl = (order.executed_price - avg_cost) * order.executed_amount
                daily_stats.realized_pnl += pnl

                if pnl >= 0:
                    daily_stats.win_count += 1
                else:
                    daily_stats.loss_count += 1

                logger.info(
                    f"실현 손익 계산: 체결가={order.executed_price:,.0f}, "
                    f"평균매수가={avg_cost:,.0f}, 수량={order.executed_amount}, "
                    f"손익={pnl:,.0f}"
                )
            else:
                logger.warning(
                    f"매도 손익 계산 불가: avg_cost_at_order가 없음 (order_id={order.id})"
                )

        # 잔고 업데이트
        try:
            balance_info = await self._validator.get_balance_info()
            daily_stats.ending_balance = balance_info.total_krw
        except (UpbitPrivateAPIError, UpbitPublicAPIError):
            pass

        logger.info(
            f"일일 통계 업데이트: trade_count={daily_stats.trade_count}, "
            f"realized_pnl={daily_stats.realized_pnl}"
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
        """현재 포지션 조회 (PositionManager에 위임)"""
        return await self._position_manager.get_position()

    async def _detect_balance_adjustment(
        self,
        prev_ending_balance: Decimal,
        current_balance: Decimal,
        target_date: date,
    ) -> BalanceAdjustment | None:
        """
        잔고 변화에서 입금/출금 감지 및 기록

        Args:
            prev_ending_balance: 전일 종료 잔고
            current_balance: 현재 잔고
            target_date: 조정 날짜

        Returns:
            BalanceAdjustment | None: 감지된 조정 내역 (없으면 None)
        """
        # 입금/출금 감지 임계값 (원)
        ADJUSTMENT_THRESHOLD = Decimal("1000")

        # 잔고 차이 계산
        diff = current_balance - prev_ending_balance

        # 임계값 미만 차이는 무시
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
        existing_result = await self._session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            logger.debug(f"이미 기록된 조정: {target_date}, {diff:,.0f}원")
            return None

        # 새 조정 기록
        adjustment = BalanceAdjustment(
            date=target_date,
            amount=diff,
            adjustment_type=adj_type.value,
            balance_before=prev_ending_balance,
            balance_after=current_balance,
            notes=f"자동 감지 ({adj_type.value})",
        )
        self._session.add(adjustment)

        logger.info(
            f"잔고 조정 기록: {adj_type.value} {diff:,.0f}원 "
            f"({prev_ending_balance:,.0f} → {current_balance:,.0f})"
        )

        return adjustment

    async def sync_position_from_upbit(self) -> Position | None:
        """Upbit 실제 잔고와 Position 테이블 동기화 (PositionManager에 위임)"""
        return await self._position_manager.sync_position_from_upbit()

    async def sync_pending_orders(self) -> int:
        """
        PENDING 상태의 주문을 Upbit와 동기화

        Returns:
            int: 동기화된 주문 수
        """
        synced_count = await self._monitor.sync_pending_orders()

        # 포지션 및 일일 통계 업데이트 (동기화된 주문 처리)
        # sync_pending_orders에서 이미 commit 했으므로 여기서는 별도 처리 없음

        return synced_count

    async def get_balance_info(self) -> BalanceInfo:
        """Upbit 계좌 잔고 조회 (PositionManager에 위임)"""
        return await self._position_manager.get_balance_info()


async def get_trading_service(
    session: AsyncSession,
    user_id: int | None = None,
    private_api: UpbitPrivateAPI | None = None,
    public_api: UpbitPublicAPI | None = None,
    risk_service: RiskService | None = None,
    notifier: "Notifier | None" = None,
) -> TradingService:
    """
    TradingService 인스턴스 반환

    Args:
        session: SQLAlchemy 비동기 세션
        user_id: 거래 소유자 ID (기본: 첫 번째 사용자)
        private_api: Upbit Private API 클라이언트 (기본: 싱글톤)
        public_api: Upbit Public API 클라이언트 (기본: 싱글톤)
        risk_service: 리스크 관리 서비스 (기본: 새 인스턴스)
        notifier: 알림 서비스 (선택)

    Returns:
        TradingService: 거래 서비스
    """
    from src.clients.upbit import get_upbit_private_api, get_upbit_public_api
    from src.entities import User
    from src.modules.risk.service import get_risk_service

    if private_api is None:
        private_api = get_upbit_private_api()

    if public_api is None:
        public_api = get_upbit_public_api()

    if risk_service is None:
        risk_service = get_risk_service(session)

    # user_id가 없으면 첫 번째 사용자 조회
    if user_id is None:
        result = await session.execute(select(User.id).order_by(User.id).limit(1))
        user_id = result.scalar_one_or_none()
        if user_id is None:
            raise TradingServiceError("등록된 사용자가 없습니다", code="NO_USER")

    return TradingService(
        session, private_api, public_api, risk_service, user_id, notifier
    )
