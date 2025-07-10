# src/trading/data_collection/controller.py

import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from src.utils.logger import get_logger
from .service import DataCollectionService

logger = get_logger(name="realtime.controller", log_file="controller.log")

def main():
    service = DataCollectionService()
    logger.info("DB 초기화 및 Service 준비 완료")

    scheduler = BackgroundScheduler()
    # 티커 수집: 즉시 실행 후 15분마다
    scheduler.add_job(
        service.collect_ticker,
        trigger="interval",
        seconds=900,
        next_run_time=datetime.now(),
        id="ticker_job",
        replace_existing=True
    )

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
