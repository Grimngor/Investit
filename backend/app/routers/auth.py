"""Authentication router."""

import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.models.auth_persistence import get_all_users, save_user_data
from app.models.auth_schemas import AuthUrlResponse, Token, UserRegister
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
	user_matches_email,
)
from app.services.gmail_import_service import GmailImportError, GmailImportService

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)
MIN_GENERATED_USERNAME_LENGTH = 3


def get_google_login_service() -> GmailImportService:
	"""Return a Gmail import service for Google login."""
	return GmailImportService()


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
	email_exists = any(user_matches_email(existing, email) for existing in users.values())
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
		"google": GmailImportService().is_configured() and is_email_allowlist_configured(),
	}


@router.get("/google/auth-url", response_model=AuthUrlResponse)
async def google_auth_url(request: Request, return_path: str = "/dashboard") -> dict[str, str]:
	"""Return a Google OAuth URL for login/register plus Gmail connection."""
	service = GmailImportService()
	try:
		redirect_uri = str(request.url_for("google_oauth_callback"))
		return {"auth_url": service.build_google_login_auth_url(redirect_uri, return_path)}
	except GmailImportError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/google/callback", name="google_oauth_callback")
async def google_oauth_callback(
	request: Request,
	code: str | None = None,
	state: str | None = None,
	error: str | None = None,
	service: GmailImportService = Depends(get_google_login_service),
) -> RedirectResponse:
	"""Handle Google OAuth login/register and store the Gmail connection."""
	return_path = "/dashboard"
	params: dict[str, str] = {}
	try:
		if error:
			raise GmailImportError(error)
		if not code or not state:
			raise GmailImportError("Missing Google OAuth callback parameters.")
		state_payload = service.parse_login_state(state)
		return_path = str(state_payload.get("return_path") or "/dashboard")
		token = await complete_google_login(code, str(request.url_for("google_oauth_callback")), service)
		params["google"] = "connected"
		params["access_token"] = token["access_token"]
		params["token_type"] = token["token_type"]
	except GmailImportError as exc:
		params["google"] = "error"
		params["message"] = str(exc)

	return RedirectResponse(f"{return_path}#{urlencode(params)}")


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


async def complete_google_login(code: str, redirect_uri: str, service: GmailImportService) -> dict[str, str]:
	"""Complete Google login/register and return an InvestIt token."""
	token_payload = await service.exchange_code(code, service.effective_google_login_redirect_uri(redirect_uri))
	profile = await service.userinfo(str(token_payload.get("access_token", "")))
	email = str(profile.get("email", "")).strip()
	if not email:
		raise GmailImportError("Google did not return an email address.")
	if not bool(profile.get("email_verified", False)):
		raise GmailImportError("Google email address is not verified.")
	if not is_trusted_proxy_email_allowed(email):
		raise GmailImportError("Google email is not allowed.")

	user = find_user_by_trusted_proxy_email(email)
	if not user:
		user = create_google_user(email, profile)
	if user.disabled:
		raise GmailImportError("Inactive user.")

	refresh_token = token_payload.get("refresh_token")
	if refresh_token:
		now = service.now_iso()
		service.save_connection(
			user.username,
			{
				"email": email,
				"scope": token_payload.get("scope", service.LOGIN_SCOPE),
				"encrypted_refresh_token": service.encrypt_token(str(refresh_token)),
				"connected_at": now,
				"updated_at": now,
			},
		)
	elif not service.get_connection(user.username):
		raise GmailImportError("Google did not return a refresh token. Reconnect and approve Gmail access.")

	access_token = create_user_access_token(user)
	return {"access_token": access_token, "token_type": "bearer"}


def create_google_user(email: str, profile: dict) -> User:
	"""Create an allowlisted app user from a Google profile."""
	users = get_all_users()
	username = build_username_from_email(email, users)
	user_data = {
		"username": username,
		"email": email,
		"hashed_password": get_password_hash(secrets.token_urlsafe(48)),
		"disabled": False,
		"holdings": [],
	}
	name = str(profile.get("name", "")).strip()
	if name:
		user_data["full_name"] = name
	save_user_data(username, user_data)
	return User(username=username, email=email, full_name=user_data.get("full_name"), disabled=False)
