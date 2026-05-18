"""Auth use cases for the F5 foundation baseline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from app.application.auth.commands import LoginCommand, LogoutCommand
from app.domain.auth.entities import CurrentActor, UserAccount
from app.domain.auth.ports import PasswordHasher, SessionStore, UserCredentialStore
from app.domain.auth.services import actor_from_user
from app.domain.shared.clock import utc_now


@dataclass(frozen=True)
class LoginResult:
    session_token: str
    actor: CurrentActor
    user: UserAccount
    expires_at: datetime


@dataclass(frozen=True)
class CurrentUserResult:
    actor: CurrentActor
    user: UserAccount
    expires_at: datetime | None = None


class AuthUseCases:
    def __init__(
        self,
        *,
        user_store: UserCredentialStore,
        session_store: SessionStore,
        password_hasher: PasswordHasher,
        session_ttl: timedelta,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._user_store = user_store
        self._session_store = session_store
        self._password_hasher = password_hasher
        self._session_ttl = session_ttl
        self._clock = clock

    def login(self, command: LoginCommand) -> LoginResult | None:
        credentials = self._user_store.get_by_identifier(command.identifier)
        if credentials is None or not credentials.account.is_active():
            return None
        if not self._password_hasher.verify_password(command.password, credentials.password_hash):
            return None

        actor = actor_from_user(credentials.account)
        expires_at = self._clock() + self._session_ttl
        issued_session = self._session_store.issue_session(actor, expires_at)
        return LoginResult(
            session_token=issued_session.raw_token,
            actor=actor,
            user=credentials.account,
            expires_at=issued_session.session.expires_at,
        )

    def current_actor(self, session_token: str | None) -> CurrentActor | None:
        current_user = self.current_user(session_token)
        if current_user is None:
            return None
        return current_user.actor

    def current_user(self, session_token: str | None) -> CurrentUserResult | None:
        if not session_token:
            return None
        session = self._session_store.get_session(session_token, self._clock())
        if session is None:
            return None
        credentials = self._user_store.get_by_user_id(session.actor_id)
        if credentials is None or not credentials.account.is_active():
            return None
        return CurrentUserResult(
            actor=session.to_actor(),
            user=credentials.account,
            expires_at=session.expires_at,
        )

    def current_user_for_actor(self, actor: CurrentActor) -> CurrentUserResult | None:
        credentials = self._user_store.get_by_user_id(actor.actor_id)
        if credentials is None or not credentials.account.is_active():
            return None
        return CurrentUserResult(actor=actor, user=credentials.account)

    def logout(self, command: LogoutCommand) -> bool:
        return self._session_store.revoke_session(command.session_token, self._clock())
