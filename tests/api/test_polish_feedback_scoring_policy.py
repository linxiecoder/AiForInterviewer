from __future__ import annotations

from app.domain.polish.policies import scoring_policy as semantic_scoring


def _rubric_dimension(*, dimension: str, adaptive_weight: float, progress_basis: tuple[str, ...]):
    assert hasattr(semantic_scoring, "AdaptiveRubricDimension")
    return semantic_scoring.AdaptiveRubricDimension(
        dimension=dimension,
        adaptive_weight=adaptive_weight,
        progress_basis=progress_basis,
        anchor_refs=(f"anchor_{dimension}",),
    )


def _dimension(*, dimension: str, score: float, adaptive_weight: float, rationale: str):
    assert hasattr(semantic_scoring, "SemanticScoreDimension")
    return semantic_scoring.SemanticScoreDimension(
        dimension=dimension,
        score=score,
        adaptive_weight=adaptive_weight,
        progress_focus=("progress_node_reliability",),
        rationale=rationale,
    )


def test_scoring_policy_aggregates_progress_adaptive_llm_comparator_scores_only() -> None:
    decision = semantic_scoring.ScoringPolicy.evaluate(
        semantic_scoring.ScoringInput(
            progress_state_ref="progress_node_reliability",
            adaptive_rubric_dimensions=(
                _rubric_dimension(
                    dimension="correctness",
                    adaptive_weight=0.16,
                    progress_basis=("current_priority:progress_node_reliability",),
                ),
                _rubric_dimension(
                    dimension="depth",
                    adaptive_weight=0.22,
                    progress_basis=("weak_skill:failure_recovery",),
                ),
                _rubric_dimension(
                    dimension="tradeoff_reasoning",
                    adaptive_weight=0.22,
                    progress_basis=("weak_skill:tradeoff_reasoning",),
                ),
                _rubric_dimension(
                    dimension="structure",
                    adaptive_weight=0.14,
                    progress_basis=("strong_skill:structured_reasoning",),
                ),
                _rubric_dimension(
                    dimension="engineering_awareness",
                    adaptive_weight=0.26,
                    progress_basis=("weak_skill:observability",),
                ),
            ),
            dimension_scores=(
                _dimension(dimension="correctness", score=88, adaptive_weight=0.16, rationale="方向正确"),
                _dimension(dimension="depth", score=76, adaptive_weight=0.22, rationale="展开不足"),
                _dimension(dimension="tradeoff_reasoning", score=72, adaptive_weight=0.22, rationale="取舍不足"),
                _dimension(dimension="structure", score=84, adaptive_weight=0.14, rationale="结构清晰"),
                _dimension(dimension="engineering_awareness", score=70, adaptive_weight=0.26, rationale="工程边界不足"),
            ),
            signals=("weakness_detected", "progress_update"),
            progress_updates=(
                {
                    "progress_node_ref": "progress_node_reliability",
                    "signal": "needs_focus",
                    "dimension": "engineering_awareness",
                },
            ),
        )
    )

    assert decision.score_type == "polish_answer"
    assert decision.score_value == 76.6
    assert decision.scoring_basis == "progress_adaptive_llm_comparator_v1"
    assert decision.aggregation_method == "progress_weighted_dimension_scores"
    assert decision.progress_state_ref == "progress_node_reliability"
    assert [item.adaptive_weight for item in decision.dimension_scores] == [0.16, 0.22, 0.22, 0.14, 0.26]
    assert [item.dimension for item in decision.dimension_scores] == [
        "correctness",
        "depth",
        "tradeoff_reasoning",
        "structure",
        "engineering_awareness",
    ]
    assert decision.signals == ("weakness_detected", "progress_update")


def test_scoring_policy_accepts_llm_drift_detected_signal_without_rule_score() -> None:
    decision = semantic_scoring.ScoringPolicy.evaluate(
        semantic_scoring.ScoringInput(
            progress_state_ref="progress_node_reliability",
            adaptive_rubric_dimensions=(
                _rubric_dimension(
                    dimension="correctness",
                    adaptive_weight=0.16,
                    progress_basis=("current_priority:progress_node_reliability",),
                ),
                _rubric_dimension(
                    dimension="depth",
                    adaptive_weight=0.22,
                    progress_basis=("weak_skill:failure_recovery",),
                ),
                _rubric_dimension(
                    dimension="tradeoff_reasoning",
                    adaptive_weight=0.22,
                    progress_basis=("weak_skill:tradeoff_reasoning",),
                ),
                _rubric_dimension(
                    dimension="structure",
                    adaptive_weight=0.14,
                    progress_basis=("strong_skill:structured_reasoning",),
                ),
                _rubric_dimension(
                    dimension="engineering_awareness",
                    adaptive_weight=0.26,
                    progress_basis=("weak_skill:observability",),
                ),
            ),
            dimension_scores=(
                _dimension(dimension="correctness", score=88, adaptive_weight=0.16, rationale="方向正确"),
                _dimension(dimension="depth", score=76, adaptive_weight=0.22, rationale="展开不足"),
                _dimension(dimension="tradeoff_reasoning", score=72, adaptive_weight=0.22, rationale="取舍不足"),
                _dimension(dimension="structure", score=84, adaptive_weight=0.14, rationale="结构清晰"),
                _dimension(dimension="engineering_awareness", score=70, adaptive_weight=0.26, rationale="工程边界不足"),
            ),
            signals=("weakness_detected", "drift_detected", "progress_update"),
            progress_updates=(
                {
                    "progress_node_ref": "progress_node_reliability",
                    "signal": "needs_focus",
                    "dimension": "engineering_awareness",
                },
            ),
        )
    )

    assert decision.score_value == 76.6
    assert decision.signals == ("weakness_detected", "drift_detected", "progress_update")
    assert "rule_based_scoring" not in decision.warnings


def test_scoring_policy_rejects_missing_semantic_dimensions_without_fallback_score() -> None:
    decision = semantic_scoring.ScoringPolicy.evaluate(
        semantic_scoring.ScoringInput(
            progress_state_ref="progress_node_reliability",
            adaptive_rubric_dimensions=(
                _rubric_dimension(
                    dimension="correctness",
                    adaptive_weight=1.0,
                    progress_basis=("current_priority:progress_node_reliability",),
                ),
            ),
            dimension_scores=(
                _dimension(dimension="correctness", score=88, adaptive_weight=1.0, rationale="方向正确"),
            ),
            signals=("progress_update",),
            progress_updates=(
                {
                    "progress_node_ref": "progress_node_reliability",
                    "signal": "needs_focus",
                    "dimension": "correctness",
                },
            ),
        )
    )

    assert decision.score_value is None
    assert decision.validation_errors == (
        "adaptive_rubric_dimensions_incomplete",
        "score_result_dimension_scores_incomplete",
    )
    assert decision.warnings == ()


def test_scoring_policy_rejects_static_score_without_progress_adaptive_rubric() -> None:
    decision = semantic_scoring.ScoringPolicy.evaluate(
        semantic_scoring.ScoringInput(
            dimension_scores=(
                _dimension(dimension="correctness", score=88, adaptive_weight=1.0, rationale="方向正确"),
            ),
            signals=("progress_update",),
        )
    )

    assert decision.score_value is None
    assert decision.validation_errors == (
        "progress_state_ref_required",
        "adaptive_rubric_required",
        "progress_updates_required",
        "adaptive_rubric_dimensions_incomplete",
        "score_result_dimension_scores_incomplete",
    )
