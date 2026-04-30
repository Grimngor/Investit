"""Portfolio read service computed from order history."""

from typing import Any

from app.config import settings
from app.models.portfolio import Investment, Portfolio, PortfolioSummary
from app.services.compute_service import ComputeService
from app.services.storage_service import StorageService


class PortfolioService:
	"""Build portfolio views from finalized orders."""

	@staticmethod
	def get_portfolio(username: str) -> Portfolio:
		"""Get a user's portfolio computed from finalized orders."""
		users = StorageService.load_json(settings.DATA_DIR / "users.json", default={})
		user_data = users.get(username)
		if not user_data:
			return Portfolio(username=username, holdings=[])

		orders = user_data.get("orders", [])
		prices = user_data.get("prices", {})
		finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]
		if not finalized_orders:
			return Portfolio(username=username, holdings=[])

		investments = PortfolioService._build_investments(finalized_orders, prices)
		return Portfolio(username=username, holdings=investments)

	@staticmethod
	def get_summary(username: str) -> PortfolioSummary:
		"""Get a summary for a user's computed portfolio."""
		portfolio = PortfolioService.get_portfolio(username)
		total_cost = sum(h.quantity * h.purchase_price for h in portfolio.holdings)
		total_value = sum(h.quantity * (h.current_price or h.purchase_price) for h in portfolio.holdings)

		return PortfolioSummary(
			total_investments=len(portfolio.holdings),
			total_cost=total_cost,
			total_value=total_value,
			total_gain_loss=total_value - total_cost,
		)

	@staticmethod
	def _build_investments(finalized_orders: list[dict[str, Any]], prices: dict[str, dict[str, Any]]) -> list[Investment]:
		"""Build visible investments from finalized orders and cached prices."""
		investments = []
		unique_isins = sorted({o.get("isin") for o in finalized_orders if o.get("isin")})

		for isin in unique_isins:
			position = ComputeService.calculate_position(finalized_orders, isin)
			if position["total_shares"] <= 0:
				continue

			price_data = prices.get(isin, {})
			isin_orders = [o for o in finalized_orders if o.get("isin") == isin]
			latest_order = max(isin_orders, key=lambda x: x.get("date", ""))

			investments.append(
				Investment(
					id=len(investments) + 1,
					symbol=isin,
					name=price_data.get("name", isin),
					quantity=position["total_shares"],
					purchase_price=position["average_cost"],
					purchase_date=latest_order.get("date", ""),
					current_price=price_data.get("price"),
					asset_type="stock",
					currency="EUR",
					resolved_symbol=None,
					last_price_timestamp=price_data.get("timestamp"),
				)
			)

		return investments
