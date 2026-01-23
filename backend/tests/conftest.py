"""
pytest 공통 픽스처 모듈

테스트에서 공통으로 사용되는 픽스처를 정의합니다.
- mock_auth: 인증 모킹 (Auth Server 호출 없이 테스트)
- test_client: FastAPI 테스트 클라이언트
"""

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from src.clients import AuthUser

from src.api.deps import get_current_user
from src.main import app

# === 테스트용 사용자 데이터 ===
TEST_USER = AuthUser(
    id="test-user-id-12345",
    email="test@example.com",
    name="Test User",
    role="user",
)

TEST_ADMIN = AuthUser(
    id="test-admin-id-12345",
    email="admin@example.com",
    name="Test Admin",
    role="admin",
)


@pytest.fixture
def mock_auth() -> Generator[None, None, None]:
    """
    인증 모킹 픽스처

    Auth Server 호출 없이 테스트를 실행할 수 있도록
    get_current_user 의존성을 오버라이드합니다.

    기본 테스트 사용자(TEST_USER)를 반환합니다.

    Usage:
        def test_my_endpoint(mock_auth):
            response = client.get("/api/v1/my-endpoint")
            assert response.status_code == 200
    """

    async def override_get_current_user() -> AuthUser:
        return TEST_USER

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_admin_auth() -> Generator[None, None, None]:
    """
    관리자 인증 모킹 픽스처

    관리자 권한이 필요한 엔드포인트 테스트용입니다.

    Usage:
        def test_admin_endpoint(mock_admin_auth):
            response = client.get("/api/v1/admin/users")
            assert response.status_code == 200
    """

    async def override_get_current_user() -> AuthUser:
        return TEST_ADMIN

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth_factory() -> Generator[Callable[[AuthUser], None], None, None]:
    """
    커스텀 사용자 인증 모킹 팩토리 픽스처

    특정 사용자 정보로 테스트가 필요한 경우 사용합니다.

    Usage:
        def test_specific_user(mock_auth_factory, client):
            custom_user = AuthUser(
                id="custom-id",
                email="custom@example.com",
                name="Custom User",
                role="user"
            )
            mock_auth_factory(custom_user)
            response = client.get("/api/v1/my-endpoint")
            assert response.status_code == 200
    """

    def _mock(user: AuthUser = TEST_USER) -> None:
        async def override_get_current_user() -> AuthUser:
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

    yield _mock
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    FastAPI 테스트 클라이언트 픽스처

    Usage:
        def test_health(client):
            response = client.get("/api/v1/health")
            assert response.status_code == 200
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(mock_auth: None) -> Generator[TestClient, None, None]:
    """
    인증된 테스트 클라이언트 픽스처

    mock_auth가 적용된 상태로 테스트 클라이언트를 제공합니다.

    Usage:
        def test_protected_endpoint(authenticated_client):
            response = authenticated_client.get("/api/v1/dashboard/summary")
            assert response.status_code == 200
    """
    with TestClient(app) as test_client:
        yield test_client
