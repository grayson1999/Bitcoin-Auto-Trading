"""
코인 유형 분류 모듈

이 모듈은 코인 심볼을 기반으로 코인 유형(메이저/밈코인/알트코인)을 분류합니다.
코인 유형에 따라 다른 트레이딩 전략과 프롬프트를 적용하기 위해 사용됩니다.
"""

from enum import Enum


class CoinType(str, Enum):
    """
    코인 유형 열거형

    Attributes:
        MAJOR: 시가총액 상위 메이저 코인 (BTC, ETH, SOL 등)
        MEMECOIN: 밈코인, 고변동성 (DOGE, SHIB, MOODENG 등)
        ALTCOIN: 일반 알트코인 (분류되지 않은 코인)
    """

    MAJOR = "major"
    MEMECOIN = "memecoin"
    ALTCOIN = "altcoin"


# 정적 코인 분류 매핑 (API 호출 없이 빠르게 판단)
COIN_TYPE_MAP: dict[str, CoinType] = {
    # === 메이저 코인 (시가총액 상위, 안정적) ===
    "BTC": CoinType.MAJOR,
    "ETH": CoinType.MAJOR,
    "SOL": CoinType.MAJOR,
    "XRP": CoinType.MAJOR,
    "ADA": CoinType.MAJOR,
    "AVAX": CoinType.MAJOR,
    "DOT": CoinType.MAJOR,
    "LINK": CoinType.MAJOR,
    "MATIC": CoinType.MAJOR,
    "ATOM": CoinType.MAJOR,
    "TON": CoinType.MAJOR,
    "TRX": CoinType.MAJOR,
    "UNI": CoinType.MAJOR,
    "NEAR": CoinType.MAJOR,
    "APT": CoinType.MAJOR,
    "ARB": CoinType.MAJOR,
    "OP": CoinType.MAJOR,
    "SUI": CoinType.MAJOR,
    "SEI": CoinType.MAJOR,
    "INJ": CoinType.MAJOR,
    # === 밈코인 (고변동성, 모멘텀/거래량 중시) ===
    "DOGE": CoinType.MEMECOIN,
    "SHIB": CoinType.MEMECOIN,
    "PEPE": CoinType.MEMECOIN,
    "MOODENG": CoinType.MEMECOIN,
    "FLOKI": CoinType.MEMECOIN,
    "BONK": CoinType.MEMECOIN,
    "WIF": CoinType.MEMECOIN,
    "BRETT": CoinType.MEMECOIN,
    "POPCAT": CoinType.MEMECOIN,
    "MOG": CoinType.MEMECOIN,
    "TURBO": CoinType.MEMECOIN,
    "NEIRO": CoinType.MEMECOIN,
    "MYRO": CoinType.MEMECOIN,
    "DOGWIFHAT": CoinType.MEMECOIN,
}


def get_coin_type(currency: str) -> CoinType:
    """
    코인 심볼로 코인 유형 결정

    Args:
        currency: 코인 심볼 (예: "SOL", "DOGE", "UNKNOWN")

    Returns:
        CoinType: 코인 유형
            - MAJOR: 매핑된 메이저 코인
            - MEMECOIN: 매핑된 밈코인
            - ALTCOIN: 매핑에 없는 코인 (기본값)

    Examples:
        >>> get_coin_type("BTC")
        CoinType.MAJOR
        >>> get_coin_type("DOGE")
        CoinType.MEMECOIN
        >>> get_coin_type("UNKNOWN123")
        CoinType.ALTCOIN
    """
    return COIN_TYPE_MAP.get(currency.upper(), CoinType.ALTCOIN)
