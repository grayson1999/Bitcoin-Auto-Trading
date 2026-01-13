"""
포지션 모델

이 모듈은 현재 보유 포지션 상태를 저장하는 SQLAlchemy 모델을 정의합니다.
- BTC/KRW 단일 포지션
- 보유 수량 및 평균 매수가
- 미실현 손익
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Position(Base):
    """
    포지션 모델

    현재 보유 포지션 상태를 저장합니다.
    BTC/KRW 마켓 전용으로 단일 레코드만 유지됩니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        symbol: 심볼 (BTC-KRW)
        quantity: 보유 수량
        avg_buy_price: 평균 매수가
        current_value: 현재 평가금액
        unrealized_pnl: 미실현 손익
        updated_at: 최종 업데이트 시간

    인덱스:
        - idx_position_symbol: 심볼별 조회 최적화 (UNIQUE)
    """

    __tablename__ = "positions"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 심볼 (BTC-KRW)
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="심볼 (BTC-KRW)",
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="최종 업데이트 시간",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 심볼별 조회를 위한 인덱스 (이미 unique=True로 생성됨)
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
