"""User data persistence compatibility helpers."""

from pathlib import Path
from typing import Any

from app.config import settings
from app.services.storage_service import StorageService, load_users, update_user_data


def get_users_file_path() -> Path:
	"""Get the path to the users.json file."""
	return settings.DATA_DIR / "users.json"


def load_user_data(username: str) -> dict[str, Any]:
	"""Load a specific user's data."""
	return get_all_users().get(username, {})


def get_all_users() -> dict[str, dict[str, Any]]:
	"""Load all users data from JSON file."""
	return load_users()


def save_user_data(username: str, user_data: dict[str, Any]) -> None:
	"""Save or update a user's data."""

	def merge(existing: dict[str, Any]) -> dict[str, Any]:
		existing.update(user_data)
		return existing

	update_user_data(username, merge)


def delete_user_data(username: str) -> bool:
	"""Delete a user's data."""
	deleted = False

	def update(users: dict[str, Any]) -> dict[str, Any]:
		nonlocal deleted
		if username in users:
			del users[username]
			deleted = True
		return users

	StorageService.update_json(get_users_file_path(), update, default={})
	return deleted
