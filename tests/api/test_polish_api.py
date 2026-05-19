from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.errors import ApiHttpError, api_http_error_handler
from app.api.v1.polish import router as polish_router
from app.application.polish.progress_prompts import (
    INITIAL_PROGRESS_TREE_PROMPT_CONTRACT,
    POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
    build_initial_progress_tree_prompt,
    build_progress_tree_state_refresh_prompt,
)
from app.application.polish.progress_evidence import (
    build_progress_evidence_chunks,
    build_progress_prompt_context,
    select_progress_tree_evidence_chunks,
)
from app.domain.auth.entities import CurrentActor
from app.domain.bindings.entities import ResumeJobBinding
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.refs import OwnerRef, VersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.infrastructure.db.models.interview import PolishSessionDetail as PolishSessionDetailModel
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from app.infrastructure.llm.errors import LlmTransportResponseError
from app.infrastructure.llm.fake_transport import FakeLlmTransport
from app.main import create_app
from tests.api.asgi_client import call_json


OWNER_A = "usr_polish_owner_a"
OWNER_B = "usr_polish_owner_b"
ACTOR_A = CurrentActor(
    actor_id=OWNER_A,
    owner_id=OWNER_A,
    roles=("user",),
    email_normalized="owner-a@example.com",
    display_name="Owner A",
)
ACTOR_B = CurrentActor(
    actor_id=OWNER_B,
    owner_id=OWNER_B,
    roles=("user",),
    email_normalized="owner-b@example.com",
    display_name="Owner B",
)


def test_polish_topics_require_authentication() -> None:
    status_code, body = call_json(create_app(), "/api/v1/polish-topics")

    assert status_code == 401
    assert body["error"]["code"] == "unauthenticated"


def test_polish_topics_return_controlled_catalog_with_binding_context() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    transport = _RecordingPolishProgressTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=transport)

    status_code, body = call_json(
        app,
        f"/api/v1/polish-topics?resume_job_binding_id={binding_id}",
    )

    assert status_code == 200
    assert body["resource_type"] == "polish_topic_list"
    topics = body["data"]
    assert [topic["topic_id"] for topic in topics] == [
        "topic_authenticity_contribution",
        "topic_technical_depth",
        "topic_scenario_roleplay",
        "topic_risk_defense",
    ]
    assert topics[0]["requires_job_binding"] is True
    assert topics[0]["subtopics"] == []


def test_polish_topics_reject_cross_owner_binding() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_B)

    status_code, body = call_json(
        app,
        f"/api/v1/polish-topics?resume_job_binding_id={binding_id}",
    )

    assert status_code == 404
    assert body["error"]["code"] == "not_found_or_inaccessible"


def test_polish_session_list_requires_authentication() -> None:
    status_code, body = call_json(create_app(), "/api/v1/polish-sessions")

    assert status_code == 401
    assert body["error"]["code"] == "unauthenticated"


def test_polish_session_list_returns_empty_for_authenticated_owner() -> None:
    session_factory = _session_factory()
    app = _isolated_polish_app(session_factory, ACTOR_A)

    status_code, body = call_json(app, "/api/v1/polish-sessions")

    assert status_code == 200
    assert body["resource_type"] == "polish_session_list"
    assert body["data"] == []


def test_polish_session_list_returns_owner_scoped_summaries() -> None:
    session_factory = _session_factory()
    binding_a = _seed_polish_sources(session_factory, OWNER_A)
    binding_b = _seed_polish_sources(session_factory, OWNER_B)
    app_a = _isolated_polish_app(session_factory, ACTOR_A)
    app_b = _isolated_polish_app(session_factory, ACTOR_B)

    _, create_a = call_json(
        app_a,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_a,
            "topic_id": "topic_authenticity_contribution",
            "custom_topic_text": "Backend API polish",
        },
    )
    _, create_b = call_json(
        app_b,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_b,
            "topic_id": "topic_scenario_roleplay",
            "custom_topic_text": "Behavioral polish",
        },
    )

    status_code, body = call_json(app_a, "/api/v1/polish-sessions")

    assert status_code == 200
    assert body["resource_type"] == "polish_session_list"
    sessions = body["data"]
    assert len(sessions) == 1
    assert sessions[0]["id"] == create_a["data"]["session_id"]
    assert sessions[0]["session_id"] == create_a["data"]["session_id"]
    assert sessions[0]["session_id"] != create_b["data"]["session_id"]
    assert sessions[0]["title"] == "Backend API polish"
    assert sessions[0]["status"] == "running"
    assert sessions[0]["mode"] == "polish"
    assert sessions[0]["resume_job_binding_id"] == binding_a
    assert sessions[0]["topic_id"] == "topic_authenticity_contribution"
    assert sessions[0]["subtopic_id"] is None
    assert "turns" not in sessions[0]
    assert sessions[0]["job_title"] == "Backend Engineer"
    assert sessions[0]["job_company"] == "ACME"
    assert sessions[0]["resume_title"] == "Backend Resume"
    assert sessions[0]["binding_label"] == "Backend Engineer / Backend Resume"
    assert sessions[0]["created_at"] is not None
    assert sessions[0]["updated_at"] is not None


