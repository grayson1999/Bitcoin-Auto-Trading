"""
API 의존성 모듈

FastAPI 엔드포인트에서 사용하는 공통 의존성을 정의합니다.
인증, 데이터베이스 세션 등의 의존성을 제공합니다.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients import AuthError, AuthUser, get_auth_client
from src.config import settings
from src.entities.user import User
from src.repositories.user_repository import UserRepository
from src.utils.database import get_session

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


async def require_admin(current_user: CurrentUser) -> AuthUser:
    """
    관리자 권한 검증 의존성

    role이 'admin'이거나, 락아웃 방지를 위해 settings.admin_emails에 등록된
    이메일이면 통과합니다. 그렇지 않으면 403을 반환합니다.

    Args:
        current_user: 인증된 사용자 정보

    Returns:
        AuthUser: 관리자 권한이 확인된 사용자

    Raises:
        HTTPException: 403 (관리자 권한 없음)
    """
    if current_user.role == "admin":
        return current_user
    # 오너 락아웃 방지 폴백: Auth Server role이 admin이 아니어도
    # 환경변수에 등록된 이메일은 관리자로 인정
    if current_user.email and current_user.email.lower() in settings.admin_emails:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="관리자 권한이 필요합니다",
    )


# 타입 별칭: 엔드포인트에서 관리자 권한을 강제할 때 사용
AdminUser = Annotated[AuthUser, Depends(require_admin)]


async def resolve_user(
    auth_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Auth Server 사용자를 내부 User 엔티티로 변환

    Auth Server에서 인증된 사용자 정보를 내부 DB의 User 엔티티로 매핑합니다.
    최초 접근 시 자동으로 User 레코드를 생성합니다.

    Args:
        auth_user: Auth Server에서 검증된 사용자 정보
        session: 데이터베이스 세션

    Returns:
        User: 내부 사용자 엔티티
    """
    repo = UserRepository(session)
    user = await repo.get_or_create(
        auth_user_id=auth_user.id,
        email=auth_user.email,
        name=auth_user.name,
    )
    return user


# 타입 별칭: 엔드포인트에서 내부 User 엔티티를 주입받을 때 사용
ResolvedUser = Annotated[User, Depends(resolve_user)]
