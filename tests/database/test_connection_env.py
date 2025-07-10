# tests/test_db_session.py

# -*- coding: utf-8 -*-
import os
import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy import text, inspect as sqlalchemy_inspect
from dotenv import load_dotenv

import database.session as db_session

# .env 로드 (tests 디렉터리에서 상대경로로 조정 필요할 수 있습니다)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

def test_env_variables_present():
    """Realtime/History DB 환경변수가 모두 로드됐는지 확인"""
    required = [
        # Realtime
        "REALTIME_DB_USER", "REALTIME_DB_PASS", "REALTIME_DB_HOST",
        "REALTIME_DB_PORT", "REALTIME_DB_NAME",
        # History
        "HISTORY_DB_USER", "HISTORY_DB_PASS", "HISTORY_DB_HOST",
        "HISTORY_DB_PORT", "HISTORY_DB_NAME",
    ]
    for var in required:
        assert os.getenv(var), f"환경변수 {var}가 설정되어 있지 않습니다"


def test_realtime_engine_url_matches_env():
    """실시간 DB engine.url이 .env와 일치하는지 확인"""
    url = str(db_session.engine_realtime.url)
    assert os.getenv("REALTIME_DB_NAME") in url
    assert os.getenv("REALTIME_DB_USER") in url


def test_history_engine_url_matches_env():
    """히스토리 DB engine_history.url이 .env와 일치하는지 확인"""
    url = str(db_session.engine_history.url)
    assert os.getenv("HISTORY_DB_NAME") in url
    assert os.getenv("HISTORY_DB_USER") in url


def test_realtime_db_connection():
    """실시간 DB에 SELECT 1 쿼리로 연결 확인"""
    conn = None
    try:
        conn = db_session.engine_realtime.connect()
        result = conn.execute(text("SELECT 1")).scalar()
    except OperationalError as e:
        pytest.skip(f"Realtime DB 연결 실패: {e}")
    else:
        assert result == 1
    finally:
        if conn:
            conn.close()


def test_history_db_connection():
    """히스토리 DB에 SELECT 1 쿼리로 연결 확인"""
    conn = None
    try:
        conn = db_session.engine_history.connect()
        result = conn.execute(text("SELECT 1")).scalar()
    except OperationalError as e:
        pytest.skip(f"History DB 연결 실패: {e}")
    else:
        assert result == 1
    finally:
        if conn:
            conn.close()


def test_realtime_session_local_works():
    """SessionLocal()로 실시간 DB 세션 작동 확인"""
    session = db_session.SessionRealtime()
    try:
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    except OperationalError as e:
        pytest.skip(f"Realtime 세션 작동 실패: {e}")
    finally:
        session.close()


def test_history_session_local_works():
    """SessionHistory()로 히스토리 DB 세션 작동 확인"""
    session = db_session.SessionHistory()
    try:
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    except OperationalError as e:
        pytest.skip(f"History 세션 작동 실패: {e}")
    finally:
        session.close()
