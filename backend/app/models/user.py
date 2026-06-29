"""User model."""

from pydantic import BaseModel, Field


class User(BaseModel):
	"""User model."""

	username: str = Field(..., min_length=3, max_length=50)
	email: str
	email_aliases: list[str] = Field(default_factory=list)
	full_name: str | None = None
	disabled: bool = False
