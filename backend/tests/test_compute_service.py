"""Tests for compute service calculations."""

import pytest
from datetime import datetime, timedelta
from app.services.compute_service import ComputeService


def test_calculate_position_single_order():
    """Test position calculation with single order."""
    orders = [{"date": "2024-01-15", "isin": "IE00B4L5Y983", "shares": 10.0, "amount_eur": 1000.0, "status": "Finalizada"}]

    position = ComputeService.calculate_position(orders, "IE00B4L5Y983")

    assert position["total_shares"] == 10.0
    assert position["average_cost"] == 100.0
    assert position["total_invested"] == 1000.0


def test_calculate_position_multiple_orders():
    """Test position calculation with multiple orders at different prices."""
    orders = [
        {"date": "2024-01-15", "isin": "IE00B4L5Y983", "shares": 10.0, "amount_eur": 1000.0, "status": "Finalizada"},
        {"date": "2024-02-20", "isin": "IE00B4L5Y983", "shares": 5.0, "amount_eur": 600.0, "status": "Finalizada"},
    ]

    position = ComputeService.calculate_position(orders, "IE00B4L5Y983")

    assert position["total_shares"] == 15.0
    assert position["total_invested"] == 1600.0
    assert position["average_cost"] == pytest.approx(106.67, rel=0.01)


def test_calculate_position_ignores_rejected_orders():
    """Test that rejected orders are ignored."""
    orders = [
        {"date": "2024-01-15", "isin": "IE00B4L5Y983", "shares": 10.0, "amount_eur": 1000.0, "status": "Finalizada"},
        {"date": "2024-02-20", "isin": "IE00B4L5Y983", "shares": 5.0, "amount_eur": 600.0, "status": "Rechazada"},
    ]

    position = ComputeService.calculate_position(orders, "IE00B4L5Y983")

    assert position["total_shares"] == 10.0
    assert position["total_invested"] == 1000.0


def test_calculate_position_different_isin():
    """Test position for different ISIN returns empty."""
    orders = [{"date": "2024-01-15", "isin": "IE00B4L5Y983", "shares": 10.0, "amount_eur": 1000.0, "status": "Finalizada"}]

    position = ComputeService.calculate_position(orders, "US1234567890")

    assert position["total_shares"] == 0.0
    assert position["average_cost"] == 0.0
    assert position["total_invested"] == 0.0


def test_calculate_pnl_profit():
    """Test PnL calculation with profit."""
    position = {"total_shares": 10.0, "average_cost": 100.0, "total_invested": 1000.0}
    current_price = 120.0

    pnl = ComputeService.calculate_pnl(position, current_price)

    assert pnl["current_value"] == 1200.0
    assert pnl["unrealized_pnl"] == 200.0
    assert pnl["unrealized_pnl_pct"] == 20.0


def test_calculate_pnl_loss():
    """Test PnL calculation with loss."""
    position = {"total_shares": 10.0, "average_cost": 100.0, "total_invested": 1000.0}
    current_price = 80.0

    pnl = ComputeService.calculate_pnl(position, current_price)

    assert pnl["current_value"] == 800.0
    assert pnl["unrealized_pnl"] == -200.0
    assert pnl["unrealized_pnl_pct"] == -20.0


def test_calculate_portfolio_metrics():
    """Test overall portfolio metrics calculation."""
    holdings = [
        {"total_invested": 1000.0, "current_value": 1200.0, "unrealized_pnl": 200.0},
        {"total_invested": 500.0, "current_value": 450.0, "unrealized_pnl": -50.0},
    ]

    metrics = ComputeService.calculate_portfolio_metrics(holdings)

    assert metrics["total_invested"] == 1500.0
    assert metrics["total_value"] == 1650.0
    assert metrics["total_pnl"] == 150.0
    assert metrics["total_pnl_pct"] == 10.0


def test_calculate_portfolio_metrics_empty():
    """Test portfolio metrics with no holdings."""
    metrics = ComputeService.calculate_portfolio_metrics([])

    assert metrics["total_invested"] == 0.0
    assert metrics["total_value"] == 0.0
    assert metrics["total_pnl"] == 0.0
    assert metrics["total_pnl_pct"] == 0.0


