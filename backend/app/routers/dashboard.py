"""Dashboard router for KPIs and portfolio metrics."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.compute_service import ComputeService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
ISIN_PREFIX_LENGTH = 2

COUNTRY_NAMES = {
	"US": "United States",
	"CA": "Canada",
	"GB": "United Kingdom",
	"DE": "Germany",
	"FR": "France",
	"ES": "Spain",
	"IT": "Italy",
	"IE": "Ireland",
	"NL": "Netherlands",
	"JP": "Japan",
	"CN": "China",
	"HK": "Hong Kong",
	"SG": "Singapore",
	"AU": "Australia",
	"CH": "Switzerland",
	"SE": "Sweden",
	"DK": "Denmark",
	"NO": "Norway",
	"FI": "Finland",
	"BE": "Belgium",
	"AT": "Austria",
	"KR": "South Korea",
	"TW": "Taiwan",
	"IN": "India",
	"BR": "Brazil",
	"MX": "Mexico",
	"ZA": "South Africa",
	"North America": "North America",
	"Europe Developed": "Europe (Developed)",
	"Europe Emerging": "Europe (Emerging)",
	"Asia Developed": "Asia (Developed)",
	"Asia Emerging": "Asia (Emerging)",
	"Latin America": "Latin America",
	"Middle East": "Middle East",
	"Africa": "Africa",
	"Oceania": "Oceania",
}


@router.get("/kpis")
async def get_kpis(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""
	Get dashboard KPIs for current user.

	Returns:
		- total_invested: Sum of all order amounts (EUR)
		- current_value: Sum of (shares x latest_price) for all positions
		- total_pnl: Absolute profit/loss (EUR)
		- total_pnl_pct: Percentage profit/loss (%)
		- positions_count: Number of active positions (ISIN with shares > 0)
		- orders_count: Total number of finalized orders
	"""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	user_data = users[current_user.username]
	orders = user_data.get("orders", [])
	prices = user_data.get("prices", {})

	# Filter only finalized orders (status: "Finalizada")
	finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]

	# Get unique ISINs from finalized orders
	unique_isins = set(o.get("isin") for o in finalized_orders if o.get("isin"))

	# Calculate positions and current values
	holdings = []
	for isin in unique_isins:
		position = ComputeService.calculate_position(finalized_orders, isin)

		if position["total_shares"] > 0:
			# Get latest price for this ISIN
			latest_price = prices.get(isin, {}).get("price", 0.0)

			# Calculate PnL
			pnl_data = ComputeService.calculate_pnl(position, latest_price)

			holdings.append(
				{
					"isin": isin,
					"total_shares": position["total_shares"],
					"total_invested": position["total_invested"],
					"current_value": pnl_data["current_value"],
					"unrealized_pnl": pnl_data["unrealized_pnl"],
				}
			)

	# Calculate portfolio-level metrics
	metrics = ComputeService.calculate_portfolio_metrics(holdings)

	return {
		"total_invested": metrics["total_invested"],
		"current_value": metrics["total_value"],
		"total_pnl": metrics["total_pnl"],
		"total_pnl_pct": metrics["total_pnl_pct"],
		"positions_count": len(holdings),
		"orders_count": len(finalized_orders),
	}


@router.get("/time-series")
async def get_time_series(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get time series data for portfolio value over time."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	user_data = users[current_user.username]
	orders = user_data.get("orders", [])
	prices = user_data.get("prices", {})

	# Filter finalized orders
	finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]

	# Extract prices as a simple dict (ISIN -> price)
	# If no current price available, use average purchase price from orders as fallback
	price_map = {}
	for isin, data in prices.items():
		price_map[isin] = data.get("price", 0.0)

	# For ISINs without current prices, calculate average purchase price as fallback
	for order in finalized_orders:
		isin = order.get("isin")
		if isin and isin not in price_map:
			# Calculate average price from all orders for this ISIN
			isin_orders = [o for o in finalized_orders if o.get("isin") == isin]
			total_amount = sum(o.get("amount_eur", 0) for o in isin_orders)
			total_shares = sum(o.get("shares", 0) for o in isin_orders)
			if total_shares > 0:
				price_map[isin] = total_amount / total_shares

	# Calculate time series
	time_series = ComputeService.calculate_time_series(finalized_orders, price_map)

	return {"time_series": time_series}


