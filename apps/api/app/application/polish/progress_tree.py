"""LLM-backed progress tree generation and state refresh."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from app.application.polish.progress_context import has_sufficient_progress_context, truncate_text
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_STATE_CONTRACT_IDS,
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
    build_progress_tree_state_refresh_prompt,
)
from app.application.polish.progress_tree_v2 import PolishProgressTreeQualityFirstPlanner
from app.application.polish.progress_v2_prompts import (
    POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
)
from app.application.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.application.llm.ports import LlmTransport
from app.application.llm.types import LlmTransportRequest


PROGRESS_TREE_STATUS_READY = "ready"
PROGRESS_TREE_STATUS_FAILED = "failed"
PROGRESS_TREE_STATUS_REFRESH_FAILED = "refresh_failed"
PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT = "insufficient_context"
PROGRESS_TREE_STATUS_PENDING = "pending"
PROGRESS_TREE_STATUS_GENERATING = "generating"
PENDING_FEEDBACK_TEXT = "本轮反馈尚未生成"


class PolishProgressTreeLlmService:
    """Call the configured LLM transport and normalize progress tree outputs."""

    def __init__(self, transport: LlmTransport | None) -> None:
        self._transport = transport

    def generate_initial(self, context: dict[str, Any]) -> dict[str, Any]:
        return PolishProgressTreeQualityFirstPlanner(self._transport).generate_initial(context)

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
        if existing_plan.get("schema_id") in {
            "polish_progress_tree_grounded_plan_v2",
            "polish_progress_quality_first_menu_v1",
        }:
            if _state_matches_plan(existing_state, existing_plan):
                state = {
                    **existing_state,
                    "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
                    "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
                    "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
                    "status": PROGRESS_TREE_STATUS_READY,
                }
            else:
                state = _initial_state_fallback(
                    existing_plan,
                    prompt_version=POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
                    failure_reason="v2_local_state_refresh",
                )
            state = _apply_turn_progress_to_state(state, context, existing_plan=existing_plan)
            return {
                "status": PROGRESS_TREE_STATUS_READY,
                "progress_tree_plan": existing_plan,
                "progress_tree_state": state,
                "progress_percent": _progress_percent(state),
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
        normalized_state = _apply_turn_progress_to_state(
            normalized_state,
            context,
            existing_plan=existing_plan,
        )
        return {
            "status": PROGRESS_TREE_STATUS_READY,
            "progress_tree_plan": existing_plan,
            "progress_tree_state": normalized_state,
            "progress_percent": _progress_percent(normalized_state),
        }


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
    if not plan_nodes:
        return _empty_state(PROGRESS_TREE_STATUS_FAILED, prompt_version=prompt_version)
    plan_by_ref = {node["progress_node_ref"]: node for node in plan_nodes}
    node_states = _complete_node_states_for_plan(
        existing_plan.get("nodes", []),
        state_payload.get("node_states", []),
    )
    node_states = _rollup_node_states(existing_plan.get("nodes", []), node_states)

    current_priority = _normalize_priority(state_payload.get("current_priority"), plan_by_ref)
    if current_priority is None:
        current_priority = _first_non_completed_priority(
            node_states,
            _flatten_leaf_nodes(existing_plan.get("nodes", [])) or plan_nodes,
        )
    if current_priority is None:
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
            "progress_percent": _progress_percent_from_leaf_nodes(
                _flatten_leaf_nodes(existing_plan.get("nodes", [])) or plan_nodes,
                node_states,
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
        "schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "context_digest": context["content_digest"],
        "nodes": [],
    }
    return {
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(
            PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
            prompt_version=POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
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
    current_priority = _fallback_priority(_flatten_leaf_nodes(plan.get("nodes", [])) or plan_nodes)
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


def _apply_turn_progress_to_state(
    state: dict[str, Any],
    context: dict[str, Any],
    *,
    existing_plan: dict[str, Any],
) -> dict[str, Any]:
    plan_nodes = existing_plan.get("nodes", [])
    flat_plan_nodes = _flatten_progress_nodes(plan_nodes)
    if not flat_plan_nodes:
        return state
    node_states = _complete_node_states_for_plan(plan_nodes, state.get("node_states", []))
    if not node_states:
        return state
    plan_ref_set = {node["progress_node_ref"] for node in flat_plan_nodes}
    turn_updates = _turn_progress_updates(context, node_states, plan_ref_set)
    if not turn_updates:
        rolled_node_states = _rollup_node_states(plan_nodes, node_states)
        return {
            **state,
            "node_states": rolled_node_states,
            "summary": "v2_local_state_refresh",
            "progress": {
                "progress_percent": _progress_percent_from_leaf_nodes(
                    _flatten_leaf_nodes(plan_nodes) or flat_plan_nodes,
                    rolled_node_states,
                )
            },
        }

    completed_counts_by_ref: dict[str, int] = {}
    latest_feedback_by_ref: dict[str, str] = {}
    in_progress_refs: set[str] = set()
    completed_refs: set[str] = set()
    latest_turn_ref: str | None = None
    for update in turn_updates:
        node_ref = update["progress_node_ref"]
        latest_turn_ref = node_ref
        if update["status"] == "completed":
            completed_refs.add(node_ref)
            in_progress_refs.discard(node_ref)
            completed_counts_by_ref[node_ref] = completed_counts_by_ref.get(node_ref, 0) + 1
        elif node_ref not in completed_refs:
            in_progress_refs.add(node_ref)
        feedback_summary = update.get("latest_feedback_summary")
        if feedback_summary:
            latest_feedback_by_ref[node_ref] = feedback_summary

    updated_node_states = []
    for item in node_states:
        updated = {**item}
        node_ref = str(updated.get("progress_node_ref") or "")
        if node_ref in completed_refs:
            updated["status"] = "completed"
            updated["completed_questions_count"] = max(
                _bounded_int(updated.get("completed_questions_count"), 0, 999),
                completed_counts_by_ref.get(node_ref, 1),
            )
        elif node_ref in in_progress_refs:
            updated["status"] = "in_progress"
        if node_ref in latest_feedback_by_ref:
            updated["latest_feedback_summary"] = latest_feedback_by_ref[node_ref]
        updated_node_states.append(updated)

    rolled_node_states = _rollup_node_states(plan_nodes, updated_node_states)
    current_priority = _current_priority_from_turns(
        latest_turn_ref=latest_turn_ref,
        updated_node_states=rolled_node_states,
        existing_state=state,
        existing_plan=existing_plan,
    )
    return {
        **state,
        "node_states": rolled_node_states,
        "current_priority": current_priority,
        "updated_from_turns_count": len(turn_updates),
        "summary": "v2_local_state_refresh",
        "progress": {
            "progress_percent": _progress_percent_from_leaf_nodes(
                _flatten_leaf_nodes(plan_nodes) or flat_plan_nodes,
                rolled_node_states,
            )
        },
    }


def _complete_node_states_for_plan(
    plan_nodes: list[dict[str, Any]],
    raw_node_states: object,
) -> list[dict[str, Any]]:
    flat_plan_nodes = _flatten_progress_nodes(plan_nodes)
    plan_ref_set = {node["progress_node_ref"] for node in flat_plan_nodes}
    raw_by_ref: dict[str, dict[str, Any]] = {}
    if isinstance(raw_node_states, list):
        for item in raw_node_states:
            if not isinstance(item, dict):
                continue
            node_ref = truncate_text(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
            if node_ref and node_ref in plan_ref_set:
                raw_by_ref[node_ref] = item
    return [
        {
            "progress_node_ref": node["progress_node_ref"],
            "status": _normalize_status(raw_by_ref.get(node["progress_node_ref"], {}).get("status")),
            "completed_questions_count": _bounded_int(
                raw_by_ref.get(node["progress_node_ref"], {}).get("completed_questions_count"),
                0,
                999,
            ),
            "latest_feedback_summary": truncate_text(
                raw_by_ref.get(node["progress_node_ref"], {}).get("latest_feedback_summary"),
                max_chars=480,
            ),
        }
        for node in flat_plan_nodes
    ]


def _rollup_node_states(
    plan_nodes: list[dict[str, Any]],
    node_states: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    state_by_ref = {
        str(item.get("progress_node_ref")): {**item}
        for item in node_states
        if item.get("progress_node_ref")
    }

    def rollup(node: dict[str, Any]) -> dict[str, Any]:
        node_ref = node["progress_node_ref"]
        current = state_by_ref.setdefault(
            node_ref,
            {
                "progress_node_ref": node_ref,
                "status": "pending",
                "completed_questions_count": 0,
                "latest_feedback_summary": None,
            },
        )
        children = [child for child in node.get("children", []) if isinstance(child, dict)]
        if not children:
            current["status"] = _normalize_status(current.get("status"))
            current["completed_questions_count"] = _bounded_int(current.get("completed_questions_count"), 0, 999)
            current["latest_feedback_summary"] = truncate_text(current.get("latest_feedback_summary"), max_chars=480)
            return current

        child_states = [rollup(child) for child in children]
        child_statuses = [_normalize_status(child.get("status")) for child in child_states]
        own_status = _normalize_status(current.get("status"))
        has_started = own_status in {"completed", "in_progress"} or any(status != "pending" for status in child_statuses)
        if child_statuses and all(status == "completed" for status in child_statuses) and own_status != "in_progress":
            current["status"] = "completed"
        elif has_started:
            current["status"] = "in_progress"
        else:
            current["status"] = "pending"
        current["completed_questions_count"] = max(
            _bounded_int(current.get("completed_questions_count"), 0, 999),
            sum(_bounded_int(child.get("completed_questions_count"), 0, 999) for child in child_states),
        )
        latest_child_feedback = next(
            (
                truncate_text(child.get("latest_feedback_summary"), max_chars=480)
                for child in reversed(child_states)
                if truncate_text(child.get("latest_feedback_summary"), max_chars=480)
            ),
            None,
        )
        current["latest_feedback_summary"] = latest_child_feedback or truncate_text(
            current.get("latest_feedback_summary"),
            max_chars=480,
        )
        return current

    for node in plan_nodes:
        rollup(node)
    return [
        state_by_ref[node["progress_node_ref"]]
        for node in _flatten_progress_nodes(plan_nodes)
        if node.get("progress_node_ref") in state_by_ref
    ]


def _progress_percent_from_leaf_nodes(
    leaf_nodes: list[dict[str, Any]],
    node_states: list[dict[str, Any]],
) -> int:
    if not leaf_nodes:
        return 0
    status_by_ref = {
        str(item.get("progress_node_ref")): _normalize_status(item.get("status"))
        for item in node_states
        if item.get("progress_node_ref")
    }
    completed_leaf_count = sum(
        1 for node in leaf_nodes if status_by_ref.get(node["progress_node_ref"]) == "completed"
    )
    return _bounded_int(round(completed_leaf_count * 100 / len(leaf_nodes)), 0, 100)


def _turn_progress_updates(
    context: dict[str, Any],
    node_states: list[dict[str, Any]],
    plan_ref_set: set[str],
) -> list[dict[str, str]]:
    turns = context.get("turns")
    if not isinstance(turns, list):
        return []
    existing_refs = {
        str(item.get("progress_node_ref"))
        for item in node_states
        if isinstance(item.get("progress_node_ref"), str) and item.get("progress_node_ref")
    }
    updates: list[dict[str, str]] = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        node_ref = truncate_text(turn.get("progress_node_ref"), max_chars=120)
        if not node_ref or node_ref not in existing_refs or node_ref not in plan_ref_set:
            continue
        status = "completed" if _turn_has_feedback(turn) else "in_progress"
        feedback_summary = _latest_turn_feedback(turn) if status == "completed" else None
        update: dict[str, str] = {
            "progress_node_ref": node_ref,
            "status": status,
        }
        if feedback_summary:
            update["latest_feedback_summary"] = truncate_text(feedback_summary, max_chars=480) or feedback_summary
        updates.append(update)
    return updates


def _turn_has_feedback(turn: dict[str, Any]) -> bool:
    if turn.get("feedback_id") or turn.get("feedback_created_at") or turn.get("score_result_id"):
        return True
    feedback_text = truncate_text(turn.get("feedback_text"), max_chars=640)
    if feedback_text and feedback_text != PENDING_FEEDBACK_TEXT:
        return True
    answers = turn.get("answers")
    if not isinstance(answers, list):
        return False
    return any(isinstance(answer, dict) and _answer_has_feedback(answer) for answer in answers)


def _answer_has_feedback(answer: dict[str, Any]) -> bool:
    if answer.get("feedback_id") or answer.get("feedback_created_at") or answer.get("score_result_id"):
        return True
    feedback_text = truncate_text(answer.get("feedback_text"), max_chars=640)
    return bool(feedback_text and feedback_text != PENDING_FEEDBACK_TEXT)


def _current_priority_from_turns(
    *,
    latest_turn_ref: str | None,
    updated_node_states: list[dict[str, Any]],
    existing_state: dict[str, Any],
    existing_plan: dict[str, Any],
) -> dict[str, Any] | None:
    plan_nodes = _flatten_progress_nodes(existing_plan.get("nodes", []))
    leaf_plan_nodes = _flatten_leaf_nodes(existing_plan.get("nodes", [])) or plan_nodes
    plan_by_ref = {node["progress_node_ref"]: node for node in plan_nodes}
    if latest_turn_ref:
        priority = _priority_for_ref(latest_turn_ref, plan_by_ref, existing_state)
        if priority is not None:
            return priority
    return _first_non_completed_priority(updated_node_states, leaf_plan_nodes)


def _priority_for_ref(
    node_ref: str,
    plan_by_ref: dict[str, dict[str, Any]],
    existing_state: dict[str, Any],
) -> dict[str, Any] | None:
    node = plan_by_ref.get(node_ref)
    if node is None:
        return None
    current_priority = existing_state.get("current_priority")
    if isinstance(current_priority, dict) and current_priority.get("progress_node_ref") == node_ref:
        return {
            "progress_node_ref": node_ref,
            "title": truncate_text(current_priority.get("title"), max_chars=120) or node["title"],
            "expected_capability": truncate_text(current_priority.get("expected_capability"), max_chars=480)
            or node["expected_capability"],
        }
    return {
        "progress_node_ref": node_ref,
        "title": node["title"],
        "expected_capability": node["expected_capability"],
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


def _latest_turn_feedback(turns: list[dict[str, Any]] | dict[str, Any]) -> str | None:
    turn_list = [turns] if isinstance(turns, dict) else turns
    for turn in reversed(turn_list):
        if not isinstance(turn, dict):
            continue
        feedback_text = truncate_text(turn.get("feedback_text"), max_chars=640)
        if feedback_text and feedback_text != PENDING_FEEDBACK_TEXT:
            return feedback_text
        answers = turn.get("answers")
        if not isinstance(answers, list):
            continue
        for answer in reversed(answers):
            if not isinstance(answer, dict):
                continue
            answer_feedback = truncate_text(answer.get("feedback_text"), max_chars=640)
            if answer_feedback and answer_feedback != PENDING_FEEDBACK_TEXT:
                return answer_feedback
    return None
