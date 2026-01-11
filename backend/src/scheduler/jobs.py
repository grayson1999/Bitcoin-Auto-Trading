"""APScheduler job definitions for scheduled tasks.

This module defines scheduled jobs for:
- Market data collection (1-second interval)
- Data cleanup (daily)
"""

from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from src.database import async_session_factory
from src.services.data_collector import get_data_collector

# Scheduler instance
scheduler = AsyncIOScheduler()

# Job configuration
DATA_COLLECTION_INTERVAL_SECONDS = 1
DATA_CLEANUP_INTERVAL_HOURS = 24
JOB_MAX_RETRY_ATTEMPTS = 3


async def collect_market_data_job() -> None:
    """Scheduled job to collect market data from Upbit.

    Runs every second to collect real-time market data.
    Uses auto-retry on network failures.
    """
    collector = get_data_collector()

    async with async_session_factory() as session:
        try:
            result = await collector.collect_with_retry(
                session, max_attempts=JOB_MAX_RETRY_ATTEMPTS
            )

            if result:
                await session.commit()
                logger.debug(
                    f"Market data collected: price={result.price}, "
                    f"timestamp={result.timestamp}"
                )
            else:
                logger.warning("Failed to collect market data after retries")

        except Exception as e:
            await session.rollback()
            logger.exception(f"Error in data collection job: {e}")


async def cleanup_old_data_job() -> None:
    """Scheduled job to clean up old market data.

    Runs daily to remove data older than the retention period.
    """
    collector = get_data_collector()

    async with async_session_factory() as session:
        try:
            deleted_count = await collector.cleanup_old_data(session)
            await session.commit()

            if deleted_count > 0:
                logger.info(f"Data cleanup completed: {deleted_count} records deleted")

        except Exception as e:
            await session.rollback()
            logger.exception(f"Error in data cleanup job: {e}")


def setup_scheduler() -> AsyncIOScheduler:
    """Configure and return the scheduler with all jobs.

    Returns:
        Configured AsyncIOScheduler instance.
    """
    # Market data collection job (every 1 second)
    scheduler.add_job(
        collect_market_data_job,
        trigger=IntervalTrigger(seconds=DATA_COLLECTION_INTERVAL_SECONDS),
        id="collect_market_data",
        name="Collect Market Data",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Data cleanup job (every 24 hours)
    scheduler.add_job(
        cleanup_old_data_job,
        trigger=IntervalTrigger(hours=DATA_CLEANUP_INTERVAL_HOURS),
        id="cleanup_old_data",
        name="Cleanup Old Data",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        f"Scheduler configured with jobs: "
        f"data_collection (every {DATA_COLLECTION_INTERVAL_SECONDS}s), "
        f"cleanup (every {DATA_CLEANUP_INTERVAL_HOURS}h)"
    )

    return scheduler


def start_scheduler() -> None:
    """Start the scheduler."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler() -> None:
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def get_scheduler_status() -> dict[str, Any]:
    """Get scheduler status and job information.

    Returns:
        Dictionary with scheduler status and jobs.
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat()
                if job.next_run_time
                else None,
                "pending": job.pending,
            }
        )

    return {
        "running": scheduler.running,
        "jobs": jobs,
        "timestamp": datetime.now(UTC).isoformat(),
    }