def test_create_and_get_polish_session_persists_owner_scoped_context() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    transport = _RecordingPolishProgressTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=transport)

    status_code, body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_authenticity_contribution",
            "custom_topic_text": "请重点打磨支付系统项目的表达",
        },
    )

    assert status_code == 201
    assert body["resource_type"] == "polish_session"
    session_data = body["data"]
    assert session_data["mode"] == "polish"
    assert session_data["turns"] == []
    assert session_data["job_title"] == "Backend Engineer"
    assert session_data["job_company"] == "ACME"
    assert session_data["resume_title"] == "Backend Resume"
    assert session_data["binding_label"] == "Backend Engineer / Backend Resume"
    assert session_data["session_status"] == "running"
    assert session_data["resume_job_binding_id"] == binding_id
    assert session_data["topic_ref"]["topic_id"] == "topic_authenticity_contribution"
    assert session_data["subtopic_ref"] is None
    assert session_data["custom_topic_text_summary"] == "请重点打磨支付系统项目的表达"
    assert session_data["progress_tree_status"] == "ready"
    assert session_data["progress_tree_plan"]["schema_id"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID
    assert session_data["progress_tree_plan"]["schema_version"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION
    assert session_data["progress_tree_plan"]["prompt_version"] == POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION
    assert session_data["progress_tree_state"]["schema_id"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_ID
    assert session_data["progress_tree_state"]["schema_version"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION
    assert session_data["progress_tree_state"]["prompt_version"] == POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION
    assert session_data["progress_tree_plan"]["nodes"]
    assert session_data["progress_tree_plan"]["nodes"][0]["evidence_chunk_ids"]
    assert session_data["progress_tree_state"]["current_priority"]["progress_node_ref"]
    assert session_data["progress_tree_state"]["current_priority"]["progress_node_ref"] == "fake_llm_progress_backend_api_fastapi"
    progress_text = _progress_tree_text(session_data)
    assert "Own backend APIs for interview preparation workflows." in progress_text
    assert "Python and FastAPI experience." in progress_text
    assert "Built backend workflow automation." in progress_text
    assert "项目经历真实性核验" not in progress_text
    assert "高并发设计" not in progress_text
    assert "岗位版本内容和简历版本内容" in INITIAL_PROGRESS_TREE_PROMPT_CONTRACT
    assert "岗位名、简历名只能作为展示信息" in INITIAL_PROGRESS_TREE_PROMPT_CONTRACT
    assert "provider_payload" not in _collect_keys(session_data)
    assert "prompt" not in _collect_keys(session_data)
    assert transport.calls[0].task_type == "polish_progress_tree_plan"
    assert transport.calls[0].evidence_bundle["output_schema"]["schema_id"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID
    assert (
        transport.calls[0].evidence_bundle["output_schema"]["schema_version"]
        == POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION
    )
    prompt_context = transport.calls[0].evidence_bundle["context"]
    selected_text = str(prompt_context["selected_evidence_chunks"])
    assert "Own backend APIs for interview preparation workflows." in selected_text
    assert "Python and FastAPI experience." in selected_text
    assert "Built backend workflow automation." in selected_text
    assert "job_snapshot" not in prompt_context
    assert "resume_snapshot" not in prompt_context

    session_id = session_data["session_id"]
    status_code, body = call_json(app, f"/api/v1/polish-sessions/{session_id}")

    assert status_code == 200
    assert body["data"]["session_id"] == session_id
    assert body["data"]["resume_version_id"].startswith("res_ver_polish_")
    assert body["data"]["job_version_id"].startswith("job_ver_polish_")


def test_polish_progress_tree_returns_insufficient_context_without_job_or_resume_content() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(
        session_factory,
        OWNER_A,
        resume_markdown="",
        responsibilities=[],
        requirements=[],
        other_notes=None,
    )
    transport = _RecordingPolishProgressTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=transport)

    status_code, body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )

    assert status_code == 201
    session_data = body["data"]
    assert session_data["progress_tree_status"] == "insufficient_context"
    assert session_data["progress_percent"] == 0
    assert session_data["progress_tree_plan"]["nodes"] == []
    assert session_data["progress_tree_state"]["current_priority"] is None
    assert transport.calls == []


def test_progress_evidence_chunks_split_long_sources_and_keep_stable_ids() -> None:
    context = _progress_context_fixture(
        requirements=[
            "Python FastAPI 服务治理能力",
            "Kafka 事件驱动一致性和可观测性",
        ],
        responsibilities=[
            "负责核心 API 和异步任务稳定性",
        ],
        resume_markdown=(
            "# Summary\n"
            + ("长摘要内容 " * 900)
            + "\n## 项目经历\n"
            + "支付系统重构：使用 FastAPI、Kafka 和 PostgreSQL 完成一致性治理，补齐监控指标。\n"
            + "\n## 技能栈\n"
            + "Python / FastAPI / Kafka / PostgreSQL\n"
        ),
    )

    chunks = build_progress_evidence_chunks(context)
    chunk_ids = [chunk.chunk_id for chunk in chunks]

    assert "job_requirement_001" in chunk_ids
    assert "job_requirement_002" in chunk_ids
    assert "job_responsibility_001" in chunk_ids
    assert "resume_project_001" in chunk_ids
    assert "resume_skill_001" in chunk_ids
    assert [chunk.chunk_id for chunk in build_progress_evidence_chunks(context)] == chunk_ids
    assert any("支付系统重构" in chunk.text for chunk in chunks)
    assert not any(chunk.text == context["resume_snapshot"]["markdown_text"] for chunk in chunks)


def test_progress_evidence_selection_prioritizes_match_gaps_and_reports_dropped_chunks() -> None:
    context = _progress_context_fixture(
        requirements=[f"Requirement {index}" for index in range(1, 8)],
        responsibilities=[f"Responsibility {index}" for index in range(1, 4)],
        resume_markdown=(
            "## 项目经历\n支付系统一致性项目\n\n"
            "## 技能栈\nPython / FastAPI / Kafka\n\n"
            "## 工作经历\n负责后端平台稳定性治理"
        ),
        match_context={
            "available": True,
            "overall_score": 68,
            "summary": "存在关键匹配缺口",
            "matched_points": [],
            "missing_points": ["缺少 Kafka exactly-once 解释"],
            "improvement_points": [],
            "interview_focus": ["追问支付一致性方案"],
            "suggested_questions": ["请解释事务消息失败补偿"],
        },
    )

    selection = select_progress_tree_evidence_chunks(
        context,
        purpose="initial_plan",
        max_chunks=4,
        max_chars=600,
    )

    selected_ids = [chunk.chunk_id for chunk in selection.selected_chunks]
    assert "match_gap_001" in selected_ids
    assert "match_focus_001" in selected_ids
    assert len(selection.selected_chunks) <= 4
    assert sum(len(chunk.text) for chunk in selection.selected_chunks) <= 600
    assert selection.dropped_context_summary["dropped_chunks_count"] > 0
    assert "job_responsibility" in selection.dropped_context_summary["dropped_source_types"]


def test_progress_tree_prompts_use_selected_evidence_chunks_instead_of_raw_long_text() -> None:
    context = _progress_context_fixture(
        requirements=["Python FastAPI 后端深度", "Kafka 消息一致性"],
        resume_markdown=(
            "## 项目经历\n支付系统重构：FastAPI + Kafka + PostgreSQL。\n"
            "## 技能栈\nPython / FastAPI / Kafka"
        ),
    )

    initial_prompt = build_initial_progress_tree_prompt(context)

    assert initial_prompt["context"]["selected_evidence_chunks"]
    assert initial_prompt["selected_evidence_chunks"] == initial_prompt["context"]["selected_evidence_chunks"]
    assert "job_snapshot" not in initial_prompt["context"]
    assert "resume_snapshot" not in initial_prompt["context"]
    assert "evidence_chunk_ids" in initial_prompt["prompt"]
    assert "不要编造 selected_evidence_chunks 中不存在的项目、技术栈、业务经验或岗位要求" in initial_prompt["prompt"]

    state_prompt = build_progress_tree_state_refresh_prompt(
        context=context,
        existing_plan={
            "status": "ready",
            "nodes": [
                {
                    "progress_node_ref": "capability.kafka",
                    "title": "Kafka 一致性",
                    "expected_capability": "解释支付消息一致性",
                    "evidence_chunk_ids": ["job_requirement_002", "resume_project_001"],
                    "children": [],
                }
            ],
        },
        existing_state={
            "status": "ready",
            "node_states": [],
            "current_priority": {"progress_node_ref": "capability.kafka"},
        },
    )
    assert state_prompt["context"]["selected_evidence_chunks"]
    assert state_prompt["context"]["turns_summary"]
    assert "selected_evidence_chunks" in state_prompt["prompt"]
    assert "不得删除或重命名 existing plan.nodes" in state_prompt["prompt"]


def test_polish_progress_tree_invalid_llm_output_returns_failed_without_raw_prompt() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=_InvalidProgressTreeTransport())

    status_code, body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )

    assert status_code == 201
    session_data = body["data"]
    assert session_data["progress_tree_status"] == "failed"
    assert session_data["progress_tree_plan"]["nodes"] == []
    assert "provider_payload" not in _collect_keys(session_data)
    assert "prompt" not in _collect_keys(session_data)
    assert "raw_completion" not in _collect_keys(session_data)


def test_polish_progress_tree_missing_schema_metadata_is_safely_completed() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=_MissingSchemaProgressTreeTransport())

    status_code, body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )

    assert status_code == 201
    session_data = body["data"]
    assert session_data["progress_tree_status"] == "ready"
    assert session_data["progress_tree_plan"]["schema_id"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID
    assert session_data["progress_tree_plan"]["schema_version"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION
    assert session_data["progress_tree_plan"]["prompt_version"] == POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION
    assert session_data["progress_tree_state"]["schema_id"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_ID
    assert session_data["progress_tree_state"]["schema_version"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION
    assert session_data["progress_tree_state"]["prompt_version"] == POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION


def test_progress_tree_parser_backfills_missing_evidence_chunk_ids() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=_MissingEvidenceChunkIdsTransport())

    status_code, body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )

    assert status_code == 201
    node = body["data"]["progress_tree_plan"]["nodes"][0]
    child = node["children"][0]
    assert node["evidence_chunk_ids"] == []
    assert child["evidence_chunk_ids"] == []


def test_polish_progress_tree_requires_semantic_evidence_not_titles_only() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(
        session_factory,
        OWNER_A,
        resume_markdown="# Summary\n泛泛的个人介绍。",
        responsibilities=[],
        requirements=["Python and FastAPI experience."],
        other_notes=None,
    )
    transport = _RecordingPolishProgressTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=transport)

    status_code, body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )

    assert status_code == 201
    assert body["data"]["progress_tree_status"] == "insufficient_context"
    assert body["data"]["progress_tree_plan"]["nodes"] == []
    assert transport.calls == []


