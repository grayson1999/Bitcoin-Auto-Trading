"""Dashboard module - dashboard summary API."""

from src.modules.dashboard.routes import router
from src.modules.dashboard.schemas import DashboardSummaryResponse

__all__ = ["DashboardSummaryResponse", "router"]
