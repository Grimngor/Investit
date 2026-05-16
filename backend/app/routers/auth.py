"""Authentication router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.models.auth_persistence import get_all_users, save_user_data
from app.models.auth_schemas import Token, UserRegister
from app.models.user import User
from app.services.auth import (
	authenticate_user,
	create_user_access_token,
	decode_trusted_proxy_header,
	find_user_by_trusted_proxy_email,
	get_current_user,
	get_password_hash,
	is_email_allowlist_configured,
	is_trusted_proxy_email_allowed,
	is_user_allowed_by_email_allowlist,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)
MIN_GENERATED_USERNAME_LENGTH = 3


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
	"""Register a new user."""
	logger.info(f"Registration attempt - Username: {user_data.username}, Email: {user_data.email}")
	users = get_all_users()
	username = user_data.username or build_username_from_email(user_data.email, users)

	# Check if username exists
	if username in users:
		logger.warning(f"Registration failed - Username already exists: {username}")
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Username already registered",
		)

	if is_email_allowlist_configured() and not is_trusted_proxy_email_allowed(user_data.email):
		logger.warning(f"Registration failed - Email is not allowlisted: {user_data.email}")
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Email is not allowed",
		)

	email = user_data.email.casefold()
	email_exists = any(str(existing.get("email", "")).casefold() == email for existing in users.values())
	if email_exists:
		logger.warning(f"Registration failed - Email already exists: {user_data.email}")
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Email already registered",
		)

	# Create new user
	hashed_password = get_password_hash(user_data.password)
	new_user = {
		"username": username,
		"email": user_data.email,
		"hashed_password": hashed_password,
		"disabled": False,
		"holdings": [],
	}
	if user_data.full_name:
		new_user["full_name"] = user_data.full_name

	save_user_data(username, new_user)

	return {"message": "User registered successfully", "username": username}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
	"""Login and receive access token."""
	user = authenticate_user(form_data.username, form_data.password)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"},
		)
	if not is_user_allowed_by_email_allowlist(user):
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Email is not allowed",
		)

	access_token = create_user_access_token(user)

	return {"access_token": access_token, "token_type": "bearer"}


@router.get("/modes")
async def auth_modes() -> dict[str, bool]:
	"""Return the authentication modes available to the frontend."""
	return {
		"password": True,
		"trusted_proxy": settings.TRUSTED_PROXY_AUTH_ENABLED,
	}


@router.post("/trusted-proxy/login", response_model=Token)
async def trusted_proxy_login(request: Request) -> dict[str, str]:
	"""Login using trusted identity headers from a private reverse proxy."""
	if not settings.TRUSTED_PROXY_AUTH_ENABLED:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trusted proxy authentication is disabled")

	raw_email = request.headers.get(settings.TRUSTED_PROXY_AUTH_HEADER_EMAIL)
	if not raw_email:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing trusted proxy identity")

	email = decode_trusted_proxy_header(raw_email)
	raw_name = request.headers.get(settings.TRUSTED_PROXY_AUTH_HEADER_NAME)
	display_name = decode_trusted_proxy_header(raw_name) if raw_name else ""
	if not email or not is_trusted_proxy_email_allowed(email):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trusted proxy identity is not allowed")

	user = find_user_by_trusted_proxy_email(email)
	if not user:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trusted proxy identity is not linked to an app user")
	if user.disabled:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

	logger.info("Trusted proxy login accepted - Email: %s, Name: %s, Username: %s", email, display_name, user.username)
	access_token = create_user_access_token(user)
	return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
	"""Get current user information."""
	return current_user


def build_username_from_email(email: str, users: dict[str, dict]) -> str:
	"""Build a stable username from an email address when one is not provided."""
	base = email.split("@", 1)[0].strip()[:50] or "user"
	if len(base) < MIN_GENERATED_USERNAME_LENGTH:
		base = f"{base}user"[:50]
	username = base
	suffix = 2
	while username in users:
		suffix_text = f"-{suffix}"
		username = f"{base[: 50 - len(suffix_text)]}{suffix_text}"
		suffix += 1
	return username
