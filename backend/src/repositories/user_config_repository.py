"""
사용자 설정 Repository

UserConfig 엔티티에 대한 데이터베이스 접근 계층입니다.
사용자별 설정 조회 및 system_configs와 병합 로직을 제공합니다.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.user_config import UserConfig
from src.repositories.base import BaseRepository
from src.utils import UTC


class UserConfigRepository(BaseRepository[UserConfig]):
    """
    사용자 설정 Repository

    UserConfig 엔티티에 대한 CRUD 및 특화된 쿼리 메서드를 제공합니다.

    사용 예시:
        async with get_session() as session:
            repo = UserConfigRepository(session)
            configs = await repo.get_all_by_user(user_id=1)
            value = await repo.get_value(user_id=1, key="stop_loss_pct")
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Repository 초기화

        Args:
            session: SQLAlchemy 비동기 세션
        """
        super().__init__(session, UserConfig)

    async def get_by_user_and_key(self, user_id: int, key: str) -> UserConfig | None:
        """
        사용자별 설정 키로 조회

        Args:
            user_id: 사용자 ID
            key: 설정 키

        Returns:
            설정 또는 None
        """
        result = await self.session.execute(
            select(UserConfig)
            .where(UserConfig.user_id == user_id)
            .where(UserConfig.key == key)
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> list[UserConfig]:
        """
        사용자의 모든 설정 조회

        Args:
            user_id: 사용자 ID

        Returns:
            설정 목록
        """
        result = await self.session.execute(
            select(UserConfig)
            .where(UserConfig.user_id == user_id)
            .order_by(UserConfig.key)
        )
        return list(result.scalars().all())

    async def get_value(self, user_id: int, key: str) -> str | None:
        """
        사용자 설정값 조회

        Args:
            user_id: 사용자 ID
            key: 설정 키

        Returns:
            설정값 또는 None
        """
        config = await self.get_by_user_and_key(user_id, key)
        return config.value if config else None

    async def set_value(
        self,
        user_id: int,
        key: str,
        value: str,
        updated_by: int | None = None,
    ) -> UserConfig:
        """
        사용자 설정값 저장 (upsert)

        Args:
            user_id: 사용자 ID
            key: 설정 키
            value: 설정값
            updated_by: 수정자 사용자 ID

        Returns:
            저장된 설정
        """
        config = await self.get_by_user_and_key(user_id, key)
        now = datetime.now(UTC)

        if config is None:
            config = UserConfig(
                user_id=user_id,
                key=key,
                value=value,
                created_at=now,
                updated_at=now,
                created_by=updated_by,
                updated_by=updated_by,
            )
            self.session.add(config)
        else:
            config.value = value
            config.updated_at = now
            config.updated_by = updated_by

        await self.session.flush()
        return config

    async def delete_by_user_and_key(self, user_id: int, key: str) -> bool:
        """
        사용자 설정 삭제

        Args:
            user_id: 사용자 ID
            key: 설정 키

        Returns:
            삭제 성공 여부
        """
        config = await self.get_by_user_and_key(user_id, key)
        if config is None:
            return False

        await self.session.delete(config)
        await self.session.flush()
        return True

    async def get_user_configs_as_dict(self, user_id: int) -> dict[str, str]:
        """
        사용자 설정을 딕셔너리로 반환

        Args:
            user_id: 사용자 ID

        Returns:
            {key: value} 딕셔너리
        """
        configs = await self.get_all_by_user(user_id)
        return {config.key: config.value for config in configs}
