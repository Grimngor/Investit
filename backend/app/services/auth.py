"""Authentication service."""

import json
from datetime import UTC, datetime, timedelta
from email.header import decode_header
from types import SimpleNamespace
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.models.auth_persistence import get_all_users
from app.models.user import User

# Passlib 1.7 reads bcrypt.__about__.__version__, which bcrypt 4.x no longer exposes.
if not hasattr(bcrypt, "__about__"):
	bcrypt.__about__ = SimpleNamespace(__version__=getattr(bcrypt, "__version__", "unknown"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""Verify a password against its hash."""
	return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
	"""Hash a password."""
	return pwd_context.hash(password)


def authenticate_user(username_or_email: str, password: str) -> User | None:
	"""Authenticate a user by username or email and password."""
	users = get_all_users()
	user_data = users.get(username_or_email)
	if not user_data:
		login_email = username_or_email.casefold()
		user_data = next((data for data in users.values() if user_matches_email(data, login_email)), None)

	if not user_data:
		return None

	if not verify_password(password, user_data.get("hashed_password", "")):
		return None

	return build_user(user_data)


def decode_trusted_proxy_header(value: str) -> str:
	"""Decode a trusted proxy header value that may use RFC 2047 encoding."""
	decoded_parts = decode_header(value)
	return "".join(part.decode(encoding or "utf-8") if isinstance(part, bytes) else part for part, encoding in decoded_parts).strip()


def get_trusted_proxy_allowed_emails() -> set[str]:
	"""Return configured email allowlist entries as casefolded strings."""
	raw_value = settings.TRUSTED_PROXY_AUTH_ALLOWED_EMAILS.strip()
	if not raw_value:
		return set()

	try:
		parsed = json.loads(raw_value)
	except json.JSONDecodeError:
		parsed = None

	if isinstance(parsed, list):
		return {str(email).strip().casefold() for email in parsed if str(email).strip()}

	return {email.strip().casefold() for email in raw_value.split(",") if email.strip()}


def is_email_allowlist_configured() -> bool:
	"""Return whether app login and registration should be restricted by email."""
	return bool(get_trusted_proxy_allowed_emails())


def is_trusted_proxy_email_allowed(email: str) -> bool:
	"""Return whether a trusted proxy email is explicitly allowlisted."""
	return email.casefold() in get_trusted_proxy_allowed_emails()


def user_email_values(user_data: dict[str, Any]) -> set[str]:
	"""Return all login email values stored for a user."""
	values = {str(user_data.get("email", "")).strip().casefold()}
	values.update(str(email).strip().casefold() for email in user_data.get("email_aliases", []) if str(email).strip())
	return {value for value in values if value}


def user_matches_email(user_data: dict[str, Any], email: str) -> bool:
	"""Return whether a stored user matches an email or email alias."""
	return email.casefold() in user_email_values(user_data)


def is_user_allowed_by_email_allowlist(user: User) -> bool:
	"""Return whether a user matches the configured email allowlist."""
	allowed = get_trusted_proxy_allowed_emails()
	if not allowed:
		return True
	emails = {user.email.casefold(), *(email.casefold() for email in user.email_aliases)}
	return bool(emails & allowed) or user.username.casefold() in allowed


def build_user(user_data: dict[str, Any]) -> User:
	"""Build a public user model from persisted user data."""
	return User(
		username=user_data["username"],
		email=user_data.get("email", ""),
		email_aliases=user_data.get("email_aliases", []),
		full_name=user_data.get("full_name"),
		disabled=user_data.get("disabled", False),
	)


def find_user_by_trusted_proxy_email(email: str) -> User | None:
	"""Find an existing app user linked to a trusted proxy email or username."""
	login_email = email.casefold()
	users = get_all_users()

	for username, user_data in users.items():
		if username.casefold() == login_email or user_matches_email(user_data, login_email):
			return build_user(user_data)

	return None


def create_user_access_token(user: User) -> str:
	"""Create a standard access token for an authenticated user."""
	access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
	return create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
	"""Create a JWT access token."""
	to_encode = data.copy()
	expire = datetime.now(UTC) + (expires_delta if expires_delta else timedelta(minutes=15))
	to_encode.update({"exp": expire})
	return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
	"""Get the current authenticated user from JWT token."""
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)

	try:
		payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
		username: str = payload.get("sub")
		if username is None:
			raise credentials_exception
	except JWTError as exc:
		raise credentials_exception from exc

	users = get_all_users()
	user_data = users.get(username)

	if user_data is None:
		raise credentials_exception

	user = build_user(user_data)

	if user.disabled:
		raise HTTPException(status_code=400, detail="Inactive user")

	return user
