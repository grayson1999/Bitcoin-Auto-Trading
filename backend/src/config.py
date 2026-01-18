"""
환경 설정 관리 모듈

이 모듈은 Pydantic Settings를 사용하여 애플리케이션 설정을 관리합니다.
- 환경 변수 및 .env 파일에서 설정 로드
- 거래 파라미터 검증 (범위 제한)
- 민감 정보 마스킹 (API 키 등)
- loguru 로깅 설정
"""

import re
import sys
from functools import lru_cache

from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 애플리케이션 버전
APP_VERSION = "0.1.0"

# === 데이터베이스 풀 설정 ===
DB_POOL_SIZE = 5  # 기본 풀 크기 (동시 연결 수)
DB_POOL_MAX_OVERFLOW = 10  # 풀 초과 시 추가 허용 연결 수 (최대 15개)


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스

    환경 변수 또는 .env 파일에서 설정을 자동으로 로드합니다.
    Pydantic의 Field를 사용하여 기본값과 유효성 검증 규칙을 정의합니다.

    Attributes:
        database_url: PostgreSQL 비동기 연결 URL
        upbit_access_key: Upbit API 접근 키
        upbit_secret_key: Upbit API 비밀 키
        gemini_api_key: Google Gemini AI API 키
        slack_webhook_url: Slack 알림 웹훅 URL (선택사항)
        position_size_pct: 주문당 자본 비율 (1-5%)
        stop_loss_pct: 손절매 임계값 (3-10%)
        daily_loss_limit_pct: 일일 손실 한도 (3-10%)
        signal_interval_hours: AI 신호 생성 주기 (1-4시간)
        volatility_threshold_pct: 거래 중단 변동성 임계값 (1-10%)
        data_retention_days: 시장 데이터 보관 기간 (일)
        debug: 디버그 모드 활성화 여부
        ai_model: AI 신호 생성에 사용할 모델
    """

    model_config = SettingsConfigDict(
        env_file=".env",  # .env 파일에서 설정 로드
        env_file_encoding="utf-8",
        case_sensitive=False,  # 대소문자 구분 없음
    )

    # === 데이터베이스 설정 ===
    database_url: str = Field(
        default="postgresql+asyncpg://trading:trading@localhost:5432/trading",
        description="비동기 PostgreSQL 연결 URL",
    )

    # === Upbit API 설정 ===
    upbit_access_key: str = Field(default="", description="Upbit API 접근 키")
    upbit_secret_key: str = Field(default="", description="Upbit API 비밀 키")

    # === Google Gemini API 설정 ===
    gemini_api_key: str = Field(default="", description="Google Gemini API 키")

    # === OpenAI API 설정 (백업) ===
    openai_api_key: str = Field(default="", description="OpenAI API 키 (백업용)")

    # === Slack 웹훅 설정 (선택사항) ===
    slack_webhook_url: str | None = Field(
        default=None, description="Slack 알림 웹훅 URL"
    )

    # === 거래 파라미터 ===
    # 각 파라미터는 ge(이상), le(이하)로 유효 범위가 제한됨
    position_size_pct: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="주문당 자본 비율 (1-5%)",
    )
    stop_loss_pct: float = Field(
        default=5.0,
        ge=3.0,
        le=10.0,
        description="손절매 임계값 (3-10%)",
    )
    daily_loss_limit_pct: float = Field(
        default=5.0,
        ge=3.0,
        le=10.0,
        description="일일 손실 한도 (3-10%)",
    )
    signal_interval_hours: int = Field(
        default=1,
        ge=1,
        le=4,
        description="AI 신호 생성 주기 (1-4시간)",
    )
    volatility_threshold_pct: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="거래 중단 변동성 임계값 (1-10%)",
    )

    # === 데이터 보관 설정 ===
    data_retention_days: int = Field(
        default=365, description="시장 데이터 보관 기간 (일)"
    )

    # === 환경 설정 ===
    debug: bool = Field(default=False, description="디버그 모드 활성화")

    # === AI 모델 설정 ===
    ai_model: str = Field(default="gemini-2.5-pro", description="AI 신호 생성 모델")
    ai_fallback_model: str = Field(
        default="gpt-4o", description="AI Fallback 모델 (Gemini 실패 시)"
    )

    # === Auth Server 설정 ===
    auth_server_url: str = Field(
        default="http://localhost:8001",
        description="Auth Server URL for token verification",
    )


@lru_cache
def get_settings() -> Settings:
    """
    설정 인스턴스 반환 (싱글톤)

    lru_cache 데코레이터를 사용하여 설정 인스턴스를 캐싱합니다.
    애플리케이션 전체에서 동일한 설정 인스턴스를 공유합니다.

    Returns:
        Settings: 캐싱된 설정 인스턴스
    """
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()


# === 민감 정보 마스킹 패턴 ===
# 로그에서 API 키와 같은 민감 정보를 숨기기 위한 정규표현식 패턴
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
    # 기본 핸들러 제거
    logger.remove()

    def mask_filter(record: dict) -> bool:
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
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "  # 타임스탬프 (녹색)
        "<level>{level: <8}</level> | "  # 로그 레벨
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "  # 위치 (청록)
        "<level>{message}</level>"  # 메시지
    )

    # 디버그 모드에 따른 로그 레벨 결정
    level = "DEBUG" if settings.debug else "INFO"

    # 콘솔 핸들러 추가 (stderr 출력)
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True,  # 색상 출력 활성화
        filter=mask_filter,  # 민감 정보 마스킹 필터
    )

    # 파일 핸들러 추가 (로그 로테이션)
    logger.add(
        "logs/app.log",
        format=log_format,
        level=level,
        rotation="10 MB",  # 10MB마다 새 파일 생성
        retention="1 week",  # 1주일간 보관
        compression="gz",  # gzip 압축
        filter=mask_filter,
    )

    # Slack 핸들러 추가 (ERROR 레벨 이상만)
    if settings.slack_webhook_url:
        from src.services.slack_log_handler import get_slack_log_handler

        slack_handler = get_slack_log_handler()
        logger.add(
            slack_handler.sink,
            level="ERROR",
            filter=mask_filter,
            format="{message}",  # 간단한 포맷 (AlertMessage에서 구조화)
        )
        logger.info("Slack 로그 핸들러 활성화됨")

    logger.info("로깅 설정 완료", debug_mode=settings.debug)