def test_progress_tree_refresh_regenerates_missing_persisted_plan_when_context_is_sufficient() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    transport = _RecordingPolishProgressTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=transport)
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
    _clear_progress_tree_storage(session_factory, session_id)
    transport.calls.clear()

    status_code, refresh_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/progress-tree/state",
        "POST",
        json_body={},
    )

    assert status_code == 200
    data = refresh_body["data"]
    assert data["progress_tree_status"] == "ready"
    assert data["progress_tree_plan"]["nodes"]
    assert data["progress_tree_state"]["node_states"]
    assert data["progress_tree_state"]["current_priority"]["progress_node_ref"]
    assert [call.task_type for call in transport.calls] == ["polish_progress_tree_plan"]


def test_progress_tree_refresh_keeps_insufficient_context_without_calling_llm() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(
        session_factory,
        OWNER_A,
        resume_markdown="",
        responsibilities=[],
        requirements=[],
        other_notes=None,
    )
    transport = _RecordingPolishProgressTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=transport)
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

    status_code, refresh_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/progress-tree/state",
        "POST",
        json_body={},
    )

    assert status_code == 200
    assert refresh_body["data"]["progress_tree_status"] == "insufficient_context"
    assert refresh_body["data"]["progress_tree_plan"]["nodes"] == []
    assert transport.calls == []


