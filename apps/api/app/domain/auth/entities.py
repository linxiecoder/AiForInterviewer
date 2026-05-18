"""Auth domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserAccount:
    user_id: str
    owner_id: str
    email_normalized: str
    username: str
    display_name: str
    status: str
    roles: tuple[str, ...]

    def is_active(self) -> bool:
        return self.status == "active"


@dataclass(frozen=True)
class UserCredentials:
    account: UserAccount
    password_hash: str


@dataclass(frozen=True)
class CurrentActor:
    actor_id: str
    owner_id: str
    roles: tuple[str, ...]
    email_normalized: str
    display_name: str


@dataclass(frozen=True)
class AuthSession:
    session_digest: str
    actor_id: str
    owner_id: str
    roles: tuple[str, ...]
    email_normalized: str
    display_name: str
    expires_at: datetime
    revoked_at: datetime | None = None

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now

    def to_actor(self) -> CurrentActor:
        return CurrentActor(
            actor_id=self.actor_id,
            owner_id=self.owner_id,
            roles=self.roles,
            email_normalized=self.email_normalized,
            display_name=self.display_name,
        )


@dataclass(frozen=True)
class IssuedAuthSession:
    raw_token: str
    session: AuthSession
