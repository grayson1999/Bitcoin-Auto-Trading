"""
AI 매매 신호 모델

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

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.models.market_data import MarketData


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


class TradingSignal(Base):
    """
    AI 매매 신호 모델

    1시간 주기로 Gemini AI가 생성하는 매매 신호를 저장합니다.
    시장 데이터 분석 결과와 신뢰도, 분석 근거를 포함합니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        market_data_id: 분석 기준 시장 데이터 FK
        signal_type: 신호 타입 (BUY/HOLD/SELL)
        confidence: 신뢰도 점수 (0.00 ~ 1.00)
        reasoning: AI 분석 근거 (한국어)
        created_at: 신호 생성 시간
        model_name: 사용된 AI 모델명 (예: gemini-2.5-flash)
        input_tokens: 입력 토큰 수 (비용 추적)
        output_tokens: 출력 토큰 수 (비용 추적)

    인덱스:
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
        comment="신호 생성 시간",
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

    # === 관계 ===
    market_data: Mapped["MarketData"] = relationship(
        "MarketData",
        lazy="selectin",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 최신 신호 빠른 조회를 위한 내림차순 인덱스
        Index("idx_signal_created_desc", created_at.desc()),
        # 신호 타입별 조회를 위한 복합 인덱스
        Index("idx_signal_type_created", signal_type, created_at.desc()),
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
