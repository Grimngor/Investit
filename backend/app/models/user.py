"""User model."""

from pydantic import BaseModel, Field
from typing import Optional


class User(BaseModel):
    """User model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str
    full_name: Optional[str] = None
    disabled: bool = False
