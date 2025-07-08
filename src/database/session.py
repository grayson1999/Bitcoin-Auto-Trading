# src/database/session.py

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Base 선언을 가져옵니다.
from .base import Base

# .env 로드
env_path = Path(__file__).resolve().parents[1] / "config" / ".env"
load_dotenv(env_path)

# DATABASE_URL 세팅 (예시)
DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST','localhost')}:{os.getenv('DB_PORT','3306')}"
    f"/{os.getenv('DB_NAME')}?charset=utf8mb4"
)

# SQLAlchemy 엔진 및 세션 팩토리
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    """테이블이 없으면 생성합니다."""
    # Base.metadata가 models.py에 정의된 모든 테이블을 알고 있습니다.
    Base.metadata.create_all(bind=engine)

def save(session, instance):
    """세션에 인스턴스를 추가하고 커밋합니다."""
    session.add(instance)
    session.commit()
