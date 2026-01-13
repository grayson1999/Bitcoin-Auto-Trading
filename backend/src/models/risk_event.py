"""
리스크 이벤트 모델

이 모듈은 리스크 관리 시스템이 발동한 이벤트를 저장하는 SQLAlchemy 모델을 정의합니다.
- 손절매 발동
- 일일 손실 한도 도달
- 포지션 크기 초과
- 변동성 감지
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class RiskEventType(str, Enum):
    """
    리스크 이벤트 유형

    - STOP_LOSS: 개별 손절 발동
    - DAILY_LIMIT: 일일 손실 한도 도달
    - POSITION_LIMIT: 포지션 크기 초과 거부
    - VOLATILITY_HALT: 변동성 감지 거래 중단
    - SYSTEM_ERROR: 시스템 오류 감지
    """

    STOP_LOSS = "STOP_LOSS"
    DAILY_LIMIT = "DAILY_LIMIT"
    POSITION_LIMIT = "POSITION_LIMIT"
    VOLATILITY_HALT = "VOLATILITY_HALT"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class RiskEvent(Base):
    """
    리스크 이벤트 모델

    리스크 관리 시스템이 발동한 모든 이벤트를 기록합니다.
    손절매, 일일 손실 한도, 포지션 제한, 변동성 감지 등의 이벤트를 추적합니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        order_id: 연관 주문 ID (없을 수 있음)
        event_type: 이벤트 유형
        trigger_value: 발동 기준값 (%)
        action_taken: 수행된 조치
        created_at: 발생 시간
        notified: 슬랙 알림 전송 여부

    인덱스:
        - idx_risk_event_created_desc: 최신 이벤트 조회 최적화
        - idx_risk_event_type_created: 이벤트 타입별 조회 최적화
    """

    __tablename__ = "risk_events"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 연관 주문 (없을 수 있음)
    # Note: orders 테이블 생성 후 FK 제약조건 추가 예정
    order_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="연관 주문 ID",
    )

    # === 이벤트 정보 ===
    event_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="이벤트 유형",
    )

    # 발동 기준값 (예: 5.0 = 5%)
    trigger_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="발동 기준값 (%)",
    )

    # 수행된 조치
    action_taken: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="수행된 조치",
    )

    # === 메타데이터 ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="발생 시간",
    )

    # 슬랙 알림 전송 여부
    notified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="슬랙 알림 전송 여부",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 최신 이벤트 빠른 조회를 위한 내림차순 인덱스
        Index("idx_risk_event_created_desc", created_at.desc()),
        # 이벤트 타입별 조회를 위한 복합 인덱스
        Index("idx_risk_event_type_created", event_type, created_at.desc()),
    )

    def __repr__(self) -> str:
        """
        디버깅용 문자열 표현

        Returns:
            str: 모델 정보 문자열
        """
        return (
            f"<RiskEvent(id={self.id}, type={self.event_type}, "
            f"trigger={self.trigger_value}%, created_at={self.created_at})>"
        )
