"""Phase 6 adaptive interview orchestration helpers for Polish question generation."""

from __future__ import annotations

from typing import Any

from app.application.polish.question_blueprint import (
    CLAIM_MODE_CLARIFICATION_NEEDED,
    QuestionBlueprint,
)


ADAPTIVE_INTERVIEW_ORCHESTRATION_VERSION = "polish_phase6_adaptive_interview_orchestration.v1"
ADAPTIVE_DIFFICULTY_BASIS = "progress_state_and_evaluation_history"
ADAPTIVE_QUESTION_DRIVER = "progress_state_weak_skill"
ADAPTIVE_PROGRESSION_PATH = ("weak", "medium", "strong")


def build_adaptive_interview_flow(
    *,
    progress_state: dict[str, Any],
    evaluation_history: object,
    progress_node: dict[str, Any],
    blueprint: QuestionBlueprint,
) -> dict[str, Any]:
    """Build deterministic Phase 6 orchestration metadata from ProgressState and history."""

    node_ref = _clean(progress_node.get("progress_node_ref")) or blueprint.progress_node_ref
    node_title = _clean(progress_node.get("title")) or blueprint.node_title
    expected_capability = _clean(progress_node.get("expected_capability")) or blueprint.expected_capability
    node_state = _progress_node_state(progress_state, node_ref)
    history_items = _history_items(evaluation_history, node_ref)
    signals = _dedupe(
        [
            *_string_list(node_state.get("signals")),
            *_history_signals(history_items),
        ],
        limit=20,
    )
    weak_points = _dedupe(
        [
            *_string_list(progress_node.get("missing_points")),
            *_string_list(node_state.get("weak_points")),
            *_history_points(history_items, "weak_points"),
            *_history_points(history_items, "missing_points"),
        ],
        limit=12,
    )
    skill_band = _skill_band(node_state=node_state, signals=signals, weak_points=weak_points)
    difficulty_level, difficulty_transition = _difficulty_decision(
        blueprint=blueprint,
        node_state=node_state,
        signals=signals,
        weak_points=weak_points,
    )
    learning_path = _learning_path(
        node_ref=node_ref,
        node_title=node_title,
        expected_capability=expected_capability,
        skill_band=skill_band,
        weak_points=weak_points,
    )
    session_structure = _session_structure(
        node_ref=node_ref,
        node_title=node_title,
        difficulty_level=difficulty_level,
    )
    return {
        "version": ADAPTIVE_INTERVIEW_ORCHESTRATION_VERSION,
        "question_driver": ADAPTIVE_QUESTION_DRIVER,
        "difficulty_basis": ADAPTIVE_DIFFICULTY_BASIS,
        "difficulty_level": difficulty_level,
        "difficulty_transition": difficulty_transition,
        "random_generation_allowed": False,
        "target_skill": {
            "progress_node_ref": node_ref,
            "title": node_title,
            "expected_capability": expected_capability,
            "current_band": skill_band,
            "weak_points": weak_points,
        },
        "learning_path": learning_path,
        "session_structure": session_structure,
        "next_question": {
            "generation_mode": "skill_driven",
            "target_progress_node_ref": node_ref,
            "target_skill": node_title,
            "expected_capability": expected_capability,
            "forbidden_generation_modes": ["random_question"],
        },
        "validation_markers": {
            "questions_are_skill_driven": True,
            "difficulty_adapts_to_progress": True,
            "full_interview_flow_is_structured": True,
            "no_random_generation": True,
        },
    }


def _difficulty_decision(
    *,
    blueprint: QuestionBlueprint,
    node_state: dict[str, Any],
    signals: list[str],
    weak_points: list[str],
) -> tuple[str, str]:
    if blueprint.claim_mode == CLAIM_MODE_CLARIFICATION_NEEDED:
        return "clarification", "clarify_missing_context"
    normalized_signals = {_clean(signal).lower() for signal in signals}
    status = _clean(node_state.get("status")).lower()
    if (
        "strength_detected" in normalized_signals
        or "improving" in normalized_signals
        or "improved" in normalized_signals
        or status in {"improving", "completed"}
    ):
        return "hard", "increase_for_improvement"
    if weak_points or "weakness_detected" in normalized_signals or status in {"not_started", "in_progress"}:
        return "easy", "decrease_for_foundation"
    previous = _difficulty_or_none(node_state.get("last_question_difficulty"))
    if previous is not None:
        return previous, "maintain_stable_level"
    return "medium", "maintain_stable_level"


