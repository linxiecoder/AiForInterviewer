from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
import pytest
from sqlalchemy import text

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.errors import ApiHttpError, api_http_error_handler
import app.api.v1.polish as polish_api
from app.api.v1 import build_api_v1_router
from app.application.polish.candidates import (
    CandidateExtractionInput,
    CandidateType,
    extract_asset_candidates,
    extract_feedback_candidates,
    extract_training_suggestion_candidates,
    extract_weakness_candidates,
)
from app.domain.auth.entities import CurrentActor
from app.infrastructure.llm.fake_transport import FakeLlmTransport
from app.infrastructure.db.repositories.polish_candidates import SqlAlchemyPolishCandidateRepository
from tests.api.asgi_client import call_json
from tests.api.test_polish_api import (
    ACTOR_A,
    ACTOR_B,
    OWNER_A,
    OWNER_B,
    _isolated_polish_app,
    _seed_polish_sources,
    _session_factory,
)


async def _run_inline_threadpool(func, *args, **kwargs):
    return func(*args, **kwargs)


@pytest.fixture(autouse=True)
def _patch_polish_run_in_threadpool(monkeypatch):
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)


def _candidate_input(
    *,
    owner_id: str = "usr_candidate_owner_a",
    feedback_payload: dict[str, Any] | None = None,
) -> CandidateExtractionInput:
    return CandidateExtractionInput(
        owner_id=owner_id,
        session_id="psess_candidate_001",
        question_id="ques_candidate_001",
        answer_id="ans_candidate_001",
        feedback_id="trc_candidate_feedback_001",
        score_result_id="score_candidate_001",
        feedback_payload=feedback_payload or _structured_feedback_payload(),
        question_metadata={
            "question_pattern": "failure_handling_design",
            "expected_answer_dimensions": ["failure handling", "idempotency"],
            "quality_score": 88,
        },
        created_at=datetime(2026, 5, 22, 10, 30, tzinfo=UTC),
    )


def _structured_feedback_payload() -> dict[str, Any]:
    return {
        "schema_id": "polish_feedback_payload_v1",
        "schema_version": "1.0",
        "status": "generated",
        "feedback_id": "trc_candidate_feedback_001",
        "answer_id": "ans_candidate_001",
        "question_id": "ques_candidate_001",
        "question_text": "请说明一次故障兜底方案。",
        "answer_text": "完整原始回答不应进入 merge_key 或候选对象。",
        "feedback_text": "结构化反馈",
        "feedback_summary": "结构化反馈",
        "polish_session_ref": {"resource_type": "polish_session", "resource_id": "psess_candidate_001"},
        "question_ref": {"resource_type": "question", "resource_id": "ques_candidate_001"},
        "answer_ref": {"resource_type": "answer", "resource_id": "ans_candidate_001"},
        "score_result_ref": {"resource_type": "score_result", "resource_id": "score_candidate_001"},
        "score_result": {
            "score_result_id": "score_candidate_001",
            "score_value": 64,
            "confidence_level": "medium",
        },
        "scoring_dimensions": [
            {"dimension_id": "technical_depth", "score_value": 55, "confidence_level": "medium"},
            {"dimension_id": "answer_structure", "score_value": 58, "confidence_level": "medium"},
            {"dimension_id": "business_impact", "score_value": 86, "confidence_level": "medium"},
        ],
        "loss_points": [
            {
                "loss_point_id": "loss_failure_handling",
                "dimension_id": "technical_depth",
                "title": "故障兜底与失败收敛表达不足",
                "reason": "缺少失败路径、补偿策略和上线验证指标。",
                "deducted_points": 14,
                "critical": True,
                "answer_excerpt": "只讲了成功路径。",
            },
            {
                "loss_point_id": "loss_structure",
                "dimension_id": "answer_structure",
                "title": "项目表达结构不清晰",
                "reason": "结论、约束、方案、结果没有分层。",
                "deducted_points": 8,
                "critical": False,
            },
        ],
        "repeated_loss_points": ["loss_failure_handling"],
        "remaining_gaps": ["loss_failure_handling", "状态机与幂等闭环不足"],
        "technical_gaps": ["状态机与幂等闭环不足"],
        "communication_gaps": ["项目表达结构不清晰"],
        "positive_evidence_points": [
            {
                "point_id": "pos_business_metric",
                "dimension_id": "business_impact",
                "title": "能说明业务指标",
                "evidence_excerpt": "提到了告警压降和恢复时间。",
                "confidence_level": "medium",
            }
        ],
        "answer_diagnosis": {"strengths": ["能说明业务指标"], "weaknesses": ["故障兜底不足"]},
        "oral_script": "我会先说故障背景，再说明兜底策略、状态机、幂等和验证指标。",
        "p7_reference_answer": "高阶参考答案：先界定失败场景，再给补偿、回滚、监控和指标。",
        "next_retry_focus": [
            {"focus_id": "retry_failure_handling", "title": "补齐失败兜底", "reason": "重复缺失"},
        ],
        "mastery_status": "stuck",
        "should_continue_same_question": True,
        "should_generate_next_question": False,
        "feedback_metadata": {"question_pattern": "failure_handling_design"},
        "trace_refs": [
            {"trace_ref_id": "ans_candidate_001", "trace_type": "answer"},
            {"trace_ref_id": "trc_candidate_feedback_001", "trace_type": "feedback"},
        ],
        "candidate_refs": [{"resource_type": "weakness_candidate", "resource_id": "legacy_weakness_ref"}],
    }


