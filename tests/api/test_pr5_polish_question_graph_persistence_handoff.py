from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import Barrier, Lock
from typing import Any

import pytest

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    build_polish_question_persistence_plan,
)
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentTaskStatusRef,
    GraphDisabledError,
    RuntimePolicyError,
    RuntimeValidationError,
)
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
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from tools.testing.temp_artifacts import ManagedTempArtifacts


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


def test_concurrent_persistence_is_idempotent_for_same_accepted_candidate() -> None:
    worker_count = 8
    repository = _PolishRepository(_session(), list_questions_barrier=Barrier(worker_count))
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

    def persist() -> Any:
        return handoff.write_question_result(plan, question_repository=repository, now=utc_now())

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        results = tuple(executor.map(lambda _: persist(), range(worker_count)))

    question_ids = {result.question.question_id for result in results}
    question_ref_ids = {result.question_ref.resource_id for result in results}
    metadata = repository.questions[0].question_metadata

    assert len(repository.questions) == 1
    assert question_ids == {repository.questions[0].question_id}
    assert question_ref_ids == {repository.questions[0].question_id}
    assert sum(1 for result in results if result.created) == 1
    assert repository.add_question_calls == 1
    assert repository.add_question_once_calls == worker_count
    assert metadata["graph_persistence_idempotency_key"] == plan.side_effect_key
    assert "raw_prompt" not in metadata
    assert "raw_completion" not in metadata
    assert "provider_payload" not in metadata


def test_sqlalchemy_repository_add_question_once_reuses_existing_graph_question_under_threads() -> None:
    worker_count = 8
    temp_artifacts = ManagedTempArtifacts(test_id="api-pr5-polish-question-idempotency")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        settings = DbSettings(database_url=f"sqlite+pysqlite:///{(workspace / 'questions.sqlite').as_posix()}")
        initialize_schema(settings)
        repository = SqlAlchemyPolishRepository(build_session_factory(settings))
        barrier = Barrier(worker_count)
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

        def add_once(index: int) -> tuple[PolishQuestion, bool]:
            barrier.wait(timeout=5)
            return repository.add_question_once(
                owner_id=OWNER_ID,
                session_id=SESSION_ID,
                graph_persistence_idempotency_key=plan.side_effect_key,
                question=_question_for_plan(f"q_sql_graph_{index}", plan),
            )

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = tuple(executor.map(add_once, range(worker_count)))

        stored_questions = repository.list_questions_for_session(OWNER_ID, SESSION_ID)
        result_question_ids = {question.question_id for question, _ in results}

        assert len(stored_questions) == 1
        assert result_question_ids == {stored_questions[0].question_id}
        assert sum(1 for _, created in results if created) == 1
        assert stored_questions[0].question_metadata["graph_persistence_idempotency_key"] == plan.side_effect_key
        assert "raw_prompt" not in stored_questions[0].question_metadata
        assert "raw_completion" not in stored_questions[0].question_metadata
        assert "provider_payload" not in stored_questions[0].question_metadata
    finally:
        temp_artifacts.cleanup()


def test_graph_enabled_path_persists_question_without_direct_service() -> None:
    facade = _FakeQuestionFacade(status_ref=_GraphStatus(candidate=_accepted_candidate()))
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _DirectQuestionGenerationBlocker()
    use_cases._question_generation_service = blocker

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


