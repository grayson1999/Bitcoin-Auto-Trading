import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from src.utils.logger import get_logger
from .api import UpbitAPI
from .parser import parse_ticker
from .db import init_db, SessionLocal, TickData, save

logger = get_logger(name="realtime.controller", log_file="controller.log")

def fetch_and_store_ticker():
    """실시간 티커 데이터를 가져와 DB에 저장."""
    raw = UpbitAPI.fetch_ticker("KRW-BTC")
    if not raw:
        logger.warning("fetch_and_store_ticker: 데이터 수신 실패")
        return

    data = parse_ticker(raw)
    if not data:
        logger.error("fetch_and_store_ticker: 데이터 정제 실패")
        return

    session = SessionLocal()
    try:
        save(session, TickData(**data))
        logger.info(f"fetch_and_store_ticker: 저장 성공 – {data}")
    except Exception as e:
        logger.exception(f"fetch_and_store_ticker: 저장 중 오류 – {e}")
    finally:
        session.close()

def main():
    # DB 테이블 생성(최초 1회)
    init_db()
    logger.info("DB 초기화 완료")

    # 스케줄러 설정: 즉시 실행 후 15분마다 티커 수집
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        fetch_and_store_ticker,
        trigger="interval",
        seconds=900,  # 15분 간격
        next_run_time=datetime.now(),
        id="ticker_job",
        replace_existing=True
    )

    scheduler.start()
    logger.info("스케줄러 시작됨: fetch_and_store_ticker 즉시 실행 후 15분마다")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("스케줄러 종료")

if __name__ == "__main__":
    main()
