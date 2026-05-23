"""Authentication runtime adapter for the F5 foundation baseline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from os import getenv

from app.application.auth.use_cases import AuthUseCases
from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from app.infrastructure.observability.logging import LogUtil
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.infrastructure.security.stores import InMemorySessionStore, InMemoryUserStore


@dataclass(frozen=True)
class AuthCookiePolicy:
    name: str = "aifi_session"
    path: str = "/api/v1"
    httponly: bool = True
    samesite: str = "lax"
    secure: bool = False


@dataclass(frozen=True)
class AuthRuntimeSettings:
    session_ttl_seconds: int = 28_800
    cookie_secure: bool = False
    seed_dev_user: bool = True
    dev_user_identifier: str = "developer"
    dev_user_email: str = "developer@example.com"
    dev_username: str = "developer"
    dev_display_name: str = "F5 Dev User"
    dev_user_password: str = ""


@dataclass(frozen=True)
class AuthRuntime:
    auth_service: AuthUseCases
    cookie_policy: AuthCookiePolicy
    user_store: InMemoryUserStore
    session_store: InMemorySessionStore


def build_auth_runtime(
    settings: AuthRuntimeSettings | None = None,
    *,
    cookie_path: str = "/api/v1",
) -> AuthRuntime:
    resolved = settings or AuthRuntimeSettings()
    hasher = Pbkdf2PasswordHasher()
    user_store = InMemoryUserStore()
    session_store = InMemorySessionStore()
    if resolved.seed_dev_user:
        user_store.add_user(
            user_id=stable_resource_id(ResourceIdPrefix.USER, resolved.dev_user_email.strip().lower()),
            email=resolved.dev_user_email,
            username=resolved.dev_username,
            display_name=resolved.dev_display_name,
            password_hash=hasher.hash_password(resolved.dev_user_password),
        )
    auth_service = AuthUseCases(
        user_store=user_store,
        session_store=session_store,
        password_hasher=hasher,
        session_ttl=timedelta(seconds=resolved.session_ttl_seconds),
    )
    return AuthRuntime(
        auth_service=auth_service,
        cookie_policy=AuthCookiePolicy(path=cookie_path, secure=resolved.cookie_secure),
        user_store=user_store,
        session_store=session_store,
    )


def build_auth_runtime_from_env(*, cookie_path: str = "/api/v1") -> AuthRuntime:
    seed_enabled = _env_bool("API_AUTH_DEV_USER_ENABLED", _default_dev_seed_enabled())
    dev_user_identifier = _env("API_AUTH_DEV_USER_IDENTIFIER", "developer")
    dev_user_password = _env_optional("API_AUTH_DEV_USER_PASSWORD")
    if seed_enabled and not dev_user_password:
        LogUtil.auth_dev_seed_disabled_missing_password()
        seed_enabled = False

    if seed_enabled and dev_user_password is None:
        seed_enabled = False

    return build_auth_runtime(
        AuthRuntimeSettings(
            session_ttl_seconds=_env_int("API_AUTH_SESSION_TTL_SECONDS", 28_800),
            cookie_secure=_env_bool("API_AUTH_COOKIE_SECURE", False),
            seed_dev_user=seed_enabled,
            dev_user_identifier=dev_user_identifier,
            dev_user_email=_env(
                "API_AUTH_DEV_USER_EMAIL", _default_dev_email_from_identifier(dev_user_identifier)
            ),
            dev_username=_env(
                "API_AUTH_DEV_USER_USERNAME", _default_dev_username_from_identifier(dev_user_identifier)
            ),
            dev_display_name=_env("API_AUTH_DEV_DISPLAY_NAME", "F5 Dev User"),
            dev_user_password=dev_user_password or "",
        ),
        cookie_path=cookie_path,
    )


def _env(name: str, default: str) -> str:
    value = getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped or default


def _env_int(name: str, default: int) -> int:
    value = getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _env_bool(name: str, default: bool) -> bool:
    value = getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_dev_seed_enabled() -> bool:
    return _env("API_AUTH_ENV", _env("API_ENV", "local")).lower() in {"local", "test", "development", "dev"}


def _env_optional(name: str) -> str | None:
    value = getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _default_dev_email_from_identifier(identifier: str) -> str:
    identifier = identifier.strip()
    if "@" in identifier:
        return identifier
    return f"{identifier}@example.com"


def _default_dev_username_from_identifier(identifier: str) -> str:
    identifier = identifier.strip()
    if "@" in identifier:
        return identifier.split("@", maxsplit=1)[0]
    return identifier
