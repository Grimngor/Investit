"""Tests for order history filtering and sorting."""

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
	return make_auth_headers(client, username="test_order_history", email="test_order_history@example.com")


@pytest.fixture(autouse=True)
def cleanup_and_seed_orders(auth_headers):
	"""Clean up and seed test orders before each test."""
	# Create multiple test orders
	test_orders = [
		{
			"date": "2024-01-15",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 1000.0,
			"shares": 5.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"date": "2024-02-20",
			"isin": "IE00B3RBWM25",
			"ticker": "VWRL",
			"amount_eur": 500.0,
			"shares": 10.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"date": "2024-03-10",
			"isin": "IE00B4L5Y983",
			"ticker": "IWDA",
			"amount_eur": 2000.0,
			"shares": 8.0,
			"order_type": "buy",
			"status": "Finalizada",
		},
		{
			"date": "2024-04-05",
			"isin": "IE00B3RBWM25",
			"ticker": "VWRL",
			"amount_eur": 300.0,
			"shares": 5.0,
			"order_type": "sell",
			"status": "Finalizada",
		},
		{
			"date": "2024-05-01",
			"isin": "US0378331005",
			"ticker": "AAPL",
			"amount_eur": 1500.0,
			"shares": 15.0,
			"order_type": "buy",
			"status": "Rechazada",
		},
	]

	for order in test_orders:
		client.post("/api/orders/", json=order, headers=auth_headers)

	yield

	# Cleanup
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	if "test_order_history" in users:
		users["test_order_history"]["orders"] = []
		StorageService.save_json(users_file, users)


def test_get_all_orders(auth_headers):
	"""Test getting all orders without filters."""
	response = client.get("/api/orders/", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert "orders" in data
	assert "total" in data
	assert data["total"] == 5
	assert len(data["orders"]) == 5


def test_filter_by_isin(auth_headers):
	"""Test filtering orders by ISIN."""
	response = client.get("/api/orders/?isin=IE00B4L5Y983", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total"] == 2
	assert all(o["isin"] == "IE00B4L5Y983" for o in data["orders"])


def test_filter_by_ticker(auth_headers):
	"""Test filtering orders by ticker."""
	response = client.get("/api/orders/?ticker=VWRL", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total"] == 2
	assert all(o["ticker"] == "VWRL" for o in data["orders"])


def test_filter_by_order_type(auth_headers):
	"""Test filtering by order type (buy/sell)."""
	# Test buy orders
	buy_response = client.get("/api/orders/?order_type=buy", headers=auth_headers)

	assert buy_response.status_code == 200
	buy_data = buy_response.json()
	assert buy_data["total"] == 4
	assert all(o["order_type"] == "buy" for o in buy_data["orders"])

	# Test sell orders
	sell_response = client.get("/api/orders/?order_type=sell", headers=auth_headers)

	assert sell_response.status_code == 200
	sell_data = sell_response.json()
	assert sell_data["total"] == 1
	assert sell_data["orders"][0]["order_type"] == "sell"


def test_filter_by_status(auth_headers):
	"""Test filtering by order status."""
	# Test Finalizada
	finalizada_response = client.get("/api/orders/?status=Finalizada", headers=auth_headers)

	assert finalizada_response.status_code == 200
	finalizada_data = finalizada_response.json()
	assert finalizada_data["total"] == 4

	# Test Rechazada
	rechazada_response = client.get("/api/orders/?status=Rechazada", headers=auth_headers)

	assert rechazada_response.status_code == 200
	rechazada_data = rechazada_response.json()
	assert rechazada_data["total"] == 1
	assert rechazada_data["orders"][0]["status"] == "Rechazada"


def test_filter_by_date_range(auth_headers):
	"""Test filtering by date range."""
	response = client.get("/api/orders/?date_from=2024-02-01&date_to=2024-03-31", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total"] == 2
	dates = [o["date"] for o in data["orders"]]
	# Check each date is within the range
	for date in dates:
		assert date >= "2024-02-01" and date <= "2024-03-31", f"Date {date} out of range"


def test_combined_filters(auth_headers):
	"""Test combining multiple filters."""
	response = client.get("/api/orders/?isin=IE00B4L5Y983&order_type=buy&status=Finalizada", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total"] == 2
	for order in data["orders"]:
		assert order["isin"] == "IE00B4L5Y983"
		assert order["order_type"] == "buy"
		assert order["status"] == "Finalizada"


def test_sort_by_date_desc(auth_headers):
	"""Test sorting by date descending (most recent first)."""
	response = client.get("/api/orders/?sort_by=date&sort_order=desc", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	dates = [o["date"] for o in data["orders"]]
	assert dates == sorted(dates, reverse=True)


def test_sort_by_date_asc(auth_headers):
	"""Test sorting by date ascending (oldest first)."""
	response = client.get("/api/orders/?sort_by=date&sort_order=asc", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	dates = [o["date"] for o in data["orders"]]
	assert dates == sorted(dates)


def test_sort_by_amount(auth_headers):
	"""Test sorting by amount."""
	response = client.get("/api/orders/?sort_by=amount_eur&sort_order=desc", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	amounts = [o["amount_eur"] for o in data["orders"]]
	assert amounts == sorted(amounts, reverse=True)


def test_sort_by_shares(auth_headers):
	"""Test sorting by shares."""
	response = client.get("/api/orders/?sort_by=shares&sort_order=asc", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	shares = [o["shares"] for o in data["orders"]]
	assert shares == sorted(shares)


def test_pagination_limit(auth_headers):
	"""Test pagination with limit."""
	response = client.get("/api/orders/?limit=2", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert len(data["orders"]) == 2
	assert data["total"] == 5
	assert data["limit"] == 2


def test_pagination_offset(auth_headers):
	"""Test pagination with offset."""
	response = client.get("/api/orders/?offset=3", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert len(data["orders"]) == 2  # 5 total - 3 offset = 2 remaining
	assert data["total"] == 5
	assert data["offset"] == 3


def test_pagination_limit_and_offset(auth_headers):
	"""Test pagination with both limit and offset."""
	response = client.get("/api/orders/?limit=2&offset=1", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert len(data["orders"]) == 2
	assert data["total"] == 5
	assert data["limit"] == 2
	assert data["offset"] == 1


def test_response_includes_filter_info(auth_headers):
	"""Test that response includes filter and sort information."""
	response = client.get("/api/orders/?isin=IE00B4L5Y983&sort_by=amount_eur&sort_order=desc", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert "filters" in data
	assert data["filters"]["isin"] == "IE00B4L5Y983"

	assert "sort" in data
	assert data["sort"]["by"] == "amount_eur"
	assert data["sort"]["order"] == "desc"


def test_empty_result_with_filters(auth_headers):
	"""Test filtering that returns no results."""
	response = client.get("/api/orders/?ticker=NONEXISTENT", headers=auth_headers)

	assert response.status_code == 200
	data = response.json()

	assert data["total"] == 0
	assert len(data["orders"]) == 0
