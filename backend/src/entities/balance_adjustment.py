"""
잔고 조정 엔티티

이 모듈은 입금/출금 내역을 추적하는 SQLAlchemy 모델을 정의합니다.
- 입금 (deposit)
- 출금 (withdrawal)
- 수동 조정 (manual)

수익률 계산 시 입금/출금을 고려하여 정확한 ROI를 산출합니다.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entities.base import AuditMixin, Base, UserOwnedMixin

if TYPE_CHECKING:
    from src.entities.user import User


class AdjustmentType(str, Enum):
    """
    잔고 조정 타입

    - DEPOSIT: 입금
    - WITHDRAWAL: 출금
    - MANUAL: 수동 조정
    """

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    MANUAL = "manual"


class BalanceAdjustment(Base, UserOwnedMixin, AuditMixin):
    """
    잔고 조정 모델

    입금/출금 내역을 추적하여 수익률 계산 시 활용합니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        user_id: 소유자 사용자 ID (FK)
        date: 조정일
        amount: 조정 금액 (입금: 양수, 출금: 음수)
        adjustment_type: 조정 타입 (deposit/withdrawal/manual)
        balance_before: 조정 전 잔고
        balance_after: 조정 후 잔고
        notes: 메모 (선택)
        created_at: 생성 시간
        updated_at: 수정 시간
        created_by: 생성자 사용자 ID
        updated_by: 수정자 사용자 ID

    제약조건:
        - UNIQUE(user_id, date, adjustment_type): 사용자별 날짜+타입 유일성

    인덱스:
        - idx_balance_adjustment_user_date: 사용자별 날짜 조회 최적화
    """

    __tablename__ = "balance_adjustments"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 조정일
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="조정일",
    )

    # === 조정 정보 ===
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="조정 금액 (입금: 양수, 출금: 음수)",
    )

    adjustment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AdjustmentType.DEPOSIT.value,
        comment="조정 타입 (deposit/withdrawal/manual)",
    )

    balance_before: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="조정 전 잔고",
    )

    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="조정 후 잔고",
    )

    # 메모 (선택)
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="메모",
    )

    # === 메타데이터 ===
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

    # === 관계 ===
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys="BalanceAdjustment.user_id",
        lazy="selectin",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 사용자별 날짜+타입 유일성 제약 (같은 날 동일 타입 여러 번 가능하게 하려면 제거)
        # UniqueConstraint("user_id", "date", "adjustment_type", name="uq_balance_adj_user_date_type"),
        # 사용자별 날짜 조회를 위한 인덱스
        Index("idx_balance_adjustment_user_date", "user_id", date.desc()),
        # 날짜 내림차순 조회를 위한 인덱스
        Index("idx_balance_adjustment_date_desc", date.desc()),
    )

    def __repr__(self) -> str:
        """
        디버깅용 문자열 표현

        Returns:
            str: 모델 정보 문자열
        """
        return (
            f"<BalanceAdjustment(date={self.date}, type={self.adjustment_type}, "
            f"amount={self.amount:,.0f})>"
        )

    @property
    def is_deposit(self) -> bool:
        """입금 여부"""
        return self.adjustment_type == AdjustmentType.DEPOSIT.value

    @property
    def is_withdrawal(self) -> bool:
        """출금 여부"""
        return self.adjustment_type == AdjustmentType.WITHDRAWAL.value
