from __future__ import annotations

from app.application.ai_runtime.business_graphs.polish_question_graph import question_candidate_quality_gate


def test_unsupported_inventory_entity_blocked() -> None:
    gate = question_candidate_quality_gate(
        _candidate(
            "请围绕支付回调和搜索排序链路回答。",
            allowed_entities=("支付回调",),
            forbidden_entities=("搜索排序",),
        )
    )

    assert gate["passed"] is False
    assert "cross_evidence_scenario_mixing" in gate["blocking_reasons"]


def test_unsupported_1gb_log_entity_blocked() -> None:
    gate = question_candidate_quality_gate(
        _candidate(
            "请说明你如何同时处理网关限流和客户端渲染性能。",
            allowed_entities=("网关限流",),
            forbidden_entities=("客户端渲染性能",),
        )
    )

    assert gate["passed"] is False
    assert "cross_evidence_scenario_mixing" in gate["blocking_reasons"]


def test_cross_evidence_mixing_blocked() -> None:
    gate = question_candidate_quality_gate(
        _candidate(
            "请围绕结算对账和搜索排序讲清一致性。",
            allowed_entities=("结算对账",),
            forbidden_entities=("搜索排序",),
        )
    )

    assert gate["passed"] is False
    assert "cross_evidence_scenario_mixing" in gate["blocking_reasons"]


def test_raw_payload_leak_blocked() -> None:
    candidate = _candidate("请围绕订单履约回答。", allowed_entities=("订单履约",))
    candidate["raw_prompt"] = "hidden prompt"
    candidate["provider_payload"] = {"body": "hidden provider body"}

    gate = question_candidate_quality_gate(candidate)

    assert gate["passed"] is False
    assert "raw_payload_leak" in gate["blocking_reasons"]


def test_jd_gap_claimed_as_project_experience_blocked() -> None:
    gate = question_candidate_quality_gate(
        _candidate(
            "请说明你负责过的高并发接口设计、限流降级和压测链路。",
            allowed_entities=("高并发接口设计", "限流降级", "压测"),
            scenario_mode="job_gap",
        )
    )

    assert gate["passed"] is False
    assert "job_gap_claimed_as_project_experience" in gate["blocking_reasons"]


def _candidate(
    question_text: str,
    *,
    allowed_entities: tuple[str, ...],
    forbidden_entities: tuple[str, ...] = (),
    scenario_mode: str = "resume_project",
) -> dict[str, object]:
    return {
        "candidate_ref": "question_candidate_ref_gate",
        "scenario": {
            "scenario_title": "场景打磨",
            "scenario_mode": scenario_mode,
            "allowed_entities": list(allowed_entities),
            "forbidden_entities": list(forbidden_entities),
        },
        "question_text": question_text,
        "question_pattern": "polish_structured_experience",
        "evidence_refs": ("resume_evidence_ref_gate",),
        "source_availability": {"resume": True},
        "confidence_level": "medium",
        "low_confidence_flags": (),
        "trace_refs": ("scenario_ref_gate", "candidate_ref_gate", "validation_ref_gate"),
        "sanitized": True,
    }
