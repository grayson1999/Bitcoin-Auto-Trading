# src/trading/data_collection/archiving.py

from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.database.session import get_realtime_db, get_history_db
from src.database.models import TickData, FiveMinOHLCV

from src.utils.logger import get_logger

# ─── 로거 가져오기 (logs/archiving.log, 일별 롤링) ────────────────────────────
logger = get_logger(
    name="trading.data_collection.archiving",
    log_file="archiving.log",
    when="midnight",
    interval=1,
    backup_count=30
)

def _bucket_5min(ts: datetime) -> datetime:
    minute = (ts.minute // 5) * 5
    return ts.replace(minute=minute, second=0, microsecond=0)

def aggregate_5min_ohlcv(ticks: List[TickData]) -> List[Dict[str, Any]]:
    buckets: Dict[datetime, List[TickData]] = defaultdict(list)
    for t in ticks:
        b = _bucket_5min(t.created_at)
        buckets[b].append(t)

    ohlcv_list: List[Dict[str, Any]] = []
    for bucket_ts in sorted(buckets):
        group = buckets[bucket_ts]
        prices = [t.trade_price for t in group]
        volumes = [t.trade_volume for t in group]
        ohlcv_list.append({
            "timestamp": bucket_ts,
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "close": prices[-1],
            "volume": sum(volumes),
        })
    return ohlcv_list

def archive_5min_ohlcv(days: int = 30, keep_hours: int = 12):
    """
    실시간 DB에서 지난 `days`일간의 tick 데이터를 가져와
    5분 OHLCV로 집계한 뒤 히스토리 DB에 저장 및 실시간 DB 원본 삭제.
    """
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)

    realtime = next(get_realtime_db())
    history  = next(get_history_db())

    try:
        ticks = (
            realtime.query(TickData)
                    .filter(TickData.created_at >= start_dt,
                            TickData.created_at <  end_dt)
                    .order_by(TickData.created_at)
                    .all()
        )

        if not ticks:
            logger.info(f"{start_dt} ~ {end_dt} 사이에 틱 데이터가 없습니다.")
            return

        ohlcvs = aggregate_5min_ohlcv(ticks)
        history.bulk_insert_mappings(FiveMinOHLCV, ohlcvs)
        history.commit()
        logger.info(f"Inserted {len(ohlcvs)} records into history DB.")

        # Delete tick data older than keep_hours from now
        delete_before_dt = datetime.utcnow() - timedelta(hours=keep_hours)
        deleted = (
            realtime.query(TickData)
                    .filter(TickData.created_at < delete_before_dt)
                    .delete(synchronize_session=False)
        )
        realtime.commit()
        logger.info(f"Deleted {deleted} records from realtime DB.")

    except Exception as e:
        history.rollback()
        realtime.rollback()
        logger.error("Archive failed", exc_info=e)
        raise

    finally:
        realtime.close()
        history.close()

if __name__ == "__main__":
    archive_5min_ohlcv()
