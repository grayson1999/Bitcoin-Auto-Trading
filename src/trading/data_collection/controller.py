# src/realtime/controller.py

"""
realtime.controller 모듈

APScheduler를 사용하여 실시간 데이터(fetch_realtime)를 지정된 주기로 수집하고,
수집된 데이터를 DB에 저장하는 컨트롤러입니다.

주요 기능:
 1. init_db(): ORM 기반 테이블 생성
 2. fetch_realtime(): Upbit API로 티커 데이터를 가져와 파싱 후 save_ticker()로 DB 저장
 3. main(): BackgroundScheduler 설정(즉시 실행 후 15분 간격), 스케줄러 시작 및 종료 제어
"""

import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from src.utils.logger import get_logger
from src.trading.data_collection.data_collection import (
    get_ticker_data, parse_and_refine_data
)
from src.trading.data_collection.models import init_db, SessionLocal, save_ticker

# logger 생성
logger = get_logger(
    name="realtime.controller",
    log_file="controller.log"
)

def fetch_realtime():
    """현재 시세를 실시간으로 수집하여 DB 저장."""
    try:
        raw = get_ticker_data("KRW-XRP")
        if not raw:
            logger.warning("fetch_realtime: 티커 데이터 수신 실패")
            return

        refined = parse_and_refine_data(raw)
        if not refined:
            logger.error("fetch_realtime: 데이터 정제 실패")
            return

        session = SessionLocal()
        save_ticker(session, refined)
        session.close()
        logger.info(f"fetch_realtime: 저장 성공 – {refined}")
    except Exception:
        logger.exception("fetch_realtime: 예외 발생")

def main():
    init_db()
    logger.info("DB 초기화 완료")

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        fetch_realtime,
        trigger="interval",
        seconds=900,  # ★ 15분마다 실행
        id="fetch_realtime_job",
        next_run_time=datetime.now(),  # ★ 시작하자마자 즉시 실행
        misfire_grace_time=10,
        max_instances=1,
        replace_existing=True
    )

    scheduler.start()
    logger.info("스케줄러 시작됨 (fetch_realtime: 즉시 실행 후 15분마다)")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("스케줄러 종료")

if __name__ == "__main__":
    main()
