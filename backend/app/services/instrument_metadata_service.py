"""Service for refreshing persisted instrument metadata."""

import logging
from typing import Any

from app.services.morningstar_service import MorningstarService
from app.services.price_service import PriceService
from app.services.storage_service import StorageService, load_users
from app.services.yahoo_finance import YahooFinanceService
from app.utils.validators import is_crypto_symbol

logger = logging.getLogger(__name__)


class InstrumentMetadataService:
	"""Service for provider-backed instrument metadata refreshes."""

	@staticmethod
	def get_user_isins(username: str) -> list[str]:
		"""Return finalized order ISINs for a user."""
		users = load_users()
		user_data = users.get(username, {})
		orders = user_data.get("orders", [])
		finalized = [o for o in orders if o.get("status", "").lower() == "finalizada" and o.get("isin")]
		return sorted(set(o["isin"] for o in finalized))

	@staticmethod
	def requires_provider(isins: list[str]) -> bool:
		"""Return True when any ISIN requires an external metadata provider."""
		return any(not is_crypto_symbol(isin) for isin in isins)

	@staticmethod
	async def refresh_for_user(username: str, force: bool = False) -> dict[str, Any]:
		"""Fetch and persist missing or forced instrument metadata for a user."""
		users = load_users()
		if username not in users:
			return {"success": False, "message": "User not found", "updated": 0, "total": 0, "errors": ["User not found"]}

		unique_isins = InstrumentMetadataService.get_user_isins(username)
		if not unique_isins:
			return {"success": True, "message": "No ISINs to refresh", "updated": 0, "total": 0, "errors": []}

		storage = StorageService()
		morningstar = MorningstarService()
		yfinance = YahooFinanceService()
		instruments = storage.load_instruments()
		inst_map = {inst.get("isin"): inst for inst in instruments}

		updated_count = 0
		skipped = 0
		errors: list[str] = []

		for isin in unique_isins:
			try:
				meta = inst_map.get(isin, {})
				needs_metadata = not meta.get("sector_allocation") or not meta.get("geo_allocation") or not meta.get("type")
				if not force and not needs_metadata:
					skipped += 1
					continue

				success = await InstrumentMetadataService.refresh_single(isin, storage, morningstar, yfinance)
				if success:
					updated_count += 1
				else:
					errors.append(f"{isin}: Could not fetch complete metadata")
			except Exception as e:
				logger.error(f"Error refreshing {isin}: {e}")
				errors.append(f"{isin}: {e!s}")

		return {
			"success": True,
			"message": f"Refreshed metadata for {updated_count}/{len(unique_isins)} instruments",
			"updated": updated_count,
			"skipped": skipped,
			"total": len(unique_isins),
			"errors": errors,
		}

	@staticmethod
	async def refresh_single(
		isin: str,
		storage: StorageService,
		morningstar: MorningstarService,
		yfinance: YahooFinanceService,
	) -> bool:
		"""Fetch and persist metadata for a single ISIN."""
		logger.info(f"Refreshing metadata for {isin}")

		if is_crypto_symbol(isin):
			storage.upsert_instrument(isin, {"name": isin, "symbol": isin, "type": "Crypto"})
			return True

		instrument_data: dict[str, Any] = {"symbol": isin}
		symbols = await PriceService.get_candidate_symbols(isin)

		for symbol in symbols:
			quote = await yfinance.get_quote(symbol)
			if quote:
				instrument_data["symbol"] = quote.get("symbol", symbol)
				instrument_data["name"] = quote.get("name", isin)
				if quote.get("asset_type"):
					instrument_data["type"] = quote["asset_type"]
				if quote.get("sector_allocation"):
					instrument_data["sector_allocation"] = quote["sector_allocation"]
				if quote.get("geo_allocation"):
					instrument_data["geo_allocation"] = quote["geo_allocation"]
				if quote.get("country_allocation"):
					instrument_data["country_allocation"] = quote["country_allocation"]
				break

		mstar_metadata = await morningstar.get_fund_metadata(isin)

		if mstar_metadata:
			logger.info(f"Got Morningstar data for {isin}")
			PriceService._merge_metadata(instrument_data, mstar_metadata, None)

		if not instrument_data.get("sector_allocation") or not instrument_data.get("geo_allocation"):
			symbol = instrument_data.get("symbol", isin)
			logger.info(f"Fetching YahooQuery data for {symbol} ({isin})")
			yq_metadata = await yfinance.get_fund_metadata(symbol)
			PriceService._merge_metadata(instrument_data, None, yq_metadata)

		if len(instrument_data) <= 1:
			return False

		storage.upsert_instrument(isin, instrument_data)
		return True
