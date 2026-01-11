"""Configuration management using Pydantic Settings."""

import re
import sys
from functools import lru_cache

from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://trading:trading@localhost:5432/trading",
        description="Async PostgreSQL connection URL",
    )

    # Upbit API
    upbit_access_key: str = Field(default="", description="Upbit API access key")
    upbit_secret_key: str = Field(default="", description="Upbit API secret key")

    # Google Gemini API
    gemini_api_key: str = Field(default="", description="Google Gemini API key")

    # Slack Webhook (Optional)
    slack_webhook_url: str | None = Field(
        default=None, description="Slack webhook URL for notifications"
    )

    # Trading Parameters
    position_size_pct: float = Field(
        default=2.0, ge=1.0, le=5.0, description="Position size as % of capital (1-5%)"
    )
    stop_loss_pct: float = Field(
        default=5.0, ge=3.0, le=10.0, description="Stop loss threshold (3-10%)"
    )
    daily_loss_limit_pct: float = Field(
        default=5.0, ge=3.0, le=10.0, description="Daily loss limit (3-10%)"
    )
    signal_interval_hours: int = Field(
        default=1, ge=1, le=4, description="AI signal generation interval in hours"
    )
    volatility_threshold_pct: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Volatility threshold for halt (1-10%)",
    )

    # Data Retention
    data_retention_days: int = Field(
        default=365, description="Market data retention period in days"
    )

    # Environment
    debug: bool = Field(default=False, description="Enable debug mode")

    # AI Model
    ai_model: str = Field(
        default="gemini-2.5-flash", description="AI model for signal generation"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()


# Patterns for masking sensitive data in logs
SENSITIVE_PATTERNS = [
    (
        re.compile(r"(upbit_access_key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I),
        r"\1***",
    ),
    (
        re.compile(r"(upbit_secret_key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I),
        r"\1***",
    ),
    (re.compile(r"(gemini_api_key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I), r"\1***"),
    (
        re.compile(r"(slack_webhook_url['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I),
        r"\1***",
    ),
    (re.compile(r"(Bearer\s+)([A-Za-z0-9\-._~+/]+=*)", re.I), r"\1***"),
    (re.compile(r"(api[_-]?key['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I), r"\1***"),
]


def mask_sensitive_data(message: str) -> str:
    """Mask sensitive data in log messages."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


def setup_logging() -> None:
    """Configure loguru logger with proper formatting and API key masking."""
    # Remove default handler
    logger.remove()

    # Custom filter to mask sensitive data in messages
    def mask_filter(record: dict) -> bool:
        """Filter that masks sensitive data in log records."""
        record["message"] = mask_sensitive_data(record["message"])
        return True

    # Log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Determine log level based on debug mode
    level = "DEBUG" if settings.debug else "INFO"

    # Add console handler with masking
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True,
        filter=mask_filter,
    )

    # Add file handler with rotation
    logger.add(
        "logs/app.log",
        format=log_format,
        level=level,
        rotation="10 MB",
        retention="1 week",
        compression="gz",
        filter=mask_filter,
    )

    logger.info("Logging configured", debug_mode=settings.debug)
