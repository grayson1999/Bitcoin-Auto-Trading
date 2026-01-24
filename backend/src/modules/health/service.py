"""
상세 헬스체크 서비스

6개 구성요소의 상태를 확인하는 서비스입니다:
1. DB 연결
2. Upbit API
3. Gemini API
4. 스케줄러
5. 최근 신호
6. 최근 주문
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

from loguru import logger
from sqlalchemy import select, text

from src.config import APP_VERSION
from src.entities import Order, TradingSignal
from src.modules.health.schemas import ComponentHealth, DetailedHealthResponse
from src.scheduler import get_scheduler_status
from src.utils import UTC

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class HealthService:
    """
    상세 헬스체크 서비스

    6개 핵심 구성요소의 상태를 확인하고 보고합니다.

    사용 예시:
        async with get_session() as session:
            service = HealthService(session)
            response = await service.check_all()
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: SQLAlchemy 비동기 세션
        """
        self.session = session

    async def check_all(self) -> DetailedHealthResponse:
        """
        모든 구성요소 상태 확인

        Returns:
            DetailedHealthResponse: 전체 헬스체크 결과
        """
        components: list[ComponentHealth] = []

        # 각 구성요소 체크 (순차 실행)
        components.append(await self._check_database())
        components.append(await self._check_upbit_api())
        components.append(await self._check_gemini_api())
        components.append(self._check_scheduler())
        components.append(await self._check_recent_signal())
        components.append(await self._check_recent_order())

        # 전체 상태 결정
        overall_status = self._determine_overall_status(components)

        return DetailedHealthResponse(
            status=overall_status,
            timestamp=datetime.now(UTC),
            version=APP_VERSION,
            components=components,
        )

    async def _check_database(self) -> ComponentHealth:
        """DB 연결 상태 확인 (SELECT 1)"""
        start = time.perf_counter()
        try:
            await self.session.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - start) * 1000

            return ComponentHealth(
                name="database",
                status="healthy",
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            logger.warning(f"DB 헬스체크 실패: {e}")
            return ComponentHealth(
                name="database",
                status="unhealthy",
                message=str(e),
            )

    async def _check_upbit_api(self) -> ComponentHealth:
        """Upbit API 연결 상태 확인"""
        # 순환 참조 방지를 위한 지연 임포트
        from src.clients.upbit import get_upbit_public_api

        start = time.perf_counter()
        try:
            client = get_upbit_public_api()
            # 간단한 API 호출로 연결 확인
            await client.get_ticker("KRW-BTC")
            latency_ms = (time.perf_counter() - start) * 1000

            return ComponentHealth(
                name="upbit_api",
                status="healthy",
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            logger.warning(f"Upbit API 헬스체크 실패: {e}")
            return ComponentHealth(
                name="upbit_api",
                status="unhealthy",
                message=str(e),
            )

    async def _check_gemini_api(self) -> ComponentHealth:
        """Gemini API 연결 상태 확인"""
        # 순환 참조 방지를 위한 지연 임포트
        from src.clients.ai import get_ai_client

        start = time.perf_counter()
        try:
            client = get_ai_client()
            # 간단한 생성 테스트
            await client.generate(prompt="Hello", max_output_tokens=5)
            latency_ms = (time.perf_counter() - start) * 1000

            return ComponentHealth(
                name="gemini_api",
                status="healthy",
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            error_msg = str(e).lower()
            # Rate Limit은 warning으로 처리
            if "rate" in error_msg or "quota" in error_msg or "429" in error_msg:
                return ComponentHealth(
                    name="gemini_api",
                    status="warning",
                    message="Rate limit exceeded",
                )
            logger.warning(f"Gemini API 헬스체크 실패: {e}")
            return ComponentHealth(
                name="gemini_api",
                status="unhealthy",
                message=str(e),
            )

    def _check_scheduler(self) -> ComponentHealth:
        """스케줄러 상태 확인"""
        try:
            status = get_scheduler_status()

            if status.get("running"):
                job_count = len(status.get("jobs", []))
                return ComponentHealth(
                    name="scheduler",
                    status="healthy",
                    message=f"{job_count} jobs registered",
                )
            else:
                return ComponentHealth(
                    name="scheduler",
                    status="unhealthy",
                    message="Scheduler not running",
                )
        except Exception as e:
            logger.warning(f"스케줄러 헬스체크 실패: {e}")
            return ComponentHealth(
                name="scheduler",
                status="unhealthy",
                message=str(e),
            )

    async def _check_recent_signal(self) -> ComponentHealth:
        """최근 1시간 내 신호 존재 여부 확인"""
        try:
            one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
            result = await self.session.execute(
                select(TradingSignal)
                .where(TradingSignal.created_at >= one_hour_ago)
                .limit(1)
            )
            signal = result.scalar_one_or_none()

            if signal:
                return ComponentHealth(
                    name="recent_signal",
                    status="healthy",
                    message=f"Latest: {signal.signal_type}",
                )
            else:
                return ComponentHealth(
                    name="recent_signal",
                    status="warning",
                    message="No signals in last hour",
                )
        except Exception as e:
            logger.warning(f"최근 신호 체크 실패: {e}")
            return ComponentHealth(
                name="recent_signal",
                status="unhealthy",
                message=str(e),
            )

    async def _check_recent_order(self) -> ComponentHealth:
        """활성 주문 상태 확인"""
        try:
            result = await self.session.execute(
                select(Order).where(Order.status == "PENDING").limit(10)
            )
            pending_orders = result.scalars().all()

            if len(pending_orders) == 0:
                return ComponentHealth(
                    name="recent_order",
                    status="healthy",
                    message="No pending orders",
                )
            elif len(pending_orders) < 5:
                return ComponentHealth(
                    name="recent_order",
                    status="healthy",
                    message=f"{len(pending_orders)} pending orders",
                )
            else:
                return ComponentHealth(
                    name="recent_order",
                    status="warning",
                    message=f"{len(pending_orders)} pending orders (high)",
                )
        except Exception as e:
            logger.warning(f"주문 상태 체크 실패: {e}")
            return ComponentHealth(
                name="recent_order",
                status="unhealthy",
                message=str(e),
            )

    def _determine_overall_status(
        self, components: list[ComponentHealth]
    ) -> Literal["healthy", "unhealthy", "degraded"]:
        """
        전체 시스템 상태 결정

        - healthy: 모든 구성요소가 healthy
        - degraded: 일부 구성요소가 warning 또는 비핵심 구성요소 unhealthy
        - unhealthy: 핵심 구성요소(DB, scheduler)가 unhealthy
        """
        # 핵심 구성요소 (unhealthy면 전체 unhealthy)
        critical_components = {"database", "scheduler"}

        has_unhealthy = False
        has_warning = False

        for component in components:
            if component.status == "unhealthy":
                if component.name in critical_components:
                    return "unhealthy"
                has_unhealthy = True
            elif component.status == "warning":
                has_warning = True

        if has_unhealthy or has_warning:
            return "degraded"

        return "healthy"
