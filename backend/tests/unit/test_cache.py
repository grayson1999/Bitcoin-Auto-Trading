"""
TTLCache 유닛 테스트

TTL 캐시의 핵심 기능을 테스트합니다:
- get_or_set: 캐시 히트/미스, 팩토리 함수 호출
- invalidate: 개별 키 및 전체 무효화
- stats: 히트/미스 통계
- TTL 만료: 시간 경과 후 재조회
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.cache import TTLCache


class TestTTLCacheGetOrSet:
    """get_or_set 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_cache_miss_calls_factory(self) -> None:
        """캐시 미스 시 팩토리 함수를 호출해야 함"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value="test_value")

        result = await cache.get_or_set("key1", factory)

        assert result == "test_value"
        factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_does_not_call_factory(self) -> None:
        """캐시 히트 시 팩토리 함수를 호출하지 않아야 함"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value="test_value")

        # 첫 번째 호출 - 캐시 미스
        await cache.get_or_set("key1", factory)
        factory.reset_mock()

        # 두 번째 호출 - 캐시 히트
        result = await cache.get_or_set("key1", factory)

        assert result == "test_value"
        factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_different_keys_stored_separately(self) -> None:
        """다른 키는 별도로 저장되어야 함"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory1 = AsyncMock(return_value="value1")
        factory2 = AsyncMock(return_value="value2")

        result1 = await cache.get_or_set("key1", factory1)
        result2 = await cache.get_or_set("key2", factory2)

        assert result1 == "value1"
        assert result2 == "value2"
        factory1.assert_called_once()
        factory2.assert_called_once()

    @pytest.mark.asyncio
    async def test_expired_cache_calls_factory_again(self) -> None:
        """만료된 캐시는 팩토리를 다시 호출해야 함"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=1)
        factory = AsyncMock(return_value="test_value")

        # 첫 번째 호출
        await cache.get_or_set("key1", factory)

        # datetime.now()를 모킹하여 TTL 만료 시뮬레이션
        expired_time = datetime.now() + timedelta(seconds=2)
        with patch("src.utils.cache.datetime") as mock_datetime:
            mock_datetime.now.return_value = expired_time

            factory.reset_mock()
            factory.return_value = "new_value"

            result = await cache.get_or_set("key1", factory)

            assert result == "new_value"
            factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_access_is_safe(self) -> None:
        """동시 접근 시에도 안전해야 함 (락 테스트)"""
        cache: TTLCache[int] = TTLCache(ttl_seconds=3600)
        call_count = 0

        async def slow_factory() -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # 약간의 지연
            return call_count

        # 동시에 여러 요청 실행
        tasks = [cache.get_or_set("key1", slow_factory) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # 모든 결과가 동일해야 함 (첫 번째 팩토리 결과)
        assert all(r == results[0] for r in results)


class TestTTLCacheInvalidate:
    """invalidate 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_invalidate_single_key(self) -> None:
        """단일 키 무효화"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value="test_value")

        await cache.get_or_set("key1", factory)
        cache.invalidate("key1")

        factory.reset_mock()
        factory.return_value = "new_value"
        result = await cache.get_or_set("key1", factory)

        assert result == "new_value"
        factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_all_keys(self) -> None:
        """전체 캐시 무효화"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory1 = AsyncMock(return_value="value1")
        factory2 = AsyncMock(return_value="value2")

        await cache.get_or_set("key1", factory1)
        await cache.get_or_set("key2", factory2)

        cache.invalidate()  # 전체 무효화

        factory1.reset_mock()
        factory2.reset_mock()
        factory1.return_value = "new_value1"
        factory2.return_value = "new_value2"

        result1 = await cache.get_or_set("key1", factory1)
        result2 = await cache.get_or_set("key2", factory2)

        assert result1 == "new_value1"
        assert result2 == "new_value2"
        factory1.assert_called_once()
        factory2.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_key_no_error(self) -> None:
        """존재하지 않는 키 무효화 시 에러 없음"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)

        # 예외가 발생하지 않아야 함
        cache.invalidate("nonexistent_key")


class TestTTLCacheStats:
    """stats 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_initial_stats_zero(self) -> None:
        """초기 통계는 0이어야 함"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)

        stats = cache.stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["size"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_misses(self) -> None:
        """캐시 미스 후 통계"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value="value")

        await cache.get_or_set("key1", factory)
        await cache.get_or_set("key2", factory)

        stats = cache.stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.0
        assert stats["size"] == 2

    @pytest.mark.asyncio
    async def test_stats_after_hits_and_misses(self) -> None:
        """히트와 미스 혼합 후 통계"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value="value")

        # 2 미스
        await cache.get_or_set("key1", factory)
        await cache.get_or_set("key2", factory)

        # 3 히트
        await cache.get_or_set("key1", factory)
        await cache.get_or_set("key1", factory)
        await cache.get_or_set("key2", factory)

        stats = cache.stats()

        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 60.0  # 3/5 * 100
        assert stats["size"] == 2

    @pytest.mark.asyncio
    async def test_high_hit_rate_scenario(self) -> None:
        """높은 히트율 시나리오 (95%+)"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value="value")

        # 1 미스
        await cache.get_or_set("key1", factory)

        # 19 히트 (총 20회 중 19회 = 95%)
        for _ in range(19):
            await cache.get_or_set("key1", factory)

        stats = cache.stats()

        assert stats["hits"] == 19
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 95.0


class TestTTLCacheResetStats:
    """reset_stats 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_reset_stats(self) -> None:
        """통계 초기화"""
        cache: TTLCache[str] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value="value")

        await cache.get_or_set("key1", factory)
        await cache.get_or_set("key1", factory)

        cache.reset_stats()

        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        # 캐시 항목은 유지됨
        assert stats["size"] == 1


class TestTTLCacheGenericType:
    """제네릭 타입 테스트"""

    @pytest.mark.asyncio
    async def test_cache_dict_type(self) -> None:
        """딕셔너리 타입 캐싱"""
        cache: TTLCache[dict] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value={"key": "value", "count": 42})

        result = await cache.get_or_set("config", factory)

        assert result == {"key": "value", "count": 42}

    @pytest.mark.asyncio
    async def test_cache_list_type(self) -> None:
        """리스트 타입 캐싱"""
        cache: TTLCache[list] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value=[1, 2, 3])

        result = await cache.get_or_set("numbers", factory)

        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_cache_none_value(self) -> None:
        """None 값 캐싱 (주의: None도 유효한 캐시 값)"""
        cache: TTLCache[str | None] = TTLCache(ttl_seconds=3600)
        factory = AsyncMock(return_value=None)

        result = await cache.get_or_set("nullable", factory)

        assert result is None
        # None도 캐시되어야 함 (두 번째 호출 시 팩토리 호출 안됨)
        factory.reset_mock()
        await cache.get_or_set("nullable", factory)
        factory.assert_not_called()
