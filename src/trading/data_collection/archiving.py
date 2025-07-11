# src/trading/data_collection/archiving.py

from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict

from src.database.session import get_realtime_db, get_history_db
from src.database.models import TickData, FiveMinOHLCV

def _bucket_5min(ts: datetime) -> datetime:
    minute = (ts.minute // 5) * 5
    return ts.replace(minute=minute, second=0, microsecond=0)

def aggregate_5min_ohlcv(ticks: List[TickData]) -> List[Dict]:
    buckets: Dict[datetime, List[TickData]] = defaultdict(list)
    for t in ticks:
        b = _bucket_5min(t.created_at)
        buckets[b].append(t)

    ohlcv_list = []
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

def archive_5min_ohlcv(days: int = 30):
    """
    실시간 DB에서 지난 `days`일간의 tick 데이터를 가져와
    5분 OHLCV로 집계한 뒤 히스토리 DB에 저장합니다.
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
            print(f"No tick data found between {start_dt} and {end_dt}.")
            return

        ohlcvs = aggregate_5min_ohlcv(ticks)
        history.bulk_insert_mappings(FiveMinOHLCV, ohlcvs)
        
        history.commit()

        print(f"Inserted {len(ohlcvs)} records into history DB.")

        # ─── 실시간 DB에서 아카이브된 데이터 일괄 삭제 ──────────────────────
        deleted = (
            realtime.query(TickData)
                    .filter(TickData.created_at < start_dt)
                    .delete(synchronize_session=False)
        )
        realtime.commit()
        print(f"Deleted {deleted} records from realtime DB.")
        print(f"Inserted {len(ohlcvs)} five-min OHLCV records for past {days} days.")

    except Exception as e:
        history.rollback()
        realtime.rollback()
        print("Archive failed:", e)
        raise

    finally:
        realtime.close()
        history.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="지난 N일간의 실시간 tick을 5분 OHLCV로 집계해 히스토리 DB에 저장합니다."
    )
    parser.add_argument(
        "-n", "--days",
        type=int,
        default=30,
        help="집계 기간(일수, 기본: 30)"
    )
    args = parser.parse_args()

    archive_5min_ohlcv(days=args.days)
