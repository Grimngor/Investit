"""Storage service with atomic writes and file locking for JSON data."""

import json
import os
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import portalocker


class StorageService:
	"""Service for safe atomic JSON file operations with file locking."""

	_RUNTIME_JSON_FILES = {"users.json", "instruments.json", "isin_ticker_mapping.json", "isin_resolution_cache.json", "prices.json"}

	@staticmethod
	def _sidecar_lock_path(file_path: Path) -> Path:
		"""Return the sidecar lock path for a data file."""
		return file_path.with_name(f".{file_path.name}.lock")

	@staticmethod
	def _uses_sqlite_runtime(file_path: Path) -> bool:
		"""Return True when a known runtime JSON file should be served by SQLite."""
		from app.config import settings

		try:
			is_data_dir_file = file_path.resolve().parent == settings.DATA_DIR.resolve()
		except OSError:
			is_data_dir_file = file_path.parent == settings.DATA_DIR
		return settings.PERSISTENCE_BACKEND == "sqlite" and is_data_dir_file and file_path.name in StorageService._RUNTIME_JSON_FILES

	@staticmethod
	def _sqlite_service():
		"""Return a SQLite database service instance."""
		from app.services.database_service import DatabaseService

		return DatabaseService()

	@staticmethod
	def _load_runtime_json(file_path: Path, default: Any = None) -> Any:
		"""Load known runtime data from SQLite using the legacy JSON shape."""
		db = StorageService._sqlite_service()
		if file_path.name == "users.json":
			return db.load_users()
		if file_path.name == "instruments.json":
			return db.load_instruments()
		if file_path.name == "isin_ticker_mapping.json":
			return {"mappings": db.load_isin_mappings()}
		if file_path.name == "isin_resolution_cache.json":
			return {"mappings": db.load_isin_resolution_cache()}
		if file_path.name == "prices.json":
			return default if default is not None else {}
		return default if default is not None else {}

	@staticmethod
	def _save_runtime_json(file_path: Path, data: Any) -> None:
		"""Persist known runtime data to SQLite using the legacy JSON shape."""
		db = StorageService._sqlite_service()
		if file_path.name == "users.json":
			db.save_users(data if isinstance(data, dict) else {})
			return
		if file_path.name == "instruments.json":
			db.save_instruments(data if isinstance(data, list) else [])
			return
		if file_path.name == "isin_ticker_mapping.json":
			mappings = data.get("mappings", {}) if isinstance(data, dict) else {}
			db.save_isin_mappings(mappings)
			return
		if file_path.name == "isin_resolution_cache.json":
			mappings = data.get("mappings", {}) if isinstance(data, dict) else {}
			db.save_isin_resolution_cache(mappings)
			return

	@staticmethod
	@contextmanager
	def _lock_file(file_path: Path, exclusive: bool = True):
		"""
		Context manager for file locking.

		Args:
			file_path: Path to the file to lock
			exclusive: If True, acquire exclusive lock (for writes), else shared lock (for reads)

		Yields:
			File object with appropriate lock
		"""
		mode = "r+b" if exclusive else "rb"
		flags = portalocker.LOCK_EX if exclusive else portalocker.LOCK_SH

		if not file_path.exists():
			file_path.parent.mkdir(parents=True, exist_ok=True)
			file_path.write_text("", encoding="utf-8")

		with open(file_path, mode) as f:
			portalocker.lock(f, flags)
			try:
				yield f
			finally:
				portalocker.unlock(f)

	@classmethod
	def load_json(cls, file_path: Path, default: Any = None) -> Any:
		"""
		Load JSON data from file with shared lock.

		Args:
			file_path: Path to JSON file
			default: Default value if file doesn't exist or is empty

		Returns:
			Parsed JSON data or default value
		"""
		if cls._uses_sqlite_runtime(file_path):
			return cls._load_runtime_json(file_path, default=default)

		try:
			with cls._lock_file(cls._sidecar_lock_path(file_path), exclusive=False):
				if not file_path.exists():
					return default if default is not None else {}
				content = file_path.read_bytes()
				if not content:
					return default if default is not None else {}
				return json.loads(content.decode("utf-8"))
		except (json.JSONDecodeError, ValueError) as e:
			print(f"Error parsing JSON from {file_path}: {e}")
			return default if default is not None else {}

	@classmethod
	def save_json(cls, file_path: Path, data: Any, indent: int = 2) -> None:
		"""
		Save JSON data to file atomically with exclusive lock.

		Uses atomic write pattern:
		1. Write to temporary file
		2. Sync to disk
		3. Rename to target (atomic operation)

		Args:
			file_path: Path to JSON file
			data: Data to serialize as JSON
			indent: JSON indentation level (default: 2)
		"""
		if cls._uses_sqlite_runtime(file_path):
			cls._save_runtime_json(file_path, data)
			return

		with cls._lock_file(cls._sidecar_lock_path(file_path), exclusive=True):
			cls._save_json_unlocked(file_path, data, indent=indent)

	@staticmethod
	def _save_json_unlocked(file_path: Path, data: Any, indent: int = 2) -> None:
		"""Save JSON data atomically; caller must hold the sidecar lock."""
		file_path.parent.mkdir(parents=True, exist_ok=True)

		# Serialize to JSON
		json_content = json.dumps(data, indent=indent, ensure_ascii=False)

		# Write to temporary file in same directory (ensures same filesystem)
		temp_fd, temp_path = tempfile.mkstemp(dir=file_path.parent, prefix=f".{file_path.name}_", suffix=".tmp", text=True)

		try:
			# Write and sync to disk
			with open(temp_fd, "w", encoding="utf-8") as f:
				f.write(json_content)
				f.flush()
				# Force write to disk (fsync)
				os.fsync(f.fileno())

			# Atomic rename (replaces existing file atomically)
			temp_path_obj = Path(temp_path)
			temp_path_obj.replace(file_path)

		except Exception:
			# Clean up temp file on error
			Path(temp_path).unlink(missing_ok=True)
			raise

	@classmethod
	def update_json(cls, file_path: Path, update_fn: Callable[[Any], Any], default: Any = None) -> Any:
		"""
		Update JSON file atomically using update function.

		Acquires exclusive lock, loads current data, applies update function,
		saves result atomically.

		Args:
			file_path: Path to JSON file
			update_fn: Function that takes current data and returns updated data
			default: Default value if file doesn't exist

		Returns:
			Updated data

		Example:
			def add_user(data):
				data['users']['new_user'] = {...}
				return data

			StorageService.update_json(users_file, add_user)
		"""
		if cls._uses_sqlite_runtime(file_path):
			data = cls._load_runtime_json(file_path, default=default)
			updated_data = update_fn(data)
			cls._save_runtime_json(file_path, updated_data)
			return updated_data

		with cls._lock_file(cls._sidecar_lock_path(file_path), exclusive=True):
			if file_path.exists():
				content = file_path.read_bytes()
				data = json.loads(content.decode("utf-8")) if content else (default if default is not None else {})
			else:
				data = default if default is not None else {}

			updated_data = update_fn(data)
			cls._save_json_unlocked(file_path, updated_data)

		return updated_data

	# ===== Instrument Metadata Helpers =====

	def _instruments_file(self) -> Path:
		"""Return path to instruments.json in data directory."""
		from app.config import settings

		return settings.DATA_DIR / "instruments.json"

	def load_instruments(self) -> list[dict[str, Any]]:
		"""Load instruments metadata list."""
		file_path = self._instruments_file()
		return self.load_json(file_path, default=[])

	def save_instruments(self, instruments: list[dict[str, Any]]) -> None:
		"""Persist instruments metadata list atomically."""
		file_path = self._instruments_file()
		self.save_json(file_path, instruments)

	def upsert_instrument(self, isin: str, metadata: dict[str, Any]) -> dict[str, Any]:
		"""Upsert a single instrument's metadata using ISIN key."""
		from app.config import settings

		if settings.PERSISTENCE_BACKEND == "sqlite":
			return self._sqlite_service().upsert_instrument(isin, metadata)

		instruments = self.load_instruments()
		idx = next((i for i, inst in enumerate(instruments) if inst.get("isin") == isin), None)
		if idx is not None:
			# Merge preserving existing keys unless overridden
			instruments[idx].update({k: v for k, v in metadata.items() if v is not None})
			updated = instruments[idx]
		else:
			new_inst = {"isin": isin, **metadata}
			instruments.append(new_inst)
			updated = new_inst
		self.save_instruments(instruments)
		return updated