def _collect_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_collect_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_collect_keys(nested))
    return keys


def _string_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_string_values(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_string_values(nested))
    elif isinstance(value, str):
        values.append(value)
    return values


def _refs_by_type(candidate: dict[str, Any], ref_field: str) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}
    for ref in candidate[ref_field]:
        refs.setdefault(str(ref["resource_type"]), set()).add(str(ref["resource_id"]))
    return refs


def test_feedback_extracts_candidate_payload_fields_and_refs() -> None:
    payload = extract_feedback_candidates(_candidate_input())

    assert payload["weakness_candidates"]
    assert payload["asset_candidates"]
    assert payload["training_suggestion_candidates"]
    assert payload["oral_script_candidates"]
    assert payload["polished_answer_candidates"]
    assert payload["candidate_refs"][0]["resource_type"] == "weakness_candidate"
    assert {ref["resource_type"] for ref in payload["candidate_refs"]} >= {
        "weakness_candidate",
        "asset_candidate",
        "training_suggestion_candidate",
        "oral_script_candidate",
        "polished_answer_candidate",
    }

    all_candidates = (
        payload["weakness_candidates"]
        + payload["asset_candidates"]
        + payload["training_suggestion_candidates"]
        + payload["oral_script_candidates"]
        + payload["polished_answer_candidates"]
    )
    assert all(candidate["status"] == "candidate" for candidate in all_candidates)
    assert all(candidate["user_confirmation_required"] is True for candidate in all_candidates)
    assert all(candidate["target_formal_ref"] is None for candidate in all_candidates)
    assert "weaknesses" not in payload
    assert "assets" not in payload
    assert "training_recommendations" not in payload

    weakness = payload["weakness_candidates"][0]
    assert weakness["candidate_type"] == "weakness_candidate"
    source_refs = _refs_by_type(weakness, "source_refs")
    trace_refs = _refs_by_type(weakness, "trace_refs")
    assert {"polish_session", "question", "answer", "feedback", "score_result", "loss_point"} <= set(source_refs)
    assert {"question", "answer", "feedback"} <= set(trace_refs)
    assert weakness["merge_key"]
    assert "完整原始回答" not in weakness["merge_key"]


def test_specific_extractors_generate_expected_candidate_types() -> None:
    extraction_input = _candidate_input()

    weakness_candidates = extract_weakness_candidates(extraction_input)
    asset_candidates = extract_asset_candidates(extraction_input)
    training_candidates = extract_training_suggestion_candidates(extraction_input)

    assert weakness_candidates
    assert all(candidate.candidate_type == CandidateType.WEAKNESS for candidate in weakness_candidates)
    assert weakness_candidates[0].evidence_refs[0]["resource_id"] == "loss_failure_handling"
    assert {candidate.candidate_type for candidate in asset_candidates} == {
        CandidateType.ASSET,
        CandidateType.ORAL_SCRIPT,
        CandidateType.POLISHED_ANSWER,
    }
    assert [candidate.candidate_type for candidate in training_candidates] == [
        CandidateType.TRAINING_SUGGESTION
    ]
    assert weakness_candidates[0].confidence_level == "high"
    assert any(candidate.candidate_payload.get("model_suggested") is True for candidate in asset_candidates)
    assert any(
        candidate.candidate_payload.get("fact_source") == "model_suggested_phrasing"
        for candidate in asset_candidates
    )


def test_repeated_loss_points_are_prioritized_over_single_minor_loss_points() -> None:
    payload = _structured_feedback_payload()
    payload["repeated_loss_points"] = ["loss_failure_handling"]
    payload["loss_points"][1]["critical"] = False
    payload["loss_points"][1]["deducted_points"] = 2

    candidates = extract_weakness_candidates(_candidate_input(feedback_payload=payload))

    assert candidates[0].evidence_refs[0]["resource_id"] == "loss_failure_handling"
    assert candidates[0].confidence_level == "high"
    assert all(candidate.confidence_level != "high" for candidate in candidates[1:])


def test_training_candidate_uses_remaining_gaps_and_retry_focus() -> None:
    payload = extract_feedback_candidates(_candidate_input())
    candidate = payload["training_suggestion_candidates"][0]

    assert candidate["candidate_type"] == "training_suggestion_candidate"
    assert candidate["confidence_level"] in {"medium", "high"}
    assert "同题" in candidate["summary"] or "重答" in candidate["summary"]
    assert _refs_by_type(candidate, "source_refs")["loss_point"]