def _normalize_geo_keys(geo: dict[str, float]) -> dict[str, float]:
	"""Normalize geography keys to ISO country codes where possible."""
	if not geo:
		return {}

	# mapping of common full names to codes
	name_to_iso = {
		"United States": "US",
		"USA": "US",
		"Canada": "CA",
		"Germany": "DE",
		"France": "FR",
		"Spain": "ES",
		"Italy": "IT",
		"Ireland": "IE",
		"Netherlands": "NL",
		"United Kingdom": "GB",
		"UK": "GB",
		"Japan": "JP",
		"China": "CN",
		"Hong Kong": "HK",
		"Singapore": "SG",
		"Australia": "AU",
	}
	normalized: dict[str, float] = {}
	for k, v in geo.items():
		code = name_to_iso.get(k, k)
		# Only keep simple tokens (avoid long region descriptions)
		normalized[code] = normalized.get(code, 0.0) + float(v)
	return normalized


def _get_fallback_geo_alloc(isin: str) -> dict[str, float]:
	"""Infer country from ISIN prefix if no metadata available."""
	# fallback country inference from ISIN prefix
	country_code = isin[:ISIN_PREFIX_LENGTH] if len(isin) >= ISIN_PREFIX_LENGTH else "XX"
	fallback_geo_map = {
		"IE": "IE",
		"DE": "DE",
		"FR": "FR",
		"NL": "NL",
		"ES": "ES",
		"IT": "IT",
		"GB": "GB",
		"US": "US",
		"CA": "CA",
		"JP": "JP",
		"CN": "CN",
		"HK": "HK",
		"SG": "SG",
		"AU": "AU",
	}
	return {fallback_geo_map.get(country_code, "Other"): 1.0}


def _build_enriched_holdings(
	unique_isins: set[str], finalized_orders: list[dict[str, Any]], prices: dict[str, Any], instrument_map: dict[str, Any]
) -> list[dict[str, Any]]:
	"""Build positions with enriched metadata (asset type, sector, geography)."""
	holdings: list[dict[str, Any]] = []
	for isin in unique_isins:
		position = ComputeService.calculate_position(finalized_orders, isin)
		if position["total_shares"] <= 0:
			continue

		price_data = prices.get(isin, {})
		latest_price = price_data.get("price") or position["average_cost"]
		name = price_data.get("name") or isin
		pnl_data = ComputeService.calculate_pnl(position, latest_price)

		meta = instrument_map.get(isin, {})
		asset_type = meta.get("type") or price_data.get("asset_type") or "Fund"
		sector_alloc = meta.get("sector_allocation") or price_data.get("sector_allocation") or {"Diversified": 1.0}
		geo_alloc_raw = meta.get("geo_allocation") or price_data.get("geo_allocation") or {}
		geo_alloc = _normalize_geo_keys(geo_alloc_raw)

		if not geo_alloc:
			geo_alloc = _get_fallback_geo_alloc(isin)

		holdings.append(
			{
				"isin": isin,
				"name": name,
				"current_value": pnl_data["current_value"],
				"asset_type": asset_type,
				"sector_allocation": sector_alloc,
				"geo_allocation": geo_alloc,
			}
		)
	return holdings


