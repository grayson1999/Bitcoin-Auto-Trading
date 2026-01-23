"""
Loguru Slack 핸들러 모듈

ERROR 레벨 이상의 로그를 자동으로 Slack으로 전송하는 커스텀 핸들러입니다.
- 비동기 Slack 전송을 위한 백그라운드 이벤트 루프 관리
- 중복 알림 방지를 위한 throttling 메커니즘
- 기존 Notifier 클래스 재사용
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from src.utils import UTC

if TYPE_CHECKING:
    from loguru import Record

# === 상수 ===
DEFAULT_THROTTLE_SECONDS = 1800  # 동일 메시지 재전송 방지 시간 (30분)
DEFAULT_MAX_MESSAGES_PER_MINUTE = 2  # 분당 최대 메시지 수
MESSAGE_HASH_TTL_SECONDS = 3600  # 메시지 해시 캐시 TTL (1시간)
MAX_MESSAGE_LENGTH = 1000  # Slack 메시지 최대 길이


@dataclass
class ThrottleEntry:
    """스로틀 엔트리"""

    message_hash: str
    last_sent: datetime
    count: int = 1


class SlackLogHandler:
    """
    Loguru Slack 핸들러

    ERROR 레벨 이상의 로그를 Slack으로 전송합니다.
    비동기 전송을 위해 별도의 이벤트 루프 스레드를 사용합니다.

    Attributes:
        _notifier: Notifier 인스턴스
        _loop: 백그라운드 이벤트 루프
        _thread: 이벤트 루프 실행 스레드
        _throttle_cache: 메시지 throttling 캐시
        _message_timestamps: 분당 메시지 제한용 타임스탬프
    """

    _instance: SlackLogHandler | None = None
    _lock = threading.Lock()

    def __new__(cls) -> SlackLogHandler:
        """싱글톤 패턴"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        throttle_seconds: int = DEFAULT_THROTTLE_SECONDS,
        max_messages_per_minute: int = DEFAULT_MAX_MESSAGES_PER_MINUTE,
    ) -> None:
        """
        핸들러 초기화

        Args:
            throttle_seconds: 동일 메시지 재전송 방지 시간 (초)
            max_messages_per_minute: 분당 최대 메시지 수
        """
        if getattr(self, "_initialized", False):
            return

        self._throttle_seconds = throttle_seconds
        self._max_messages_per_minute = max_messages_per_minute
        self._throttle_cache: dict[str, ThrottleEntry] = {}
        self._message_timestamps: deque[datetime] = deque(
            maxlen=max_messages_per_minute * 2
        )

        # 백그라운드 이벤트 루프 설정
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._notifier = None  # 지연 초기화

        self._initialized = True

    def _start_background_loop(self) -> None:
        """백그라운드 이벤트 루프 시작"""
        if self._thread is not None and self._thread.is_alive():
            return

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="slack-log-handler",
        )
        self._thread.start()

    def _run_loop(self) -> None:
        """이벤트 루프 실행"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _get_message_hash(self, message: str, module: str, function: str) -> str:
        """메시지 해시 생성 (중복 감지용)"""
        content = f"{module}:{function}:{message}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _should_throttle(self, message_hash: str) -> bool:
        """
        메시지 전송 여부 결정 (throttling)

        Returns:
            bool: True면 전송 안함 (throttle), False면 전송
        """
        now = datetime.now(UTC)

        # 1. 분당 메시지 제한 체크
        # 오래된 타임스탬프 제거
        cutoff = now.timestamp() - 60
        while (
            self._message_timestamps
            and self._message_timestamps[0].timestamp() < cutoff
        ):
            self._message_timestamps.popleft()

        if len(self._message_timestamps) >= self._max_messages_per_minute:
            return True

        # 2. 동일 메시지 throttling 체크
        if message_hash in self._throttle_cache:
            entry = self._throttle_cache[message_hash]
            elapsed = (now - entry.last_sent).total_seconds()

            if elapsed < self._throttle_seconds:
                entry.count += 1
                return True

        # 3. 캐시 정리 (TTL 만료 항목 제거)
        self._cleanup_throttle_cache(now)

        return False

    def _cleanup_throttle_cache(self, now: datetime) -> None:
        """만료된 throttle 캐시 정리"""
        expired_keys = [
            key
            for key, entry in self._throttle_cache.items()
            if (now - entry.last_sent).total_seconds() > MESSAGE_HASH_TTL_SECONDS
        ]
        for key in expired_keys:
            del self._throttle_cache[key]

    def _record_message(self, message_hash: str) -> None:
        """메시지 전송 기록"""
        now = datetime.now(UTC)
        self._message_timestamps.append(now)
        self._throttle_cache[message_hash] = ThrottleEntry(
            message_hash=message_hash,
            last_sent=now,
        )

    async def _send_to_slack(
        self,
        level: str,
        message: str,
        module: str,
        function: str,
        line: int,
        timestamp: datetime,
    ) -> None:
        """비동기 Slack 전송"""
        from src.modules.notification.notifier import (
            AlertLevel,
            AlertMessage,
            get_notifier,
        )

        if self._notifier is None:
            self._notifier = get_notifier()

        # 레벨 매핑
        level_map = {
            "ERROR": AlertLevel.ERROR,
            "CRITICAL": AlertLevel.CRITICAL,
        }
        alert_level = level_map.get(level.upper(), AlertLevel.ERROR)

        # 알림 메시지 생성
        alert = AlertMessage(
            title=f"[{level.upper()}] 시스템 로그 알림",
            message=message[:MAX_MESSAGE_LENGTH],
            level=alert_level,
            fields={
                "모듈": module,
                "함수": f"{function}:{line}",
                "시간": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            },
            timestamp=timestamp,
        )

        # Slack 전송 실패 시 무시 (로그 기록 시 무한 루프 방지)
        with contextlib.suppress(Exception):
            await self._notifier.send_slack_message(alert)

    def sink(self, message: Record) -> None:
        """
        Loguru 싱크 함수

        loguru.add()에 전달되는 콜백 함수입니다.
        ERROR 레벨 이상의 로그를 Slack으로 전송합니다.

        Args:
            message: loguru 로그 레코드
        """
        record = message.record
        level = record["level"].name

        # ERROR, CRITICAL만 처리
        if level not in ("ERROR", "CRITICAL"):
            return

        # 메시지 추출
        log_message = record["message"]
        module = record["name"]
        function = record["function"]
        line = record["line"]
        timestamp = record["time"].replace(tzinfo=UTC)

        # Throttling 체크
        message_hash = self._get_message_hash(log_message, module, function)
        if self._should_throttle(message_hash):
            return

        # 메시지 기록
        self._record_message(message_hash)

        # 백그라운드 루프 시작 (필요 시)
        self._start_background_loop()

        # 비동기 전송 스케줄링
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(
                self._send_to_slack(
                    level=level,
                    message=log_message,
                    module=module,
                    function=function,
                    line=line,
                    timestamp=timestamp,
                ),
                self._loop,
            )

    def close(self) -> None:
        """핸들러 종료"""
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=5)


def get_slack_log_handler() -> SlackLogHandler:
    """SlackLogHandler 싱글톤 인스턴스 반환"""
    return SlackLogHandler()
