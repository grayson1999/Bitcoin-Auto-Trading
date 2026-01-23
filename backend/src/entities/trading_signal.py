"""
AI 매매 신호 엔티티

이 모듈은 Gemini AI가 생성한 매매 신호를 저장하는 SQLAlchemy 모델을 정의합니다.
- BUY/HOLD/SELL 신호 타입
- 신뢰도 점수 (0~1)
- AI 분석 근거
- 토큰 사용량 추적 (비용 모니터링)
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.entities.base import AuditMixin, Base, UserOwnedMixin

if TYPE_CHECKING:
    from src.entities.market_data import MarketData
    from src.entities.user import User


class SignalType(str, Enum):
    """
    매매 신호 타입

    AI가 생성하는 세 가지 신호 유형:
    - BUY: 매수 권장
    - HOLD: 관망 권장
    - SELL: 매도 권장
    """

    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class TradingSignal(Base, UserOwnedMixin, AuditMixin):
    """
    AI 매매 신호 모델

    1시간 주기로 Gemini AI가 생성하는 매매 신호를 저장합니다.
    시장 데이터 분석 결과와 신뢰도, 분석 근거를 포함합니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        user_id: 소유자 사용자 ID (FK)
        market_data_id: 분석 기준 시장 데이터 FK
        signal_type: 신호 타입 (BUY/HOLD/SELL)
        confidence: 신뢰도 점수 (0.00 ~ 1.00)
        reasoning: AI 분석 근거 (한국어)
        created_at: 신호 생성 시간
        updated_at: 신호 수정 시간
        model_name: 사용된 AI 모델명 (예: gemini-2.5-flash)
        input_tokens: 입력 토큰 수 (비용 추적)
        output_tokens: 출력 토큰 수 (비용 추적)
        created_by: 생성자 사용자 ID
        updated_by: 수정자 사용자 ID

    인덱스:
        - idx_signal_user_id: 사용자별 조회 최적화
        - idx_signal_created_desc: 최신 신호 조회 최적화
        - idx_signal_type_created: 신호 타입별 조회 최적화
    """

    __tablename__ = "trading_signals"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 분석 기준 시장 데이터 참조
    market_data_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("market_data.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="분석 기준 시장 데이터 ID",
    )

    # === 신호 정보 ===
    signal_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="신호 타입 (BUY/HOLD/SELL)",
    )

    # 신뢰도: 0.00 ~ 1.00 (소수점 2자리)
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        comment="신뢰도 점수 (0~1)",
    )

    # AI 분석 근거 (JSON 또는 자연어 텍스트)
    reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI 분석 근거",
    )

    # === 메타데이터 ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=func.now(),
        server_default=func.now(),
        comment="신호 생성 시간",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        comment="신호 수정 시간",
    )

    # AI 모델 정보
    model_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="사용된 AI 모델명",
    )

    # === 토큰 사용량 (비용 추적) ===
    input_tokens: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="입력 토큰 수",
    )
    output_tokens: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="출력 토큰 수",
    )

    # === 성과 추적 필드 ===
    # 신호 생성 시 가격 (성과 평가 기준)
    price_at_signal: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="신호 생성 시 가격",
    )

    # 4시간 후 가격 (단기 성과 평가)
    price_after_4h: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="4시간 후 가격",
    )

    # 24시간 후 가격 (중기 성과 평가)
    price_after_24h: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="24시간 후 가격",
    )

    # 성과 평가 완료 여부
    outcome_evaluated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="성과 평가 완료 여부",
    )

    # 신호 정확성 (가격 방향 일치 여부)
    # BUY 신호 후 가격 상승 = True, SELL 신호 후 가격 하락 = True
    outcome_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="신호 정확성 (방향 일치 여부)",
    )

    # 기술적 지표 스냅샷 (JSON 형식)
    technical_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="기술적 지표 스냅샷 (JSON)",
    )

    # === 관계 ===
    market_data: Mapped["MarketData"] = relationship(
        "MarketData",
        lazy="selectin",
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys="TradingSignal.user_id",
        lazy="selectin",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 최신 신호 빠른 조회를 위한 내림차순 인덱스
        Index("idx_signal_created_desc", created_at.desc()),
        # 신호 타입별 조회를 위한 복합 인덱스
        Index("idx_signal_type_created", signal_type, created_at.desc()),
        # 사용자별 최신 신호 조회
        Index("idx_signal_user_created", "user_id", created_at.desc()),
    )

    def __repr__(self) -> str:
        """
        디버깅용 문자열 표현

        Returns:
            str: 모델 정보 문자열
        """
        return (
            f"<TradingSignal(id={self.id}, type={self.signal_type}, "
            f"confidence={self.confidence}, created_at={self.created_at})>"
        )
