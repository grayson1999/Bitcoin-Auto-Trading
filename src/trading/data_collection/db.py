import os
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, Float, String,
    BigInteger, DateTime, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 root/config/.env 기준)
env_path = Path(__file__).resolve().parents[3] / "config" / ".env"
load_dotenv(env_path)

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class TickData(Base):
    __tablename__ = "tick_data"
    id                   = Column(BigInteger, primary_key=True, autoincrement=True)
    market               = Column(String(20), nullable=False)
    trade_price          = Column(Float,    nullable=False)
    prev_closing_price   = Column(Float,    nullable=False)
    opening_price        = Column(Float,    nullable=False)
    high_price           = Column(Float,    nullable=False)
    low_price            = Column(Float,    nullable=False)
    change_type          = Column(String(10), nullable=False)
    change_rate          = Column(Float,    nullable=False)
    trade_volume         = Column(Float,    nullable=False)
    acc_trade_volume_24h = Column(Float,    nullable=False)
    data_timestamp       = Column(BigInteger, nullable=False)
    created_at           = Column(DateTime,  server_default="CURRENT_TIMESTAMP")

    __table_args__ = (
        Index("idx_data_timestamp", "data_timestamp"),
    )

class AccountData(Base):
    __tablename__ = "account_data"
    id             = Column(BigInteger, primary_key=True, autoincrement=True)
    currency       = Column(String(10), nullable=False)
    balance        = Column(Float,    nullable=False)
    locked         = Column(Float,    nullable=False)
    avg_buy_price  = Column(Float,    nullable=True)
    data_timestamp = Column(BigInteger, nullable=False)
    created_at     = Column(DateTime,  server_default="CURRENT_TIMESTAMP")

    __table_args__ = (
        UniqueConstraint("currency", "data_timestamp", name="uq_currency_timestamp"),
    )

def init_db():
    """테이블이 없으면 생성합니다."""
    Base.metadata.create_all(bind=engine)

def save(session, instance):
    """단일 인스턴스를 DB에 저장하고 커밋."""
    session.add(instance)
    session.commit()
