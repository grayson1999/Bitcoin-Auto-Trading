"""
시장 데이터 엔티티

이 모듈은 Upbit에서 수집한 실시간 시장 데이터를 저장하는 SQLAlchemy 모델을 정의합니다.
- 암호화폐 가격, 거래량, 거래 정보 저장
- 1초 간격으로 수집되는 데이터
- 인덱스 최적화로 빠른 조회 지원
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.entities.base import Base


class MarketData(Base):
    """
    실시간 시장 데이터 모델

    Upbit API에서 수집한 시세 정보를 저장합니다.
    1초 간격으로 수집되며, 설정된 보관 기간(기본 365일) 동안 유지됩니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        symbol: 마켓 심볼 (예: KRW-BTC, KRW-SOL)
        timestamp: 데이터 수집 시간 (UTC, 타임존 포함)
        price: 현재 가격 (KRW)
        volume: 24시간 누적 거래량
        high_price: 24시간 최고가
        low_price: 24시간 최저가
        trade_count: 거래 건수

    인덱스:
        - idx_market_data_symbol_timestamp: 심볼별 시간순 조회 최적화
        - idx_market_data_timestamp_desc: 최신 데이터 조회 최적화 (내림차순)
        - idx_market_data_date: 날짜 범위 조회 최적화 (오름차순)
    """

    __tablename__ = "market_data"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 마켓 심볼 (예: KRW-BTC, KRW-SOL)
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="마켓 심볼 (예: KRW-BTC)",
    )

    # 데이터 수집 시간 (타임존 포함)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,  # 기본 인덱스
    )

    # === 가격 정보 ===
    # Numeric(18, 8): 최대 18자리, 소수점 8자리 (암호화폐 정밀도)
    price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="현재 가격 (KRW)",
    )

    # === 거래량 정보 ===
    volume: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="24시간 누적 거래량",
    )

    # === 24시간 고가/저가 ===
    high_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="24시간 최고가",
    )
    low_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="24시간 최저가",
    )

    # === 거래 건수 ===
    trade_count: Mapped[int] = mapped_column(
        nullable=False,
        comment="거래 건수",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 심볼별 시간순 조회를 위한 복합 인덱스 (가장 중요)
        Index("idx_market_data_symbol_timestamp", "symbol", timestamp.desc()),
        # 최신 데이터 빠른 조회를 위한 내림차순 인덱스
        Index("idx_market_data_timestamp_desc", timestamp.desc()),
        # 날짜 범위 검색을 위한 오름차순 인덱스
        Index("idx_market_data_date", timestamp),
    )

    def __repr__(self) -> str:
        """
        디버깅용 문자열 표현

        Returns:
            str: 모델 정보 문자열
        """
        return (
            f"<MarketData(id={self.id}, symbol={self.symbol}, "
            f"timestamp={self.timestamp}, price={self.price})>"
        )
