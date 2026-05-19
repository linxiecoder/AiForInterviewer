from __future__ import annotations

from fastapi import FastAPI

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.errors import ApiHttpError, api_http_error_handler
from app.api.v1.polish import router as polish_router
from app.domain.auth.entities import CurrentActor
from app.domain.bindings.entities import ResumeJobBinding
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.refs import OwnerRef, VersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
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
    app = _isolated_polish_app(session_factory, ACTOR_A)

    status_code, body = call_json(
        app,
        f"/api/v1/polish-topics?resume_job_binding_id={binding_id}",
    )

    assert status_code == 200
    assert body["resource_type"] == "polish_topic_list"
    topics = body["data"]
    assert [topic["topic_id"] for topic in topics] == [
        "topic_project_depth",
        "topic_system_design",
        "topic_behavioral",
    ]
    assert topics[0]["requires_job_binding"] is True
    assert topics[0]["subtopics"][0]["subtopic_id"].startswith("subtopic_")


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
            "topic_id": "topic_project_depth",
            "subtopic_id": "subtopic_project_impact",
            "custom_topic_text": "Backend API polish",
        },
    )
    _, create_b = call_json(
        app_b,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_b,
            "topic_id": "topic_behavioral",
            "subtopic_id": "subtopic_collaboration",
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
    assert sessions[0]["topic_id"] == "topic_project_depth"
    assert sessions[0]["subtopic_id"] == "subtopic_project_impact"
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
    app = _isolated_polish_app(session_factory, ACTOR_A)

    status_code, body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_project_depth",
            "subtopic_id": "subtopic_project_impact",
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
    assert session_data["topic_ref"]["topic_id"] == "topic_project_depth"
    assert session_data["subtopic_ref"]["subtopic_id"] == "subtopic_project_impact"
    assert session_data["custom_topic_text_summary"] == "请重点打磨支付系统项目的表达"

    session_id = session_data["session_id"]
    status_code, body = call_json(app, f"/api/v1/polish-sessions/{session_id}")

    assert status_code == 200
    assert body["data"]["session_id"] == session_id
    assert body["data"]["resume_version_id"].startswith("res_ver_polish_")
    assert body["data"]["job_version_id"].startswith("job_ver_polish_")


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
            "topic_id": "topic_system_design",
            "subtopic_id": "subtopic_tradeoff",
        },
    )
    session_id = create_body["data"]["session_id"]

    status_code, question_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/questions",
        "POST",
        json_body={"progress_node_ref": "node_backend_depth"},
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
    assert "topic_system_design" in question_text
    assert "node_backend_depth" in question_text
    assert turns[0]["answers"], "answers should be returned for submitted question"
    assert turns[0]["answers"][0]["answer_text"] == answer_text
    assert turns[0]["answers"][0]["feedback_text"] != "本轮反馈尚未生成"
    assert "polish_answer" in turns[0]["answers"][0]["feedback_text"]


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
            "topic_id": "topic_system_design",
            "subtopic_id": "subtopic_tradeoff",
        },
    )
    session_id = create_body["data"]["session_id"]

    _, question_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/questions",
        "POST",
        json_body={"progress_node_ref": "node_backend_depth"},
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


def _session_factory():
    settings = DbSettings(database_url="sqlite+pysqlite:///:memory:")
    session_factory = build_session_factory(settings)
    initialize_schema(session_factory=session_factory)
    return session_factory


def _isolated_polish_app(session_factory, actor: CurrentActor) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(ApiHttpError, api_http_error_handler)
    app.include_router(polish_router, prefix="/api/v1")

    async def _actor_override() -> CurrentActor:
        return actor

    async def _session_factory_override():
        return session_factory

    app.dependency_overrides[require_authenticated_actor] = _actor_override
    app.dependency_overrides[get_db_session_factory] = _session_factory_override
    return app


def _seed_polish_sources(session_factory, owner_id: str) -> str:
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
            markdown_text="# Summary\nBuilt backend workflow automation.",
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
            responsibilities=["Own backend APIs for interview preparation workflows."],
            requirements=["Python and FastAPI experience."],
            other_notes="PostgreSQL is a plus.",
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
