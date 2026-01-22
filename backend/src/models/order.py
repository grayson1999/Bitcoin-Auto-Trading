"""
주문 모델

이 모듈은 Upbit에 제출된 매매 주문 기록을 저장하는 SQLAlchemy 모델을 정의합니다.
- MARKET/LIMIT 주문 타입
- BUY/SELL 주문 방향
- 주문 상태 추적 (PENDING → EXECUTED/CANCELLED/FAILED)
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import settings
from src.models import Base

if TYPE_CHECKING:
    from src.models.trading_signal import TradingSignal


class OrderType(str, Enum):
    """
    주문 타입

    - MARKET: 시장가 주문
    - LIMIT: 지정가 주문
    """

    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderSide(str, Enum):
    """
    주문 방향

    - BUY: 매수 (bid)
    - SELL: 매도 (ask)
    """

    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """
    주문 상태

    - PENDING: 대기 중
    - EXECUTED: 체결 완료
    - CANCELLED: 취소됨
    - FAILED: 실패 (API 오류, 잔고 부족 등)
    """

    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Order(Base):
    """
    주문 모델

    Upbit에 제출된 매매 주문 기록을 저장합니다.
    AI 신호에 의한 자동 주문과 수동 주문 모두 지원합니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        signal_id: 연관 AI 신호 ID (수동 주문 시 NULL)
        order_type: 주문 타입 (MARKET/LIMIT)
        side: 주문 방향 (BUY/SELL)
        market: 마켓 코드
        amount: 주문 금액/수량
        price: 지정가 (시장가 주문 시 NULL)
        status: 주문 상태
        executed_price: 체결 가격
        executed_amount: 체결 금액/수량
        fee: 수수료
        upbit_uuid: Upbit 주문 UUID
        error_message: 실패 시 오류 메시지
        created_at: 주문 생성 시간
        executed_at: 체결 시간

    인덱스:
        - idx_order_status: 상태별 조회 최적화
        - idx_order_created_desc: 최신 주문 조회 최적화
        - idx_order_upbit_uuid: Upbit UUID 조회 최적화
    """

    __tablename__ = "orders"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 연관 AI 신호 (수동 주문 시 NULL 가능)
    signal_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("trading_signals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="연관 AI 신호 ID",
    )

    # === 주문 정보 ===
    order_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="주문 타입 (MARKET/LIMIT)",
    )

    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="주문 방향 (BUY/SELL)",
    )

    market: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=settings.trading_ticker,
        comment="마켓 코드",
    )

    # 주문 금액 (매수 시 KRW, 매도 시 코인 수량)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="주문 금액/수량",
    )

    # 지정가 (시장가 주문 시 NULL)
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="지정가 (시장가 시 NULL)",
    )

    # === 주문 상태 ===
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OrderStatus.PENDING.value,
        comment="주문 상태",
    )

    # === 체결 정보 ===
    executed_price: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="체결 가격",
    )

    executed_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="체결 금액/수량",
    )

    fee: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="수수료",
    )

    # Upbit 주문 UUID (유니크, 조회용)
    upbit_uuid: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="Upbit 주문 UUID",
    )

    # 재시도 시 중복 주문 방지용 키
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
        index=True,
        comment="재시도 시 중복 방지용 키",
    )

    # 실패 시 오류 메시지
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="실패 시 오류 메시지",
    )

    # === 시간 정보 ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="주문 생성 시간",
    )

    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="체결 시간",
    )

    # === 관계 ===
    signal: Mapped["TradingSignal | None"] = relationship(
        "TradingSignal",
        lazy="selectin",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 상태별 조회를 위한 인덱스
        Index("idx_order_status", status),
        # 최신 주문 빠른 조회를 위한 내림차순 인덱스
        Index("idx_order_created_desc", created_at.desc()),
        # Upbit UUID 조회용 (unique 제약으로 자동 생성되지만 명시적 추가)
        Index("idx_order_upbit_uuid", upbit_uuid),
    )

    def __repr__(self) -> str:
        """
        디버깅용 문자열 표현

        Returns:
            str: 모델 정보 문자열
        """
        return (
            f"<Order(id={self.id}, side={self.side}, amount={self.amount}, "
            f"status={self.status}, upbit_uuid={self.upbit_uuid})>"
        )

    @property
    def is_pending(self) -> bool:
        """
        대기 상태 여부

        Returns:
            bool: 대기 중이면 True
        """
        return self.status == OrderStatus.PENDING.value

    @property
    def is_executed(self) -> bool:
        """
        체결 완료 여부

        Returns:
            bool: 체결 완료면 True
        """
        return self.status == OrderStatus.EXECUTED.value

    @property
    def is_failed(self) -> bool:
        """
        실패 여부

        Returns:
            bool: 실패면 True
        """
        return self.status == OrderStatus.FAILED.value

    @property
    def is_buy(self) -> bool:
        """
        매수 주문 여부

        Returns:
            bool: 매수면 True
        """
        return self.side == OrderSide.BUY.value

    @property
    def is_sell(self) -> bool:
        """
        매도 주문 여부

        Returns:
            bool: 매도면 True
        """
        return self.side == OrderSide.SELL.value

    def mark_executed(
        self,
        executed_price: Decimal,
        executed_amount: Decimal,
        fee: Decimal,
        executed_at: datetime | None = None,
    ) -> None:
        """
        체결 완료로 상태 변경

        Args:
            executed_price: 체결 가격
            executed_amount: 체결 수량
            fee: 수수료
            executed_at: 체결 시간 (기본: 현재 시간)
        """
        from src.utils import UTC

        self.status = OrderStatus.EXECUTED.value
        self.executed_price = executed_price
        self.executed_amount = executed_amount
        self.fee = fee
        self.executed_at = executed_at or datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        """
        실패로 상태 변경

        Args:
            error_message: 오류 메시지
        """
        self.status = OrderStatus.FAILED.value
        self.error_message = error_message

    def mark_cancelled(self) -> None:
        """취소로 상태 변경"""
        self.status = OrderStatus.CANCELLED.value
