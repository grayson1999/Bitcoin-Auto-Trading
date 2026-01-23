"""
시장 데이터 Repository

MarketData 엔티티에 대한 데이터베이스 접근 계층입니다.
시세 조회, 히스토리, 통계 관련 쿼리를 추상화합니다.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.config.constants import DATA_RETENTION_DAYS
from src.entities.market_data import MarketData
from src.repositories.base import BaseRepository
from src.utils import UTC


class MarketRepository(BaseRepository[MarketData]):
    """
    시장 데이터 Repository

    MarketData 엔티티에 대한 CRUD 및 특화된 쿼리 메서드를 제공합니다.

    사용 예시:
        async with get_session() as session:
            repo = MarketRepository(session)
            latest = await repo.get_latest()
            history = await repo.get_history(hours=24)
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Repository 초기화

        Args:
            session: SQLAlchemy 비동기 세션
        """
        super().__init__(session, MarketData)

    async def get_latest(
        self,
        limit: int = 1,
        symbol: str | None = None,
    ) -> list[MarketData]:
        """
        최신 시장 데이터 조회

        가장 최근에 수집된 데이터를 조회합니다.

        Args:
            limit: 조회할 레코드 수 (기본: 1)
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            최신 시장 데이터 목록 (최신순)
        """
        target_symbol = symbol or settings.trading_ticker
        result = await self.session.execute(
            select(MarketData)
            .where(MarketData.symbol == target_symbol)
            .order_by(MarketData.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_one(self, symbol: str | None = None) -> MarketData | None:
        """
        가장 최신 시장 데이터 1건 조회

        Args:
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            최신 MarketData 또는 None
        """
        data = await self.get_latest(limit=1, symbol=symbol)
        return data[0] if data else None

    async def get_history(
        self,
        hours: int = 24,
        symbol: str | None = None,
    ) -> list[MarketData]:
        """
        시간 범위 내 히스토리 조회

        지정된 시간 동안의 데이터를 시간순으로 조회합니다.

        Args:
            hours: 조회할 시간 범위 (기본: 24)
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            시간 범위 내 시장 데이터 목록 (오래된 순)
        """
        start_time = datetime.now(UTC) - timedelta(hours=hours)
        return await self.get_range(start_time, symbol=symbol)

    async def get_range(
        self,
        start_time: datetime,
        end_time: datetime | None = None,
        symbol: str | None = None,
    ) -> list[MarketData]:
        """
        시간 범위 내 시장 데이터 조회

        지정된 시간 범위의 데이터를 시간순으로 조회합니다.

        Args:
            start_time: 시작 시간
            end_time: 종료 시간 (기본: 현재 시간)
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            시간 범위 내 시장 데이터 목록 (오래된 순)
        """
        if end_time is None:
            end_time = datetime.now(UTC)

        target_symbol = symbol or settings.trading_ticker
        result = await self.session.execute(
            select(MarketData)
            .where(MarketData.symbol == target_symbol)
            .where(MarketData.timestamp >= start_time)
            .where(MarketData.timestamp <= end_time)
            .order_by(MarketData.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_hourly_summary(
        self,
        hours: int = 24,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        시간별 요약 통계 조회

        지정된 시간 동안의 가격 변동 통계를 계산합니다.

        Args:
            hours: 통계 기간 (시간)
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            요약 통계 딕셔너리:
                - count: 데이터 포인트 수
                - period_hours: 기간 (시간)
                - latest_price: 최신 가격
                - high: 최고가
                - low: 최저가
                - price_change_pct: 가격 변동률 (%)
                - first_timestamp: 시작 시간
                - last_timestamp: 종료 시간
        """
        data = await self.get_history(hours, symbol)

        if not data:
            return {
                "count": 0,
                "period_hours": hours,
                "latest_price": None,
                "high": None,
                "low": None,
                "price_change_pct": None,
            }

        prices = [d.price for d in data]
        first_price = prices[0]
        last_price = prices[-1]

        price_change_pct = (
            ((last_price - first_price) / first_price * 100)
            if first_price > 0
            else Decimal("0")
        )

        return {
            "count": len(data),
            "period_hours": hours,
            "latest_price": float(last_price),
            "high": float(max(prices)),
            "low": float(min(prices)),
            "price_change_pct": float(price_change_pct),
            "first_timestamp": data[0].timestamp.isoformat(),
            "last_timestamp": data[-1].timestamp.isoformat(),
        }

    async def cleanup_old_data(self, retention_days: int | None = None) -> int:
        """
        오래된 데이터 정리

        보관 기간이 지난 시장 데이터를 삭제합니다.

        Args:
            retention_days: 보관 기간 (일) (기본: DATA_RETENTION_DAYS)

        Returns:
            삭제된 레코드 수
        """
        if retention_days is None:
            retention_days = DATA_RETENTION_DAYS

        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

        result = await self.session.execute(
            delete(MarketData).where(MarketData.timestamp < cutoff_date)
        )

        return result.rowcount

    async def get_count_by_symbol(self, symbol: str | None = None) -> int:
        """
        심볼별 레코드 개수 조회

        Args:
            symbol: 마켓 심볼 (기본: settings.trading_ticker)

        Returns:
            레코드 개수
        """
        target_symbol = symbol or settings.trading_ticker
        result = await self.session.execute(
            select(func.count())
            .select_from(MarketData)
            .where(MarketData.symbol == target_symbol)
        )
        return result.scalar() or 0

    async def save(self, market_data: MarketData) -> MarketData:
        """
        시장 데이터 저장

        Args:
            market_data: 저장할 MarketData 엔티티

        Returns:
            저장된 MarketData (ID 할당됨)
        """
        self.session.add(market_data)
        await self.session.flush()
        return market_data