def test_merge_key_is_stable_and_owner_isolated() -> None:
    first = extract_feedback_candidates(_candidate_input())
    second = extract_feedback_candidates(_candidate_input())
    other_owner = extract_feedback_candidates(_candidate_input(owner_id="usr_candidate_owner_b"))

    first_key = first["weakness_candidates"][0]["merge_key"]
    assert first_key == second["weakness_candidates"][0]["merge_key"]
    assert first_key != other_owner["weakness_candidates"][0]["merge_key"]
    assert "完整原始回答" not in first_key


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "pending", "feedback_text": "本轮反馈尚未生成"},
        {"status": "generated", "feedback_text": "legacy feedback text", "candidate_refs": []},
    ],
)
def test_pending_and_old_feedback_payloads_do_not_create_invalid_candidates(payload: dict[str, Any]) -> None:
    result = extract_feedback_candidates(_candidate_input(feedback_payload=payload))

    assert result["weakness_candidates"] == []
    assert result["asset_candidates"] == []
    assert result["training_suggestion_candidates"] == []
    assert result["oral_script_candidates"] == []
    assert result["polished_answer_candidates"] == []
    assert result["candidate_refs"] == []


def test_candidate_payload_sanitizes_raw_prompt_completion_and_provider_payload() -> None:
    payload = _structured_feedback_payload()
    payload["raw_prompt"] = "raw prompt must not be returned"
    payload["completion"] = "raw completion must not be returned"
    payload["provider_payload"] = {"api_key": "secret"}
    payload["full_resume"] = "full resume markdown must not be returned"
    payload["full_jd"] = "full JD text must not be returned"
    payload["loss_points"][0]["hidden_rubric"] = "internal scoring rule"
    payload["positive_evidence_points"][0]["full_evidence_text"] = "full answer evidence"
    payload["loss_points"][0]["title"] = "raw_prompt must not be returned"
    payload["loss_points"][0]["answer_excerpt"] = "provider_payload must not be returned"
    payload["positive_evidence_points"][0]["evidence_excerpt"] = "full_evidence_text must not be returned"
    payload["technical_gaps"] = ["cookie=session-secret must not be returned"]
    payload["oral_script"] = "provider_payload must not be returned"
    payload["p7_reference_answer"] = "api_key=sk-test-secret must not be returned"
    result = extract_feedback_candidates(_candidate_input(feedback_payload=payload))

    forbidden = {
        "raw_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "hidden_rubric",
        "full_evidence_text",
        "full_resume",
        "full_jd",
        "api_key",
        "cookie",
        "secret",
        "token",
    }
    assert not (_collect_keys(result) & forbidden)
    serialized_values = "\n".join(_string_values(result)).lower()
    for forbidden_text in (
        "raw prompt must not be returned",
        "raw_prompt must not be returned",
        "provider_payload must not be returned",
        "full_evidence_text must not be returned",
        "full resume markdown must not be returned",
        "full jd text must not be returned",
        "cookie=session-secret must not be returned",
        "api_key=sk-test-secret must not be returned",
    ):
        assert forbidden_text not in serialized_values


def test_safe_candidate_dict_sanitizes_candidate_fields_refs_payload_and_merge_key() -> None:
    from app.application.polish.candidates import (
        CandidateSourceType,
        CandidateStatus,
        PolishCandidate,
        safe_candidate_dict,
    )

    candidate = PolishCandidate(
        candidate_id="cand_sensitive",
        candidate_type=CandidateType.WEAKNESS,
        owner_id="usr_candidate_owner_a",
        source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
        source_refs=({"resource_type": "answer", "resource_id": "token=answer-secret"},),
        evidence_refs=({"resource_type": "loss_point", "resource_id": "cookie=session-secret"},),
        trace_refs=({"trace_type": "feedback", "trace_ref_id": "secret=trace-secret"},),
        session_id="psess_candidate_001",
        question_id="ques_candidate_001",
        answer_id="ans_candidate_001",
        feedback_id="trc_candidate_feedback_001",
        title="raw_prompt must not be returned",
        summary="provider_payload must not be returned",
        evidence_excerpt="api_key=sk-test-secret must not be returned",
        reason="token=reason-secret cookie=session-secret secret=plain-secret",
        confidence_level="medium",
        merge_key="weakness_candidate:完整原始回答不应进入:raw_prompt:api_key=sk-test-secret",
        created_at=datetime(2026, 5, 22, 10, 30, tzinfo=UTC),
        updated_at=datetime(2026, 5, 22, 10, 30, tzinfo=UTC),
        status=CandidateStatus.CANDIDATE,
        candidate_payload={
            "full_resume": "full resume markdown must not be returned",
            "nested": {
                "hidden_rubric": "hidden rubric must not be returned",
                "full_evidence_text": "full evidence text must not be returned",
                "full_jd": "full JD text must not be returned",
                "provider_payload": {"secret": "secret=payload-secret"},
            },
            "list": [
                {"raw_prompt": "raw_prompt must not be returned"},
                "token=list-secret must not be returned",
            ],
            "safe_note": "safe note remains",
        },
    )

    result = safe_candidate_dict(candidate)

    assert result["candidate_payload"]["safe_note"] == "safe note remains"
    forbidden = {
        "raw_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "hidden_rubric",
        "full_evidence_text",
        "full_resume",
        "full_jd",
        "api_key",
        "cookie",
        "secret",
        "token",
    }
    assert not (_collect_keys(result) & forbidden)
    serialized_values = "\n".join(_string_values(result)).lower()
    for forbidden_text in (
        "raw_prompt",
        "provider_payload",
        "api_key=sk-test-secret",
        "token=answer-secret",
        "cookie=session-secret",
        "secret=trace-secret",
        "full resume markdown",
        "full jd text",
        "full evidence text",
        "完整原始回答不应进入",
    ):
        assert forbidden_text not in serialized_values


