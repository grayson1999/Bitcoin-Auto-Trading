"""
Repository 패키지

데이터베이스 접근 계층을 추상화하는 Repository 클래스를 제공합니다.
모든 Repository는 BaseRepository를 상속받아 공통 CRUD 메서드를 사용합니다.

Phase 2에서는 BaseRepository만 구현됩니다.
Phase 5 (User Story 3)에서 도메인별 Repository가 추가됩니다:
- MarketRepository
- SignalRepository
- OrderRepository
- PositionRepository
- ConfigRepository
"""

from src.repositories.base import BaseRepository

__all__ = [
    "BaseRepository",
]
