"""Tests for manual order CRUD operations."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage_service import StorageService
from app.config import settings

client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Get authentication headers for test user."""
    # Register test user
    username = "test_manual_orders"
    password = "testpass123"
    
    # Try to register (might already exist)
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": "test@example.com",
            "password": password
        }
    )
    
    # Login
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password}
    )
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def cleanup_test_user():
    """Clean up test user orders before each test."""
    yield
    # Cleanup after test
    users_file = settings.DATA_DIR / "users.json"
    users = StorageService.load_json(users_file, default={})
    if "test_manual_orders" in users:
        users["test_manual_orders"]["orders"] = []
        StorageService.save_json(users_file, users)


def test_create_order(auth_headers):
    """Test creating a new order manually."""
    order_data = {
        "date": "2024-01-15",
        "isin": "IE00B4L5Y983",
        "ticker": "IWDA",
        "amount_eur": 1000.50,
        "shares": 5.5,
        "order_type": "buy",
        "status": "Finalizada",
        "notes": "Test order"
    }
    
    response = client.post(
        "/api/orders/",
        json=order_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["date"] == "2024-01-15"
    assert data["isin"] == "IE00B4L5Y983"
    assert data["ticker"] == "IWDA"
    assert data["amount_eur"] == 1000.50
    assert data["shares"] == 5.5
    assert data["order_type"] == "buy"
    assert data["status"] == "Finalizada"
    assert data["notes"] == "Test order"
    assert "id" in data
    assert "created_at" in data


def test_create_order_unauthorized():
    """Test creating order without authentication."""
    order_data = {
        "date": "2024-01-15",
        "isin": "IE00B4L5Y983",
        "amount_eur": 1000.0,
        "shares": 5.0,
        "order_type": "buy"
    }
    
    response = client.post("/api/orders/", json=order_data)
    assert response.status_code == 401


def test_get_orders_empty(auth_headers):
    """Test getting orders when user has none."""
    response = client.get("/api/orders/", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == []


def test_get_orders_after_create(auth_headers):
    """Test retrieving orders after creating some."""
    # Create two orders
    order1 = {
        "date": "2024-01-15",
        "isin": "IE00B4L5Y983",
        "ticker": "IWDA",
        "amount_eur": 1000.0,
        "shares": 5.0,
        "order_type": "buy"
    }
    
    order2 = {
        "date": "2024-01-20",
        "isin": "IE00B3RBWM25",
        "ticker": "VWRL",
        "amount_eur": 500.0,
        "shares": 10.0,
        "order_type": "buy"
    }
    
    client.post("/api/orders/", json=order1, headers=auth_headers)
    client.post("/api/orders/", json=order2, headers=auth_headers)
    
    # Get all orders
    response = client.get("/api/orders/", headers=auth_headers)
    
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 2
    
    # Should be sorted by date (most recent first)
    assert orders[0]["date"] == "2024-01-20"
    assert orders[1]["date"] == "2024-01-15"


def test_get_order_by_id(auth_headers):
    """Test retrieving a specific order by ID."""
    # Create order
    create_response = client.post(
        "/api/orders/",
        json={
            "date": "2024-01-15",
            "isin": "IE00B4L5Y983",
            "ticker": "IWDA",
            "amount_eur": 1000.0,
            "shares": 5.0,
            "order_type": "buy"
        },
        headers=auth_headers
    )
    
    order_id = create_response.json()["id"]
    
    # Get order by ID
    response = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    
    assert response.status_code == 200
    order = response.json()
    assert order["id"] == order_id
    assert order["isin"] == "IE00B4L5Y983"


def test_get_order_not_found(auth_headers):
    """Test getting non-existent order."""
    response = client.get("/api/orders/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_update_order(auth_headers):
    """Test updating an existing order."""
    # Create order
    create_response = client.post(
        "/api/orders/",
        json={
            "date": "2024-01-15",
            "isin": "IE00B4L5Y983",
            "ticker": "IWDA",
            "amount_eur": 1000.0,
            "shares": 5.0,
            "order_type": "buy",
            "notes": "Original note"
        },
        headers=auth_headers
    )
    
    order_id = create_response.json()["id"]
    
    # Update order
    update_response = client.put(
        f"/api/orders/{order_id}",
        json={
            "shares": 7.5,
            "amount_eur": 1500.0,
            "notes": "Updated note"
        },
        headers=auth_headers
    )
    
    assert update_response.status_code == 200
    updated = update_response.json()
    
    assert updated["id"] == order_id
    assert updated["shares"] == 7.5
    assert updated["amount_eur"] == 1500.0
    assert updated["notes"] == "Updated note"
    # Unchanged fields
    assert updated["isin"] == "IE00B4L5Y983"
    assert updated["date"] == "2024-01-15"


def test_update_order_not_found(auth_headers):
    """Test updating non-existent order."""
    response = client.put(
        "/api/orders/nonexistent-id",
        json={"shares": 10.0},
        headers=auth_headers
    )
    assert response.status_code == 404


def test_delete_order(auth_headers):
    """Test deleting an order."""
    # Create order
    create_response = client.post(
        "/api/orders/",
        json={
            "date": "2024-01-15",
            "isin": "IE00B4L5Y983",
            "ticker": "IWDA",
            "amount_eur": 1000.0,
            "shares": 5.0,
            "order_type": "buy"
        },
        headers=auth_headers
    )
    
    order_id = create_response.json()["id"]
    
    # Delete order
    delete_response = client.delete(f"/api/orders/{order_id}", headers=auth_headers)
    assert delete_response.status_code == 204
    
    # Verify order is gone
    get_response = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert get_response.status_code == 404
    
    # Verify orders list is empty
    list_response = client.get("/api/orders/", headers=auth_headers)
    assert len(list_response.json()) == 0


def test_delete_order_not_found(auth_headers):
    """Test deleting non-existent order."""
    response = client.delete("/api/orders/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_order_crud_workflow(auth_headers):
    """Test complete CRUD workflow."""
    # Create
    create_response = client.post(
        "/api/orders/",
        json={
            "date": "2024-01-15",
            "isin": "IE00B4L5Y983",
            "ticker": "IWDA",
            "amount_eur": 1000.0,
            "shares": 5.0,
            "order_type": "buy",
            "notes": "Test workflow"
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    order_id = create_response.json()["id"]
    
    # Read
    get_response = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["notes"] == "Test workflow"
    
    # Update
    update_response = client.put(
        f"/api/orders/{order_id}",
        json={"notes": "Updated workflow"},
        headers=auth_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["notes"] == "Updated workflow"
    
    # Delete
    delete_response = client.delete(f"/api/orders/{order_id}", headers=auth_headers)
    assert delete_response.status_code == 204
    
    # Verify deletion
    final_get = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert final_get.status_code == 404
