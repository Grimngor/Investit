"""Tests for price refresh endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.price_service import PriceService
from app.services.storage_service import StorageService
from tests.conftest import make_auth_headers

client = TestClient(app)


def _set_user_orders_and_prices(username: str, prices: dict[str, Any] | None = None) -> None:
	"""Persist one finalized order and optional price data for a test user."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})
	users[username]["orders"] = [
		{
			"id": "order-1",
			"date": "2024-01-01",
			"isin": "IE00TEST0001",
			"amount_eur": 100.0,
			"shares": 1.0,
			"order_type": "buy",
			"status": "Finalizada",
		}
	]
	users[username]["prices"] = prices or {}
	StorageService.save_json(users_file, users)


def test_manual_price_fetch_always_queues_force_refresh(monkeypatch) -> None:
	"""Test manual price fetch queues a force refresh."""
	username = "manual_price_user"
	headers = make_auth_headers(client, username)
	_set_user_orders_and_prices(
		username,
		{"IE00TEST0001": {"price": 123.0, "timestamp": datetime.now(UTC).isoformat()}},
	)
	calls = []

	async def fake_fetch(user: str, isins: list[str], force: bool = False) -> None:
		calls.append((user, isins, force))

	monkeypatch.setattr(PriceService, "fetch_and_update_prices", fake_fetch)

	response = client.post("/api/prices/fetch", headers=headers)

	assert response.status_code == 200
	assert response.json()["count"] == 1
	assert calls == [(username, ["IE00TEST0001"], True)]


def test_refresh_if_needed_queues_missing_prices(monkeypatch) -> None:
	"""Test refresh-if-needed queues missing cached prices."""
	username = "missing_price_user"
	headers = make_auth_headers(client, username)
	_set_user_orders_and_prices(username)
	calls = []

	async def fake_fetch(user: str, isins: list[str], force: bool = False) -> None:
		calls.append((user, isins, force))

	monkeypatch.setattr(PriceService, "fetch_and_update_prices", fake_fetch)

	response = client.post("/api/prices/refresh-if-needed", headers=headers)

	assert response.status_code == 200
	assert response.json()["queued"] is True
	assert response.json()["count"] == 1
	assert calls == [(username, ["IE00TEST0001"], False)]


def test_refresh_if_needed_skips_fresh_prices(monkeypatch) -> None:
	"""Test refresh-if-needed does not queue when cached prices are fresh."""
	username = "fresh_price_user"
	headers = make_auth_headers(client, username)
	_set_user_orders_and_prices(
		username,
		{"IE00TEST0001": {"price": 123.0, "timestamp": datetime.now(UTC).isoformat()}},
	)
	calls = []

	async def fake_fetch(user: str, isins: list[str], force: bool = False) -> None:
		calls.append((user, isins, force))

	monkeypatch.setattr(PriceService, "fetch_and_update_prices", fake_fetch)

	response = client.post("/api/prices/refresh-if-needed", headers=headers)

	assert response.status_code == 200
	assert response.json()["queued"] is False
	assert response.json()["count"] == 0
	assert calls == []
