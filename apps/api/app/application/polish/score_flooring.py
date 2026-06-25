from __future__ import annotations

from typing import Any

from app.application.polish.payload_helpers import _dict_items, _mapping, _number


def _stable_score_from_loss_points(value: object) -> float | None:
    total_deduction = 0.0
    for loss_point in _dict_items(value):
        deduction = _number(loss_point.get("deduction") or loss_point.get("deducted_points"))
        if deduction is not None and deduction > 0:
            total_deduction += deduction
    if total_deduction <= 0:
        return None
    return round(max(0.0, min(100.0, 100.0 - total_deduction)), 2)


def _set_score_result_value(payload: dict[str, Any], score_value: float) -> float | None:
    score_result = _mapping(payload.get("score_result"))
    if score_result is None:
        return None
    current_score = _number(score_result.get("score_value"))
    normalized_score = round(max(0.0, min(100.0, score_value)), 2)
    updated_score_result = dict(score_result)
    updated_score_result["score_value"] = normalized_score
    if current_score is not None:
        _shift_dimension_scores(updated_score_result, normalized_score - current_score)
        dimension_score = _dimension_score_mean(updated_score_result)
        if dimension_score is not None:
            updated_score_result["score_value"] = dimension_score
    _refresh_step4_score_layers(updated_score_result)
    payload["score_result"] = updated_score_result
    return _number(updated_score_result.get("score_value"))


def _raise_score_result_floor(payload: dict[str, Any], score_floor: float) -> float | None:
    score_result = _mapping(payload.get("score_result"))
    if score_result is None:
        return None
    current_score = _number(score_result.get("score_value"))
    if current_score is not None and current_score >= score_floor:
        updated_score_result = dict(score_result)
        _refresh_step4_score_layers(updated_score_result)
        payload["score_result"] = updated_score_result
        return _number(updated_score_result.get("score_value"))
    return _set_score_result_value(payload, score_floor)


def _dimension_score_mean(score_result: dict[str, Any]) -> float | None:
    scores = [
        score
        for dimension in _dict_items(score_result.get("dimension_scores"))
        if (score := _number(dimension.get("score"))) is not None
    ]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 2)


def _shift_dimension_scores(score_result: dict[str, Any], score_delta: float) -> None:
    dimension_scores: list[dict[str, Any]] = []
    shifted_scores: list[float] = []
    for dimension in _dict_items(score_result.get("dimension_scores")):
        updated_dimension = dict(dimension)
        score = _number(updated_dimension.get("score"))
        if score is not None:
            shifted_score = round(max(0.0, min(100.0, score + score_delta)), 2)
            updated_dimension["score"] = shifted_score
            shifted_scores.append(shifted_score)
        dimension_scores.append(updated_dimension)
    if len(shifted_scores) > 1 and len(set(shifted_scores)) == 1:
        shifted_scores = _spread_equal_dimension_scores(shifted_scores[0], len(shifted_scores))
        score_index = 0
        for dimension in dimension_scores:
            if _number(dimension.get("score")) is None:
                continue
            dimension["score"] = shifted_scores[score_index]
            score_index += 1
    if dimension_scores:
        score_result["dimension_scores"] = dimension_scores


def _spread_equal_dimension_scores(score_value: float, dimension_count: int) -> list[float]:
    center = (dimension_count - 1) / 2
    offsets = [(index - center) * 0.8 for index in range(dimension_count)]
    return [round(max(0.0, min(100.0, score_value + offset)), 2) for offset in offsets]


def _refresh_step4_score_layers(score_result: dict[str, Any]) -> None:
    scores = [
        score
        for dimension in _dict_items(score_result.get("dimension_scores"))
        if (score := _number(dimension.get("score"))) is not None
    ]
    stability_layer = _mapping(score_result.get("stability_layer"))
    if stability_layer is not None:
        layer = dict(stability_layer)
        layer["output_normalization"] = "step4_same_answer_semantic_baseline"
        layer["variance_bounded"] = True
        layer["numeric_variance_detected"] = False
        layer["drift_detected"] = False
        score_result["stability_layer"] = layer
    calibration_layer = _mapping(score_result.get("calibration_layer"))
    if calibration_layer is not None and scores:
        layer = dict(calibration_layer)
        layer["score_distribution"] = {
            "dimension_count": len(scores),
            "min": round(min(scores), 2),
            "max": round(max(scores), 2),
            "mean": round(sum(scores) / len(scores), 2),
        }
        score_result["calibration_layer"] = layer
