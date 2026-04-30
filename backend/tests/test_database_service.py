"""Tests for SQLite runtime persistence."""

import pytest

from app.config import settings
from app.services.database_service import DatabaseService


def test_schema_initialization_is_idempotent() -> None:
	"""Initialize the SQLite schema repeatedly without errors."""
	db = DatabaseService()

	db.initialize()
	db.initialize()

	assert settings.DATABASE_PATH.exists()
	assert db.counts() == {
		"users": 0,
		"orders": 0,
		"prices": 0,
		"instruments": 0,
		"isin_mappings": 0,
		"isin_resolution_cache": 0,
	}


def test_user_order_price_round_trip() -> None:
	"""Persist and load user data with orders and prices."""
	db = DatabaseService()
	users = {
		"grimngor": {
			"username": "grimngor",
			"hashed_password": "hash",
			"holdings": [],
			"orders": [{"id": "order-1", "isin": "IE00TEST0001", "shares": 1, "amount_eur": 100, "status": "Finalizada"}],
			"prices": {"IE00TEST0001": {"price": 100.0, "currency": "EUR"}},
		}
	}

	db.save_users(users)

	loaded = db.load_users()
	assert loaded["grimngor"]["hashed_password"] == "hash"
	assert loaded["grimngor"]["orders"][0]["id"] == "order-1"
	assert loaded["grimngor"]["prices"]["IE00TEST0001"]["price"] == 100.0


def test_instrument_and_isin_mapping_round_trip() -> None:
	"""Persist and load instruments and ISIN mappings."""
	db = DatabaseService()

	db.save_instruments([{"isin": "IE00TEST0001", "symbol": "TEST.AS", "name": "Test Fund"}])
	db.save_isin_mappings({"IE00TEST0001": {"ticker": "TEST.AS", "source": "manual"}})
	db.save_isin_resolution_cache({"IE00TEST0002": {"ticker": "CACHE.AS", "source": "openfigi"}})

	assert db.load_instruments()[0]["symbol"] == "TEST.AS"
	assert db.load_isin_mappings()["IE00TEST0001"]["ticker"] == "TEST.AS"
	assert db.load_isin_resolution_cache()["IE00TEST0002"]["source"] == "openfigi"


def test_migration_renames_test_user_and_preserves_counts() -> None:
	"""Migrate JSON data while renaming test to grimngor."""
	db = DatabaseService()
	users = {
		"test": {
			"username": "test",
			"hashed_password": "hash",
			"orders": [{"id": "order-1", "isin": "IE00TEST0001"}],
			"prices": {"IE00TEST0001": {"price": 10.0}},
		}
	}

	counts = db.migrate_from_json(
		users,
		[{"isin": "IE00TEST0001", "symbol": "TEST.AS"}],
		{"IE00TEST0001": {"ticker": "TEST.AS"}},
		rename_users={"test": "grimngor"},
	)

	loaded = db.load_users()
	assert "test" not in loaded
	assert loaded["grimngor"]["username"] == "grimngor"
	assert loaded["grimngor"]["hashed_password"] == "hash"
	assert counts["orders"] == 1
	assert counts["prices"] == 1
	assert counts["instruments"] == 1
	assert counts["isin_mappings"] == 1


def test_migration_aborts_on_username_conflict() -> None:
	"""Abort migration when a rename target already exists."""
	db = DatabaseService()
	users = {"test": {"username": "test"}, "grimngor": {"username": "grimngor"}}

	with pytest.raises(ValueError, match="target user already exists"):
		db.migrate_from_json(users, [], {}, rename_users={"test": "grimngor"})
