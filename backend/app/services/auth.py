"""Authentication service."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

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
		user_data = next((data for data in users.values() if str(data.get("email", "")).casefold() == login_email), None)

	if not user_data:
		return None

	if not verify_password(password, user_data.get("hashed_password", "")):
		return None

	return User(
		username=user_data["username"],
		email=user_data.get("email", ""),
		full_name=user_data.get("full_name"),
		disabled=user_data.get("disabled", False),
	)


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

	user = User(
		username=user_data["username"],
		email=user_data.get("email", ""),
		full_name=user_data.get("full_name"),
		disabled=user_data.get("disabled", False),
	)

	if user.disabled:
		raise HTTPException(status_code=400, detail="Inactive user")

	return user
