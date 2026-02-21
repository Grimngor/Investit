"""Compute service for portfolio calculations (PnL, positions, metrics)."""

from datetime import datetime
from decimal import Decimal
from typing import Any


class ComputeService:
	"""Service for portfolio computations and financial calculations."""

	@staticmethod
	def calculate_position(orders: list[dict[str, Any]], isin: str) -> dict[str, Any]:
		"""
		Calculate current position for a specific ISIN from order history.

		Args:
			orders: List of order dicts with date, isin, shares, amount_eur, status, price_per_share, order_type
			isin: ISIN code to calculate position for

		Returns:
			Dict with total_shares, average_cost, total_invested
		"""
		relevant_orders = [o for o in orders if o.get("isin") == isin and o.get("status", "").lower() == "finalizada"]

		if not relevant_orders:
			return {"total_shares": 0.0, "average_cost": 0.0, "total_invested": 0.0}

		total_shares = Decimal("0")
		total_cost = Decimal("0")  # Cumulative cost basis
		average_cost = Decimal("0")  # Running average cost per share

		for order in relevant_orders:
			shares = Decimal(str(order.get("shares", 0)))
			order_type = order.get("order_type", "buy").lower()

			if order_type == "sell":
				# For sells: reduce shares and reduce cost by (shares sold * current average cost)
				# This maintains the cost basis correctly
				if total_shares > 0 and average_cost > 0:
					cost_reduction = shares * average_cost
					total_shares -= shares
					total_cost -= cost_reduction
					# average_cost stays the same (cost basis per share doesn't change)
				else:
					# Edge case: selling without any prior buys (shouldn't happen, but handle gracefully)
					total_shares -= shares
					# Don't modify total_cost if we don't have a cost basis
			else:  # buy
				# Prioritize amount_eur as the actual cost basis if available
				amount_eur = order.get("amount_eur")
				if amount_eur is not None and amount_eur > 0:
					cost = Decimal(str(amount_eur))
				elif "price_per_share" in order and order["price_per_share"] is not None:
					price = Decimal(str(order["price_per_share"]))
					cost = shares * price
				else:
					cost = Decimal("0")

				total_shares += shares
				total_cost += cost
				# Recalculate average cost after each buy
				average_cost = total_cost / total_shares if total_shares > 0 else Decimal("0")

		return {
			"total_shares": float(total_shares),
			"average_cost": float(average_cost),
			"total_invested": float(total_cost),
		}

	@staticmethod
	def calculate_pnl(position: dict[str, Any], current_price: float) -> dict[str, Any]:
		"""
		Calculate profit/loss for a position.

		Args:
			position: Position dict with total_shares, average_cost, total_invested
			current_price: Current market price per share

		Returns:
			Dict with current_value, unrealized_pnl, unrealized_pnl_pct
		"""
		total_shares = position.get("total_shares", 0.0)
		total_invested = position.get("total_invested", 0.0)

		current_value = total_shares * current_price
		unrealized_pnl = current_value - total_invested
		unrealized_pnl_pct = (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0.0

		return {
			"current_value": current_value,
			"unrealized_pnl": unrealized_pnl,
			"unrealized_pnl_pct": unrealized_pnl_pct,
		}

	@staticmethod
	def calculate_portfolio_metrics(holdings: list[dict[str, Any]]) -> dict[str, Any]:
		"""
		Calculate overall portfolio metrics.

		Args:
			holdings: List of holdings with total_invested, current_value, unrealized_pnl

		Returns:
			Dict with total_invested, total_value, total_pnl, total_pnl_pct
		"""
		if not holdings:
			return {
				"total_invested": 0.0,
				"total_value": 0.0,
				"total_pnl": 0.0,
				"total_pnl_pct": 0.0,
			}

		total_invested = sum(h.get("total_invested", 0.0) for h in holdings)
		total_value = sum(h.get("current_value", 0.0) for h in holdings)
		total_pnl = total_value - total_invested
		total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

		return {
			"total_invested": total_invested,
			"total_value": total_value,
			"total_pnl": total_pnl,
			"total_pnl_pct": total_pnl_pct,
		}

	@staticmethod
	def calculate_allocation_by_key(holdings: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
		"""
		Calculate allocation breakdown by a specific key (e.g., geography, sector, asset_type).

		Args:
			holdings: List of holdings with current_value and the specified key
			key: Key to group by (e.g., 'geography', 'sector', 'asset_type')

		Returns:
			List of dicts with category, value, percentage
		"""
		if not holdings:
			return []

		total_value = sum(h.get("current_value", 0.0) for h in holdings)
		if total_value == 0:
			return []

		# Group by key
		groups: dict[str, float] = {}
		for h in holdings:
			category = h.get(key, "Unknown")
			value = h.get("current_value", 0.0)
			groups[category] = groups.get(category, 0.0) + value

		# Calculate percentages
		result = []
		for category, value in sorted(groups.items(), key=lambda x: x[1], reverse=True):
			result.append(
				{
					"category": category,
					"value": value,
					"percentage": (value / total_value * 100) if total_value > 0 else 0.0,
				}
			)

		return result

	@staticmethod
	def calculate_time_series(orders: list[dict[str, Any]], prices: dict[str, float]) -> list[dict[str, Any]]:
		"""
		Calculate invested vs current value over time.

		Args:
			orders: List of orders sorted by date
			prices: Dict mapping ISIN to current price

		Returns:
			List of dicts with date, invested_value, current_value
		"""
		if not orders:
			return []

		# Sort orders by date
		sorted_orders = sorted(orders, key=lambda x: x.get("date", ""))

		time_series = []
		cumulative_invested = Decimal("0")
		positions: dict[str, Decimal] = {}  # ISIN -> shares
		average_costs: dict[str, Decimal] = {}  # ISIN -> average cost per share

		for order in sorted_orders:
			if order.get("status", "").lower() != "finalizada":
				continue

			date = order.get("date")
			isin = order.get("isin")
			shares = Decimal(str(order.get("shares", 0)))
			order_type = order.get("order_type", "buy").lower()

			if order_type == "sell":
				# For sells: reduce shares and cost by (shares sold * average cost)
				if isin in positions and positions[isin] > 0 and isin in average_costs:
					cost_reduction = shares * average_costs[isin]
					cumulative_invested -= cost_reduction
					positions[isin] = positions.get(isin, Decimal("0")) - shares
				else:
					# Edge case: selling without prior buys
					positions[isin] = positions.get(isin, Decimal("0")) - shares
			else:  # buy
				# Calculate actual cost using price_per_share if available
				if "price_per_share" in order and order["price_per_share"] is not None:
					price_per_share = Decimal(str(order["price_per_share"]))
					cost = shares * price_per_share
				else:
					# Fallback to amount_eur
					cost = Decimal(str(order.get("amount_eur", 0)))

				cumulative_invested += cost
				old_shares = positions.get(isin, Decimal("0"))
				new_shares = old_shares + shares

				# Update average cost for this ISIN
				if isin in average_costs and old_shares > 0:
					old_cost = old_shares * average_costs[isin]
					new_cost = old_cost + cost
					average_costs[isin] = new_cost / new_shares
				else:
					average_costs[isin] = cost / shares if shares > 0 else Decimal("0")

				positions[isin] = new_shares

			# Calculate current value with current prices
			current_value = 0.0
			for pos_isin, pos_shares in positions.items():
				price = prices.get(pos_isin, 0.0)
				current_value += float(pos_shares) * price

			time_series.append(
				{
					"date": date,
					"invested_value": float(cumulative_invested),
					"current_value": current_value,
				}
			)

		return time_series

	@staticmethod
	def is_price_stale(last_update: str, threshold_days: int = 3) -> bool:
		"""
		Check if a price is stale (older than threshold).

		Args:
			last_update: ISO format datetime string
			threshold_days: Number of days to consider stale (default: 3)

		Returns:
			True if price is stale, False otherwise
		"""
		if not last_update:
			return True

		try:
			last_update_dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
			now = datetime.now(last_update_dt.tzinfo)
			age_days = (now - last_update_dt).days
			return age_days > threshold_days
		except (ValueError, AttributeError):
			return True

	@staticmethod
	def calculate_diversification_score(allocations: list[dict[str, Any]]) -> float:
		"""
		Calculate diversification score using Herfindahl-Hirschman Index (HHI).

		Args:
			allocations: List of dicts with 'percentage' key

		Returns:
			Score from 0-100, where 100 is perfectly diversified
		"""
		if not allocations:
			return 0.0

		# Calculate HHI (sum of squared percentages)
		hhi = sum((a.get("percentage", 0) / 100) ** 2 for a in allocations)

		# Normalize to 0-100 scale (lower HHI = better diversification)
		# HHI ranges from 1/n (perfect diversification) to 1 (concentrated)
		# Convert to score where 100 is best
		n = len(allocations)
		min_hhi = 1.0 / n if n > 0 else 1.0
		max_hhi = 1.0

		if max_hhi == min_hhi:
			return 100.0

		normalized = (max_hhi - hhi) / (max_hhi - min_hhi)
		return normalized * 100

	@staticmethod
	def calculate_weighted_average(items: list[dict[str, Any]], value_key: str, weight_key: str) -> float:
		"""
		Calculate weighted average.

		Args:
			items: List of items
			value_key: Key for the value to average
			weight_key: Key for the weight

		Returns:
			Weighted average
		"""
		total_weight = sum(item.get(weight_key, 0.0) for item in items)
		if total_weight == 0:
			return 0.0

		weighted_sum = sum(item.get(value_key, 0.0) * item.get(weight_key, 0.0) for item in items)
		return weighted_sum / total_weight
