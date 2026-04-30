"""Prices router for fetching and managing NAV/prices."""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.background_jobs import background_jobs
from app.services.price_service import PriceService
from app.services.storage_service import StorageService
from app.services.yahoo_finance import YahooFinanceService

router = APIRouter(prefix="/api/prices", tags=["prices"])
logger = logging.getLogger(__name__)
PRICE_FETCH_JOB = "price_fetch"


def _get_user_isins(user_data: dict[str, Any]) -> list[str]:
	"""Return unique finalized order ISINs for a user."""
	orders = user_data.get("orders", [])
	finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]
	return sorted({o.get("isin") for o in finalized_orders if o.get("isin")})


def _get_stale_or_missing_isins(user_data: dict[str, Any]) -> list[str]:
	"""Return ISINs whose cached price is missing or stale."""
	prices = user_data.get("prices", {})
	isins = _get_user_isins(user_data)
	return [isin for isin in isins if not PriceService.is_fresh(prices, isin)]


async def _fetch_and_clear_active(username: str, isins: list[str], force: bool) -> None:
	"""Run a price fetch and record job state after completion."""
	background_jobs.start(username, PRICE_FETCH_JOB)
	try:
		await PriceService.fetch_and_update_prices(username, isins, force=force)
	except Exception as e:
		background_jobs.fail(username, PRICE_FETCH_JOB, str(e))
		raise
	else:
		background_jobs.complete(username, PRICE_FETCH_JOB, {"count": len(isins), "force": force})


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
	unique_isins = _get_user_isins(user_data)

	if not unique_isins:
		return {
			"success": True,
			"message": "No instruments found to fetch prices for",
			"count": 0,
		}

	logger.info(f"Queueing price fetch for {len(unique_isins)} ISINs - User: {current_user.username}")

	if background_jobs.is_active(current_user.username, PRICE_FETCH_JOB):
		return {
			"success": True,
			"queued": False,
			"in_progress": True,
			"job_type": PRICE_FETCH_JOB,
			"message": "Price refresh already in progress",
			"count": 0,
		}

	background_jobs.queue(current_user.username, PRICE_FETCH_JOB, len(unique_isins))
	background_tasks.add_task(_fetch_and_clear_active, current_user.username, unique_isins, True)

	return {
		"success": True,
		"queued": True,
		"in_progress": False,
		"job_type": PRICE_FETCH_JOB,
		"message": f"Fetching prices for {len(unique_isins)} instruments",
		"count": len(unique_isins),
	}


@router.post("/refresh-if-needed")
async def refresh_prices_if_needed(
	background_tasks: BackgroundTasks,
	current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
	"""Queue a background price refresh only when cached prices are missing or stale."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	if background_jobs.is_active(current_user.username, PRICE_FETCH_JOB):
		return {
			"success": True,
			"queued": False,
			"in_progress": True,
			"job_type": PRICE_FETCH_JOB,
			"count": 0,
			"message": "Price refresh already in progress",
		}

	user_data = users[current_user.username]
	stale_or_missing_isins = _get_stale_or_missing_isins(user_data)

	if not stale_or_missing_isins:
		return {
			"success": True,
			"queued": False,
			"in_progress": False,
			"count": 0,
			"message": "All cached prices are fresh",
		}

	background_jobs.queue(current_user.username, PRICE_FETCH_JOB, len(stale_or_missing_isins))
	background_tasks.add_task(_fetch_and_clear_active, current_user.username, stale_or_missing_isins, False)

	return {
		"success": True,
		"queued": True,
		"in_progress": False,
		"job_type": PRICE_FETCH_JOB,
		"count": len(stale_or_missing_isins),
		"message": f"Refreshing {len(stale_or_missing_isins)} stale or missing prices",
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
		"refreshing": background_jobs.is_active(current_user.username, PRICE_FETCH_JOB),
		"job": background_jobs.get(current_user.username, PRICE_FETCH_JOB),
		"cache_hours": settings.PRICE_CACHE_HOURS,
	}
