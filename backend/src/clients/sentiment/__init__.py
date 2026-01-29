"""
감성/심리 데이터 클라이언트 패키지

외부 API를 통해 시장 심리 지표를 조회합니다.
"""

from src.clients.sentiment.fear_greed import (
    FearGreedClient,
    FearGreedData,
    get_fear_greed_client,
)

__all__ = [
    "FearGreedClient",
    "FearGreedData",
    "get_fear_greed_client",
]
