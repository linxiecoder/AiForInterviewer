from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    build_polish_question_persistence_plan,
)
from app.application.ai_runtime.contracts import GraphDisabledError, RuntimePolicyError, RuntimeValidationError
from app.application.ai_runtime.handoff import AgentPersistenceHandoff
from app.application.polish.commands import CreatePolishQuestionTaskCommand
from app.application.polish.entities import (
    PolishAnswer,
    PolishFeedback,
    PolishQuestion,
    PolishSession,
    PolishTaskStatus,
)
from app.application.polish.use_cases import PolishUseCases
from app.domain.bindings.entities import ResumeJobBinding
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import OwnerRef, ResourceRef, VersionRef


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
OWNER_ID = "usr_pr5_q4_owner"
ACTOR_ID = OWNER_ID
SESSION_ID = "ses_pr5_q4"
NODE_REF = "progress_node_q4_payment_consistency"


def test_persist_accepted_candidate_creates_question() -> None:
    repository = _PolishRepository(_session())
    plan = build_polish_question_persistence_plan(
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="aitask_q4_graph",
        agent_run_id="arun_q4_graph",
        candidate=_accepted_candidate(),
        progress_node_ref=NODE_REF,
        trace_refs=("trace_q4_graph",),
    )

    result = AgentPersistenceHandoff().write_question_result(plan, question_repository=repository, now=utc_now())

    assert result.question_ref.resource_type == "question"
    assert result.question.question_id == result.question_ref.resource_id
    assert result.question.ai_task_id == "aitask_q4_graph"
    assert result.question.question_text == _accepted_candidate()["question_text"]
    assert result.question.evidence_refs == ("resume_evidence_ref_q4",)
    assert result.question.progress_node_ref == NODE_REF
    assert result.task_status.result_ref.trace_type == "question"
    assert result.task_status.result_ref.trace_ref_id == result.question.question_id
    assert repository.questions == [result.question]


def test_persistence_rejects_blocked_quality_gate() -> None:
    repository = _PolishRepository(_session())

    with pytest.raises(RuntimeValidationError):
        plan = build_polish_question_persistence_plan(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            ai_task_id="aitask_q4_graph",
            agent_run_id="arun_q4_graph",
            candidate=_accepted_candidate(quality_gate={"status": "blocked", "passed": False}),
            progress_node_ref=NODE_REF,
            trace_refs=("trace_q4_graph",),
        )
        AgentPersistenceHandoff().write_question_result(plan, question_repository=repository, now=utc_now())

    assert repository.questions == []


def test_persistence_rejects_raw_payload() -> None:
    repository = _PolishRepository(_session())
    candidate = _accepted_candidate(raw_prompt="do not persist", provider_payload={"token": "secret"})

    with pytest.raises(RuntimePolicyError):
        plan = build_polish_question_persistence_plan(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            ai_task_id="aitask_q4_graph",
            agent_run_id="arun_q4_graph",
            candidate=candidate,
            progress_node_ref=NODE_REF,
            trace_refs=("trace_q4_graph",),
        )
        AgentPersistenceHandoff().write_question_result(plan, question_repository=repository, now=utc_now())

    assert repository.questions == []


def test_persistence_is_idempotent_for_same_candidate() -> None:
    repository = _PolishRepository(_session())
    handoff = AgentPersistenceHandoff()
    plan = build_polish_question_persistence_plan(
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="aitask_q4_graph",
        agent_run_id="arun_q4_graph",
        candidate=_accepted_candidate(),
        progress_node_ref=NODE_REF,
        trace_refs=("trace_q4_graph",),
    )

    first = handoff.write_question_result(plan, question_repository=repository, now=utc_now())
    second = handoff.write_question_result(plan, question_repository=repository, now=utc_now())

    assert len(repository.questions) == 1
    assert first.question.question_id == second.question.question_id
    assert first.created is True
    assert second.created is False


def test_graph_enabled_path_persists_question_without_legacy_llm() -> None:
    facade = _FakeQuestionFacade(status_ref=_GraphStatus(candidate=_accepted_candidate()))
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _LegacyQuestionLlmBlocker()
    use_cases._question_llm_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.ai_task_id == "aitask_q4_graph"
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert result.value.result_ref.trace_type == "question"
    assert len(repository.questions) == 1
    assert repository.questions[0].question_id == result.value.result_ref.trace_ref_id
    assert repository.add_question_calls == 1
    assert blocker.calls == 0


