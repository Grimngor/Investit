"""Pydantic schemas for authentication."""

from pydantic import BaseModel, Field


class Token(BaseModel):
	"""Token response schema."""

	access_token: str
	token_type: str


class TokenData(BaseModel):
	"""Token payload data."""

	username: str | None = None


class UserLogin(BaseModel):
	"""User login request schema."""

	username: str = Field(..., min_length=3, max_length=50)
	password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
	"""User registration request schema."""

	email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
	password: str = Field(..., min_length=6)
	username: str | None = Field(default=None, min_length=3, max_length=50)
	full_name: str | None = None