# Convenience functions for common operations
def load_users() -> dict[str, Any]:
	"""Load users.json file."""
	from app.config import settings

	return StorageService.load_json(settings.DATA_DIR / "users.json", default={})


def save_users(users: dict[str, Any]) -> None:
	"""Save users.json file."""
	from app.config import settings

	StorageService.save_json(settings.DATA_DIR / "users.json", users)


def load_user_data(username: str) -> dict[str, Any] | None:
	"""Load specific user data."""
	users = load_users()
	return users.get(username)


def save_user_data(username: str, user_data: dict[str, Any]) -> None:
	"""Save specific user data atomically."""
	from app.config import settings

	def update(data: dict[str, Any]) -> dict[str, Any]:
		data[username] = user_data
		return data

	StorageService.update_json(settings.DATA_DIR / "users.json", update, default={})


def update_user_data(
	username: str,
	update_fn: Callable[[dict[str, Any]], dict[str, Any]],
	default: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Update one user's data atomically and return the updated user data."""
	from app.config import settings

	updated_user: dict[str, Any] = {}

	def update(users: dict[str, Any]) -> dict[str, Any]:
		nonlocal updated_user
		user_data = users.get(username, default.copy() if default else {})
		updated_user = update_fn(user_data)
		users[username] = updated_user
		return users

	StorageService.update_json(settings.DATA_DIR / "users.json", update, default={})
	return updated_user