def _skill_band(*, node_state: dict[str, Any], signals: list[str], weak_points: list[str]) -> str:
    normalized_signals = {_clean(signal).lower() for signal in signals}
    status = _clean(node_state.get("status")).lower()
    if "strength_detected" in normalized_signals or status in {"improving", "completed"}:
        return "medium"
    if weak_points or "weakness_detected" in normalized_signals or status in {"not_started", "in_progress"}:
        return "weak"
    return "medium"


def _learning_path(
    *,
    node_ref: str,
    node_title: str,
    expected_capability: str,
    skill_band: str,
    weak_points: list[str],
) -> dict[str, Any]:
    return {
        "planner_version": ADAPTIVE_INTERVIEW_ORCHESTRATION_VERSION,
        "progression_path": list(ADAPTIVE_PROGRESSION_PATH),
        "path_strategy": "weak_to_medium_to_strong",
        "skill_sequence": [
            {
                "progress_node_ref": node_ref,
                "skill": node_title,
                "expected_capability": expected_capability,
                "current_band": skill_band,
                "target_band": "medium" if skill_band == "weak" else "strong",
                "weak_points": weak_points,
            }
        ],
    }


def _session_structure(*, node_ref: str, node_title: str, difficulty_level: str) -> list[dict[str, str]]:
    return [
        {
            "stage": "warmup",
            "purpose": "confirm_foundation",
            "progress_node_ref": node_ref,
            "skill_dimension": node_title,
            "difficulty": "easy",
        },
        {
            "stage": "core_technical",
            "purpose": "evaluate_core_chain",
            "progress_node_ref": node_ref,
            "skill_dimension": node_title,
            "difficulty": "medium" if difficulty_level != "clarification" else "clarification",
        },
        {
            "stage": "deep_dive",
            "purpose": "probe_tradeoffs_and_failure_paths",
            "progress_node_ref": node_ref,
            "skill_dimension": node_title,
            "difficulty": difficulty_level,
        },
        {
            "stage": "pressure",
            "purpose": "stress_test_boundaries_and_recovery",
            "progress_node_ref": node_ref,
            "skill_dimension": node_title,
            "difficulty": "hard" if difficulty_level != "clarification" else "clarification",
        },
    ]


def _progress_node_state(progress_state: dict[str, Any], node_ref: str) -> dict[str, Any]:
    node_states = progress_state.get("node_states")
    if not isinstance(node_states, list):
        return {}
    for item in node_states:
        if isinstance(item, dict) and _clean(item.get("progress_node_ref")) == node_ref:
            return item
    return {}


def _history_items(evaluation_history: object, node_ref: str) -> list[dict[str, Any]]:
    if not isinstance(evaluation_history, list):
        return []
    result: list[dict[str, Any]] = []
    for item in evaluation_history:
        if not isinstance(item, dict):
            continue
        item_ref = _clean(item.get("progress_node_ref"))
        if item_ref and item_ref != node_ref:
            continue
        result.append(item)
    return result


def _history_signals(items: list[dict[str, Any]]) -> list[str]:
    signals: list[str] = []
    for item in items:
        signals.extend(_string_list(item.get("signals")))
        score_result = item.get("score_result") if isinstance(item.get("score_result"), dict) else {}
        signals.extend(_string_list(score_result.get("signals")))
        progress_updates = item.get("progress_updates")
        if not isinstance(progress_updates, list):
            progress_updates = score_result.get("progress_updates")
        if isinstance(progress_updates, list):
            for update in progress_updates:
                if isinstance(update, dict):
                    signal = _clean(update.get("signal"))
                    if signal:
                        signals.append(signal)
    return signals


def _history_points(items: list[dict[str, Any]], field_name: str) -> list[str]:
    points: list[str] = []
    for item in items:
        points.extend(_string_list(item.get(field_name)))
        score_result = item.get("score_result") if isinstance(item.get("score_result"), dict) else {}
        adaptive_insights = (
            score_result.get("adaptive_insights")
            if isinstance(score_result.get("adaptive_insights"), dict)
            else {}
        )
        points.extend(_string_list(adaptive_insights.get(field_name)))
    return points


def _difficulty_or_none(value: object) -> str | None:
    difficulty = _clean(value).lower()
    if difficulty in {"easy", "medium", "hard", "clarification"}:
        return difficulty
    return None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_clean(item) for item in value if _clean(item)]


def _dedupe(items: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
        if len(result) >= limit:
            break
    return result


def _clean(value: object) -> str:
    return " ".join(str(value or "").split())
