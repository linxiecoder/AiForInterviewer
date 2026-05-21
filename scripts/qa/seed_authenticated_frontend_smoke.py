from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import gettempdir
from urllib.parse import unquote

from sqlalchemy import delete

from app.infrastructure.db.models.binding import ResumeJobBinding as BindingModel
from app.infrastructure.db.models.interview import InterviewSession as InterviewSessionModel
from app.infrastructure.db.models.interview import PolishSessionDetail as PolishSessionDetailModel
from app.infrastructure.db.models.job import Job as JobModel
from app.infrastructure.db.models.job import JobVersion as JobVersionModel
from app.infrastructure.db.models.question import Question as QuestionModel
from app.infrastructure.db.models.resume import Resume as ResumeModel
from app.infrastructure.db.models.resume import ResumeVersion as ResumeVersionModel
from app.application.polish.entities import PolishQuestion, PolishQuestionSource, PolishSession
from app.domain.bindings.entities import ResumeJobBinding
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from app.domain.shared.refs import OwnerRef, VersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


def main() -> None:
    database_url = _required_smoke_database_url()
    dev_email = os.getenv("API_AUTH_DEV_USER_EMAIL", "developer@example.com").strip().lower()
    owner_id = stable_resource_id(ResourceIdPrefix.USER, dev_email)
    now = utc_now()
    session_factory = build_session_factory(DbSettings(database_url=database_url))
    initialize_schema(session_factory=session_factory)

    resume_id = "res_auth_frontend_smoke"
    resume_version_id = "res_ver_auth_frontend_smoke"
    job_id = "job_auth_frontend_smoke"
    job_version_id = "job_ver_auth_frontend_smoke"
    binding_id = "bind_auth_frontend_smoke"
    session_id = "ses_auth_frontend_smoke"
    question_id = "que_auth_frontend_smoke"
    progress_node_ref = "node_auth_frontend_smoke"

    _delete_existing_smoke_rows(
        session_factory=session_factory,
        resume_id=resume_id,
        resume_version_id=resume_version_id,
        job_id=job_id,
        job_version_id=job_version_id,
        binding_id=binding_id,
        session_id=session_id,
        question_id=question_id,
    )

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
            title="认证 smoke 简历",
            file_name="auth-smoke-resume.md",
            created_at=now,
            updated_at=now,
        ),
        ResumeVersion(
            resume_version_id=resume_version_id,
            owner_id=owner_id,
            resume_id=resume_id,
            version_number=1,
            markdown_text="## 项目经历\n负责登录态工作台验证、FastAPI API 编排和前端列表页联调。",
            status="current",
            created_at=now,
        ),
    )

    job_repository = SqlAlchemyJobRepository(session_factory)
    job_repository.create_job(
        Job(
            job_id=job_id,
            owner_id=owner_id,
            title="认证 smoke 后端工程师",
            company="AIFI",
            department="QA",
            application_status="interviewing",
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
            responsibilities=["维护登录后的前端工作台 smoke 与 API 契约验证。"],
            requirements=["熟悉 FastAPI、React、认证态接口和本地 QA 自动化。"],
            other_notes="测试不接真实 LLM，不依赖外部网络。",
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

    progress_tree_plan = {
        "status": "ready",
        "context_digest": "auth-frontend-smoke-digest",
        "nodes": [
            {
                "progress_node_ref": progress_node_ref,
                "title": "认证工作台 smoke 节点",
                "display_title": "认证工作台 smoke 节点",
                "category": "resume_deep_dive",
                "display_category_title": "深度打磨类",
                "expected_capability": "能说明登录后的列表与工作台路径如何稳定验证。",
                "related_job_requirements": ["熟悉认证态接口和本地 QA 自动化。"],
                "related_resume_evidence": ["负责登录态工作台验证。"],
                "missing_points": [],
                "depth_goal": "覆盖 authenticated list、session detail 和 question_metadata。",
                "children": [],
            }
        ],
    }
    progress_tree_state = {
        "status": "ready",
        "node_states": [
            {
                "progress_node_ref": progress_node_ref,
                "status": "in_progress",
                "completed_questions_count": 0,
                "latest_feedback_summary": None,
            }
        ],
        "current_priority": {
            "progress_node_ref": progress_node_ref,
            "title": "认证工作台 smoke 节点",
            "expected_capability": "能说明登录后的列表与工作台路径如何稳定验证。",
        },
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
    }

    polish_repository = SqlAlchemyPolishRepository(session_factory)
    polish_repository.add_session(
        PolishSession(
            session_id=session_id,
            owner_id=owner_id,
            actor_id=owner_id,
            binding_id=binding_id,
            resume_id=resume_id,
            resume_version_id=resume_version_id,
            job_id=job_id,
            job_version_id=job_version_id,
            status="running",
            topic_id="topic_authenticity_contribution",
            subtopic_id=None,
            custom_topic_text_summary="认证前端 smoke 主题",
            created_at=now,
            updated_at=now,
            polish_theme="mixed",
            progress_tree_status="ready",
            progress_percent=0,
            progress_tree_plan=progress_tree_plan,
            progress_tree_state=progress_tree_state,
        )
    )
    polish_repository.add_question(
        PolishQuestion(
            question_id=question_id,
            owner_id=owner_id,
            actor_id=owner_id,
            session_id=session_id,
            ai_task_id="task_auth_frontend_smoke",
            question_text="请说明你如何验证登录后的前端工作台路径。[1]",
            status="active",
            created_at=now,
            updated_at=now,
            question_sources=(
                PolishQuestionSource(
                    index=1,
                    source_type="progress_node",
                    title="认证工作台 smoke 节点",
                    excerpt="覆盖 authenticated list、session detail 和 question_metadata。",
                    ref_id=progress_node_ref,
                    availability="available",
                ),
            ),
            progress_node_ref=progress_node_ref,
            evidence_refs=(progress_node_ref,),
            context_digest="auth-frontend-smoke-digest",
            question_metadata={
                "question_pattern": "authenticated_frontend_smoke",
                "confidence_level": "medium",
                "low_confidence_flags": [],
                "expected_answer_dimensions": ["authenticated_list", "workbench_detail"],
                "quality_score": 88,
                "quality_warnings": [],
                "builder_version": "phase-2c-smoke",
                "validator_version": "phase-2c-smoke",
                "signal_version": "phase-2c-smoke",
                "source_availability": "available",
                "generated_at": now.isoformat(),
            },
        )
    )

    print(json.dumps({"session_id": session_id, "owner_id": owner_id}, ensure_ascii=True))


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"{name} is required")
    return value.strip()


def _required_smoke_database_url() -> str:
    database_url = _required_env("API_DATABASE_URL")
    if not database_url.startswith("sqlite+pysqlite:///"):
        raise RuntimeError("API_DATABASE_URL must point to the smoke SQLite database.")

    raw_path = unquote(database_url.removeprefix("sqlite+pysqlite:///"))
    database_path = Path(raw_path).resolve()
    temp_root = Path(gettempdir()).resolve()
    if not database_path.is_absolute() or not database_path.is_relative_to(temp_root):
        raise RuntimeError("Smoke seed database must be under the system temporary directory.")
    if database_path.name != "smoke.sqlite3" or not any(
        part.startswith("aifi-auth-smoke-") for part in database_path.parts
    ):
        raise RuntimeError("Smoke seed database path does not match the authenticated smoke temp layout.")
    return database_url


def _delete_existing_smoke_rows(
    *,
    session_factory,
    resume_id: str,
    resume_version_id: str,
    job_id: str,
    job_version_id: str,
    binding_id: str,
    session_id: str,
    question_id: str,
) -> None:
    with session_factory() as session:
        session.execute(delete(QuestionModel).where(QuestionModel.id == question_id))
        session.execute(delete(PolishSessionDetailModel).where(PolishSessionDetailModel.session_id == session_id))
        session.execute(delete(InterviewSessionModel).where(InterviewSessionModel.id == session_id))
        session.execute(delete(BindingModel).where(BindingModel.id == binding_id))
        session.execute(delete(JobVersionModel).where(JobVersionModel.id == job_version_id))
        session.execute(delete(JobModel).where(JobModel.id == job_id))
        session.execute(delete(ResumeVersionModel).where(ResumeVersionModel.id == resume_version_id))
        session.execute(delete(ResumeModel).where(ResumeModel.id == resume_id))
        session.commit()


if __name__ == "__main__":
    main()
