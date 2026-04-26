"""Prices router for fetching and managing NAV/prices."""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.price_service import PriceService
from app.services.storage_service import StorageService
from app.services.yahoo_finance import YahooFinanceService

router = APIRouter(prefix="/api/prices", tags=["prices"])
logger = logging.getLogger(__name__)


@router.post("/fetch")
async def fetch_prices(
	background_tasks: BackgroundTasks,
	current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
	"""
	Fetch current prices for all ISINs in user's portfolio.

	This triggers a background task that fetches prices from Yahoo Finance
	and updates the user's price data.
	"""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	user_data = users[current_user.username]
	orders = user_data.get("orders", [])

	# Get unique ISINs from finalized orders
	finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]
	unique_isins = list(set(o.get("isin") for o in finalized_orders if o.get("isin")))

	if not unique_isins:
		return {
			"success": True,
			"message": "No instruments found to fetch prices for",
			"count": 0,
		}

	logger.info(f"Queueing price fetch for {len(unique_isins)} ISINs - User: {current_user.username}")

	# Queue background task
	background_tasks.add_task(PriceService.fetch_and_update_prices, current_user.username, unique_isins)

	return {
		"success": True,
		"message": f"Fetching prices for {len(unique_isins)} instruments",
		"count": len(unique_isins),
	}


@router.get("/status")
async def get_price_status(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get status of cached prices (how many, how old)."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	user_data = users[current_user.username]
	prices = user_data.get("prices", {})
	yahoo = YahooFinanceService()

	stale_count = 0
	fresh_count = 0

	for _isin, price_data in prices.items():
		timestamp = price_data.get("timestamp", "")
		if yahoo.is_price_stale(timestamp):
			stale_count += 1
		else:
			fresh_count += 1

	return {
		"total": len(prices),
		"fresh": fresh_count,
		"stale": stale_count,
		"cache_hours": settings.PRICE_CACHE_HOURS,
	}
