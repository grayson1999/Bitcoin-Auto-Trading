"""
시스템 설정 엔티티

런타임 설정값을 저장하는 SQLAlchemy 모델입니다.
- 포지션 크기, 손절, 일일 손실 한도 등 리스크 파라미터
- AI 신호 주기, 모델 설정
- 변동성 임계값
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.entities.base import Base

if TYPE_CHECKING:
    pass


class SystemConfig(Base):
    """
    시스템 설정 엔티티

    런타임 설정값을 키-값 형태로 저장합니다.
    설정값은 JSON 문자열로 저장되며, 애플리케이션에서 파싱하여 사용합니다.
    사용자별 설정은 user_configs 테이블에 저장되며 이 값을 오버라이드합니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        key: 설정 키 (UNIQUE)
        value: 설정 값 (JSON 문자열)
        created_at: 생성 시간
        updated_at: 최종 수정 시간
        created_by: 생성자 사용자 ID
        updated_by: 수정자 사용자 ID
    """

    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="설정 키",
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="설정 값 (JSON)",
    )

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
        comment="최종 수정 시간",
    )

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="생성자 사용자 ID",
    )

    updated_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="수정자 사용자 ID",
    )

    __table_args__ = (Index("idx_system_config_updated", updated_at.desc()),)

    def __repr__(self) -> str:
        """디버깅용 문자열 표현"""
        value_preview = self.value[:50] if len(self.value) > 50 else self.value
        return f"<SystemConfig(key={self.key}, value={value_preview}...)>"


# 기본 설정값 상수
# DB 오버라이드 가능한 7개 설정만 포함
# - trading_ticker: 환경변수로 관리
# - trading_enabled: Risk API로 제어
DEFAULT_CONFIGS = {
    "position_size_min_pct": "25.0",
    "position_size_max_pct": "50.0",
    "stop_loss_pct": "5.0",
    "daily_loss_limit_pct": "5.0",
    "signal_interval_hours": "1",
    "ai_model": '"gemini-2.5-pro"',
    "volatility_threshold_pct": "3.0",
}
