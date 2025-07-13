# src/trading/orchestrator.py

import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo

from src.utils.logger import get_logger
from src.trading.data_collection.service import DataCollectionService
from src.trading.signal_generation.service import SignalGenerationService
from src.database.session import init_db

logger = get_logger(name="trading.orchestrator", log_file="orchestrator.log")

# --- 설정 변수 ---
# 자동매매를 실행할 마켓을 지정합니다.
# 예: "KRW-BTC", "KRW-ETH", "BTC-XRP" 등
TARGET_MARKET = "KRW-XRP"


def main():
    """자동매매 전체 프로세스를 조율하고 실행합니다."""
    
    # --- DB 초기화 ---
    logger.info("데이터베이스 테이블 생성을 시도합니다.")
    init_db()
    logger.info("데이터베이스 초기화 완료.")

    # --- 서비스 초기화 ---
    data_service = DataCollectionService()
    signal_service = SignalGenerationService()
    logger.info("모든 서비스가 성공적으로 초기화되었습니다.")

    # --- 스케줄러 설정 ---
    scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Seoul"))

    # Job 1: 시세 데이터 수집 (30초마다)
    scheduler.add_job(
        data_service.collect_ticker,
        trigger="interval",
        seconds=30,
        args=[TARGET_MARKET], # args로 마켓 전달
        id="ticker_collection_job"
    )


    # Job 2: 매매 신호 생성 및 처리 (10분 마다)
    def trading_cycle_job():
        logger.info("==== 새로운 매매 사이클 시작 ====")
        try:
            # 1. 데이터 조회
            logger.info(f"[1/3] {TARGET_MARKET} 마켓의 실시간 데이터를 조회합니다.")
            realtime_data = data_service.get_realtime_data(market=TARGET_MARKET, count=20)
            if not realtime_data.ticks:
                logger.warning("조회된 시세 데이터가 없어 매매 사이클을 건너뜁니다.")
                return

            # 2. 신호 생성
            logger.info("[2/3] 매매 신호를 생성합니다.")
            signal_response = signal_service.generate_signal(realtime_data)
            logger.info(f"수신 신호: {signal_response.signal}, 이유: {signal_response.reason}")

            # 3. 주문 실행 (TODO)
            logger.info("[3/3] 신호에 따라 주문을 실행합니다. (현재는 로그만 기록)")
            # TODO: 아래 주석을 실제 주문 실행 로직으로 교체해야 합니다.
            # from src.trading.order.service import OrderService
            # order_service = OrderService())
            # if signal_response.signal == "buy":
            #     order_service.place_buy_order(...)
            # elif signal_response.signal == "sell":
            #     order_service.place_sell_order(...)
            
        except Exception as e:
            logger.error(f"매매 사이클 중 심각한 오류 발생: {e}", exc_info=True)
        finally:
            logger.info("==== 매매 사이클 종료 ====\n")

    scheduler.add_job(
        trading_cycle_job,
        trigger="interval",
        seconds=600,
        id="trading_cycle_job",
        next_run_time=datetime.now() # 즉시 1회 실행
    )

    # Job 4: 데이터 아카이빙 (매일 자정)
    scheduler.add_job(
        data_service.archive_1h,
        trigger="cron",
        hour=0,
        minute=0,
        id="archive_1h_job"
    )
    
    logger.info("모든 작업이 스케줄러에 등록되었습니다.")

    # --- 스케줄러 시작 ---
    scheduler.start()
    logger.info("*** 자동매매 시스템이 시작되었습니다. ***")

    try:
        # 애플리케이션이 계속 실행되도록 유지
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("*** 시스템 종료 신호를 감지했습니다. 모든 서비스를 안전하게 종료합니다. ***")
        scheduler.shutdown()
        data_service.close()
        logger.info("*** 자동매매 시스템이 종료되었습니다. ***")

if __name__ == "__main__":
    main()
