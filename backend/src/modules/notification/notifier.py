"""
알림 서비스 모듈

이 모듈은 다양한 채널로 알림을 전송하는 서비스를 제공합니다.
- Slack 웹훅 알림
- 리스크 이벤트, 거래 체결, 시스템 오류 알림
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import httpx
from loguru import logger

from src.config import settings
from src.utils import UTC

# === 상수 ===
SLACK_TIMEOUT_SECONDS = 10  # Slack API 타임아웃
MAX_RETRY_ATTEMPTS = 3  # 최대 재시도 횟수
RETRY_DELAY_SECONDS = 1  # 재시도 간격


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


class NotifierError(Exception):
    """알림 서비스 오류"""

    pass


class Notifier:
    """
    알림 서비스

    Slack 웹훅을 통해 알림을 전송합니다.
    웹훅 URL이 설정되지 않은 경우 로그만 출력합니다.

    Attributes:
        _webhook_url: Slack 웹훅 URL
        _client: httpx 비동기 클라이언트
    """

    def __init__(
        self,
        webhook_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """
        Notifier 초기화

        Args:
            webhook_url: Slack 웹훅 URL (기본: 설정에서 로드)
            client: httpx 클라이언트 (기본: 새로 생성)
        """
        self._webhook_url = webhook_url or settings.slack_webhook_url
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        """httpx 클라이언트 반환 (지연 초기화)"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=SLACK_TIMEOUT_SECONDS)
        return self._client

    async def close(self) -> None:
        """클라이언트 종료"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_color_for_level(self, level: AlertLevel) -> str:
        """알림 수준에 따른 색상 반환"""
        colors = {
            AlertLevel.INFO: "#36a64f",  # 녹색
            AlertLevel.WARNING: "#ffcc00",  # 노란색
            AlertLevel.ERROR: "#ff6600",  # 주황색
            AlertLevel.CRITICAL: "#ff0000",  # 빨간색
        }
        return colors.get(level, "#808080")

    def _get_emoji_for_level(self, level: AlertLevel) -> str:
        """알림 수준에 따른 이모지 반환"""
        emojis = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "🔴",
            AlertLevel.CRITICAL: "🚨",
        }
        return emojis.get(level, "📢")

    def _build_slack_payload(self, alert: AlertMessage) -> dict:
        """Slack 메시지 페이로드 생성"""
        timestamp = alert.timestamp or datetime.now(UTC)
        color = self._get_color_for_level(alert.level)
        emoji = self._get_emoji_for_level(alert.level)

        attachment: dict = {
            "color": color,
            "title": f"{emoji} {alert.title}",
            "text": alert.message,
            "footer": "Bitcoin Auto-Trading",
            "ts": int(timestamp.timestamp()),
        }

        # 추가 필드가 있는 경우
        if alert.fields:
            attachment["fields"] = [
                {"title": k, "value": v, "short": True} for k, v in alert.fields.items()
            ]

        return {"attachments": [attachment]}

    async def send_slack_message(
        self,
        alert: AlertMessage,
    ) -> bool:
        """
        Slack으로 메시지 전송

        Args:
            alert: 알림 메시지

        Returns:
            bool: 성공 여부
        """
        if not self._webhook_url:
            logger.debug(f"Slack 웹훅 미설정, 로그만 출력: {alert.title}")
            return False

        payload = self._build_slack_payload(alert)
        client = await self._get_client()

        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                response = await client.post(
                    self._webhook_url,
                    json=payload,
                )
                response.raise_for_status()
                logger.debug(f"Slack 알림 전송 성공: {alert.title}")
                return True

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"Slack API 오류 (시도 {attempt + 1}/{MAX_RETRY_ATTEMPTS}): "
                    f"{e.response.status_code}"
                )
            except httpx.RequestError as e:
                logger.warning(
                    f"Slack 요청 오류 (시도 {attempt + 1}/{MAX_RETRY_ATTEMPTS}): {e}"
                )

            if attempt < MAX_RETRY_ATTEMPTS - 1:
                await asyncio.sleep(RETRY_DELAY_SECONDS)

        logger.error(f"Slack 알림 전송 실패: {alert.title}")
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

        # Slack 전송
        return await self.send_slack_message(alert)

    # === 편의 메서드 ===

    async def send_risk_alert(
        self,
        event_type: str,
        trigger_value: float,
        action: str,
    ) -> bool:
        """
        리스크 이벤트 알림

        Args:
            event_type: 이벤트 유형
            trigger_value: 발동값
            action: 수행된 조치

        Returns:
            bool: 성공 여부
        """
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
        """
        거래 체결 알림

        Args:
            side: 매수/매도
            amount: 거래량
            price: 체결가
            symbol: 심볼 (기본값: settings.trading_ticker)

        Returns:
            bool: 성공 여부
        """
        symbol = symbol or settings.trading_ticker
        emoji = "🟢" if side.upper() == "BUY" else "🔴"
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
        """
        시스템 오류 알림

        Args:
            error_type: 오류 유형
            error_message: 오류 메시지
            context: 추가 컨텍스트 (선택)

        Returns:
            bool: 성공 여부
        """
        fields = {"오류 유형": error_type}
        if context:
            fields["컨텍스트"] = context

        return await self.send_alert(
            title="시스템 오류",
            message=error_message,
            level=AlertLevel.ERROR,
            fields=fields,
        )


# 싱글톤 인스턴스
_notifier: Notifier | None = None


def get_notifier() -> Notifier:
    """
    Notifier 싱글톤 인스턴스 반환

    Returns:
        Notifier: 알림 서비스 인스턴스
    """
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier
