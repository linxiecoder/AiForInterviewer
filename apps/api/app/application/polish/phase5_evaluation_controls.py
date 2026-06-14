"""Phase 5 stability, calibration, and learning controls for Polish feedback."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE5_EVALUATION_CONTROLS_VERSION = "polish_phase5_evaluation_controls.v1"
PHASE5_EVALUATION_PIPELINE = (
    "evaluate",
    "stability_layer",
    "calibration",
    "learning_control",
    "normalized_progress_update",
)


def apply_phase5_evaluation_controls(
    payload: dict[str, Any],
    *,
    secondary_candidate_payload: dict[str, Any] | None = None,
    secondary_validation_errors: tuple[str, ...] = (),
    secondary_low_confidence_flags: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Attach Phase 5 controls without replacing the Phase 4 scoring contract."""

    result = deepcopy(payload)
    score_result = result.get("score_result")
    if not isinstance(score_result, dict):
        return result

    secondary_score_result = (
        secondary_candidate_payload.get("score_result")
        if isinstance(secondary_candidate_payload, dict)
        and isinstance(secondary_candidate_payload.get("score_result"), dict)
        else None
    )
    controlled_score_result = _controlled_score_result(
        score_result,
        secondary_score_result=secondary_score_result,
        secondary_validation_errors=secondary_validation_errors,
    )
    result["score_result"] = controlled_score_result

    flags = _string_list(result.get("low_confidence_flags"), max_items=40, max_item_chars=160)
    flags.extend(_string_list(secondary_low_confidence_flags, max_items=20, max_item_chars=160))
    if controlled_score_result.get("stability_layer", {}).get("drift_detected"):
        flags.append("evaluation_drift_detected")
    if secondary_validation_errors:
        flags.append("evaluation_secondary_pass_invalid")
    result["low_confidence_flags"] = list(dict.fromkeys(flag for flag in flags if flag))

    metadata = result.get("feedback_metadata")
    metadata = dict(metadata) if isinstance(metadata, dict) else {}
    metadata["phase5_controls_version"] = PHASE5_EVALUATION_CONTROLS_VERSION
    metadata["phase5_pipeline"] = list(PHASE5_EVALUATION_PIPELINE)
    metadata["phase5_secondary_pass_valid"] = secondary_score_result is not None
    if secondary_validation_errors:
        metadata["phase5_secondary_validation_errors"] = list(secondary_validation_errors)
    result["feedback_metadata"] = metadata
    return result


def _controlled_score_result(
    primary: dict[str, Any],
    *,
    secondary_score_result: dict[str, Any] | None,
    secondary_validation_errors: tuple[str, ...],
) -> dict[str, Any]:
    controlled = deepcopy(primary)
    primary_score = _number(primary.get("score_value"))
    secondary_score = _number(secondary_score_result.get("score_value")) if secondary_score_result else None
    if secondary_score_result is not None and primary_score is not None and secondary_score is not None:
        controlled = _stabilize_dual_pass_score(primary, secondary_score_result)

    secondary_signals = (
        _string_list(secondary_score_result.get("signals"), max_items=20, max_item_chars=80)
        if secondary_score_result is not None
        else []
    )
    signals = _dedupe_strings(
        [
            *_string_list(primary.get("signals"), max_items=20, max_item_chars=80),
            *secondary_signals,
        ],
        limit=20,
    )
    if signals:
        controlled["signals"] = signals
    controlled["progress_updates"] = _controlled_progress_updates(
        _dict_list(controlled.get("progress_updates")),
        learning_rate=_learning_rate(signals),
    )

    score_passes = [score for score in (primary_score, secondary_score) if score is not None]
    numeric_variance_detected = len(score_passes) == 2 and round(abs(score_passes[0] - score_passes[1]), 6) > 0
    drift_detected = "drift_detected" in signals or numeric_variance_detected
    controlled["stability_layer"] = {
        "version": "phase5_llm_stability_layer.v1",
        "dual_pass_judging": secondary_score_result is not None,
        "pass_count": len(score_passes) if secondary_score_result is not None else 1,
        "score_value_passes": [round(score, 2) for score in score_passes],
        "score_value_delta": round(abs(score_passes[0] - score_passes[1]), 2) if len(score_passes) == 2 else 0,
        "output_normalization": "llm_dual_pass_dimension_mean" if secondary_score_result is not None else "single_pass",
        "variance_bounded": _variance_is_bounded(controlled.get("score_value"), score_passes),
        "numeric_variance_detected": numeric_variance_detected,
        "drift_detected": drift_detected,
        "secondary_validation_errors": list(secondary_validation_errors),
    }
    controlled["calibration_layer"] = _calibration_layer(controlled)
    controlled["learning_control"] = _learning_control(controlled)
    return controlled