def test_feedback_generation_persists_candidates_and_exposes_list_get() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    feedback_payload = _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)

    status_code, list_body = call_json(app, "/api/v1/polish-candidates")

    assert status_code == 200
    candidates = list_body["data"]
    assert candidates
    assert {candidate["candidate_type"] for candidate in candidates} >= {
        "weakness_candidate",
        "asset_candidate",
        "training_suggestion_candidate",
        "oral_script_candidate",
        "polished_answer_candidate",
    }
    assert {candidate["candidate_id"] for candidate in candidates} == {
        ref["resource_id"] for ref in feedback_payload["candidate_refs"]
    }
    assert all(candidate["status"] == "candidate" for candidate in candidates)
    assert all(candidate["user_confirmation_required"] is True for candidate in candidates)
    assert all(candidate["target_formal_ref"] is None for candidate in candidates)

    weakness = next(candidate for candidate in candidates if candidate["candidate_type"] == "weakness_candidate")
    assert {"polish_session", "question", "answer", "feedback"} <= {
        ref["resource_type"] for ref in weakness["source_refs"]
    }
    assert {"question", "answer", "feedback"} <= {
        ref["resource_type"] for ref in weakness["trace_refs"]
    }
    assert weakness["evidence_refs"]
    assert weakness["candidate_payload"]["formal_write_intent"] is False

    status_code, detail_body = call_json(app, f"/api/v1/polish-candidates/{weakness['candidate_id']}")

    assert status_code == 200
    assert detail_body["resource_type"] == "polish_candidate"
    assert detail_body["data"] == weakness
    _assert_no_formal_memory_written(session_factory)


def test_candidate_list_filters_status_type_session_source_and_confidence() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    feedback_payload = _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    session_id = feedback_payload["polish_session_ref"]["resource_id"]

    status_code, body = call_json(
        app,
        f"/api/v1/polish-candidates?status=candidate&candidate_type=weakness_candidate&session_id={session_id}",
    )

    assert status_code == 200
    assert body["data"]
    assert all(candidate["status"] == "candidate" for candidate in body["data"])
    assert all(candidate["candidate_type"] == "weakness_candidate" for candidate in body["data"])
    assert all(candidate["session_id"] == session_id for candidate in body["data"])

    source_type = body["data"][0]["source_type"]
    confidence_level = body["data"][0]["confidence_level"]
    status_code, filtered_body = call_json(
        app,
        f"/api/v1/polish-candidates?source_type={source_type}&confidence_level={confidence_level}",
    )

    assert status_code == 200
    assert filtered_body["data"]
    assert all(candidate["source_type"] == source_type for candidate in filtered_body["data"])
    assert all(candidate["confidence_level"] == confidence_level for candidate in filtered_body["data"])


def test_candidate_api_enforces_owner_isolation_and_not_found() -> None:
    session_factory = _session_factory()
    app_a = _isolated_candidates_app(session_factory, ACTOR_A)
    app_b = _isolated_candidates_app(session_factory, ACTOR_B)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)

    _, list_a = call_json(app_a, "/api/v1/polish-candidates?candidate_type=weakness_candidate")
    candidate_id = list_a["data"][0]["candidate_id"]

    status_code, list_b = call_json(app_b, "/api/v1/polish-candidates")
    assert status_code == 200
    assert list_b["data"] == []

    status_code, detail_b = call_json(app_b, f"/api/v1/polish-candidates/{candidate_id}")
    assert status_code == 404
    assert detail_b["error"]["code"] == "not_found_or_inaccessible"


def test_persisted_candidate_payload_keeps_sanitizer_effective() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)

    status_code, list_body = call_json(app, "/api/v1/polish-candidates")

    assert status_code == 200
    forbidden = {
        "raw_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "hidden_rubric",
        "full_evidence_text",
        "full_resume",
        "full_jd",
        "api_key",
        "cookie",
        "secret",
        "token",
    }
    assert not (_collect_keys(list_body) & forbidden)
    serialized_values = "\n".join(_string_values(list_body)).lower()
    for forbidden_text in (
        "raw_prompt",
        "provider_payload",
        "hidden_rubric",
        "full resume markdown",
        "full jd text",
        "api_key=",
        "cookie=",
        "secret=",
        "token=",
    ):
        assert forbidden_text not in serialized_values


