"""
민감 읽기 엔드포인트 admin 인가 (M10) 통합 테스트

대시보드/잔고/포지션/주문 등 소유자 금융 데이터 노출 엔드포인트가
admin 권한을 요구하는지 검증한다 (일반 user → 403).
"""

from fastapi.testclient import TestClient

SENSITIVE_GET_ENDPOINTS = [
    "/api/v1/dashboard/summary",
    "/api/v1/trading/balance",
    "/api/v1/trading/position",
    "/api/v1/trading/orders",
]


def test_sensitive_endpoints_unauthenticated_401(client: TestClient) -> None:
    """무인증 → 401."""
    for ep in SENSITIVE_GET_ENDPOINTS:
        resp = client.get(ep)
        assert resp.status_code == 401, f"{ep} expected 401, got {resp.status_code}"


def test_sensitive_endpoints_normal_user_403(
    mock_auth: None, client: TestClient
) -> None:
    """일반 user → 403 (admin 권한 없음)."""
    for ep in SENSITIVE_GET_ENDPOINTS:
        resp = client.get(ep)
        assert resp.status_code == 403, f"{ep} expected 403, got {resp.status_code}"


def test_sensitive_endpoints_admin_passes_authz(
    mock_admin_auth: None, client: TestClient
) -> None:
    """admin → 인가 통과 (403이 아님; DB/Upbit 미연결로 200은 아닐 수 있음)."""
    for ep in SENSITIVE_GET_ENDPOINTS:
        resp = client.get(ep)
        assert resp.status_code != 403, (
            f"{ep} admin should not be 403, got {resp.status_code}"
        )
        assert resp.status_code != 401, (
            f"{ep} admin should not be 401, got {resp.status_code}"
        )
