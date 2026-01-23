"""
사용자 설정 엔티티

사용자별 개인 설정을 저장하는 SQLAlchemy 모델입니다.
system_configs의 기본값을 사용자별로 오버라이드할 수 있습니다.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entities.base import Base


class UserConfig(Base):
    """
    사용자 설정 모델

    사용자별 개인 설정을 키-값 형태로 저장합니다.
    system_configs의 기본값을 오버라이드하는 용도로 사용됩니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        user_id: 사용자 ID (FK)
        key: 설정 키
        value: 설정 값 (JSON 문자열)
        created_at: 생성 시간
        updated_at: 수정 시간
        created_by: 생성자 ID
        updated_by: 수정자 ID

    제약조건:
        - UNIQUE(user_id, key): 사용자별 설정 키 유일성

    인덱스:
        - idx_user_configs_user_key: 사용자별 설정 조회 (UNIQUE)
        - idx_user_configs_updated: 수정 시간순 조회
    """

    __tablename__ = "user_configs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="사용자 ID",
    )

    key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="설정 키",
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="설정 값 (JSON)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        comment="생성 시간",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        comment="수정 시간",
    )

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="생성자 ID",
    )

    updated_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="수정자 ID",
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_configs_user_key"),
        Index("idx_user_configs_user_id", user_id),
        Index("idx_user_configs_updated", updated_at.desc()),
    )

    def __repr__(self) -> str:
        if self.value and len(self.value) > 30:
            value_preview = self.value[:30] + "..."
        else:
            value_preview = self.value or ""
        return f"<UserConfig(user_id={self.user_id}, key={self.key}, value={value_preview})>"
