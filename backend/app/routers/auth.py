"""Authentication router."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.models.auth_persistence import get_all_users, save_user_data
from app.models.auth_schemas import Token, UserRegister
from app.models.user import User
from app.services.auth import authenticate_user, create_access_token, get_current_user, get_password_hash

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
	"""Register a new user."""
	users = get_all_users()

	# Check if username exists
	if user_data.username in users:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Username already registered",
		)

	# Create new user
	hashed_password = get_password_hash(user_data.password)
	new_user = {
		"username": user_data.username,
		"hashed_password": hashed_password,
		"disabled": False,
		"holdings": [],
	}

	save_user_data(user_data.username, new_user)

	return {"message": "User registered successfully", "username": user_data.username}


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

	access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
	access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

	return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
	"""Get current user information."""
	return current_user
