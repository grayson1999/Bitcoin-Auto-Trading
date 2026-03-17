"""
알림 서비스 모듈

이 모듈은 다양한 채널로 알림을 전송하는 서비스를 제공합니다.
- Telegram Bot API 알림
- 리스크 이벤트, 거래 체결, 시스템 오류 알림

Note: 실제 구현은 clients/telegram_client.py에 있으며,
이 모듈은 하위 호환성을 위해 re-export합니다.
"""

from src.clients.telegram_client import (
    AlertLevel,
    AlertMessage,
    Notifier,
    NotifierError,
    TelegramClient,
    TelegramClientError,
    get_notifier,
    get_telegram_client,
)

__all__ = [
    "AlertLevel",
    "AlertMessage",
    "Notifier",
    "NotifierError",
    "TelegramClient",
    "TelegramClientError",
    "get_notifier",
    "get_telegram_client",
]
