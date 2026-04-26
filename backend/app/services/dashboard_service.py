"""Dashboard service for orchestrating portfolio metrics and data aggregation."""

import logging
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.services.compute_service import ComputeService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class DashboardService:
	"""Service for gathering and orchestrating dashboard data."""

	@staticmethod
	def get_kpis(username: str) -> dict[str, Any]:
		"""Get dashboard KPIs for a user."""
		users_file = settings.DATA_DIR / "users.json"
		users = StorageService.load_json(users_file, default={})

		if username not in users:
			return {}

		user_data = users[username]
		orders = user_data.get("orders", [])
		prices = user_data.get("prices", {})

		# Filter only finalized orders
		finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]
		unique_isins = set(o.get("isin") for o in finalized_orders if o.get("isin"))

		holdings = []
		for isin in unique_isins:
			position = ComputeService.calculate_position(finalized_orders, isin)
			if position["total_shares"] > 0:
				latest_price = prices.get(isin, {}).get("price", 0.0)
				pnl_data = ComputeService.calculate_pnl(position, latest_price)
				holdings.append(
					{
						"isin": isin,
						"total_shares": position["total_shares"],
						"total_invested": position["total_invested"],
						"current_value": pnl_data["current_value"],
					}
				)

		metrics = ComputeService.calculate_portfolio_metrics(holdings)

		return {
			"total_invested": metrics["total_invested"],
			"current_value": metrics["total_value"],
			"total_pnl": metrics["total_pnl"],
			"total_pnl_pct": metrics["total_pnl_pct"],
			"positions_count": len(holdings),
			"orders_count": len(finalized_orders),
		}

	@staticmethod
	def get_time_series(username: str) -> dict[str, Any]:
		"""Get time series data for a user's portfolio."""
		users_file = settings.DATA_DIR / "users.json"
		users = StorageService.load_json(users_file, default={})

		if username not in users:
			return {"time_series": []}

		user_data = users[username]
		orders = user_data.get("orders", [])
		prices = user_data.get("prices", {})

		finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]

		price_map = {}
		for isin, data in prices.items():
			price_map[isin] = data.get("price", 0.0)

		# Fallback for missing prices
		for order in finalized_orders:
			isin = order.get("isin")
			if isin and isin not in price_map:
				isin_orders = [o for o in finalized_orders if o.get("isin") == isin]
				total_amount = sum(o.get("amount_eur", 0) for o in isin_orders)
				total_shares = sum(o.get("shares", 0) for o in isin_orders)
				if total_shares > 0:
					price_map[isin] = total_amount / total_shares

		time_series = ComputeService.calculate_time_series(finalized_orders, price_map)
		return {"time_series": time_series}

	@staticmethod
	def get_allocations(username: str) -> dict[str, Any]:
		"""Get allocation data for a user."""
		users_file = settings.DATA_DIR / "users.json"
		users = StorageService.load_json(users_file, default={})

		if username not in users:
			return {}

		user_data = users[username]
		orders = user_data.get("orders", [])
		prices = user_data.get("prices", {})

		finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]
		unique_isins = {o.get("isin") for o in finalized_orders if o.get("isin")}

		storage = StorageService()
		instrument_map = {inst.get("isin"): inst for inst in storage.load_instruments()}

		holdings = ComputeService.build_enriched_holdings(unique_isins, finalized_orders, prices, instrument_map)
		total_value = sum(h["current_value"] for h in holdings)
		allocs = ComputeService.calculate_allocations(holdings, total_value)

		return {
			**allocs,
			"crypto_pct": (allocs["crypto_value"] / total_value * 100.0) if total_value > 0 else 0.0,
		}

	@staticmethod
	def get_price_status(username: str) -> dict[str, Any]:
		"""Get stale price status for a user's portfolio."""
		users_file = settings.DATA_DIR / "users.json"
		users = StorageService.load_json(users_file, default={})

		if username not in users:
			return {}

		prices = users[username].get("prices", {})
		stale_instruments = []
		stale_count = 0

		for isin, price_data in prices.items():
			timestamp = price_data.get("timestamp")
			if timestamp and ComputeService.is_price_stale(timestamp, threshold_days=3):
				stale_count += 1
				try:
					last_update_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
					days_stale = (datetime.now(UTC) - last_update_dt).days
					last_price_date = last_update_dt.strftime("%Y-%m-%d")
				except (ValueError, AttributeError):
					days_stale = 999
					last_price_date = "Unknown"

				stale_instruments.append(
					{
						"isin": isin,
						"symbol": isin,
						"name": price_data.get("name", isin),
						"last_price_date": last_price_date,
						"days_stale": days_stale,
					}
				)

		return {
			"total_instruments": len(prices),
			"stale_count": stale_count,
			"stale_instruments": stale_instruments,
		}
