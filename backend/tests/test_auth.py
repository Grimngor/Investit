"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models.persistence import get_all_users, load_user_data, save_user_data
from app.routers.auth import complete_google_login
from app.services.auth import get_password_hash
from app.services.gmail_import_service import GmailImportError, GmailImportService
from app.services.storage_service import StorageService

client = TestClient(app)


class FakeGoogleLoginService(GmailImportService):
	"""Google login service with network calls replaced by fixtures."""

	def __init__(self, email: str = "google-user@example.com", refresh_token: str | None = "refresh-token") -> None:
		"""Initialize the fake Google service."""
		super().__init__()
		self.email = email
		self.refresh_token = refresh_token

	async def exchange_code(self, code: str, redirect_uri: str) -> dict:
		"""Return fake OAuth tokens."""
		payload = {"access_token": "google-access-token", "scope": self.LOGIN_SCOPE}
		if self.refresh_token:
			payload["refresh_token"] = self.refresh_token
		return payload

	async def userinfo(self, access_token: str) -> dict:
		"""Return fake Google profile data."""
		return {"email": self.email, "email_verified": True, "name": "Google User"}


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


def test_login_with_email_alias(test_user):
	"""Test successful login with an email alias when one is stored."""
	users = get_all_users()
	users[test_user["username"]]["email"] = "auth-user@example.com"
	users[test_user["username"]]["email_aliases"] = ["alias@example.com"]
	StorageService.save_json(settings.DATA_DIR / "users.json", users)

	response = client.post("/api/auth/login", data={"username": "ALIAS@example.com", "password": test_user["password"]})

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


def test_login_accepts_allowlisted_alias_when_allowlist_configured(monkeypatch):
	"""Test password login accepts users whose alias is allowlisted."""
	username = "allowed_alias_login"
	save_user_data(
		username,
		{
			"username": username,
			"email": "primary@example.com",
			"email_aliases": ["allowed-alias@example.com"],
			"hashed_password": get_password_hash("password123"),
			"disabled": False,
			"holdings": [],
		},
	)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "allowed-alias@example.com")

	response = client.post("/api/auth/login", data={"username": username, "password": "password123"})

	assert response.status_code == 200
	assert "access_token" in response.json()


def test_auth_modes_default_to_password_only():
	"""Test default authentication modes keep trusted proxy auth disabled."""
	response = client.get("/api/auth/modes")

	assert response.status_code == 200
	assert response.json() == {"password": True, "trusted_proxy": False, "google": False}


def test_auth_modes_enable_google_when_oauth_and_allowlist_configured(monkeypatch):
	"""Test Google auth mode appears only when OAuth and allowlist are configured."""
	monkeypatch.setattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "client-id")
	monkeypatch.setattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "owner@example.com")

	response = client.get("/api/auth/modes")

	assert response.status_code == 200
	assert response.json()["google"] is True


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


def test_trusted_proxy_login_success_for_linked_alias(monkeypatch):
	"""Test trusted proxy login can match a stored email alias."""
	username = "tailscale_alias_user"
	email = "owner@example.com"
	alias = "owner.alias@example.com"
	save_user_data(
		username,
		{
			"username": username,
			"email": email,
			"email_aliases": [alias],
			"hashed_password": get_password_hash("unused-password"),
			"disabled": False,
			"holdings": [],
		},
	)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ENABLED", True)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", alias)

	response = client.post("/api/auth/trusted-proxy/login", headers={"Tailscale-User-Login": alias})

	assert response.status_code == 200
	token = response.json()["access_token"]

	me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
	assert me.status_code == 200
	assert me.json()["username"] == username


@pytest.mark.asyncio
async def test_google_login_creates_allowlisted_user_and_gmail_connection(monkeypatch):
	"""Test Google login can auto-register allowlisted users and save Gmail connection."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "google-user@example.com")
	service = FakeGoogleLoginService()

	token = await complete_google_login("code", "http://testserver/api/auth/google/callback", service)

	assert token["token_type"] == "bearer"
	created = load_user_data("google-user")
	assert created["email"] == "google-user@example.com"
	connection = service.get_connection("google-user")
	assert connection is not None
	assert connection["email"] == "google-user@example.com"


@pytest.mark.asyncio
async def test_google_login_links_email_alias_to_existing_user(monkeypatch):
	"""Test Google login maps an alias to an existing account instead of creating another user."""
	save_user_data(
		"existing_google_owner",
		{
			"username": "existing_google_owner",
			"email": "primary@example.com",
			"email_aliases": ["google-user@example.com"],
			"hashed_password": get_password_hash("password123"),
			"disabled": False,
			"holdings": [],
		},
	)
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "google-user@example.com")
	service = FakeGoogleLoginService()

	token = await complete_google_login("code", "http://testserver/api/auth/google/callback", service)

	me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
	assert me.status_code == 200
	assert me.json()["username"] == "existing_google_owner"
	assert load_user_data("google-user") == {}
	assert service.get_connection("existing_google_owner") is not None


@pytest.mark.asyncio
async def test_google_login_rejects_non_allowlisted_email(monkeypatch):
	"""Test Google login rejects emails outside the allowlist."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "owner@example.com")

	with pytest.raises(GmailImportError, match="Google email is not allowed"):
		await complete_google_login("code", "http://testserver/api/auth/google/callback", FakeGoogleLoginService())


@pytest.mark.asyncio
async def test_google_login_without_refresh_token_still_logs_in(monkeypatch):
	"""Test Google login succeeds when Google omits a repeat-login refresh token."""
	monkeypatch.setattr(settings, "TRUSTED_PROXY_AUTH_ALLOWED_EMAILS", "google-user@example.com")
	service = FakeGoogleLoginService(refresh_token=None)

	token = await complete_google_login("code", "http://testserver/api/auth/google/callback", service)

	assert token["token_type"] == "bearer"
	assert load_user_data("google-user")["email"] == "google-user@example.com"
	connection = service.get_connection("google-user")
	assert connection is not None
	assert connection["email"] == "google-user@example.com"
	assert "encrypted_access_token" in connection


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
