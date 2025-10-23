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
            orders: List of order dicts with date, isin, shares, amount_eur, status
            isin: ISIN code to calculate position for

        Returns:
            Dict with total_shares, average_cost, total_invested
        """
        relevant_orders = [o for o in orders if o.get("isin") == isin and o.get("status", "").lower() == "finalizada"]

        if not relevant_orders:
            return {"total_shares": 0.0, "average_cost": 0.0, "total_invested": 0.0}

        total_shares = Decimal("0")
        total_invested = Decimal("0")

        for order in relevant_orders:
            shares = Decimal(str(order.get("shares", 0)))
            amount = Decimal(str(order.get("amount_eur", 0)))

            total_shares += shares
            total_invested += amount

        # Calculate average cost per share
        avg_cost = float(total_invested / total_shares) if total_shares > 0 else 0.0

        return {
            "total_shares": float(total_shares),
            "average_cost": avg_cost,
            "total_invested": float(total_invested),
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
        cumulative_invested = 0.0
        positions: dict[str, Decimal] = {}  # ISIN -> shares

        for order in sorted_orders:
            if order.get("status", "").lower() != "finalizada":
                continue

            date = order.get("date")
            isin = order.get("isin")
            shares = Decimal(str(order.get("shares", 0)))
            amount = Decimal(str(order.get("amount_eur", 0)))

            # Update cumulative invested
            cumulative_invested += float(amount)

            # Update position
            positions[isin] = positions.get(isin, Decimal("0")) + shares

            # Calculate current value with current prices
            current_value = 0.0
            for pos_isin, pos_shares in positions.items():
                price = prices.get(pos_isin, 0.0)
                current_value += float(pos_shares) * price

            time_series.append(
                {
                    "date": date,
                    "invested_value": cumulative_invested,
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
