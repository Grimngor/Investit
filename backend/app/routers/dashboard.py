"""Dashboard router for KPIs and portfolio metrics."""

from typing import Any

from fastapi import APIRouter, Depends

from app.models.user import User
from app.routers.auth import get_current_user
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis")
async def get_kpis(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get dashboard KPIs for current user."""
	return DashboardService.get_kpis(current_user.username)


@router.get("/time-series")
async def get_time_series(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get time series data for portfolio value over time."""
	return DashboardService.get_time_series(current_user.username)


@router.get("/allocations")
async def get_allocations(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get allocation data for pie charts."""
	return DashboardService.get_allocations(current_user.username)


@router.get("/price-status")
async def get_price_status(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get price status to check for stale prices."""
	return DashboardService.get_price_status(current_user.username)
