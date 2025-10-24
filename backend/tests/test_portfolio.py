"""Tests for portfolio endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.persistence import save_user_data
from app.services.auth import get_password_hash

client = TestClient(app)


@pytest.fixture
def authenticated_client():
	"""Create an authenticated test client."""
	username = "test_portfolio_user"
	password = "testpass123"
	user_data = {"username": username, "hashed_password": get_password_hash(password), "is_active": True, "holdings": []}
	save_user_data(username, user_data)

	# Get auth token
	response = client.post("/api/auth/login", data={"username": username, "password": password})
	token = response.json()["access_token"]
	headers = {"Authorization": f"Bearer {token}"}

	yield client, headers


def test_get_empty_portfolio(authenticated_client):
	"""Test getting an empty portfolio."""
	client, headers = authenticated_client

	# Get all orders and delete them to ensure clean state
	orders_response = client.get("/api/orders", headers=headers)
	if orders_response.status_code == 200:
		orders_data = orders_response.json()
		orders = orders_data.get("orders", [])
		for order in orders:
			client.delete(f"/api/orders/{order['id']}", headers=headers)

	# Now portfolio should be empty
	response = client.get("/api/portfolio/", headers=headers)
	assert response.status_code == 200
	data = response.json()
	assert "holdings" in data
	assert len(data["holdings"]) == 0


def test_add_investment(authenticated_client):
	"""Test adding a new investment."""
	client, headers = authenticated_client
	investment_data = {
		"symbol": "AAPL",
		"name": "Apple Inc.",
		"quantity": 10.0,
		"purchase_price": 150.0,
		"purchase_date": "2024-01-15",
		"asset_type": "stock",
		"currency": "USD",
	}
	response = client.post("/api/portfolio/", json=investment_data, headers=headers)
	assert response.status_code == 201
	data = response.json()
	assert data["symbol"] == "AAPL"
	assert data["quantity"] == 10.0
	assert "id" in data


def test_get_portfolio_with_holdings(authenticated_client):
	"""Test getting portfolio after adding investment."""
	client, headers = authenticated_client

	# Add an order (portfolio now computed from orders)
	order_data = {
		"date": "01-02-2024",
		"isin": "US5949181045",  # MSFT ISIN
		"amount_eur": 1500.0,
		"shares": 5.0,
		"status": "Finalizada",
	}
	client.post("/api/orders", json=order_data, headers=headers)

	# Get portfolio
	response = client.get("/api/portfolio/", headers=headers)
	assert response.status_code == 200
	data = response.json()
	assert len(data["holdings"]) >= 1
	# Portfolio returns ISIN as symbol now
	assert any(h["symbol"] == "US5949181045" for h in data["holdings"])


def test_delete_investment(authenticated_client):
	"""Test that deleting an order affects portfolio holdings."""
	client, headers = authenticated_client

	# Clear existing orders for clean state
	orders_response = client.get("/api/orders", headers=headers)
	if orders_response.status_code == 200:
		orders_data = orders_response.json()
		orders = orders_data.get("orders", [])
		for order in orders:
			client.delete(f"/api/orders/{order['id']}", headers=headers)

	# Add an order
	order_data = {
		"date": "01-03-2024",
		"isin": "US02079K3059",  # GOOGL ISIN
		"amount_eur": 7500.0,
		"shares": 3.0,
		"status": "Finalizada",
	}
	add_response = client.post("/api/orders", json=order_data, headers=headers)
	order_id = add_response.json()["id"]

	# Verify order creates holding in portfolio
	portfolio_response = client.get("/api/portfolio/", headers=headers)
	holdings = portfolio_response.json()["holdings"]
	assert len(holdings) > 0

	# Delete the order
	delete_response = client.delete(f"/api/orders/{order_id}", headers=headers)
	assert delete_response.status_code == 204

	# Verify holding is gone from portfolio
	portfolio_response = client.get("/api/portfolio/", headers=headers)
	holdings = portfolio_response.json()["holdings"]
	assert len(holdings) == 0


def test_update_investment(authenticated_client):
	"""Test that updating an order affects portfolio holdings."""
	client, headers = authenticated_client

	# Clear existing orders for clean state
	orders_response = client.get("/api/orders", headers=headers)
	if orders_response.status_code == 200:
		orders_data = orders_response.json()
		orders = orders_data.get("orders", [])
		for order in orders:
			client.delete(f"/api/orders/{order['id']}", headers=headers)

	# Add an order
	order_data = {
		"date": "01-04-2024",
		"isin": "US88160R1014",  # TSLA ISIN
		"amount_eur": 1600.0,
		"shares": 2.0,
		"status": "Finalizada",
	}
	add_response = client.post("/api/orders", json=order_data, headers=headers)
	order_id = add_response.json()["id"]

	# Update the order
	update_data = {"shares": 5.0, "amount_eur": 3750.0}
	update_response = client.put(f"/api/orders/{order_id}", json=update_data, headers=headers)
	assert update_response.status_code == 200
	updated = update_response.json()
	assert updated["shares"] == 5.0
	assert updated["amount_eur"] == 3750.0

	# Verify portfolio reflects the update
	portfolio_response = client.get("/api/portfolio/", headers=headers)
	holdings = portfolio_response.json()["holdings"]
	assert len(holdings) == 1  # Only the one we added
	assert any(h["quantity"] == 5.0 for h in holdings)


def test_delete_nonexistent_investment(authenticated_client):
	"""Test deleting an investment that doesn't exist."""
	client, headers = authenticated_client
	response = client.delete("/api/portfolio/99999", headers=headers)
	assert response.status_code == 404
