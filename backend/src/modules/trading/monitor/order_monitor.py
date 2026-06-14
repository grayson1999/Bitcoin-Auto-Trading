"""
주문 모니터링 모듈

이 모듈은 주문 상태 추적 및 동기화를 담당합니다.
- 주문 상태 폴링
- PENDING 주문 동기화
- 체결 확인 및 업데이트
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import UpbitPrivateAPI, UpbitPrivateAPIError
from src.config.constants import (
    ORDER_POLL_INTERVAL_SECONDS,
    ORDER_POLL_MAX_ATTEMPTS,
    UPBIT_FEE_RATE,
)
from src.entities import Order, OrderStatus
from src.utils import UTC

# 상수를 Decimal로 변환
_UPBIT_FEE_RATE = Decimal(str(UPBIT_FEE_RATE))


class OrderMonitor:
    """
    주문 모니터링 서비스

    Upbit API를 통해 주문 상태를 추적하고 동기화합니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        private_api: UpbitPrivateAPI,
    ) -> None:
        """
        OrderMonitor 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            private_api: Upbit Private API 클라이언트
        """
        self._session = session
        self._private_api = private_api

    def calculate_executed_price(self, order: Order, upbit_response) -> Decimal:
        """
        체결가 계산 헬퍼

        우선순위:
        1. avg_price (평균 체결가)
        2. executed_funds / executed_volume (총 체결금액 / 총 체결수량)
        3. trades 배열에서 가중 평균 계산
        4. price 필드 (지정가 주문)

        Args:
            order: 주문 객체
            upbit_response: Upbit 주문 응답

        Returns:
            Decimal: 계산된 체결가
        """
        # 1. avg_price 우선 사용 (0보다 커야 유효)
        if upbit_response.avg_price and upbit_response.avg_price > 0:
            return upbit_response.avg_price

        # 2. executed_funds / executed_volume 계산
        if (
            upbit_response.executed_funds
            and upbit_response.executed_volume
            and upbit_response.executed_volume > 0
        ):
            return upbit_response.executed_funds / upbit_response.executed_volume

        # 3. trades 배열에서 가중 평균 계산
        if upbit_response.trades:
            total_funds = sum(t.funds for t in upbit_response.trades)
            total_volume = sum(t.volume for t in upbit_response.trades)
            if total_volume > 0:
                avg_price = total_funds / total_volume
                logger.info(
                    f"[체결가 계산] trades에서 계산: order_id={order.id}, "
                    f"avg_price={avg_price}"
                )
                return avg_price

        # 4. fallback: price 필드 (지정가 주문에서 사용)
        if upbit_response.price and upbit_response.price > 0:
            return upbit_response.price

        # 모든 방법 실패 시 경고
        logger.warning(
            f"[체결가 계산] avg_price/executed_funds/trades/price 모두 없음, "
            f"order_id={order.id}, trades_count={len(upbit_response.trades)}"
        )
        return Decimal("0")

    async def update_order_status(self, order: Order, upbit_response) -> None:
        """
        Upbit 응답으로 주문 상태 업데이트

        Args:
            order: 주문 객체
            upbit_response: Upbit API 응답
        """
        # 체결 상태 확인
        if upbit_response.state == "done":
            # 시장가 매수는 첫 응답에 executed_volume이 없을 수 있음 → 폴링 필요
            if upbit_response.executed_volume is None:
                order.status = OrderStatus.PENDING.value
                logger.info(
                    f"[주문 체결 대기] order_id={order.id}, 체결 정보 폴링 필요"
                )
                return

            executed_price = self.calculate_executed_price(order, upbit_response)
            executed_volume = upbit_response.executed_volume
            # 수수료 = 체결금액 * 수수료율 (KRW 기준)
            total_value = executed_volume * executed_price
            fee = total_value * _UPBIT_FEE_RATE

            order.mark_executed(
                executed_price=executed_price,
                executed_amount=executed_volume,
                fee=fee,
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

    async def poll_order_completion(self, order: Order, uuid: str) -> None:
        """
        주문 체결 상태 폴링

        시장가 주문이 대기 상태일 때 체결될 때까지 폴링합니다.

        Args:
            order: 주문 객체
            uuid: Upbit 주문 UUID
        """
        for attempt in range(ORDER_POLL_MAX_ATTEMPTS):
            await asyncio.sleep(ORDER_POLL_INTERVAL_SECONDS)

            try:
                upbit_response = await self._private_api.get_order(uuid)

                logger.debug(
                    f"[주문 상태 확인] attempt={attempt + 1}, "
                    f"uuid={uuid}, state={upbit_response.state}"
                )

                if upbit_response.state == "done":
                    # 체결 정보가 없으면 계속 폴링
                    if upbit_response.executed_volume is None:
                        logger.debug("[주문 상태] done이지만 체결 정보 없음, 계속 폴링")
                        continue

                    # 체결 완료 - calculate_executed_price 사용
                    executed_price = self.calculate_executed_price(
                        order, upbit_response
                    )
                    executed_volume = upbit_response.executed_volume
                    # 수수료 = 체결금액 * 수수료율 (KRW 기준)
                    total_value = executed_volume * executed_price
                    fee = total_value * _UPBIT_FEE_RATE

                    order.mark_executed(
                        executed_price=executed_price,
                        executed_amount=executed_volume,
                        fee=fee,
                    )
                    logger.info(
                        f"[주문 체결 확인] order_id={order.id}, "
                        f"executed_price={order.executed_price}, "
                        f"executed_amount={order.executed_amount}"
                    )
                    return

                elif upbit_response.state == "cancel":
                    # 부분 체결 후 취소된 경우 (시장가 매수에서 자주 발생)
                    if (
                        upbit_response.executed_volume
                        and upbit_response.executed_volume > 0
                    ):
                        executed_price = self.calculate_executed_price(
                            order, upbit_response
                        )
                        executed_volume = upbit_response.executed_volume
                        total_value = executed_volume * executed_price
                        fee = total_value * _UPBIT_FEE_RATE

                        order.mark_executed(
                            executed_price=executed_price,
                            executed_amount=executed_volume,
                            fee=fee,
                        )
                        logger.info(
                            f"[부분 체결 후 취소] order_id={order.id}, "
                            f"executed_price={executed_price}, "
                            f"executed_amount={executed_volume}"
                        )
                        return

                    order.mark_cancelled()
                    logger.warning(f"[주문 취소됨] order_id={order.id}")
                    return

                # state == "wait" 계속 폴링

            except UpbitPrivateAPIError as e:
                logger.warning(f"주문 상태 조회 실패: {e.message}")
                continue

        # 최대 시도 횟수 초과
        logger.warning(f"주문 체결 확인 타임아웃: order_id={order.id}, uuid={uuid}")

    async def sync_pending_orders(self) -> tuple[int, list[Order]]:
        """
        PENDING 상태의 주문을 Upbit와 동기화

        24시간 이내이면서 upbit_uuid가 있는 PENDING 주문을 Upbit의 실제 상태로
        업데이트합니다. 그 외(upbit_uuid 없음 또는 24시간 초과)의 좀비 주문은
        `_reconcile_stale_orders`에서 FAILED로 폐기합니다.

        Returns:
            tuple[int, list[Order]]: (동기화+폐기 주문 수, 이번에 체결 전환된 주문 목록)
                체결 전환 주문은 호출자가 포지션/통계에 반영한다.
        """
        # upbit_uuid 없는 좀비 PENDING 주문 먼저 정리 (Upbit 조회 불가)
        reconciled_count = await self._reconcile_stale_orders()

        # upbit_uuid 보유 PENDING 주문은 생성 시점과 무관하게 Upbit 동기화 대상.
        # (기존엔 24시간 필터로 오래된 주문이 영구 방치 → 좀비화. 제거함)
        stmt = select(Order).where(
            Order.status == OrderStatus.PENDING.value,
            Order.upbit_uuid.isnot(None),
        )
        result = await self._session.execute(stmt)
        pending_orders = list(result.scalars().all())

        if not pending_orders:
            return reconciled_count, []

        logger.info(f"PENDING 주문 동기화 시작: {len(pending_orders)}건")

        synced_count = 0
        executed_orders: list[Order] = []
        for order in pending_orders:
            try:
                upbit_order = await self._private_api.get_order(order.upbit_uuid)

                if upbit_order.state == "done":
                    # 체결 완료 - calculate_executed_price 사용
                    executed_volume = upbit_order.executed_volume or Decimal("0")

                    # 부분 취소 감지: 체결 수량 0이면 실질적 취소
                    if executed_volume == Decimal("0"):
                        order.mark_cancelled()
                        logger.warning(
                            f"PENDING 주문 부분 취소 감지 (체결 없이 done): "
                            f"order_id={order.id}"
                        )
                        synced_count += 1
                        continue

                    executed_price = self.calculate_executed_price(order, upbit_order)
                    total_value = executed_volume * executed_price
                    fee = total_value * _UPBIT_FEE_RATE

                    order.mark_executed(
                        executed_price=executed_price,
                        executed_amount=executed_volume,
                        fee=fee,
                    )

                    logger.info(
                        f"PENDING 주문 체결 확인: order_id={order.id}, "
                        f"executed_price={executed_price}, "
                        f"executed_amount={executed_volume}"
                    )
                    executed_orders.append(order)
                    synced_count += 1

                elif upbit_order.state == "cancel":
                    # 부분 체결 후 취소된 경우
                    executed_volume = upbit_order.executed_volume or Decimal("0")
                    if executed_volume > 0:
                        executed_price = self.calculate_executed_price(
                            order, upbit_order
                        )
                        total_value = executed_volume * executed_price
                        fee = total_value * _UPBIT_FEE_RATE

                        order.mark_executed(
                            executed_price=executed_price,
                            executed_amount=executed_volume,
                            fee=fee,
                        )
                        logger.info(
                            f"PENDING 주문 부분 체결 확인: order_id={order.id}, "
                            f"executed_price={executed_price}, "
                            f"executed_amount={executed_volume}"
                        )
                        executed_orders.append(order)
                    else:
                        order.mark_cancelled()
                        logger.info(f"PENDING 주문 취소 확인: order_id={order.id}")
                    synced_count += 1

                # state == "wait" 인 경우는 여전히 대기 중이므로 건너뜀

            except UpbitPrivateAPIError as e:
                logger.warning(
                    f"PENDING 주문 동기화 실패: order_id={order.id}, error={e.message}"
                )
                continue

        if synced_count > 0:
            await self._session.commit()
            logger.info(f"PENDING 주문 동기화 완료: {synced_count}건")

        return synced_count + reconciled_count, executed_orders

    async def _reconcile_stale_orders(self) -> int:
        """
        upbit_uuid 없는 좀비 PENDING 주문을 FAILED로 폐기

        upbit_uuid가 없는 PENDING 주문은 Upbit에 실제 주문이 생성되지 않은
        미체결 상태이므로 Upbit 조회로 복구할 수 없다. 이런 주문은 정상 동기화
        쿼리(upbit_uuid IS NOT NULL)에서 영구 제외되어 좀비로 남으므로 폐기한다.
        단, 막 생성되어 아직 upbit_uuid 할당 전인 주문을 오폐기하지 않도록
        생성 후 1시간이 지난 것만 대상으로 한다.

        Returns:
            int: FAILED로 폐기한 주문 수
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=1)
        stmt = select(Order).where(
            Order.status == OrderStatus.PENDING.value,
            Order.upbit_uuid.is_(None),
            Order.created_at <= cutoff_time,
        )
        result = await self._session.execute(stmt)
        stale_orders = list(result.scalars().all())

        if not stale_orders:
            return 0

        for order in stale_orders:
            order.mark_failed("upbit_uuid 없음 - 주문 미생성으로 자동 폐기")
            logger.warning(
                f"좀비 PENDING 주문 폐기: order_id={order.id}, "
                f"created_at={order.created_at}"
            )

        await self._session.commit()
        logger.info(f"좀비 PENDING 주문 폐기 완료: {len(stale_orders)}건")
        return len(stale_orders)

    async def check_and_update_existing_order(self, order: Order) -> bool:
        """
        기존 주문 상태 확인 및 업데이트

        재시도 시 이전 시도에서 Upbit UUID를 받은 경우 상태를 확인합니다.

        Args:
            order: 확인할 주문

        Returns:
            bool: 기존 주문이 존재하여 새 주문이 필요 없으면 True
        """
        if not order or not order.upbit_uuid:
            return False

        logger.info(f"재시도: 기존 주문 상태 확인 uuid={order.upbit_uuid}")
        try:
            existing = await self._private_api.get_order(order.upbit_uuid)
            if existing.state in ("done", "wait"):
                logger.info(f"기존 주문 발견: state={existing.state}")
                await self.update_order_status(order, existing)
                if not order.is_executed and existing.uuid:
                    await self.poll_order_completion(order, existing.uuid)
                return True  # 이미 주문이 있으므로 새 주문 안 함
        except UpbitPrivateAPIError as check_err:
            logger.warning(f"기존 주문 확인 실패: {check_err.message}")
            # 확인 실패 시 새 주문 시도
        return False
