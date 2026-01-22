"""
리스크 관리 서비스

이 모듈은 거래 리스크 관리를 담당하는 서비스를 제공합니다.
- 포지션 크기 검증
- 개별 손절 체크
- 일일 손실 한도 체크
- 변동성 감지
- 리스크 이벤트 로깅

기존 파일: services/risk_manager.py
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.config.constants import RISK_WARNING_THRESHOLD_RATIO
from src.entities import (
    DailyStats,
    MarketData,
    Position,
    RiskEvent,
    RiskEventType,
    SystemConfig,
)
from src.utils import UTC

if TYPE_CHECKING:
    from src.clients.slack_client import SlackClient


class RiskCheckResult(str, Enum):
    """리스크 체크 결과"""

    PASS = "PASS"  # 통과
    BLOCKED = "BLOCKED"  # 거래 차단
    WARNING = "WARNING"  # 경고 (거래 가능)


@dataclass
class RiskStatus:
    """현재 리스크 상태"""

    trading_enabled: bool
    daily_loss_pct: float
    daily_loss_limit_pct: float
    position_size_pct: float
    stop_loss_pct: float
    volatility_threshold_pct: float
    current_volatility_pct: float
    is_halted: bool
    halt_reason: str | None
    last_check_at: datetime


@dataclass
class PositionCheckResult:
    """포지션 크기 검증 결과"""

    result: RiskCheckResult
    max_amount: Decimal
    requested_amount: Decimal
    message: str


@dataclass
class StopLossCheckResult:
    """손절 체크 결과"""

    result: RiskCheckResult
    current_loss_pct: float
    stop_loss_threshold_pct: float
    should_close: bool
    message: str


class RiskServiceError(Exception):
    """리스크 서비스 오류"""

    pass


class RiskService:
    """
    리스크 관리 서비스

    거래 전 리스크 체크, 손절매 감시, 일일 손실 한도 관리 등을 수행합니다.

    Attributes:
        _db: SQLAlchemy 비동기 세션
        _notifier: 알림 서비스 (선택)
    """

    def __init__(
        self,
        db: AsyncSession,
        notifier: "SlackClient | None" = None,
    ) -> None:
        """
        RiskService 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            notifier: 알림 서비스 (선택)
        """
        self._db = db
        self._notifier = notifier

    # =========================================================================
    # 포지션 크기 검증
    # =========================================================================

    async def check_position_size(
        self,
        requested_amount: Decimal,
        total_balance: Decimal,
    ) -> PositionCheckResult:
        """
        포지션 크기 검증

        주문 금액이 설정된 포지션 크기 비율을 초과하는지 확인합니다.

        Args:
            requested_amount: 주문 요청 금액 (KRW)
            total_balance: 전체 잔고 (KRW)

        Returns:
            PositionCheckResult: 검증 결과
        """
        # 동적 포지션 사이징의 최대값을 리스크 한도로 사용
        position_size_max_pct = await self._get_config_value(
            "position_size_max_pct", settings.position_size_max_pct
        )
        max_amount = total_balance * Decimal(str(position_size_max_pct)) / Decimal("100")

        if requested_amount > max_amount:
            message = (
                f"포지션 크기 초과: 요청 {requested_amount:,.0f}원 > "
                f"최대 {max_amount:,.0f}원 ({position_size_max_pct}%)"
            )
            logger.warning(message)

            # 리스크 이벤트 기록
            await self._create_risk_event(
                event_type=RiskEventType.POSITION_LIMIT,
                trigger_value=Decimal(str(position_size_max_pct)),
                action_taken=f"주문 거부: {requested_amount:,.0f}원 초과",
            )

            return PositionCheckResult(
                result=RiskCheckResult.BLOCKED,
                max_amount=max_amount,
                requested_amount=requested_amount,
                message=message,
            )

        return PositionCheckResult(
            result=RiskCheckResult.PASS,
            max_amount=max_amount,
            requested_amount=requested_amount,
            message=f"포지션 크기 적합: {requested_amount:,.0f}원 <= {max_amount:,.0f}원",
        )

    # =========================================================================
    # 개별 손절 체크
    # =========================================================================

    async def check_stop_loss(
        self,
        position: Position,
        current_price: Decimal,
    ) -> StopLossCheckResult:
        """
        개별 손절 체크

        포지션의 현재 손실률이 손절 임계값을 초과하는지 확인합니다.

        Args:
            position: 현재 포지션
            current_price: 현재 가격

        Returns:
            StopLossCheckResult: 손절 체크 결과
        """
        stop_loss_pct = await self._get_config_value(
            "stop_loss_pct", settings.stop_loss_pct
        )

        # 포지션이 없거나 수량이 0인 경우
        if position.quantity == 0:
            return StopLossCheckResult(
                result=RiskCheckResult.PASS,
                current_loss_pct=0.0,
                stop_loss_threshold_pct=stop_loss_pct,
                should_close=False,
                message="포지션 없음",
            )

        # 손실률 계산
        cost_basis = position.avg_buy_price * position.quantity
        current_value = current_price * position.quantity
        loss_pct = float(((current_value - cost_basis) / cost_basis) * 100)

        # 손실인 경우 음수, 손절 임계값과 비교
        if loss_pct < -stop_loss_pct:
            message = f"손절 발동: 현재 손실 {loss_pct:.2f}% < -{stop_loss_pct}%"
            logger.warning(message)

            # 리스크 이벤트 기록
            await self._create_risk_event(
                event_type=RiskEventType.STOP_LOSS,
                trigger_value=Decimal(str(abs(loss_pct))),
                action_taken=f"손절 주문 실행 권장: {position.quantity} BTC",
            )

            return StopLossCheckResult(
                result=RiskCheckResult.BLOCKED,
                current_loss_pct=loss_pct,
                stop_loss_threshold_pct=stop_loss_pct,
                should_close=True,
                message=message,
            )

        # 경고 수준 (손절 임계값의 80%)
        warning_threshold = -stop_loss_pct * RISK_WARNING_THRESHOLD_RATIO
        if loss_pct < warning_threshold:
            message = (
                f"손절 경고: 현재 손실 {loss_pct:.2f}% (임계값: -{stop_loss_pct}%)"
            )
            logger.info(message)
            return StopLossCheckResult(
                result=RiskCheckResult.WARNING,
                current_loss_pct=loss_pct,
                stop_loss_threshold_pct=stop_loss_pct,
                should_close=False,
                message=message,
            )

        return StopLossCheckResult(
            result=RiskCheckResult.PASS,
            current_loss_pct=loss_pct,
            stop_loss_threshold_pct=stop_loss_pct,
            should_close=False,
            message=f"손익률: {loss_pct:+.2f}%",
        )

    # =========================================================================
    # 일일 손실 한도 체크
    # =========================================================================

    async def check_daily_loss_limit(self) -> tuple[RiskCheckResult, str]:
        """
        일일 손실 한도 체크

        오늘의 실현 손실이 일일 손실 한도를 초과하는지 확인합니다.

        Returns:
            tuple[RiskCheckResult, str]: (결과, 메시지)
        """
        daily_loss_limit_pct = await self._get_config_value(
            "daily_loss_limit_pct", settings.daily_loss_limit_pct
        )

        # 오늘 일별 통계 조회
        today = date.today()
        stmt = select(DailyStats).where(DailyStats.date == today)
        result = await self._db.execute(stmt)
        daily_stats = result.scalar_one_or_none()

        # 통계가 없으면 거래 가능
        if daily_stats is None:
            return (
                RiskCheckResult.PASS,
                "오늘 거래 통계 없음 - 거래 가능",
            )

        # 이미 거래 중단 상태인 경우
        if daily_stats.is_trading_halted:
            return (
                RiskCheckResult.BLOCKED,
                f"거래 중단 상태: {daily_stats.halt_reason}",
            )

        # 일일 손실률 계산
        loss_pct = daily_stats.loss_pct

        if loss_pct < -daily_loss_limit_pct:
            message = f"일일 손실 한도 도달: {loss_pct:.2f}% < -{daily_loss_limit_pct}%"
            logger.warning(message)

            # 거래 중단 상태 업데이트
            daily_stats.is_trading_halted = True
            daily_stats.halt_reason = f"일일 손실 한도 도달 ({loss_pct:.2f}%)"

            # 리스크 이벤트 기록
            await self._create_risk_event(
                event_type=RiskEventType.DAILY_LIMIT,
                trigger_value=Decimal(str(abs(loss_pct))),
                action_taken="거래 중단",
            )

            return (RiskCheckResult.BLOCKED, message)

        # 경고 수준 (한도의 80%)
        warning_threshold = -daily_loss_limit_pct * RISK_WARNING_THRESHOLD_RATIO
        if loss_pct < warning_threshold:
            message = (
                f"일일 손실 경고: {loss_pct:.2f}% (한도: -{daily_loss_limit_pct}%)"
            )
            logger.info(message)
            return (RiskCheckResult.WARNING, message)

        return (
            RiskCheckResult.PASS,
            f"일일 손익: {loss_pct:+.2f}% (한도: -{daily_loss_limit_pct}%)",
        )

    # =========================================================================
    # 변동성 감지
    # =========================================================================

    async def check_volatility(
        self, window_minutes: int = 5
    ) -> tuple[RiskCheckResult, float, str]:
        """
        변동성 감지

        지정된 시간 윈도우 내의 가격 변동률을 확인합니다.
        임계값을 초과하면 거래를 중단합니다.

        Args:
            window_minutes: 변동성 측정 윈도우 (분, 기본 5분)

        Returns:
            tuple[RiskCheckResult, float, str]: (결과, 변동률, 메시지)
        """
        volatility_threshold_pct = await self._get_config_value(
            "volatility_threshold_pct", settings.volatility_threshold_pct
        )

        # 최근 N분간의 시장 데이터 조회
        now = datetime.now(UTC)
        window_start = now.replace(second=0, microsecond=0) - timedelta(
            minutes=window_minutes
        )

        stmt = select(
            func.min(MarketData.price).label("min_price"),
            func.max(MarketData.price).label("max_price"),
        ).where(MarketData.timestamp >= window_start)
        result = await self._db.execute(stmt)
        row = result.one_or_none()

        if row is None or row.min_price is None or row.max_price is None:
            return (
                RiskCheckResult.PASS,
                0.0,
                f"최근 {window_minutes}분 데이터 부족",
            )

        min_price = Decimal(str(row.min_price))
        max_price = Decimal(str(row.max_price))

        # 변동률 계산 ((max - min) / min * 100)
        if min_price == 0:
            return (RiskCheckResult.PASS, 0.0, "최저가 0 - 계산 불가")

        volatility_pct = float(((max_price - min_price) / min_price) * 100)

        if volatility_pct > volatility_threshold_pct:
            message = (
                f"변동성 감지: {volatility_pct:.2f}% > {volatility_threshold_pct}% "
                f"(최근 {window_minutes}분)"
            )
            logger.warning(message)

            # 리스크 이벤트 기록
            await self._create_risk_event(
                event_type=RiskEventType.VOLATILITY_HALT,
                trigger_value=Decimal(str(volatility_pct)),
                action_taken=f"거래 중단 권장: {window_minutes}분 내 {volatility_pct:.2f}% 변동",
            )

            return (RiskCheckResult.BLOCKED, volatility_pct, message)

        # 경고 수준 (임계값의 80%)
        warning_threshold = volatility_threshold_pct * RISK_WARNING_THRESHOLD_RATIO
        if volatility_pct > warning_threshold:
            message = (
                f"변동성 경고: {volatility_pct:.2f}% "
                f"(임계값: {volatility_threshold_pct}%)"
            )
            logger.info(message)
            return (RiskCheckResult.WARNING, volatility_pct, message)

        return (
            RiskCheckResult.PASS,
            volatility_pct,
            f"변동성 정상: {volatility_pct:.2f}% < {volatility_threshold_pct}%",
        )

    # =========================================================================
    # 거래 중단/재개
    # =========================================================================

    async def halt_trading(self, reason: str) -> None:
        """
        거래 중단

        Args:
            reason: 중단 사유
        """
        await self._set_config_value("trading_enabled", "false")

        # 오늘 일별 통계 업데이트
        today = date.today()
        stmt = select(DailyStats).where(DailyStats.date == today)
        result = await self._db.execute(stmt)
        daily_stats = result.scalar_one_or_none()

        if daily_stats:
            daily_stats.is_trading_halted = True
            daily_stats.halt_reason = reason

        logger.warning(f"거래 중단: {reason}")

        # 알림 전송
        if self._notifier:
            await self._notifier.send_alert(
                title="⚠️ 거래 중단",
                message=reason,
            )

    async def resume_trading(self) -> None:
        """거래 재개"""
        await self._set_config_value("trading_enabled", "true")

        # 오늘 일별 통계 업데이트
        today = date.today()
        stmt = select(DailyStats).where(DailyStats.date == today)
        result = await self._db.execute(stmt)
        daily_stats = result.scalar_one_or_none()

        if daily_stats:
            daily_stats.is_trading_halted = False
            daily_stats.halt_reason = None

        logger.info("거래 재개")

        # 알림 전송
        if self._notifier:
            await self._notifier.send_alert(
                title="✅ 거래 재개",
                message="거래가 재개되었습니다.",
            )

    async def is_trading_enabled(self) -> bool:
        """거래 가능 여부 확인"""
        enabled = await self._get_config_value("trading_enabled", True)
        if isinstance(enabled, str):
            return enabled.lower() == "true"
        return bool(enabled)

    # =========================================================================
    # 리스크 상태 조회
    # =========================================================================

    async def get_risk_status(self) -> RiskStatus:
        """
        현재 리스크 상태 조회

        Returns:
            RiskStatus: 현재 리스크 상태
        """
        trading_enabled = await self.is_trading_enabled()

        # 설정값 조회
        daily_loss_limit_pct = await self._get_config_value(
            "daily_loss_limit_pct", settings.daily_loss_limit_pct
        )
        position_size_pct = await self._get_config_value(
            "position_size_max_pct", settings.position_size_max_pct
        )
        stop_loss_pct = await self._get_config_value(
            "stop_loss_pct", settings.stop_loss_pct
        )
        volatility_threshold_pct = await self._get_config_value(
            "volatility_threshold_pct", settings.volatility_threshold_pct
        )

        # 일일 손익률 조회
        today = date.today()
        stmt = select(DailyStats).where(DailyStats.date == today)
        result = await self._db.execute(stmt)
        daily_stats = result.scalar_one_or_none()

        daily_loss_pct = 0.0
        is_halted = False
        halt_reason = None

        if daily_stats:
            daily_loss_pct = daily_stats.loss_pct
            is_halted = daily_stats.is_trading_halted
            halt_reason = daily_stats.halt_reason

        # 현재 변동성 조회
        _, current_volatility_pct, _ = await self.check_volatility()

        return RiskStatus(
            trading_enabled=trading_enabled,
            daily_loss_pct=daily_loss_pct,
            daily_loss_limit_pct=daily_loss_limit_pct,
            position_size_pct=position_size_pct,
            stop_loss_pct=stop_loss_pct,
            volatility_threshold_pct=volatility_threshold_pct,
            current_volatility_pct=current_volatility_pct,
            is_halted=is_halted,
            halt_reason=halt_reason,
            last_check_at=datetime.now(UTC),
        )

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
    # 내부 헬퍼 메서드
    # =========================================================================

    async def _get_config_value(
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

    async def _set_config_value(self, key: str, value: str) -> None:
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

    async def _create_risk_event(
        self,
        event_type: RiskEventType,
        trigger_value: Decimal,
        action_taken: str,
        order_id: int | None = None,
    ) -> RiskEvent:
        """
        리스크 이벤트 생성 및 저장

        Args:
            event_type: 이벤트 유형
            trigger_value: 발동 기준값
            action_taken: 수행된 조치
            order_id: 연관 주문 ID (선택)

        Returns:
            RiskEvent: 생성된 이벤트
        """
        event = RiskEvent(
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


# === 팩토리 함수 ===
def get_risk_service(
    db: AsyncSession,
    notifier: "SlackClient | None" = None,
) -> RiskService:
    """
    RiskService 인스턴스 생성

    Args:
        db: SQLAlchemy 비동기 세션
        notifier: 알림 서비스 (선택)

    Returns:
        RiskService 인스턴스
    """
    return RiskService(db, notifier)
