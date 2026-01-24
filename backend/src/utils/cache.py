"""
TTL (Time-To-Live) 캐시 구현

설정값 등 자주 조회되지만 드물게 변경되는 데이터를 메모리에 캐싱합니다.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """
    비동기 TTL 캐시

    특징:
    - 지정된 TTL 후 자동 만료
    - asyncio.Lock으로 동시성 안전
    - 히트/미스 통계 제공
    - 개별 키 또는 전체 무효화 지원

    Example:
        cache = TTLCache[str](ttl_seconds=3600)
        value = await cache.get_or_set("key", async_factory)
        cache.invalidate("key")
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        """
        Args:
            ttl_seconds: 캐시 만료 시간 (초). 기본값 3600초 (1시간)
        """
        self._cache: dict[str, tuple[T, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
    ) -> T:
        """
        캐시에서 값을 조회하거나, 없으면 factory를 호출하여 저장합니다.

        Args:
            key: 캐시 키
            factory: 캐시 미스 시 호출할 비동기 팩토리 함수

        Returns:
            캐시된 값 또는 새로 생성된 값
        """
        async with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if datetime.now() < expires_at:
                    self._hits += 1
                    return value

            self._misses += 1
            value = await factory()
            self._cache[key] = (value, datetime.now() + self._ttl)
            return value

    def invalidate(self, key: str | None = None) -> None:
        """
        캐시를 무효화합니다.

        Args:
            key: 무효화할 키. None이면 전체 캐시 무효화
        """
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    def stats(self) -> dict[str, int | float]:
        """
        캐시 통계를 반환합니다.

        Returns:
            hits: 캐시 히트 수
            misses: 캐시 미스 수
            hit_rate: 히트율 (%)
            size: 현재 캐시 항목 수
        """
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 2) if total > 0 else 0.0,
            "size": len(self._cache),
        }

    def reset_stats(self) -> None:
        """통계를 초기화합니다."""
        self._hits = 0
        self._misses = 0
