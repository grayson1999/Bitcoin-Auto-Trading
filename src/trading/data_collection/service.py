# src/trading/data_collection/service.py

from .api import UpbitAPI
from .parser import parse_ticker, parse_account
from src.database.session import SessionRealtime, init_db
from src.database.models import TickData, AccountData
from src.utils.logger import get_logger
from .dto import RealtimeData, RealtimeTickData, RealtimeAccountData
from sqlalchemy import desc

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

    def get_realtime_data(self, market: str = "KRW-BTC", count: int = 10) -> RealtimeData:
        """최신 실시간 데이터를 DB와 API에서 조회하여 DTO로 반환"""
        
        # 1. 최신 시세 정보 (DB에서 조회)
        ticks_from_db = self.db.query(TickData).filter_by(market=market).order_by(desc(TickData.data_timestamp)).limit(count).all()
        realtime_ticks = [
            RealtimeTickData(
                market=t.market,
                trade_price=t.trade_price,
                prev_closing_price=t.prev_closing_price,
                opening_price=t.opening_price,
                high_price=t.high_price,
                low_price=t.low_price,
                change_type=t.change_type,
                change_rate=t.change_rate,
                trade_volume=t.trade_volume,
                acc_trade_volume_24h=t.acc_trade_volume_24h,
                data_timestamp=t.data_timestamp
            ) for t in ticks_from_db
        ]

        # 2. 최신 계좌 정보 (API에서 직접 조회)
        realtime_accounts = []
        try:
            raw_accounts = UpbitAPI.fetch_accounts()
            if raw_accounts:
                # market(예: "KRW-BTC")에 포함된 모든 통화(KRW, BTC)의 정보를 파싱
                currencies = market.split('-')
                for currency in currencies:
                    parsed_account = parse_account(raw_accounts, currency)
                    if parsed_account:
                        realtime_accounts.append(RealtimeAccountData(**parsed_account))
            else:
                logger.warning("get_realtime_data: API로부터 계좌 정보를 가져오지 못했습니다.")
        except Exception as e:
            logger.error(f"get_realtime_data: API에서 계좌 정보 조회 중 오류 발생 - {e}", exc_info=True)

        return RealtimeData(ticks=realtime_ticks, accounts=realtime_accounts)

    
    def archive_5min(
        self,
        days: int = 30,
        keep_hours: int = 12
    ) -> None:
        """
        실시간 DB에서 지난 `days`일간의 tick 데이터를 5분 OHLCV로 집계해
        히스토리 DB에 저장 및 원본 삭제까지 수행합니다.
        `keep_hours`는 실시간 DB에 유지할 최근 데이터의 시간(기본 12시간)입니다.
        """
        from .archiving import archive_5min_ohlcv

        try:
            archive_5min_ohlcv(days=days, keep_hours=keep_hours)
            logger.info(f"Service: {days}일치 5분 OHLCV 아카이빙 완료. 최근 {keep_hours}시간 데이터 유지.")
        except Exception as e:
            logger.error(f"Service: 아카이빙 중 예외 발생 – {e}", exc_info=e)
    
    def close(self):
        self.db.close()
