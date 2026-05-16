"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models.persistence import get_all_users, load_user_data, save_user_data
from app.services.auth import get_password_hash
from app.services.storage_service import StorageService

client = TestClient(app)


@pytest.fixture
def test_user():
	"""Create a test user for authentication tests."""
	username = "test_auth_user"
	password = "testpass123"
	user_data = {"username": username, "hashed_password": get_password_hash(password), "is_active": True, "holdings": []}
	save_user_data(username, user_data)
	yield {"username": username, "password": password}
	# Cleanup would go here if we implement user deletion


def test_register_new_user():
	"""Test user registration with new credentials."""
	# Clean up the user first if it exists
	username = "new_test_user"
	user_data = load_user_data(username)
	if user_data:
		# Delete the user from users.json
		users = get_all_users()
		if username in users:
			del users[username]
			StorageService.save_json(settings.DATA_DIR / "users.json", users)

	response = client.post(
		"/api/auth/register", json={"username": username, "email": "newuser@test.com", "password": "password123", "full_name": "Test User"}
	)
	assert response.status_code == 201
	data = response.json()
	assert data["username"] == username
	assert data["message"] == "User registered successfully"
	created = load_user_data(username)
	assert created["email"] == "newuser@test.com"
	assert created["full_name"] == "Test User"


def test_register_username_and_full_name_are_optional():
	"""Test user registration can derive username from required email."""
	response = client.post("/api/auth/register", json={"email": "optional-user@test.com", "password": "password123"})

	assert response.status_code == 201
	created = load_user_data("optional-user")
	assert created["email"] == "optional-user@test.com"
	assert "full_name" not in created


def test_register_requires_email():
	"""Test user registration requires an email address."""
	response = client.post("/api/auth/register", json={"username": "missing_email", "password": "password123"})

	assert response.status_code == 422


def test_register_duplicate_email_fails_case_insensitive():
	"""Test duplicate emails are rejected case-insensitively when provided."""
	client.post(
		"/api/auth/register",
		json={"username": "email_owner", "email": "Owner@Test.com", "password": "password123"},
	)

	response = client.post(
		"/api/auth/register",
		json={"username": "email_duplicate", "email": "owner@test.com", "password": "password123"},
	)

	assert response.status_code == 400
	assert response.json()["detail"] == "Email already registered"


def test_register_requires_allowlisted_email_when_allowlist_configured(monkeypatch):
	"""Test registration rejects emails outside the configured allowlist."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "allowed@example.com")

	response = client.post(
		"/api/auth/register",
		json={"username": "blocked_email", "email": "blocked@example.com", "password": "password123"},
	)

	assert response.status_code == 403
	assert response.json()["detail"] == "Email is not allowed"


def test_register_accepts_allowlisted_email_when_allowlist_configured(monkeypatch):
	"""Test registration accepts emails inside the configured allowlist."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", '["allowed@example.com"]')

	response = client.post(
		"/api/auth/register",
		json={"username": "allowed_email", "email": "allowed@example.com", "password": "password123"},
	)

	assert response.status_code == 201


def test_register_duplicate_user(test_user):
	"""Test that registering with existing username fails."""
	response = client.post(
		"/api/auth/register",
		json={
			"username": test_user["username"],
			"email": "another@test.com",
			"password": "anypassword",
			"full_name": "Another User",
		},
	)
	assert response.status_code == 400


def test_login_success(test_user):
	"""Test successful login with correct credentials."""
	response = client.post("/api/auth/login", data={"username": test_user["username"], "password": test_user["password"]})
	assert response.status_code == 200
	data = response.json()
	assert "access_token" in data
	assert data["token_type"] == "bearer"


def test_login_with_email(test_user):
	"""Test successful login with email when one is stored."""
	users = get_all_users()
	users[test_user["username"]]["email"] = "auth-user@example.com"
	StorageService.save_json(settings.DATA_DIR / "users.json", users)

	response = client.post("/api/auth/login", data={"username": "AUTH-USER@example.com", "password": test_user["password"]})

	assert response.status_code == 200
	assert "access_token" in response.json()


