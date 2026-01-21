"""
엔티티 기본 클래스

모든 SQLAlchemy ORM 모델의 기본 클래스와 공통 믹스인을 정의합니다.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
        default=func.now(),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )
