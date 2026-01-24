"""
상세 헬스체크 통합 테스트

/api/v1/health/detail 엔드포인트 테스트:
- 6개 구성요소 상태 반환 확인
- 응답 스키마 검증
- 전체 상태 결정 로직 검증
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.health.schemas import ComponentHealth, DetailedHealthResponse
from src.modules.health.service import HealthService


class TestHealthService:
    """HealthService 통합 테스트"""

    @pytest.mark.asyncio
    async def test_check_all_returns_6_components(self) -> None:
        """6개 구성요소 상태를 반환해야 함"""
        # Mock session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        # Mock 결과 설정
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = HealthService(mock_session)

        # 외부 API 호출 모킹
        with (
            patch(
                "src.clients.upbit.get_upbit_public_api"
            ) as mock_upbit,
            patch("src.clients.ai.get_ai_client") as mock_ai,
            patch("src.scheduler.get_scheduler_status") as mock_scheduler,
        ):
            # Upbit 클라이언트 모킹
            mock_upbit_client = AsyncMock()
            mock_upbit_client.get_ticker = AsyncMock(return_value={"price": 100000000})
            mock_upbit.return_value = mock_upbit_client

            # AI 클라이언트 모킹
            mock_ai_client = AsyncMock()
            mock_ai_client.generate = AsyncMock(return_value=MagicMock(text="Hello"))
            mock_ai.return_value = mock_ai_client

            # 스케줄러 모킹
            mock_scheduler.return_value = {"running": True, "jobs": [1, 2, 3]}

            response = await service.check_all()

        # 6개 구성요소 확인
        assert len(response.components) == 6

        # 구성요소 이름 확인
        component_names = {c.name for c in response.components}
        expected_names = {
            "database",
            "upbit_api",
            "gemini_api",
            "scheduler",
            "recent_signal",
            "recent_order",
        }
        assert component_names == expected_names

    @pytest.mark.asyncio
    async def test_response_schema_validation(self) -> None:
        """응답 스키마가 올바른 형식이어야 함"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = HealthService(mock_session)

        with (
            patch(
                "src.clients.upbit.get_upbit_public_api"
            ) as mock_upbit,
            patch("src.clients.ai.get_ai_client") as mock_ai,
            patch("src.scheduler.get_scheduler_status") as mock_scheduler,
        ):
            mock_upbit_client = AsyncMock()
            mock_upbit_client.get_ticker = AsyncMock()
            mock_upbit.return_value = mock_upbit_client

            mock_ai_client = AsyncMock()
            mock_ai_client.generate = AsyncMock()
            mock_ai.return_value = mock_ai_client

            mock_scheduler.return_value = {"running": True, "jobs": []}

            response = await service.check_all()

        # 응답 타입 확인
        assert isinstance(response, DetailedHealthResponse)
        assert isinstance(response.timestamp, datetime)
        assert response.status in ("healthy", "unhealthy", "degraded")
        assert isinstance(response.version, str)

        # 구성요소 스키마 확인
        for component in response.components:
            assert isinstance(component, ComponentHealth)
            assert component.status in ("healthy", "unhealthy", "warning")


