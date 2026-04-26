"""Tests for dashboard KPI endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.storage_service import StorageService
from tests.conftest import make_auth_headers

client = TestClient(app)


@pytest.fixture
def auth_headers():
	"""Get authentication headers for test user."""
	return make_auth_headers(client, username="test_dashboard_kpis", email="dashboard@example.com")


@pytest.fixture
def cleanup_user_data(auth_headers):
	"""Clean up test user data before and after tests."""
	# Get username from token
	username = "test_dashboard_kpis"

	# Clean up before test
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	if username in users:
		users[username]["orders"] = []
		users[username]["prices"] = {}
		StorageService.save_json(users_file, users)

	yield

	# Clean up after test
	users = StorageService.load_json(users_file, default={})
	if username in users:
		users[username]["orders"] = []
		users[username]["prices"] = {}
		StorageService.save_json(users_file, users)


def test_get_kpis_empty_portfolio(auth_headers, cleanup_user_data):
	"""Test KPIs with no orders."""
	response = client.get("/api/dashboard/kpis", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total_invested"] == 0.0
	assert data["current_value"] == 0.0
	assert data["total_pnl"] == 0.0
	assert data["total_pnl_pct"] == 0.0
	assert data["positions_count"] == 0
	assert data["orders_count"] == 0


def test_get_kpis_single_position_no_price(auth_headers, cleanup_user_data):
	"""Test KPIs with one order but no price data."""
	# Create an order
	client.post(
		"/api/orders/",
		json={
			"date": "2024-01-15",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 1000.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		headers=auth_headers,
	)

	response = client.get("/api/dashboard/kpis", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total_invested"] == 1000.0
	assert data["current_value"] == 0.0  # No price data
	assert data["total_pnl"] == -1000.0
	assert data["total_pnl_pct"] == -100.0
	assert data["positions_count"] == 1
	assert data["orders_count"] == 1


def test_get_kpis_single_position_with_profit(auth_headers, cleanup_user_data):
	"""Test KPIs with one position showing profit."""
	# Add price data first
	username = "test_dashboard_kpis"
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	users[username]["prices"] = {"IE00B4L5Y983": {"price": 110.0, "timestamp": "2024-01-20T10:00:00"}}
	StorageService.save_json(users_file, users)

	# Create an order (10 shares @ 100 EUR/share = 1000 EUR)
	client.post(
		"/api/orders/",
		json={
			"date": "2024-01-15",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 1000.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		headers=auth_headers,
	)

	response = client.get("/api/dashboard/kpis", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total_invested"] == 1000.0
	assert data["current_value"] == 1100.0  # 10 shares * 110 EUR
	assert data["total_pnl"] == 100.0
	assert data["total_pnl_pct"] == 10.0
	assert data["positions_count"] == 1
	assert data["orders_count"] == 1


def test_get_kpis_single_position_with_loss(auth_headers, cleanup_user_data):
	"""Test KPIs with one position showing loss."""
	# Add price data
	username = "test_dashboard_kpis"
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	users[username]["prices"] = {"IE00B4L5Y983": {"price": 90.0, "timestamp": "2024-01-20T10:00:00"}}
	StorageService.save_json(users_file, users)

	# Create an order (10 shares @ 100 EUR/share = 1000 EUR)
	client.post(
		"/api/orders/",
		json={
			"date": "2024-01-15",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 1000.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		headers=auth_headers,
	)

	response = client.get("/api/dashboard/kpis", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total_invested"] == 1000.0
	assert data["current_value"] == 900.0  # 10 shares * 90 EUR
	assert data["total_pnl"] == -100.0
	assert data["total_pnl_pct"] == -10.0
	assert data["positions_count"] == 1
	assert data["orders_count"] == 1


def test_get_kpis_multiple_positions(auth_headers, cleanup_user_data):
	"""Test KPIs with multiple positions."""
	# Add price data for multiple ISINs
	username = "test_dashboard_kpis"
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	users[username]["prices"] = {
		"IE00B4L5Y983": {"price": 110.0, "timestamp": "2024-01-20T10:00:00"},
		"IE00B3RBWM25": {"price": 55.0, "timestamp": "2024-01-20T10:00:00"},
		"US0378331005": {"price": 150.0, "timestamp": "2024-01-20T10:00:00"},
	}
	StorageService.save_json(users_file, users)

	# Create multiple orders
	orders = [
		{
			"date": "2024-01-15",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 1000.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"date": "2024-01-16",
			"isin": "IE00B3RBWM25",
			"ticker": "VWRL",
			"amount_eur": 500.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"date": "2024-01-17",
			"isin": "US0378331005",
			"ticker": "AAPL",
			"amount_eur": 1500.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
	]

	for order in orders:
		client.post("/api/orders/", json=order, headers=auth_headers)

	response = client.get("/api/dashboard/kpis", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	# Total invested: 1000 + 500 + 1500 = 3000
	assert data["total_invested"] == 3000.0

	# Current value: (10*110) + (10*55) + (10*150) = 1100 + 550 + 1500 = 3150
	assert data["current_value"] == 3150.0

	# PnL: 3150 - 3000 = 150
	assert data["total_pnl"] == 150.0

	# PnL%: 150 / 3000 * 100 = 5.0%
	assert data["total_pnl_pct"] == 5.0

	assert data["positions_count"] == 3
	assert data["orders_count"] == 3


def test_get_kpis_ignores_rejected_orders(auth_headers, cleanup_user_data):
	"""Test that KPIs ignore rejected orders."""
	# Add price data
	username = "test_dashboard_kpis"
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	users[username]["prices"] = {"IE00B4L5Y983": {"price": 110.0, "timestamp": "2024-01-20T10:00:00"}}
	StorageService.save_json(users_file, users)

	# Create finalized order
	client.post(
		"/api/orders/",
		json={
			"date": "2024-01-15",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 1000.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		headers=auth_headers,
	)

	# Create rejected order (should be ignored)
	client.post(
		"/api/orders/",
		json={
			"date": "2024-01-16",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 500.0,
			"shares": 5.0,
			"order_type": "buy",
			"status": "Rechazada",
		},
		headers=auth_headers,
	)

	response = client.get("/api/dashboard/kpis", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	# Should only count the finalized order
	assert data["total_invested"] == 1000.0
	assert data["current_value"] == 1100.0
	assert data["orders_count"] == 1  # Only finalized


def test_get_kpis_multiple_orders_same_isin(auth_headers, cleanup_user_data):
	"""Test KPIs with multiple orders for the same ISIN."""
	# Add price data
	username = "test_dashboard_kpis"
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	users[username]["prices"] = {"IE00B4L5Y983": {"price": 105.0, "timestamp": "2024-01-20T10:00:00"}}
	StorageService.save_json(users_file, users)

	# Create two orders for same ISIN
	orders = [
		{
			"date": "2024-01-15",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 1000.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"date": "2024-01-20",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 550.0,
			"shares": 5.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
	]

	for order in orders:
		client.post("/api/orders/", json=order, headers=auth_headers)

	response = client.get("/api/dashboard/kpis", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	# Total invested: 1000 + 550 = 1550
	assert data["total_invested"] == 1550.0

	# Total shares: 10 + 5 = 15
	# Current value: 15 * 105 = 1575
	assert data["current_value"] == 1575.0

	# PnL: 1575 - 1550 = 25
	assert data["total_pnl"] == 25.0

	# PnL%: 25 / 1550 * 100 ≈ 1.61%
	assert abs(data["total_pnl_pct"] - 1.6129032258064515) < 0.01

	assert data["positions_count"] == 1  # Same ISIN
	assert data["orders_count"] == 2


def test_get_kpis_unauthorized(cleanup_user_data):
	"""Test that KPIs endpoint requires authentication."""
	response = client.get("/api/dashboard/kpis")
	assert response.status_code == 401
