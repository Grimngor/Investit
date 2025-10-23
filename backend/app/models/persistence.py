"""Data persistence operations."""

import json
from pathlib import Path
from typing import Any

from app.config import settings


def get_users_file_path() -> Path:
	"""Get the path to the users.json file."""
	return settings.DATA_DIR / "users.json"


def load_user_data(username: str) -> dict[str, Any]:
	"""Load a specific user's data."""
	users = get_all_users()
	return users.get(username, {})


def get_all_users() -> dict[str, dict[str, Any]]:
	"""Load all users data from JSON file."""
	users_file = get_users_file_path()

	if not users_file.exists():
		return {}

	try:
		with open(users_file, encoding="utf-8") as f:
			return json.load(f)
	except Exception as e:
		print(f"Error loading users data: {e}")
		return {}


def save_user_data(username: str, user_data: dict[str, Any]) -> None:
	"""Save or update a user's data."""
	users = get_all_users()

	# Merge with existing data
	if username in users:
		users[username].update(user_data)
	else:
		users[username] = user_data

	# Ensure data directory exists
	settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

	# Save to file
	users_file = get_users_file_path()
	with open(users_file, "w", encoding="utf-8") as f:
		json.dump(users, f, indent=2, ensure_ascii=False)
