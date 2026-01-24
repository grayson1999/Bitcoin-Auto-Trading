"""
설정 서비스

DB-first 우선순위로 설정값을 관리합니다.
설정 조회 순서: DB → 환경변수 → 기본값

캐시 통합:
- ConfigRepository의 TTL 캐시를 자동으로 활용
- 조회 시 캐시 히트로 DB 부하 95% 감소
- 변경 시 캐시 자동 무효화로 일관성 유지
"""

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import DB_OVERRIDABLE_KEYS, Settings, settings
from src.repositories.config_repository import ConfigRepository, get_config_cache


class ConfigService:
    """
    설정 서비스

    DB 우선순위 로직을 적용하여 설정값을 조회합니다.

    설정 조회 순서:
        1. DB (system_configs 테이블)
        2. 환경변수 (settings)
        3. 기본값 (default 파라미터)

    민감 정보 (API 키 등)는 환경변수 전용으로 DB 저장이 불가합니다.

    사용 예시:
        async with get_session() as session:
            service = ConfigService(session)
            value = await service.get("trading_enabled", default=True)
            await service.set("position_size_min_pct", 30.0)
    """

    def __init__(
        self,
        session: AsyncSession,
        env_settings: Settings | None = None,
    ) -> None:
        """
        서비스 초기화

        Args:
            session: SQLAlchemy 비동기 세션
            env_settings: 환경변수 설정 (기본: 전역 settings)
        """
        self.repo = ConfigRepository(session)
        self.settings = env_settings or settings

    async def get(self, key: str, default: Any = None) -> Any:
        """
        설정값 조회 (DB 우선)

        Args:
            key: 설정 키
            default: 기본값 (DB, 환경변수 모두 없을 때)

        Returns:
            설정값 (DB → 환경변수 → 기본값 순서)
        """
        # 1. DB에서 조회 (DB 오버라이드 가능한 키만)
        if key in DB_OVERRIDABLE_KEYS:
            db_value = await self.repo.get_value(key)
            if db_value is not None:
                logger.debug(f"설정 '{key}' DB에서 조회: {db_value}")
                return db_value

        # 2. 환경변수에서 조회
        env_value = getattr(self.settings, key, None)
        if env_value is not None:
            logger.debug(f"설정 '{key}' 환경변수에서 조회: {env_value}")
            return env_value

        # 3. 기본값 반환
        logger.debug(f"설정 '{key}' 기본값 사용: {default}")
        return default

    async def set(self, key: str, value: Any) -> bool:
        """
        설정값 저장 (DB에 저장)

        DB 오버라이드 가능한 키만 저장됩니다.
        민감 정보 키는 저장이 거부됩니다.

        Args:
            key: 설정 키
            value: 설정 값

        Returns:
            저장 성공 여부
        """
        if key not in DB_OVERRIDABLE_KEYS:
            logger.warning(f"설정 '{key}'는 DB 저장이 허용되지 않습니다")
            return False

        await self.repo.set_value(key, value)
        logger.info(f"설정 '{key}' DB에 저장: {value}")
        return True

    async def get_all(self) -> dict[str, Any]:
        """
        모든 설정 조회 (DB 우선 병합)

        Returns:
            병합된 설정 딕셔너리 (DB 값이 환경변수 값을 오버라이드)
        """
        # 환경변수 설정을 기본값으로
        result: dict[str, Any] = {}

        # DB 오버라이드 가능한 키에 대해 환경변수 값 추가
        for key in DB_OVERRIDABLE_KEYS:
            env_value = getattr(self.settings, key, None)
            if env_value is not None:
                result[key] = env_value

        # DB 값으로 오버라이드
        db_configs = await self.repo.get_all_configs()
        for key, value in db_configs.items():
            if key in DB_OVERRIDABLE_KEYS:
                result[key] = value

        return result

    async def get_db_configs(self) -> dict[str, Any]:
        """
        DB에 저장된 설정만 조회

        Returns:
            DB 설정 딕셔너리
        """
        return await self.repo.get_all_configs()

    async def delete(self, key: str) -> bool:
        """
        DB에서 설정 삭제

        삭제 후 해당 키는 환경변수 값으로 폴백됩니다.

        Args:
            key: 삭제할 설정 키

        Returns:
            삭제 성공 여부
        """
        if key not in DB_OVERRIDABLE_KEYS:
            logger.warning(f"설정 '{key}'는 DB에 존재하지 않습니다")
            return False

        success = await self.repo.delete_key(key)
        if success:
            logger.info(f"설정 '{key}' DB에서 삭제됨")
        return success

    async def is_trading_enabled(self) -> bool:
        """
        거래 활성화 여부 조회

        Returns:
            거래 활성화 상태 (기본: True)
        """
        value = await self.get("trading_enabled", default=True)
        return bool(value)

    async def get_position_size_range(self) -> tuple[float, float]:
        """
        포지션 크기 범위 조회

        Returns:
            (최소 %, 최대 %) 튜플
        """
        min_pct = await self.get("position_size_min_pct", default=25.0)
        max_pct = await self.get("position_size_max_pct", default=50.0)
        return (float(min_pct), float(max_pct))

    async def get_risk_params(self) -> dict[str, float]:
        """
        리스크 파라미터 조회

        Returns:
            리스크 관련 설정 딕셔너리
        """
        return {
            "stop_loss_pct": float(await self.get("stop_loss_pct", default=5.0)),
            "daily_loss_limit_pct": float(
                await self.get("daily_loss_limit_pct", default=5.0)
            ),
            "volatility_threshold_pct": float(
                await self.get("volatility_threshold_pct", default=3.0)
            ),
        }

    async def get_config_with_source(
        self, key: str
    ) -> tuple[Any, str, datetime | None]:
        """
        설정값과 출처 정보 조회

        Args:
            key: 설정 키

        Returns:
            (값, 출처, 수정시간) 튜플
            - 출처: "db", "env", "default"
            - 수정시간: DB 값인 경우에만 반환
        """
        # 1. DB에서 조회
        if key in DB_OVERRIDABLE_KEYS:
            db_config = await self.repo.get_by_key(key)
            if db_config is not None:
                parsed_value = self.repo._parse_value(db_config.value)
                return (parsed_value, "db", db_config.updated_at)

        # 2. 환경변수에서 조회
        env_value = getattr(self.settings, key, None)
        if env_value is not None:
            return (env_value, "env", None)

        # 3. 기본값
        return (None, "default", None)

    async def set_and_get(self, key: str, value: Any) -> tuple[Any, datetime]:
        """
        설정값 저장 후 저장된 값과 시간 반환

        Args:
            key: 설정 키
            value: 설정 값

        Returns:
            (파싱된 값, 수정시간) 튜플

        Raises:
            ValueError: DB 오버라이드 불가한 키인 경우
        """
        if key not in DB_OVERRIDABLE_KEYS:
            raise ValueError(f"'{key}'는 DB 저장이 허용되지 않습니다")

        config = await self.repo.set_value(key, value)
        logger.info(f"설정 '{key}' DB에 저장: {value}")
        parsed_value = self.repo._parse_value(config.value)
        return (parsed_value, config.updated_at)

    @staticmethod
    def get_cache_stats() -> dict[str, int | float]:
        """
        설정 캐시 통계 조회

        캐시 히트율 모니터링 및 성능 검증용.
        목표: 히트율 95% 이상

        Returns:
            hits: 캐시 히트 수
            misses: 캐시 미스 수
            hit_rate: 히트율 (%)
            size: 현재 캐시 항목 수
        """
        return get_config_cache().stats()
