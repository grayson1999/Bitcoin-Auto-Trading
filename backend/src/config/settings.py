"""
애플리케이션 설정 관리 모듈

Pydantic BaseSettings를 사용하여 환경 변수 및 .env 파일에서 설정을 로드합니다.
DB 오버라이드가 가능한 필드는 주석으로 표시됩니다.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스

    환경 변수 또는 .env 파일에서 설정을 자동으로 로드합니다.
    Pydantic의 Field를 사용하여 기본값과 유효성 검증 규칙을 정의합니다.

    DB 오버라이드 가능 필드:
        - position_size_min_pct, position_size_max_pct
        - stop_loss_pct, daily_loss_limit_pct
        - signal_interval_hours, ai_model
        - volatility_threshold_pct, trading_ticker
        - trading_enabled

    환경변수 전용 (민감 정보):
        - database_url, upbit_access_key, upbit_secret_key
        - gemini_api_key, openai_api_key
        - slack_webhook_url, auth_server_url
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # === 데이터베이스 설정 (환경변수 전용) ===
    database_url: str = Field(
        default="postgresql+asyncpg://trading:trading@localhost:5432/trading",
        description="비동기 PostgreSQL 연결 URL",
    )

    # === Upbit API 설정 (환경변수 전용) ===
    upbit_access_key: str = Field(default="", description="Upbit API 접근 키")
    upbit_secret_key: str = Field(default="", description="Upbit API 비밀 키")

    # === Google Gemini API 설정 (환경변수 전용) ===
    gemini_api_key: str = Field(default="", description="Google Gemini API 키")

    # === OpenAI API 설정 (환경변수 전용) ===
    openai_api_key: str = Field(default="", description="OpenAI API 키 (백업용)")

    # === Slack 웹훅 설정 (환경변수 전용) ===
    slack_webhook_url: str | None = Field(
        default=None, description="Slack 알림 웹훅 URL"
    )

    # === Auth Server 설정 (환경변수 전용) ===
    auth_server_url: str = Field(
        default="http://localhost:9000",
        description="Auth Server URL for token verification",
    )

    # === 거래 파라미터 (DB 오버라이드 가능) ===
    # 동적 포지션 사이징: AI 신뢰도에 따라 min~max 범위에서 계산
    position_size_min_pct: float = Field(
        default=25.0,
        ge=1.0,
        le=50.0,
        description="최소 포지션 크기 비율 (신뢰도 낮을 때) [DB 오버라이드 가능]",
    )
    position_size_max_pct: float = Field(
        default=50.0,
        ge=5.0,
        le=100.0,
        description="최대 포지션 크기 비율 (신뢰도 높을 때) [DB 오버라이드 가능]",
    )
    # 기존 호환성을 위해 유지 (deprecated)
    position_size_pct: float = Field(
        default=2.0,
        ge=1.0,
        le=100.0,
        description="주문당 자본 비율 (deprecated) [DB 오버라이드 가능]",
    )
    stop_loss_pct: float = Field(
        default=5.0,
        ge=3.0,
        le=10.0,
        description="손절매 임계값 (3-10%) [DB 오버라이드 가능]",
    )
    daily_loss_limit_pct: float = Field(
        default=5.0,
        ge=3.0,
        le=10.0,
        description="일일 손실 한도 (3-10%) [DB 오버라이드 가능]",
    )
    signal_interval_hours: int = Field(
        default=1,
        ge=1,
        le=4,
        description="AI 신호 생성 주기 (1-4시간) [DB 오버라이드 가능]",
    )
    volatility_threshold_pct: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="거래 중단 변동성 임계값 (1-10%) [DB 오버라이드 가능]",
    )

    # === 환경 설정 ===
    debug: bool = Field(default=False, description="디버그 모드 활성화")

    # === AI 모델 설정 (DB 오버라이드 가능) ===
    ai_model: str = Field(
        default="gemini-2.5-pro",
        description="AI 신호 생성 모델 [DB 오버라이드 가능]",
    )
    ai_fallback_model: str = Field(
        default="gpt-4.1-mini", description="AI Fallback 모델 (Gemini 실패 시)"
    )

    # === 거래 대상 설정 (DB 오버라이드 가능) ===
    trading_ticker: str = Field(
        default="KRW-SOL",
        description="거래 마켓 코드 [DB 오버라이드 가능]",
    )
    trading_currency: str = Field(
        default="SOL",
        description="거래 코인 심볼 (예: SOL, BTC, MOODENG)",
    )

    # === AI 신호 손절/익절 비율 ===
    signal_stop_loss_pct: float = Field(
        default=0.015,
        ge=0.005,
        le=0.10,
        description="AI 신호 손절 비율 (0.015 = 1.5%)",
    )
    signal_take_profit_pct: float = Field(
        default=0.025,
        ge=0.01,
        le=0.20,
        description="AI 신호 익절 비율 (0.025 = 2.5%)",
    )
    signal_trailing_stop_pct: float = Field(
        default=0.02,
        ge=0.005,
        le=0.10,
        description="트레일링 스탑 활성화 수익률 (0.02 = 2%)",
    )
    signal_breakeven_pct: float = Field(
        default=0.01,
        ge=0.005,
        le=0.05,
        description="본전 손절 활성화 수익률 (0.01 = 1%)",
    )

    # === 변동성 돌파 전략 설정 (참고용) ===
    volatility_k_value: float = Field(
        default=0.6,
        ge=0.1,
        le=1.0,
        description="변동성 돌파 K 계수 (0.1-1.0) - AI 참고용",
    )
    hybrid_mode_enabled: bool = Field(
        default=False,
        description="[Deprecated] 하이브리드 모드 비활성화 - AI가 직접 판단",
    )
    breakout_min_strength: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="[Deprecated] 최소 돌파 강도 - AI가 직접 판단",
    )


# DB 오버라이드 가능한 설정 키 목록
DB_OVERRIDABLE_KEYS = frozenset(
    {
        "position_size_min_pct",
        "position_size_max_pct",
        "position_size_pct",
        "stop_loss_pct",
        "daily_loss_limit_pct",
        "signal_interval_hours",
        "volatility_threshold_pct",
        "ai_model",
        "trading_ticker",
        "trading_enabled",
    }
)


@lru_cache
def get_settings() -> Settings:
    """
    설정 인스턴스 반환 (싱글톤)

    lru_cache 데코레이터를 사용하여 설정 인스턴스를 캐싱합니다.

    Returns:
        Settings: 캐싱된 설정 인스턴스
    """
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
