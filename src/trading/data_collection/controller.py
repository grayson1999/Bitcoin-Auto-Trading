# src/trading/data_collection/controller.py

import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo
from src.utils.logger import get_logger
from .service import DataCollectionService
from .archiving import archive_5min_ohlcv

logger = get_logger(name="realtime.controller", log_file="controller.log")

def main():
    service = DataCollectionService()
    logger.info("DB 초기화 및 Service 준비 완료")

    scheduler = BackgroundScheduler()
    # 스케줄러에 KST 타임존 설정 (Python 3.9+ 표준 모듈)
    scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Seoul"))

    # 티커 수집: 즉시 실행 후 3초마다
    scheduler.add_job(
        service.collect_ticker,
        trigger="interval",
        seconds=3,
        next_run_time=datetime.now(),
        id="ticker_job",
        replace_existing=True
    )

    # 아카이브: 매일 자정(한국시간)에 5분 OHLCV 집계 및 저장
    scheduler.add_job(
        archive_5min_ohlcv,
        trigger="cron",
        hour=0,
        minute=0,
        id="archive_5min_job",
        replace_existing=True
    )
    logger.info("아카이브 스케줄러 등록됨: 매일 자정")

    scheduler.start()
    logger.info("스케줄러 시작됨")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        service.close()
        logger.info("스케줄러 종료 및 DB 세션 닫힘")

if __name__ == "__main__":
    main()
