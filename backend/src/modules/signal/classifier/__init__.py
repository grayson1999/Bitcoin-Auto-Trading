"""Signal classifier module - coin type classification."""

from src.modules.signal.classifier.coin_classifier import (
    COIN_TYPE_MAP,
    CoinType,
    get_coin_type,
)

__all__ = [
    "COIN_TYPE_MAP",
    "CoinType",
    "get_coin_type",
]
