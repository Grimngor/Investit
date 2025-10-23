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

    # Add an investment first
    investment_data = {
        "symbol": "MSFT",
        "name": "Microsoft",
        "quantity": 5.0,
        "purchase_price": 300.0,
        "purchase_date": "2024-02-01",
    }
    client.post("/api/portfolio/", json=investment_data, headers=headers)

    # Get portfolio
    response = client.get("/api/portfolio/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["holdings"]) >= 1
    assert any(h["symbol"] == "MSFT" for h in data["holdings"])


def test_delete_investment(authenticated_client):
    """Test deleting an investment."""
    client, headers = authenticated_client

    # Add an investment
    investment_data = {
        "symbol": "GOOGL",
        "name": "Alphabet",
        "quantity": 3.0,
        "purchase_price": 2500.0,
        "purchase_date": "2024-03-01",
    }
    add_response = client.post("/api/portfolio/", json=investment_data, headers=headers)
    investment_id = add_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/api/portfolio/{investment_id}", headers=headers)
    assert delete_response.status_code == 204

    # Verify it's gone
    portfolio_response = client.get("/api/portfolio/", headers=headers)
    holdings = portfolio_response.json()["holdings"]
    assert not any(h["id"] == investment_id for h in holdings)


def test_update_investment(authenticated_client):
    """Test updating an investment."""
    client, headers = authenticated_client

    # Add an investment
    investment_data = {
        "symbol": "TSLA",
        "name": "Tesla",
        "quantity": 2.0,
        "purchase_price": 800.0,
        "purchase_date": "2024-04-01",
    }
    add_response = client.post("/api/portfolio/", json=investment_data, headers=headers)
    investment_id = add_response.json()["id"]

    # Update it
    update_data = {"quantity": 5.0, "purchase_price": 750.0}
    update_response = client.put(f"/api/portfolio/{investment_id}", json=update_data, headers=headers)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["quantity"] == 5.0
    assert updated["purchase_price"] == 750.0


def test_delete_nonexistent_investment(authenticated_client):
    """Test deleting an investment that doesn't exist."""
    client, headers = authenticated_client
    response = client.delete("/api/portfolio/99999", headers=headers)
    assert response.status_code == 404
