"""LLM-backed progress tree generation and state refresh."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from app.application.polish.entities import PolishSession
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
        if not has_sufficient_progress_context(context):
            return _insufficient_artifacts(context)
        if existing_plan.get("status") != PROGRESS_TREE_STATUS_READY:
            return {
                "status": existing_plan.get("status") or PROGRESS_TREE_STATUS_FAILED,
                "progress_tree_plan": existing_plan,
                "progress_tree_state": existing_state,
                "progress_percent": _progress_percent(existing_state),
            }
        if self._transport is None:
            return _refresh_failed_artifacts(existing_plan, existing_state)

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
            return _refresh_failed_artifacts(existing_plan, existing_state)

        state_payload = result.result.get("progress_tree_state") or result.result.get("state")
        if not isinstance(state_payload, dict):
            return _refresh_failed_artifacts(existing_plan, existing_state)
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
        if normalized_state["status"] == PROGRESS_TREE_STATUS_REFRESH_FAILED:
            return _refresh_failed_artifacts(existing_plan, existing_state)
        return {
            "status": PROGRESS_TREE_STATUS_READY,
            "progress_tree_plan": existing_plan,
            "progress_tree_state": normalized_state,
            "progress_percent": _progress_percent(normalized_state),
        }


def build_progress_node_question_text(
    *,
    session: PolishSession,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> str:
    node = resolve_progress_node(plan=plan, state=state, requested_ref=requested_ref)
    if node is None:
        topic = session.topic_id or "manual_topic"
        return f"请围绕 {topic} 说明一个具体案例，并补充你在当前进展节点中的关键取舍。"

    job_requirement = _first_text(
        *node.get("related_job_requirements", []),
        *context["job_snapshot"].get("requirements", []),
        *context["job_snapshot"].get("responsibilities", []),
    )
    snapshot_requirement = _first_text(*context["job_snapshot"].get("requirements", []))
    requirement_hint = (
        f"；核心岗位要求：{snapshot_requirement}"
        if snapshot_requirement and snapshot_requirement != job_requirement
        else ""
    )
    resume_evidence = _first_text(
        *node.get("related_resume_evidence", []),
        *context["resume_snapshot"].get("project_experiences", []),
        context["resume_snapshot"].get("summary"),
    )
    missing_point = _first_text(
        *node.get("missing_points", []),
        *context["match_context"].get("missing_points", []),
        "请主动说明你认为面试官最可能继续追问的薄弱点",
    )
    previous_turn = _latest_turn_feedback(context.get("turns", []))
    history_hint = f"上一轮反馈提示：{previous_turn}。" if previous_turn else ""
    return (
        f"请围绕「{node['title']}」说明一个具体案例。"
        f"岗位要求/职责依据：{job_requirement}{requirement_hint}；简历证据：{resume_evidence}。"
        f"{history_hint}"
        f"请补充你的关键取舍、结果指标、风险处理，并回应当前缺口：{missing_point}。"
    )


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
        return _failed_artifacts(context, reason="llm_state_missing")

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
        return _failed_artifacts(context, reason="llm_state_invalid")
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
        "children": children[:10],
    }


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


def _refresh_failed_artifacts(existing_plan: dict[str, Any], existing_state: dict[str, Any]) -> dict[str, Any]:
    state = {**existing_state, "status": PROGRESS_TREE_STATUS_REFRESH_FAILED}
    state.setdefault("schema_id", POLISH_PROGRESS_TREE_STATE_SCHEMA_ID)
    state.setdefault("schema_version", POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION)
    state.setdefault("prompt_version", POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION)
    state.setdefault("progress", {"progress_percent": _progress_percent(existing_state)})
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
