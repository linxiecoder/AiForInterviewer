"""Auth API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=4096)


class CurrentUserResponse(BaseModel):
    user_id: str
    owner_id: str
    email: str
    username: str
    display_name: str
    roles: list[str]
    session_expires_at: datetime | None = None


class LogoutResponse(BaseModel):
    logged_out: bool