def test_initial_progress_tree_keeps_valid_plan_when_initial_state_is_invalid() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=_InvalidInitialStateProgressTreeTransport())

    status_code, body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )

    assert status_code == 201
    session_data = body["data"]
    assert session_data["progress_tree_status"] == "ready"
    assert session_data["progress_tree_plan"]["nodes"]
    assert session_data["progress_tree_plan"].get("failure_reason") is None
    assert session_data["progress_tree_state"]["status"] == "ready"
    assert session_data["progress_tree_state"]["node_states"]
    assert session_data["progress_tree_state"]["current_priority"]["progress_node_ref"]
    assert session_data["progress_tree_state"]["progress"]["progress_percent"] == 0
    assert session_data["progress_tree_state"]["failure_reason"] == "llm_state_invalid_state_fallback"


def test_progress_tree_refresh_invalid_state_keeps_plan_and_returns_refresh_failed() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    transport = _InvalidRefreshStateProgressTreeTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=transport)
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
    original_nodes = create_body["data"]["progress_tree_plan"]["nodes"]

    status_code, refresh_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/progress-tree/state",
        "POST",
        json_body={},
    )

    assert status_code == 200
    data = refresh_body["data"]
    assert data["progress_tree_status"] == "refresh_failed"
    assert data["progress_tree_plan"]["nodes"] == original_nodes
    assert data["progress_tree_state"]["status"] == "refresh_failed"
    assert data["progress_tree_state"]["node_states"]
    assert data["progress_tree_state"]["failure_reason"] == "llm_state_invalid"


