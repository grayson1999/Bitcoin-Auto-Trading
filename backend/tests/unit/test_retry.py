"""
지수 백오프 재시도 데코레이터 테스트

테스트 항목:
- 성공 시 즉시 반환
- 실패 후 재시도 성공
- 최대 시도 후 예외 발생
- 지수 백오프 대기 시간
- 특정 예외만 재시도
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.retry import with_retry


class TestRetrySuccess:
    """성공 케이스 테스트"""

    @pytest.mark.asyncio
    async def test_returns_immediately_on_success(self) -> None:
        """첫 번째 시도에서 성공하면 즉시 반환"""
        mock_func = AsyncMock(return_value="success")

        @with_retry()
        async def test_func() -> str:
            return await mock_func()

        result = await test_func()

        assert result == "success"
        mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_after_retries(self) -> None:
        """실패 후 재시도에서 성공"""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        async def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count == 3


class TestRetryFailure:
    """실패 케이스 테스트"""

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self) -> None:
        """최대 시도 횟수 초과 시 예외 발생"""

        @with_retry(max_attempts=3, base_delay=0.01)
        async def always_fails() -> None:
            raise ValueError("permanent error")

        with pytest.raises(ValueError, match="permanent error"):
            await always_fails()

    @pytest.mark.asyncio
    async def test_does_not_retry_unspecified_exceptions(self) -> None:
        """지정하지 않은 예외는 재시도하지 않음"""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
        async def raises_type_error() -> None:
            nonlocal call_count
            call_count += 1
            raise TypeError("not retryable")

        with pytest.raises(TypeError, match="not retryable"):
            await raises_type_error()

        # TypeError는 재시도하지 않으므로 1회만 호출
        assert call_count == 1


class TestExponentialBackoff:
    """지수 백오프 테스트"""

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self) -> None:
        """지수 백오프 대기 시간 확인 (1초, 2초, 4초)"""
        delays: list[float] = []

        with patch("src.utils.retry.asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda d: delays.append(d)

            @with_retry(max_attempts=4, base_delay=1.0)
            async def always_fails() -> None:
                raise ValueError("error")

            with pytest.raises(ValueError):
                await always_fails()

        # 3번 재시도 (4번째는 최종 실패이므로 대기 없음)
        assert delays == [1.0, 2.0, 4.0]

    @pytest.mark.asyncio
    async def test_custom_base_delay(self) -> None:
        """커스텀 기본 대기 시간"""
        delays: list[float] = []

        with patch("src.utils.retry.asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda d: delays.append(d)

            @with_retry(max_attempts=3, base_delay=0.5)
            async def always_fails() -> None:
                raise ValueError("error")

            with pytest.raises(ValueError):
                await always_fails()

        # 0.5초, 1.0초 대기
        assert delays == [0.5, 1.0]


class TestRetryWithSpecificExceptions:
    """특정 예외 재시도 테스트"""

    @pytest.mark.asyncio
    async def test_retries_only_specified_exceptions(self) -> None:
        """지정된 예외만 재시도"""
        call_count = 0

        @with_retry(
            max_attempts=3,
            base_delay=0.01,
            exceptions=(ConnectionError, TimeoutError),
        )
        async def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("connection failed")
            if call_count == 2:
                raise TimeoutError("timeout")
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_multiple_exception_types(self) -> None:
        """여러 예외 타입 재시도"""
        exceptions_raised: list[str] = []

        @with_retry(
            max_attempts=4,
            base_delay=0.01,
            exceptions=(ValueError, RuntimeError),
        )
        async def alternating_errors() -> str:
            if len(exceptions_raised) == 0:
                exceptions_raised.append("ValueError")
                raise ValueError("first")
            if len(exceptions_raised) == 1:
                exceptions_raised.append("RuntimeError")
                raise RuntimeError("second")
            return "done"

        result = await alternating_errors()

        assert result == "done"
        assert exceptions_raised == ["ValueError", "RuntimeError"]


class TestRetryLogging:
    """로깅 테스트"""

    @pytest.mark.asyncio
    async def test_logs_warning_on_retry(self) -> None:
        """재시도 시 경고 로그 출력"""
        with patch("src.utils.retry.logger") as mock_logger:

            @with_retry(max_attempts=2, base_delay=0.01)
            async def fails_once() -> str:
                if mock_logger.warning.call_count == 0:
                    raise ValueError("temporary")
                return "success"

            # 재시도 후 성공해야 함
            try:
                await fails_once()
            except ValueError:
                pass

            # warning이 호출되었는지 확인
            assert mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_logs_error_on_final_failure(self) -> None:
        """최종 실패 시 에러 로그 출력"""
        with patch("src.utils.retry.logger") as mock_logger:

            @with_retry(max_attempts=2, base_delay=0.01)
            async def always_fails() -> None:
                raise ValueError("permanent")

            with pytest.raises(ValueError):
                await always_fails()

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "failed after 2 attempts" in call_args


class TestRetryEdgeCases:
    """엣지 케이스 테스트"""

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self) -> None:
        """함수 메타데이터 보존 (functools.wraps)"""

        @with_retry()
        async def documented_func() -> None:
            """This is a docstring."""
            pass

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a docstring."

    @pytest.mark.asyncio
    async def test_max_attempts_one(self) -> None:
        """max_attempts=1이면 재시도 없음"""

        @with_retry(max_attempts=1)
        async def no_retry() -> None:
            raise ValueError("no retry")

        with pytest.raises(ValueError):
            await no_retry()

    @pytest.mark.asyncio
    async def test_passes_arguments_correctly(self) -> None:
        """인자가 올바르게 전달됨"""

        @with_retry(max_attempts=2, base_delay=0.01)
        async def with_args(a: int, b: str, *, c: bool = False) -> dict:
            return {"a": a, "b": b, "c": c}

        result = await with_args(1, "test", c=True)

        assert result == {"a": 1, "b": "test", "c": True}
