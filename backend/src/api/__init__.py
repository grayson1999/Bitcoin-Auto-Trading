"""FastAPI routers with versioned API structure."""

from fastapi import APIRouter

from src.api.dashboard import router as dashboard_router
from src.api.health import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(dashboard_router, tags=["Dashboard"])

__all__ = ["api_router"]