def test_get_polish_session_does_not_regenerate_progress_tree() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    transport = _RecordingPolishProgressTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=transport)
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
    _clear_progress_tree_storage(session_factory, session_id)
    transport.calls.clear()

    status_code, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")

    assert status_code == 200
    assert detail_body["data"]["progress_tree_status"] == "insufficient_context"
    assert detail_body["data"]["progress_tree_plan"]["nodes"] == []
    assert transport.calls == []


def test_polish_question_answer_and_feedback_task_core() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_A)
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
    original_plan_nodes = create_body["data"]["progress_tree_plan"]["nodes"]

    status_code, question_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/questions",
        "POST",
        json_body={"progress_node_ref": progress_node_ref},
    )

    assert status_code == 202
    assert question_body["status"] == "accepted"
    assert question_body["resource_type"] == "ai_task"
    assert question_body["data"]["task_type"] == "polish_question_generation"
    assert question_body["data"]["status"] == "succeeded"
    assert question_body["data"]["contract_ids"] == ["P-POLISH-002", "P-SHARED-001", "P-SHARED-003"]
    question_ref = question_body["data"]["result_ref"]
    assert question_ref["trace_type"] == "question"
    question_id = question_ref["trace_ref_id"]

    answer_text = "我会先说明项目背景，再解释我负责的核心接口和取舍。"
    status_code, answer_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/answers",
        "POST",
        json_body={
            "question_id": question_id,
            "answer_text": answer_text,
            "base_question_version_ref": {"resource_type": "question", "resource_id": question_id, "version_id": "1"},
        },
    )

    assert status_code == 201
    assert answer_body["resource_type"] == "polish_answer"
    assert answer_body["data"]["answer_round"] == 1
    assert answer_body["data"]["question_id"] == question_id
    answer_id = answer_body["data"]["answer_id"]

    status_code, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )

    assert status_code == 202
    assert feedback_body["resource_type"] == "ai_task"
    assert feedback_body["data"]["task_type"] == "polish_feedback_generation"
    assert feedback_body["data"]["status"] == "succeeded"
    assert feedback_body["data"]["score_type"] == "polish_answer"
    assert feedback_body["data"]["candidate_refs"] == []
    assert feedback_body["data"]["suggestion_refs"] == []
    assert "provider_payload" not in _collect_keys(feedback_body)

    status_code, refresh_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/progress-tree/state",
        "POST",
        json_body={},
    )
    assert status_code == 200
    assert refresh_body["data"]["progress_tree_plan"]["nodes"] == original_plan_nodes
    assert refresh_body["data"]["progress_tree_state"]["current_priority"]["progress_node_ref"] == progress_node_ref
    assert refresh_body["data"]["progress_tree_state"]["schema_id"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_ID
    assert (
        refresh_body["data"]["progress_tree_state"]["schema_version"]
        == POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION
    )
    assert (
        refresh_body["data"]["progress_tree_state"]["prompt_version"]
        == POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION
    )
    assert refresh_body["data"]["progress_tree_state"]["progress"]["progress_percent"] == 100

    status_code, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    assert status_code == 200
    assert detail_body["resource_type"] == "polish_session"
    detail_data = detail_body["data"]
    assert detail_data["job_title"] == "Backend Engineer"
    assert detail_data["job_company"] == "ACME"
    assert detail_data["resume_title"] == "Backend Resume"
    assert detail_data["binding_label"] == "Backend Engineer / Backend Resume"

    turns = detail_data["turns"]
    assert isinstance(turns, list) and len(turns) == 1
    question_text = turns[0]["question_text"]
    assert "Python and FastAPI experience." in question_text
    assert "Built backend workflow automation." in question_text
    assert "岗位要求/职责依据" in question_text
    assert turns[0]["answers"], "answers should be returned for submitted question"
    assert turns[0]["answers"][0]["answer_text"] == answer_text
    assert turns[0]["answers"][0]["feedback_text"] != "本轮反馈尚未生成"
    assert "polish_answer" in turns[0]["answers"][0]["feedback_text"]
    assert detail_data["progress_tree_state"]["updated_from_turns_count"] == 1
    state_text = str(detail_data["progress_tree_state"])
    assert "Fake LLM 状态刷新" in state_text


def test_polish_next_question_uses_progress_node_evidence_chunks() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(
        session_factory,
        OWNER_A,
        resume_markdown=(
            "## 项目经历\n"
            "支付系统重构：使用 FastAPI、Kafka、Outbox 和 PostgreSQL 完成一致性治理。\n"
            "## 技能栈\nPython / FastAPI / Kafka"
        ),
        requirements=[
            "需要候选人解释 Kafka 事务消息、Outbox 和最终一致性。",
            "需要掌握 FastAPI 服务治理。",
        ],
    )
    app = _isolated_polish_app(session_factory, ACTOR_A)
    _, create_body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={"resume_job_binding_id": binding_id},
    )
    session_id = create_body["data"]["session_id"]
    progress_node_ref = create_body["data"]["progress_tree_state"]["current_priority"]["progress_node_ref"]

    status_code, question_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/questions",
        "POST",
        json_body={"progress_node_ref": progress_node_ref},
    )

    assert status_code == 202
    question_id = question_body["data"]["result_ref"]["trace_ref_id"]
    _, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    question_text = next(
        turn["question_text"]
        for turn in detail_body["data"]["turns"]
        if turn["question_id"] == question_id
    )
    assert "Kafka 事务消息" in question_text
    assert "支付系统重构" in question_text


