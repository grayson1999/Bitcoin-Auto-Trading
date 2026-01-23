"""
로깅 설정 모듈

loguru를 사용한 로깅 설정을 관리합니다.
- 콘솔 출력 (색상)
- 파일 로깅 (로테이션, 압축)
- 민감 정보 마스킹
- Slack 알림 (ERROR 레벨 이상)
"""

import re
import sys
from typing import TYPE_CHECKING

from loguru import logger

from src.config.constants import LOG_RETENTION_PERIOD, LOG_ROTATION_SIZE

if TYPE_CHECKING:
    from loguru import Record

# === 민감 정보 마스킹 패턴 ===
SENSITIVE_PATTERNS = [
    # Upbit API 키 마스킹
    (
        re.compile(r"(upbit_access_key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I),
        r"\1***",
    ),
    (
        re.compile(r"(upbit_secret_key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I),
        r"\1***",
    ),
    # Gemini API 키 마스킹
    (re.compile(r"(gemini_api_key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I), r"\1***"),
    # OpenAI API 키 마스킹
    (re.compile(r"(openai_api_key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I), r"\1***"),
    # Slack 웹훅 URL 마스킹
    (
        re.compile(r"(slack_webhook_url['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I),
        r"\1***",
    ),
    # Bearer 토큰 마스킹
    (re.compile(r"(Bearer\s+)([A-Za-z0-9\-._~+/]+=*)", re.I), r"\1***"),
    # 일반 API 키 마스킹
    (re.compile(r"(api[_-]?key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I), r"\1***"),
]


def mask_sensitive_data(message: str) -> str:
    """
    로그 메시지에서 민감 정보 마스킹

    API 키, 토큰 등의 민감 정보를 '***'로 대체합니다.

    Args:
        message: 원본 로그 메시지

    Returns:
        str: 민감 정보가 마스킹된 메시지
    """
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


def setup_logging() -> None:
    """
    loguru 로거 설정

    콘솔과 파일 로깅을 설정합니다.
    - 콘솔: 색상 출력, 민감 정보 마스킹
    - 파일: 10MB 로테이션, 1주 보관, gzip 압축

    로그 포맷:
        시간 | 레벨 | 모듈:함수:라인 | 메시지
    """
    from src.config.settings import settings

    # 기본 핸들러 제거
    logger.remove()

    def mask_filter(record: "Record") -> bool:
        """
        로그 레코드 필터

        모든 로그 메시지에서 민감 정보를 마스킹합니다.

        Args:
            record: loguru 로그 레코드

        Returns:
            bool: 항상 True (모든 로그 통과)
        """
        record["message"] = mask_sensitive_data(record["message"])
        return True

    # 로그 포맷 정의
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 디버그 모드에 따른 로그 레벨 결정
    level = "DEBUG" if settings.debug else "INFO"

    # 콘솔 핸들러 추가 (stderr 출력)
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True,
        filter=mask_filter,
    )

    # 파일 핸들러 추가 (로그 로테이션)
    logger.add(
        "logs/app.log",
        format=log_format,
        level=level,
        rotation=LOG_ROTATION_SIZE,
        retention=LOG_RETENTION_PERIOD,
        compression="gz",
        filter=mask_filter,
    )

    # Slack 핸들러 추가 (ERROR 레벨 이상만)
    if settings.slack_webhook_url:
        from src.modules.notification import get_slack_log_handler

        slack_handler = get_slack_log_handler()
        logger.add(
            slack_handler.sink,
            level="ERROR",
            filter=mask_filter,
            format="{message}",
        )
        logger.info("Slack 로그 핸들러 활성화됨")

    logger.info("로깅 설정 완료", debug_mode=settings.debug)
