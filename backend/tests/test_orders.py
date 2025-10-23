"""Tests for orders router (CSV import and CRUD)."""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.models.persistence import save_user_data, get_all_users
from app.services.auth import get_password_hash
from app.config import settings
import json

client = TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user for orders tests."""
    username = "test_orders_user"
    password = "testpass123"
    user_data = {"username": username, "hashed_password": get_password_hash(password), "is_active": True, "holdings": [], "orders": []}
    save_user_data(username, user_data)
    yield {"username": username, "password": password}
    # Cleanup: remove user
    users = get_all_users()
    if username in users:
        del users[username]
        with open(settings.DATA_DIR / "users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)


@pytest.fixture
def auth_token(test_user):
    """Get authentication token."""
    response = client.post("/api/auth/login", data={"username": test_user["username"], "password": test_user["password"]})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_import_csv_success(auth_token):
    """Test successful CSV import."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada
20/02/2024,US0378331005,1000.00 EUR,10.0,Finalizada"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/orders/import-csv", files={"file": ("orders.csv", f, "text/csv")}, headers={"Authorization": f"Bearer {auth_token}"}
            )

        print(f"Response: {response.status_code}, {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported_count"] == 2
        assert data["rejected_count"] == 0
        assert len(data["errors"]) == 0
    finally:
        tmp_path.unlink(missing_ok=True)


def test_import_csv_with_errors(auth_token):
    """Test CSV import with validation errors."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
invalid_date,IE00B4L5Y983,500.00 EUR,5.0,Finalizada
20/02/2024,INVALID_ISIN,1000.00 EUR,10.0,Finalizada"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/orders/import-csv", files={"file": ("orders.csv", f, "text/csv")}, headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["errors"]) > 0
    finally:
        tmp_path.unlink(missing_ok=True)


def test_import_csv_not_csv_file(auth_token):
    """Test CSV import with non-CSV file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp.write("not a csv")
        tmp_path = Path(tmp.name)

    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/orders/import-csv", files={"file": ("orders.txt", f, "text/plain")}, headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 400
        assert "CSV" in response.json()["detail"]
    finally:
        tmp_path.unlink(missing_ok=True)


def test_import_csv_unauthorized():
    """Test CSV import without authentication."""
    csv_content = "Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        with open(tmp_path, "rb") as f:
            response = client.post("/api/orders/import-csv", files={"file": ("orders.csv", f, "text/csv")})

        assert response.status_code == 401
    finally:
        tmp_path.unlink(missing_ok=True)


def test_get_orders_empty(auth_token):
    """Test getting orders when none exist."""
    response = client.get("/api/orders/", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_orders_after_import(auth_token):
    """Test getting orders after CSV import."""
    # First import some orders
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        with open(tmp_path, "rb") as f:
            client.post("/api/orders/import-csv", files={"file": ("orders.csv", f, "text/csv")}, headers={"Authorization": f"Bearer {auth_token}"})
    finally:
        tmp_path.unlink(missing_ok=True)

    # Now get orders
    response = client.get("/api/orders/", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["isin"] == "IE00B4L5Y983"


def test_get_order_by_id(auth_token):
    """Test getting specific order by ID."""
    # First import an order
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        with open(tmp_path, "rb") as f:
            import_response = client.post("/api/orders/import-csv", files={"file": ("orders.csv", f, "text/csv")}, headers={"Authorization": f"Bearer {auth_token}"})
    finally:
        tmp_path.unlink(missing_ok=True)

    # Get all orders first to get an order ID
    orders_response = client.get("/api/orders/", headers={"Authorization": f"Bearer {auth_token}"})
    orders = orders_response.json()
    assert len(orders) > 0
    
    order_id = orders[0]["id"]
    
    # Get specific order by ID
    response = client.get(f"/api/orders/{order_id}", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["isin"] == "IE00B4L5Y983"


def test_get_order_not_found(auth_token):
    """Test getting non-existent order."""
    response = client.get("/api/orders/999", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 404
