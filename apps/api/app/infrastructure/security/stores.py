"""In-memory auth stores for F5 foundation baseline."""

from __future__ import annotations

from base64 import urlsafe_b64encode
from dataclasses import replace
from datetime import datetime
from hashlib import sha256
import secrets

from app.domain.auth.entities import AuthSession, CurrentActor, IssuedAuthSession, UserAccount, UserCredentials


class InMemoryUserStore:
    def __init__(self) -> None:
        self._by_identifier: dict[str, UserCredentials] = {}
        self._by_user_id: dict[str, UserCredentials] = {}

    def add_user(
        self,
        *,
        user_id: str,
        email: str,
        username: str,
        display_name: str,
        password_hash: str,
        roles: tuple[str, ...] = ("user",),
        status: str = "active",
    ) -> None:
        account = UserAccount(
            user_id=user_id,
            owner_id=user_id,
            email_normalized=email.strip().lower(),
            username=username.strip().lower(),
            display_name=display_name,
            status=status,
            roles=roles,
        )
        credentials = UserCredentials(account=account, password_hash=password_hash)
        self._by_user_id[user_id] = credentials
        self._by_identifier[account.email_normalized] = credentials
        self._by_identifier[account.username] = credentials

    def get_by_identifier(self, identifier: str) -> UserCredentials | None:
        return self._by_identifier.get(identifier.strip().lower())

    def get_by_user_id(self, user_id: str) -> UserCredentials | None:
        return self._by_user_id.get(user_id)


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions_by_digest: dict[str, AuthSession] = {}

    def issue_session(self, actor: CurrentActor, expires_at: datetime) -> IssuedAuthSession:
        raw_token = _new_session_token()
        digest = digest_session_token(raw_token)
        session = AuthSession(
            session_digest=digest,
            actor_id=actor.actor_id,
            owner_id=actor.owner_id,
            roles=actor.roles,
            email_normalized=actor.email_normalized,
            display_name=actor.display_name,
            expires_at=expires_at,
        )
        self._sessions_by_digest[digest] = session
        return IssuedAuthSession(raw_token=raw_token, session=session)

    def get_session(self, raw_token: str, now: datetime) -> AuthSession | None:
        session = self._sessions_by_digest.get(digest_session_token(raw_token))
        if session is None or not session.is_active(now):
            return None
        return session

    def revoke_session(self, raw_token: str, now: datetime) -> bool:
        digest = digest_session_token(raw_token)
        session = self._sessions_by_digest.get(digest)
        if session is None:
            return False
        self._sessions_by_digest[digest] = replace(session, revoked_at=now)
        return True


def digest_session_token(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()


def _new_session_token() -> str:
    token_bytes = secrets.token_bytes(32)
    return urlsafe_b64encode(token_bytes).rstrip(b"=").decode("ascii")
