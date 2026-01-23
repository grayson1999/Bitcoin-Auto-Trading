"""
포지션 Repository

Position 엔티티에 대한 데이터베이스 접근 계층입니다.
포지션 조회, 업데이트, 종료 등 쿼리를 추상화합니다.
모든 쿼리에 user_id 필터링이 적용됩니다.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.entities.position import Position
from src.repositories.base import BaseRepository
from src.utils import UTC


class PositionRepository(BaseRepository[Position]):
    """
    포지션 Repository

    Position 엔티티에 대한 CRUD 및 특화된 쿼리 메서드를 제공합니다.
    모든 쿼리 메서드에 user_id 필터링이 적용됩니다.

    사용 예시:
        async with get_session() as session:
            repo = PositionRepository(session, user_id=1)
            position = await repo.get_open()
            await repo.close_position(position.symbol)
    """

    def __init__(self, session: AsyncSession, user_id: int | None = None) -> None:
        """
        Repository 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            user_id: 사용자 ID (필터링용, 없으면 전체 조회)
        """
        super().__init__(session, Position)
        self.user_id = user_id

    def _user_filter(self, query):
        """user_id 필터 적용"""
        if self.user_id is not None:
            return query.where(Position.user_id == self.user_id)
        return query

    async def get_open(self, symbol: str | None = None) -> Position | None:
        """
        열린 포지션 조회

        수량이 0보다 큰 포지션을 조회합니다.

        Args:
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            열린 포지션 또는 None
        """
        target_symbol = symbol or settings.trading_ticker
        query = (
            select(Position)
            .where(Position.symbol == target_symbol)
            .where(Position.quantity > 0)
        )
        query = self._user_filter(query)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_symbol(self, symbol: str | None = None) -> Position | None:
        """
        심볼로 포지션 조회 (수량 무관)

        Args:
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            포지션 또는 None
        """
        target_symbol = symbol or settings.trading_ticker
        query = select(Position).where(Position.symbol == target_symbol)
        query = self._user_filter(query)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create(self, symbol: str | None = None) -> Position:
        """
        포지션 조회 또는 생성

        포지션이 없으면 새로 생성합니다.
        user_id가 설정되어 있어야 합니다.

        Args:
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            기존 또는 새로 생성된 포지션

        Raises:
            ValueError: user_id가 설정되지 않은 경우
        """
        if self.user_id is None:
            raise ValueError("user_id is required for get_or_create")

        target_symbol = symbol or settings.trading_ticker
        position = await self.get_by_symbol(target_symbol)

        if position is None:
            now = datetime.now(UTC)
            position = Position(
                user_id=self.user_id,
                symbol=target_symbol,
                quantity=Decimal("0"),
                avg_buy_price=Decimal("0"),
                current_value=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                created_at=now,
                updated_at=now,
            )
            self.session.add(position)
            await self.session.flush()

        return position

    async def close_position(self, symbol: str | None = None) -> bool:
        """
        포지션 종료 (수량 0으로 리셋)

        Args:
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            종료 성공 여부
        """
        target_symbol = symbol or settings.trading_ticker
        position = await self.get_by_symbol(target_symbol)

        if position is None:
            return False

        position.quantity = Decimal("0")
        position.avg_buy_price = Decimal("0")
        position.current_value = Decimal("0")
        position.unrealized_pnl = Decimal("0")
        position.updated_at = datetime.now(UTC)

        await self.session.flush()
        return True

    async def update_position(
        self,
        symbol: str | None = None,
        quantity: Decimal | None = None,
        avg_buy_price: Decimal | None = None,
        current_value: Decimal | None = None,
        unrealized_pnl: Decimal | None = None,
    ) -> Position | None:
        """
        포지션 업데이트

        Args:
            symbol: 마켓 심볼 (기본: settings.trading_ticker)
            quantity: 보유 수량
            avg_buy_price: 평균 매수가
            current_value: 현재 평가금액
            unrealized_pnl: 미실현 손익

        Returns:
            업데이트된 포지션 또는 None
        """
        target_symbol = symbol or settings.trading_ticker
        position = await self.get_by_symbol(target_symbol)

        if position is None:
            return None

        if quantity is not None:
            position.quantity = quantity
        if avg_buy_price is not None:
            position.avg_buy_price = avg_buy_price
        if current_value is not None:
            position.current_value = current_value
        if unrealized_pnl is not None:
            position.unrealized_pnl = unrealized_pnl

        position.updated_at = datetime.now(UTC)
        await self.session.flush()
        return position

    async def update_value_by_price(
        self,
        current_price: Decimal,
        symbol: str | None = None,
    ) -> Position | None:
        """
        현재가로 평가금액 및 손익 업데이트

        Args:
            current_price: 현재 가격
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            업데이트된 포지션 또는 None
        """
        target_symbol = symbol or settings.trading_ticker
        position = await self.get_by_symbol(target_symbol)

        if position is None:
            return None

        position.update_value(current_price)
        position.updated_at = datetime.now(UTC)
        await self.session.flush()
        return position

    async def has_open_position(self, symbol: str | None = None) -> bool:
        """
        열린 포지션 존재 여부 확인

        Args:
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            열린 포지션 존재 여부
        """
        position = await self.get_open(symbol)
        return position is not None

    async def get_all_open(self) -> list[Position]:
        """
        모든 열린 포지션 조회

        Returns:
            열린 포지션 목록
        """
        query = select(Position).where(Position.quantity > 0)
        query = self._user_filter(query)
        result = await self.session.execute(query.order_by(Position.updated_at.desc()))
        return list(result.scalars().all())

    async def save(self, position: Position) -> Position:
        """
        포지션 저장

        Args:
            position: 저장할 Position 엔티티

        Returns:
            저장된 Position (ID 할당됨)
        """
        self.session.add(position)
        await self.session.flush()
        return position
