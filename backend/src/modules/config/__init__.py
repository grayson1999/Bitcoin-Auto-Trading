"""
설정 모듈

시스템 설정 관리 기능을 제공합니다.
- ConfigService: DB 우선순위 설정 조회/수정
- ConfigRepository: 설정 DB 접근 계층
- routes: 설정 API 엔드포인트 (/api/v1/config)
- schemas: 요청/응답 Pydantic 모델
"""

from src.modules.config.routes import router
from src.modules.config.service import ConfigService

__all__ = [
    "ConfigService",
    "router",
]