def test_polish_session_returns_latest_feedback_when_multiple_feedback_records_exist() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_A)
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
            "answer_text": "第一轮回答。",
        },
    )
    answer_id = answer_body["data"]["answer_id"]

    call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )
    _, second_feedback = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )

    status_code, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    assert status_code == 200
    turns = detail_body["data"]["turns"]
    assert isinstance(turns, list) and len(turns) == 1
    answers = turns[0]["answers"]
    assert answers, "answers should exist"
    assert answers[0]["answer_text"] == "第一轮回答。"
    assert answers[0]["feedback_id"] == second_feedback["data"]["result_ref"]["trace_ref_id"]


def test_polish_answer_rejects_blank_text_with_error_envelope() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_A)
    _, create_body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={"resume_job_binding_id": binding_id},
    )
    session_id = create_body["data"]["session_id"]
    _, question_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/questions",
        "POST",
        json_body={},
    )
    question_id = question_body["data"]["result_ref"]["trace_ref_id"]

    status_code, body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/answers",
        "POST",
        json_body={"question_id": question_id, "answer_text": "   "},
    )

    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"
    assert body["error"]["details"]["field"] == "answer_text"


def test_polish_progress_tree_prompt_governance_is_documented_and_not_in_provider_adapter() -> None:
    provider_adapter = Path("apps/api/app/infrastructure/llm/openai_compatible.py").read_text(encoding="utf-8")
    assert "进展树规划器" not in provider_adapter
    assert "岗位版本内容、简历版本内容" not in provider_adapter
    assert "不得返回通用技术分类" not in provider_adapter

    prompt_spec = Path("docs/02-design/PROMPT_SPEC.md").read_text(encoding="utf-8")
    polish_contracts = Path("docs/02-design/prompt-contracts/POLISH_CONTRACTS.md").read_text(encoding="utf-8")
    for text in (prompt_spec, polish_contracts):
        assert "polish_progress_tree_plan" in text
        assert "polish_progress_tree_state" in text
        assert POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID in text
        assert POLISH_PROGRESS_TREE_STATE_SCHEMA_ID in text


