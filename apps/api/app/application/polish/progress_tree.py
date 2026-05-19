"""LLM-backed progress tree generation and state refresh."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from app.application.polish.entities import PolishQuestionDraft, PolishQuestionSource, PolishSession
from app.application.polish.progress_evidence import ProgressEvidenceChunk, select_progress_tree_evidence_chunks
from app.application.polish.progress_context import has_sufficient_progress_context, truncate_text
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_PLAN_CONTRACT_IDS,
    POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
    POLISH_PROGRESS_TREE_STATE_CONTRACT_IDS,
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
    build_initial_progress_tree_prompt,
    build_progress_tree_state_refresh_prompt,
)
from app.infrastructure.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.infrastructure.llm.ports import LlmTransport
from app.infrastructure.llm.types import LlmTransportRequest


PROGRESS_TREE_STATUS_READY = "ready"
PROGRESS_TREE_STATUS_FAILED = "failed"
PROGRESS_TREE_STATUS_REFRESH_FAILED = "refresh_failed"
PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT = "insufficient_context"
QUESTION_GENERATION_PROGRESS_NODE_CONTRACT = (
    "生成下一题时必须使用 progress_node_ref 对应节点的 title、expected_capability、相关岗位要求、"
    "相关简历证据、当前缺口和历史 turns。"
)
QUESTION_SOURCE_JOB_TYPES = {"job_requirement", "job_responsibility"}
QUESTION_SOURCE_RESUME_TYPES = {"resume_project", "resume_skill", "resume_work_experience", "resume_summary"}
QUESTION_SOURCE_TITLE_BY_TYPE = {
    "job_requirement": "岗位要求",
    "resume_evidence": "简历项目经历",
    "progress_node": "当前进展节点",
    "missing_point": "当前缺口",
    "history_feedback": "历史反馈",
}


class PolishProgressTreeLlmService:
    """Call the configured LLM transport and normalize progress tree outputs."""

    def __init__(self, transport: LlmTransport | None) -> None:
        self._transport = transport

    def generate_initial(self, context: dict[str, Any]) -> dict[str, Any]:
        if not has_sufficient_progress_context(context):
            return _insufficient_artifacts(context)
        if self._transport is None:
            return _failed_artifacts(context, reason="llm_transport_missing")

        try:
            result = self._transport.generate(
                LlmTransportRequest(
                    contract_ids=POLISH_PROGRESS_TREE_PLAN_CONTRACT_IDS,
                    task_type="polish_progress_tree_plan",
                    input_refs=_input_refs(context),
                    evidence_bundle=build_initial_progress_tree_prompt(context),
                )
            )
        except (LlmTransportConfigurationError, LlmTransportUnavailableError, LlmTransportResponseError):
            return _failed_artifacts(context, reason="llm_transport_failed")

        return _normalize_initial_artifacts(result.result, context)

    def refresh_state(
        self,
        *,
        context: dict[str, Any],
        existing_plan: dict[str, Any],
        existing_state: dict[str, Any],
    ) -> dict[str, Any]:
        if existing_plan.get("status") != PROGRESS_TREE_STATUS_READY:
            if not has_sufficient_progress_context(context):
                return _insufficient_artifacts(context)
            return {
                "status": existing_plan.get("status") or PROGRESS_TREE_STATUS_FAILED,
                "progress_tree_plan": existing_plan,
                "progress_tree_state": existing_state,
                "progress_percent": _progress_percent(existing_state),
            }
        if self._transport is None:
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="llm_transport_missing",
            )

        try:
            result = self._transport.generate(
                LlmTransportRequest(
                    contract_ids=POLISH_PROGRESS_TREE_STATE_CONTRACT_IDS,
                    task_type="polish_progress_tree_state",
                    input_refs=_input_refs(context),
                    evidence_bundle=build_progress_tree_state_refresh_prompt(
                        context=context,
                        existing_plan=existing_plan,
                        existing_state=existing_state,
                    ),
                )
            )
        except (LlmTransportConfigurationError, LlmTransportUnavailableError, LlmTransportResponseError):
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="llm_transport_failed",
            )

        state_payload = result.result.get("progress_tree_state") or result.result.get("state")
        if not isinstance(state_payload, dict):
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="llm_state_invalid",
            )
        normalized_state = _normalize_state(
            state_payload,
            existing_plan=existing_plan,
            allow_refresh_failed=True,
            prompt_version=_metadata_value(
                result.result,
                state_payload,
                "prompt_version",
                POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
            ),
            schema_id=_metadata_value(
                result.result,
                state_payload,
                "schema_id",
                POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
            ),
            schema_version=_metadata_value(
                result.result,
                state_payload,
                "schema_version",
                POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
            ),
        )
        if normalized_state["status"] != PROGRESS_TREE_STATUS_READY:
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="llm_state_invalid",
            )
        return {
            "status": PROGRESS_TREE_STATUS_READY,
            "progress_tree_plan": existing_plan,
            "progress_tree_state": normalized_state,
            "progress_percent": _progress_percent(normalized_state),
        }


def build_progress_node_question(
    *,
    session: PolishSession,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> PolishQuestionDraft:
    node = resolve_progress_node(plan=plan, state=state, requested_ref=requested_ref)
    if node is None:
        topic = session.topic_id or "manual_topic"
        source = PolishQuestionSource(
            index=1,
            source_type="progress_node",
            title=QUESTION_SOURCE_TITLE_BY_TYPE["progress_node"],
            excerpt="未找到可用的 progress_node_ref，已按当前打磨主题生成低置信问题。",
            ref_id=requested_ref,
            availability="unavailable",
        )
        return PolishQuestionDraft(
            question_text=(
                f"针对「{topic}」这个打磨目标，请选一个真实项目场景，讲清楚你当时负责的技术决策、"
                "取舍依据和结果验证方式。[1]"
            ),
            question_sources=(source,),
        )

    evidence_selection = select_progress_tree_evidence_chunks(
        context,
        purpose="next_question",
        existing_plan=plan,
        existing_state=state,
        progress_node_ref=node["progress_node_ref"],
    )
    evidence_chunks = list(evidence_selection.selected_chunks)
    sources = _index_question_sources(
        [
            _progress_node_source(node),
            _source_from_chunks(
                evidence_chunks,
                source_types=QUESTION_SOURCE_JOB_TYPES,
                normalized_source_type="job_requirement",
                fallback_title=QUESTION_SOURCE_TITLE_BY_TYPE["job_requirement"],
                fallback_ref_id=_snapshot_ref_id(context.get("job_snapshot", {}), "job_version_id", "job_id"),
                fallback_values=[
                    *node.get("related_job_requirements", []),
                    *context["job_snapshot"].get("requirements", []),
                    *context["job_snapshot"].get("responsibilities", []),
                ],
            ),
            _source_from_chunks(
                evidence_chunks,
                source_types=QUESTION_SOURCE_RESUME_TYPES,
                normalized_source_type="resume_evidence",
                fallback_title=QUESTION_SOURCE_TITLE_BY_TYPE["resume_evidence"],
                fallback_ref_id=_snapshot_ref_id(context.get("resume_snapshot", {}), "resume_version_id", "resume_id"),
                fallback_values=[
                    *node.get("related_resume_evidence", []),
                    *context["resume_snapshot"].get("project_experiences", []),
                    context["resume_snapshot"].get("summary"),
                ],
            ),
            _source_from_chunks(
                evidence_chunks,
                source_types={"match_gap"},
                normalized_source_type="missing_point",
                fallback_title=QUESTION_SOURCE_TITLE_BY_TYPE["missing_point"],
                fallback_ref_id=_snapshot_ref_id(context.get("match_context", {}), "analysis_id"),
                fallback_values=[
                    *node.get("missing_points", []),
                    *context["match_context"].get("missing_points", []),
                ],
                required=False,
            ),
            _source_from_chunks(
                evidence_chunks,
                source_types={"turn_feedback"},
                normalized_source_type="history_feedback",
                fallback_title=QUESTION_SOURCE_TITLE_BY_TYPE["history_feedback"],
                fallback_ref_id=None,
                fallback_values=[_latest_turn_feedback(context.get("turns", []))],
                required=False,
            ),
        ]
    )
    citations = "".join(f"[{source.index}]" for source in sources)
    focus = _question_focus(node)
    return PolishQuestionDraft(
        question_text=(
            f"针对「{focus}」这个进展节点，请选一个你实际参与的具体场景，讲清楚当时要解决的问题、"
            f"你负责的技术改造或决策、为什么这样取舍，以及上线后如何验证效果。{citations}"
        ),
        question_sources=sources,
    )


def build_progress_node_question_text(
    *,
    session: PolishSession,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> str:
    return build_progress_node_question(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=requested_ref,
    ).question_text


def _index_question_sources(sources: list[PolishQuestionSource | None]) -> tuple[PolishQuestionSource, ...]:
    indexed: list[PolishQuestionSource] = []
    seen: set[tuple[str, str, str]] = set()
    for source in sources:
        if source is None:
            continue
        key = (source.source_type, source.title, source.excerpt)
        if key in seen:
            continue
        seen.add(key)
        indexed.append(
            PolishQuestionSource(
                index=len(indexed) + 1,
                source_type=source.source_type,
                title=source.title,
                excerpt=source.excerpt,
                ref_id=source.ref_id,
                availability=source.availability,
            )
        )
    return tuple(indexed)


def _progress_node_source(node: dict[str, Any]) -> PolishQuestionSource:
    return PolishQuestionSource(
        index=0,
        source_type="progress_node",
        title=QUESTION_SOURCE_TITLE_BY_TYPE["progress_node"],
        excerpt=_source_excerpt(
            "；".join(
                item
                for item in (
                    f"节点：{truncate_text(node.get('title'), max_chars=80)}",
                    f"能力目标：{truncate_text(node.get('expected_capability'), max_chars=120)}",
                )
                if item
            )
        ),
        ref_id=truncate_text(node.get("progress_node_ref"), max_chars=120) or None,
        availability="available",
    )


def _source_from_chunks(
    chunks: list[ProgressEvidenceChunk],
    *,
    source_types: set[str],
    normalized_source_type: str,
    fallback_title: str,
    fallback_ref_id: str | None,
    fallback_values: list[object | None],
    required: bool = True,
) -> PolishQuestionSource | None:
    chunk = next((item for item in chunks if item.source_type in source_types and item.text), None)
    if chunk is not None:
        return PolishQuestionSource(
            index=0,
            source_type=normalized_source_type,
            title=_question_source_title(normalized_source_type, chunk.source_type),
            excerpt=_source_excerpt(chunk.text),
            ref_id=_chunk_ref_id(chunk) or fallback_ref_id,
            availability="available",
        )

    fallback_text = _first_available_text(*fallback_values)
    if fallback_text:
        return PolishQuestionSource(
            index=0,
            source_type=normalized_source_type,
            title=fallback_title,
            excerpt=_source_excerpt(fallback_text),
            ref_id=fallback_ref_id,
            availability="partial",
        )
    if not required:
        return None
    return PolishQuestionSource(
        index=0,
        source_type=normalized_source_type,
        title=fallback_title,
        excerpt="当前来源暂不可用，题目已按进展节点低置信生成。",
        ref_id=fallback_ref_id,
        availability="unavailable",
    )


def _question_source_title(normalized_source_type: str, raw_source_type: str) -> str:
    if raw_source_type == "job_responsibility":
        return "岗位职责"
    if raw_source_type == "resume_skill":
        return "简历技能证据"
    if raw_source_type == "resume_work_experience":
        return "简历工作经历"
    return QUESTION_SOURCE_TITLE_BY_TYPE.get(normalized_source_type, "来源")


def _question_focus(node: dict[str, Any]) -> str:
    return (
        truncate_text(node.get("title"), max_chars=80)
        or truncate_text(node.get("expected_capability"), max_chars=80)
        or "当前能力打磨目标"
    )


def _source_excerpt(value: object | None) -> str:
    return truncate_text(value, max_chars=180) or "内容待补充"


def _first_available_text(*values: object | None) -> str | None:
    for value in values:
        if isinstance(value, (list, tuple)):
            nested = _first_available_text(*value)
            if nested:
                return nested
            continue
        text = truncate_text(value, max_chars=320)
        if text:
            return text
    return None


def _chunk_ref_id(chunk: ProgressEvidenceChunk) -> str | None:
    source_ref = chunk.source_ref or {}
    for key in ("job_version_id", "resume_version_id", "analysis_id", "question_id", "turn_index"):
        ref_value = source_ref.get(key)
        if ref_value:
            return str(ref_value)
    return chunk.chunk_id


def _snapshot_ref_id(snapshot: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = snapshot.get(key)
        if value:
            return str(value)
    return None


def resolve_progress_node(
    *,
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> dict[str, Any] | None:
    if plan.get("status") != PROGRESS_TREE_STATUS_READY:
        return None
    nodes = plan.get("nodes", [])
    if requested_ref:
        requested = _find_progress_node(nodes, requested_ref)
        if requested is not None:
            return requested
    current_priority = state.get("current_priority") or {}
    priority_ref = current_priority.get("progress_node_ref")
    if priority_ref:
        priority = _find_progress_node(nodes, priority_ref)
        if priority is not None:
            return priority
    leaves = _flatten_leaf_nodes(nodes)
    return leaves[0] if leaves else None


def _normalize_initial_artifacts(result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    plan_payload = result.get("progress_tree_plan") or result.get("plan")
    state_payload = result.get("progress_tree_state") or result.get("state")
    if not isinstance(plan_payload, dict):
        return _failed_artifacts(context, reason="llm_plan_missing")

    plan = _normalize_plan(
        plan_payload,
        context_digest=context["content_digest"],
        prompt_version=_metadata_value(
            result,
            plan_payload,
            "prompt_version",
            POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        ),
        schema_id=_metadata_value(result, plan_payload, "schema_id", POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID),
        schema_version=_metadata_value(
            result,
            plan_payload,
            "schema_version",
            POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
        ),
    )
    if plan["status"] != PROGRESS_TREE_STATUS_READY:
        return {
            "status": plan["status"],
            "progress_tree_plan": plan,
            "progress_tree_state": _empty_state(
                plan["status"],
                prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            ),
            "progress_percent": 0,
        }
    if not isinstance(state_payload, dict):
        state = _initial_state_fallback(
            plan,
            prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            failure_reason="llm_state_invalid_state_fallback",
        )
        return {
            "status": PROGRESS_TREE_STATUS_READY,
            "progress_tree_plan": plan,
            "progress_tree_state": state,
            "progress_percent": _progress_percent(state),
        }

    state = _normalize_state(
        state_payload,
        existing_plan=plan,
        allow_refresh_failed=False,
        prompt_version=_metadata_value(
            result,
            state_payload,
            "prompt_version",
            POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        ),
        schema_id=_metadata_value(result, state_payload, "schema_id", POLISH_PROGRESS_TREE_STATE_SCHEMA_ID),
        schema_version=_metadata_value(
            result,
            state_payload,
            "schema_version",
            POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        ),
    )
    if state["status"] != PROGRESS_TREE_STATUS_READY:
        state = _initial_state_fallback(
            plan,
            prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            failure_reason="llm_state_invalid_state_fallback",
        )
    return {
        "status": PROGRESS_TREE_STATUS_READY,
        "progress_tree_plan": plan,
        "progress_tree_state": state,
        "progress_percent": _progress_percent(state),
    }


def _normalize_plan(
    plan_payload: dict[str, Any],
    *,
    context_digest: str,
    prompt_version: str,
    schema_id: str,
    schema_version: str,
) -> dict[str, Any]:
    raw_status = plan_payload.get("status")
    if raw_status == PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT:
        return {
            "schema_id": schema_id,
            "schema_version": schema_version,
            "prompt_version": prompt_version,
            "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
            "context_digest": context_digest,
            "nodes": [],
        }
    nodes = [
        node
        for index, item in enumerate(plan_payload.get("nodes", []), start=1)
        if (node := _normalize_node(item, index=index, context_digest=context_digest)) is not None
    ]
    if not nodes:
        return {
            "schema_id": schema_id,
            "schema_version": schema_version,
            "prompt_version": prompt_version,
            "status": PROGRESS_TREE_STATUS_FAILED,
            "context_digest": context_digest,
            "nodes": [],
        }
    return {
        "schema_id": schema_id,
        "schema_version": schema_version,
        "prompt_version": prompt_version,
        "status": PROGRESS_TREE_STATUS_READY,
        "context_digest": context_digest,
        "nodes": nodes[:10],
    }


def _normalize_node(item: object, *, index: int, context_digest: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    title = truncate_text(item.get("title"), max_chars=120)
    expected_capability = truncate_text(item.get("expected_capability"), max_chars=480)
    if not title or not expected_capability:
        return None
    node_ref = truncate_text(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
    children = [
        child
        for child_index, child_item in enumerate(item.get("children", []), start=1)
        if (
            child := _normalize_node(
                child_item,
                index=(index * 100) + child_index,
                context_digest=context_digest,
            )
        )
        is not None
    ]
    return {
        "progress_node_ref": node_ref or _node_ref(context_digest, f"{index}:{title}"),
        "title": title,
        "expected_capability": expected_capability,
        "related_job_requirements": _string_list(item.get("related_job_requirements"), limit=5),
        "related_resume_evidence": _string_list(item.get("related_resume_evidence"), limit=5),
        "missing_points": _string_list(item.get("missing_points"), limit=5),
        "evidence_chunk_ids": _node_evidence_chunk_ids(item),
        "children": children[:10],
    }


def _node_evidence_chunk_ids(item: dict[str, Any]) -> list[str]:
    evidence_chunk_ids = _string_list(item.get("evidence_chunk_ids"), limit=20)
    if evidence_chunk_ids:
        return evidence_chunk_ids
    evidence = item.get("evidence")
    if isinstance(evidence, dict):
        return _string_list(evidence.get("evidence_chunk_ids"), limit=20)
    return []


def _normalize_state(
    state_payload: dict[str, Any],
    *,
    existing_plan: dict[str, Any],
    allow_refresh_failed: bool,
    prompt_version: str,
    schema_id: str,
    schema_version: str,
) -> dict[str, Any]:
    if state_payload.get("status") == PROGRESS_TREE_STATUS_REFRESH_FAILED and allow_refresh_failed:
        return _empty_state(PROGRESS_TREE_STATUS_REFRESH_FAILED, prompt_version=prompt_version)

    plan_nodes = _flatten_progress_nodes(existing_plan.get("nodes", []))
    plan_ref_set = {node["progress_node_ref"] for node in plan_nodes}
    plan_by_ref = {node["progress_node_ref"]: node for node in plan_nodes}
    node_states = []
    for item in state_payload.get("node_states", []):
        if not isinstance(item, dict):
            continue
        node_ref = truncate_text(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
        if not node_ref or node_ref not in plan_ref_set:
            continue
        node_states.append(
            {
                "progress_node_ref": node_ref,
                "status": _normalize_status(item.get("status")),
                "completed_questions_count": _bounded_int(item.get("completed_questions_count"), 0, 999),
                "latest_feedback_summary": truncate_text(item.get("latest_feedback_summary"), max_chars=480),
            }
        )

    current_priority = _normalize_priority(state_payload.get("current_priority"), plan_by_ref)
    if current_priority is None:
        current_priority = _first_non_completed_priority(node_states, plan_nodes)
    if not node_states or current_priority is None:
        return _empty_state(PROGRESS_TREE_STATUS_FAILED, prompt_version=prompt_version)

    return {
        "schema_id": schema_id,
        "schema_version": schema_version,
        "prompt_version": prompt_version,
        "status": PROGRESS_TREE_STATUS_READY,
        "node_states": node_states,
        "current_priority": current_priority,
        "updated_from_turns_count": _bounded_int(state_payload.get("updated_from_turns_count"), 0, 999),
        "progress": {
            "progress_percent": _bounded_int(
                (state_payload.get("progress") or {}).get("progress_percent")
                if isinstance(state_payload.get("progress"), dict)
                else state_payload.get("progress_percent"),
                0,
                100,
            )
        },
    }


def _normalize_priority(value: object, plan_by_ref: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    node_ref = truncate_text(value.get("progress_node_ref") or value.get("node_ref"), max_chars=120)
    if not node_ref or node_ref not in plan_by_ref:
        return None
    node = plan_by_ref[node_ref]
    return {
        "progress_node_ref": node_ref,
        "title": truncate_text(value.get("title"), max_chars=120) or node["title"],
        "expected_capability": truncate_text(value.get("expected_capability"), max_chars=480)
        or node["expected_capability"],
    }


def _first_non_completed_priority(
    node_states: list[dict[str, Any]],
    plan_nodes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    status_by_ref = {state["progress_node_ref"]: state["status"] for state in node_states}
    for node in plan_nodes:
        if status_by_ref.get(node["progress_node_ref"]) != "completed":
            return {
                "progress_node_ref": node["progress_node_ref"],
                "title": node["title"],
                "expected_capability": node["expected_capability"],
            }
    if plan_nodes:
        node = plan_nodes[-1]
        return {
            "progress_node_ref": node["progress_node_ref"],
            "title": node["title"],
            "expected_capability": node["expected_capability"],
        }
    return None


def _insufficient_artifacts(context: dict[str, Any]) -> dict[str, Any]:
    plan = {
        "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "context_digest": context["content_digest"],
        "nodes": [],
    }
    return {
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(
            PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
            prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        ),
        "progress_percent": 0,
    }


def _failed_artifacts(context: dict[str, Any], *, reason: str) -> dict[str, Any]:
    plan = {
        "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_FAILED,
        "context_digest": context["content_digest"],
        "nodes": [],
        "failure_reason": reason,
    }
    return {
        "status": PROGRESS_TREE_STATUS_FAILED,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(
            PROGRESS_TREE_STATUS_FAILED,
            prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        ),
        "progress_percent": 0,
    }


def _refresh_failed_artifacts(
    existing_plan: dict[str, Any],
    existing_state: dict[str, Any],
    *,
    reason: str,
) -> dict[str, Any]:
    if _state_matches_plan(existing_state, existing_plan):
        state = {**existing_state, "status": PROGRESS_TREE_STATUS_REFRESH_FAILED}
    else:
        state = _initial_state_fallback(
            existing_plan,
            status=PROGRESS_TREE_STATUS_REFRESH_FAILED,
            prompt_version=POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
            failure_reason=reason,
        )
    state.setdefault("schema_id", POLISH_PROGRESS_TREE_STATE_SCHEMA_ID)
    state.setdefault("schema_version", POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION)
    state.setdefault("prompt_version", POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION)
    state.setdefault("progress", {"progress_percent": _progress_percent(existing_state)})
    state["failure_reason"] = reason
    return {
        "status": PROGRESS_TREE_STATUS_REFRESH_FAILED,
        "progress_tree_plan": existing_plan,
        "progress_tree_state": state,
        "progress_percent": _progress_percent(state),
    }


def _empty_state(status: str, *, prompt_version: str = POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION) -> dict[str, Any]:
    return {
        "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        "prompt_version": prompt_version,
        "status": status,
        "node_states": [],
        "current_priority": None,
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
    }


def _initial_state_fallback(
    plan: dict[str, Any],
    *,
    status: str = PROGRESS_TREE_STATUS_READY,
    prompt_version: str,
    failure_reason: str,
) -> dict[str, Any]:
    plan_nodes = _flatten_progress_nodes(plan.get("nodes", []))
    current_priority = _fallback_priority(plan_nodes)
    return {
        "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        "prompt_version": prompt_version,
        "status": status,
        "node_states": [
            {
                "progress_node_ref": node["progress_node_ref"],
                "status": "pending",
                "completed_questions_count": 0,
                "latest_feedback_summary": None,
            }
            for node in plan_nodes
        ],
        "current_priority": current_priority,
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
        "summary": "进展树已生成，等待首次问答后刷新进度",
        "failure_reason": failure_reason,
    }


def _fallback_priority(plan_nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not plan_nodes:
        return None
    node = plan_nodes[0]
    return {
        "progress_node_ref": node["progress_node_ref"],
        "title": node["title"],
        "expected_capability": node["expected_capability"],
    }


def _state_matches_plan(state: dict[str, Any], plan: dict[str, Any]) -> bool:
    if not isinstance(state, dict):
        return False
    plan_refs = {node["progress_node_ref"] for node in _flatten_progress_nodes(plan.get("nodes", []))}
    node_states = state.get("node_states")
    if not plan_refs or not isinstance(node_states, list) or not node_states:
        return False
    state_refs = {
        item.get("progress_node_ref")
        for item in node_states
        if isinstance(item, dict) and item.get("progress_node_ref")
    }
    return bool(state_refs) and state_refs.issubset(plan_refs)


def _input_refs(context: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        ref
        for ref in (
            f"polish_session:{context['session']['session_id']}",
            f"job_version:{context['job_snapshot']['job_version_id']}",
            f"resume_version:{context['resume_snapshot']['resume_version_id']}",
        )
        if ref
    )


def _metadata_value(
    root_payload: dict[str, Any],
    nested_payload: dict[str, Any],
    key: str,
    fallback: str,
) -> str:
    for payload in (nested_payload, root_payload):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def _string_list(value: object, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = truncate_text(item, max_chars=480)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _bounded_int(value: object, lower: int, upper: int) -> int:
    if isinstance(value, bool):
        return lower
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return lower
    return max(lower, min(upper, parsed))


def _normalize_status(value: object) -> str:
    if value in {"completed", "mastered"}:
        return "completed"
    if value in {"in_progress", "active", "current"}:
        return "in_progress"
    return "pending"


def _node_ref(context_digest: str, seed: str) -> str:
    return f"progress_{sha256(f'{context_digest}:{seed}'.encode('utf-8')).hexdigest()[:16]}"


def _progress_percent(state: dict[str, Any]) -> int:
    progress = state.get("progress")
    if isinstance(progress, dict):
        return _bounded_int(progress.get("progress_percent"), 0, 100)
    return _bounded_int(state.get("progress_percent"), 0, 100)


def _flatten_progress_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_progress_nodes(node.get("children", [])))
    return result


def _flatten_leaf_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        children = node.get("children", [])
        if children:
            result.extend(_flatten_leaf_nodes(children))
        else:
            result.append(node)
    return result


def _find_progress_node(nodes: list[dict[str, Any]], progress_node_ref: str) -> dict[str, Any] | None:
    for node in _flatten_progress_nodes(nodes):
        if node.get("progress_node_ref") == progress_node_ref:
            return node
    return None


def _first_text(*values: object | None) -> str:
    for value in values:
        if isinstance(value, (list, tuple)):
            nested = _first_text(*value)
            if nested:
                return nested
            continue
        text = truncate_text(value, max_chars=320)
        if text:
            return text
    return "内容待补充"


def _latest_turn_feedback(turns: list[dict[str, Any]]) -> str | None:
    for turn in reversed(turns):
        feedback_text = turn.get("feedback_text")
        if feedback_text:
            return str(feedback_text)
    return None
