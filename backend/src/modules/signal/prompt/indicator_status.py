"""
기술적 지표 상태 코드 매핑 모듈

이 모듈은 영문 상태 코드를 한글로 변환하는 매핑을 제공합니다.
prompt_builder.py에서 사용됩니다.
"""

# RSI 상태 매핑
RSI_STATUS_KO: dict[str, str] = {
    "oversold": "과매도",
    "overbought": "과매수",
    "neutral": "중립",
}

# MACD 상태 매핑
MACD_STATUS_KO: dict[str, str] = {
    "bullish": "매수 신호",
    "bearish": "매도 신호",
    "neutral": "중립",
}

# 볼린저 밴드 상태 매핑
BB_STATUS_KO: dict[str, str] = {
    "overbought": "상단 돌파",
    "oversold": "하단 돌파",
    "upper_zone": "상단 접근",
    "lower_zone": "하단 접근",
    "neutral": "중립",
}

# EMA 배열 상태 매핑
EMA_STATUS_KO: dict[str, str] = {
    "bullish": "정배열",
    "bearish": "역배열",
    "mixed": "혼조",
}

# 변동성 수준 매핑
VOLATILITY_STATUS_KO: dict[str, str] = {
    "low": "낮음",
    "medium": "보통",
    "high": "높음",
}

# 타임프레임 이름 매핑
TIMEFRAME_NAMES_KO: dict[str, str] = {
    "1h": "1시간봉",
    "4h": "4시간봉",
    "1d": "일봉",
    "1w": "주봉",
}

# 추세 상태 매핑
TREND_STATUS_KO: dict[str, str] = {
    "bullish": "상승",
    "bearish": "하락",
    "sideways": "횡보",
}

# 종합 편향 매핑
BIAS_STATUS_KO: dict[str, str] = {
    "strong_buy": "강한 매수",
    "buy": "매수",
    "neutral": "중립",
    "sell": "매도",
    "strong_sell": "강한 매도",
}


def get_status_ko(status_map: dict[str, str], key: str) -> str:
    """
    상태 코드를 한글로 변환

    Args:
        status_map: 상태 매핑 딕셔너리
        key: 영문 상태 코드

    Returns:
        str: 한글 상태 (매핑 없으면 원본 반환)
    """
    return status_map.get(key, key)
