"""FastAPI dependencies for F5 auth and owner boundary."""

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from app.api.errors import raise_api_error
from app.application.ai_runtime.facade import AiOrchestrationFacade
from app.application.job_match.ports import JobMatchAnalyzer
from app.application.polish.question_generation_policy import (
    DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY,
    QuestionGenerationRuntimePolicy,
    QuestionGenerationRuntimePolicyResolver,
    mark_question_generation_runtime_policy_source,
    resolve_question_generation_runtime_policy,
)
from app.domain.auth.entities import CurrentActor
from app.domain.auth.value_objects import OwnerScope
from app.application.llm.ports import LlmTransport


def get_auth_runtime(request: Request) -> Any:
    runtime = getattr(request.app.state, "auth_runtime", None)
    if runtime is None:
        raise_api_error(
            status_code=500,
            code="internal_error",
            message="Auth runtime is not available.",
        )
    return runtime


async def get_db_session_factory(request: Request) -> sessionmaker[Session]:
    session_factory = getattr(request.app.state, "db_session_factory", None)
    if session_factory is None:
        raise_api_error(
            status_code=500,
            code="internal_error",
            message="Database session factory is not available.",
        )
    return session_factory


async def get_job_match_analyzer(request: Request) -> JobMatchAnalyzer:
    analyzer = getattr(request.app.state, "job_match_analyzer", None)
    if analyzer is None:
        raise_api_error(
            status_code=500,
            code="internal_error",
            message="Job match analyzer is not available.",
        )
    return analyzer


async def get_llm_transport(request: Request) -> LlmTransport:
    transport = getattr(request.app.state, "llm_transport", None)
    if transport is None:
        raise_api_error(
            status_code=500,
            code="internal_error",
            message="LLM transport is not available.",
        )
    return transport


async def get_ai_orchestration_facade(request: Request) -> AiOrchestrationFacade | None:
    return getattr(request.app.state, "ai_orchestration_facade", None)


async def get_question_generation_runtime_policy(request: Request) -> QuestionGenerationRuntimePolicy:
    policy = getattr(request.app.state, "question_generation_runtime_policy", None)
    if isinstance(policy, QuestionGenerationRuntimePolicy):
        return mark_question_generation_runtime_policy_source(
            policy,
            source=policy.source or "app_state.question_generation_runtime_policy",
            source_type="app_state",
            fallback=False,
            source_chain=("api_dependency:app_state.question_generation_runtime_policy",),
            source_version=policy.policy_version,
        )
    return mark_question_generation_runtime_policy_source(
        DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY,
        source="fallback_default",
        source_type="fallback_default",
        fallback=True,
        source_chain=(
            "api_dependency:default_question_generation_runtime_policy",
            "python_default:QuestionGenerationRuntimePolicy",
        ),
        source_version=DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY.policy_version,
    )


async def get_question_generation_runtime_policy_resolver(
    request: Request,
) -> QuestionGenerationRuntimePolicyResolver:
    resolver = getattr(request.app.state, "question_generation_runtime_policy_resolver", None)
    if callable(resolver):
        return resolver
    return resolve_question_generation_runtime_policy


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
