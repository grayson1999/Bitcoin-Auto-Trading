# src/database/session.py

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Base 선언을 가져옵니다.
from .base import BaseRealtime, BaseHistory

# .env 로드
env_path = Path(__file__).resolve().parents[2] / "config" / ".env"
load_dotenv(env_path)

# ─────────────────────────────────────────────────────────────────────────────
# 1) Realtime DB 설정
# ─────────────────────────────────────────────────────────────────────────────
REALTIME_DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('REALTIME_DB_USER')}:{os.getenv('REALTIME_DB_PASS')}"
    f"@{os.getenv('REALTIME_DB_HOST','localhost')}:{os.getenv('REALTIME_DB_PORT','3306')}"
    f"/{os.getenv('REALTIME_DB_NAME')}?charset=utf8mb4"
)
engine_realtime = create_engine(REALTIME_DATABASE_URL, pool_pre_ping=True)
SessionRealtime = sessionmaker(bind=engine_realtime, autoflush=False, autocommit=False)

def init_db():
    """Realtime DB 테이블이 없으면 생성합니다."""
    BaseRealtime.metadata.create_all(bind=engine_realtime)

def save_realtime(session, instance):
    """실시간 DB 세션에 인스턴스를 추가하고 커밋합니다."""
    session.add(instance)
    session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 2) History DB 설정
# ─────────────────────────────────────────────────────────────────────────────
HISTORY_DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('HISTORY_DB_USER')}:{os.getenv('HISTORY_DB_PASS')}"
    f"@{os.getenv('HISTORY_DB_HOST','localhost')}:{os.getenv('HISTORY_DB_PORT','3306')}"
    f"/{os.getenv('HISTORY_DB_NAME')}?charset=utf8mb4"
)

engine_history = create_engine(HISTORY_DATABASE_URL, pool_pre_ping=True)
SessionHistory = sessionmaker(bind=engine_history, autoflush=False, autocommit=False)

def init_history_db():
    """History DB 테이블이 없으면 생성합니다."""
    BaseHistory.metadata.create_all(bind=engine_history)

def save_history(session, instance):
    """히스토리 DB 세션에 인스턴스를 추가하고 커밋합니다."""
    session.add(instance)
    session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 3) Dependency / Session Generator
# ─────────────────────────────────────────────────────────────────────────────
def get_realtime_db():
    """실시간 DB 세션을 생성·반환하고, 사용 후 닫습니다."""
    db = SessionRealtime()
    try:
        yield db
    finally:
        db.close()

def get_history_db():
    """히스토리 DB 세션을 생성·반환하고, 사용 후 닫습니다."""
    db = SessionHistory()
    # print(os.getenv('HISTORY_DB_USER'), os.getenv('REALTIME_DB_USER'))
    try:
        yield db
    finally:
        db.close()
