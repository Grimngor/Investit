"""Router for instrument metadata management."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.routers.auth import get_current_user
from app.services.morningstar_service import MorningstarService
from app.services.storage_service import StorageService, load_users
from app.services.yahoo_finance import YahooFinanceService
from app.services.yahooquery_service import YahooQueryService

router = APIRouter(prefix="/api/instruments", tags=["instruments"])
logger = logging.getLogger(__name__)


@router.get("/{isin}")
async def get_instrument(isin: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""
	Get instrument metadata by ISIN.

	Returns instrument information including name, type, and allocations.
	"""
	storage = StorageService()
	instruments = storage.load_instruments()

	# Find instrument by ISIN
	instrument = next((inst for inst in instruments if inst.get("isin") == isin), None)

	if not instrument:
		raise HTTPException(status_code=404, detail=f"Instrument {isin} not found")

	return instrument


@router.post("/sync")
async def sync_instrument_metadata(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Fetch and persist missing instrument metadata (sector/geography/asset_type) via Yahoo Finance.

	Uses user's finalized orders to determine which ISINs to attempt.
	Only updates instruments lacking sector or geo allocations.
	"""
	users = load_users()
	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")
	user_data = users[current_user.username]
	orders = user_data.get("orders", [])
	finalized = [o for o in orders if o.get("status", "").lower() == "finalizada" and o.get("isin")]
	unique_isins = sorted(set(o["isin"] for o in finalized))

	storage = StorageService()
	instruments = storage.load_instruments()
	inst_map = {inst.get("isin"): inst for inst in instruments}

	yahoo = YahooFinanceService()
	updated = 0
	skipped = 0
	failures: list[str] = []

	for isin in unique_isins:
		meta = inst_map.get(isin, {})
		needs_sector = not meta.get("sector_allocation")
		needs_geo = not meta.get("geo_allocation")
		needs_type = not meta.get("type")
		if not (needs_sector or needs_geo or needs_type):
			skipped += 1
			continue

		# Try suffix variants similar to price fetching for better coverage
		suffixes = ["", ".PA", ".AS", ".DE", ".MI"]
		fetched = None
		for suffix in suffixes:
			symbol = f"{isin}{suffix}"
			quote = await yahoo.get_quote(symbol)
			if quote:
				fetched = quote
				break

		if not fetched:
			failures.append(isin)
			continue

		instrument_metadata: dict[str, Any] = {"name": fetched.get("name", isin)}
		if fetched.get("asset_type"):
			instrument_metadata["type"] = fetched.get("asset_type")
		if fetched.get("sector_allocation"):
			instrument_metadata["sector_allocation"] = fetched.get("sector_allocation")
		if fetched.get("geo_allocation"):
			instrument_metadata["geo_allocation"] = fetched.get("geo_allocation")

		storage.upsert_instrument(isin, instrument_metadata)
		updated += 1

	return {
		"attempted": len(unique_isins),
		"updated": updated,
		"skipped": skipped,
		"failures": failures,
	}


@router.put("/{isin}")
async def update_instrument_metadata(isin: str, metadata: dict[str, Any], current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""
	Update instrument metadata (manual override for geo/sector allocations).

	Allows users to manually set:
	- geo_allocation: dict of country codes to percentages
	- sector_allocation: dict of sector names to percentages
	- name: instrument name
	- type: instrument type (fund, etf, crypto, bond)
	"""
	storage = StorageService()
	instruments = storage.load_instruments()

	# Find existing instrument
	existing_idx = next((i for i, inst in enumerate(instruments) if inst.get("isin") == isin), None)

	if existing_idx is not None:
		# Update existing instrument
		instruments[existing_idx].update(metadata)
		updated = instruments[existing_idx]
	else:
		# Create new instrument entry
		new_instrument = {"isin": isin, **metadata}
		instruments.append(new_instrument)
		updated = new_instrument

	# Save updated instruments
	storage.save_instruments(instruments)

	return updated


@router.get("/")
async def list_instruments(current_user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
	"""
	List all instruments with metadata.
	"""
	storage = StorageService()
	instruments = storage.load_instruments()
	return instruments


@router.post("/refresh")
async def refresh_instrument_metadata(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""
	Force refresh of instrument metadata from Morningstar and YahooQuery.

	Fetches fresh data for all ISINs in user's portfolio.
	Useful when metadata seems incomplete or outdated.
	"""
	users = load_users()
	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	user_data = users[current_user.username]
	orders = user_data.get("orders", [])
	finalized = [o for o in orders if o.get("status", "").lower() == "finalizada" and o.get("isin")]
	unique_isins = sorted(set(o["isin"] for o in finalized))

	if not unique_isins:
		return {"success": True, "message": "No ISINs to refresh", "updated": 0}

	storage = StorageService()
	morningstar = MorningstarService()
	yahooquery = YahooQueryService()
	yfinance = YahooFinanceService()

	updated_count = 0
	errors = []

	for isin in unique_isins:
		try:
			success = await _refresh_single_instrument(isin, storage, morningstar, yahooquery, yfinance)
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
		"total": len(unique_isins),
		"errors": errors,
	}


async def _refresh_single_instrument(
	isin: str,
	storage: StorageService,
	morningstar: MorningstarService,
	yahooquery: YahooQueryService,
	yfinance: YahooFinanceService,
) -> bool:
	"""Fetch and persist metadata for a single ISIN."""
	logger.info(f"Refreshing metadata for {isin}")

	# Get Yahoo ticker first
	ticker_result = await yfinance.get_ticker_from_isin(isin)
	if not ticker_result:
		return False

	symbol = ticker_result.get("symbol", isin)

	# Try Morningstar first (best regional data)
	instrument_data = {"isin": isin, "symbol": symbol}
	mstar_metadata = await morningstar.get_fund_metadata(isin)

	if mstar_metadata:
		logger.info(f"Got Morningstar data for {isin}")
		if mstar_metadata.get("name"):
			instrument_data["name"] = mstar_metadata["name"]
		if mstar_metadata.get("sector_allocation"):
			instrument_data["sector_allocation"] = mstar_metadata["sector_allocation"]
		if mstar_metadata.get("regional_allocation"):
			instrument_data["geo_allocation"] = mstar_metadata["regional_allocation"]
		instrument_data["type"] = "Fund"

	# Fallback to yahooquery for missing data
	if not instrument_data.get("sector_allocation") or not instrument_data.get("geo_allocation"):
		logger.info(f"Fetching YahooQuery data for {symbol} ({isin})")
		yq_metadata = await yahooquery.get_fund_metadata(symbol)

		if yq_metadata:
			if not instrument_data.get("sector_allocation") and yq_metadata.get("sector_allocation"):
				instrument_data["sector_allocation"] = yq_metadata["sector_allocation"]
			if not instrument_data.get("geo_allocation") and yq_metadata.get("geo_allocation"):
				instrument_data["geo_allocation"] = yq_metadata["geo_allocation"]

	# Save to instruments.json
	storage.upsert_instrument(instrument_data)
	return True
