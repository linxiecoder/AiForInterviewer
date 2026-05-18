"""Auth commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginCommand:
    identifier: str
    password: str


@dataclass(frozen=True)
class LogoutCommand:
    session_token: str
