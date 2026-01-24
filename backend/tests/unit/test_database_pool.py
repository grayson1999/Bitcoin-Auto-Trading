"""
데이터베이스 커넥션 풀 테스트

DB 커넥션 풀 크기 설정 및 동시 세션 처리 능력을 테스트합니다.
"""

import asyncio

import pytest

from src.config import DB_POOL_MAX_OVERFLOW, DB_POOL_SIZE
from src.utils.database import async_session_factory, engine


class TestDatabasePoolConfiguration:
    """DB 풀 설정 테스트"""

    def test_pool_size_is_10(self) -> None:
        """DB_POOL_SIZE가 10으로 설정되어 있는지 확인"""
        assert DB_POOL_SIZE == 10, f"Expected 10, got {DB_POOL_SIZE}"

    def test_max_overflow_is_10(self) -> None:
        """DB_POOL_MAX_OVERFLOW가 10으로 설정되어 있는지 확인"""
        assert DB_POOL_MAX_OVERFLOW == 10, f"Expected 10, got {DB_POOL_MAX_OVERFLOW}"

    def test_engine_pool_size(self) -> None:
        """엔진의 풀 크기가 설정값과 일치하는지 확인"""
        assert engine.pool.size() == DB_POOL_SIZE

    def test_total_max_connections(self) -> None:
        """최대 연결 수가 20개인지 확인 (pool + overflow)"""
        max_connections = DB_POOL_SIZE + DB_POOL_MAX_OVERFLOW
        assert max_connections == 20


class TestConcurrentSessions:
    """동시 세션 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_10_sessions(self) -> None:
        """동시 10개 세션 생성 및 작업 수행 - 기본 풀 크기 테스트"""
        results: list[int] = []

        async def db_task(task_id: int) -> int:
            async with async_session_factory() as session:
                result = await session.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
                result.scalar()
                results.append(task_id)
                return task_id

        # 동시 10개 작업 실행
        tasks = [db_task(i) for i in range(10)]
        completed = await asyncio.gather(*tasks)

        assert len(completed) == 10
        assert len(results) == 10
        assert set(completed) == set(range(10))
