# src/realtime/db.py

import os
from sqlalchemy import (
    create_engine, Column, BigInteger, Integer, String,
    Float, DateTime, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# .env 위치를 절대 경로로 계산해서 로드
env_path = Path(__file__).resolve().parents[2] / "config" / ".env"
load_dotenv(env_path)

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

print(f"DB_USER: {DB_USER}, DB_PASS: {DB_PASS}, DB_HOST: {DB_HOST}, DB_PORT: {DB_PORT}, DB_NAME: {DB_NAME}")

# SQLAlchemy 엔진 및 세션 설정
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

class TickData(Base):
    __tablename__ = "tick_data"
    id                    = Column(BigInteger, primary_key=True, autoincrement=True)
    market                = Column(String(20), nullable=False)
    trade_price           = Column(Float,    nullable=False)
    prev_closing_price    = Column(Float,    nullable=False)
    opening_price         = Column(Float,    nullable=False)
    high_price            = Column(Float,    nullable=False)
    low_price             = Column(Float,    nullable=False)
    change_type           = Column(String(10), nullable=False)
    change_rate           = Column(Float,    nullable=False)
    trade_volume          = Column(Float,    nullable=False)
    acc_trade_volume_24h  = Column(Float,    nullable=False)
    data_timestamp        = Column(BigInteger, nullable=False)
    created_at            = Column(DateTime,  server_default="CURRENT_TIMESTAMP")

    __table_args__ = (
        Index("idx_data_timestamp", "data_timestamp"),
    )

class AccountData(Base):
    __tablename__ = "account_data"
    id                    = Column(BigInteger, primary_key=True, autoincrement=True)
    currency              = Column(String(10), nullable=False)
    balance               = Column(Float,    nullable=False)
    locked                = Column(Float,    nullable=False)
    avg_buy_price         = Column(Float,    nullable=True)
    data_timestamp        = Column(BigInteger, nullable=False)
    created_at            = Column(DateTime,  server_default="CURRENT_TIMESTAMP")

    __table_args__ = (
        UniqueConstraint("currency", "data_timestamp", name="uq_currency_timestamp"),
    )

def init_db():
    """테이블이 없으면 생성합니다."""
    Base.metadata.create_all(bind=engine)

def save_ticker(session, refined: dict):
    """정제된 티커 데이터를 DB에 저장합니다."""
    td = TickData(
        market               = refined["market"],
        trade_price          = refined["trade_price"],
        prev_closing_price   = refined["prev_closing_price"],
        opening_price        = refined["opening_price"],
        high_price           = refined["high_price"],
        low_price            = refined["low_price"],
        change_type          = refined["change"],
        change_rate          = refined["change_rate"],
        trade_volume         = refined["trade_volume"],
        acc_trade_volume_24h = refined["acc_trade_volume_24h"],
        data_timestamp       = refined["timestamp"]
    )
    session.add(td)
    session.commit()

def save_account(session, acct: dict):
    """정제된 계좌 정보를 DB에 저장합니다."""
    ad = AccountData(
        currency        = acct["currency"],
        balance         = float(acct["balance"]),
        locked          = float(acct["locked"]),
        avg_buy_price   = float(acct.get("avg_buy_price", 0)),
        data_timestamp  = acct["timestamp"]
    )
    session.add(ad)
    session.commit()
