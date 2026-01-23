"""
엔티티 기본 클래스

모든 SQLAlchemy ORM 모델의 기본 클래스와 공통 믹스인을 정의합니다.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy 모델 기본 클래스

    모든 데이터베이스 모델은 이 클래스를 상속받아야 합니다.
    DeclarativeBase를 상속하여 SQLAlchemy 2.0 스타일의 선언적 매핑을 지원합니다.
    """

    pass


class TimestampMixin:
    """
    타임스탬프 믹스인

    모델에 created_at과 updated_at 컬럼을 자동으로 추가합니다.
    - created_at: 레코드 생성 시간 (자동 설정)
    - updated_at: 레코드 수정 시간 (자동 갱신)

    사용 예시:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AuditMixin:
    """
    감사 필드 믹스인

    레코드를 생성/수정한 사용자를 추적합니다.
    - created_by: 레코드를 생성한 사용자 ID (시스템 작업 시 NULL)
    - updated_by: 레코드를 마지막으로 수정한 사용자 ID (시스템 작업 시 NULL)

    사용 예시:
        class MyModel(Base, TimestampMixin, AuditMixin):
            __tablename__ = "my_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    @declared_attr
    def created_by(cls) -> Mapped[int | None]:
        return mapped_column(
            BigInteger,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="생성한 사용자 ID",
        )

    @declared_attr
    def updated_by(cls) -> Mapped[int | None]:
        return mapped_column(
            BigInteger,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="수정한 사용자 ID",
        )


class UserOwnedMixin:
    """
    사용자 소유 믹스인

    특정 사용자에게 귀속되는 데이터에 사용합니다.
    - user_id: 레코드 소유자의 사용자 ID (필수)

    사용 예시:
        class Order(Base, UserOwnedMixin, TimestampMixin, AuditMixin):
            __tablename__ = "orders"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(
            BigInteger,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="소유자 사용자 ID",
        )