def test_graph_quality_block_does_not_fallback_to_legacy() -> None:
    facade = _FakeQuestionFacade(
        status_ref=_GraphStatus(candidate=_accepted_candidate(quality_gate={"status": "blocked", "passed": False}))
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _LegacyQuestionLlmBlocker()
    use_cases._question_llm_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert result.value.result_ref.trace_type == "agent_run"
    assert repository.questions == []
    assert blocker.calls == 0


def test_graph_disabled_still_uses_legacy() -> None:
    facade = _FakeQuestionFacade(error=GraphDisabledError("disabled"))
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert result.value.result_ref.trace_type == "question"
    assert len(repository.questions) == 1


def test_no_langgraph_import_in_application_layers() -> None:
    violations: list[str] = []
    for root in (
        APP_ROOT / "application" / "polish",
        APP_ROOT / "application" / "ai_runtime",
        APP_ROOT / "domain",
        APP_ROOT / "api",
    ):
        violations.extend(_find_forbidden_imports(root, forbidden_prefixes=("langgraph", "langchain")))

    assert violations == []


def _accepted_candidate(**overrides: Any) -> dict[str, Any]:
    candidate: dict[str, Any] = {
        "candidate_ref": "question_candidate_ref_q4",
        "question_text": "请围绕「支付链路一致性」回答。先说明业务背景、你的职责边界和目标，再讲清核心链路、关键技术取舍、失败处理或风险兜底、验证指标。",
        "question_sources": (
            {
                "index": 1,
                "source_type": "resume_project",
                "title": "支付链路一致性",
                "excerpt": "我负责支付链路状态流转、幂等和失败补偿。",
                "ref_id": "resume_evidence_ref_q4",
                "availability": "available",
            },
        ),
        "progress_node_ref": NODE_REF,
        "evidence_refs": ("resume_evidence_ref_q4",),
        "context_digest": "ctx_q4_graph",
        "question_pattern": "polish_structured_experience",
        "confidence_level": "high",
        "low_confidence_flags": (),
        "question_metadata": {"llm_generation_mode": "graph_candidate_handoff"},
        "trace_refs": ("trace_q4_graph", "validation_ref_q4", "question_candidate_ref_q4"),
        "quality_gate": {"status": "accepted", "passed": True, "blocking_reasons": ()},
        "sanitized": True,
    }
    candidate.update(overrides)
    return candidate


@dataclass(frozen=True)
class _GraphStatus:
    candidate: dict[str, Any]
    ai_task_id: str = "aitask_q4_graph"
    agent_run_id: str = "arun_q4_graph"
    status: str = "succeeded"
    trace_refs: tuple[str, ...] = ("trace_q4_graph",)
    candidate_refs: tuple[str, ...] = ("question_candidate_ref_q4",)
    interrupt_refs: tuple[str, ...] = ()
    formal_refs: tuple[str, ...] = ()


class _FakeQuestionFacade:
    def __init__(self, *, status_ref: _GraphStatus | None = None, error: Exception | None = None) -> None:
        self.status_ref = status_ref or _GraphStatus(candidate=_accepted_candidate())
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def start_polish_question_generation(
        self,
        *,
        owner_id: str,
        actor_id: str,
        session_ref: str,
        progress_node_refs: tuple[str, ...],
        completed_focus_refs: tuple[str, ...],
        idempotency_key: str,
    ) -> _GraphStatus:
        self.calls.append(
            {
                "owner_id": owner_id,
                "actor_id": actor_id,
                "session_ref": session_ref,
                "progress_node_refs": progress_node_refs,
                "completed_focus_refs": completed_focus_refs,
                "idempotency_key": idempotency_key,
            }
        )
        if self.error is not None:
            raise self.error
        return self.status_ref


class _LegacyQuestionLlmBlocker:
    def __init__(self) -> None:
        self.calls = 0

    def generate_with_llm_or_fallback(self, **_: Any) -> object:
        self.calls += 1
        raise AssertionError("legacy question LLM must not run when graph accepted candidate is persisted")


class _PolishRepository:
    def __init__(self, session: PolishSession) -> None:
        self.session = session
        self.questions: list[PolishQuestion] = []
        self.tasks: list[PolishTaskStatus] = []
        self.task_targets: list[str] = []
        self.add_question_calls = 0

    def add_session(self, session: PolishSession) -> None:
        self.session = session

    def update_progress_tree(self, session: PolishSession) -> None:
        self.session = session

    def list_sessions(self, owner_id: str) -> tuple[PolishSession, ...]:
        return (self.session,) if self.session.owner_id == owner_id else ()

    def get_session(self, owner_id: str, session_id: str) -> PolishSession | None:
        if self.session.owner_id == owner_id and self.session.session_id == session_id:
            return self.session
        return None

    def list_questions_for_session(self, owner_id: str, session_id: str) -> tuple[PolishQuestion, ...]:
        return tuple(
            question
            for question in self.questions
            if question.owner_id == owner_id and question.session_id == session_id
        )

    def add_question(self, question: PolishQuestion) -> None:
        self.add_question_calls += 1
        self.questions.append(question)

    def get_question(self, owner_id: str, question_id: str) -> PolishQuestion | None:
        return next(
            (
                question
                for question in self.questions
                if question.owner_id == owner_id and question.question_id == question_id
            ),
            None,
        )

    def add_answer(self, answer: PolishAnswer) -> None:
        raise NotImplementedError

    def get_answer(self, owner_id: str, answer_id: str) -> PolishAnswer | None:
        return None

    def list_answers_for_session(self, owner_id: str, session_id: str) -> tuple[PolishAnswer, ...]:
        return ()

    def count_answers_for_question(self, owner_id: str, question_id: str) -> int:
        return 0

    def add_feedback(self, feedback: PolishFeedback) -> None:
        raise NotImplementedError

    def list_feedbacks_for_session(self, owner_id: str, session_id: str) -> tuple[PolishFeedback, ...]:
        return ()

    def add_task(self, task: PolishTaskStatus, *, owner_id: str, actor_id: str, target_ref_id: str) -> None:
        self.tasks.append(task)
        self.task_targets.append(target_ref_id)

    def get_ref(self, session_id: str) -> ResourceRef | None:
        if session_id == self.session.session_id:
            return ResourceRef(resource_type="polish_session", resource_id=session_id)
        return None


class _ResumeRepository:
    def __init__(self, resume: Resume, resume_version: ResumeVersion) -> None:
        self.resume = resume
        self.resume_version = resume_version

    def get_ref(self, resume_id: str) -> ResourceRef | None:
        if resume_id == self.resume.resume_id:
            return ResourceRef(resource_type="resume", resource_id=resume_id)
        return None

    def get(self, resume_id: str) -> Resume | None:
        return self.resume if resume_id == self.resume.resume_id else None

    def get_version(self, resume_version_id: str) -> ResumeVersion | None:
        return self.resume_version if resume_version_id == self.resume_version.resume_version_id else None

    def list_by_owner(self, owner_id: str) -> list[Resume]:
        return [self.resume] if self.resume.owner_ref.owner_id == owner_id else []

    def add(self, resume: Resume) -> None:
        self.resume = resume

    def add_version(self, version: ResumeVersion) -> None:
        self.resume_version = version

    def create_with_version(self, resume: Resume, version: ResumeVersion) -> None:
        self.resume = resume
        self.resume_version = version


class _JobRepository:
    def __init__(self, job: Job, job_version: JobVersion) -> None:
        self.job = job
        self.job_version = job_version

    def get(self, job_id: str) -> Job | None:
        return self.job if job_id == self.job.job_id else None

    def list_by_owner(self, owner_id: str) -> list[Job]:
        return [self.job] if self.job.owner_id == owner_id else []

    def create_job(self, job: Job) -> None:
        self.job = job

    def update_job(self, job: Job) -> None:
        self.job = job

    def create_job_version(self, version: JobVersion) -> None:
        self.job_version = version

    def update_job_version(self, version: JobVersion) -> None:
        self.job_version = version

    def get_job_version(self, job_version_id: str) -> JobVersion | None:
        return self.job_version if job_version_id == self.job_version.job_version_id else None


class _BindingRepository:
    def __init__(self, binding: ResumeJobBinding) -> None:
        self.binding = binding

    def get(self, binding_id: str) -> ResumeJobBinding | None:
        return self.binding if binding_id == self.binding.binding_id else None

    def add(self, binding: ResumeJobBinding) -> None:
        self.binding = binding

    def update(self, binding: ResumeJobBinding) -> None:
        self.binding = binding

    def list_by_owner(self, owner_id: str) -> list[ResumeJobBinding]:
        return [self.binding] if self.binding.owner_id == owner_id else []

    def list_by_job(self, owner_id: str, job_id: str) -> list[ResumeJobBinding]:
        if self.binding.owner_id == owner_id and self.binding.job_id == job_id:
            return [self.binding]
        return []

    def find_active_binding(self, owner_id: str, resume_id: str, job_id: str) -> ResumeJobBinding | None:
        if self.binding.owner_id == owner_id and self.binding.resume_id == resume_id and self.binding.job_id == job_id:
            return self.binding
        return None

    def register_resume(self, owner_id: str, resume_id: str, resume_version_id: str) -> None:
        return None

    def get_resume_current_version(self, owner_id: str, resume_id: str) -> str | None:
        if self.binding.owner_id == owner_id and self.binding.resume_id == resume_id:
            return self.binding.resume_version_id
        return None


def _use_cases(*, ai_orchestration_facade: object | None) -> tuple[PolishUseCases, _PolishRepository]:
    now = utc_now()
    resume_id = "res_pr5_q4"
    resume_version_id = "resver_pr5_q4"
    job_id = "job_pr5_q4"
    job_version_id = "jobver_pr5_q4"
    binding_id = "bind_pr5_q4"
    session = _session(
        now=now,
        resume_id=resume_id,
        resume_version_id=resume_version_id,
        job_id=job_id,
        job_version_id=job_version_id,
        binding_id=binding_id,
    )
    resume = Resume(
        resume_id=resume_id,
        owner_ref=OwnerRef(owner_id=OWNER_ID),
        current_version_ref=VersionRef(resource_type="resume", resource_id=resume_id, version_id=resume_version_id),
        status="active",
        title="Backend Resume",
        file_name="resume.md",
        created_at=now,
        updated_at=now,
    )
    resume_version = ResumeVersion(
        resume_version_id=resume_version_id,
        owner_id=OWNER_ID,
        resume_id=resume_id,
        version_number=1,
        markdown_text="## 项目经历\n我负责支付链路状态流转、幂等和失败补偿。",
        status="current",
        created_at=now,
    )
    job = Job(
        job_id=job_id,
        owner_id=OWNER_ID,
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
    job_version = JobVersion(
        job_version_id=job_version_id,
        owner_id=OWNER_ID,
        job_id=job_id,
        version_number=1,
        responsibilities=["Own backend APIs for interview preparation workflows."],
        requirements=["Python and FastAPI experience."],
        other_notes="PostgreSQL is a plus.",
        status="current",
        created_at=now,
    )
    binding = ResumeJobBinding(
        binding_id=binding_id,
        owner_id=OWNER_ID,
        resume_id=resume_id,
        job_id=job_id,
        resume_version_id=resume_version_id,
        job_version_id=job_version_id,
        status="active",
        record_version=1,
        created_at=now,
        updated_at=now,
    )
    polish_repository = _PolishRepository(session)
    use_cases = PolishUseCases(
        polish_repository=polish_repository,
        binding_repository=_BindingRepository(binding),
        resume_repository=_ResumeRepository(resume, resume_version),
        job_repository=_JobRepository(job, job_version),
        ai_orchestration_facade=ai_orchestration_facade,
    )
    return use_cases, polish_repository


def _session(
    *,
    now: Any | None = None,
    resume_id: str = "res_pr5_q4",
    resume_version_id: str = "resver_pr5_q4",
    job_id: str = "job_pr5_q4",
    job_version_id: str = "jobver_pr5_q4",
    binding_id: str = "bind_pr5_q4",
) -> PolishSession:
    timestamp = now or utc_now()
    return PolishSession(
        session_id=SESSION_ID,
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        binding_id=binding_id,
        resume_id=resume_id,
        resume_version_id=resume_version_id,
        job_id=job_id,
        job_version_id=job_version_id,
        status="running",
        topic_id="topic_technical_depth",
        subtopic_id=None,
        custom_topic_text_summary=None,
        created_at=timestamp,
        updated_at=timestamp,
        polish_theme="mixed",
        progress_tree_status="ready",
        progress_percent=0,
        progress_tree_plan={
            "status": "ready",
            "context_digest": "ctx_q4_graph",
            "nodes": [{"progress_node_ref": NODE_REF, "title": "支付链路一致性", "children": []}],
        },
        progress_tree_state={
            "status": "ready",
            "node_states": [],
            "current_priority": {"progress_node_ref": NODE_REF, "title": "支付链路一致性"},
            "completed_focus_refs": [],
            "updated_from_turns_count": 0,
            "progress": {"progress_percent": 0},
        },
    )


def _command(**overrides: Any) -> CreatePolishQuestionTaskCommand:
    values = {
        "owner_id": OWNER_ID,
        "actor_id": ACTOR_ID,
        "session_id": SESSION_ID,
        "progress_node_ref": NODE_REF,
    }
    values.update(overrides)
    return CreatePolishQuestionTaskCommand(**values)


def _find_forbidden_imports(root: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    paths = [root] if root.is_file() else sorted(root.rglob("*.py"))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module_names: list[str] = []
            if isinstance(node, ast.Import):
                module_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_names.append(node.module)
            for module_name in module_names:
                if module_name.startswith(forbidden_prefixes):
                    violations.append(f"{path.relative_to(REPO_ROOT)}: {module_name}")
    return violations
