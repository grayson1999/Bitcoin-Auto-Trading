# src/trading/data_collection/service.py

from .api import UpbitAPI
from .parser import parse_ticker, parse_account
from src.database.session import SessionRealtime, init_db
from src.database.models import TickData, AccountData
from src.utils.logger import get_logger

logger = get_logger(name="data.service", log_file="service.log")

class DataCollectionService:
    def __init__(self):
        # DB 테이블이 없으면 생성 (최초 1회)
        init_db()
        self.db = SessionRealtime()

    def collect_ticker(self, market: str = "KRW-BTC") -> None:
        raw = UpbitAPI.fetch_ticker(market)
        if not raw:
            logger.warning("collect_ticker: 데이터 수신 실패")
            return

        data = parse_ticker(raw)
        if not data:
            logger.error("collect_ticker: 데이터 정제 실패")
            return

        try:
            tick = TickData(**data)
            self.db.add(tick)
            self.db.commit()
            logger.info(f"collect_ticker: 저장 성공 – {data}")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"collect_ticker: 저장 중 오류 – {e}")

    def collect_account(self, currency: str = "BTC") -> None:
        raw_list = UpbitAPI.fetch_accounts()
        if not raw_list:
            logger.warning("collect_account: 데이터 수신 실패")
            return

        acct = parse_account(raw_list, currency)
        if not acct:
            logger.error(f"collect_account: {currency} 정보 없음")
            return

        try:
            account = AccountData(**acct)
            self.db.add(account)
            self.db.commit()
            logger.info(f"collect_account: 저장 성공 – {acct}")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"collect_account: 저장 중 오류 – {e}")

    
    def archive_5min(
        self,
        days: int = 30
    ) -> None:
        """
        실시간 DB에서 지난 `days`일간의 tick 데이터를 5분 OHLCV로 집계해
        히스토리 DB에 저장 및 원본 삭제까지 수행합니다.
        """
        from .archiving import archive_5min_ohlcv

        try:
            archive_5min_ohlcv(days=days)
            logger.info(f"Service: {days}일치 5분 OHLCV 아카이빙 완료")
        except Exception as e:
            logger.error(f"Service: 아카이빙 중 예외 발생 – {e}", exc_info=e)
    
    def close(self):
        self.db.close()
