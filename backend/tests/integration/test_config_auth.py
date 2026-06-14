"""
config/admin 엔드포인트 인증·인가 통합 테스트

C1+C2 회귀 방지:
- /config GET은 로그인 필요 (401 if 무인증)
- /config PATCH/DELETE는 admin 권한 필요 (403 if 일반 user)
- /admin/* 은 admin 권한 필요

권한 거부(401/403)는 의존성 해석 단계에서 발생하므로 DB가 필요 없다.
admin 통과 경로는 ConfigService를 모킹하여 DB 없이 인가 로직만 검증한다.
"""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.app import app
from src.modules.config.routes import get_config_service


def _override_config_service() -> None:
    """ConfigService를 모킹하여 DB 없이 라우트 본문이 실행되도록 한다."""

    service = AsyncMock()
    service.set_and_get = AsyncMock(return_value=("2.5", "2026-06-14T00:00:00"))

    async def _override() -> AsyncMock:
        return service

    app.dependency_overrides[get_config_service] = _override


# === GET /config: 로그인 필요 ===


def test_get_config_unauthenticated_returns_401(client: TestClient) -> None:
    """무인증 GET /config → 401."""
    response = client.get("/api/v1/config/keys")
    assert response.status_code == 401


def test_get_config_keys_authenticated_user_ok(
    mock_auth: None, client: TestClient
) -> None:
    """일반 user GET /config/keys → 200 (로그인만 필요)."""
    response = client.get("/api/v1/config/keys")
    assert response.status_code == 200


# === PATCH /config/{key}: admin 필요 ===


def test_patch_config_unauthenticated_returns_401(client: TestClient) -> None:
    """무인증 PATCH /config/{key} → 401."""
    response = client.patch("/api/v1/config/stop_loss_pct", json={"value": "2.5"})
    assert response.status_code == 401


def test_patch_config_normal_user_returns_403(
    mock_auth: None, client: TestClient
) -> None:
    """일반 user PATCH /config/{key} → 403 (admin 권한 없음)."""
    response = client.patch("/api/v1/config/stop_loss_pct", json={"value": "2.5"})
    assert response.status_code == 403


def test_patch_config_admin_allowed(mock_admin_auth: None, client: TestClient) -> None:
    """admin PATCH /config/{key} → 인가 통과 (403 아님)."""
    _override_config_service()
    try:
        response = client.patch("/api/v1/config/stop_loss_pct", json={"value": "2.5"})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_config_service, None)


# === DELETE /config/{key}: admin 필요 ===


def test_delete_config_normal_user_returns_403(
    mock_auth: None, client: TestClient
) -> None:
    """일반 user DELETE /config/{key} → 403."""
    response = client.delete("/api/v1/config/stop_loss_pct")
    assert response.status_code == 403


# === PATCH /config (batch): admin 필요 ===


def test_batch_patch_config_normal_user_returns_403(
    mock_auth: None, client: TestClient
) -> None:
    """일반 user 배치 PATCH /config → 403."""
    response = client.patch("/api/v1/config", json={"configs": {}})
    assert response.status_code == 403


# === /admin/system: admin 필요 ===


def test_admin_system_unauthenticated_returns_401(client: TestClient) -> None:
    """무인증 GET /admin/system → 401."""
    response = client.get("/api/v1/admin/system")
    assert response.status_code == 401


def test_admin_system_normal_user_returns_403(
    mock_auth: None, client: TestClient
) -> None:
    """일반 user GET /admin/system → 403."""
    response = client.get("/api/v1/admin/system")
    assert response.status_code == 403