def test_graph_enabled_path_persists_formal_candidate_payload_without_direct_service() -> None:
    accepted_payload = AgentCandidatePayload(
        candidate_ref="question_candidate_ref_q4",
        candidate_type="polish_question_candidate",
        payload_schema_id="polish_question_candidate.v1",
        payload=_accepted_candidate(),
        trace_refs=("trace_q4_graph",),
        validation_refs=("validation_ref_q4",),
    )
    facade = _FakeQuestionFacade(
        status_ref=AgentTaskStatusRef(
            ai_task_id="aitask_q4_graph",
            agent_run_id="arun_q4_graph",
            status="succeeded",
            trace_refs=("trace_q4_graph",),
            candidate_refs=("question_candidate_ref_q4",),
            candidate_payloads=(accepted_payload,),
        )
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _DirectQuestionGenerationBlocker()
    use_cases._question_generation_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert len(repository.questions) == 1
    assert repository.questions[0].question_text == _accepted_candidate()["question_text"]
    assert blocker.calls == 0


def test_formal_candidate_payload_rejects_raw_content_before_persistence() -> None:
    with pytest.raises(RuntimePolicyError):
        AgentCandidatePayload(
            candidate_ref="question_candidate_ref_q4",
            candidate_type="polish_question_candidate",
            payload_schema_id="polish_question_candidate.v1",
            payload=_accepted_candidate(raw_prompt="hidden prompt"),
        )


def test_graph_enabled_path_uses_only_accepted_polish_question_candidate_payload() -> None:
    feedback_payload = AgentCandidatePayload(
        candidate_ref="feedback_candidate_ref_q4",
        candidate_type="polish_feedback_candidate",
        payload_schema_id="polish_feedback_candidate.v1",
        payload={"candidate_ref": "feedback_candidate_ref_q4"},
        status="accepted",
    )
    pending_question_payload = AgentCandidatePayload(
        candidate_ref="question_candidate_ref_pending",
        candidate_type="polish_question_candidate",
        payload_schema_id="polish_question_candidate.v1",
        payload=_accepted_candidate(candidate_ref="question_candidate_ref_pending", question_text="不应被持久化"),
        status="candidate",
    )
    accepted_question_payload = AgentCandidatePayload(
        candidate_ref="question_candidate_ref_q4",
        candidate_type="polish_question_candidate",
        payload_schema_id="polish_question_candidate.v1",
        payload=_accepted_candidate(),
        status="passed",
    )
    facade = _FakeQuestionFacade(
        status_ref=AgentTaskStatusRef(
            ai_task_id="aitask_q4_graph",
            agent_run_id="arun_q4_graph",
            status="succeeded",
            trace_refs=("trace_q4_graph",),
            candidate_refs=(
                "feedback_candidate_ref_q4",
                "question_candidate_ref_pending",
                "question_candidate_ref_q4",
            ),
            candidate_payloads=(feedback_payload, pending_question_payload, accepted_question_payload),
        )
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _DirectQuestionGenerationBlocker()
    use_cases._question_generation_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert len(repository.questions) == 1
    assert repository.questions[0].question_text == _accepted_candidate()["question_text"]
    assert blocker.calls == 0


def test_graph_status_does_not_fallback_to_dynamic_candidate_when_formal_payloads_are_present() -> None:
    pending_question_payload = AgentCandidatePayload(
        candidate_ref="question_candidate_ref_pending",
        candidate_type="polish_question_candidate",
        payload_schema_id="polish_question_candidate.v1",
        payload=_accepted_candidate(candidate_ref="question_candidate_ref_pending", question_text="不应被持久化"),
        status="candidate",
    )
    facade = _FakeQuestionFacade(
        status_ref=_GraphStatus(
            candidate=_accepted_candidate(),
            status="succeeded",
            candidate_payloads=(pending_question_payload,),
        )
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _DirectQuestionGenerationBlocker()
    use_cases._question_generation_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.QUEUED
    assert repository.questions == []
    assert blocker.calls == 0


def test_graph_quality_block_does_not_fallback_to_direct_service() -> None:
    facade = _FakeQuestionFacade(
        status_ref=_GraphStatus(candidate=_accepted_candidate(quality_gate={"status": "blocked", "passed": False}))
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _DirectQuestionGenerationBlocker()
    use_cases._question_generation_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert result.value.result_ref.trace_type == "agent_run"
    assert repository.questions == []
    assert blocker.calls == 0


def test_graph_disabled_still_uses_direct_service() -> None:
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


def _question_for_plan(question_id: str, plan: Any) -> PolishQuestion:
    now = utc_now()
    return PolishQuestion(
        question_id=question_id,
        owner_id=plan.owner_id,
        actor_id=plan.actor_id,
        session_id=plan.session_id,
        ai_task_id=plan.ai_task_id,
        question_text=plan.question_text,
        question_sources=(),
        progress_node_ref=plan.progress_node_ref,
        evidence_refs=plan.evidence_refs,
        context_digest=plan.context_digest,
        question_metadata={
            "graph_persistence_idempotency_key": plan.side_effect_key,
            "sanitized": True,
        },
        status="generated",
        created_at=now,
        updated_at=now,
    )


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
    candidate_payloads: tuple[AgentCandidatePayload, ...] = ()


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
        context_snapshot: dict[str, Any] | None = None,
    ) -> _GraphStatus:
        self.calls.append(
            {
                "owner_id": owner_id,
                "actor_id": actor_id,
                "session_ref": session_ref,
                "progress_node_refs": progress_node_refs,
                "completed_focus_refs": completed_focus_refs,
                "idempotency_key": idempotency_key,
                "context_snapshot": context_snapshot,
            }
        )
        if self.error is not None:
            raise self.error
        return self.status_ref


class _DirectQuestionGenerationBlocker:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, **_: Any) -> object:
        self.calls += 1
        raise AssertionError("direct question generation service must not run when graph accepted candidate is persisted")


class _PolishRepository:
    def __init__(self, session: PolishSession, *, list_questions_barrier: Barrier | None = None) -> None:
        self.session = session
        self.questions: list[PolishQuestion] = []
        self.tasks: list[PolishTaskStatus] = []
        self.task_targets: list[str] = []
        self.add_question_calls = 0
        self.add_question_once_calls = 0
        self._list_questions_barrier = list_questions_barrier
        self._lock = Lock()

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
        with self._lock:
            questions = tuple(
                question
                for question in self.questions
                if question.owner_id == owner_id and question.session_id == session_id
            )
        if self._list_questions_barrier is not None:
            self._list_questions_barrier.wait(timeout=5)
        return questions

    def add_question(self, question: PolishQuestion) -> None:
        with self._lock:
            self.add_question_calls += 1
            self.questions.append(question)

    def add_question_once(
        self,
        *,
        owner_id: str,
        session_id: str,
        graph_persistence_idempotency_key: str,
        question: PolishQuestion,
    ) -> tuple[PolishQuestion, bool]:
        with self._lock:
            self.add_question_once_calls += 1
            existing = self._find_question_by_idempotency_key(
                owner_id=owner_id,
                session_id=session_id,
                graph_persistence_idempotency_key=graph_persistence_idempotency_key,
            )
            if existing is not None:
                return existing, False
            self.add_question_calls += 1
            self.questions.append(question)
            return question, True

    def _find_question_by_idempotency_key(
        self,
        *,
        owner_id: str,
        session_id: str,
        graph_persistence_idempotency_key: str,
    ) -> PolishQuestion | None:
        return next(
            (
                question
                for question in self.questions
                if question.owner_id == owner_id
                and question.session_id == session_id
                and question.question_metadata.get("graph_persistence_idempotency_key")
                == graph_persistence_idempotency_key
            ),
            None,
        )

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
