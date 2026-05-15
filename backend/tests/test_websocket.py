"""Tests for WebSocket real-time updates."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.main import app
from app.services.storage_service import StorageService

client = TestClient(app)


def authenticate_websocket(websocket, token: str) -> dict:
	"""Authenticate a WebSocket test connection and return its handshake."""
	websocket.send_json({"type": "auth", "token": token})
	return websocket.receive_json()


@pytest.fixture
def auth_token():
	"""Get authentication token for test user."""
	username = "test_websocket"
	password = "testpass123"

	# Try to register
	client.post("/api/auth/register", json={"username": username, "email": f"{username}@example.com", "password": password})

	# Login
	response = client.post("/api/auth/login", data={"username": username, "password": password})

	assert response.status_code == 200
	return response.json()["access_token"]


@pytest.fixture
def cleanup_user_data():
	"""Clean up test user data before and after tests."""
	username = "test_websocket"

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


def test_websocket_connection_with_valid_token(auth_token, cleanup_user_data):
	"""Test WebSocket connection with valid authentication token."""
	with client.websocket_connect("/ws") as websocket:
		data = authenticate_websocket(websocket, auth_token)

		# Should receive connection status message
		assert data["type"] == "connection_status"
		assert data["status"] == "connected"
		assert data["client_id"] == "test_websocket"


def test_websocket_connection_without_token(cleanup_user_data):
	"""Test WebSocket connection fails without token."""
	with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws") as websocket:
		websocket.send_json({"type": "auth"})
		websocket.receive_json()


def test_websocket_connection_with_invalid_token(cleanup_user_data):
	"""Test WebSocket connection fails with invalid token."""
	with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws") as websocket:
		websocket.send_json({"type": "auth", "token": "invalid_token"})
		websocket.receive_json()


def test_websocket_connection_with_trusted_proxy_header(monkeypatch, cleanup_user_data):
	"""Test WebSocket connection can authenticate with a trusted proxy identity header."""
	username = "test_websocket_trusted"
	email = "trusted-ws@example.com"
	client.post("/api/auth/register", json={"username": username, "email": email, "password": "testpass123"})
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ENABLED", True)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", email)

	with client.websocket_connect("/ws", headers={"Tailscale-User-Login": email}) as websocket:
		data = websocket.receive_json()

		assert data["type"] == "connection_status"
		assert data["status"] == "connected"
		assert data["client_id"] == username


def test_websocket_trusted_proxy_missing_header_still_requires_token(monkeypatch, cleanup_user_data):
	"""Test trusted proxy mode still rejects unauthenticated WebSockets without identity or token."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ENABLED", True)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "trusted-ws@example.com")

	with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws") as websocket:
		websocket.send_json({"type": "auth"})
		websocket.receive_json()


def test_websocket_trusted_proxy_rejects_denied_identity(monkeypatch, cleanup_user_data):
	"""Test WebSocket trusted proxy auth rejects non-allowlisted identities."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ENABLED", True)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "trusted-ws@example.com")

	with (
		pytest.raises(WebSocketDisconnect),
		client.websocket_connect("/ws", headers={"Tailscale-User-Login": "denied@example.com"}) as websocket,
	):
		websocket.receive_json()


def test_websocket_legacy_client_id_route_is_removed(cleanup_user_data):
	"""Test legacy unauthenticated WebSocket route is not available."""
	with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws/test-client"):
		pass


def test_websocket_ping_pong(auth_token, cleanup_user_data):
	"""Test WebSocket ping/pong mechanism."""
	with client.websocket_connect("/ws") as websocket:
		authenticate_websocket(websocket, auth_token)

		# Send ping
		websocket.send_json({"type": "ping"})

		# Should receive pong
		data = websocket.receive_json()
		assert data["type"] == "pong"
		assert "timestamp" in data


def test_websocket_broadcast_on_order_create(auth_token, cleanup_user_data):
	"""Test that WebSocket broadcasts when an order is created."""
	with client.websocket_connect("/ws") as websocket:
		authenticate_websocket(websocket, auth_token)

		# Create an order via API
		response = client.post(
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
			headers={"Authorization": f"Bearer {auth_token}"},
		)
		assert response.status_code == 201

		# Should receive broadcast message
		data = websocket.receive_json()
		assert data["type"] == "order_created"
		assert "order_id" in data
		assert "timestamp" in data


def test_websocket_broadcast_on_order_update(auth_token, cleanup_user_data):
	"""Test that WebSocket broadcasts when an order is updated."""
	# Create an order first
	response = client.post(
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
		headers={"Authorization": f"Bearer {auth_token}"},
	)
	order_id = response.json()["id"]

	with client.websocket_connect("/ws") as websocket:
		authenticate_websocket(websocket, auth_token)

		# Update the order
		response = client.put(
			f"/api/orders/{order_id}",
			json={"notes": "Updated note"},
			headers={"Authorization": f"Bearer {auth_token}"},
		)
		assert response.status_code == 200

		# Should receive broadcast message
		data = websocket.receive_json()
		assert data["type"] == "order_updated"
		assert data["order_id"] == order_id
		assert "timestamp" in data


def test_websocket_broadcast_on_order_delete(auth_token, cleanup_user_data):
	"""Test that WebSocket broadcasts when an order is deleted."""
	# Create an order first
	response = client.post(
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
		headers={"Authorization": f"Bearer {auth_token}"},
	)
	order_id = response.json()["id"]

	with client.websocket_connect("/ws") as websocket:
		authenticate_websocket(websocket, auth_token)

		# Delete the order
		response = client.delete(
			f"/api/orders/{order_id}",
			headers={"Authorization": f"Bearer {auth_token}"},
		)
		assert response.status_code == 204

		# Should receive broadcast message
		data = websocket.receive_json()
		assert data["type"] == "order_deleted"
		assert data["order_id"] == order_id
		assert "timestamp" in data


def test_websocket_broadcast_on_csv_import(auth_token, cleanup_user_data):
	"""Test that WebSocket broadcasts when CSV is imported."""
	with client.websocket_connect("/ws") as websocket:
		authenticate_websocket(websocket, auth_token)

		# Import CSV
		csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE00B4L5Y983,"1.000,00 EUR",10.5,Finalizada"""

		response = client.post(
			"/api/orders/import-csv",
			files={"file": ("test.csv", csv_content, "text/csv")},
			headers={"Authorization": f"Bearer {auth_token}"},
		)
		assert response.status_code == 200

		# Should receive broadcast message
		data = websocket.receive_json()
		assert data["type"] == "orders_imported"
		assert data["count"] == 1
		assert "timestamp" in data
