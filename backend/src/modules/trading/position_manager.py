"""
포지션 관리 모듈

주문 체결 후 포지션 업데이트, 동기화 등 포지션 관련 로직을 담당합니다.
trading/service.py에서 분리됨.
"""

from datetime import datetime
from decimal import Decimal

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import (
    UpbitPrivateAPIError,
    UpbitPublicAPI,
    UpbitPublicAPIError,
)
from src.config import settings
from src.entities import Order, Position
from src.modules.trading.order_validator import BalanceInfo, OrderValidator
from src.utils import UTC


class PositionManager:
    """
    포지션 관리자

    주문 체결 후 포지션 업데이트, Upbit 잔고 동기화 등을 담당합니다.

    Attributes:
        _session: SQLAlchemy 비동기 세션
        _public_api: Upbit Public API 클라이언트
        _validator: 주문 검증기 (잔고 조회용)
    """

    def __init__(
        self,
        session: AsyncSession,
        public_api: UpbitPublicAPI,
        validator: OrderValidator,
    ) -> None:
        """
        PositionManager 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            public_api: Upbit Public API 클라이언트
            validator: 주문 검증기
        """
        self._session = session
        self._public_api = public_api
        self._validator = validator

    async def get_position(self) -> Position | None:
        """현재 포지션 조회"""
        stmt = select(Position).where(Position.symbol == settings.trading_ticker)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_position_after_order(self, order: Order) -> None:
        """
        주문 체결 후 포지션 업데이트

        Args:
            order: 체결된 주문
        """
        position = await self.get_position()

        if position is None:
            # 포지션 생성
            position = Position(
                symbol=settings.trading_ticker,
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
                # 시장가 매수의 경우 executed_amount는 KRW, 실제 코인 수량 계산 필요
                coin_quantity = order.executed_amount / order.executed_price
                new_quantity = position.quantity + coin_quantity

                if new_quantity > 0:
                    # 가중 평균 매수가 계산
                    old_cost = position.quantity * position.avg_buy_price
                    new_cost = order.executed_amount
                    position.avg_buy_price = (old_cost + new_cost) / new_quantity

                position.quantity = new_quantity

        elif order.is_sell and order.executed_amount:
            # 매도: 수량 감소 (평균 매수가는 유지)
            position.quantity = max(
                Decimal("0"), position.quantity - order.executed_amount
            )

            # 수량이 0이면 평균 매수가 초기화
            if position.quantity == 0:
                position.avg_buy_price = Decimal("0")

        # 현재가로 평가금액 업데이트
        try:
            ticker = await self._public_api.get_ticker(settings.trading_ticker)
            position.update_value(ticker.trade_price)
        except (UpbitPrivateAPIError, UpbitPublicAPIError):
            pass

        position.updated_at = datetime.now(UTC)

        logger.info(
            f"포지션 업데이트: quantity={position.quantity}, "
            f"avg_price={position.avg_buy_price}, pnl={position.unrealized_pnl}"
        )

    async def sync_position_from_upbit(self) -> Position | None:
        """
        Upbit 실제 잔고와 Position 테이블 동기화

        Upbit API에서 실제 코인 잔고를 조회하여 Position 테이블에 반영합니다.
        외부에서 직접 거래한 내역도 Position에 반영됩니다.

        Returns:
            Position | None: 동기화된 포지션 (코인이 없으면 None)
        """
        try:
            balance_info = await self._validator.get_balance_info()
        except (UpbitPrivateAPIError, UpbitPublicAPIError) as e:
            logger.warning(f"포지션 동기화 실패 - 잔고 조회 오류: {e.message}")
            return None

        # 코인 보유량이 없으면 포지션 삭제 또는 0으로 설정
        position = await self.get_position()

        if balance_info.coin_available <= 0 and balance_info.coin_locked <= 0:
            if position:
                position.quantity = Decimal("0")
                position.current_value = Decimal("0")
                position.unrealized_pnl = Decimal("0")
                position.updated_at = datetime.now(UTC)
                logger.info(
                    f"포지션 동기화: {settings.trading_currency} 보유량 없음 - 포지션 초기화"
                )
            return position

        # 포지션이 없으면 새로 생성
        if position is None:
            position = Position(
                symbol=settings.trading_ticker,
                quantity=Decimal("0"),
                avg_buy_price=Decimal("0"),
                current_value=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                updated_at=datetime.now(UTC),
            )
            self._session.add(position)

        # Upbit 잔고로 포지션 업데이트
        total_coin = balance_info.coin_available + balance_info.coin_locked
        position.quantity = total_coin
        position.avg_buy_price = balance_info.coin_avg_price

        # 현재가로 평가금액 및 손익 계산
        try:
            ticker = await self._public_api.get_ticker(settings.trading_ticker)
            position.update_value(ticker.trade_price)
        except (UpbitPrivateAPIError, UpbitPublicAPIError):
            # 현재가 조회 실패 시 평균 매수가로 계산
            position.current_value = total_coin * balance_info.coin_avg_price
            position.unrealized_pnl = Decimal("0")

        position.updated_at = datetime.now(UTC)
        await self._session.flush()

        logger.info(
            f"포지션 동기화 완료: quantity={position.quantity:.4f} "
            f"{settings.trading_currency}, "
            f"avg_price={position.avg_buy_price:,.0f}, "
            f"unrealized_pnl={position.unrealized_pnl:,.0f}"
        )

        return position

    async def get_balance_info(self) -> BalanceInfo:
        """
        Upbit 계좌 잔고 조회

        Returns:
            BalanceInfo: 잔고 정보
        """
        return await self._validator.get_balance_info()