def _stabilize_dual_pass_score(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    stable = deepcopy(primary)
    secondary_by_dimension = {
        _clean(item.get("dimension"), max_chars=80): item
        for item in _dict_list(secondary.get("dimension_scores"))
        if _clean(item.get("dimension"), max_chars=80)
    }
    stable_dimensions: list[dict[str, Any]] = []
    for item in _dict_list(primary.get("dimension_scores")):
        dimension = _clean(item.get("dimension"), max_chars=80)
        stable_item = dict(item)
        primary_score = _number(item.get("score"))
        secondary_score = _number(secondary_by_dimension.get(dimension, {}).get("score"))
        if primary_score is not None and secondary_score is not None:
            stable_item["score"] = round((primary_score + secondary_score) / 2, 2)
        stable_dimensions.append(stable_item)
    if stable_dimensions:
        stable["dimension_scores"] = stable_dimensions
        score_value = _weighted_dimension_score(stable_dimensions)
        if score_value is not None:
            stable["score_value"] = score_value
    stable["progress_updates"] = _dedupe_progress_updates(
        [
            *_dict_list(primary.get("progress_updates")),
            *_dict_list(secondary.get("progress_updates")),
        ]
    )
    return stable


def _calibration_layer(score_result: dict[str, Any]) -> dict[str, Any]:
    dimension_scores = [_number(item.get("score")) for item in _dict_list(score_result.get("dimension_scores"))]
    scores = [score for score in dimension_scores if score is not None]
    distribution: dict[str, float | int | None] = {
        "dimension_count": len(scores),
        "min": round(min(scores), 2) if scores else None,
        "max": round(max(scores), 2) if scores else None,
        "mean": round(sum(scores) / len(scores), 2) if scores else None,
    }
    return {
        "version": "phase5_calibration_layer.v1",
        "anchor_re_alignment": {
            "anchor_set_id": _clean(score_result.get("anchor_set_id"), max_chars=120),
            "status": "tracked",
        },
        "score_distribution": distribution,
        "periodic_recalibration": {"status": "observed", "basis": "score_distribution_monitoring"},
        "semantic_adjustment_applied": False,
    }


def _learning_control(score_result: dict[str, Any]) -> dict[str, Any]:
    signals = _string_list(score_result.get("signals"), max_items=20, max_item_chars=80)
    dimensions = _dict_list(score_result.get("dimension_scores"))
    weights = [_number(item.get("adaptive_weight")) for item in dimensions]
    valid_weights = [weight for weight in weights if weight is not None]
    progress_updates = _dict_list(score_result.get("progress_updates"))
    return {
        "version": "phase5_learning_controller.v1",
        "learning_rate": _learning_rate(signals),
        "learning_rate_basis": "llm_signal_count",
        "skill_weight_balance": {
            "dimension_count": len(valid_weights),
            "weight_sum": round(sum(valid_weights), 6) if valid_weights else 0,
        },
        "oscillation_dampening": {
            "basis": "metadata_only_until_persistent_history_available",
            "applied_to_scoring": False,
        },
        "controlled_progress_update_count": len(progress_updates),
        "hardcoded_thresholds_used": False,
    }


def _weighted_dimension_score(dimensions: list[dict[str, Any]]) -> float | None:
    weighted_sum = 0.0
    total_weight = 0.0
    for item in dimensions:
        score = _number(item.get("score"))
        weight = _number(item.get("adaptive_weight"))
        if score is None or weight is None or weight <= 0:
            continue
        weighted_sum += score * weight
        total_weight += weight
    if total_weight <= 0:
        return None
    return round(weighted_sum / total_weight, 2)


def _variance_is_bounded(score_value: object, score_passes: list[float]) -> bool:
    score = _number(score_value)
    if score is None or not score_passes:
        return False
    return min(score_passes) <= score <= max(score_passes)


def _dedupe_progress_updates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        node_ref = _clean(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
        signal = _clean(item.get("signal"), max_chars=80)
        dimension = _clean(item.get("dimension"), max_chars=80)
        key = (node_ref, signal, dimension)
        if not node_ref or not signal or key in seen:
            continue
        seen.add(key)
        normalized = dict(item)
        normalized["progress_node_ref"] = node_ref
        normalized["signal"] = signal
        if dimension:
            normalized["dimension"] = dimension
        result.append(normalized)
    return result


def _controlled_progress_updates(items: list[dict[str, Any]], *, learning_rate: float) -> list[dict[str, Any]]:
    controlled: list[dict[str, Any]] = []
    for item in items:
        update = dict(item)
        update["learning_rate"] = learning_rate
        update["learning_rate_basis"] = "llm_signal_count"
        controlled.append(update)
    return controlled


def _learning_rate(signals: list[str]) -> float:
    signal_count = len(signals) or 1
    return round(1 / signal_count, 6)


def _dedupe_strings(items: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
        if len(result) >= limit:
            break
    return result


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _string_list(value: object, *, max_items: int, max_item_chars: int) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value:
        text = _clean(item, max_chars=max_item_chars)
        if text and text not in result:
            result.append(text)
        if len(result) >= max_items:
            break
    return result


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _clean(value: object, *, max_chars: int) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
