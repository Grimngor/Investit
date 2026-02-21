"""Prices router for fetching and managing NAV/prices."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.websocket import manager as websocket_manager
from app.services.morningstar_service import MorningstarService
from app.services.storage_service import StorageService
from app.services.yahoo_finance import YahooFinanceService
from app.services.yahooquery_service import YahooQueryService
from app.utils.validators import is_crypto_symbol

router = APIRouter(prefix="/api/prices", tags=["prices"])
logger = logging.getLogger(__name__)


def _is_fresh(prices: dict[str, Any], isin: str, yahoo: YahooFinanceService) -> bool:
	existing = prices.get(isin)
	if not existing:
		return False
	return not yahoo.is_price_stale(existing.get("timestamp", ""))


async def _fetch_crypto(isin: str, yahoo: YahooFinanceService) -> dict[str, Any] | None:
	quote = await yahoo.get_crypto_quote(isin, currency="EUR")
	if not quote:
		return None
	return {
		"price": quote["price"],
		"currency": quote["currency"],
		"timestamp": quote["timestamp"],
		"name": quote.get("name", f"{isin} Cryptocurrency"),
		"symbol": quote.get("symbol", isin),
		"asset_type": "Crypto",
	}


async def _fetch_traditional(
	isin: str,
	yahoo: YahooFinanceService,
	yahooquery: YahooQueryService,
	morningstar: MorningstarService,
	storage: StorageService,
) -> dict[str, Any] | None:
	suffixes = ["", ".PA", ".AS", ".DE", ".MI"]
	for idx, suffix in enumerate(suffixes):
		symbol = f"{isin}{suffix}"
		quote = await yahoo.get_quote(symbol)
		if quote:
			resolved = quote.get("symbol", symbol)
			data = {
				"price": quote["price"],
				"currency": quote["currency"],
				"timestamp": quote["timestamp"],
				"name": quote.get("name", isin),
				"symbol": resolved,
			}
			# Metadata enrichment
			mstar = await morningstar.get_fund_metadata(isin)
			instrument_data = {"name": data["name"], "symbol": resolved}
			if mstar:
				instrument_data["name"] = mstar.get("name") or instrument_data["name"]
				if mstar.get("sector_allocation"):
					instrument_data["sector_allocation"] = mstar["sector_allocation"]
				if mstar.get("regional_allocation"):
					instrument_data["geo_allocation"] = mstar["regional_allocation"]
				if mstar.get("morningstar_code"):
					instrument_data["type"] = "Fund"
			if not mstar or not instrument_data.get("sector_allocation"):
				yq = await yahooquery.get_fund_metadata(resolved)
				if yq:
					if not instrument_data.get("sector_allocation") and yq.get("sector_allocation"):
						instrument_data["sector_allocation"] = yq["sector_allocation"]
					if not instrument_data.get("geo_allocation") and yq.get("geo_allocation"):
						instrument_data["geo_allocation"] = yq["geo_allocation"]
					if not instrument_data.get("type") and yq.get("asset_type"):
						instrument_data["type"] = yq["asset_type"]
			storage.upsert_instrument(isin, instrument_data)
			return data
		# Delay between attempts
		if idx < len(suffixes) - 1:
			await asyncio.sleep(0.3)
	return None


async def fetch_and_update_prices(username: str, isins: list[str]):
	"""Background task to fetch prices for given ISINs/crypto symbols."""
	yahoo = YahooFinanceService()
	yahooquery = YahooQueryService()
	morningstar = MorningstarService()
	storage = StorageService()
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	if username not in users:
		logger.error(f"User not found for price update: {username}")
		return
	user_data = users[username]
	prices: dict[str, Any] = user_data.get("prices", {})
	updated = 0
	for isin in isins:
		if _is_fresh(prices, isin, yahoo):
			logger.info(f"Using cached price for {isin}")
			updated += 1
			continue
		quote = await (
			_fetch_crypto(isin, yahoo)
			if is_crypto_symbol(isin)
			else _fetch_traditional(
				isin,
				yahoo,
				yahooquery,
				morningstar,
				storage,
			)
		)
		if quote:
			prices[isin] = quote
			updated += 1
		else:
			logger.warning(f"Price fetch failed for {isin}")
	users[username]["prices"] = prices
	StorageService.save_json(users_file, users)
	logger.info(f"Price update complete: {updated}/{len(isins)} instruments updated")
	await websocket_manager.broadcast_to_user(
		username,
		{"type": "prices_updated", "count": updated, "timestamp": datetime.now(UTC).isoformat()},
	)


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
	background_tasks.add_task(fetch_and_update_prices, current_user.username, unique_isins)

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
		"cache_hours": 24,
	}
