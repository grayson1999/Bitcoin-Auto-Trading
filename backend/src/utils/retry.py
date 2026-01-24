"""
지수 백오프 재시도 데코레이터

일시적인 오류(Rate Limit, 네트워크 오류 등)에 대해 자동 재시도를 제공합니다.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from loguru import logger

P = ParamSpec("P")
R = TypeVar("R")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    지수 백오프 재시도 데코레이터

    실패 시 base_delay * 2^(attempt-1) 초 대기 후 재시도합니다.
    예: base_delay=1.0이면 1초, 2초, 4초 대기

    Args:
        max_attempts: 최대 시도 횟수 (기본값 3)
        base_delay: 기본 대기 시간 (초) (기본값 1.0)
        exceptions: 재시도할 예외 타입 튜플

    Returns:
        데코레이터 함수

    Example:
        @with_retry(max_attempts=3, exceptions=(HTTPError,))
        async def fetch_data():
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed, "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

            # 이 코드에 도달하면 안 되지만, 타입 안전성을 위해 유지
            if last_exception:
                raise last_exception
            return await func(*args, **kwargs)

        return wrapper

    return decorator
