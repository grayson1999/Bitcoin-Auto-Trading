"""
주문 모니터링 모듈

이 모듈은 주문 상태 추적 및 동기화를 담당합니다.
- 주문 상태 폴링
- PENDING 주문 동기화
- 체결 확인 및 업데이트
"""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constants import (
    ORDER_POLL_INTERVAL_SECONDS,
    ORDER_POLL_MAX_ATTEMPTS,
    UPBIT_FEE_RATE,
)
from src.entities import Order, OrderStatus
from src.services.upbit_client import UpbitClient, UpbitError

if TYPE_CHECKING:
    pass

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
        upbit_client: UpbitClient,
    ) -> None:
        """
        OrderMonitor 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            upbit_client: Upbit API 클라이언트
        """
        self._session = session
        self._upbit_client = upbit_client

    def calculate_executed_price(self, order: Order, upbit_response) -> Decimal:
        """
        체결가 계산 헬퍼

        시장가 주문(매수/매도 모두)은 avg_price 또는 executed_funds/executed_volume 사용,
        지정가 주문은 price 사용.

        Args:
            order: 주문 객체
            upbit_response: Upbit 주문 응답

        Returns:
            Decimal: 계산된 체결가
        """
        # 시장가 주문 (매수/매도 모두): avg_price 우선 사용
        # - 시장가 매수: ord_type='price' (KRW 금액 지정)
        # - 시장가 매도: ord_type='market' (수량 지정)
        if upbit_response.avg_price:
            return upbit_response.avg_price
        elif upbit_response.executed_funds and upbit_response.executed_volume:
            return upbit_response.executed_funds / upbit_response.executed_volume

        # fallback: price 필드 (지정가 주문에서 사용)
        if upbit_response.price:
            return upbit_response.price

        # 모든 방법 실패 시 경고
        logger.warning(
            f"[체결가 계산] avg_price/executed_funds/price 모두 없음, "
            f"order_id={order.id}"
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
                upbit_response = await self._upbit_client.get_order(uuid)

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
            f"주문 체결 확인 타임아웃: order_id={order.id}, uuid={uuid}"
        )

    async def sync_pending_orders(self) -> int:
        """
        PENDING 상태의 주문을 Upbit와 동기화

        24시간 이내의 PENDING 상태 주문을 조회하여 Upbit의 실제 상태로 업데이트합니다.

        Returns:
            int: 동기화된 주문 수
        """
        # 24시간 이내의 PENDING 주문만 조회
        cutoff_time = datetime.now(UTC) - timedelta(hours=24)
        stmt = select(Order).where(
            Order.status == OrderStatus.PENDING.value,
            Order.upbit_uuid.isnot(None),
            Order.created_at > cutoff_time,
        )
        result = await self._session.execute(stmt)
        pending_orders = list(result.scalars().all())

        if not pending_orders:
            return 0

        logger.info(f"PENDING 주문 동기화 시작: {len(pending_orders)}건")

        synced_count = 0
        for order in pending_orders:
            try:
                upbit_order = await self._upbit_client.get_order(order.upbit_uuid)

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
                    synced_count += 1

                elif upbit_order.state == "cancel":
                    order.mark_cancelled()
                    logger.info(f"PENDING 주문 취소 확인: order_id={order.id}")
                    synced_count += 1

                # state == "wait" 인 경우는 여전히 대기 중이므로 건너뜀

            except UpbitError as e:
                logger.warning(
                    f"PENDING 주문 동기화 실패: order_id={order.id}, error={e.message}"
                )
                continue

        if synced_count > 0:
            await self._session.commit()
            logger.info(f"PENDING 주문 동기화 완료: {synced_count}건")

        return synced_count

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
            existing = await self._upbit_client.get_order(order.upbit_uuid)
            if existing.state in ("done", "wait"):
                logger.info(f"기존 주문 발견: state={existing.state}")
                await self.update_order_status(order, existing)
                if not order.is_executed and existing.uuid:
                    await self.poll_order_completion(order, existing.uuid)
                return True  # 이미 주문이 있으므로 새 주문 안 함
        except UpbitError as check_err:
            logger.warning(f"기존 주문 확인 실패: {check_err.message}")
            # 확인 실패 시 새 주문 시도
        return False
