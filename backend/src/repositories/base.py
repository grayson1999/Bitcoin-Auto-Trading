"""
기본 Repository 클래스

모든 도메인 Repository가 상속받는 Generic CRUD 기본 클래스입니다.
SQLAlchemy 2.0 async session과 호환됩니다.
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic Repository 기본 클래스

    공통 CRUD 메서드를 제공하며, 도메인별 Repository에서 상속받아
    특화된 쿼리 메서드를 추가할 수 있습니다.

    사용 예시:
        class MarketRepository(BaseRepository[MarketData]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, MarketData)

            async def get_latest(self) -> MarketData | None:
                # 도메인 특화 쿼리
                ...
    """

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        """
        Repository 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            model: 대상 Entity 클래스
        """
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        """
        ID로 단일 엔티티 조회

        Args:
            id: 엔티티 ID

        Returns:
            엔티티 또는 None (존재하지 않는 경우)
        """
        return await self.session.get(self.model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """
        전체 엔티티 조회 (페이징)

        Args:
            limit: 최대 조회 개수 (기본: 100)
            offset: 건너뛸 개수 (기본: 0)

        Returns:
            엔티티 목록
        """
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> T:
        """
        새 엔티티 생성

        Args:
            **kwargs: 엔티티 필드 값

        Returns:
            생성된 엔티티
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: int, **kwargs: Any) -> T | None:
        """
        엔티티 수정

        Args:
            id: 대상 엔티티 ID
            **kwargs: 수정할 필드 값

        Returns:
            수정된 엔티티 또는 None (존재하지 않는 경우)
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        return instance

    async def delete(self, id: int) -> bool:
        """
        엔티티 삭제

        Args:
            id: 대상 엔티티 ID

        Returns:
            삭제 성공 여부
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def count(self) -> int:
        """
        전체 엔티티 개수 조회

        Returns:
            엔티티 개수
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0

    async def exists(self, id: int) -> bool:
        """
        엔티티 존재 여부 확인

        Args:
            id: 엔티티 ID

        Returns:
            존재 여부
        """
        instance = await self.get_by_id(id)
        return instance is not None