def test_old_payloads_do_not_persist_invalid_candidates_and_duplicate_merge_key_is_owner_scoped() -> None:
    session_factory = _session_factory()
    app_a = _isolated_candidates_app(session_factory, ACTOR_A)
    app_b = _isolated_candidates_app(session_factory, ACTOR_B)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    _create_feedback_payload(session_factory, ACTOR_B, OWNER_B)

    status_code, list_a = call_json(app_a, "/api/v1/polish-candidates")
    status_code_b, list_b = call_json(app_b, "/api/v1/polish-candidates")

    assert status_code == 200
    assert status_code_b == 200
    merge_keys_a = {candidate["merge_key"] for candidate in list_a["data"]}
    merge_keys_b = {candidate["merge_key"] for candidate in list_b["data"]}
    assert len(list_a["data"]) == len(merge_keys_a)
    assert merge_keys_a.isdisjoint(merge_keys_b)


def test_candidate_repository_allows_same_candidate_id_across_different_owners() -> None:
    session_factory = _session_factory()
    repository = SqlAlchemyPolishCandidateRepository(session_factory)
    payload = {
        "weakness_candidates": [
            {
                "candidate_id": "cand_shared_content_hash",
                "candidate_type": "weakness_candidate",
                "status": "candidate",
                "source_type": "structured_feedback",
                "source_refs": [{"resource_type": "feedback", "resource_id": "feedback_shared"}],
                "evidence_refs": [{"resource_type": "loss_point", "resource_id": "loss_shared"}],
                "trace_refs": [{"trace_type": "feedback", "trace_ref_id": "feedback_shared"}],
                "session_id": "psess_shared",
                "question_id": "ques_shared",
                "answer_id": "ans_shared",
                "feedback_id": "feedback_shared",
                "title": "同内容候选",
                "summary": "同内容候选摘要",
                "evidence_excerpt": "同内容证据",
                "reason": "同内容原因",
                "confidence_level": "medium",
                "merge_key": "weakness_candidate:shared-content",
                "target_formal_ref": None,
                "candidate_payload": {"formal_write_intent": False},
                "user_confirmation_required": True,
            }
        ]
    }

    persisted_a = repository.upsert_from_feedback_payload(OWNER_A, payload)
    persisted_b = repository.upsert_from_feedback_payload(OWNER_B, payload)

    assert persisted_a[0]["candidate_id"] == "cand_shared_content_hash"
    assert persisted_b[0]["candidate_id"] == "cand_shared_content_hash"
    assert repository.get_candidate(owner_id=OWNER_A, candidate_id="cand_shared_content_hash")["owner_id"] == OWNER_A
    assert repository.get_candidate(owner_id=OWNER_B, candidate_id="cand_shared_content_hash")["owner_id"] == OWNER_B


def test_confirm_weakness_candidate_creates_formal_weakness_with_refs() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    weakness = _candidate_by_type(app, "weakness_candidate")

    status_code, body = call_json(
        app,
        f"/api/v1/polish-candidates/{weakness['candidate_id']}/confirm",
        "POST",
    )

    assert status_code == 200
    assert body["resource_type"] == "polish_candidate_action"
    result = body["data"]
    assert result["action"] == "confirm"
    assert result["candidate"]["status"] == "confirmed"
    assert result["candidate"]["confirmed_at"] is not None
    assert result["candidate"]["target_formal_ref"]["resource_type"] == "weakness"
    assert result["formal_ref"] == result["candidate"]["target_formal_ref"]

    row = _fetch_one(
        session_factory,
        "select id, owner_id, title, summary, status, confidence_level, source_refs_json, "
        "evidence_refs_json, trace_refs_json, created_from_candidate_id, user_confirmation_ref_json "
        "from weaknesses",
    )
    assert row["id"] == result["formal_ref"]["resource_id"]
    assert row["owner_id"] == OWNER_A
    assert row["status"] == "active"
    assert row["created_from_candidate_id"] == weakness["candidate_id"]
    assert row["title"] == weakness["title"]
    assert row["summary"] == weakness["summary"]
    assert row["confidence_level"] == weakness["confidence_level"]
    assert _decode_json(row["source_refs_json"]) == weakness["source_refs"]
    assert _decode_json(row["evidence_refs_json"]) == weakness["evidence_refs"]
    assert _decode_json(row["trace_refs_json"]) == weakness["trace_refs"]
    assert _decode_json(row["user_confirmation_ref_json"])["resource_type"] == "user_confirmation"


