from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from app.application.ai_runtime.business_graphs.polish_question_graph import POLISH_QUESTION_GRAPH_FLAG
from app.application.ai_runtime.contracts import (
    AgentTaskStatusRef,
    GraphDisabledError,
    RuntimeConflictError,
    RuntimePolicyError,
    RuntimeValidationError,
)
from app.application.ai_runtime.facade import AiOrchestrationFacade
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.llm.errors import LlmTransportUnavailableError
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.commands import CreatePolishQuestionTaskCommand
from app.application.polish.entities import PolishAnswer, PolishFeedback, PolishQuestion, PolishSession, PolishTaskStatus
from app.application.polish.question_generation_policy import (
    QuestionGenerationRuntimePolicy,
    QuestionGenerationRuntimePolicyResolver,
)
from app.application.polish.use_cases import PolishUseCases
from app.domain.bindings.entities import ResumeJobBinding
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus, ConfidenceLevel, ValidationStatus
from app.domain.shared.refs import OwnerRef, ResourceRef, VersionRef
from app.infrastructure.ai_runtime.langgraph.fake_runtime import FakeLangGraphRuntime
from app.infrastructure.llm.fake_transport import FakeLlmTransport


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
OWNER_ID = "usr_pr5_q2_owner"
ACTOR_ID = OWNER_ID
SESSION_ID = "ses_pr5_q2"
NODE_REF = "progress_node_payment_consistency"


def test_create_question_task_uses_direct_service_when_facade_absent() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert result.value.result_ref.trace_type == "question"
    assert len(repository.questions) == 1
    assert repository.questions[0].question_id == result.value.result_ref.trace_ref_id


def test_create_question_task_uses_direct_service_when_graph_disabled() -> None:
    facade = _FakeQuestionFacade(error=GraphDisabledError("disabled"))
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert result.value.result_ref.trace_type == "question"
    assert len(facade.calls) == 1
    assert len(repository.questions) == 1
    assert repository.questions[0].question_id == result.value.result_ref.trace_ref_id


