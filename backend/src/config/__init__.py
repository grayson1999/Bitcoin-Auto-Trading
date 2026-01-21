"""
설정 패키지

애플리케이션 설정, 상수, 로깅을 통합 관리합니다.

사용 예시:
    from src.config import settings, APP_VERSION, setup_logging

    # 설정 접근
    db_url = settings.database_url

    # 상수 접근
    print(f"Version: {APP_VERSION}")

    # 로깅 초기화
    setup_logging()
"""

from src.config.constants import (
    APP_NAME,
    APP_VERSION,
    DATA_CLEANUP_INTERVAL_HOURS,
    DATA_COLLECTION_INTERVAL_SECONDS,
    DB_POOL_MAX_OVERFLOW,
    DB_POOL_SIZE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    ERROR_INTERNAL_SERVER,
    ERROR_NOT_FOUND,
    ERROR_UNAUTHORIZED,
    HTTP_STATUS_BAD_REQUEST,
    HTTP_STATUS_CREATED,
    HTTP_STATUS_FORBIDDEN,
    HTTP_STATUS_INTERNAL_SERVER_ERROR,
    HTTP_STATUS_NOT_FOUND,
    HTTP_STATUS_OK,
    HTTP_STATUS_UNAUTHORIZED,
    LOG_RETENTION_DAYS,
    LOG_RETENTION_PERIOD,
    LOG_ROTATION_SIZE,
    UPBIT_FEE_RATE,
    UPBIT_MIN_ORDER_KRW,
    UPBIT_RATE_LIMIT_ORDER,
    UPBIT_RATE_LIMIT_QUERY,
)
from src.config.logging import mask_sensitive_data, setup_logging
from src.config.settings import DB_OVERRIDABLE_KEYS, Settings, get_settings, settings

__all__ = [
    # Settings
    "Settings",
    "settings",
    "get_settings",
    "DB_OVERRIDABLE_KEYS",
    # Constants
    "APP_NAME",
    "APP_VERSION",
    "DB_POOL_SIZE",
    "DB_POOL_MAX_OVERFLOW",
    "UPBIT_FEE_RATE",
    "UPBIT_MIN_ORDER_KRW",
    "UPBIT_RATE_LIMIT_ORDER",
    "UPBIT_RATE_LIMIT_QUERY",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY_SECONDS",
    "DEFAULT_TIMEOUT_SECONDS",
    "LOG_ROTATION_SIZE",
    "LOG_RETENTION_DAYS",
    "LOG_RETENTION_PERIOD",
    "DATA_COLLECTION_INTERVAL_SECONDS",
    "DATA_CLEANUP_INTERVAL_HOURS",
    "HTTP_STATUS_OK",
    "HTTP_STATUS_CREATED",
    "HTTP_STATUS_BAD_REQUEST",
    "HTTP_STATUS_UNAUTHORIZED",
    "HTTP_STATUS_FORBIDDEN",
    "HTTP_STATUS_NOT_FOUND",
    "HTTP_STATUS_INTERNAL_SERVER_ERROR",
    "ERROR_INTERNAL_SERVER",
    "ERROR_UNAUTHORIZED",
    "ERROR_NOT_FOUND",
    # Logging
    "setup_logging",
    "mask_sensitive_data",
]
