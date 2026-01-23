"""
스케줄러 작업 모듈

도메인별로 분리된 스케줄러 작업을 정의합니다:
- data_collection: 시장 데이터 수집
- cleanup: 오래된 데이터 정리
- signal_generation: AI 신호 생성 및 자동 매매
- order_sync: PENDING 주문 동기화
"""

from src.scheduler.jobs.cleanup import cleanup_old_data_job
from src.scheduler.jobs.data_collection import collect_market_data_job
from src.scheduler.jobs.order_sync import sync_pending_orders_job
from src.scheduler.jobs.signal_generation import (
    check_volatility_job,
    evaluate_signal_performance_job,
    execute_trading_from_signal_job,
    generate_trading_signal_job,
)

__all__ = [
    "check_volatility_job",
    # 데이터 정리
    "cleanup_old_data_job",
    # 데이터 수집
    "collect_market_data_job",
    "evaluate_signal_performance_job",
    "execute_trading_from_signal_job",
    # 신호 생성
    "generate_trading_signal_job",
    # 주문 동기화
    "sync_pending_orders_job",
]
