from sqlalchemy import (
    Column, Float, String,
    BigInteger, DateTime,
    UniqueConstraint, Index, text
)
from .base import Base  # 공통 Declarative Base 가져오기


class TickData(Base):
    __tablename__ = "tick_data"
    # ─── PK 및 자동 증가 ID ───────────────────────────────────────────────────
    id                   = Column(BigInteger, primary_key=True, autoincrement=True)

    # ─── 시장 및 가격·거래량 정보 ───────────────────────────────────────────────
    market               = Column(String(20), nullable=False)   # 마켓 코드 (예: "KRW-BTC")
    trade_price          = Column(Float,    nullable=False)     # 현재 체결 가격
    prev_closing_price   = Column(Float,    nullable=False)     # 전일 종가
    opening_price        = Column(Float,    nullable=False)     # 시가
    high_price           = Column(Float,    nullable=False)     # 고가
    low_price            = Column(Float,    nullable=False)     # 저가
    change_type          = Column(String(10), nullable=False)   # 변화 유형 ("RISE"/"FALL")
    change_rate          = Column(Float,    nullable=False)     # 변화율
    trade_volume         = Column(Float,    nullable=False)     # 체결량
    acc_trade_volume_24h = Column(Float,    nullable=False)     # 24시간 누적 체결량

    # ─── 타임스탬프 및 생성 일시 ───────────────────────────────────────────────
    data_timestamp       = Column(BigInteger, nullable=False)   # API 응답 타임스탬프 (ms)
    created_at           = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),               # 레코드 생성 시 자동 현재시각
        nullable=False
    )

    # ─── 인덱스 설정 ─────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_data_timestamp", "data_timestamp"),           # 데이터 타임스탬프 인덱스
    )


class AccountData(Base):
    __tablename__ = "account_data"
    # ─── PK 및 자동 증가 ID ───────────────────────────────────────────────────
    id             = Column(BigInteger, primary_key=True, autoincrement=True)

    # ─── 계좌별 잔고 정보 ───────────────────────────────────────────────────────
    currency       = Column(String(10), nullable=False)         # 통화 코드 (예: "BTC")
    balance        = Column(Float,    nullable=False)           # 잔고
    locked         = Column(Float,    nullable=False)           # 주문 중 잠긴 금액
    avg_buy_price  = Column(Float,    nullable=True)            # 평균 매수가

    # ─── 타임스탬프 및 생성 일시 ───────────────────────────────────────────────
    data_timestamp = Column(BigInteger, nullable=False)         # 데이터 생성 타임스탬프 (ms)
    created_at     = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),               # 레코드 생성 시 자동 현재시각
        nullable=False
    )

    # ─── 유니크 제약조건 ───────────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("currency", "data_timestamp", name="uq_currency_timestamp"),  # 동일 통화·타임스탬프 중복 방지
    )
