"""
API 의존성 모듈

FastAPI 엔드포인트에서 사용하는 공통 의존성을 정의합니다.
인증, 데이터베이스 세션 등의 의존성을 제공합니다.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_client import AuthError, AuthUser, get_auth_client

# Bearer 토큰 추출을 위한 보안 스키마
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> AuthUser:
    """
    현재 인증된 사용자 정보 반환

    Authorization 헤더에서 Bearer 토큰을 추출하고,
    Auth Server를 통해 토큰을 검증하여 사용자 정보를 반환합니다.

    Args:
        credentials: HTTP Bearer 인증 정보

    Returns:
        AuthUser: 인증된 사용자 정보

    Raises:
        HTTPException: 401 (토큰 없음/무효), 503 (Auth Server 연결 실패)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization 헤더가 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        auth_client = get_auth_client()
        user = await auth_client.verify_token(token)
        return user
    except AuthError as e:
        if e.status_code == 503:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=e.message,
            ) from e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# 타입 별칭: 엔드포인트에서 인증된 사용자를 주입받을 때 사용
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