class _RecordingPolishProgressTransport(FakeLlmTransport):
    def __init__(self) -> None:
        self.calls = []

    def generate(self, request):
        self.calls.append(request)
        return super().generate(request)


class _InvalidProgressTreeTransport:
    def generate(self, request):
        if request.task_type == "polish_progress_tree_plan":
            raise LlmTransportResponseError("invalid json")
        return FakeLlmTransport().generate(request)


class _MissingSchemaProgressTreeTransport(FakeLlmTransport):
    def generate(self, request):
        result = super().generate(request)
        if request.task_type in {"polish_progress_tree_plan", "polish_progress_tree_state"}:
            result.result.pop("schema_id", None)
            result.result.pop("schema_version", None)
            result.result.pop("prompt_version", None)
            for field in ("progress_tree_plan", "progress_tree_state"):
                payload = result.result.get(field)
                if isinstance(payload, dict):
                    payload.pop("schema_id", None)
                    payload.pop("schema_version", None)
                    payload.pop("prompt_version", None)
        return result


class _MissingEvidenceChunkIdsTransport(FakeLlmTransport):
    def generate(self, request):
        result = super().generate(request)
        if request.task_type == "polish_progress_tree_plan":
            for node in result.result["progress_tree_plan"]["nodes"]:
                _remove_evidence_chunk_ids(node)
        return result


class _InvalidInitialStateProgressTreeTransport(FakeLlmTransport):
    def generate(self, request):
        result = super().generate(request)
        if request.task_type == "polish_progress_tree_plan":
            result.result.pop("progress_tree_state", None)
        return result


class _InvalidRefreshStateProgressTreeTransport(FakeLlmTransport):
    def generate(self, request):
        result = super().generate(request)
        if request.task_type == "polish_progress_tree_state":
            result.result["progress_tree_state"] = {
                "status": "ready",
                "node_states": [],
                "current_priority": None,
                "progress": {"progress_percent": 80},
            }
        return result


def _session_factory():
    settings = DbSettings(database_url="sqlite+pysqlite:///:memory:")
    session_factory = build_session_factory(settings)
    initialize_schema(session_factory=session_factory)
    return session_factory


def _isolated_polish_app(
    session_factory,
    actor: CurrentActor,
    *,
    llm_transport=None,
) -> FastAPI:
    app = FastAPI()
    app.state.llm_transport = llm_transport or FakeLlmTransport()
    app.add_exception_handler(ApiHttpError, api_http_error_handler)
    app.include_router(polish_router, prefix="/api/v1")

    async def _actor_override() -> CurrentActor:
        return actor

    async def _session_factory_override():
        return session_factory

    app.dependency_overrides[require_authenticated_actor] = _actor_override
    app.dependency_overrides[get_db_session_factory] = _session_factory_override
    return app