def test_login_requires_allowlisted_user_when_allowlist_configured(monkeypatch):
	"""Test password login rejects users outside the configured email allowlist."""
	username = "blocked_login"
	save_user_data(
		username,
		{
			"username": username,
			"email": "blocked-login@example.com",
			"hashed_password": get_password_hash("password123"),
			"disabled": False,
			"holdings": [],
		},
	)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "allowed@example.com")

	response = client.post("/api/auth/login", data={"username": username, "password": "password123"})

	assert response.status_code == 403
	assert response.json()["detail"] == "Email is not allowed"


def test_login_accepts_allowlisted_user_when_allowlist_configured(monkeypatch):
	"""Test password login accepts users inside the configured email allowlist."""
	username = "allowed_login"
	email = "allowed-login@example.com"
	save_user_data(
		username,
		{
			"username": username,
			"email": email,
			"hashed_password": get_password_hash("password123"),
			"disabled": False,
			"holdings": [],
		},
	)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", email)

	response = client.post("/api/auth/login", data={"username": username, "password": "password123"})

	assert response.status_code == 200
	assert "access_token" in response.json()


def test_auth_modes_default_to_password_only():
	"""Test default authentication modes keep trusted proxy auth disabled."""
	response = client.get("/api/auth/modes")

	assert response.status_code == 200
	assert response.json() == {"password": True, "trusted_proxy": False}


def test_trusted_proxy_login_returns_404_when_disabled():
	"""Test trusted proxy login is unavailable unless explicitly enabled."""
	response = client.post("/api/auth/trusted-proxy/login", headers={"Tailscale-User-Login": "owner@example.com"})

	assert response.status_code == 404


def test_trusted_proxy_login_requires_identity_header(monkeypatch):
	"""Test trusted proxy login rejects requests without identity headers."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ENABLED", True)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "owner@example.com")

	response = client.post("/api/auth/trusted-proxy/login")

	assert response.status_code == 403
	assert response.json()["detail"] == "Missing trusted proxy identity"


def test_trusted_proxy_login_requires_allowlisted_email(monkeypatch):
	"""Test trusted proxy login rejects non-allowlisted identities."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ENABLED", True)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "owner@example.com")

	response = client.post("/api/auth/trusted-proxy/login", headers={"Tailscale-User-Login": "intruder@example.com"})

	assert response.status_code == 403
	assert response.json()["detail"] == "Trusted proxy identity is not allowed"


def test_trusted_proxy_login_requires_linked_user(monkeypatch):
	"""Test trusted proxy login rejects allowlisted identities without an app user."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ENABLED", True)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "owner@example.com")

	response = client.post("/api/auth/trusted-proxy/login", headers={"Tailscale-User-Login": "owner@example.com"})

	assert response.status_code == 403
	assert response.json()["detail"] == "Trusted proxy identity is not linked to an app user"


def test_trusted_proxy_login_success_for_linked_allowlisted_user(monkeypatch):
	"""Test trusted proxy login returns a normal bearer token for a linked user."""
	username = "tailscale_user"
	email = "owner@example.com"
	save_user_data(
		username,
		{
			"username": username,
			"email": email,
			"hashed_password": get_password_hash("unused-password"),
			"disabled": False,
			"holdings": [],
		},
	)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ENABLED", True)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", email.upper())

	response = client.post("/api/auth/trusted-proxy/login", headers={"Tailscale-User-Login": email})

	assert response.status_code == 200
	token = response.json()["access_token"]
	assert response.json()["token_type"] == "bearer"

	me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
	assert me.status_code == 200
	assert me.json()["username"] == username


def test_login_wrong_password(test_user):
	"""Test login fails with wrong password."""
	response = client.post("/api/auth/login", data={"username": test_user["username"], "password": "wrongpassword"})
	assert response.status_code == 401


def test_login_nonexistent_user():
	"""Test login fails for non-existent user."""
	response = client.post("/api/auth/login", data={"username": "nonexistent", "password": "anypassword"})
	assert response.status_code == 401


def test_get_current_user_unauthorized():
	"""Test that accessing protected endpoint without token fails."""
	response = client.get("/api/portfolio/")
	assert response.status_code == 401