def test_confirm_asset_candidate_creates_formal_asset_and_asset_version() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    asset_candidate = _candidate_by_type(app, "asset_candidate")

    status_code, body = call_json(
        app,
        f"/api/v1/polish-candidates/{asset_candidate['candidate_id']}/confirm",
        "POST",
    )

    assert status_code == 200
    result = body["data"]
    assert result["candidate"]["status"] == "confirmed"
    assert result["candidate"]["target_formal_ref"]["resource_type"] == "asset"
    assert result["asset_version_ref"]["resource_type"] == "asset_version"

    asset_row = _fetch_one(
        session_factory,
        "select id, owner_id, asset_type, title, summary, content, current_version_id, status, "
        "source_refs_json, evidence_refs_json, trace_refs_json, created_from_candidate_id, "
        "user_confirmation_ref_json, fact_source from assets",
    )
    version_row = _fetch_one(
        session_factory,
        "select id, owner_id, asset_id, version_number, content, edit_summary, "
        "created_from_candidate_id from asset_versions",
    )
    assert asset_row["id"] == result["formal_ref"]["resource_id"]
    assert asset_row["owner_id"] == OWNER_A
    assert asset_row["asset_type"] == "asset"
    assert asset_row["status"] == "active"
    assert asset_row["created_from_candidate_id"] == asset_candidate["candidate_id"]
    assert asset_row["title"] == asset_candidate["title"]
    assert asset_row["summary"] == asset_candidate["summary"]
    assert asset_row["content"] == asset_candidate["evidence_excerpt"]
    assert asset_row["current_version_id"] == version_row["id"]
    assert asset_row["fact_source"] in {"user_fact", "score_signal"}
    assert _decode_json(asset_row["source_refs_json"]) == asset_candidate["source_refs"]
    assert _decode_json(asset_row["evidence_refs_json"]) == asset_candidate["evidence_refs"]
    assert _decode_json(asset_row["trace_refs_json"]) == asset_candidate["trace_refs"]
    assert _decode_json(asset_row["user_confirmation_ref_json"])["resource_type"] == "user_confirmation"
    assert version_row["asset_id"] == asset_row["id"]
    assert version_row["version_number"] == 1
    assert version_row["content"] == asset_candidate["evidence_excerpt"]
    assert version_row["created_from_candidate_id"] == asset_candidate["candidate_id"]


def test_dismiss_merge_and_archive_candidate_state_flow_without_formal_write() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    candidates = _candidate_list(app)
    dismissed = candidates[0]
    merged = candidates[1]
    merge_target = candidates[2]
    archived = candidates[3]

    status_code, dismiss_body = call_json(
        app,
        f"/api/v1/polish-candidates/{dismissed['candidate_id']}/dismiss",
        "POST",
    )
    assert status_code == 200
    assert dismiss_body["data"]["candidate"]["status"] == "dismissed"
    assert dismiss_body["data"]["candidate"]["dismissed_at"] is not None

    status_code, merge_body = call_json(
        app,
        f"/api/v1/polish-candidates/{merged['candidate_id']}/merge",
        "POST",
        json_body={"target_candidate_id": merge_target["candidate_id"]},
    )
    assert status_code == 200
    assert merge_body["data"]["candidate"]["status"] == "merged"
    assert merge_body["data"]["candidate"]["merge_target_candidate_id"] == merge_target["candidate_id"]

    status_code, archive_body = call_json(
        app,
        f"/api/v1/polish-candidates/{archived['candidate_id']}/archive",
        "POST",
    )
    assert status_code == 200
    assert archive_body["data"]["candidate"]["status"] == "archived"
    assert archive_body["data"]["candidate"]["archived_at"] is not None
    _assert_no_formal_memory_written(session_factory)


def test_confirm_enforces_owner_isolation_and_repeated_confirm_is_safe() -> None:
    session_factory = _session_factory()
    app_a = _isolated_candidates_app(session_factory, ACTOR_A)
    app_b = _isolated_candidates_app(session_factory, ACTOR_B)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    weakness = _candidate_by_type(app_a, "weakness_candidate")

    status_code, body_b = call_json(
        app_b,
        f"/api/v1/polish-candidates/{weakness['candidate_id']}/confirm",
        "POST",
    )
    assert status_code == 404
    assert body_b["error"]["code"] == "not_found_or_inaccessible"
    assert _table_count(session_factory, "weaknesses") == 0

    status_code, _ = call_json(
        app_a,
        f"/api/v1/polish-candidates/{weakness['candidate_id']}/confirm",
        "POST",
    )
    assert status_code == 200
    status_code, repeat_body = call_json(
        app_a,
        f"/api/v1/polish-candidates/{weakness['candidate_id']}/confirm",
        "POST",
    )
    assert status_code == 409
    assert repeat_body["error"]["code"] == "candidate_not_confirmable"
    assert _table_count(session_factory, "weaknesses") == 1


def test_confirm_failure_rolls_back_candidate_status_and_formal_write(monkeypatch) -> None:
    import app.infrastructure.db.repositories.polish_candidates as candidate_repo

    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    weakness = _candidate_by_type(app, "weakness_candidate")
    repository = SqlAlchemyPolishCandidateRepository(session_factory)

    def _raise_after_candidate_status_update(*args, **kwargs):
        raise RuntimeError("forced formal write failure")

    monkeypatch.setattr(candidate_repo, "_create_formal_weakness_from_candidate", _raise_after_candidate_status_update)

    with pytest.raises(RuntimeError, match="forced formal write failure"):
        repository.confirm_candidate(
            owner_id=OWNER_A,
            actor_id=ACTOR_A.actor_id,
            candidate_id=weakness["candidate_id"],
        )

    rolled_back = repository.get_candidate(owner_id=OWNER_A, candidate_id=weakness["candidate_id"])
    assert rolled_back["status"] == "candidate"
    assert rolled_back["target_formal_ref"] is None
    assert _table_count(session_factory, "weaknesses") == 0


