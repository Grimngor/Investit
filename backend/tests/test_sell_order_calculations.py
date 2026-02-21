"""Test sell order calculations to verify cost basis is handled correctly."""

import pytest

from app.services.compute_service import ComputeService


def test_sell_order_maintains_cost_basis():
	"""
	Test that selling shares maintains the correct cost basis and average cost.

	Example scenario:
	1. Buy 100 shares at €50 each = €5,000 total
	2. Sell 20 shares at €60 each = €1,200 proceeds

	Expected after sell:
	- Remaining shares: 80
	- Total cost basis: €4,000 (not €3,800!)
	- Average cost: €50/share (unchanged)
	"""
	orders = [
		{
			"isin": "IE0032126645",
			"date": "2024-01-01",
			"shares": 100,
			"amount_eur": 5000,
			"price_per_share": 50.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"isin": "IE0032126645",
			"date": "2024-02-01",
			"shares": 20,
			"amount_eur": 1200,  # Sell proceeds (not cost basis)
			"price_per_share": 60.0,  # Sell price (higher than buy)
			"order_type": "sell",
			"status": "Finalizada",
		},
	]

	position = ComputeService.calculate_position(orders, "IE0032126645")

	# Verify shares are correct
	assert position["total_shares"] == 80.0, f"Expected 80 shares, got {position['total_shares']}"

	# Verify cost basis is correct (should be 4000, not 3800)
	assert position["total_invested"] == pytest.approx(4000.0), f"Expected €4,000 cost basis, got €{position['total_invested']}"

	# Verify average cost remains €50/share
	assert position["average_cost"] == pytest.approx(50.0), f"Expected €50/share average cost, got €{position['average_cost']}"


def test_multiple_buys_then_sell():
	"""Test selling after multiple buys at different prices."""
	orders = [
		{
			"isin": "IE0032126645",
			"date": "2024-01-01",
			"shares": 50,
			"amount_eur": 2500,
			"price_per_share": 50.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"isin": "IE0032126645",
			"date": "2024-02-01",
			"shares": 50,
			"amount_eur": 3000,
			"price_per_share": 60.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"isin": "IE0032126645",
			"date": "2024-03-01",
			"shares": 30,
			"amount_eur": 2100,  # Sell proceeds at €70/share
			"price_per_share": 70.0,
			"order_type": "sell",
			"status": "Finalizada",
		},
	]

	position = ComputeService.calculate_position(orders, "IE0032126645")

	# After buys: 100 shares at average cost of €55 = €5,500 total
	# After sell: 70 shares, cost reduced by 30 * €55 = €1,650
	# Remaining cost: €5,500 - €1,650 = €3,850

	assert position["total_shares"] == 70.0
	assert position["total_invested"] == pytest.approx(3850.0)
	assert position["average_cost"] == pytest.approx(55.0)  # Average cost unchanged by sell


def test_sell_all_shares():
	"""Test selling all shares results in zero position."""
	orders = [
		{
			"isin": "IE0032126645",
			"date": "2024-01-01",
			"shares": 50,
			"amount_eur": 2500,
			"price_per_share": 50.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"isin": "IE0032126645",
			"date": "2024-02-01",
			"shares": 50,
			"amount_eur": 3000,  # Sell at different price
			"price_per_share": 60.0,
			"order_type": "sell",
			"status": "Finalizada",
		},
	]

	position = ComputeService.calculate_position(orders, "IE0032126645")

	assert position["total_shares"] == 0.0
	assert position["total_invested"] == 0.0
	assert position["average_cost"] == pytest.approx(50.0)  # Average cost preserved


def test_pnl_calculation_with_sells():
	"""Test that P&L is calculated correctly on remaining position after sells."""
	orders = [
		{
			"isin": "IE0032126645",
			"date": "2024-01-01",
			"shares": 100,
			"amount_eur": 5000,
			"price_per_share": 50.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"isin": "IE0032126645",
			"date": "2024-02-01",
			"shares": 20,
			"amount_eur": 1200,
			"price_per_share": 60.0,
			"order_type": "sell",
			"status": "Finalizada",
		},
	]

	position = ComputeService.calculate_position(orders, "IE0032126645")

	# Now calculate P&L with current price of €70
	current_price = 70.0
	pnl = ComputeService.calculate_pnl(position, current_price)

	# Current value: 80 shares * €70 = €5,600
	# Cost basis: €4,000
	# Unrealized P&L: €1,600
	# Unrealized P&L %: (1600/4000) * 100 = 40%

	assert pnl["current_value"] == pytest.approx(5600.0)
	assert pnl["unrealized_pnl"] == pytest.approx(1600.0)
	assert pnl["unrealized_pnl_pct"] == pytest.approx(40.0)
