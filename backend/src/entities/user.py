"""
사용자 엔티티

Auth Server의 사용자 정보를 내부 시스템과 매핑하는 SQLAlchemy 모델입니다.
- Auth Server UUID → 내부 BigInteger ID 매핑
- 사용자 기본 정보 캐싱 (email, name)
"""

from sqlalchemy import BigInteger, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.entities.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    사용자 모델

    Auth Server의 사용자 정보를 내부 시스템에 매핑합니다.
    JWT 토큰에서 추출한 auth_user_id를 통해 내부 user_id를 조회합니다.

    Attributes:
        id: 내부 사용자 ID (자동 증가)
        auth_user_id: Auth Server의 UUID (UNIQUE)
        email: 사용자 이메일 (캐싱용)
        name: 사용자 이름 (캐싱용)
        created_at: 최초 로그인 시간
        updated_at: 마지막 정보 동기화 시간

    인덱스:
        - idx_users_auth_user_id: Auth Server UUID 조회 (UNIQUE)
        - idx_users_email: 이메일 조회
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    auth_user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        comment="Auth Server UUID",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="사용자 이메일",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="사용자 이름",
    )

    __table_args__ = (
        Index("idx_users_auth_user_id", auth_user_id, unique=True),
        Index("idx_users_email", email),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, auth_user_id={self.auth_user_id})>"