def test_confirm_keeps_sanitizer_effective_on_formal_objects() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    weakness = _candidate_by_type(app, "weakness_candidate")
    asset_candidate = _candidate_by_type(app, "asset_candidate")

    call_json(app, f"/api/v1/polish-candidates/{weakness['candidate_id']}/confirm", "POST")
    call_json(app, f"/api/v1/polish-candidates/{asset_candidate['candidate_id']}/confirm", "POST")

    rows = _fetch_all(session_factory, "select * from weaknesses") + _fetch_all(session_factory, "select * from assets")
    forbidden = {
        "raw_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "hidden_rubric",
        "full_evidence_text",
        "full_resume",
        "full_jd",
        "api_key",
        "cookie",
        "secret",
        "token",
    }
    serialized = json.dumps([dict(row) for row in rows], ensure_ascii=False, default=str).lower()
    for forbidden_text in forbidden:
        assert forbidden_text not in serialized


def test_confirm_polished_answer_keeps_model_suggested_reference_out_of_user_fact() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    polished = _candidate_by_type(app, "polished_answer_candidate")

    status_code, body = call_json(
        app,
        f"/api/v1/polish-candidates/{polished['candidate_id']}/confirm",
        "POST",
    )

    assert status_code == 200
    asset_row = _fetch_one(
        session_factory,
        "select id, asset_type, fact_source, source_refs_json, content from assets",
    )
    assert asset_row["id"] == body["data"]["formal_ref"]["resource_id"]
    assert asset_row["asset_type"] == "polished_answer"
    assert asset_row["fact_source"] == "model_suggested_phrasing"
    assert asset_row["content"] == polished["evidence_excerpt"]
    assert any(ref["resource_type"] == "p7_reference_answer" for ref in _decode_json(asset_row["source_refs_json"]))


def test_confirm_training_suggestion_candidate_creates_training_recommendation_without_task() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    training = _candidate_by_type(app, "training_suggestion_candidate")

    status_code, body = call_json(
        app,
        f"/api/v1/polish-candidates/{training['candidate_id']}/confirm",
        "POST",
    )

    assert status_code == 200
    assert body["resource_type"] == "polish_candidate_action"
    result = body["data"]
    assert result["action"] == "confirm"
    assert result["candidate"]["status"] == "confirmed"
    assert result["candidate"]["target_formal_ref"]["resource_type"] == "training_recommendation"
    assert result["formal_ref"] == result["candidate"]["target_formal_ref"]
    assert _table_count(session_factory, "training_recommendations") == 1
    assert _table_count(session_factory, "training_tasks") == 0

    row = _fetch_one(
        session_factory,
        "select id, owner_id, title, summary, status, confidence_level, source_refs_json, "
        "evidence_refs_json, trace_refs_json, created_from_candidate_id, user_confirmation_ref_json, "
        "question_pattern, expected_answer_dimensions_json, target_weakness_refs_json "
        "from training_recommendations",
    )
    assert row["id"] == result["formal_ref"]["resource_id"]
    assert row["owner_id"] == OWNER_A
    assert row["title"] == training["title"]
    assert row["summary"] == training["summary"]
    assert row["status"] == "confirmed"
    assert row["confidence_level"] == training["confidence_level"]
    assert row["created_from_candidate_id"] == training["candidate_id"]
    assert _decode_json(row["user_confirmation_ref_json"])["resource_type"] == "user_confirmation"
    assert _decode_json(row["trace_refs_json"])
    assert _decode_json(row["evidence_refs_json"])
    assert row["question_pattern"] or _decode_json(row["target_weakness_refs_json"])
    assert _decode_json(row["expected_answer_dimensions_json"])


def test_training_recommendation_list_is_owner_scoped() -> None:
    session_factory = _session_factory()
    app_a = _isolated_candidates_app(session_factory, ACTOR_A)
    app_b = _isolated_candidates_app(session_factory, ACTOR_B)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    _create_feedback_payload(session_factory, ACTOR_B, OWNER_B)
    training_a = _candidate_by_type(app_a, "training_suggestion_candidate")
    training_b = _candidate_by_type(app_b, "training_suggestion_candidate")
    call_json(app_a, f"/api/v1/polish-candidates/{training_a['candidate_id']}/confirm", "POST")
    call_json(app_b, f"/api/v1/polish-candidates/{training_b['candidate_id']}/confirm", "POST")

    status_code, body_a = call_json(app_a, "/api/v1/training-suggestions")
    status_code_b, body_b = call_json(app_b, "/api/v1/training-suggestions")

    assert status_code == 200
    assert status_code_b == 200
    assert len(body_a["data"]) == 1
    assert len(body_b["data"]) == 1
    assert body_a["data"][0]["owner_id"] == OWNER_A
    assert body_b["data"][0]["owner_id"] == OWNER_B
    assert body_a["data"][0]["training_recommendation_id"] != body_b["data"][0]["training_recommendation_id"]


