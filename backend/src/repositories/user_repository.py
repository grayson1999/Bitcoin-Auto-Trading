"""
사용자 Repository

User 엔티티에 대한 데이터베이스 접근 계층입니다.
Auth Server 사용자와 내부 사용자 매핑을 관리합니다.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entities.user import User
from src.repositories.base import BaseRepository
from src.utils import UTC


class UserRepository(BaseRepository[User]):
    """
    사용자 Repository

    User 엔티티에 대한 CRUD 및 특화된 쿼리 메서드를 제공합니다.

    사용 예시:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_or_create(
                auth_user_id="uuid",
                email="user@example.com",
                name="User"
            )
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Repository 초기화

        Args:
            session: SQLAlchemy 비동기 세션
        """
        super().__init__(session, User)

    async def get_by_auth_user_id(self, auth_user_id: str) -> User | None:
        """
        Auth Server UUID로 사용자 조회

        Args:
            auth_user_id: Auth Server의 사용자 UUID

        Returns:
            사용자 또는 None
        """
        result = await self.session.execute(
            select(User).where(User.auth_user_id == auth_user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        이메일로 사용자 조회

        Args:
            email: 사용자 이메일

        Returns:
            사용자 또는 None
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        auth_user_id: str,
        email: str,
        name: str,
    ) -> User:
        """
        사용자 조회 또는 생성

        Auth Server 사용자가 최초 접근 시 내부 사용자 레코드를 생성합니다.
        이미 존재하면 정보를 동기화(업데이트)합니다.

        Args:
            auth_user_id: Auth Server의 사용자 UUID
            email: 사용자 이메일
            name: 사용자 이름

        Returns:
            기존 또는 새로 생성된 사용자
        """
        user = await self.get_by_auth_user_id(auth_user_id)

        if user is None:
            # 새 사용자 생성
            user = User(
                auth_user_id=auth_user_id,
                email=email,
                name=name,
            )
            self.session.add(user)
            await self.session.flush()
        else:
            # 기존 사용자 정보 동기화
            if user.email != email or user.name != name:
                user.email = email
                user.name = name
                user.updated_at = datetime.now(UTC)
                await self.session.flush()

        return user

    async def get_system_user(self) -> User | None:
        """
        시스템 사용자 조회

        마이그레이션에서 생성된 기본 시스템 사용자를 반환합니다.

        Returns:
            시스템 사용자 또는 None
        """
        return await self.get_by_auth_user_id("00000000-0000-0000-0000-000000000000")

    async def save(self, user: User) -> User:
        """
        사용자 저장

        Args:
            user: 저장할 User 엔티티

        Returns:
            저장된 User (ID 할당됨)
        """
        self.session.add(user)
        await self.session.flush()
        return user
