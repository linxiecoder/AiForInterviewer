from __future__ import annotations

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    POLISH_QUESTION_GRAPH_FLAG,
    POLISH_QUESTION_GRAPH_VERSION,
    run_polish_question_readonly_parity,
)
from app.application.ai_runtime.contracts import AgentCommandEnvelope, AgentRunContext, contains_sensitive_payload
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver


def test_readonly_graph_returns_candidate_refs_only_without_writes_or_provider_calls() -> None:
    context = _context()
    resolver = RuntimeFlagResolver(test_overrides={POLISH_QUESTION_GRAPH_FLAG: True})

    result = run_polish_question_readonly_parity(context, context.command, flag_resolver=resolver)

    assert result.status == "readonly_parity_succeeded"
    assert result.output_refs == (result.metadata["candidate"]["candidate_ref"],)
    assert result.output_refs[0].startswith("question_candidate_ref_")
    assert result.formal_refs == ()
    assert result.interrupt_refs == ()
    assert result.metadata["readonly_parity"] is True
    assert result.metadata["provider_calls"] == 0
    assert result.metadata["db_business_writes"] == 0
    assert result.metadata["formal_business_writes"] == 0
    assert result.metadata["checkpoint_refs_are_business_facts"] is False
    assert result.metadata["scenario_derivation"] == "dynamic_evidence_based"
    assert result.metadata["candidate"]["sanitized"] is True
    assert result.metadata["candidate"]["quality_gate"]["passed"] is True
    assert result.metadata["quality_gate"]["passed"] is True
    assert result.metadata["scenario"]["scenario_title"]
    assert any(ref.startswith("scenario_ref_") for ref in result.trace_refs)
    assert any(ref.startswith("question_candidate_ref_") for ref in result.trace_refs)
    assert any(ref.startswith("validation_ref_") for ref in result.trace_refs)
    assert contains_sensitive_payload(result.metadata) is False


def _context() -> AgentRunContext:
    command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("session_ref_q3", "progress_node_ref_order"),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr5_q3",
        metadata={
            "selected_progress_node_summary": "订单履约系统状态流转表达打磨",
            "selected_evidence_refs": ("resume_evidence_ref_order_fulfillment",),
            "resume_evidence_summaries": (
                {
                    "ref": "resume_evidence_ref_order_fulfillment",
                    "summary": "我负责订单履约系统中的库存预占、支付回调和超时取消状态流转。",
                    "source_type": "resume_project",
                },
            ),
            "job_requirement_summaries": (),
            "match_gap_summaries": (),
            "history_feedback_summaries": (
                {
                    "ref": "feedback_summary_ref_1",
                    "summary": "上一轮反馈要求补充失败处理和验证指标。",
                    "source_type": "history_feedback",
                },
            ),
            "completed_focus_refs": ("completed_focus_ref_state_flow",),
        },
    )
    return AgentRunContext(
        owner_id="owner_q3",
        actor_id="actor_q3",
        run_id="arun_pr5_q3",
        ai_task_id="aitask_pr5_q3",
        graph_name="polish_question_graph",
        graph_version=POLISH_QUESTION_GRAPH_VERSION,
        command=command,
    )