def test_training_recommendation_can_be_dismissed_by_owner() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    training = _candidate_by_type(app, "training_suggestion_candidate")
    _, confirm_body = call_json(
        app,
        f"/api/v1/polish-candidates/{training['candidate_id']}/confirm",
        "POST",
    )
    recommendation_id = confirm_body["data"]["formal_ref"]["resource_id"]

    status_code, body = call_json(
        app,
        f"/api/v1/training-suggestions/{recommendation_id}/dismiss",
        "POST",
    )

    assert status_code == 200
    assert body["data"]["status"] == "dismissed"
    assert body["data"]["user_confirmation_ref"]["resource_type"] == "user_confirmation"


def test_training_task_requires_explicit_user_action_and_completion_only_returns_progress_hint() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _create_feedback_payload(session_factory, ACTOR_A, OWNER_A)
    training = _candidate_by_type(app, "training_suggestion_candidate")
    _, confirm_body = call_json(
        app,
        f"/api/v1/polish-candidates/{training['candidate_id']}/confirm",
        "POST",
    )
    recommendation_id = confirm_body["data"]["formal_ref"]["resource_id"]
    assert _table_count(session_factory, "training_tasks") == 0
    baseline_formal_count = _table_count(session_factory, "weaknesses") + _table_count(session_factory, "assets")

    status_code, start_body = call_json(
        app,
        f"/api/v1/training-suggestions/{recommendation_id}/tasks",
        "POST",
    )

    assert status_code == 200
    task = start_body["data"]
    assert task["status"] == "in_progress"
    assert task["training_recommendation_id"] == recommendation_id
    assert _table_count(session_factory, "training_tasks") == 1

    status_code, complete_body = call_json(
        app,
        f"/api/v1/training-suggestions/{recommendation_id}/tasks/{task['training_task_id']}/complete",
        "POST",
    )

    assert status_code == 200
    completed = complete_body["data"]
    assert completed["status"] == "completed"
    assert completed["progress_update_hint"]["resource_type"] == "training_progress_hint"
    assert completed["progress_update_hint"]["training_task_id"] == task["training_task_id"]
    assert completed["progress_update_hint"]["writes_formal_memory"] is False
    assert _table_count(session_factory, "weaknesses") + _table_count(session_factory, "assets") == baseline_formal_count


def _isolated_candidates_app(session_factory, actor: CurrentActor) -> FastAPI:
    app = FastAPI()
    app.state.llm_transport = FakeLlmTransport()
    app.add_exception_handler(ApiHttpError, api_http_error_handler)
    app.include_router(build_api_v1_router("/api/v1"))

    async def _actor_override() -> CurrentActor:
        return actor

    async def _session_factory_override():
        return session_factory

    app.dependency_overrides[require_authenticated_actor] = _actor_override
    app.dependency_overrides[get_db_session_factory] = _session_factory_override
    return app


def _create_feedback_payload(session_factory, actor: CurrentActor, owner_id: str) -> dict[str, Any]:
    app = _isolated_polish_app(session_factory, actor)
    binding_id = _seed_polish_sources(session_factory, owner_id)
    _, create_body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )
    session_id = create_body["data"]["session_id"]
    progress_node_ref = create_body["data"]["progress_tree_state"]["current_priority"]["progress_node_ref"]
    _, question_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/questions",
        "POST",
        json_body={"progress_node_ref": progress_node_ref},
    )
    question_id = question_body["data"]["result_ref"]["trace_ref_id"]
    _, answer_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/answers",
        "POST",
        json_body={
            "question_id": question_id,
            "answer_text": "我会补充接口幂等、失败补偿、指标验证和上线复盘。",
        },
    )
    status_code, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_body["data"]["answer_id"]},
    )
    assert status_code == 202
    return feedback_body["data"]["feedback_payload"]


def _assert_no_formal_memory_written(session_factory) -> None:
    with session_factory() as db:
        for table_name in (
            "weaknesses",
            "weakness_candidates",
            "assets",
            "asset_versions",
            "training_recommendations",
        ):
            assert db.execute(text(f"select count(*) from {table_name}")).scalar_one() == 0


def _candidate_list(app: FastAPI) -> list[dict[str, Any]]:
    status_code, body = call_json(app, "/api/v1/polish-candidates")
    assert status_code == 200
    assert len(body["data"]) >= 4
    return body["data"]


def _candidate_by_type(app: FastAPI, candidate_type: str) -> dict[str, Any]:
    status_code, body = call_json(app, f"/api/v1/polish-candidates?candidate_type={candidate_type}")
    assert status_code == 200
    assert body["data"]
    return body["data"][0]


def _table_count(session_factory, table_name: str) -> int:
    with session_factory() as db:
        return int(db.execute(text(f"select count(*) from {table_name}")).scalar_one())


def _fetch_one(session_factory, query: str) -> dict[str, Any]:
    rows = _fetch_all(session_factory, query)
    assert len(rows) == 1
    return rows[0]


def _fetch_all(session_factory, query: str) -> list[dict[str, Any]]:
    with session_factory() as db:
        return [dict(row) for row in db.execute(text(query)).mappings().all()]


def _decode_json(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value
