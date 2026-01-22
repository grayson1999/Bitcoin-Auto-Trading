"""
주문 Repository

Order 엔티티에 대한 데이터베이스 접근 계층입니다.
주문 조회, 상태별 필터링 등 쿼리를 추상화합니다.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.order import Order, OrderSide, OrderStatus
from src.repositories.base import BaseRepository
from src.utils import UTC


class OrderRepository(BaseRepository[Order]):
    """
    주문 Repository

    Order 엔티티에 대한 CRUD 및 특화된 쿼리 메서드를 제공합니다.

    사용 예시:
        async with get_session() as session:
            repo = OrderRepository(session)
            pending = await repo.get_pending()
            executed = await repo.get_by_status(OrderStatus.EXECUTED)
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Repository 초기화

        Args:
            session: SQLAlchemy 비동기 세션
        """
        super().__init__(session, Order)

    async def get_pending(self, limit: int = 100) -> list[Order]:
        """
        대기 중인 주문 조회

        PENDING 상태의 주문을 조회합니다.

        Args:
            limit: 최대 조회 개수

        Returns:
            대기 중인 주문 목록 (생성순)
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.status == OrderStatus.PENDING.value)
            .order_by(Order.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: OrderStatus,
        limit: int = 100,
    ) -> list[Order]:
        """
        상태별 주문 조회

        Args:
            status: 주문 상태
            limit: 최대 조회 개수

        Returns:
            해당 상태의 주문 목록 (최신순)
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.status == status.value)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_side(
        self,
        side: OrderSide,
        limit: int = 100,
    ) -> list[Order]:
        """
        방향별 주문 조회

        Args:
            side: 주문 방향 (BUY/SELL)
            limit: 최대 조회 개수

        Returns:
            해당 방향의 주문 목록 (최신순)
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.side == side.value)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_upbit_uuid(self, upbit_uuid: str) -> Order | None:
        """
        Upbit UUID로 주문 조회

        Args:
            upbit_uuid: Upbit 주문 UUID

        Returns:
            주문 또는 None
        """
        result = await self.session.execute(
            select(Order).where(Order.upbit_uuid == upbit_uuid)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Order | None:
        """
        멱등성 키로 주문 조회

        Args:
            idempotency_key: 멱등성 키

        Returns:
            주문 또는 None
        """
        result = await self.session.execute(
            select(Order).where(Order.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def get_recent(self, limit: int = 50) -> list[Order]:
        """
        최근 주문 조회

        Args:
            limit: 조회 개수

        Returns:
            최근 주문 목록 (최신순)
        """
        result = await self.session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> list[Order]:
        """
        날짜 범위 내 주문 조회

        Args:
            start_time: 시작 시간
            end_time: 종료 시간 (기본: 현재 시간)

        Returns:
            날짜 범위 내 주문 목록 (오래된 순)
        """
        if end_time is None:
            end_time = datetime.now(UTC)

        result = await self.session.execute(
            select(Order)
            .where(Order.created_at >= start_time)
            .where(Order.created_at <= end_time)
            .order_by(Order.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_today_executed_count(self) -> int:
        """
        오늘 체결된 주문 수 조회

        Returns:
            오늘 체결 주문 개수
        """
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        result = await self.session.execute(
            select(func.count(Order.id))
            .where(Order.created_at >= today_start)
            .where(Order.status == OrderStatus.EXECUTED.value)
        )
        return result.scalar() or 0

    async def get_by_signal_id(self, signal_id: int) -> list[Order]:
        """
        AI 신호 ID로 주문 조회

        Args:
            signal_id: 연관 AI 신호 ID

        Returns:
            해당 신호의 주문 목록
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.signal_id == signal_id)
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_executed_by_hours(self, hours: int = 24) -> list[Order]:
        """
        시간 범위 내 체결된 주문 조회

        Args:
            hours: 조회 시간 범위 (기본: 24)

        Returns:
            체결된 주문 목록 (오래된 순)
        """
        start_time = datetime.now(UTC) - timedelta(hours=hours)
        result = await self.session.execute(
            select(Order)
            .where(Order.created_at >= start_time)
            .where(Order.status == OrderStatus.EXECUTED.value)
            .order_by(Order.created_at.asc())
        )
        return list(result.scalars().all())

    async def save(self, order: Order) -> Order:
        """
        주문 저장

        Args:
            order: 저장할 Order 엔티티

        Returns:
            저장된 Order (ID 할당됨)
        """
        self.session.add(order)
        await self.session.flush()
        return order