def _calculate_allocations(holdings: list[dict[str, Any]], total_value: float) -> dict[str, Any]:
	"""Helper to calculate allocations by instrument, geography, sector, and asset type."""
	by_instrument = {}
	by_geography = {}
	by_sector = {}
	by_asset_type = {}
	crypto_value = 0.0

	if total_value <= 0:
		return {
			"by_instrument": {},
			"by_geography": {},
			"by_sector": {},
			"by_asset_type": {},
			"crypto_value": 0.0,
		}

	crypto_total = 0.0
	for h in holdings:
		name = h["name"]
		value = h["current_value"]
		asset_type = h.get("asset_type", "Unknown")

		# By instrument (collapse crypto into "Crypto")
		if asset_type == "Crypto":
			crypto_total += value
		else:
			by_instrument[name] = value

		# By asset type
		by_asset_type[asset_type] = by_asset_type.get(asset_type, 0.0) + value
		if asset_type == "Crypto":
			crypto_value += value

		# Weighted geography/sector (exclude crypto)
		if asset_type != "Crypto":
			geo_alloc = h.get("geo_allocation", {})
			for geo, weight in geo_alloc.items():
				by_geography[geo] = by_geography.get(geo, 0.0) + (value * weight)

			sector_alloc = h.get("sector_allocation", {})
			for sector, weight in sector_alloc.items():
				by_sector[sector] = by_sector.get(sector, 0.0) + (value * weight)

	# Transform and sort
	by_instrument = dict(sorted(by_instrument.items(), key=lambda x: x[1], reverse=True))
	if crypto_total > 0:
		by_instrument["Crypto"] = crypto_total

	by_geography_named = {COUNTRY_NAMES.get(code, code): value for code, value in by_geography.items()}
	by_geography_named = dict(sorted(by_geography_named.items(), key=lambda x: x[1], reverse=True))
	by_sector = dict(sorted(by_sector.items(), key=lambda x: x[1], reverse=True))
	by_asset_type = dict(sorted(by_asset_type.items(), key=lambda x: x[1], reverse=True))

	return {
		"by_instrument": by_instrument,
		"by_geography": by_geography_named,
		"by_sector": by_sector,
		"by_asset_type": by_asset_type,
		"crypto_value": crypto_value,
	}


@router.get("/allocations")
async def get_allocations(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get allocation data for pie charts."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail=f"User {current_user.username} not found")

	user_data = users[current_user.username]
	orders = user_data.get("orders", [])
	prices = user_data.get("prices", {})

	# Filter finalized orders and get unique ISINs
	finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]
	unique_isins = {o.get("isin") for o in finalized_orders if o.get("isin")}

	# Load global instrument metadata
	storage = StorageService()
	instrument_map = {inst.get("isin"): inst for inst in storage.load_instruments()}

	# Build holdings enriched with instrument metadata
	holdings = _build_enriched_holdings(unique_isins, finalized_orders, prices, instrument_map)

	total_value = sum(h["current_value"] for h in holdings)
	allocs = _calculate_allocations(holdings, total_value)

	return {
		**allocs,
		"crypto_pct": (allocs["crypto_value"] / total_value * 100.0) if total_value > 0 else 0.0,
	}


@router.get("/price-status")
async def get_price_status(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get price status to check for stale prices."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	user_data = users[current_user.username]
	prices = user_data.get("prices", {})

	stale_instruments = []
	total_instruments = len(prices)
	stale_count = 0

	for isin, price_data in prices.items():
		timestamp = price_data.get("timestamp")
		name = price_data.get("name", isin)

		if timestamp and ComputeService.is_price_stale(timestamp, threshold_days=3):
			stale_count += 1
			# Calculate days stale
			try:
				last_update_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
				now = datetime.now(UTC)
				days_stale = (now - last_update_dt).days
				last_price_date = last_update_dt.strftime("%Y-%m-%d")
			except (ValueError, AttributeError):
				days_stale = 999
				last_price_date = "Unknown"

			stale_instruments.append(
				{
					"isin": isin,
					"symbol": isin,  # Use ISIN as symbol for now
					"name": name,
					"last_price_date": last_price_date,
					"days_stale": days_stale,
				}
			)

	return {
		"total_instruments": total_instruments,
		"stale_count": stale_count,
		"stale_instruments": stale_instruments,
	}
