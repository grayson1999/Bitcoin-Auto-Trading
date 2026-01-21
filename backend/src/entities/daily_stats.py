"""
일별 통계 엔티티

이 모듈은 일별 거래 및 손익 통계를 저장하는 SQLAlchemy 모델을 정의합니다.
- 일별 시작/종료 잔고
- 실현 손익
- 거래 횟수 및 승률
- 거래 중단 상태
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.entities.base import Base


class DailyStats(Base):
    """
    일별 통계 모델

    일별 거래 및 손익 통계를 저장합니다.
    리스크 관리를 위한 일일 손실 한도 추적에 활용됩니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        date: 거래일
        starting_balance: 시작 잔고 (KRW)
        ending_balance: 종료 잔고 (KRW)
        realized_pnl: 실현 손익 (KRW)
        trade_count: 거래 횟수
        win_count: 수익 거래 수
        loss_count: 손실 거래 수
        is_trading_halted: 거래 중단 여부
        halt_reason: 중단 사유

    인덱스:
        - idx_daily_stats_date: 날짜별 조회 최적화 (UNIQUE)
    """

    __tablename__ = "daily_stats"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 거래일 (UNIQUE)
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=True,
        index=True,
        comment="거래일",
    )

    # === 잔고 정보 ===
    starting_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="시작 잔고 (KRW)",
    )

    ending_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="종료 잔고 (KRW)",
    )

    # 실현 손익
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
        comment="실현 손익 (KRW)",
    )

    # === 거래 통계 ===
    trade_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="거래 횟수",
    )

    win_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="수익 거래 수",
    )

    loss_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="손실 거래 수",
    )

    # === 거래 중단 상태 ===
    is_trading_halted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="거래 중단 여부",
    )

    halt_reason: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="중단 사유",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 날짜 내림차순 조회를 위한 인덱스
        Index("idx_daily_stats_date_desc", date.desc()),
    )

    def __repr__(self) -> str:
        """
        디버깅용 문자열 표현

        Returns:
            str: 모델 정보 문자열
        """
        return (
            f"<DailyStats(date={self.date}, pnl={self.realized_pnl}, "
            f"trades={self.trade_count}, halted={self.is_trading_halted})>"
        )

    @property
    def win_rate(self) -> float:
        """
        승률 계산

        Returns:
            float: 승률 (0.0 ~ 1.0)
        """
        if self.trade_count == 0:
            return 0.0
        return self.win_count / self.trade_count

    @property
    def loss_pct(self) -> float:
        """
        일일 손실률 계산

        Returns:
            float: 손실률 (%)
        """
        if self.starting_balance == 0:
            return 0.0
        return float((self.realized_pnl / self.starting_balance) * 100)
