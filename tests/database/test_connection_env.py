# -*- coding: utf-8 -*-
import os
import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy import inspect as sqlalchemy_inspect
from dotenv import load_dotenv
import database.session as db_session



def test_env_variables_present():
    """.env에서 DB_USER, DB_PASS, DB_NAME 등 필수 환경변수가 로드됐는지 확인"""
    for var in ("DB_USER", "DB_PASS", "DB_HOST", "DB_PORT", "DB_NAME"):
        assert os.getenv(var), f"환경변수 {var}가 설정되어 있지 않습니다"

def test_engine_url_matches_env():
    """engine.url이 .env의 DATABASE_URL과 일치하는지 간단히 확인"""
    url = str(db_session.engine.url)
    assert os.getenv("DB_NAME") in url
    assert os.getenv("DB_USER") in url

def test_real_db_connection():
    """
    실제 MySQL 서버에 연결하여
    SELECT 1 쿼리가 성공적으로 실행되는지 확인
    """
    conn = None
    try:
        from sqlalchemy import text
        conn = db_session.engine.connect()
        # 문자열 SQL은 text()로 감싸야 실행 가능합니다.
        result = conn.execute(text("SELECT 1")).scalar()
    except OperationalError as e:
        pytest.skip(f"DB 연결 실패: {e}")  # 실제 서버가 없으면 테스트 스킵
    else:
        assert result == 1
    finally:
        if conn:
            conn.close()

def test_session_local_works():
    """
    SessionLocal() 로 세션을 열고
    단순 SELECT 1 쿼리가 실행되는지 확인
    """
    session = db_session.SessionLocal()
    try:
        # SQLAlchemy 2.x dialect에서는 .execute(text(...))가 필요할 수 있습니다.
        from sqlalchemy import text
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    except OperationalError as e:
        pytest.skip(f"세션 작동 확인 실패: {e}")
    finally:
        session.close()
