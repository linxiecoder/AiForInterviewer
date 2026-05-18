"""Auth domain ports."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.auth.entities import AuthSession, CurrentActor, IssuedAuthSession, UserCredentials


class PasswordHasher(Protocol):
    def hash_password(self, password: str) -> str: ...

    def verify_password(self, password: str, password_hash: str) -> bool: ...


class UserCredentialStore(Protocol):
    def get_by_identifier(self, identifier: str) -> UserCredentials | None: ...

    def get_by_user_id(self, user_id: str) -> UserCredentials | None: ...


class SessionStore(Protocol):
    def issue_session(self, actor: CurrentActor, expires_at: datetime) -> IssuedAuthSession: ...

    def get_session(self, raw_token: str, now: datetime) -> AuthSession | None: ...

    def revoke_session(self, raw_token: str, now: datetime) -> bool: ...
