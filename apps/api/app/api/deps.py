"""FastAPI dependencies for F5 auth and owner boundary."""

from typing import Any

from fastapi import Request

from app.api.errors import raise_api_error
from app.domain.auth.entities import CurrentActor
from app.domain.auth.value_objects import OwnerScope


def get_auth_runtime(request: Request) -> Any:
    runtime = getattr(request.app.state, "auth_runtime", None)
    if runtime is None:
        raise_api_error(
            status_code=500,
            code="internal_error",
            message="Auth runtime is not available.",
        )
    return runtime


def get_current_actor(request: Request) -> CurrentActor | None:
    runtime = get_auth_runtime(request)
    session_token = request.cookies.get(runtime.cookie_policy.name)
    return runtime.auth_service.current_actor(session_token)


async def optional_actor(request: Request) -> CurrentActor | None:
    return get_current_actor(request)


async def require_authenticated_actor(request: Request) -> CurrentActor:
    actor = get_current_actor(request)
    if actor is None:
        raise_api_error(
            status_code=401,
            code="unauthenticated",
            message="Authentication is required.",
            user_action="login",
        )
    return actor


async def require_current_actor(request: Request) -> CurrentActor:
    return await require_authenticated_actor(request)


def owner_scope_for_actor(actor: CurrentActor) -> OwnerScope:
    return OwnerScope(actor_id=actor.actor_id, owner_id=actor.owner_id, roles=actor.roles)
