from __future__ import annotations

from typing import Any

import app.application.polish.feedback_rules as feedback_rules


def test_expected_points_builder_constructs_points_from_feedback_context() -> None:
    from app.application.polish.context.expected_points import ExpectedPointsBuilder

    points = ExpectedPointsBuilder().build(
        {
            "question_metadata": {"expected_answer_dimensions": ["幂等设计", "失败补偿"]},
            "progress_node_snapshot": {
                "expected_capability": "说明支付链路一致性。",
                "missing_points": ["上线验证指标"],
            },
            "canonical_project_assets": {
                "available": True,
                "items": [
                    {
                        "asset_id": "asset_payment",
                        "status": "asset_confirmed",
                        "summary": "支付链路包含 Redis 幂等键和补偿任务。",
                    }
                ],
            },
            "job_snapshot": {"requirements": ["支付可靠性经验"]},
        }
    )

    assert points == [
        "幂等设计",
        "失败补偿",
        "说明支付链路一致性。",
        "上线验证指标",
        "支付链路包含 Redis 幂等键和补偿任务。",
        "支付可靠性经验",
    ]


def test_feedback_rules_delegate_expected_points_to_context_builder(monkeypatch: Any) -> None:
    calls: list[object] = []

    class _RecordingExpectedPointsBuilder:
        def build(self, context: object) -> list[str]:
            calls.append(context)
            return ["forced_expected_point"]

    monkeypatch.setattr(feedback_rules, "ExpectedPointsBuilder", _RecordingExpectedPointsBuilder)

    payload = {
        "score_result": {"score_value": 80},
        "loss_points": [],
        "next_recommended_actions": ["continue_same_question"],
        "project_asset_update_candidates": [],
    }
    result = feedback_rules.apply_feedback_core_rules(
        payload,
        {
            "answer_text": "我只说明了 MQ 解耦。",
            "canonical_project_assets": {"available": False, "items": []},
            "same_question_answers": [],
        },
    )

    assert calls
    assert result["answer_coverage"]["expected_points"] == ["forced_expected_point"]
