"""
매매 신호 Repository

TradingSignal 엔티티에 대한 데이터베이스 접근 계층입니다.
AI 매매 신호 조회, 날짜 범위 조회 등 쿼리를 추상화합니다.
모든 쿼리에 user_id 필터링이 적용됩니다.
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.trading_signal import SignalType, TradingSignal
from src.repositories.base import BaseRepository
from src.utils import UTC


class SignalRepository(BaseRepository[TradingSignal]):
    """
    매매 신호 Repository

    TradingSignal 엔티티에 대한 CRUD 및 특화된 쿼리 메서드를 제공합니다.
    모든 쿼리 메서드에 user_id 필터링이 적용됩니다.

    사용 예시:
        async with get_session() as session:
            repo = SignalRepository(session, user_id=1)
            latest = await repo.get_latest()
            signals = await repo.get_by_date_range(start, end)
    """

    def __init__(self, session: AsyncSession, user_id: int | None = None) -> None:
        """
        Repository 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            user_id: 사용자 ID (필터링용, 없으면 전체 조회)
        """
        super().__init__(session, TradingSignal)
        self.user_id = user_id

    def _user_filter(self, query):
        """user_id 필터 적용"""
        if self.user_id is not None:
            return query.where(TradingSignal.user_id == self.user_id)
        return query

    async def get_latest(
        self, limit: int = 1, offset: int = 0
    ) -> list[TradingSignal]:
        """
        최신 매매 신호 조회

        가장 최근에 생성된 신호를 조회합니다.

        Args:
            limit: 조회할 레코드 수 (기본: 1)
            offset: 건너뛸 레코드 수 (기본: 0)

        Returns:
            최신 매매 신호 목록 (최신순)
        """
        query = select(TradingSignal)
        query = self._user_filter(query)
        result = await self.session.execute(
            query.order_by(TradingSignal.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_one(self) -> TradingSignal | None:
        """
        가장 최신 매매 신호 1건 조회

        Returns:
            최신 TradingSignal 또는 None
        """
        signals = await self.get_latest(limit=1)
        return signals[0] if signals else None

    async def get_by_date_range(
        self,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> list[TradingSignal]:
        """
        날짜 범위 내 매매 신호 조회

        지정된 날짜 범위의 신호를 시간순으로 조회합니다.

        Args:
            start_time: 시작 시간
            end_time: 종료 시간 (기본: 현재 시간)

        Returns:
            날짜 범위 내 매매 신호 목록 (오래된 순)
        """
        if end_time is None:
            end_time = datetime.now(UTC)

        query = (
            select(TradingSignal)
            .where(TradingSignal.created_at >= start_time)
            .where(TradingSignal.created_at <= end_time)
        )
        query = self._user_filter(query)
        result = await self.session.execute(
            query.order_by(TradingSignal.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_hours(self, hours: int = 24) -> list[TradingSignal]:
        """
        시간 범위 내 매매 신호 조회

        지정된 시간 동안의 신호를 조회합니다.

        Args:
            hours: 조회할 시간 범위 (기본: 24)

        Returns:
            시간 범위 내 매매 신호 목록 (오래된 순)
        """
        start_time = datetime.now(UTC) - timedelta(hours=hours)
        return await self.get_by_date_range(start_time)

    async def get_by_type(
        self,
        signal_type: SignalType,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TradingSignal]:
        """
        신호 타입별 조회

        Args:
            signal_type: 신호 타입 (BUY/HOLD/SELL)
            limit: 최대 조회 개수
            offset: 건너뛸 레코드 수 (기본: 0)

        Returns:
            해당 타입의 매매 신호 목록 (최신순)
        """
        query = select(TradingSignal).where(
            TradingSignal.signal_type == signal_type.value
        )
        query = self._user_filter(query)
        result = await self.session.execute(
            query.order_by(TradingSignal.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unevaluated(self, limit: int = 100) -> list[TradingSignal]:
        """
        성과 미평가 신호 조회

        아직 성과 평가가 완료되지 않은 신호를 조회합니다.

        Args:
            limit: 최대 조회 개수

        Returns:
            미평가 매매 신호 목록 (오래된 순)
        """
        query = select(TradingSignal).where(TradingSignal.outcome_evaluated == False)  # noqa: E712
        query = self._user_filter(query)
        result = await self.session.execute(
            query.order_by(TradingSignal.created_at.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_evaluated(self, limit: int = 100) -> list[TradingSignal]:
        """
        성과 평가 완료 신호 조회

        성과 평가가 완료된 신호를 조회합니다.

        Args:
            limit: 최대 조회 개수

        Returns:
            평가 완료 매매 신호 목록 (최신순)
        """
        query = select(TradingSignal).where(TradingSignal.outcome_evaluated == True)  # noqa: E712
        query = self._user_filter(query)
        result = await self.session.execute(
            query.order_by(TradingSignal.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_correct_signals(self, limit: int = 100) -> list[TradingSignal]:
        """
        정확한 신호 조회

        신호 방향이 정확했던 신호를 조회합니다.

        Args:
            limit: 최대 조회 개수

        Returns:
            정확한 매매 신호 목록 (최신순)
        """
        query = select(TradingSignal).where(TradingSignal.outcome_correct == True)  # noqa: E712
        query = self._user_filter(query)
        result = await self.session.execute(
            query.order_by(TradingSignal.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def save(self, signal: TradingSignal) -> TradingSignal:
        """
        매매 신호 저장

        Args:
            signal: 저장할 TradingSignal 엔티티

        Returns:
            저장된 TradingSignal (ID 할당됨)
        """
        self.session.add(signal)
        await self.session.flush()
        return signal
