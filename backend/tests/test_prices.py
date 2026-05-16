"""Tests for price refresh endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.metrics_service import metrics
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


@pytest.mark.asyncio
async def test_price_refresh_uses_stale_cache_when_provider_fails(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Failed provider refresh keeps a usable stale cached price with source attribution."""
	username = "stale_fallback_user"
	headers = make_auth_headers(client, username)
	stale_timestamp = (datetime.now(UTC) - timedelta(days=10)).isoformat()
	_set_user_orders_and_prices(
		username,
		{
			"IE00TEST0001": {
				"price": 123.0,
				"currency": "EUR",
				"timestamp": stale_timestamp,
				"source": "yahoo_finance",
			}
		},
	)

	async def no_quote(isin: str) -> dict[str, Any] | None:
		return None

	monkeypatch.setattr(PriceService, "fetch_traditional_quote", no_quote)

	await PriceService.fetch_and_update_prices(username, ["IE00TEST0001"], force=True)

	users = StorageService.load_json(settings.DATA_DIR / "users.json", default={})
	price = users[username]["prices"]["IE00TEST0001"]
	assert headers["Authorization"].startswith("Bearer ")
	assert price["price"] == 123.0
	assert price["timestamp"] == stale_timestamp
	assert price["source"] == "stale_cache"
	assert price["stale_cache_fallback"] is True
	assert price["source_detail"] == "Stale cached price used after provider refresh failed"


def test_price_status_exposes_provider_order_and_health() -> None:
	"""Price status includes reliability metadata for provider observability."""
	username = "provider_health_user"
	headers = make_auth_headers(client, username)
	_set_user_orders_and_prices(username)

	metrics.record_provider_call("yahoo_finance.quote", "price", False, detail="offline")

	response = client.get("/api/prices/status", headers=headers)

	assert response.status_code == 200
	payload = response.json()
	assert payload["provider_order"] == ["yahoo_finance.quote", "stale_cache"]
	assert payload["provider_health"]["price:yahoo_finance.quote"]["failure_count"] >= 1
