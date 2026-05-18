"""Auth HTTP adapter."""

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import get_auth_runtime, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.auth.commands import LoginCommand, LogoutCommand
from app.domain.auth.entities import CurrentActor
from app.schemas.auth import CurrentUserResponse, LoginRequest, LogoutResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(payload: LoginRequest, request: Request, response: Response):
    runtime = get_auth_runtime(request)
    result = runtime.auth_service.login(LoginCommand(identifier=payload.identifier, password=payload.password))
    if result is None:
        raise_api_error(
            status_code=401,
            code="unauthenticated",
            message="Invalid credentials.",
            user_action="login",
        )

    _set_session_cookie(response, runtime.cookie_policy, result.session_token)
    return success_envelope(
        resource_type="current_user",
        data=_current_user_response(result.user, result.expires_at).model_dump(mode="json"),
    )


@router.get("/me")
async def me(request: Request, actor: CurrentActor = Depends(require_authenticated_actor)):
    runtime = get_auth_runtime(request)
    result = runtime.auth_service.current_user_for_actor(actor)
    if result is None:
        raise_api_error(
            status_code=401,
            code="unauthenticated",
            message="Authentication is required.",
            user_action="login",
        )
    return success_envelope(
        resource_type="current_user",
        data=_current_user_response(result.user, result.expires_at).model_dump(mode="json"),
    )


@router.post("/logout")
async def logout(request: Request, response: Response):
    runtime = get_auth_runtime(request)
    session_token = request.cookies.get(runtime.cookie_policy.name)
    if session_token:
        runtime.auth_service.logout(LogoutCommand(session_token=session_token))
    _clear_session_cookie(response, runtime.cookie_policy)
    data = LogoutResponse(logged_out=True).model_dump(mode="json")
    return success_envelope(resource_type="auth_logout", data=data)


def _current_user_response(user, session_expires_at) -> CurrentUserResponse:
    return CurrentUserResponse(
        user_id=user.user_id,
        owner_id=user.owner_id,
        email=user.email_normalized,
        username=user.username,
        display_name=user.display_name,
        roles=list(user.roles),
        session_expires_at=session_expires_at,
    )


def _set_session_cookie(response: Response, cookie_policy, token: str) -> None:
    response.set_cookie(
        key=cookie_policy.name,
        value=token,
        httponly=cookie_policy.httponly,
        secure=cookie_policy.secure,
        samesite=cookie_policy.samesite,
        path=cookie_policy.path,
    )


def _clear_session_cookie(response: Response, cookie_policy) -> None:
    response.delete_cookie(
        key=cookie_policy.name,
        path=cookie_policy.path,
        secure=cookie_policy.secure,
        httponly=cookie_policy.httponly,
        samesite=cookie_policy.samesite,
    )
