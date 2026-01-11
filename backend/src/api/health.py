"""Health check endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import APP_VERSION

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    timestamp: datetime
    version: str = APP_VERSION


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API health status.

    Returns:
        HealthResponse with status, timestamp, and version.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
    )
