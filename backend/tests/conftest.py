"""Pytest configuration: path setup, shared helpers, and warning filters."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend path is on sys.path for 'app' package imports when running pytest directly.
BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
	sys.path.insert(0, str(BACKEND))

# Silence deprecation warning from python-jose using utcnow (third-party, cannot be changed).
warnings.filterwarnings(
	"ignore",
	category=DeprecationWarning,
	message=r".*datetime\.utcnow\(\) is deprecated.*",
)


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Run tests against temporary data files instead of project data."""
	from app.config import settings
	from app.services.background_jobs import background_jobs
	from app.services.isin_mapper import get_isin_mapper

	data_dir = tmp_path / "data"
	data_dir.mkdir()
	(data_dir / "users.json").write_text("{}", encoding="utf-8")
	(data_dir / "instruments.json").write_text("[]", encoding="utf-8")
	monkeypatch.setattr(settings, "DATA_DIR", data_dir)
	background_jobs.clear()
	get_isin_mapper.cache_clear()


def make_auth_headers(client: TestClient, username: str, password: str = "testpass123", email: str | None = None) -> dict[str, str]:
	"""Register (if needed) and log in a test user, returning auth headers.

	This helper is intentionally a plain function (not a fixture) so each
	test file can call it with its own username, avoiding shared state.
	"""
	if email is None:
		email = f"{username}@example.com"

	# Try to register — it's fine if the user already exists (409).
	client.post("/api/auth/register", json={"username": username, "email": email, "password": password})

	response = client.post("/api/auth/login", data={"username": username, "password": password})
	assert response.status_code == 200, f"Login failed for '{username}': {response.json()}"

	token = response.json()["access_token"]
	return {"Authorization": f"Bearer {token}"}
