from __future__ import annotations

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    build_polish_question_candidate_readonly,
    derive_question_scenario,
    question_candidate_quality_gate,
)


def test_scenario_derived_from_resume_project() -> None:
    scenario = derive_question_scenario(
        session_ref="session_ref_q3",
        selected_progress_node_summary="订单履约系统状态流转表达打磨",
        selected_evidence_refs=("resume_evidence_ref_order_fulfillment",),
        resume_evidence_summaries=(
            _evidence(
                "resume_evidence_ref_order_fulfillment",
                "我负责订单履约系统中的库存预占、支付回调和超时取消状态流转。",
            ),
        ),
    )

    assert scenario["scenario_title"]
    assert any("支付回调" in entity or "状态流转" in entity for entity in scenario["allowed_entities"])
    assert "日志" not in repr(scenario)
    assert "RAG" not in repr(scenario)
    assert "AI模拟面试工作台" not in repr(scenario)
    assert scenario["confidence_level"] != "low"


def test_scenario_derived_from_job_gap_without_claiming_experience() -> None:
    scenario = derive_question_scenario(
        session_ref="session_ref_q3",
        selected_progress_node_summary="高并发接口设计表达打磨",
        selected_evidence_refs=("job_requirement_ref_high_concurrency",),
        resume_evidence_summaries=(),
        job_requirement_summaries=(
            _evidence(
                "job_requirement_ref_high_concurrency",
                "要求具备高并发接口设计、限流降级、压测和可观测性经验。",
                source_type="job_requirement",
            ),
        ),
    )
    candidate = build_polish_question_candidate_readonly(
        owner_id="owner_q3",
        run_id="run_q3",
        ai_task_id="task_q3",
        session_ref="session_ref_q3",
        scenario=scenario,
    )

    assert scenario["scenario_mode"] in {"job_gap", "learning_gap"}
    assert any(term in candidate["question_text"] for term in ("理解", "补齐计划", "可迁移经验"))
    assert "你负责过" not in candidate["question_text"]
    assert "你做过" not in candidate["question_text"]
    assert candidate["quality_gate"]["passed"] is True


def test_multiple_domains_do_not_merge() -> None:
    scenario = derive_question_scenario(
        session_ref="session_ref_q3",
        selected_progress_node_summary="项目经历表达打磨",
        selected_evidence_refs=("resume_evidence_ref_upload", "resume_evidence_ref_inventory"),
        resume_evidence_summaries=(
            _evidence("resume_evidence_ref_upload", "项目 A 做过 1GB 文件上传和异步解析。"),
            _evidence("resume_evidence_ref_inventory", "项目 B 做过库存扣减和事务消息。"),
        ),
    )
    candidate = build_polish_question_candidate_readonly(
        owner_id="owner_q3",
        run_id="run_q3",
        ai_task_id="task_q3",
        session_ref="session_ref_q3",
        scenario=scenario,
    )

    assert not ("1GB" in candidate["question_text"] and "库存扣减" in candidate["question_text"])
    assert any("库存扣减" in entity or "事务消息" in entity for entity in scenario["forbidden_entities"])
    mixed_candidate = {
        **candidate,
        "question_text": "请围绕 1GB 文件上传和库存扣减回答核心链路。",
    }

    gate = question_candidate_quality_gate(mixed_candidate)

    assert gate["passed"] is False
    assert "cross_evidence_scenario_mixing" in gate["blocking_reasons"]


def _evidence(ref: str, summary: str, *, source_type: str = "resume_project") -> dict[str, str]:
    return {
        "ref": ref,
        "summary": summary,
        "source_type": source_type,
    }
