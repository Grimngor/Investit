"""Create a local development user."""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.models.persistence import load_user_data, save_user_data  # noqa: E402
from app.services.auth import get_password_hash  # noqa: E402


def create_test_user(username: str, password: str, email: str | None = None, full_name: str | None = None) -> bool:
	"""Create a local development user with the given credentials."""
	if load_user_data(username):
		print(f"[SKIP] User '{username}' already exists")
		return False

	user_data = {
		"username": username,
		"hashed_password": get_password_hash(password),
		"disabled": False,
		"holdings": [],
		"orders": [],
	}
	if email:
		user_data["email"] = email
	if full_name:
		user_data["full_name"] = full_name

	save_user_data(username, user_data)
	print(f"[OK] Created user '{username}'")
	return True


def main() -> None:
	"""Run the local user creation script."""
	parser = argparse.ArgumentParser(description="Create a local development user")
	parser.add_argument("username", nargs="?", default="test")
	parser.add_argument("password", nargs="?", default="1234")
	parser.add_argument("--email")
	parser.add_argument("--full-name")
	args = parser.parse_args()
	create_test_user(args.username, args.password, email=args.email, full_name=args.full_name)


if __name__ == "__main__":
	main()
