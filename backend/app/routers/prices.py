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

router = APIRouter(prefix="/api/prices", tags=["prices"])
logger = logging.getLogger(__name__)


async def fetch_and_update_prices(username: str, isins: list[str]):
	"""
	Background task to fetch prices for ISINs and update user data.

	Args:
		username: Username to update prices for
		isins: List of ISINs to fetch prices for
	"""
	yahoo = YahooFinanceService()
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if username not in users:
		logger.error(f"User not found for price update: {username}")
		return

	user_data = users[username]
	prices = user_data.get("prices", {})

	# For each ISIN, try to find the Yahoo symbol
	# Try common European exchange suffixes, but stop after first success
	yahoo = YahooFinanceService()
	yahooquery = YahooQueryService()
	morningstar = MorningstarService()

	updated_count = 0
	storage = StorageService()
	for isin in isins:
		# Skip if we already have a recent price
		if isin in prices:
			existing_price = prices[isin]
			if not yahoo.is_price_stale(existing_price.get("timestamp", "")):
				logger.info(f"Using cached price for {isin}")
				updated_count += 1
				continue

		# Try common suffixes for European ETFs/funds (most common first)
		# Stop at first successful fetch to minimize requests
		suffixes = ["", ".PA", ".AS", ".DE", ".MI"]  # Reduced from 6 to 5, ordered by likelihood
		quote_data = None

		for suffix in suffixes:
			symbol = f"{isin}{suffix}"
			quote_data = await yahoo.get_quote(symbol)

			if quote_data:
				# Found a working symbol, save basic price data
				# Use the actual Yahoo ticker symbol (not ISIN) for metadata fetching
				resolved_symbol = quote_data.get("symbol", symbol)

				prices[isin] = {
					"price": quote_data["price"],
					"currency": quote_data["currency"],
					"timestamp": quote_data["timestamp"],
					"name": quote_data.get("name", isin),
					"symbol": resolved_symbol,  # Store the resolved Yahoo ticker
				}
				updated_count += 1
				logger.info(f"Updated price for {isin}: {quote_data['price']} {quote_data['currency']} (symbol: {resolved_symbol})")

				# Fetch comprehensive metadata - try Morningstar first (best regional data)
				mstar_metadata = await morningstar.get_fund_metadata(isin)

				instrument_data = {
					"name": quote_data.get("name", isin),
					"symbol": resolved_symbol,
				}

				# Use Morningstar data if available (preferred for geography + sectors)
				if mstar_metadata:
					instrument_data["name"] = mstar_metadata.get("name") or instrument_data["name"]

					if mstar_metadata.get("sector_allocation"):
						instrument_data["sector_allocation"] = mstar_metadata["sector_allocation"]

					if mstar_metadata.get("regional_allocation"):
						instrument_data["geo_allocation"] = mstar_metadata["regional_allocation"]

					if mstar_metadata.get("morningstar_code"):
						instrument_data["type"] = "Fund"

				# Fallback to yahooquery if Morningstar didn't provide data
				if not mstar_metadata or not instrument_data.get("sector_allocation"):
					yq_metadata = await yahooquery.get_fund_metadata(resolved_symbol)

					if yq_metadata:
						if not instrument_data.get("sector_allocation") and yq_metadata.get("sector_allocation"):
							instrument_data["sector_allocation"] = yq_metadata["sector_allocation"]

						if not instrument_data.get("geo_allocation") and yq_metadata.get("geo_allocation"):
							instrument_data["geo_allocation"] = yq_metadata["geo_allocation"]

						if not instrument_data.get("type") and yq_metadata.get("asset_type"):
							instrument_data["type"] = yq_metadata["asset_type"]

				# Persist to instruments.json
				storage.upsert_instrument(isin, instrument_data)
				sector_count = len(instrument_data.get("sector_allocation", {}))
				geo_count = len(instrument_data.get("geo_allocation", {}))
				source = "Morningstar" if mstar_metadata else "YahooQuery"
				logger.info(f"Stored metadata for {isin} ({source}): sectors={sector_count}, geo={geo_count}")

				break

			# Small delay between suffix attempts
			await asyncio.sleep(0.3)

		if not quote_data:
			logger.warning(f"Could not fetch price for {isin} after trying {len(suffixes)} symbols")

	users[username]["prices"] = prices
	StorageService.save_json(users_file, users)

	logger.info(f"Price update complete: {updated_count}/{len(isins)} ISINs updated")

	# Broadcast update via WebSocket
	await websocket_manager.broadcast_to_user(
		username,
		{
			"type": "prices_updated",
			"count": updated_count,
			"timestamp": datetime.now(UTC).isoformat(),
		},
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