def _seed_polish_sources(
    session_factory,
    owner_id: str,
    *,
    resume_markdown: str = "## 项目经历\nBuilt backend workflow automation.",
    responsibilities: list[str] | None = None,
    requirements: list[str] | None = None,
    other_notes: str | None = "PostgreSQL is a plus.",
) -> str:
    now = utc_now()
    resume_id = f"res_polish_{owner_id}"
    resume_version_id = f"res_ver_polish_{owner_id}"
    job_id = f"job_polish_{owner_id}"
    job_version_id = f"job_ver_polish_{owner_id}"
    binding_id = f"bind_polish_{owner_id}"

    SqlAlchemyResumeRepository(session_factory).create_with_version(
        Resume(
            resume_id=resume_id,
            owner_ref=OwnerRef(owner_id=owner_id),
            current_version_ref=VersionRef(
                resource_type="resume",
                resource_id=resume_id,
                version_id=resume_version_id,
            ),
            status="active",
            title="Backend Resume",
            file_name="resume.md",
            created_at=now,
            updated_at=now,
        ),
        ResumeVersion(
            resume_version_id=resume_version_id,
            owner_id=owner_id,
            resume_id=resume_id,
            version_number=1,
            markdown_text=resume_markdown,
            status="current",
            created_at=now,
        ),
    )

    job_repository = SqlAlchemyJobRepository(session_factory)
    job_repository.create_job(
        Job(
            job_id=job_id,
            owner_id=owner_id,
            title="Backend Engineer",
            company="ACME",
            department="Engineering",
            application_status="draft",
            status="active",
            current_version_id=job_version_id,
            record_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    job_repository.create_job_version(
        JobVersion(
            job_version_id=job_version_id,
            owner_id=owner_id,
            job_id=job_id,
            version_number=1,
            responsibilities=responsibilities
            if responsibilities is not None
            else ["Own backend APIs for interview preparation workflows."],
            requirements=requirements if requirements is not None else ["Python and FastAPI experience."],
            other_notes=other_notes,
            status="current",
            created_at=now,
        )
    )

    SqlAlchemyBindingRepository(session_factory).add(
        ResumeJobBinding(
            binding_id=binding_id,
            owner_id=owner_id,
            resume_id=resume_id,
            job_id=job_id,
            resume_version_id=resume_version_id,
            job_version_id=job_version_id,
            status="active",
            record_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return binding_id


def _progress_context_fixture(
    *,
    requirements: list[str] | None = None,
    responsibilities: list[str] | None = None,
    resume_markdown: str = "## 项目经历\nBuilt backend workflow automation.",
    match_context: dict | None = None,
) -> dict:
    context = {
        "session": {
            "session_id": "sess_test",
            "mode": "polish",
            "topic": "topic_technical_depth",
            "subtopic": None,
            "custom_topic": None,
        },
        "job_snapshot": {
            "job_id": "job_test",
            "job_version_id": "job_ver_test",
            "title": "Backend Engineer",
            "company": "ACME",
            "department": "Engineering",
            "responsibilities": responsibilities or ["Own backend APIs."],
            "requirements": requirements or ["Python and FastAPI experience."],
            "other_notes": "PostgreSQL is a plus.",
            "application_status": "draft",
            "content_digest": "job-digest",
        },
        "resume_snapshot": {
            "resume_id": "res_test",
            "resume_version_id": "res_ver_test",
            "title": "Backend Resume",
            "markdown_text": resume_markdown,
            "summary": "Backend resume",
            "skills": [],
            "project_experiences": [],
            "work_experiences": [],
            "content_digest": "resume-digest",
        },
        "match_context": match_context
        or {
            "available": False,
            "overall_score": None,
            "summary": None,
            "matched_points": [],
            "missing_points": [],
            "improvement_points": [],
            "interview_focus": [],
            "suggested_questions": [],
        },
        "weakness_context": {"items": []},
        "asset_context": {"items": []},
        "turns": [
            {
                "turn_index": 1,
                "question_text": "请解释支付一致性方案。",
                "answer_text": "我使用 Outbox 推动最终一致性。",
                "feedback_text": "需要补充 Kafka 失败补偿和指标。",
                "answers": [],
            }
        ],
        "content_digest": "context-digest",
    }
    context["prompt_context"] = build_progress_prompt_context(context, purpose="initial_plan")
    return context


def _remove_evidence_chunk_ids(node: dict) -> None:
    node.pop("evidence_chunk_ids", None)
    for child in node.get("children", []):
        _remove_evidence_chunk_ids(child)


def _clear_progress_tree_storage(session_factory, session_id: str) -> None:
    with session_factory() as db:
        detail = db.get(PolishSessionDetailModel, f"{session_id}_detail")
        assert detail is not None
        detail.progress_tree_status = None
        detail.progress_percent = None
        detail.progress_tree_plan_json = None
        detail.progress_tree_state_json = None
        db.commit()


def _progress_tree_text(session_data: dict) -> str:
    nodes = session_data["progress_tree_plan"]["nodes"]
    return str(nodes)


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for item in value.values():
            keys.update(_collect_keys(item))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_collect_keys(item))
        return keys
    return set()
