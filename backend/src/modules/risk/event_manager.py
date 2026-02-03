"""
리스크 이벤트 관리 모듈

리스크 이벤트 생성, 조회 및 설정값 관리를 담당합니다.
risk/service.py에서 분리됨.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities import RiskEvent, RiskEventType, SystemConfig
from src.utils import UTC

if TYPE_CHECKING:
    from src.clients.slack_client import SlackClient


class RiskEventManager:
    """
    리스크 이벤트 관리자

    리스크 이벤트 생성, 조회, 설정값 관리를 담당합니다.

    Attributes:
        _db: SQLAlchemy 비동기 세션
        _notifier: Slack 알림 클라이언트 (선택)
    """

    def __init__(
        self,
        db: AsyncSession,
        notifier: "SlackClient | None" = None,
    ) -> None:
        """
        RiskEventManager 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            notifier: Slack 알림 클라이언트 (선택)
        """
        self._db = db
        self._notifier = notifier

    # =========================================================================
    # 리스크 이벤트 조회
    # =========================================================================

    async def get_recent_events(
        self,
        limit: int = 50,
        event_type: RiskEventType | None = None,
    ) -> list[RiskEvent]:
        """
        최근 리스크 이벤트 조회

        Args:
            limit: 조회 개수
            event_type: 이벤트 유형 필터 (선택)

        Returns:
            list[RiskEvent]: 리스크 이벤트 목록
        """
        stmt = select(RiskEvent).order_by(RiskEvent.created_at.desc()).limit(limit)

        if event_type:
            stmt = stmt.where(RiskEvent.event_type == event_type.value)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_events_count(
        self,
        event_type: RiskEventType | None = None,
    ) -> int:
        """
        리스크 이벤트 개수 조회

        Args:
            event_type: 이벤트 유형 필터 (선택)

        Returns:
            int: 이벤트 개수
        """
        stmt = select(func.count(RiskEvent.id))

        if event_type:
            stmt = stmt.where(RiskEvent.event_type == event_type.value)

        result = await self._db.execute(stmt)
        return result.scalar() or 0

    # =========================================================================
    # 설정값 관리
    # =========================================================================

    async def get_config_value(
        self, key: str, default: float | int | bool | str
    ) -> float:
        """설정값 조회"""
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await self._db.execute(stmt)
        config = result.scalar_one_or_none()

        if config is None:
            return float(default) if isinstance(default, (int, float)) else default

        try:
            return float(config.value)
        except ValueError:
            return config.value

    async def set_config_value(self, key: str, value: str) -> None:
        """설정값 저장"""
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await self._db.execute(stmt)
        config = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if config is None:
            config = SystemConfig(key=key, value=value, updated_at=now)
            self._db.add(config)
        else:
            config.value = value
            config.updated_at = now

    # =========================================================================
    # 리스크 이벤트 생성
    # =========================================================================

    async def create_risk_event(
        self,
        event_type: RiskEventType,
        trigger_value: Decimal,
        action_taken: str,
        order_id: int | None = None,
        user_id: int = 1,
    ) -> RiskEvent:
        """
        리스크 이벤트 생성 및 저장

        Args:
            event_type: 이벤트 유형
            trigger_value: 발동 기준값
            action_taken: 수행된 조치
            order_id: 연관 주문 ID (선택)
            user_id: 소유자 사용자 ID (기본값: 1, 시스템 사용자)

        Returns:
            RiskEvent: 생성된 이벤트
        """
        event = RiskEvent(
            user_id=user_id,
            order_id=order_id,
            event_type=event_type.value,
            trigger_value=trigger_value,
            action_taken=action_taken,
            created_at=datetime.now(UTC),
            notified=False,
        )
        self._db.add(event)

        # 리스크 이벤트 로깅
        logger.warning(
            f"리스크 이벤트 발생: [{event_type.value}] "
            f"trigger={trigger_value}, action={action_taken}"
        )

        # 알림 전송 (주요 이벤트만)
        if self._notifier and event_type in (
            RiskEventType.STOP_LOSS,
            RiskEventType.DAILY_LIMIT,
            RiskEventType.VOLATILITY_HALT,
        ):
            await self._notifier.send_alert(
                title=f"⚠️ {event_type.value}",
                message=f"{action_taken}\n발동값: {trigger_value}%",
            )
            event.notified = True

        return event
