"""SQLite database service for runtime persistence."""

import json
import sqlite3
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.config import settings


class DatabaseService:
	"""Service for SQLite runtime data operations."""

	SCHEMA_VERSION = 1

	def __init__(self, database_path: Path | None = None) -> None:
		"""Initialize the service with a database path."""
		self.database_path = database_path or settings.DATABASE_PATH

	@contextmanager
	def connect(self):
		"""Open a SQLite connection with app defaults."""
		self.database_path.parent.mkdir(parents=True, exist_ok=True)
		conn = sqlite3.connect(self.database_path)
		conn.row_factory = sqlite3.Row
		conn.execute("PRAGMA foreign_keys = ON")
		try:
			yield conn
		finally:
			conn.close()

	def initialize(self) -> None:
		"""Create SQLite schema if it does not already exist."""
		with self.connect() as conn:
			conn.executescript(
				"""
				CREATE TABLE IF NOT EXISTS schema_migrations (
					version INTEGER PRIMARY KEY,
					applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
				);

				CREATE TABLE IF NOT EXISTS users (
					username TEXT PRIMARY KEY,
					user_json TEXT NOT NULL
				);

				CREATE TABLE IF NOT EXISTS orders (
					username TEXT NOT NULL,
					order_key TEXT NOT NULL,
					sort_order INTEGER NOT NULL,
					order_json TEXT NOT NULL,
					PRIMARY KEY (username, order_key),
					FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
				);

				CREATE TABLE IF NOT EXISTS prices (
					username TEXT NOT NULL,
					isin TEXT NOT NULL,
					price_json TEXT NOT NULL,
					PRIMARY KEY (username, isin),
					FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
				);

				CREATE TABLE IF NOT EXISTS instruments (
					isin TEXT PRIMARY KEY,
					instrument_json TEXT NOT NULL
				);

				CREATE TABLE IF NOT EXISTS isin_mappings (
					isin TEXT PRIMARY KEY,
					mapping_json TEXT NOT NULL
				);

				CREATE TABLE IF NOT EXISTS isin_resolution_cache (
					isin TEXT PRIMARY KEY,
					mapping_json TEXT NOT NULL
				);

				CREATE TABLE IF NOT EXISTS gmail_connections (
					username TEXT PRIMARY KEY,
					connection_json TEXT NOT NULL,
					FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
				);

				CREATE TABLE IF NOT EXISTS gmail_imports (
					username TEXT NOT NULL,
					gmail_message_id TEXT NOT NULL,
					import_json TEXT NOT NULL,
					PRIMARY KEY (username, gmail_message_id),
					FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
				);
				"""
			)
			conn.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)", (self.SCHEMA_VERSION,))
			conn.commit()

	def load_users(self) -> dict[str, Any]:
		"""Load all users with their orders and prices."""
		self.initialize()
		with self.connect() as conn:
			users: dict[str, Any] = {}
			for row in conn.execute("SELECT username, user_json FROM users ORDER BY username"):
				user_data = json.loads(row["user_json"])
				user_data["username"] = row["username"]
				user_data["orders"] = []
				user_data["prices"] = {}
				users[row["username"]] = user_data

			for row in conn.execute("SELECT username, order_json FROM orders ORDER BY username, sort_order"):
				if row["username"] in users:
					users[row["username"]]["orders"].append(json.loads(row["order_json"]))

			for row in conn.execute("SELECT username, isin, price_json FROM prices ORDER BY username, isin"):
				if row["username"] in users:
					users[row["username"]]["prices"][row["isin"]] = json.loads(row["price_json"])

			return users

	def save_users(self, users: dict[str, Any]) -> None:
		"""Replace user, order, and price data while preserving per-user integration rows."""
		self.initialize()
		with self.connect() as conn, conn:
			conn.execute("DELETE FROM prices")
			conn.execute("DELETE FROM orders")
			usernames = list(users)
			if usernames:
				placeholders = ",".join("?" for _ in usernames)
				conn.execute(f"DELETE FROM users WHERE username NOT IN ({placeholders})", usernames)
			else:
				conn.execute("DELETE FROM users")
			self._insert_users(conn, users)

	def update_users(self, update_fn: Callable[[dict[str, Any]], dict[str, Any]], default: dict[str, Any] | None = None) -> dict[str, Any]:
		"""Update all users through a compatibility callback."""
		users = self.load_users()
		if not users and default is not None:
			users = default
		updated = update_fn(users)
		self.save_users(updated)
		return updated

	def load_instruments(self) -> list[dict[str, Any]]:
		"""Load all instrument metadata."""
		self.initialize()
		with self.connect() as conn:
			return [json.loads(row["instrument_json"]) for row in conn.execute("SELECT instrument_json FROM instruments ORDER BY isin")]

	def save_instruments(self, instruments: list[dict[str, Any]]) -> None:
		"""Replace all instrument metadata."""
		self.initialize()
		with self.connect() as conn, conn:
			conn.execute("DELETE FROM instruments")
			for instrument in instruments:
				isin = instrument.get("isin")
				if isin:
					conn.execute(
						"INSERT INTO instruments (isin, instrument_json) VALUES (?, ?)",
						(isin, json.dumps(instrument, ensure_ascii=False)),
					)

	def upsert_instrument(self, isin: str, metadata: dict[str, Any]) -> dict[str, Any]:
		"""Upsert one instrument and return the stored record."""
		instruments = self.load_instruments()
		idx = next((i for i, inst in enumerate(instruments) if inst.get("isin") == isin), None)
		if idx is not None:
			instruments[idx].update({k: v for k, v in metadata.items() if v is not None})
			updated = instruments[idx]
		else:
			updated = {"isin": isin, **metadata}
			instruments.append(updated)
		self.save_instruments(instruments)
		return updated

	def load_isin_mappings(self) -> dict[str, dict[str, Any]]:
		"""Load local ISIN mappings."""
		return self._load_mapping_table("isin_mappings")

	def save_isin_mappings(self, mappings: dict[str, dict[str, Any]]) -> None:
		"""Replace local ISIN mappings."""
		self._save_mapping_table("isin_mappings", mappings)

	def load_isin_resolution_cache(self) -> dict[str, dict[str, Any]]:
		"""Load provider-derived ISIN mappings."""
		return self._load_mapping_table("isin_resolution_cache")

	def save_isin_resolution_cache(self, mappings: dict[str, dict[str, Any]]) -> None:
		"""Replace provider-derived ISIN mappings."""
		self._save_mapping_table("isin_resolution_cache", mappings)

	def migrate_from_json(
		self,
		users: dict[str, Any],
		instruments: list[dict[str, Any]],
		isin_mappings: dict[str, dict[str, Any]],
		isin_resolution_cache: dict[str, dict[str, Any]] | None = None,
		rename_users: dict[str, str] | None = None,
	) -> dict[str, int]:
		"""Migrate JSON payloads into SQLite and return migrated counts."""
		rename_users = rename_users or {}
		migrated_users = self._rename_users(users, rename_users)
		self.initialize()
		with self.connect() as conn, conn:
			self._clear_all(conn)
			self._insert_users(conn, migrated_users)
			for instrument in instruments:
				isin = instrument.get("isin")
				if isin:
					conn.execute(
						"INSERT INTO instruments (isin, instrument_json) VALUES (?, ?)",
						(isin, json.dumps(instrument, ensure_ascii=False)),
					)
			self._insert_mappings(conn, "isin_mappings", isin_mappings)
			self._insert_mappings(conn, "isin_resolution_cache", isin_resolution_cache or {})

		return {
			"users": len(migrated_users),
			"orders": sum(len(user.get("orders", [])) for user in migrated_users.values()),
			"prices": sum(len(user.get("prices", {})) for user in migrated_users.values()),
			"instruments": len(instruments),
			"isin_mappings": len(isin_mappings),
			"isin_resolution_cache": len(isin_resolution_cache or {}),
		}

	def counts(self) -> dict[str, int]:
		"""Return record counts for runtime tables."""
		self.initialize()
		with self.connect() as conn:
			return {
				"users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
				"orders": conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
				"prices": conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0],
				"instruments": conn.execute("SELECT COUNT(*) FROM instruments").fetchone()[0],
				"isin_mappings": conn.execute("SELECT COUNT(*) FROM isin_mappings").fetchone()[0],
				"isin_resolution_cache": conn.execute("SELECT COUNT(*) FROM isin_resolution_cache").fetchone()[0],
				"gmail_connections": conn.execute("SELECT COUNT(*) FROM gmail_connections").fetchone()[0],
				"gmail_imports": conn.execute("SELECT COUNT(*) FROM gmail_imports").fetchone()[0],
			}

	def _load_mapping_table(self, table: str) -> dict[str, dict[str, Any]]:
		"""Load a mapping table keyed by ISIN."""
		self.initialize()
		json_column = "mapping_json"
		with self.connect() as conn:
			rows = conn.execute(f"SELECT isin, {json_column} FROM {table} ORDER BY isin")
			return {row["isin"]: json.loads(row[json_column]) for row in rows}

	def _save_mapping_table(self, table: str, mappings: dict[str, dict[str, Any]]) -> None:
		"""Replace a mapping table keyed by ISIN."""
		self.initialize()
		with self.connect() as conn, conn:
			conn.execute(f"DELETE FROM {table}")
			self._insert_mappings(conn, table, mappings)

	def _clear_all(self, conn: sqlite3.Connection) -> None:
		"""Clear all runtime data tables."""
		conn.execute("DELETE FROM isin_resolution_cache")
		conn.execute("DELETE FROM isin_mappings")
		conn.execute("DELETE FROM instruments")
		conn.execute("DELETE FROM prices")
		conn.execute("DELETE FROM orders")
		conn.execute("DELETE FROM users")

	def _insert_users(self, conn: sqlite3.Connection, users: dict[str, Any]) -> None:
		"""Insert users, orders, and prices."""
		for username, user_data in users.items():
			stored = dict(user_data)
			stored["username"] = username
			orders = stored.pop("orders", [])
			prices = stored.pop("prices", {})
			conn.execute(
				"""
				INSERT INTO users (username, user_json)
				VALUES (?, ?)
				ON CONFLICT(username) DO UPDATE SET user_json = excluded.user_json
				""",
				(username, json.dumps(stored, ensure_ascii=False)),
			)

			for index, order in enumerate(orders):
				order_key = str(order.get("id") or f"{index}")
				conn.execute(
					"INSERT INTO orders (username, order_key, sort_order, order_json) VALUES (?, ?, ?, ?)",
					(username, order_key, index, json.dumps(order, ensure_ascii=False)),
				)

			for isin, price in prices.items():
				conn.execute(
					"INSERT INTO prices (username, isin, price_json) VALUES (?, ?, ?)",
					(username, isin, json.dumps(price, ensure_ascii=False)),
				)

	def _insert_mappings(self, conn: sqlite3.Connection, table: str, mappings: dict[str, dict[str, Any]]) -> None:
		"""Insert ISIN mappings into a mapping table."""
		for isin, mapping in mappings.items():
			conn.execute(
				f"INSERT INTO {table} (isin, mapping_json) VALUES (?, ?)",
				(isin, json.dumps(mapping, ensure_ascii=False)),
			)

	def _rename_users(self, users: dict[str, Any], rename_users: dict[str, str]) -> dict[str, Any]:
		"""Return users with configured username renames applied."""
		result = dict(users)
		for old, new in rename_users.items():
			if old not in result:
				continue
			if new in result and new != old:
				raise ValueError(f"Cannot rename '{old}' to '{new}': target user already exists")
			user_data = dict(result.pop(old))
			user_data["username"] = new
			result[new] = user_data
		return result
