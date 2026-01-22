"""
설정 Repository

시스템 설정(SystemConfig) 엔티티에 대한 데이터베이스 접근 계층입니다.
키-값 형태의 설정을 관리합니다.
"""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.system_config import SystemConfig
from src.repositories.base import BaseRepository


class ConfigRepository(BaseRepository[SystemConfig]):
    """
    설정 Repository

    SystemConfig 엔티티에 대한 CRUD 및 특화된 쿼리 메서드를 제공합니다.

    사용 예시:
        async with get_session() as session:
            repo = ConfigRepository(session)
            value = await repo.get_value("trading_enabled")
            await repo.set_value("trading_enabled", True)
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Repository 초기화

        Args:
            session: SQLAlchemy 비동기 세션
        """
        super().__init__(session, SystemConfig)

    async def get_value(self, key: str) -> Any | None:
        """
        설정 키로 값 조회

        Args:
            key: 설정 키

        Returns:
            파싱된 설정 값 또는 None (키가 없는 경우)
        """
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()

        if config is None:
            return None

        return self._parse_value(config.value)

    async def set_value(self, key: str, value: Any) -> SystemConfig:
        """
        설정 키에 값 저장 (upsert)

        키가 존재하면 업데이트하고, 없으면 생성합니다.

        Args:
            key: 설정 키
            value: 저장할 값 (JSON 직렬화 가능)

        Returns:
            저장된 SystemConfig 엔티티
        """
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()

        json_value = json.dumps(value)
        now = datetime.now(UTC)

        if config is None:
            config = SystemConfig(
                key=key,
                value=json_value,
                updated_at=now,
            )
            self.session.add(config)
        else:
            config.value = json_value
            config.updated_at = now

        await self.session.flush()
        return config

    async def get_all_configs(self) -> dict[str, Any]:
        """
        모든 설정 조회

        Returns:
            키-값 딕셔너리 (값은 파싱된 상태)
        """
        result = await self.session.execute(select(SystemConfig))
        configs = result.scalars().all()

        return {config.key: self._parse_value(config.value) for config in configs}

    async def delete_key(self, key: str) -> bool:
        """
        설정 키 삭제

        Args:
            key: 삭제할 설정 키

        Returns:
            삭제 성공 여부
        """
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()

        if config is None:
            return False

        await self.session.delete(config)
        await self.session.flush()
        return True

    async def get_by_key(self, key: str) -> SystemConfig | None:
        """
        설정 키로 엔티티 조회

        Args:
            key: 설정 키

        Returns:
            SystemConfig 엔티티 또는 None
        """
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _parse_value(json_str: str) -> Any:
        """
        JSON 문자열을 파싱하여 Python 값으로 변환

        Args:
            json_str: JSON 문자열

        Returns:
            파싱된 Python 값
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 원본 문자열 반환
            return json_str