def test_create_question_task_starts_graph_when_facade_enabled() -> None:
    facade = _FakeQuestionFacade(
        status_ref=AgentTaskStatusRef(
            ai_task_id="aitask_graph_question",
            agent_run_id="arun_graph_question",
            status="queued",
            trace_refs=("trace_graph_question",),
            candidate_refs=("question_candidate_ref_1",),
        )
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _DirectQuestionGenerationBlocker()
    use_cases._question_generation_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.ai_task_id == "aitask_graph_question"
    assert result.value.task_type == "polish_question_generation"
    assert result.value.status == AiTaskStatus.QUEUED
    assert result.value.result_ref.trace_type == "agent_run"
    assert result.value.result_ref.trace_ref_id == "arun_graph_question"
    assert result.value.user_visible_status == "题目生成任务已启动"
    assert {ref.resource_type for ref in result.value.candidate_refs} >= {"agent_run", "trace", "question_candidate"}
    assert all(ref.resource_type != "question" for ref in result.value.candidate_refs)
    assert repository.questions == []
    assert repository.tasks == [result.value]
    assert repository.task_targets == [SESSION_ID]
    assert blocker.calls == 0
    call = facade.calls[0]
    context_snapshot = call["context_snapshot"]
    assert context_snapshot["context_source"] == "use_case_repository_snapshot"
    assert context_snapshot["session"]["session_id"] == SESSION_ID
    assert context_snapshot["session"]["resume_version_id"] == "resver_pr5_q2"
    assert context_snapshot["session"]["job_version_id"] == "jobver_pr5_q2"
    assert context_snapshot["requested_progress_node_ref"] == NODE_REF
    assert context_snapshot["progress_context"]["resume_snapshot"]["resume_version_id"] == "resver_pr5_q2"
    assert context_snapshot["progress_context"]["job_snapshot"]["job_version_id"] == "jobver_pr5_q2"
    assert context_snapshot["progress_tree_plan"]["nodes"][0]["progress_node_ref"] == NODE_REF


def test_create_question_task_persists_fake_runtime_agent_candidate_payload() -> None:
    flags = _enabled_question_graph_flags()
    runtime = FakeLangGraphRuntime(flag_resolver=flags)
    facade = AiOrchestrationFacade(
        runner=runtime,
        registry=AgentGraphRegistry.default(),
        flag_resolver=flags,
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _DirectQuestionGenerationBlocker()
    use_cases._question_generation_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert result.value.result_ref.trace_type == "question"
    assert len(repository.questions) == 1
    assert repository.questions[0].question_id == result.value.result_ref.trace_ref_id
    assert repository.questions[0].ai_task_id == result.value.ai_task_id
    assert repository.questions[0].question_metadata["llm_generation_mode"] == "deterministic_agent_fallback"
    assert repository.questions[0].question_metadata["fallback_reason"] == "provider_disabled_deterministic_drafting_tool"
    assert repository.questions[0].question_metadata["phase_results"]
    assert repository.questions[0].question_metadata["tool_results"]
    assert blocker.calls == 0

    agent_run_ref = next(ref for ref in result.value.candidate_refs if ref.resource_type == "agent_run")
    status = runtime.get_status(agent_run_ref.resource_id, OWNER_ID)
    assert status.status == "agent_orchestration_succeeded"
    assert status.metadata["accepted_candidate_payload"] is True
    assert any(ref.startswith("question_candidate_ref_") for ref in status.output_refs)


def test_create_question_task_provider_enabled_graph_uses_transport_and_repository_context() -> None:
    flags = _enabled_question_graph_flags(provider_enabled=True)
    transport = _RecordingQuestionProviderTransport()
    runtime = FakeLangGraphRuntime(flag_resolver=flags, polish_question_llm_transport=transport)
    facade = AiOrchestrationFacade(
        runner=runtime,
        registry=AgentGraphRegistry.default(),
        flag_resolver=flags,
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    blocker = _DirectQuestionGenerationBlocker()
    use_cases._question_generation_service = blocker

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert len(repository.questions) == 1
    assert blocker.calls == 0
    assert len(transport.requests) == 1
    request = transport.requests[0]
    input_data = request.evidence_bundle["input_data"]
    assert request.graph_name == "polish_question_graph"
    assert request.node_name == "question_drafting"
    assert input_data["progress_node"]["ref"] == NODE_REF
    assert input_data["evidence_refs"]
    assert input_data["source_context"]["context_source"] == "use_case_repository_snapshot"
    assert input_data["source_context"]["session_ref"] == SESSION_ID
    assert input_data["source_context"]["resume_version_id"] == "resver_pr5_q2"
    assert input_data["source_context"]["job_version_id"] == "jobver_pr5_q2"

    metadata = repository.questions[0].question_metadata
    assert metadata["llm_generation_mode"] == "agent_provider_path"
    assert metadata["provider_status"] == "enabled"
    assert metadata["fallback_reason"] is None
    assert metadata["context_source"] == "use_case_repository_snapshot"
    assert metadata["provider_calls"] == 1
    assert "deterministic" not in metadata["llm_generation_mode"]


def test_create_question_task_provider_failure_does_not_create_success_question() -> None:
    flags = _enabled_question_graph_flags(provider_enabled=True)
    runtime = FakeLangGraphRuntime(
        flag_resolver=flags,
        polish_question_llm_transport=_FailingQuestionProviderTransport(),
    )
    facade = AiOrchestrationFacade(
        runner=runtime,
        registry=AgentGraphRegistry.default(),
        flag_resolver=flags,
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    use_cases._question_generation_service = _DirectQuestionGenerationBlocker()

    result = use_cases.create_question_task(_command())

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "validation_failed"
    assert repository.questions == []
    assert repository.tasks == []


def test_create_question_task_provider_enabled_rejects_fake_transport_as_provider() -> None:
    flags = _enabled_question_graph_flags(provider_enabled=True)
    runtime = FakeLangGraphRuntime(
        flag_resolver=flags,
        polish_question_llm_transport=FakeLlmTransport(),
    )
    facade = AiOrchestrationFacade(
        runner=runtime,
        registry=AgentGraphRegistry.default(),
        flag_resolver=flags,
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)
    use_cases._question_generation_service = _DirectQuestionGenerationBlocker()

    result = use_cases.create_question_task(_command())

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "validation_failed"
    assert repository.questions == []
    assert repository.tasks == []


def test_create_question_task_does_not_fallback_on_runtime_conflict() -> None:
    facade = _FakeQuestionFacade(error=RuntimeConflictError("idempotency key reused with different request"))
    use_cases, repository = _use_cases(ai_orchestration_facade=facade)

    result = use_cases.create_question_task(_command())

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "validation_failed"
    assert result.error.details["reason"] == "idempotency_conflict"
    assert repository.questions == []
    assert repository.tasks == []


def test_create_question_task_does_not_fallback_on_runtime_validation_or_policy_error() -> None:
    cases = (
        (RuntimeValidationError("invalid graph request"), "runtime_validation_failed"),
        (RuntimePolicyError("blocked by runtime policy"), "runtime_policy_blocked"),
    )

    for error, reason in cases:
        facade = _FakeQuestionFacade(error=error)
        use_cases, repository = _use_cases(ai_orchestration_facade=facade)

        result = use_cases.create_question_task(_command())

        assert not result.is_success
        assert result.error is not None
        assert result.error.code == "validation_failed"
        assert result.error.details["reason"] == reason
        assert repository.questions == []
        assert repository.tasks == []


def test_create_question_task_passes_progress_node_and_completed_focus_refs() -> None:
    facade = _FakeQuestionFacade(
        status_ref=AgentTaskStatusRef(
            ai_task_id="aitask_graph_refs",
            agent_run_id="arun_graph_refs",
            status="running",
            trace_refs=("trace_graph_refs",),
            candidate_refs=("candidate_graph_refs",),
        )
    )
    state = _progress_state(
        completed_focus_refs=[
            {"progress_node_ref": NODE_REF, "focus_key": "state_focus"},
            {"progress_node_ref": "other_node", "focus_key": "must_not_pass"},
        ]
    )
    use_cases, _repository = _use_cases(ai_orchestration_facade=facade, progress_tree_state=state)
    command = _command(completed_focus_refs=("manual_focus",))

    first = use_cases.create_question_task(command)
    second = use_cases.create_question_task(command)

    assert first.is_success
    assert second.is_success
    assert len(facade.calls) == 2
    assert facade.calls[0]["progress_node_refs"] == (NODE_REF,)
    assert facade.calls[0]["completed_focus_refs"] == ("manual_focus", "state_focus")
    assert facade.calls[0]["idempotency_key"] == facade.calls[1]["idempotency_key"]


def test_no_langgraph_import_in_application_polish_path() -> None:
    violations = _find_forbidden_imports(
        APP_ROOT / "application" / "polish",
        forbidden_prefixes=("langgraph", "langchain"),
    )

    assert violations == []


class _FakeQuestionFacade:
    def __init__(self, *, status_ref: AgentTaskStatusRef | None = None, error: Exception | None = None) -> None:
        self.status_ref = status_ref or AgentTaskStatusRef(
            ai_task_id="aitask_graph_default",
            agent_run_id="arun_graph_default",
            status="queued",
        )
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
    ) -> AgentTaskStatusRef:
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


class _RecordingQuestionProviderTransport:
    def __init__(self) -> None:
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        input_data = request.evidence_bundle["input_data"]
        policy = input_data["generation_policy"]
        evidence_refs = tuple(input_data["evidence_refs"])
        primary = input_data["evidence_summaries"][0]
        question_text = (
            f"围绕「{input_data['progress_node']['title']}」，请基于主要证据「{primary['excerpt']}」展开："
            "说明 FastAPI 后端工作流的一致性边界、失败补偿、验证指标和复盘信号。"
        )
        return LlmTransportResult(
            result={
                "transport": "recording_provider",
                "question_text": question_text,
                "question_kind": policy["question_kind"],
                "focus_dimension": policy["question_kind"],
                "difficulty": "hard",
                "skill_dimension": input_data["progress_node"]["expected_capability"],
                "expected_signal": "回答应围绕 FastAPI 后端工作流说明边界、取舍、失败处理和验证指标。",
                "follow_ups": ["失败补偿如何验证？", "一致性边界如何证明？"],
                "scoring_rubric": [
                    {"dimension": "grounding", "signals": ["引用证据", "不编造经历"]},
                    {"dimension": "reasoning", "signals": ["说明边界", "说明验证指标"]},
                ],
                "missing_context": [],
                "evidence_refs": list(evidence_refs),
                "confidence": "high",
                "clarification_needed": False,
                "trace_ref": "trace_recording_provider_question",
            },
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.HIGH,
            low_confidence_flags=(),
            trace_refs=("trace_recording_provider_question",),
            evidence_refs=evidence_refs,
        )


class _FailingQuestionProviderTransport:
    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        raise LlmTransportUnavailableError("provider unavailable")


class _DirectQuestionGenerationBlocker:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, **_: Any) -> object:
        self.calls += 1
        raise AssertionError("direct question generation service must not run when graph path starts")


class _PolishRepository:
    def __init__(self, session: PolishSession) -> None:
        self.session = session
        self.questions: list[PolishQuestion] = []
        self.tasks: list[PolishTaskStatus] = []
        self.task_targets: list[str] = []

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
        self.questions.append(question)

    def get_question(self, owner_id: str, question_id: str) -> PolishQuestion | None:
        return next(
            (question for question in self.questions if question.owner_id == owner_id and question.question_id == question_id),
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


def _use_cases(
    *,
    ai_orchestration_facade: object | None,
    progress_tree_state: dict[str, Any] | None = None,
    question_generation_policy: QuestionGenerationRuntimePolicy | None = None,
    question_generation_policy_resolver: QuestionGenerationRuntimePolicyResolver | None = None,
) -> tuple[PolishUseCases, _PolishRepository]:
    now = utc_now()
    resume_id = "res_pr5_q2"
    resume_version_id = "resver_pr5_q2"
    job_id = "job_pr5_q2"
    job_version_id = "jobver_pr5_q2"
    binding_id = "bind_pr5_q2"
    session = PolishSession(
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
        created_at=now,
        updated_at=now,
        polish_theme="mixed",
        progress_tree_status="ready",
        progress_percent=0,
        progress_tree_plan=_progress_plan(),
        progress_tree_state=progress_tree_state or _progress_state(),
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
        markdown_text="## 项目经历\nBuilt backend workflow automation with FastAPI and PostgreSQL.",
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
        question_generation_policy=question_generation_policy,
        question_generation_policy_resolver=question_generation_policy_resolver,
    )
    return use_cases, polish_repository


def _enabled_question_graph_flags(*, provider_enabled: bool = False) -> RuntimeFlagResolver:
    return RuntimeFlagResolver(
        test_overrides={
            "AIFI_AI_RUNTIME_ENABLED": True,
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
            POLISH_QUESTION_GRAPH_FLAG: True,
            "AIFI_REAL_PROVIDER_ENABLED": provider_enabled,
        }
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


def _progress_plan() -> dict[str, Any]:
    return {
        "status": "ready",
        "context_digest": "ctx_pr5_q2",
        "nodes": [
            {
                "progress_node_ref": NODE_REF,
                "title": "支付链路一致性",
                "expected_capability": "能说明支付链路的状态流转、幂等、失败补偿和上线验证。",
                "related_job_requirements": ["Python and FastAPI experience."],
                "related_resume_evidence": ["Built backend workflow automation with FastAPI and PostgreSQL."],
                "missing_points": ["需要补足幂等和失败补偿。"],
                "children": [],
            }
        ],
    }


def _progress_state(completed_focus_refs: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {
        "status": "ready",
        "node_states": [],
        "current_priority": {
            "progress_node_ref": NODE_REF,
            "title": "支付链路一致性",
            "expected_capability": "能说明支付链路的状态流转、幂等、失败补偿和上线验证。",
        },
        "completed_focus_refs": completed_focus_refs or [],
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
    }


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
                    rel = path.relative_to(REPO_ROOT)
                    violations.append(f"{rel}: {module_name}")
    return violations
