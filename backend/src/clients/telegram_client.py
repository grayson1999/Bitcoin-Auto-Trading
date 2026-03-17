"""
Telegram 클라이언트 모듈

Telegram Bot API를 통해 알림을 전송하는 클라이언트를 제공합니다.
- 리스크 이벤트 알림
- 거래 체결 알림
- 시스템 오류 알림
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import httpx
from loguru import logger

from src.config import settings
from src.config.constants import DEFAULT_MAX_RETRIES, DEFAULT_RETRY_DELAY_SECONDS
from src.utils import UTC

# === 상수 ===
TELEGRAM_TIMEOUT_SECONDS = 10
TELEGRAM_API_BASE = "https://api.telegram.org/bot"
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


class AlertLevel(str, Enum):
    """알림 수준"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AlertMessage:
    """알림 메시지"""

    title: str
    message: str
    level: AlertLevel = AlertLevel.INFO
    fields: dict[str, str] | None = None
    timestamp: datetime | None = None


class TelegramClientError(Exception):
    """Telegram 클라이언트 오류"""

    pass


class TelegramClient:
    """
    Telegram 클라이언트

    Telegram Bot API를 통해 알림을 전송합니다.
    봇 토큰이 설정되지 않은 경우 로그만 출력합니다.

    Attributes:
        _bot_token: Telegram Bot 토큰
        _chat_id: Telegram Chat ID
        _client: httpx 비동기 클라이언트
    """

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._bot_token = bot_token or settings.telegram_bot_token
        self._chat_id = chat_id or settings.telegram_chat_id
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        """httpx 클라이언트 반환 (지연 초기화)"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=TELEGRAM_TIMEOUT_SECONDS)
        return self._client

    async def close(self) -> None:
        """클라이언트 종료"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_emoji_for_level(self, level: AlertLevel) -> str:
        """알림 수준에 따른 이모지 반환"""
        emojis = {
            AlertLevel.INFO: "\u2139\ufe0f",
            AlertLevel.WARNING: "\u26a0\ufe0f",
            AlertLevel.ERROR: "\U0001f534",
            AlertLevel.CRITICAL: "\U0001f6a8",
        }
        return emojis.get(level, "\U0001f4e2")

    def _build_telegram_message(self, alert: AlertMessage) -> str:
        """Telegram HTML 메시지 생성"""
        timestamp = alert.timestamp or datetime.now(UTC)
        emoji = self._get_emoji_for_level(alert.level)

        lines = [
            f"<b>{emoji} {_escape_html(alert.title)}</b>",
            f"{_escape_html(alert.message)}",
        ]

        if alert.fields:
            lines.append("")
            for key, value in alert.fields.items():
                lines.append(f"{_escape_html(key)}: <code>{_escape_html(value)}</code>")

        lines.append("")
        lines.append(
            f"<i>Bitcoin Auto-Trading \u00b7 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>"
        )

        text = "\n".join(lines)
        return text[:TELEGRAM_MAX_MESSAGE_LENGTH]

    async def send_telegram_message(
        self,
        alert: AlertMessage,
    ) -> bool:
        """
        Telegram으로 메시지 전송

        Args:
            alert: 알림 메시지

        Returns:
            bool: 성공 여부
        """
        if not self._bot_token or not self._chat_id:
            logger.debug(f"Telegram 설정 미완료, 로그만 출력: {alert.title}")
            return False

        text = self._build_telegram_message(alert)
        url = f"{TELEGRAM_API_BASE}{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        client = await self._get_client()

        for attempt in range(DEFAULT_MAX_RETRIES):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                if result.get("ok"):
                    logger.debug(f"Telegram 알림 전송 성공: {alert.title}")
                    return True

                logger.warning(
                    f"Telegram API 오류 (시도 {attempt + 1}/{DEFAULT_MAX_RETRIES}): "
                    f"{result.get('description', 'Unknown error')}"
                )

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"Telegram API 오류 (시도 {attempt + 1}/{DEFAULT_MAX_RETRIES}): "
                    f"{e.response.status_code}"
                )
            except httpx.RequestError as e:
                logger.warning(
                    f"Telegram 요청 오류 (시도 {attempt + 1}/{DEFAULT_MAX_RETRIES}): {e}"
                )

            if attempt < DEFAULT_MAX_RETRIES - 1:
                await asyncio.sleep(DEFAULT_RETRY_DELAY_SECONDS)

        logger.error(f"Telegram 알림 전송 실패: {alert.title}")
        return False

    async def send_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.WARNING,
        fields: dict[str, str] | None = None,
    ) -> bool:
        """
        알림 전송

        Args:
            title: 알림 제목
            message: 알림 내용
            level: 알림 수준 (기본: WARNING)
            fields: 추가 필드 (선택)

        Returns:
            bool: 성공 여부
        """
        alert = AlertMessage(
            title=title,
            message=message,
            level=level,
            fields=fields,
            timestamp=datetime.now(UTC),
        )

        # 로그 기록
        log_msg = f"[{level.value.upper()}] {title}: {message}"
        if level == AlertLevel.CRITICAL:
            logger.critical(log_msg)
        elif level == AlertLevel.ERROR:
            logger.error(log_msg)
        elif level == AlertLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        return await self.send_telegram_message(alert)

    # === 편의 메서드 ===

    async def send_risk_alert(
        self,
        event_type: str,
        trigger_value: float,
        action: str,
    ) -> bool:
        """리스크 이벤트 알림"""
        return await self.send_alert(
            title=f"리스크 이벤트: {event_type}",
            message=action,
            level=AlertLevel.WARNING,
            fields={
                "이벤트 유형": event_type,
                "발동값": f"{trigger_value:.2f}%",
            },
        )

    async def send_trade_notification(
        self,
        side: str,
        amount: float,
        price: float,
        symbol: str | None = None,
    ) -> bool:
        """거래 체결 알림"""
        symbol = symbol or settings.trading_ticker
        emoji = "\U0001f7e2" if side.upper() == "BUY" else "\U0001f534"
        return await self.send_alert(
            title=f"{emoji} {side.upper()} 체결",
            message=f"{symbol} {amount:.8f} @ {price:,.0f}원",
            level=AlertLevel.INFO,
            fields={
                "심볼": symbol,
                "수량": f"{amount:.8f}",
                "가격": f"{price:,.0f}원",
            },
        )

    async def send_error_notification(
        self,
        error_type: str,
        error_message: str,
        context: str | None = None,
    ) -> bool:
        """시스템 오류 알림"""
        fields = {"오류 유형": error_type}
        if context:
            fields["컨텍스트"] = context

        return await self.send_alert(
            title="시스템 오류",
            message=error_message,
            level=AlertLevel.ERROR,
            fields=fields,
        )


def _escape_html(text: str) -> str:
    """Telegram HTML 특수 문자 이스케이프"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# 싱글톤 인스턴스
_telegram_client: TelegramClient | None = None


def get_telegram_client() -> TelegramClient:
    """TelegramClient 싱글톤 인스턴스 반환"""
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient()
    return _telegram_client


async def close_telegram_client() -> None:
    """TelegramClient 싱글톤 인스턴스 종료"""
    global _telegram_client
    if _telegram_client is not None:
        await _telegram_client.close()
        _telegram_client = None


# 하위 호환성을 위한 별칭
Notifier = TelegramClient
NotifierError = TelegramClientError
get_notifier = get_telegram_client
