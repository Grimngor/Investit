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


def test_register_email_and_full_name_are_optional():
	"""Test user registration does not require email or full name."""
	response = client.post("/api/auth/register", json={"username": "optional_user", "password": "password123"})

	assert response.status_code == 201
	created = load_user_data("optional_user")
	assert "email" not in created
	assert "full_name" not in created


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
