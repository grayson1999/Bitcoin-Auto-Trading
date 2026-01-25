"""
Auth Server 클라이언트 모듈

Auth Server와 통신하여 토큰 검증을 수행하는 HTTP 클라이언트입니다.
싱글톤 패턴으로 구현되어 애플리케이션 전체에서 하나의 인스턴스를 공유합니다.
"""

from typing import ClassVar

import httpx
from loguru import logger
from pydantic import BaseModel

from src.config import settings


class AuthError(Exception):
    """
    Auth Server 관련 오류

    인증 실패, 토큰 무효, Auth Server 연결 실패 등의 오류를 나타냅니다.

    Attributes:
        message: 오류 메시지
        status_code: HTTP 상태 코드 (기본값: 401)
    """

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthUser(BaseModel):
    """
    Auth Server에서 검증된 사용자 정보

    토큰 검증 성공 시 반환되는 사용자 정보 스키마입니다.

    Attributes:
        id: 사용자 고유 ID (UUID)
        email: 이메일 주소
        name: 사용자 이름
        role: 역할 (admin/user)
    """

    id: str
    email: str
    name: str
    role: str

    model_config = {"frozen": True}


class AuthClient:
    """
    Auth Server HTTP 클라이언트

    Auth Server의 토큰 검증 API를 호출하여 액세스 토큰의 유효성을 확인합니다.
    싱글톤 패턴으로 구현되어 연결 풀을 재사용합니다.

    Attributes:
        _instance: 싱글톤 인스턴스
        _client: httpx 비동기 클라이언트
    """

    _instance: ClassVar["AuthClient | None"] = None

    def __init__(self, base_url: str):
        """
        AuthClient 초기화

        Args:
            base_url: Auth Server URL (예: http://localhost:9000)
        """
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(5.0, connect=3.0),
            http2=False,  # HTTP/1.1 강제 (RemoteProtocolError 방지)
            limits=httpx.Limits(
                max_keepalive_connections=5,
                keepalive_expiry=30.0,  # 30초 후 연결 만료
            ),
        )
        logger.info(f"AuthClient 초기화 완료: {base_url}")

    async def verify_token(self, token: str, max_retries: int = 2) -> AuthUser:
        """
        액세스 토큰 검증

        Auth Server의 /api/v1/auth/verify 엔드포인트를 호출하여
        토큰의 유효성을 검증하고 사용자 정보를 반환합니다.
        연결 오류 시 재시도를 수행합니다.

        Args:
            token: Bearer 액세스 토큰
            max_retries: 최대 재시도 횟수 (기본값: 2)

        Returns:
            AuthUser: 검증된 사용자 정보

        Raises:
            AuthError: 토큰 무효 (401), Auth Server 연결 실패 (503)
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = await self._client.get(
                    "/api/v1/auth/verify",
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("is_valid"):
                        user_data = data.get("user", {})
                        return AuthUser(
                            id=user_data.get("id", ""),
                            email=user_data.get("email", ""),
                            name=user_data.get("name", ""),
                            role=user_data.get("role", "user"),
                        )
                    raise AuthError("토큰이 유효하지 않습니다", 401)

                if response.status_code == 401:
                    detail = response.json().get("detail", "인증 실패")
                    raise AuthError(detail, 401)

                raise AuthError(
                    f"토큰 검증 실패: {response.status_code}", response.status_code
                )

            except httpx.ConnectError as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        f"Auth Server 연결 실패, 재시도 ({attempt + 1}/{max_retries}): {e}"
                    )
                    continue
                logger.error(f"Auth Server 연결 실패: {e}")
                raise AuthError("인증 서버에 연결할 수 없습니다", 503) from e
            except httpx.RemoteProtocolError as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        f"Auth Server 프로토콜 오류, 재시도 ({attempt + 1}/{max_retries}): {e}"
                    )
                    continue
                logger.error(f"Auth Server 프로토콜 오류: {e}")
                raise AuthError("인증 서버 연결이 끊어졌습니다", 503) from e
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        f"Auth Server 타임아웃, 재시도 ({attempt + 1}/{max_retries}): {e}"
                    )
                    continue
                logger.error(f"Auth Server 타임아웃: {e}")
                raise AuthError("인증 서버 응답 시간 초과", 503) from e
            except httpx.HTTPError as e:
                logger.error(f"Auth Server HTTP 오류: {e}")
                raise AuthError("인증 서버 오류", 503) from e

        # 이 지점에 도달하면 안 되지만, 안전을 위해 추가
        raise AuthError("인증 서버 오류", 503) from last_error

    async def close(self) -> None:
        """HTTP 클라이언트 연결 종료"""
        await self._client.aclose()
        logger.info("AuthClient 연결 종료")


def get_auth_client() -> AuthClient:
    """
    AuthClient 싱글톤 인스턴스 반환

    애플리케이션 전체에서 하나의 AuthClient 인스턴스를 공유합니다.
    처음 호출 시 인스턴스를 생성하고, 이후에는 기존 인스턴스를 반환합니다.

    Returns:
        AuthClient: 싱글톤 AuthClient 인스턴스
    """
    if AuthClient._instance is None:
        AuthClient._instance = AuthClient(settings.auth_server_url)
    return AuthClient._instance


async def close_auth_client() -> None:
    """
    AuthClient 싱글톤 인스턴스 종료

    애플리케이션 종료 시 호출하여 HTTP 연결을 정리합니다.
    """
    if AuthClient._instance is not None:
        await AuthClient._instance.close()
        AuthClient._instance = None
