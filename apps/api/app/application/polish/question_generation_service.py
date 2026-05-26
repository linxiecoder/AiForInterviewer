"""Phase 1 Polish question generation service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from time import perf_counter, sleep
from typing import Any

from app.application.common.logging import LogUtil
from app.application.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.application.llm.ports import LlmTransport
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.entities import PolishQuestionDraft, PolishQuestionSource, PolishSession
from app.application.polish.next_question_agent import validate_next_question_agent_output
from app.application.polish.progress_evidence import ProgressEvidenceChunk, select_progress_tree_evidence_chunks
from app.application.polish.question_blueprint import (
    CLAIM_MODE_CLARIFICATION_NEEDED,
    EvidenceScope,
    QuestionBlueprint,
    build_question_blueprint,
)
from app.application.polish.question_generation_prompts import (
    build_follow_up_question_prompt_asset,
    build_question_prompt_asset,
    build_question_prompt_metadata,
    render_blueprint_question,
    validate_question_prompt_anchor_contract,
)
from app.application.polish.question_generation_policy import (
    DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY,
    QuestionGenerationRuntimePolicy,
)
from app.application.polish.question_grounding import GroundingResult, validate_question_grounding


QUESTION_GENERATION_SERVICE_VERSION = "polish_question_generation.v1"
UNSAFE_QUESTION_TEXT_MARKERS = (
    "raw_prompt",
    "system_prompt",
    "provider_payload",
    "api_key",
    "token=",
    "secret=",
)
PROJECT_CLARIFICATION_MARKERS = (
    "补充一个",
    "请分享一个您亲自负责",
    "请先补充",
    "你是否有另一个项目",
)
ENGINEERING_EVIDENCE_TERMS = (
    "Redis",
    "RocketMQ",
    "MQ",
    "异步",
    "分片",
    "状态",
    "MinIO",
    "大文件",
    "失败",
    "重试",
    "幂等",
    "恢复",
)


@dataclass(frozen=True)
class QuestionGenerationResult:
    succeeded: bool
    draft: PolishQuestionDraft | None
    blueprint: QuestionBlueprint | None
    grounding_result: GroundingResult
    validation_errors: tuple[str, ...] = ()
    progress_node_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()


class QuestionGenerationService:
    def __init__(
        self,
        *,
        llm_transport: LlmTransport | None = None,
        surface_question_builder: Callable[[QuestionBlueprint, EvidenceScope], str] | None = None,
        runtime_policy: QuestionGenerationRuntimePolicy | None = None,
    ) -> None:
        self._llm_transport = llm_transport
        self._surface_question_builder = surface_question_builder or render_blueprint_question
        self._runtime_policy = runtime_policy or DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY

    def generate(
        self,
        *,
        session: PolishSession,
        context: dict[str, Any],
        plan: dict[str, Any],
        state: dict[str, Any],
        requested_ref: str,
        follow_up_context: dict[str, Any] | None = None,
        runtime_policy: QuestionGenerationRuntimePolicy | None = None,
    ) -> QuestionGenerationResult:
        policy = runtime_policy or self._runtime_policy
        node = _resolve_progress_node(plan=plan, state=state, requested_ref=requested_ref)
        if node is None:
            return _validation_failed("progress_node_not_found", progress_node_ref=requested_ref)
        scope = _build_evidence_scope(
            context=context,
            plan=plan,
            state=state,
            node=node,
            requested_ref=requested_ref,
            source_priority_policy=policy.source_priority_by_purpose,
        )
        blueprint = build_question_blueprint(
            scope,
            question_kind_taxonomy=policy.question_kind_taxonomy,
        )
        is_follow_up = isinstance(follow_up_context, dict)
        prompt_asset = (
            build_follow_up_question_prompt_asset(
                blueprint,
                scope,
                follow_up_context=follow_up_context or {},
                runtime_policy=policy,
            )
            if is_follow_up
            else build_question_prompt_asset(blueprint, scope, runtime_policy=policy)
        )
        prompt_contract_errors = validate_question_prompt_anchor_contract(prompt_asset)
        if prompt_contract_errors:
            LogUtil.agent_runtime_step(
                task_type=policy.task_type,
                phase="prompt_contract_validation",
                status="failed",
                input_ref=scope.progress_node_ref,
                error_type=",".join(prompt_contract_errors),
            )
            return QuestionGenerationResult(
                succeeded=False,
                draft=None,
                blueprint=blueprint,
                grounding_result=GroundingResult(False, prompt_contract_errors),
                validation_errors=prompt_contract_errors,
                progress_node_ref=scope.progress_node_ref,
                evidence_refs=blueprint.evidence_refs,
            )
        LogUtil.agent_runtime_step(
            task_type=policy.task_type,
            phase="prompt_contract_validation",
            status="succeeded",
            input_ref=scope.progress_node_ref,
        )
        prompt_metadata = build_question_prompt_metadata(prompt_asset, runtime_policy=policy)
        prompt_task_type = _clean(prompt_asset.get("task_type")) or policy.task_type
        question_pattern = "follow_up_targeted" if is_follow_up else blueprint.question_kind
        follow_up_metadata = _follow_up_generation_metadata(follow_up_context, prompt_asset) if is_follow_up else {}
        llm_payload: dict[str, Any] | None = None
        llm_result: LlmTransportResult | None = None
        generation_metadata: dict[str, Any]
        rewrite_metadata: dict[str, Any] = {}
        if self._llm_transport is not None:
            llm_result = _generate_llm_question(
                transport=self._llm_transport,
                prompt_asset=prompt_asset,
                blueprint=blueprint,
                scope=scope,
                runtime_policy=policy,
            )
            if isinstance(llm_result, QuestionGenerationResult):
                return llm_result
            llm_payload, validation_errors = _parse_llm_question_payload(
                llm_result.result,
                blueprint=blueprint,
            )
            if validation_errors:
                LogUtil.agent_runtime_step(
                    task_type=policy.task_type,
                    phase="parse_output",
                    status="failed",
                    input_ref=scope.progress_node_ref,
                    error_type=",".join(validation_errors),
                )
                return QuestionGenerationResult(
                    succeeded=False,
                    draft=None,
                    blueprint=blueprint,
                    grounding_result=GroundingResult(False, validation_errors),
                    validation_errors=validation_errors,
                    progress_node_ref=scope.progress_node_ref,
                    evidence_refs=blueprint.evidence_refs,
                )
            LogUtil.agent_runtime_step(
                task_type=policy.task_type,
                phase="parse_output",
                status="succeeded",
                input_ref=scope.progress_node_ref,
                output_ref=_clean(llm_result.result.get("trace_ref")) or None,
            )
            if llm_payload.get("next_question_agent"):
                question_pattern = _clean(llm_payload.get("question_kind")) or question_pattern
            question_text = str(llm_payload["question_text"]).strip()
            transport_kind = _clean(llm_result.result.get("transport"))
            is_fake_transport = transport_kind == "fake"
            generation_metadata = {
                "llm_task_type": prompt_task_type,
                "prompt_version": policy.prompt_version,
                "llm_output_validation_status": "valid",
                "llm_generation_mode": (
                    "deterministic_fake_transport" if is_fake_transport else "provider_structured_json"
                ),
                "fallback_visible": is_fake_transport,
                "provider_status": "fake_transport" if is_fake_transport else "called",
                "llm_trace_refs": list(llm_result.trace_refs),
                "llm_evidence_refs": list(llm_result.evidence_refs),
            }
            if is_fake_transport:
                generation_metadata["fallback_reason"] = "fake_transport_configured"
        else:
            question_text = (
                _render_follow_up_degraded_question(blueprint, scope, follow_up_context or {})
                if is_follow_up
                else self._surface_question_builder(blueprint, scope)
            )
            LogUtil.agent_runtime_step(
                task_type=policy.task_type,
                phase="llm_call",
                status="skipped",
                input_ref=scope.progress_node_ref,
                error_type="llm_transport_unavailable",
            )
            generation_metadata = {
                "llm_task_type": prompt_task_type,
                "llm_generation_mode": "deterministic_degraded_generation",
                "fallback_reason": "llm_transport_unavailable",
                "fallback_visible": True,
                "provider_status": "not_configured",
            }
        question_text = str(question_text).strip()
        if not llm_payload or not llm_payload.get("next_question_agent"):
            question_text, rewrite_metadata = _rewrite_project_clarification_question(
                question_text,
                scope=scope,
                blueprint=blueprint,
            )
        if not question_text:
            return _validation_failed("question_text_required", progress_node_ref=scope.progress_node_ref)
        if _contains_unsafe_question_text_marker(question_text):
            return _validation_failed("question_text_unsafe_leakage", progress_node_ref=scope.progress_node_ref)
        grounding_result = validate_question_grounding(
            blueprint=blueprint,
            question_text=question_text,
            primary_source_type=scope.primary_source_type,
        )
        grounding_errors = tuple(grounding_result.validation_errors)
        grounding_failed = not grounding_result.passed
        llm_evidence_refs = tuple(llm_payload.get("evidence_refs") or ()) if llm_payload else ()
        draft_evidence_refs = llm_evidence_refs or blueprint.evidence_refs
        llm_clarification_needed = bool(llm_payload.get("clarification_needed")) if llm_payload else False
        low_confidence_flags: list[str] = []
        if not draft_evidence_refs or llm_clarification_needed:
            low_confidence_flags.append("clarification_needed")
        if grounding_failed:
            low_confidence_flags.extend(("grounding_failed", "manual_review_required", *grounding_errors))
        low_confidence_flags = list(dict.fromkeys(low_confidence_flags))
        quality_warnings = list(grounding_errors) if grounding_failed else []
        manual_review_required = grounding_failed or llm_clarification_needed
        manual_review_reason = (
            "grounding_failed_soft_warning"
            if grounding_failed
            else ("clarification_needed" if llm_clarification_needed else None)
        )
        grounding_status = "failed_warning" if grounding_failed else "passed"
        confidence_level = "low" if low_confidence_flags else ("medium" if draft_evidence_refs else "low")
        source_availability = (
            "weak"
            if grounding_failed
            else ("available" if draft_evidence_refs else "partial")
        )
        next_question_metadata = _next_question_agent_metadata(llm_payload)
        draft = PolishQuestionDraft(
            question_text=question_text,
            question_sources=scope.question_sources,
            progress_node_ref=scope.progress_node_ref,
            evidence_refs=draft_evidence_refs,
            context_digest=scope.context_digest,
            question_pattern=question_pattern,
            quality_score=None,
            confidence_level=confidence_level,
            low_confidence_flags=tuple(low_confidence_flags),
            expected_answer_dimensions=_expected_answer_dimensions(blueprint, follow_up_context),
            question_metadata={
                "question_pattern": question_pattern,
                "quality_score": None,
                "quality_warnings": quality_warnings,
                "confidence_level": confidence_level,
                "low_confidence_flags": low_confidence_flags,
                "expected_answer_dimensions": list(_expected_answer_dimensions(blueprint, follow_up_context)),
                "builder_version": QUESTION_GENERATION_SERVICE_VERSION,
                "validator_version": "polish_question_grounding.v1",
                "signal_version": "evidence_grounded_blueprint.v1",
                "source_availability": source_availability,
                "generation_service": QUESTION_GENERATION_SERVICE_VERSION,
                "blueprint_version": blueprint.metadata.get("blueprint_version"),
                **prompt_metadata,
                **follow_up_metadata,
                **generation_metadata,
                **rewrite_metadata,
                **next_question_metadata,
                "question_kind": question_pattern,
                "claim_mode": blueprint.claim_mode,
                "llm_difficulty": llm_payload.get("difficulty") if llm_payload else None,
                "llm_skill_dimension": llm_payload.get("skill_dimension") if llm_payload else None,
                "llm_expected_signal": llm_payload.get("expected_signal") if llm_payload else None,
                "llm_confidence": llm_payload.get("confidence") if llm_payload else None,
                "llm_missing_context": list(llm_payload.get("missing_context", ())) if llm_payload else [],
                "llm_clarification_needed": llm_clarification_needed if llm_payload else None,
                "primary_evidence_ref": blueprint.primary_evidence_ref,
                "primary_question_evidence_ref": blueprint.primary_evidence_ref,
                "primary_source_type": scope.primary_source_type,
                "grounding_status": grounding_status,
                "grounding_validation_errors": list(grounding_errors),
                "grounding_blocking_bypassed": grounding_failed,
                "manual_review_required": manual_review_required,
                "manual_review_reason": manual_review_reason,
                "grounding_gate_result": grounding_status,
                "grounding_gate_issues": list(grounding_errors),
                "validation_errors": [],
            },
            builder_version=QUESTION_GENERATION_SERVICE_VERSION,
            validator_version="polish_question_grounding.v1",
        )
        return QuestionGenerationResult(
            succeeded=True,
            draft=draft,
            blueprint=blueprint,
            grounding_result=grounding_result,
            validation_errors=(),
            progress_node_ref=scope.progress_node_ref,
            evidence_refs=draft_evidence_refs,
        )


def _generate_llm_question(
    *,
    transport: LlmTransport,
    prompt_asset: dict[str, Any],
    blueprint: QuestionBlueprint,
    scope: EvidenceScope,
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> LlmTransportResult | QuestionGenerationResult:
    task_type = _clean(prompt_asset.get("task_type")) or runtime_policy.task_type
    prompt_version = _clean(prompt_asset.get("prompt_version")) or runtime_policy.prompt_version
    schema_id = _clean(prompt_asset.get("schema_id")) or runtime_policy.prompt_schema_id
    request = LlmTransportRequest(
        contract_ids=runtime_policy.contract_ids,
        task_type=task_type,
        input_refs=(scope.progress_node_ref, *blueprint.evidence_refs),
        evidence_bundle=prompt_asset,
        prompt_version=prompt_version,
        schema_id=schema_id,
    )
    max_retries = max(0, int(runtime_policy.llm_max_retries))
    max_attempts = max_retries + 1
    for attempt in range(1, max_attempts + 1):
        started_at = perf_counter()
        LogUtil.agent_runtime_step(
            task_type=runtime_policy.task_type,
            phase="llm_call",
            status="started",
            attempt=attempt,
            max_attempts=max_attempts,
            input_ref=scope.progress_node_ref,
        )
        try:
            result = transport.generate(request)
        except LlmTransportConfigurationError:
            return _llm_generation_failed(
                blueprint=blueprint,
                scope=scope,
                validation_error="llm_transport_configuration_failed",
                runtime_policy=runtime_policy,
                attempt=attempt,
                max_attempts=max_attempts,
                started_at=started_at,
            )
        except (LlmTransportUnavailableError, LlmTransportResponseError, TimeoutError) as exc:
            error_type = exc.__class__.__name__
            if attempt <= max_retries:
                LogUtil.agent_runtime_step(
                    task_type=runtime_policy.task_type,
                    phase="llm_call",
                    status="retry_scheduled",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    retry_delay_seconds=runtime_policy.llm_retry_backoff_seconds,
                    duration_ms=round((perf_counter() - started_at) * 1000, 3),
                    input_ref=scope.progress_node_ref,
                    error_type=error_type,
                )
                sleep(runtime_policy.llm_retry_backoff_seconds)
                continue
            return _llm_generation_failed(
                blueprint=blueprint,
                scope=scope,
                validation_error="llm_transport_generation_failed",
                runtime_policy=runtime_policy,
                attempt=attempt,
                max_attempts=max_attempts,
                started_at=started_at,
                error_type=error_type,
            )
        except Exception as exc:
            return _llm_generation_failed(
                blueprint=blueprint,
                scope=scope,
                validation_error="llm_transport_generation_failed",
                runtime_policy=runtime_policy,
                attempt=attempt,
                max_attempts=max_attempts,
                started_at=started_at,
                error_type=exc.__class__.__name__,
            )
        LogUtil.agent_runtime_step(
            task_type=runtime_policy.task_type,
            phase="llm_call",
            status="succeeded",
            attempt=attempt,
            max_attempts=max_attempts,
            duration_ms=round((perf_counter() - started_at) * 1000, 3),
            input_ref=scope.progress_node_ref,
            output_ref=(result.trace_refs[0] if result.trace_refs else None),
        )
        return result

    validation_errors = ("llm_transport_generation_failed",)
    return QuestionGenerationResult(
        succeeded=False,
        draft=None,
        blueprint=blueprint,
        grounding_result=GroundingResult(False, validation_errors),
        validation_errors=validation_errors,
        progress_node_ref=scope.progress_node_ref,
        evidence_refs=blueprint.evidence_refs,
    )


def _rewrite_project_clarification_question(
    question_text: str,
    *,
    scope: EvidenceScope,
    blueprint: QuestionBlueprint,
) -> tuple[str, dict[str, Any]]:
    if not _looks_like_project_clarification_question(question_text):
        return question_text, {}
    source = _preferred_engineering_resume_source(scope.question_sources)
    if source is None:
        return question_text, {}

    title = _clean(blueprint.node_title) or "当前能力点"
    background = _project_background(source)
    terms = _matched_engineering_terms(f"{source.title} {source.excerpt}")
    mechanism_clause = (
        f"使用{'、'.join(terms[:4])}等机制"
        if terms
        else "处理关键工程链路"
    )
    rewritten = (
        f"基于你在{background}中{mechanism_clause}的经历，这条实际链路当时是怎么串起来的？"
        "请按业务入口、状态记录、存储或消息处理、异常处理和效果验证来说明。"
    )
    return (
        rewritten,
        {
            "question_text_rewritten_from_clarification": True,
            "question_text_rewrite_reason": "project_clarification_to_implementation_deep_dive",
            "question_text_rewrite_source_ref": source.ref_id,
            "question_text_rewrite_target_capability": title,
        },
    )


def _looks_like_project_clarification_question(question_text: str) -> bool:
    text = _clean(question_text)
    if any(marker in text for marker in PROJECT_CLARIFICATION_MARKERS):
        return True
    return "未涉及" in text and "能否补充" in text


def _preferred_engineering_resume_source(
    sources: tuple[PolishQuestionSource, ...],
) -> PolishQuestionSource | None:
    candidates = [
        source
        for source in sources
        if source.source_type == "resume_project" and (_clean(source.title) or _clean(source.excerpt))
    ]
    if not candidates:
        return None
    return max(candidates, key=_engineering_source_score)


def _engineering_source_score(source: PolishQuestionSource) -> int:
    text = f"{source.title} {source.excerpt}".lower()
    return sum(1 for term in ENGINEERING_EVIDENCE_TERMS if term.lower() in text)


def _matched_engineering_terms(text: str) -> list[str]:
    normalized = text.lower()
    matched: list[str] = []
    for term in ENGINEERING_EVIDENCE_TERMS:
        if term.lower() not in normalized:
            continue
        if term == "MQ" and any(item.endswith("MQ") for item in matched):
            continue
        matched.append(term)
    return matched


def _project_background(source: PolishQuestionSource) -> str:
    raw = _clean(source.title) or _clean(source.excerpt) or "已有项目"
    for separator in ("：", ":", "。", "；", ";", "\n"):
        candidate = raw.split(separator, 1)[0].strip()
        if candidate:
            raw = candidate
            break
    return _compact_text(raw, limit=60)


def _llm_generation_failed(
    *,
    blueprint: QuestionBlueprint,
    scope: EvidenceScope,
    validation_error: str,
    runtime_policy: QuestionGenerationRuntimePolicy,
    attempt: int,
    max_attempts: int,
    started_at: float,
    error_type: str | None = None,
) -> QuestionGenerationResult:
    LogUtil.agent_runtime_step(
        task_type=runtime_policy.task_type,
        phase="llm_call",
        status="failed",
        attempt=attempt,
        max_attempts=max_attempts,
        duration_ms=round((perf_counter() - started_at) * 1000, 3),
        input_ref=scope.progress_node_ref,
        error_type=error_type or validation_error,
    )
    validation_errors = (validation_error,)
    return QuestionGenerationResult(
        succeeded=False,
        draft=None,
        blueprint=blueprint,
        grounding_result=GroundingResult(False, validation_errors),
        validation_errors=validation_errors,
        progress_node_ref=scope.progress_node_ref,
        evidence_refs=blueprint.evidence_refs,
    )


def _parse_llm_question_payload(
    payload: dict[str, Any],
    *,
    blueprint: QuestionBlueprint,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if isinstance(payload.get("decision"), dict) or isinstance(payload.get("question"), dict):
        agent_payload, agent_errors = validate_next_question_agent_output(
            payload,
            allowed_evidence_refs=blueprint.evidence_refs,
        )
        if agent_errors or agent_payload is None:
            return None, agent_errors
        question = agent_payload["question"]
        return (
            {
                "question_text": question["question_text"],
                "question_kind": question["question_kind"],
                "focus_dimension": question["question_kind"],
                "difficulty": question["difficulty"],
                "skill_dimension": question["skill_dimension"],
                "expected_signal": question["expected_signal"],
                "follow_ups": list(question["follow_ups"]),
                "scoring_rubric": list(question["scoring_rubric"]),
                "missing_context": list(agent_payload["missing_context"]),
                "evidence_refs": list(agent_payload["evidence_refs"]),
                "confidence": agent_payload["confidence"],
                "clarification_needed": agent_payload["clarification_needed"],
                "next_question_agent": agent_payload,
            },
            (),
        )

    errors: list[str] = []
    question_text = _clean(payload.get("question_text"))
    if not question_text:
        errors.append("llm_question_text_required")
    elif _contains_unsafe_question_text_marker(question_text):
        errors.append("llm_question_text_unsafe_leakage")

    question_kind = _clean(payload.get("question_kind"))
    if question_kind and question_kind != blueprint.question_kind:
        errors.append("llm_question_kind_mismatch")
    if not question_kind:
        question_kind = blueprint.question_kind

    focus_dimension = _clean(payload.get("focus_dimension")) or blueprint.question_kind
    difficulty = _clean(payload.get("difficulty"))
    if difficulty not in {"easy", "medium", "hard", "clarification"}:
        errors.append("llm_difficulty_invalid")

    skill_dimension = _clean(payload.get("skill_dimension")) or _clean(blueprint.expected_capability)
    if not skill_dimension:
        errors.append("llm_skill_dimension_required")

    expected_signal = _clean(payload.get("expected_signal"))
    if not expected_signal:
        errors.append("llm_expected_signal_required")

    follow_ups = _string_list(payload.get("follow_ups"), max_items=3)
    if not follow_ups:
        errors.append("llm_follow_ups_required")

    scoring_rubric = _scoring_rubric(payload.get("scoring_rubric"))
    if not scoring_rubric:
        errors.append("llm_scoring_rubric_required")

    missing_context = _string_list(payload.get("missing_context"), max_items=8)
    confidence = _clean(payload.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        errors.append("llm_confidence_invalid")

    clarification_needed = payload.get("clarification_needed")
    if not isinstance(clarification_needed, bool):
        errors.append("llm_clarification_needed_required")

    if "evidence_refs" not in payload:
        errors.append("llm_evidence_refs_required")
    evidence_refs = _string_list(payload.get("evidence_refs"), max_items=8)

    if errors:
        return None, tuple(dict.fromkeys(errors))
    return (
        {
            "question_text": question_text,
            "question_kind": question_kind,
            "focus_dimension": focus_dimension,
            "difficulty": difficulty,
            "skill_dimension": skill_dimension,
            "expected_signal": expected_signal,
            "follow_ups": follow_ups,
            "scoring_rubric": scoring_rubric,
            "missing_context": missing_context,
            "evidence_refs": evidence_refs,
            "confidence": confidence,
            "clarification_needed": clarification_needed,
        },
        (),
    )


def _next_question_agent_metadata(llm_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(llm_payload, dict):
        return {}
    agent = llm_payload.get("next_question_agent")
    if not isinstance(agent, dict):
        return {}
    decision = agent.get("decision") if isinstance(agent.get("decision"), dict) else {}
    question = agent.get("question") if isinstance(agent.get("question"), dict) else {}
    persistence_hints = (
        agent.get("persistence_hints") if isinstance(agent.get("persistence_hints"), dict) else {}
    )
    post_check_hints = (
        agent.get("post_check_hints") if isinstance(agent.get("post_check_hints"), dict) else {}
    )
    return {
        "next_question_schema_id": agent.get("schema_id"),
        "next_question_schema_version": agent.get("schema_version"),
        "next_question_prompt_version": agent.get("prompt_version"),
        "next_question_clarification_needed": bool(agent.get("clarification_needed")),
        "next_question_confidence": agent.get("confidence"),
        "next_question_missing_context": list(agent.get("missing_context") or []),
        "next_question_decision": dict(decision),
        "next_question_question": dict(question),
        "next_question_persistence_hints": dict(persistence_hints),
        "next_question_evidence_refs": list(agent.get("evidence_refs") or []),
        "next_question_post_check_hints": dict(post_check_hints),
        "turn_intent": decision.get("turn_intent"),
        "evidence_support_level": decision.get("evidence_support_level"),
        "main_question_style": decision.get("main_question_style"),
        "allowed_extension_depth": decision.get("allowed_extension_depth"),
        "unsupported_capability_claims": list(decision.get("unsupported_capability_claims") or []),
    }


def _scoring_rubric(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, Any]] = []
    for raw_item in value[:4]:
        if not isinstance(raw_item, dict):
            continue
        dimension = _clean(raw_item.get("dimension"))
        signals = _string_list(raw_item.get("signals"), max_items=4)
        if dimension and signals:
            items.append({"dimension": dimension, "signals": signals})
    return items


def _validation_failed(reason: str, *, progress_node_ref: str | None = None) -> QuestionGenerationResult:
    grounding_result = GroundingResult(passed=False, validation_errors=(reason,))
    return QuestionGenerationResult(
        succeeded=False,
        draft=None,
        blueprint=None,
        grounding_result=grounding_result,
        validation_errors=grounding_result.validation_errors,
        progress_node_ref=progress_node_ref,
        evidence_refs=(),
    )


def _contains_unsafe_question_text_marker(question_text: str) -> bool:
    normalized = question_text.lower()
    return any(marker in normalized for marker in UNSAFE_QUESTION_TEXT_MARKERS)


def _build_evidence_scope(
    *,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    node: dict[str, Any],
    requested_ref: str,
    source_priority_policy: dict[str, dict[str, int]],
) -> EvidenceScope:
    selection = select_progress_tree_evidence_chunks(
        context,
        purpose="next_question",
        max_chunks=4,
        max_chars=1800,
        existing_plan=plan,
        existing_state=state,
        progress_node_ref=requested_ref,
        source_priority_policy=source_priority_policy,
    )
    chunks = tuple(chunk for chunk in selection.selected_chunks if _clean(chunk.text))
    primary = _primary_chunk(chunks, source_priority_policy=source_priority_policy)
    evidence_refs = tuple(chunk.chunk_id for chunk in chunks)
    sources = tuple(_question_source(index=index, chunk=chunk) for index, chunk in enumerate(chunks, start=1))
    node_title = _first_text(node.get("display_title"), node.get("title"), node.get("exam_point"), requested_ref)
    expected_capability = _first_text(node.get("expected_capability"), node.get("description"), node_title)
    return EvidenceScope(
        progress_node_ref=requested_ref,
        node_title=node_title,
        expected_capability=expected_capability,
        missing_points=tuple(_string_list(node.get("missing_points"))),
        primary_evidence_ref=primary.chunk_id if primary is not None else None,
        primary_evidence_text=primary.text if primary is not None else None,
        primary_source_type=primary.source_type if primary is not None else None,
        evidence_refs=evidence_refs,
        question_sources=sources,
        context_digest=_first_text(plan.get("context_digest"), context.get("content_digest"), None),
        dropped_context_summary=selection.dropped_context_summary,
    )


def _resolve_progress_node(
    *,
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str,
) -> dict[str, Any] | None:
    nodes = plan.get("nodes")
    if not isinstance(nodes, list):
        return None
    requested = _find_progress_node(nodes, requested_ref)
    if requested is not None:
        return requested
    priority = state.get("current_priority")
    if isinstance(priority, dict):
        priority_ref = _clean(priority.get("progress_node_ref"))
        if priority_ref:
            return _find_progress_node(nodes, priority_ref)
    leaves = _flatten_leaf_nodes(nodes)
    return leaves[0] if leaves else None


def _find_progress_node(nodes: list[dict[str, Any]], progress_node_ref: str) -> dict[str, Any] | None:
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if _clean(node.get("progress_node_ref")) == progress_node_ref:
            return node
        child = _find_progress_node(node.get("children", []), progress_node_ref)
        if child is not None:
            return child
    return None


def _flatten_leaf_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leaves: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = [child for child in node.get("children", []) if isinstance(child, dict)]
        if children:
            leaves.extend(_flatten_leaf_nodes(children))
        else:
            leaves.append(node)
    return leaves


def _primary_chunk(
    chunks: tuple[ProgressEvidenceChunk, ...],
    *,
    source_priority_policy: dict[str, dict[str, int]],
) -> ProgressEvidenceChunk | None:
    if not chunks:
        return None
    order = source_priority_policy.get("next_question", {})
    return min(chunks, key=lambda chunk: (order.get(chunk.source_type, 99), chunk.sequence))


def _question_source(*, index: int, chunk: ProgressEvidenceChunk) -> PolishQuestionSource:
    return PolishQuestionSource(
        index=index,
        source_type=chunk.source_type,
        title=chunk.title,
        excerpt=chunk.text,
        ref_id=chunk.chunk_id,
        availability="available",
    )


def _expected_answer_dimensions(
    blueprint: QuestionBlueprint,
    follow_up_context: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    if follow_up_context:
        target_dimension = _clean(follow_up_context.get("target_dimension"))
        if target_dimension:
            return (target_dimension, "失败路径、边界和验证指标")
    if blueprint.required_answer_materials:
        return blueprint.required_answer_materials
    return ("业务背景", "关键技术链路", "异常处理或取舍", "验证指标")


def _string_list(value: object, *, max_items: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = [_clean(item) for item in value if _clean(item)]
    if max_items is None:
        return cleaned
    return cleaned[:max_items]


def _first_text(*values: object) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _clean(value: object) -> str:
    return str(value or "").strip()


def _follow_up_generation_metadata(
    follow_up_context: dict[str, Any] | None,
    prompt_asset: dict[str, Any],
) -> dict[str, Any]:
    context = follow_up_context if isinstance(follow_up_context, dict) else {}
    input_refs = [
        _clean(context.get("parent_question_id")),
        _clean(context.get("parent_answer_id")),
        _clean(context.get("parent_feedback_id")),
    ]
    focus_seed = "|".join(ref for ref in input_refs if ref) or _clean(context.get("target_dimension")) or "follow_up"
    focus_digest = sha256(focus_seed.encode("utf-8")).hexdigest()[:12]
    return {
        "follow_up_reason": _clean(context.get("follow_up_reason")) or "business_follow_up_request",
        "follow_up_target_dimension": _clean(context.get("target_dimension")) or "未覆盖追问点",
        "follow_up_prompt_task_type": _clean(prompt_asset.get("task_type")),
        "follow_up_prompt_version": _clean(prompt_asset.get("prompt_version")),
        "follow_up_input_refs": [ref for ref in input_refs if ref],
        "focus_dimension": _clean(context.get("target_dimension")) or "follow_up_targeted",
        "focus_key": f"focus_follow_up_{focus_digest}",
        "template_signature": f"llm:follow_up_prompt:{focus_digest}",
        "blueprint_signature": f"bp:follow_up_context:{focus_digest}",
        "duplicate_gate_result": "follow_up_parent_bound",
    }


def _render_follow_up_degraded_question(
    blueprint: QuestionBlueprint,
    scope: EvidenceScope,
    follow_up_context: dict[str, Any],
) -> str:
    target_dimension = _compact_text(
        _clean(follow_up_context.get("target_dimension")) or blueprint.expected_capability or "未覆盖追问点",
        limit=96,
    )
    answer_excerpt = _compact_text(
        _clean(follow_up_context.get("parent_answer_excerpt")) or "上一轮回答",
        limit=96,
    )
    evidence_excerpt = _compact_text(
        _clean(blueprint.primary_evidence_text) or _clean(scope.node_title) or "当前岗位与简历证据",
        limit=120,
    )
    return (
        f"你上一轮回答中提到「{answer_excerpt}」，现在围绕「{target_dimension}」继续追问："
        f"请结合上一题背景和当前岗位/简历证据「{evidence_excerpt}」，说明你的具体判断、边界、"
        "失败处理、验证指标和关键取舍。"
    )


def _compact_text(value: str, *, limit: int) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."
