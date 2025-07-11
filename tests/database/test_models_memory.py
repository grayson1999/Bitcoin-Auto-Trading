# -*- coding: utf-8 -*-
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

import src.database.base as base_mod
import src.database.session as db_session
import src.database.models as models

@pytest.fixture(autouse=True)
def memory_db(monkeypatch):
    """
    메모리 엔진으로 대체하여
    모델·save() 동작만 검증
    """
    mem_engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(db_session, "engine_realtime", mem_engine)
    monkeypatch.setattr(db_session, "SessionRealtime",
                        sessionmaker(bind=mem_engine, autoflush=False, autocommit=False))
    # 테이블 생성
    base_mod.Base.metadata.create_all(mem_engine)
    yield
    # 테스트 후 드롭
    base_mod.Base.metadata.drop_all(mem_engine)

@pytest.fixture
def session():
    return db_session.SessionRealtime()

def test_테이블_생성_확인():
    """메모리 DB에서 테이블이 생성됐는지 확인"""
    inspector = inspect(db_session.engine_realtime)
    assert "tick_data" in inspector.get_table_names()
    assert "account_data" in inspector.get_table_names()

def test_틱데이터_CRUD_및_저장_확인(session):
    """TickData CRUD 및 save(session, instance) 검증"""
    tick = models.TickData(
        market="KRW-TEST", trade_price=1.23, prev_closing_price=1.0,
        opening_price=1.1, high_price=1.5, low_price=0.9,
        change_type="RISE", change_rate=0.23,
        trade_volume=0.5, acc_trade_volume_24h=10.0,
        data_timestamp=1234567890
    )
    # 직접 add/commit
    session.add(tick)
    session.commit()
    assert session.query(models.TickData).count() == 1

    # save() 함수로 추가
    another = models.TickData(
        market="KRW-SAVE", trade_price=9.99, prev_closing_price=9.0,
        opening_price=9.5, high_price=10.0, low_price=9.0,
        change_type="FALL", change_rate=-0.11,
        trade_volume=0.1, acc_trade_volume_24h=5.0,
        data_timestamp=9876543210
    )
    db_session.save_realtime(session, another)
    assert session.query(models.TickData).filter_by(market="KRW-SAVE").one()

def test_계좌정보_유니크_제약조건_확인(session):
    """AccountData (currency, data_timestamp) 유니크 제약조건 확인"""
    a1 = models.AccountData(
        currency="ABC", balance=1.0, locked=0.0,
        avg_buy_price=100.0, data_timestamp=111
    )
    session.add(a1)
    session.commit()

    a2 = models.AccountData(
        currency="ABC", balance=2.0, locked=0.0,
        avg_buy_price=200.0, data_timestamp=111
    )
    session.add(a2)
    with pytest.raises(Exception):
        session.commit()
