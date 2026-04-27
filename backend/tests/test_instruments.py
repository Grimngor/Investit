"""Tests for instrument metadata routes."""

from typing import Any

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.storage_service import StorageService
from tests.conftest import make_auth_headers

client = TestClient(app)


def test_list_and_get_instruments() -> None:
	"""List and fetch persisted instrument metadata."""
	headers = make_auth_headers(client, "instrument_list_user")
	instruments_file = settings.DATA_DIR / "instruments.json"
	StorageService.save_json(
		instruments_file,
		[
			{
				"isin": "IE00B4L5Y983",
				"symbol": "IWDA.AS",
				"name": "iShares Core MSCI World",
				"type": "ETF",
			}
		],
	)

	list_response = client.get("/api/instruments/", headers=headers)
	assert list_response.status_code == 200
	assert list_response.json()[0]["isin"] == "IE00B4L5Y983"

	get_response = client.get("/api/instruments/IE00B4L5Y983", headers=headers)
	assert get_response.status_code == 200
	assert get_response.json()["symbol"] == "IWDA.AS"


def test_update_instrument_metadata_upserts() -> None:
	"""Create or update instrument metadata through the manual override endpoint."""
	headers = make_auth_headers(client, "instrument_update_user")
	StorageService.save_json(settings.DATA_DIR / "instruments.json", [])

	response = client.put(
		"/api/instruments/IE00B4L5Y983",
		json={
			"symbol": "IWDA.AS",
			"name": "Manual Name",
			"type": "ETF",
			"geo_allocation": {"US": 0.7, "Europe": 0.3},
		},
		headers=headers,
	)

	assert response.status_code == 200
	assert response.json()["name"] == "Manual Name"

	get_response = client.get("/api/instruments/IE00B4L5Y983", headers=headers)
	assert get_response.status_code == 200
	assert get_response.json()["geo_allocation"]["US"] == 0.7


def test_refresh_crypto_metadata_without_external_provider() -> None:
	"""Refresh crypto metadata without calling external fund providers."""
	username = "instrument_crypto_user"
	headers = make_auth_headers(client, username)
	users_file = settings.DATA_DIR / "users.json"

	def add_crypto_order(users: dict[str, Any]) -> dict[str, Any]:
		users[username]["orders"] = [
			{
				"id": "crypto-order",
				"date": "2024-01-01",
				"isin": "BTC",
				"amount_eur": 100.0,
				"shares": 0.01,
				"order_type": "buy",
				"status": "Finalizada",
			}
		]
		return users

	StorageService.update_json(users_file, add_crypto_order, default={})
	StorageService.save_json(settings.DATA_DIR / "instruments.json", [])

	response = client.post("/api/instruments/refresh", headers=headers)

	assert response.status_code == 200
	assert response.json()["updated"] == 1
	instruments = StorageService.load_json(settings.DATA_DIR / "instruments.json", default=[])
	assert instruments[0]["isin"] == "BTC"
	assert instruments[0]["type"] == "Crypto"
