"""
API 패키지

버전별 API 라우터를 제공합니다.
"""

from src.api.router import create_api_router

api_router = create_api_router()

__all__ = ["api_router"]
