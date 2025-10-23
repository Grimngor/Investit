"""Authentication service."""

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.models.auth_persistence import get_all_users
from app.models.user import User

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


def authenticate_user(username: str, password: str) -> User | None:
	"""Authenticate a user by username and password."""
	users = get_all_users()
	user_data = users.get(username)

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
	expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
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
