"""Price service for fetching and updating prices and instrument metadata."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.services.metrics_service import metrics
from app.services.morningstar_service import MorningstarService
from app.services.storage_service import StorageService
from app.services.yahoo_finance import YahooFinanceService
from app.utils.validators import is_crypto_symbol, validate_price

logger = logging.getLogger(__name__)

# Suffixes to try when resolving an ISIN to a Yahoo Finance ticker
_YAHOO_SUFFIXES = ["", ".PA", ".AS", ".DE", ".MI"]


class PriceService:
	"""Service for fetching and persisting market prices and instrument metadata."""

	@staticmethod
	def is_fresh(prices: dict[str, Any], isin: str) -> bool:
		"""Return True if a cached price for the given ISIN is still fresh."""
		existing = prices.get(isin)
		if not existing:
			return False
		yahoo = YahooFinanceService()
		return not yahoo.is_price_stale(existing.get("timestamp", ""))

	@staticmethod
	async def fetch_crypto_quote(isin: str) -> dict[str, Any] | None:
		"""Fetch current price for a crypto symbol. Returns a standardised quote dict."""
		yahoo = YahooFinanceService()
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

	@staticmethod
	def _merge_metadata(
		instrument_data: dict[str, Any],
		mstar: dict[str, Any] | None,
		yq: dict[str, Any] | None,
	) -> None:
		"""Merge Morningstar and Yahoo metadata into instrument_data in-place.

		Priority: Morningstar > Yahoo Finance > existing values.
		"""
		mstar = mstar or {}
		yq = yq or {}

		# Declarative field-by-field merging
		# For each field, we take the first available non-null value from priority sources
		metadata_fields = [
			("name", [mstar.get("name"), yq.get("name")]),
			("sector_allocation", [mstar.get("sector_allocation"), yq.get("sector_allocation")]),
			("geo_allocation", [mstar.get("regional_allocation"), yq.get("geo_allocation")]),
			("type", [mstar.get("morningstar_code") and "Fund", yq.get("asset_type")]),
		]

		for field, values in metadata_fields:
			# Use the first truthy value if available, otherwise keep existing
			for value in values:
				if value:
					instrument_data[field] = value
					break

	@staticmethod
	async def fetch_traditional_quote(isin: str) -> dict[str, Any] | None:
		"""Fetch price and metadata for a traditional instrument (fund/ETF/stock).

		Tries Yahoo Finance with multiple exchange suffixes, then enriches with
		Morningstar and Yahoo Fund metadata.
		"""
		yahoo = YahooFinanceService()
		morningstar = MorningstarService()
		storage = StorageService()

		for idx, suffix in enumerate(_YAHOO_SUFFIXES):
			symbol = f"{isin}{suffix}"
			quote = await yahoo.get_quote(symbol)
			if not quote:
				if idx < len(_YAHOO_SUFFIXES) - 1:
					await asyncio.sleep(0.3)
				continue

			resolved = quote.get("symbol", symbol)
			data: dict[str, Any] = {
				"price": quote["price"],
				"currency": quote["currency"],
				"timestamp": quote["timestamp"],
				"name": quote.get("name", isin),
				"symbol": resolved,
			}

			# Enrich with fund metadata
			instrument_data: dict[str, Any] = {"name": data["name"], "symbol": resolved}
			mstar = await morningstar.get_fund_metadata(isin)

			# Fetch Yahoo data if mstar is missing core info (sector OR geo)
			needs_yahoo = not mstar or not mstar.get("sector_allocation") or not mstar.get("regional_allocation")
			yq = await yahoo.get_fund_metadata(resolved) if needs_yahoo else None

			PriceService._merge_metadata(instrument_data, mstar, yq)
			storage.upsert_instrument(isin, instrument_data)

			return data

		return None

	@staticmethod
	async def fetch_and_update_prices(username: str, isins: list[str]) -> None:
		"""Background task to fetch and persist prices for the given ISINs."""
		from app.routers.websocket import manager as websocket_manager

		users_file = settings.DATA_DIR / "users.json"
		users = StorageService.load_json(users_file, default={})

		if username not in users:
			logger.error(f"User not found for price update: {username}")
			return

		user_data = users[username]
		prices: dict[str, Any] = user_data.get("prices", {})
		updated = 0

		for isin in isins:
			if PriceService.is_fresh(prices, isin):
				logger.info(f"Using cached price for {isin}")
				updated += 1
				continue

			if is_crypto_symbol(isin):
				quote = await PriceService.fetch_crypto_quote(isin)
			else:
				quote = await PriceService.fetch_traditional_quote(isin)

			if quote and validate_price(quote.get("price")):
				prices[isin] = quote
				updated += 1
			else:
				logger.warning(f"Price fetch or validation failed for {isin}. Result: {quote}")

		users[username]["prices"] = prices
		StorageService.save_json(users_file, users)
		logger.info(f"Price update complete: {updated}/{len(isins)} instruments updated")

		# Record metric
		metrics.record_price_fetch("success", updated)

		await websocket_manager.broadcast_to_user(
			username,
			{"type": "prices_updated", "count": updated, "timestamp": datetime.now(UTC).isoformat()},
		)