def test_calculate_allocation_by_geography():
    """Test allocation calculation by geography."""
    holdings = [
        {"current_value": 1000.0, "geography": "North America"},
        {"current_value": 500.0, "geography": "Europe"},
        {"current_value": 300.0, "geography": "North America"},
    ]

    allocation = ComputeService.calculate_allocation_by_key(holdings, "geography")

    assert len(allocation) == 2
    assert allocation[0]["category"] == "North America"
    assert allocation[0]["value"] == 1300.0
    assert allocation[0]["percentage"] == pytest.approx(72.22, rel=0.01)
    assert allocation[1]["category"] == "Europe"
    assert allocation[1]["value"] == 500.0
    assert allocation[1]["percentage"] == pytest.approx(27.78, rel=0.01)


def test_calculate_allocation_empty():
    """Test allocation with empty holdings."""
    allocation = ComputeService.calculate_allocation_by_key([], "geography")
    assert allocation == []


def test_calculate_time_series():
    """Test time series calculation."""
    orders = [
        {"date": "2024-01-15", "isin": "ISIN1", "shares": 10.0, "amount_eur": 1000.0, "status": "Finalizada"},
        {"date": "2024-02-20", "isin": "ISIN2", "shares": 5.0, "amount_eur": 500.0, "status": "Finalizada"},
    ]
    prices = {"ISIN1": 110.0, "ISIN2": 120.0}

    time_series = ComputeService.calculate_time_series(orders, prices)

    assert len(time_series) == 2
    assert time_series[0]["date"] == "2024-01-15"
    assert time_series[0]["invested_value"] == 1000.0
    assert time_series[0]["current_value"] == 1100.0
    assert time_series[1]["date"] == "2024-02-20"
    assert time_series[1]["invested_value"] == 1500.0
    assert time_series[1]["current_value"] == 1700.0


def test_is_price_stale():
    """Test stale price detection."""
    # Fresh price (today)
    today = datetime.now().isoformat()
    assert ComputeService.is_price_stale(today, threshold_days=3) is False

    # Stale price (10 days ago)
    old_date = (datetime.now() - timedelta(days=10)).isoformat()
    assert ComputeService.is_price_stale(old_date, threshold_days=3) is True

    # Invalid date
    assert ComputeService.is_price_stale("invalid", threshold_days=3) is True

    # Empty string
    assert ComputeService.is_price_stale("", threshold_days=3) is True


def test_calculate_diversification_score_perfect():
    """Test diversification score with perfect diversification."""
    allocations = [
        {"percentage": 25.0},
        {"percentage": 25.0},
        {"percentage": 25.0},
        {"percentage": 25.0},
    ]

    score = ComputeService.calculate_diversification_score(allocations)
    assert score == pytest.approx(100.0, rel=0.01)


def test_calculate_diversification_score_concentrated():
    """Test diversification score with concentrated portfolio."""
    allocations = [
        {"percentage": 90.0},
        {"percentage": 10.0},
    ]

    score = ComputeService.calculate_diversification_score(allocations)
    # HHI = 0.9^2 + 0.1^2 = 0.82, should give low score
    assert score < 50.0


def test_calculate_diversification_score_empty():
    """Test diversification score with empty allocations."""
    score = ComputeService.calculate_diversification_score([])
    assert score == 0.0


def test_calculate_weighted_average():
    """Test weighted average calculation."""
    items = [
        {"return": 10.0, "value": 1000.0},
        {"return": 5.0, "value": 500.0},
        {"return": 15.0, "value": 1500.0},
    ]

    avg = ComputeService.calculate_weighted_average(items, "return", "value")
    # (10*1000 + 5*500 + 15*1500) / 3000 = 11.67
    assert avg == pytest.approx(11.67, rel=0.01)


def test_calculate_weighted_average_zero_weight():
    """Test weighted average with zero total weight."""
    items = [
        {"return": 10.0, "value": 0.0},
        {"return": 5.0, "value": 0.0},
    ]

    avg = ComputeService.calculate_weighted_average(items, "return", "value")
    assert avg == 0.0
