"""
Repository 패키지

데이터베이스 접근 계층을 추상화하는 Repository 클래스를 제공합니다.
모든 Repository는 BaseRepository를 상속받아 공통 CRUD 메서드를 사용합니다.

Phase 3 (User Story 1)에서 추가:
- ConfigRepository

Phase 5 (User Story 3)에서 추가:
- MarketRepository
- SignalRepository
- OrderRepository
- PositionRepository
"""

from src.repositories.base import BaseRepository
from src.repositories.config_repository import ConfigRepository
from src.repositories.market_repository import MarketRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.position_repository import PositionRepository
from src.repositories.signal_repository import SignalRepository

__all__ = [
    "BaseRepository",
    "ConfigRepository",
    "MarketRepository",
    "OrderRepository",
    "PositionRepository",
    "SignalRepository",
]
