"""Dashboard router for KPIs and portfolio metrics."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.compute_service import ComputeService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


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