class TestHealthServiceStatusDetermination:
    """전체 상태 결정 로직 테스트"""

    def test_all_healthy_returns_healthy(self) -> None:
        """모든 구성요소가 healthy면 전체 상태도 healthy"""
        components = [
            ComponentHealth(name="database", status="healthy"),
            ComponentHealth(name="upbit_api", status="healthy"),
            ComponentHealth(name="gemini_api", status="healthy"),
            ComponentHealth(name="scheduler", status="healthy"),
            ComponentHealth(name="recent_signal", status="healthy"),
            ComponentHealth(name="recent_order", status="healthy"),
        ]

        service = HealthService(AsyncMock())
        status = service._determine_overall_status(components)

        assert status == "healthy"

    def test_critical_unhealthy_returns_unhealthy(self) -> None:
        """핵심 구성요소(database)가 unhealthy면 전체 상태도 unhealthy"""
        components = [
            ComponentHealth(name="database", status="unhealthy"),
            ComponentHealth(name="upbit_api", status="healthy"),
            ComponentHealth(name="gemini_api", status="healthy"),
            ComponentHealth(name="scheduler", status="healthy"),
            ComponentHealth(name="recent_signal", status="healthy"),
            ComponentHealth(name="recent_order", status="healthy"),
        ]

        service = HealthService(AsyncMock())
        status = service._determine_overall_status(components)

        assert status == "unhealthy"

    def test_scheduler_unhealthy_returns_unhealthy(self) -> None:
        """핵심 구성요소(scheduler)가 unhealthy면 전체 상태도 unhealthy"""
        components = [
            ComponentHealth(name="database", status="healthy"),
            ComponentHealth(name="upbit_api", status="healthy"),
            ComponentHealth(name="gemini_api", status="healthy"),
            ComponentHealth(name="scheduler", status="unhealthy"),
            ComponentHealth(name="recent_signal", status="healthy"),
            ComponentHealth(name="recent_order", status="healthy"),
        ]

        service = HealthService(AsyncMock())
        status = service._determine_overall_status(components)

        assert status == "unhealthy"

    def test_non_critical_unhealthy_returns_degraded(self) -> None:
        """비핵심 구성요소가 unhealthy면 전체 상태는 degraded"""
        components = [
            ComponentHealth(name="database", status="healthy"),
            ComponentHealth(name="upbit_api", status="unhealthy"),
            ComponentHealth(name="gemini_api", status="healthy"),
            ComponentHealth(name="scheduler", status="healthy"),
            ComponentHealth(name="recent_signal", status="healthy"),
            ComponentHealth(name="recent_order", status="healthy"),
        ]

        service = HealthService(AsyncMock())
        status = service._determine_overall_status(components)

        assert status == "degraded"

    def test_warning_returns_degraded(self) -> None:
        """warning 상태가 있으면 전체 상태는 degraded"""
        components = [
            ComponentHealth(name="database", status="healthy"),
            ComponentHealth(name="upbit_api", status="healthy"),
            ComponentHealth(name="gemini_api", status="warning"),
            ComponentHealth(name="scheduler", status="healthy"),
            ComponentHealth(name="recent_signal", status="warning"),
            ComponentHealth(name="recent_order", status="healthy"),
        ]

        service = HealthService(AsyncMock())
        status = service._determine_overall_status(components)

        assert status == "degraded"


class TestComponentHealthChecks:
    """개별 구성요소 체크 테스트"""

    @pytest.mark.asyncio
    async def test_database_check_healthy(self) -> None:
        """DB 연결 성공 시 healthy 반환"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        service = HealthService(mock_session)
        result = await service._check_database()

        assert result.name == "database"
        assert result.status == "healthy"
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_database_check_unhealthy_on_error(self) -> None:
        """DB 연결 실패 시 unhealthy 반환"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Connection failed"))

        service = HealthService(mock_session)
        result = await service._check_database()

        assert result.name == "database"
        assert result.status == "unhealthy"
        assert "Connection failed" in (result.message or "")

    def test_scheduler_check_running(self) -> None:
        """스케줄러 실행 중이면 healthy 반환"""
        with patch("src.modules.health.service.get_scheduler_status") as mock:
            mock.return_value = {"running": True, "jobs": [1, 2, 3, 4, 5]}

            service = HealthService(AsyncMock())
            result = service._check_scheduler()

        assert result.name == "scheduler"
        assert result.status == "healthy"
        assert "5 jobs" in (result.message or "")

    def test_scheduler_check_not_running(self) -> None:
        """스케줄러 중지 시 unhealthy 반환"""
        with patch("src.modules.health.service.get_scheduler_status") as mock:
            mock.return_value = {"running": False, "jobs": []}

            service = HealthService(AsyncMock())
            result = service._check_scheduler()

        assert result.name == "scheduler"
        assert result.status == "unhealthy"
