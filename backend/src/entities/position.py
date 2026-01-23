"""
포지션 엔티티

이 모듈은 현재 보유 포지션 상태를 저장하는 SQLAlchemy 모델을 정의합니다.
- 거래 코인 단일 포지션
- 보유 수량 및 평균 매수가
- 미실현 손익
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entities.base import AuditMixin, Base, UserOwnedMixin

if TYPE_CHECKING:
    from src.entities.user import User


class Position(Base, UserOwnedMixin, AuditMixin):
    """
    포지션 모델

    현재 보유 포지션 상태를 저장합니다.
    사용자별 마켓 심볼당 하나의 레코드만 유지됩니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        user_id: 소유자 사용자 ID (FK)
        symbol: 마켓 심볼 (예: KRW-SOL)
        quantity: 보유 수량
        avg_buy_price: 평균 매수가
        current_value: 현재 평가금액
        unrealized_pnl: 미실현 손익
        created_at: 생성 시간
        updated_at: 최종 업데이트 시간
        created_by: 생성자 사용자 ID
        updated_by: 수정자 사용자 ID

    제약조건:
        - UNIQUE(user_id, symbol): 사용자별 심볼 유일성

    인덱스:
        - idx_position_user_symbol: 사용자별 심볼 조회 최적화
    """

    __tablename__ = "positions"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 마켓 심볼 (user_id와 함께 UNIQUE)
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="마켓 심볼",
    )

    # === 포지션 정보 ===
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0"),
        comment="보유 수량",
    )

    avg_buy_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0"),
        comment="평균 매수가",
    )

    # === 평가 정보 ===
    current_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0"),
        comment="현재 평가금액",
    )

    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0"),
        comment="미실현 손익",
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
        comment="최종 업데이트 시간",
    )

    # === 관계 ===
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys="Position.user_id",
        lazy="selectin",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 사용자별 심볼 유일성 제약
        UniqueConstraint("user_id", "symbol", name="uq_positions_user_symbol"),
        # 사용자별 심볼 조회를 위한 인덱스
        Index("idx_position_user_symbol", "user_id", "symbol"),
        # 업데이트 시간순 조회
        Index("idx_position_updated", updated_at.desc()),
    )

    def __repr__(self) -> str:
        """
        디버깅용 문자열 표현

        Returns:
            str: 모델 정보 문자열
        """
        return (
            f"<Position(symbol={self.symbol}, quantity={self.quantity}, "
            f"avg_price={self.avg_buy_price}, pnl={self.unrealized_pnl})>"
        )

    @property
    def cost_basis(self) -> Decimal:
        """
        매수 원가 계산

        Returns:
            Decimal: 매수 원가 (수량 * 평균 매수가)
        """
        return self.quantity * self.avg_buy_price

    @property
    def pnl_pct(self) -> float:
        """
        손익률 계산

        Returns:
            float: 손익률 (%)
        """
        if self.cost_basis == 0:
            return 0.0
        return float((self.unrealized_pnl / self.cost_basis) * 100)

    def update_value(self, current_price: Decimal) -> None:
        """
        현재가로 평가금액 및 미실현 손익 업데이트

        Args:
            current_price: 현재 가격
        """
        self.current_value = self.quantity * current_price
        self.unrealized_pnl = self.current_value - self.cost_basis
