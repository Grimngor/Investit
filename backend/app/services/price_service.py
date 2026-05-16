"""Price service for fetching and updating prices and instrument metadata."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.services.isin_mapper import get_isin_mapper
from app.services.metrics_service import metrics
from app.services.morningstar_service import MorningstarService
from app.services.provider_reliability import ProviderReliabilityService
from app.services.storage_service import StorageService
from app.services.yahoo_finance import YahooFinanceService
from app.utils.validators import is_crypto_symbol, validate_price

logger = logging.getLogger(__name__)

# Suffixes to try when resolving an ISIN to a Yahoo Finance ticker.
_YAHOO_SUFFIXES = ["", ".F", ".SG", ".PA", ".AS", ".DE", ".MI"]


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
			ProviderReliabilityService.record_attempt("yahoo_finance.quote", "price", False, f"{isin}: no crypto quote")
			return None
		ProviderReliabilityService.record_attempt("yahoo_finance.quote", "price", True, f"{isin}: crypto quote")
		return ProviderReliabilityService.annotate(
			{
				"price": quote["price"],
				"currency": quote["currency"],
				"timestamp": quote["timestamp"],
				"name": quote.get("name", f"{isin} Cryptocurrency"),
				"symbol": quote.get("symbol", isin),
				"asset_type": "Crypto",
			},
			"yahoo_finance",
			"price",
			[ProviderReliabilityService.attempt("yahoo_finance.quote", True, "crypto quote")],
			"Yahoo Finance crypto quote",
		)

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
			("country_allocation", [mstar.get("country_allocation"), yq.get("country_allocation")]),
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
	async def get_candidate_symbols(isin: str) -> list[str]:
		"""Return ordered provider symbols for an ISIN."""
		storage = StorageService()
		instruments = storage.load_instruments()
		existing = next((inst for inst in instruments if inst.get("isin") == isin), {})
		resolved = await get_isin_mapper().resolve_isin_info(isin)
		resolved_symbol = resolved.get("ticker") if resolved else None
		symbols = [existing.get("symbol"), resolved_symbol, *[f"{isin}{suffix}" for suffix in _YAHOO_SUFFIXES]]
		return [symbol for index, symbol in enumerate(symbols) if symbol and symbol not in symbols[:index]]

	@staticmethod
	async def fetch_traditional_quote(isin: str) -> dict[str, Any] | None:
		"""Fetch price and metadata for a traditional instrument (fund/ETF/stock).

		Tries Yahoo Finance with multiple exchange suffixes, then enriches with
		Morningstar and Yahoo Fund metadata.
		"""
		yahoo = YahooFinanceService()
		morningstar = MorningstarService()
		storage = StorageService()
		symbols = await PriceService.get_candidate_symbols(isin)
		attempts: list[dict[str, Any]] = []

		for idx, symbol in enumerate(symbols):
			quote = await yahoo.get_quote(symbol)
			if not quote:
				attempts.append(ProviderReliabilityService.attempt("yahoo_finance.quote", False, symbol))
				ProviderReliabilityService.record_attempt("yahoo_finance.quote", "price", False, f"{isin}: {symbol}")
				if idx < len(symbols) - 1:
					await asyncio.sleep(0.3)
				continue
			attempts.append(ProviderReliabilityService.attempt("yahoo_finance.quote", True, symbol))
			ProviderReliabilityService.record_attempt("yahoo_finance.quote", "price", True, f"{isin}: {symbol}")

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
			metadata_attempts: list[dict[str, Any]] = []
			mstar = await morningstar.get_fund_metadata(isin)
			metadata_attempts.append(ProviderReliabilityService.attempt("morningstar", bool(mstar), "price refresh metadata"))
			ProviderReliabilityService.record_attempt("morningstar", "metadata", bool(mstar), isin)

			# Fetch Yahoo data if mstar is missing core info (sector OR geo)
			needs_yahoo = not mstar or not mstar.get("sector_allocation") or not mstar.get("regional_allocation")
			yq = None
			if needs_yahoo:
				yq = await yahoo.get_fund_metadata(resolved)
				metadata_attempts.append(ProviderReliabilityService.attempt("yahooquery", bool(yq), resolved))
				ProviderReliabilityService.record_attempt("yahooquery", "metadata", bool(yq), f"{isin}: {resolved}")

			PriceService._merge_metadata(instrument_data, mstar, yq)
			metadata_sources = [attempt["provider"] for attempt in metadata_attempts if attempt.get("success")]
			metadata_source = "+".join(metadata_sources) if metadata_sources else "yahoo_finance.quote"
			storage.upsert_instrument(
				isin,
				ProviderReliabilityService.annotate(
					instrument_data,
					metadata_source,
					"metadata",
					metadata_attempts,
					f"Metadata resolved during price refresh through {metadata_source}",
				),
			)

			return ProviderReliabilityService.annotate(data, "yahoo_finance", "price", attempts, f"Yahoo Finance quote via {symbol}")

		return None

	@staticmethod
	def _stale_cache_fallback(isin: str, cached: dict[str, Any] | None) -> dict[str, Any] | None:
		"""Return stale cached price data when providers fail but cached price is usable."""
		if not cached or not validate_price(cached.get("price")):
			return None
		fallback = ProviderReliabilityService.annotate(
			cached,
			"stale_cache",
			"price",
			[ProviderReliabilityService.attempt("stale_cache", True, "provider refresh failed")],
			"Stale cached price used after provider refresh failed",
		)
		fallback["stale_cache_fallback"] = True
		fallback["fallback_timestamp"] = datetime.now(UTC).isoformat()
		logger.warning(f"Using stale cached price for {isin} after provider refresh failure")
		ProviderReliabilityService.record_attempt("stale_cache", "price", True, isin)
		return fallback

	@staticmethod
	async def fetch_and_update_prices(username: str, isins: list[str], force: bool = False) -> None:
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
			if not force and PriceService.is_fresh(prices, isin):
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
				fallback = PriceService._stale_cache_fallback(isin, prices.get(isin))
				if fallback:
					prices[isin] = fallback
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
