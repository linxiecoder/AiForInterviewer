from __future__ import annotations

import json
from typing import Any

from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.entities import PolishAnswer
from app.application.polish.question_generation_service import QuestionGenerationService
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus

from tests.api.test_polish_question_graph_integration import (
    ACTOR_ID,
    NODE_REF,
    OWNER_ID,
    SESSION_ID,
    _command,
    _use_cases,
)


def test_phase1_question_service_blocks_inventory_evidence_from_log_vector_pipeline() -> None:
    service = QuestionGenerationService()
    session, context, plan, state = _question_generation_inputs(
        primary_text="库存扣减链路使用分布式锁、事务消息和本地事务保证一致性。",
        node_title="库存一致性与异常补偿",
        expected_capability="能说明库存扣减的一致性、异常补偿和验证指标。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    question_text = result.draft.question_text
    for unsupported in ("1GB 日志", "上传入口", "解析", "切块", "向量化", "入库", "15 秒到 3 秒"):
        assert unsupported not in question_text
    assert result.blueprint is not None
    assert result.blueprint.primary_evidence_ref in result.draft.evidence_refs


def test_phase1_question_service_keeps_job_gap_probe_from_claiming_candidate_experience() -> None:
    service = QuestionGenerationService()
    session, context, plan, state = _question_generation_inputs(
        primary_text="岗位要求候选人具备支付链路幂等、失败补偿和上线验证经验。",
        primary_source_type="job_requirement",
        node_title="岗位匹配缺口与技术深度防御",
        expected_capability="验证候选人是否能补齐岗位要求中的支付可靠性缺口。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.blueprint is not None
    assert result.blueprint.claim_mode == "job_gap_probe"
    assert result.draft is not None
    for forbidden in ("你负责过", "你实现过", "你主导过", "你参与过"):
        assert forbidden not in result.draft.question_text


def test_phase1_question_service_clarification_question_requires_four_materials() -> None:
    service = QuestionGenerationService()
    session, _context, plan, state = _question_generation_inputs(primary_text="")
    context = {"content_digest": "ctx_phase1_empty", "turns": []}

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.blueprint is not None
    assert result.blueprint.claim_mode == "clarification_needed"
    assert result.draft is not None
    for required in ("业务入口", "职责边界", "失败案例", "验证指标"):
        assert required in result.draft.question_text


def test_phase1_grounding_failure_persists_failed_task_without_question() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._question_generation_service = QuestionGenerationService(
        surface_question_builder=lambda _blueprint, _scope: " "
    )

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert result.value.validation_errors
    assert repository.questions == []
    assert len(repository.tasks) == 1


def test_phase1_feedback_task_returns_reserved_placeholder_without_candidates_or_score() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    question_result = use_cases.create_question_task(_command())
    assert question_result.is_success
    question = repository.questions[0]
    answer = PolishAnswer(
        answer_id="ans_phase1_reserved",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        question_id=question.question_id,
        answer_round=1,
        answer_text="我会先说明业务背景，再说明一致性方案和验证指标。",
        status="saved",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    repository.answers = [answer]
    repository.feedbacks = []
    repository.get_answer = lambda owner_id, answer_id: next(
        (item for item in repository.answers if item.owner_id == owner_id and item.answer_id == answer_id),
        None,
    )
    repository.list_answers_for_session = lambda owner_id, session_id: tuple(
        item for item in repository.answers if item.owner_id == owner_id and item.session_id == session_id
    )
    repository.add_feedback = lambda feedback: repository.feedbacks.append(feedback)
    repository.list_feedbacks_for_session = lambda owner_id, session_id: tuple(
        item for item in repository.feedbacks if item.owner_id == owner_id and item.session_id == session_id
    )

    result = use_cases.create_feedback_task(
        CreatePolishFeedbackTaskCommand(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            answer_id=answer.answer_id,
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert result.value.score_type is None
    assert result.value.candidate_refs == ()
    assert len(repository.feedbacks) == 1
    feedback_payload = json.loads(repository.feedbacks[0].feedback_summary)
    assert feedback_payload["status"] == "reserved"
    assert feedback_payload["score_result"] is None
    assert feedback_payload["candidate_refs"] == []
    assert feedback_payload["reference_answer"] is None
    assert feedback_payload["feedback_metadata"]["reserved"] is True


def _question_generation_inputs(
    *,
    primary_text: str,
    primary_source_type: str = "resume_project",
    node_title: str = "支付链路一致性",
    expected_capability: str = "能说明状态流转、幂等、失败补偿和上线验证。",
) -> tuple[Any, dict[str, Any], dict[str, Any], dict[str, Any]]:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    detail = use_cases._build_session_detail(owner_id=OWNER_ID, session=repository.session)
    context = dict(detail.progress_context)
    if primary_source_type == "job_requirement":
        context["resume_snapshot"] = {
            "resume_id": "res_phase1_empty",
            "resume_version_id": "resver_phase1_empty",
            "summary": "",
            "project_experiences": [],
            "skills": [],
        }
        context["job_snapshot"] = {
            "job_id": "job_phase1",
            "job_version_id": "jobver_phase1",
            "requirements": [primary_text] if primary_text else [],
            "responsibilities": [],
        }
    else:
        context["resume_snapshot"] = {
            "resume_id": "res_phase1",
            "resume_version_id": "resver_phase1",
            "summary": "",
            "project_experiences": [primary_text] if primary_text else [],
            "skills": [],
        }
        context["job_snapshot"] = {
            "job_id": "job_phase1",
            "job_version_id": "jobver_phase1",
            "requirements": [],
            "responsibilities": [],
        }
    plan = {
        "status": "ready",
        "context_digest": "ctx_phase1",
        "nodes": [
            {
                "progress_node_ref": NODE_REF,
                "title": node_title,
                "expected_capability": expected_capability,
                "missing_points": ["需要补充验证指标。"],
                "children": [],
            }
        ],
    }
    state = {
        "status": "ready",
        "node_states": [],
        "current_priority": {"progress_node_ref": NODE_REF},
        "progress": {"progress_percent": 0},
    }
    return repository.session, context, plan, state
