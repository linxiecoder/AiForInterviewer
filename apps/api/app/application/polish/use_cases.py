"""Polish use cases."""

from __future__ import annotations

import json
import threading
from dataclasses import replace
from hashlib import sha256
from typing import Any

from app.application.common.result import ApplicationResult
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentTaskStatusRef,
    GraphDisabledError,
    RuntimeConflictError,
    RuntimePolicyError,
    RuntimeValidationError,
)
from app.application.ai_runtime.facade import AiOrchestrationFacade
from app.application.ai_runtime.handoff import AgentPersistenceHandoff, build_question_result_write_plan
from app.application.job_match.entities import JobMatchAnalysis
from app.application.job_match.ports import JobMatchRepository
from app.application.polish.commands import (
    CompletePolishQuestionCommand,
    CreatePolishAnswerCommand,
    CreatePolishFeedbackTaskCommand,
    CreatePolishQuestionTaskCommand,
    CreatePolishSessionCommand,
    EndPolishSessionCommand,
    RefreshPolishProgressTreeStateCommand,
)
from app.application.polish.candidate_llm import PolishCandidateLlmService
from app.application.polish.candidates import CandidateExtractionInput, extract_feedback_candidates
from app.application.polish.entities import (
    PolishAnswer,
    PolishFeedback,
    PolishQuestion,
    PolishQuestionDraft,
    PolishQuestionSource,
    PolishSessionAnswerDetail,
    PolishSessionDetail,
    PolishSessionTurn,
    PolishSession,
    PolishSubtopic,
    PolishTaskStatus,
    PolishTopic,
)
from app.application.polish.feedback_contracts import (
    FEEDBACK_SCHEMA_ID,
    FEEDBACK_SCHEMA_VERSION,
    FeedbackInput,
    RetryFeedbackInput,
)
from app.application.polish.feedback_quality import (
    compute_score_result_from_dimensions,
    validate_feedback_consistency,
)
from app.application.polish.feedback_llm import PolishFeedbackLlmService
from app.application.polish.ports import PolishCandidateRepository, PolishRepository
from app.application.polish.question_metadata import empty_question_metadata, normalize_question_metadata
from app.application.polish.question_llm import PolishQuestionLlmService
from app.application.polish.theme_strategy import PolishThemeStrategy, resolve_polish_theme_strategy
from app.application.polish.progress_context import build_polish_progress_context
from app.application.polish.progress_prompts import (
    INITIAL_PROGRESS_TREE_PROMPT_CONTRACT,
    PROGRESS_TREE_STATE_REFRESH_PROMPT_CONTRACT,
)
from app.application.polish.progress_tree import (
    PROGRESS_TREE_STATUS_FAILED,
    PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
    PROGRESS_TREE_STATUS_READY,
    PROGRESS_TREE_STATUS_REFRESH_FAILED,
    PolishProgressTreeLlmService,
    build_deterministic_progress_node_question,
)
from app.application.polish.queries import GetPolishSessionQuery, ListPolishSessionsQuery, ListPolishTopicsQuery
from app.application.resumes.ports import ResumeRepository
from app.domain.bindings.ports import BindingRepository
from app.domain.jobs.entities import Job, JobVersion
from app.domain.jobs.ports import JobRepository
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus, ScoreType
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.domain.shared.refs import ResourceRef, TraceRef
from app.application.llm.ports import LlmTransport


SESSION_STATUS_RUNNING = "running"
SESSION_STATUS_ENDED = "ended"
QUESTION_STATUS_GENERATED = "generated"
ANSWER_STATUS_SAVED = "saved"
FEEDBACK_STATUS_GENERATED = "generated"
QUESTION_GENERATION_MODE_NEW = "new_question"
QUESTION_GENERATION_MODE_FOLLOW_UP = "follow_up"
QUESTION_GENERATION_MODES = {QUESTION_GENERATION_MODE_NEW, QUESTION_GENERATION_MODE_FOLLOW_UP}

QUESTION_CONTRACT_IDS = ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")
_POLISH_QUESTION_CANDIDATE_STATUSES = frozenset({"accepted", "passed"})
_POLISH_QUESTION_CANDIDATE_TYPES = frozenset(
    {"polish_question", "question_candidate", "polish_question_candidate"}
)
_POLISH_QUESTION_CANDIDATE_PAYLOAD_SCHEMA_IDS = frozenset(
    {
        "polish_question_candidate.v1",
        "polish_question_candidate_v1",
        "polish_question_generation_output_v1",
    }
)
FEEDBACK_CONTRACT_IDS = (
    "P-POLISH-003",
    "P-POLISH-004",
    "P-POLISH-005",
    "P-POLISH-009",
)
FEEDBACK_NEXT_RECOMMENDED_ACTIONS = (
    "answer_again",
    "continue_same_question",
    "generate_reference_answer",
    "explain_knowledge_point",
    "expand_technical_principle",
    "generate_next_round_suggestion",
    "generate_next_question",
)
ANSWER_TEXT_MIN_LENGTH = 2
ANSWER_TEXT_MAX_LENGTH = 8000
ANSWER_IDEMPOTENCY_KEY_MAX_LENGTH = 128
UNNAMED_JOB_TITLE = "未命名岗位"
UNNAMED_RESUME_TITLE = "未命名简历"
UNNAMED_COMPANY_TITLE = "未命名公司"
UNNAMED_QUESTION_TEXT = "题干缺失"
UNNAMED_ANSWER_TEXT = "暂无回答"
UNNAMED_FEEDBACK_TEXT = "本轮反馈尚未生成"
_ANSWER_SUBMISSION_LOCKS_GUARD = threading.Lock()
_ANSWER_SUBMISSION_LOCKS: dict[tuple[str, str, str], threading.Lock] = {}
_ANSWER_IDEMPOTENCY_CACHE_GUARD = threading.Lock()
_ANSWER_IDEMPOTENCY_CACHE: dict[tuple[str, str, str, str], tuple[str, str]] = {}
PREVIOUS_FEEDBACK_SUMMARY_LIMIT = 5
PREVIOUS_FEEDBACK_LOSS_POINT_LIMIT = 12
PREVIOUS_FEEDBACK_DIMENSION_LIMIT = 12
PREVIOUS_FEEDBACK_TEXT_LIMIT = 600

POLISH_TOPICS: tuple[PolishTopic, ...] = (
    PolishTopic(
        topic_id="topic_authenticity_contribution",
        title="经历真实性与贡献拷问",
        description="围绕简历经历真实性、个人贡献边界、关键证据和追问抗压能力进行模拟面试。",
        requires_job_binding=True,
    ),
    PolishTopic(
        topic_id="topic_technical_depth",
        title="能力深度与技术碾压",
        description="围绕核心技术栈、架构设计、性能瓶颈和底层原理进行深度追问。",
        requires_job_binding=True,
    ),
    PolishTopic(
        topic_id="topic_scenario_roleplay",
        title="情景模拟与角色扮演",
        description="围绕真实业务场景、团队协作、跨角色沟通和临场决策进行角色化模拟。",
        requires_job_binding=True,
    ),
    PolishTopic(
        topic_id="topic_risk_defense",
        title="风险点排查与防御性打磨",
        description="围绕简历和岗位匹配中的风险点、薄弱项、反问陷阱和防御性表达进行打磨。",
        requires_job_binding=True,
    ),
)


class PolishUseCases:
    def __init__(
        self,
        *,
        polish_repository: PolishRepository,
        binding_repository: BindingRepository,
        resume_repository: ResumeRepository,
        job_repository: JobRepository,
        job_match_repository: JobMatchRepository | None = None,
        candidate_repository: PolishCandidateRepository | None = None,
        progress_tree_service: PolishProgressTreeLlmService | None = None,
        llm_transport: LlmTransport | None = None,
        ai_orchestration_facade: AiOrchestrationFacade | None = None,
    ) -> None:
        self._polish_repository = polish_repository
        self._binding_repository = binding_repository
        self._resume_repository = resume_repository
        self._job_repository = job_repository
        self._job_match_repository = job_match_repository
        self._candidate_repository = candidate_repository
        self._progress_tree_service = progress_tree_service or PolishProgressTreeLlmService(None)
        self._question_llm_service = PolishQuestionLlmService(llm_transport)
        self._feedback_llm_service = PolishFeedbackLlmService(llm_transport)
        self._candidate_llm_service = PolishCandidateLlmService(llm_transport)
        self._ai_orchestration_facade = ai_orchestration_facade

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="polish_skeleton")

    def list_topics(self, query: ListPolishTopicsQuery) -> ApplicationResult[tuple[PolishTopic, ...]]:
        if query.resume_job_binding_id:
            binding = self._binding_repository.get(query.resume_job_binding_id)
            if binding is None or binding.owner_id != query.owner_id:
                return ApplicationResult(
                    error=DomainError(code="not_found_or_inaccessible", message="Binding not found")
                )
        return ApplicationResult(value=POLISH_TOPICS)

    def list_sessions(self, query: ListPolishSessionsQuery) -> ApplicationResult[tuple[PolishSessionDetail, ...]]:
        sessions = self._polish_repository.list_sessions(query.owner_id)
        return ApplicationResult(
            value=tuple(
                self._build_session_detail(owner_id=query.owner_id, session=session, include_turns=False)
                for session in sessions
            )
        )

    def create_session(self, command: CreatePolishSessionCommand) -> ApplicationResult[PolishSession]:
        binding = self._binding_repository.get(command.resume_job_binding_id)
        if binding is None or binding.owner_id != command.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Binding not found")
            )
        if binding.status != "active":
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Binding must be active")
            )

        topic_error = _validate_topic_selection(command.topic_id, command.subtopic_id)
        if topic_error is not None:
            return ApplicationResult(error=topic_error)
        try:
            theme_strategy = resolve_polish_theme_strategy(command.polish_theme)
        except ValueError:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Invalid polish theme",
                    details={"field": "polish_theme"},
                )
            )

        resume_version = self._resume_repository.get_version(binding.resume_version_id)
        if (
            resume_version is None
            or resume_version.owner_id != command.owner_id
            or resume_version.resume_id != binding.resume_id
        ):
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Resume version not found")
            )

        job_version = self._job_repository.get_job_version(binding.job_version_id)
        if (
            job_version is None
            or job_version.owner_id != command.owner_id
            or job_version.job_id != binding.job_id
        ):
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job version not found")
            )

        now = utc_now()
        session = PolishSession(
            session_id=generate_resource_id(ResourceIdPrefix.SESSION),
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            binding_id=binding.binding_id,
            resume_id=binding.resume_id,
            resume_version_id=binding.resume_version_id,
            job_id=binding.job_id,
            job_version_id=binding.job_version_id,
            status=SESSION_STATUS_RUNNING,
            topic_id=command.topic_id,
            subtopic_id=command.subtopic_id,
            custom_topic_text_summary=_custom_topic_summary(command.custom_topic_text),
            created_at=now,
            updated_at=now,
            polish_theme=theme_strategy.theme,
        )
        job = self._resolve_job(owner_id=command.owner_id, job_id=binding.job_id)
        resume = self._resolve_resume(owner_id=command.owner_id, resume_id=binding.resume_id)
        job_title, job_company = self._job_labels_from_job(job)
        resume_title = self._resume_title_from_resume(resume)
        progress_context = build_polish_progress_context(
            PolishSessionDetail(
                session=session,
                job_title=job_title,
                job_company=job_company,
                resume_title=resume_title,
                binding_label=self._build_binding_label(job_title=job_title, resume_title=resume_title),
                turns=(),
            ),
            job=job,
            job_version=job_version,
            resume=resume,
            resume_version=resume_version,
            match_analysis=self._resolve_match_analysis(owner_id=command.owner_id, session=session),
            weaknesses=None,
            assets=None,
        )
        progress_artifacts = _progress_artifacts_with_theme(
            self._progress_tree_service.generate_initial(progress_context),
            theme_strategy,
        )
        session = replace(
            session,
            progress_tree_status=progress_artifacts["status"],
            progress_percent=progress_artifacts["progress_percent"],
            progress_tree_plan=progress_artifacts["progress_tree_plan"],
            progress_tree_state=progress_artifacts["progress_tree_state"],
        )
        self._polish_repository.add_session(session)
        return ApplicationResult(value=session)

    def get_session(self, query: GetPolishSessionQuery) -> ApplicationResult[PolishSessionDetail]:
        session = self._polish_repository.get_session(query.owner_id, query.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        detail = self._build_session_detail(owner_id=query.owner_id, session=session)
        return ApplicationResult(value=detail)

    def create_question_task(self, command: CreatePolishQuestionTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        if session.status != SESSION_STATUS_RUNNING:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Polish session is not running",
                    details={"field": "session_status", "session_status": session.status},
                )
            )
        request_error = _validate_question_generation_request(command)
        if request_error is not None:
            return ApplicationResult(error=request_error)
        detail = self._build_session_detail(owner_id=command.owner_id, session=session)
        if detail.progress_tree_status == PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Progress tree context is insufficient",
                    details={"progress_tree_status": detail.progress_tree_status},
                )
            )
        if detail.progress_tree_status not in {PROGRESS_TREE_STATUS_READY, PROGRESS_TREE_STATUS_REFRESH_FAILED}:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Progress tree is not ready",
                    details={"progress_tree_status": detail.progress_tree_status},
                )
            )
        if not _has_valid_progress_tree_plan(detail.progress_tree_plan):
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Progress tree plan is not ready",
                    details={"progress_tree_status": detail.progress_tree_status},
                )
            )

        now = utc_now()
        requested_progress_node_ref = _question_generation_requested_ref(command)
        completed_focus_refs = _combined_completed_focus_refs(
            command.completed_focus_refs,
            detail.progress_tree_state,
            progress_node_ref=requested_progress_node_ref,
        )
        if self._ai_orchestration_facade is not None:
            stable_idempotency_key = _stable_polish_question_generation_idempotency_key(
                owner_id=command.owner_id,
                session_id=command.session_id,
                requested_progress_node_ref=requested_progress_node_ref,
                completed_focus_refs=completed_focus_refs,
            )
            try:
                graph_status = self._ai_orchestration_facade.start_polish_question_generation(
                    owner_id=command.owner_id,
                    actor_id=command.actor_id,
                    session_ref=command.session_id,
                    progress_node_refs=(requested_progress_node_ref,) if requested_progress_node_ref else (),
                    completed_focus_refs=completed_focus_refs,
                    idempotency_key=stable_idempotency_key,
                )
            except GraphDisabledError:
                graph_status = None
            except RuntimeValidationError:
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="Polish question graph request is invalid",
                        details={"reason": "runtime_validation_failed"},
                    )
                )
            except RuntimeConflictError:
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="Polish question graph request conflicts",
                        details={"reason": "idempotency_conflict"},
                    )
                )
            except RuntimePolicyError:
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="Polish question graph request blocked",
                        details={"reason": "runtime_policy_blocked"},
                    )
                )
            except Exception:
                return ApplicationResult(
                    error=DomainError(code="generation_failed", message="Polish question graph failed")
                )
            if graph_status is not None:
                candidate_payload = _graph_status_candidate_payload(graph_status)
                if candidate_payload is not None:
                    try:
                        plan = build_question_result_write_plan(
                            owner_id=command.owner_id,
                            actor_id=command.actor_id,
                            session_id=command.session_id,
                            ai_task_id=graph_status.ai_task_id,
                            agent_run_id=graph_status.agent_run_id,
                            candidate=candidate_payload,
                            progress_node_ref=requested_progress_node_ref,
                            trace_refs=graph_status.trace_refs,
                            contract_ids=QUESTION_CONTRACT_IDS,
                        )
                        write_result = AgentPersistenceHandoff().write_question_result(
                            plan,
                            question_repository=self._polish_repository,
                            now=now,
                        )
                    except RuntimeValidationError:
                        task = _polish_question_graph_validation_failed_task_status(
                            graph_status,
                            requested_progress_node_ref=requested_progress_node_ref,
                            created_at=now,
                        )
                        self._polish_repository.add_task(
                            task,
                            owner_id=command.owner_id,
                            actor_id=command.actor_id,
                            target_ref_id=command.session_id,
                        )
                        return ApplicationResult(value=task)
                    except RuntimePolicyError:
                        return ApplicationResult(
                            error=DomainError(
                                code="validation_failed",
                                message="Polish question graph persistence blocked",
                                details={"reason": "runtime_policy_blocked"},
                            )
                        )
                    except Exception:
                        return ApplicationResult(
                            error=DomainError(
                                code="generation_failed",
                                message="Polish question graph persistence failed",
                            )
                        )
                    if write_result is not None:
                        task = write_result.task_status
                        self._polish_repository.add_task(
                            task,
                            owner_id=command.owner_id,
                            actor_id=command.actor_id,
                            target_ref_id=command.session_id,
                        )
                        return ApplicationResult(value=task)

                task = _polish_question_graph_task_status(
                    graph_status,
                    requested_progress_node_ref=requested_progress_node_ref,
                    created_at=now,
                )
                self._polish_repository.add_task(
                    task,
                    owner_id=command.owner_id,
                    actor_id=command.actor_id,
                    target_ref_id=command.session_id,
                )
                return ApplicationResult(value=task)

        task_id = generate_resource_id(ResourceIdPrefix.TASK)
        question_id = generate_resource_id(ResourceIdPrefix.QUESTION)
        progress_context = _progress_context_with_completed_focus_refs(
            detail.progress_context,
            completed_focus_refs,
        )
        if _question_generation_mode(command) == QUESTION_GENERATION_MODE_FOLLOW_UP:
            follow_up_result = _build_follow_up_question_draft(command=command, detail=detail)
            if isinstance(follow_up_result, DomainError):
                return ApplicationResult(error=follow_up_result)
            question_draft = follow_up_result
        else:
            question_result = self._question_llm_service.generate_with_llm_or_fallback(
                session=session,
                context=progress_context,
                plan=detail.progress_tree_plan,
                state=detail.progress_tree_state,
                requested_ref=requested_progress_node_ref,
                deterministic_builder=lambda: build_deterministic_progress_node_question(
                    session=session,
                    context=progress_context,
                    plan=detail.progress_tree_plan,
                    state=detail.progress_tree_state,
                    requested_ref=requested_progress_node_ref,
                ),
            )
            question_draft = question_result.draft
        question_metadata = _metadata_for_new_question(
            getattr(question_draft, "question_metadata", None),
            generated_at=now.isoformat(),
        )
        question_metadata.update(
            _question_generation_request_metadata(
                command,
                requested_progress_node_ref=requested_progress_node_ref,
                resolved_progress_node_ref=question_draft.progress_node_ref,
            )
        )
        question_metadata["completed_focus_refs"] = list(completed_focus_refs)
        question = PolishQuestion(
            question_id=question_id,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            session_id=command.session_id,
            ai_task_id=task_id,
            question_text=question_draft.question_text,
            question_sources=question_draft.question_sources,
            progress_node_ref=question_draft.progress_node_ref,
            evidence_refs=question_draft.evidence_refs,
            context_digest=question_draft.context_digest,
            question_metadata=question_metadata,
            status=QUESTION_STATUS_GENERATED,
            created_at=now,
            updated_at=now,
        )
        task = PolishTaskStatus(
            ai_task_id=task_id,
            task_type="polish_question_generation",
            status=AiTaskStatus.SUCCEEDED,
            contract_ids=QUESTION_CONTRACT_IDS,
            retryable=False,
            result_ref=TraceRef(trace_ref_id=question_id, trace_type="question", created_at=now),
            user_visible_status="题目已生成",
            candidate_refs=(
                (ResourceRef(resource_type="question", resource_id=question_id),)
                + ((ResourceRef(resource_type="progress_node", resource_id=question_draft.progress_node_ref),) if question_draft.progress_node_ref is not None else ())
                + tuple(
                    ResourceRef(resource_type="evidence", resource_id=evidence_ref)
                    for evidence_ref in question_draft.evidence_refs
                )
            ),
        )
        self._polish_repository.add_question(question)
        self._polish_repository.add_task(
            task,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            target_ref_id=command.session_id,
        )
        return ApplicationResult(value=task)

    def complete_question(self, command: CompletePolishQuestionCommand) -> ApplicationResult[PolishSessionDetail]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        if session.status != SESSION_STATUS_RUNNING:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Polish session is not running",
                    details={"field": "session_status", "session_status": session.status},
                )
            )
        question = self._polish_repository.get_question(command.owner_id, command.question_id)
        if question is None or question.session_id != command.session_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Question not found")
            )
        now = utc_now()
        progress_tree_state = _progress_tree_state_with_completed_question(
            session.progress_tree_state,
            progress_tree_plan=session.progress_tree_plan,
            question=question,
            completed_at=now,
        )
        updated_session = replace(session, progress_tree_state=progress_tree_state, updated_at=now)
        self._polish_repository.update_progress_tree(updated_session)
        return ApplicationResult(value=self._build_session_detail(owner_id=command.owner_id, session=updated_session))

    def end_session(self, command: EndPolishSessionCommand) -> ApplicationResult[PolishSessionDetail]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        if session.status == SESSION_STATUS_ENDED:
            return ApplicationResult(value=self._build_session_detail(owner_id=command.owner_id, session=session))
        now = utc_now()
        updated_state = _progress_tree_state_with_session_ended(session.progress_tree_state, ended_at=now)
        updated_session = replace(
            session,
            status=SESSION_STATUS_ENDED,
            progress_tree_state=updated_state,
            updated_at=now,
        )
        self._polish_repository.update_progress_tree(updated_session)
        return ApplicationResult(value=self._build_session_detail(owner_id=command.owner_id, session=updated_session))

    def create_answer(self, command: CreatePolishAnswerCommand) -> ApplicationResult[PolishAnswer]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        if session.status != SESSION_STATUS_RUNNING:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Polish session is not running",
                    details={"field": "session_status", "session_status": session.status},
                )
            )
        question = self._polish_repository.get_question(command.owner_id, command.question_id)
        if question is None or question.session_id != command.session_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Question not found")
            )
        answer_text = command.answer_text.strip()
        text_error = _validate_answer_text(answer_text)
        if text_error is not None:
            return ApplicationResult(error=text_error)
        raw_idempotency_key = getattr(command, "idempotency_key", None)
        idempotency_key_error = _validate_answer_idempotency_key(raw_idempotency_key)
        if idempotency_key_error is not None:
            return ApplicationResult(error=idempotency_key_error)
        idempotency_key = _normalize_answer_idempotency_key(raw_idempotency_key)

        answer_lock = _answer_submission_lock(
            owner_id=command.owner_id,
            session_id=command.session_id,
            question_id=command.question_id,
        )
        with answer_lock:
            if idempotency_key is not None:
                cached = _cached_answer_idempotency_record(
                    owner_id=command.owner_id,
                    session_id=command.session_id,
                    question_id=command.question_id,
                    idempotency_key=idempotency_key,
                )
                if cached is not None:
                    cached_answer_id, cached_answer_text = cached
                    if cached_answer_text != answer_text:
                        return ApplicationResult(
                            error=DomainError(
                                code="validation_failed",
                                message="Idempotency key conflicts with a different answer payload",
                                details={
                                    "field": "idempotency_key",
                                    "reason": "idempotency_conflict",
                                },
                            )
                        )
                    existing_answer = self._polish_repository.get_answer(command.owner_id, cached_answer_id)
                    if (
                        existing_answer is not None
                        and existing_answer.session_id == command.session_id
                        and existing_answer.question_id == command.question_id
                    ):
                        return ApplicationResult(value=existing_answer)

            answer_round = self._polish_repository.count_answers_for_question(
                command.owner_id,
                command.question_id,
            ) + 1
            now = utc_now()
            answer = PolishAnswer(
                answer_id=generate_resource_id(ResourceIdPrefix.ANSWER),
                owner_id=command.owner_id,
                actor_id=command.actor_id,
                session_id=command.session_id,
                question_id=command.question_id,
                answer_round=answer_round,
                answer_text=answer_text,
                status=ANSWER_STATUS_SAVED,
                created_at=now,
                updated_at=now,
            )
            self._polish_repository.add_answer(answer)
            if idempotency_key is not None:
                _remember_answer_idempotency_record(
                    owner_id=command.owner_id,
                    session_id=command.session_id,
                    question_id=command.question_id,
                    idempotency_key=idempotency_key,
                    answer_id=answer.answer_id,
                    answer_text=answer_text,
                )
        return ApplicationResult(value=answer)

    def create_feedback_task(self, command: CreatePolishFeedbackTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        answer = self._polish_repository.get_answer(command.owner_id, command.answer_id)
        if answer is None or answer.session_id != command.session_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Answer not found")
            )
        question = self._polish_repository.get_question(command.owner_id, answer.question_id)
        if question is None or question.session_id != command.session_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Question not found")
            )
        same_session_answers = self._polish_repository.list_answers_for_session(
            command.owner_id,
            command.session_id,
        )
        same_session_feedbacks = self._polish_repository.list_feedbacks_for_session(
            command.owner_id,
            command.session_id,
        )
        previous_answers = tuple(
            previous_answer
            for previous_answer in same_session_answers
            if previous_answer.question_id == answer.question_id
            and previous_answer.answer_id != answer.answer_id
            and previous_answer.answer_round < answer.answer_round
        )
        latest_feedback_by_answer_id = _latest_feedback_by_answer_id(same_session_feedbacks)
        previous_feedbacks = tuple(
            previous_feedback
            for previous_answer in previous_answers
            if (previous_feedback := latest_feedback_by_answer_id.get(previous_answer.answer_id)) is not None
        )

        now = utc_now()
        task_id = generate_resource_id(ResourceIdPrefix.TASK)
        feedback_id = generate_resource_id(ResourceIdPrefix.TRACE)
        score_result_id = generate_resource_id(ResourceIdPrefix.SCORE)
        feedback_input = _build_feedback_input(
            session=session,
            question=question,
            answer=answer,
            previous_answers=previous_answers,
            previous_feedbacks=previous_feedbacks,
        )
        raw_feedback_payload = _build_deterministic_structured_feedback_payload(
            feedback_input=feedback_input,
            session=session,
            question=question,
            answer=answer,
            feedback_id=feedback_id,
            ai_task_id=task_id,
            score_result_id=score_result_id,
            created_at=now,
        )
        feedback_llm_result = self._feedback_llm_service.generate_with_llm_or_fallback(
            feedback_input=feedback_input,
            deterministic_payload=raw_feedback_payload,
        )
        raw_feedback_payload = feedback_llm_result.feedback_payload
        validation_result = validate_feedback_consistency(raw_feedback_payload)
        feedback_payload = validation_result["normalized_feedback_payload"]
        feedback_payload = _ensure_feedback_legacy_compatibility(
            feedback_payload,
            session=session,
            question=question,
            answer=answer,
            feedback_id=feedback_id,
            ai_task_id=task_id,
            score_result_id=score_result_id,
            validation_result=validation_result,
            created_at=now,
        )
        try:
            feedback_payload = extract_feedback_candidates(
                CandidateExtractionInput(
                    owner_id=command.owner_id,
                    session_id=command.session_id,
                    question_id=question.question_id,
                    answer_id=answer.answer_id,
                    feedback_id=feedback_id,
                    score_result_id=score_result_id,
                    feedback_payload=feedback_payload,
                    question_metadata=question.question_metadata,
                    created_at=now,
                )
            )
        except Exception as exc:
            metadata = feedback_payload.get("feedback_metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            metadata["candidate_extraction_failed"] = True
            metadata["candidate_extraction_error"] = type(exc).__name__
            feedback_payload["feedback_metadata"] = metadata
        feedback_payload = self._candidate_llm_service.enhance_with_llm_or_fallback(
            feedback_payload=feedback_payload,
        )
        payload_error = _validate_contract_shaped_feedback_payload(feedback_payload)
        if payload_error is not None:
            return ApplicationResult(error=payload_error)
        persisted_candidate_refs: tuple[ResourceRef, ...] = ()
        if self._candidate_repository is not None:
            persisted_candidates = self._candidate_repository.upsert_from_feedback_payload(
                command.owner_id,
                feedback_payload,
            )
            persisted_candidate_refs = tuple(
                ResourceRef(
                    resource_type=str(candidate["candidate_type"]),
                    resource_id=str(candidate["candidate_id"]),
                )
                for candidate in persisted_candidates
                if candidate.get("candidate_type") and candidate.get("candidate_id")
            )
        feedback = PolishFeedback(
            feedback_id=feedback_id,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            session_id=command.session_id,
            answer_id=command.answer_id,
            ai_task_id=task_id,
            score_result_id=score_result_id,
            feedback_summary=_serialize_feedback_payload(feedback_payload),
            status=FEEDBACK_STATUS_GENERATED,
            created_at=now,
            updated_at=now,
        )
        task = PolishTaskStatus(
            ai_task_id=task_id,
            task_type="polish_feedback_generation",
            status=AiTaskStatus.SUCCEEDED,
            contract_ids=FEEDBACK_CONTRACT_IDS,
            retryable=False,
            result_ref=TraceRef(trace_ref_id=feedback_id, trace_type="feedback", created_at=now),
            user_visible_status="反馈已生成",
            score_type=ScoreType.POLISH_ANSWER,
            candidate_refs=persisted_candidate_refs,
        )
        self._polish_repository.add_feedback(feedback)
        self._polish_repository.add_task(
            task,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            target_ref_id=command.answer_id,
        )
        return ApplicationResult(value=task)

    def refresh_progress_tree_state(
        self,
        command: RefreshPolishProgressTreeStateCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )

        detail = self._build_session_detail(owner_id=command.owner_id, session=session)
        if _should_regenerate_progress_tree(detail):
            progress_artifacts = self._progress_tree_service.generate_initial(detail.progress_context)
        else:
            progress_artifacts = self._progress_tree_service.refresh_state(
                context=detail.progress_context,
                existing_plan=detail.progress_tree_plan,
                existing_state=detail.progress_tree_state,
            )
        progress_artifacts = _progress_artifacts_with_theme(progress_artifacts, _session_theme_strategy(session))
        updated_session = replace(
            session,
            updated_at=utc_now(),
            progress_tree_status=progress_artifacts["status"],
            progress_percent=progress_artifacts["progress_percent"],
            progress_tree_plan=progress_artifacts["progress_tree_plan"],
            progress_tree_state=progress_artifacts["progress_tree_state"],
        )
        self._polish_repository.update_progress_tree(updated_session)
        return ApplicationResult(value=self._build_session_detail(owner_id=command.owner_id, session=updated_session))

    def _build_session_detail(
        self, *, owner_id: str, session: PolishSession, include_turns: bool = True
    ) -> PolishSessionDetail:
        job = self._resolve_job(owner_id=owner_id, job_id=session.job_id)
        job_version = self._resolve_job_version(owner_id=owner_id, session=session)
        resume = self._resolve_resume(owner_id=owner_id, resume_id=session.resume_id)
        resume_version = self._resolve_resume_version(owner_id=owner_id, session=session)
        job_title, job_company = self._job_labels_from_job(job)
        resume_title = self._resume_title_from_resume(resume)
        binding_label = self._build_binding_label(job_title=job_title, resume_title=resume_title)
        turns = self._build_session_turns(owner_id=owner_id, session_id=session.session_id) if include_turns else ()
        detail = PolishSessionDetail(
            session=session,
            job_title=job_title,
            job_company=job_company,
            resume_title=resume_title,
            binding_label=binding_label,
            turns=tuple(turns),
        )
        match_analysis = self._resolve_match_analysis(owner_id=owner_id, session=session)
        progress_context = build_polish_progress_context(
            detail,
            job=job,
            job_version=job_version,
            resume=resume,
            resume_version=resume_version,
            match_analysis=match_analysis,
            weaknesses=None,
            assets=None,
        )
        progress_tree_plan = session.progress_tree_plan or {
            "status": session.progress_tree_status,
            "context_digest": progress_context["content_digest"],
            "nodes": [],
        }
        progress_tree_state = session.progress_tree_state or {
            "status": session.progress_tree_status,
            "node_states": [],
            "current_priority": None,
            "updated_from_turns_count": 0,
            "progress": {"progress_percent": session.progress_percent},
        }
        return PolishSessionDetail(
            session=session,
            job_title=job_title,
            job_company=job_company,
            resume_title=resume_title,
            binding_label=binding_label,
            turns=tuple(turns),
            progress_tree_status=session.progress_tree_status,
            progress_percent=session.progress_percent,
            progress_context=progress_context,
            progress_tree_plan=progress_tree_plan,
            progress_tree_state=progress_tree_state,
        )

    def _build_session_turns(self, owner_id: str, session_id: str) -> tuple[PolishSessionTurn, ...]:
        questions = self._polish_repository.list_questions_for_session(owner_id=owner_id, session_id=session_id)
        answers = self._polish_repository.list_answers_for_session(owner_id=owner_id, session_id=session_id)
        feedbacks = self._polish_repository.list_feedbacks_for_session(owner_id=owner_id, session_id=session_id)

        feedback_map = _latest_feedback_by_answer_id(feedbacks)
        answers_by_question: dict[str, list[PolishSessionAnswerDetail]] = {}
        for answer in answers:
            answers_by_question.setdefault(answer.question_id, []).append(
                _to_session_answer_detail(answer=answer, feedback=feedback_map.get(answer.answer_id))
            )

        return tuple(
            PolishSessionTurn(
                question_id=question.question_id,
                question_text=_or_fallback_text(question.question_text, UNNAMED_QUESTION_TEXT),
                question_created_at=question.created_at,
                question_sources=question.question_sources,
                progress_node_ref=question.progress_node_ref,
                evidence_refs=question.evidence_refs,
                context_digest=question.context_digest,
                question_metadata=question.question_metadata,
                answers=tuple(answers_by_question.get(question.question_id, ())),
            )
            for question in questions
        )

    def _resolve_job_labels(self, *, owner_id: str, job_id: str) -> tuple[str, str]:
        return self._job_labels_from_job(self._resolve_job(owner_id=owner_id, job_id=job_id))

    def _resolve_resume_title(self, *, owner_id: str, resume_id: str) -> str:
        return self._resume_title_from_resume(self._resolve_resume(owner_id=owner_id, resume_id=resume_id))

    def _resolve_job(self, *, owner_id: str, job_id: str) -> Job | None:
        if not job_id:
            return None
        job = self._job_repository.get(job_id)
        if job is None or job.owner_id != owner_id:
            return None
        return job

    def _resolve_job_version(self, *, owner_id: str, session: PolishSession) -> JobVersion | None:
        if not session.job_version_id:
            return None
        job_version = self._job_repository.get_job_version(session.job_version_id)
        if (
            job_version is None
            or job_version.owner_id != owner_id
            or job_version.job_id != session.job_id
        ):
            return None
        return job_version

    def _resolve_resume(self, *, owner_id: str, resume_id: str) -> Resume | None:
        if not resume_id:
            return None
        resume = self._resume_repository.get(resume_id)
        if resume is None or resume.owner_ref.owner_id != owner_id:
            return None
        return resume

    def _resolve_resume_version(self, *, owner_id: str, session: PolishSession) -> ResumeVersion | None:
        if not session.resume_version_id:
            return None
        resume_version = self._resume_repository.get_version(session.resume_version_id)
        if (
            resume_version is None
            or resume_version.owner_id != owner_id
            or resume_version.resume_id != session.resume_id
        ):
            return None
        return resume_version

    def _resolve_match_analysis(self, *, owner_id: str, session: PolishSession) -> JobMatchAnalysis | None:
        if self._job_match_repository is None:
            return None
        analysis = self._job_match_repository.get_latest_by_binding(owner_id, session.binding_id)
        if analysis is None or analysis.owner_id != owner_id:
            return None
        if analysis.resume_version_id != session.resume_version_id or analysis.job_version_id != session.job_version_id:
            return None
        return analysis

    def _job_labels_from_job(self, job: Job | None) -> tuple[str, str]:
        if job is None:
            return (UNNAMED_JOB_TITLE, UNNAMED_COMPANY_TITLE)
        return (
            _or_fallback_text(job.title, UNNAMED_JOB_TITLE),
            _or_fallback_text(job.company, UNNAMED_COMPANY_TITLE),
        )

    def _resume_title_from_resume(self, resume: Resume | None) -> str:
        if resume is None:
            return UNNAMED_RESUME_TITLE
        return _or_fallback_text(resume.title, UNNAMED_RESUME_TITLE)

    def _build_binding_label(self, *, job_title: str, resume_title: str) -> str:
        if job_title and resume_title:
            return f"{job_title} / {resume_title}"
        return f"{job_title or UNNAMED_JOB_TITLE} / {resume_title or UNNAMED_RESUME_TITLE}"


def _metadata_for_new_question(raw_metadata: object, *, generated_at: str) -> dict[str, Any]:
    try:
        metadata = normalize_question_metadata(raw_metadata)
    except Exception:
        metadata = empty_question_metadata().to_dict()
    metadata["generated_at"] = generated_at
    return metadata


def _progress_tree_state_with_completed_question(
    raw_state: object,
    *,
    progress_tree_plan: object,
    question: PolishQuestion,
    completed_at: object,
) -> dict[str, Any]:
    state = dict(raw_state) if isinstance(raw_state, dict) else {}
    metadata = question.question_metadata if isinstance(question.question_metadata, dict) else {}
    focus_key = _clean_question_request_text(metadata.get("focus_key")) or _question_request_focus_key(question.question_id)
    progress_node_ref = _clean_question_request_text(question.progress_node_ref)
    completed_entry = {
        "question_id": question.question_id,
        "progress_node_ref": progress_node_ref,
        "focus_key": focus_key,
        "focus_dimension": _clean_question_request_text(metadata.get("focus_dimension")),
        "template_signature": _clean_question_request_text(metadata.get("template_signature")),
        "blueprint_signature": _clean_question_request_text(metadata.get("blueprint_signature")),
        "completed_at": completed_at.isoformat() if hasattr(completed_at, "isoformat") else None,
        "source": "manual_question_complete",
    }
    state["completed_focus_refs"] = _completed_focus_refs_with_entry(
        state.get("completed_focus_refs"),
        completed_entry,
    )
    state["node_states"] = _node_states_with_completed_question(
        state.get("node_states"),
        progress_node_ref=progress_node_ref,
        plan_refs=_plan_progress_node_refs(progress_tree_plan),
    )
    state["summary"] = "manual_question_completed"
    return state


def _progress_tree_state_with_session_ended(raw_state: object, *, ended_at: object) -> dict[str, Any]:
    state = dict(raw_state) if isinstance(raw_state, dict) else {}
    state["session_ended_at"] = ended_at.isoformat() if hasattr(ended_at, "isoformat") else None
    state["summary"] = "session_ended"
    return state


def _completed_focus_refs_with_entry(raw_refs: object, entry: dict[str, Any]) -> list[dict[str, Any]]:
    entries = _normalized_completed_focus_entries(raw_refs)
    entry_key = _completed_focus_entry_key(entry)
    if not any(_completed_focus_entry_key(item) == entry_key for item in entries):
        entries.append(entry)
    return entries


def _normalized_completed_focus_entries(raw_refs: object) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not isinstance(raw_refs, list):
        return entries
    for item in raw_refs:
        if not isinstance(item, dict):
            continue
        focus_key = _clean_question_request_text(item.get("focus_key"))
        question_id = _clean_question_request_text(item.get("question_id"))
        if focus_key is None and question_id is None:
            continue
        entries.append(
            {
                "question_id": question_id,
                "progress_node_ref": _clean_question_request_text(item.get("progress_node_ref")),
                "focus_key": focus_key,
                "focus_dimension": _clean_question_request_text(item.get("focus_dimension")),
                "template_signature": _clean_question_request_text(item.get("template_signature")),
                "blueprint_signature": _clean_question_request_text(item.get("blueprint_signature")),
                "completed_at": _clean_question_request_text(item.get("completed_at")),
                "source": _clean_question_request_text(item.get("source")) or "manual_question_complete",
            }
        )
    return entries


def _completed_focus_entry_key(entry: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    return (
        _clean_question_request_text(entry.get("question_id")),
        _clean_question_request_text(entry.get("progress_node_ref")),
        _clean_question_request_text(entry.get("focus_key")),
    )


def _node_states_with_completed_question(
    raw_node_states: object,
    *,
    progress_node_ref: str | None,
    plan_refs: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(raw_node_states, list):
        return []
    updated_states: list[dict[str, Any]] = []
    for item in raw_node_states:
        if not isinstance(item, dict):
            continue
        updated = {**item}
        node_ref = _clean_question_request_text(updated.get("progress_node_ref"))
        if progress_node_ref and node_ref == progress_node_ref and (not plan_refs or progress_node_ref in plan_refs):
            updated["status"] = "completed"
            updated["completed_questions_count"] = max(_safe_int(updated.get("completed_questions_count")), 1)
        updated_states.append(updated)
    return updated_states


def _plan_progress_node_refs(raw_plan: object) -> set[str]:
    if not isinstance(raw_plan, dict):
        return set()
    refs: set[str] = set()

    def collect(nodes: object) -> None:
        if not isinstance(nodes, list):
            return
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_ref = _clean_question_request_text(node.get("progress_node_ref"))
            if node_ref:
                refs.add(node_ref)
            collect(node.get("children"))

    collect(raw_plan.get("nodes"))
    return refs


def _safe_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _combined_completed_focus_refs(
    command_refs: tuple[str, ...],
    raw_state: object,
    *,
    progress_node_ref: str | None,
) -> tuple[str, ...]:
    refs = list(_clean_question_request_list(command_refs))
    state = raw_state if isinstance(raw_state, dict) else {}
    for item in _normalized_completed_focus_entries(state.get("completed_focus_refs")):
        item_node_ref = _clean_question_request_text(item.get("progress_node_ref"))
        if progress_node_ref is not None and item_node_ref not in {None, progress_node_ref}:
            continue
        focus_key = _clean_question_request_text(item.get("focus_key"))
        if focus_key and focus_key not in refs:
            refs.append(focus_key)
    return tuple(refs)


def _progress_context_with_completed_focus_refs(
    progress_context: dict[str, Any],
    completed_focus_refs: tuple[str, ...],
) -> dict[str, Any]:
    if not completed_focus_refs:
        return progress_context
    return {
        **progress_context,
        "completed_focus_refs": list(completed_focus_refs),
    }


def _stable_polish_question_generation_idempotency_key(
    *,
    owner_id: str,
    session_id: str,
    requested_progress_node_ref: str | None,
    completed_focus_refs: tuple[str, ...],
) -> str:
    completed_focus_digest = sha256(
        json.dumps(list(completed_focus_refs), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    request_digest = sha256(
        json.dumps(
            {
                "owner_id": owner_id,
                "session_id": session_id,
                "progress_node_ref": requested_progress_node_ref or "current",
                "completed_focus_refs_digest": completed_focus_digest,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return f"polish_question_generation:{request_digest}"


def _polish_question_graph_task_status(
    status_ref: AgentTaskStatusRef,
    *,
    requested_progress_node_ref: str | None,
    created_at: Any,
) -> PolishTaskStatus:
    status = _graph_task_status_to_polish_status(status_ref.status)
    return PolishTaskStatus(
        ai_task_id=status_ref.ai_task_id,
        task_type="polish_question_generation",
        status=status,
        contract_ids=QUESTION_CONTRACT_IDS,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=status_ref.agent_run_id, trace_type="agent_run", created_at=created_at),
        user_visible_status="题目生成中" if status == AiTaskStatus.RUNNING else "题目生成任务已启动",
        candidate_refs=_polish_question_graph_candidate_refs(
            status_ref,
            requested_progress_node_ref=requested_progress_node_ref,
        ),
    )


def _graph_status_candidate_payload(status_ref: object) -> dict[str, Any] | None:
    candidate_payloads = getattr(status_ref, "candidate_payloads", ()) or ()
    if candidate_payloads:
        for candidate_payload in candidate_payloads:
            if _is_accepted_polish_question_candidate_payload(candidate_payload):
                return candidate_payload.payload
        return None
    for attribute in ("accepted_candidate", "candidate", "candidate_payload", "question_candidate"):
        candidate = getattr(status_ref, attribute, None)
        if isinstance(candidate, dict):
            return candidate
    return None


def _is_accepted_polish_question_candidate_payload(candidate_payload: object) -> bool:
    if not isinstance(candidate_payload, AgentCandidatePayload):
        return False
    if candidate_payload.status.strip().lower() not in _POLISH_QUESTION_CANDIDATE_STATUSES:
        return False
    if candidate_payload.candidate_type.strip().lower() not in _POLISH_QUESTION_CANDIDATE_TYPES:
        return False
    if (
        candidate_payload.payload_schema_id.strip().lower()
        not in _POLISH_QUESTION_CANDIDATE_PAYLOAD_SCHEMA_IDS
    ):
        return False
    return isinstance(candidate_payload.payload, dict)


def _polish_question_graph_validation_failed_task_status(
    status_ref: AgentTaskStatusRef,
    *,
    requested_progress_node_ref: str | None,
    created_at: Any,
) -> PolishTaskStatus:
    return PolishTaskStatus(
        ai_task_id=status_ref.ai_task_id,
        task_type="polish_question_generation",
        status=AiTaskStatus.VALIDATION_FAILED,
        contract_ids=QUESTION_CONTRACT_IDS,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=status_ref.agent_run_id, trace_type="agent_run", created_at=created_at),
        user_visible_status="题目生成校验未通过",
        candidate_refs=_polish_question_graph_candidate_refs(
            status_ref,
            requested_progress_node_ref=requested_progress_node_ref,
        ),
    )


def _graph_task_status_to_polish_status(raw_status: str) -> AiTaskStatus:
    normalized = str(raw_status or "").strip().lower()
    if normalized in {"running", "in_progress", "started"}:
        return AiTaskStatus.RUNNING
    if normalized in {"cancelled", "canceled"}:
        return AiTaskStatus.CANCELLED
    if normalized in {"timed_out", "timeout"}:
        return AiTaskStatus.TIMED_OUT
    if normalized in {"validation_failed", "invalid"}:
        return AiTaskStatus.VALIDATION_FAILED
    if "failed" in normalized or normalized in {"error", "errored"}:
        return AiTaskStatus.GENERATION_FAILED
    return AiTaskStatus.QUEUED


def _polish_question_graph_candidate_refs(
    status_ref: AgentTaskStatusRef,
    *,
    requested_progress_node_ref: str | None,
) -> tuple[ResourceRef, ...]:
    refs: list[ResourceRef] = [ResourceRef(resource_type="agent_run", resource_id=status_ref.agent_run_id)]
    refs.extend(ResourceRef(resource_type="trace", resource_id=trace_ref) for trace_ref in status_ref.trace_refs)
    refs.extend(
        ResourceRef(resource_type="question_candidate", resource_id=candidate_ref)
        for candidate_ref in status_ref.candidate_refs
    )
    refs.extend(
        ResourceRef(resource_type="agent_interrupt", resource_id=interrupt_ref)
        for interrupt_ref in status_ref.interrupt_refs
    )
    if requested_progress_node_ref is not None:
        refs.append(ResourceRef(resource_type="progress_node", resource_id=requested_progress_node_ref))
    return tuple(refs)


def _build_follow_up_question_draft(
    *,
    command: CreatePolishQuestionTaskCommand,
    detail: PolishSessionDetail,
) -> PolishQuestionDraft | DomainError:
    parent_turn = _find_turn(detail.turns, command.parent_question_id)
    if parent_turn is None:
        return DomainError(
            code="validation_failed",
            message="follow_up parent question is not in this session",
            details={"field": "parent_question_id"},
        )
    parent_answer = _find_turn_answer(parent_turn, command.parent_answer_id)
    if parent_answer is None:
        return DomainError(
            code="validation_failed",
            message="follow_up parent answer is not in this session",
            details={"field": "parent_answer_id"},
        )
    if command.parent_feedback_id is not None and parent_answer.feedback_id != command.parent_feedback_id:
        return DomainError(
            code="validation_failed",
            message="follow_up parent feedback does not match parent answer",
            details={"field": "parent_feedback_id"},
        )

    target_dimension, follow_up_reason = _select_follow_up_target(parent_turn, parent_answer)
    answer_excerpt = _follow_up_excerpt(parent_answer.answer_text)
    focus_key = _question_request_focus_key(target_dimension)
    progress_node_ref = _clean_question_request_text(command.selected_progress_node_ref) or parent_turn.progress_node_ref
    question_text = (
        f"你上一轮回答中提到「{answer_excerpt}」，但还没有讲清楚「{target_dimension}」。"
        "现在只聚焦这个点：请结合上一题背景，说明你的具体判断、边界、失败处理、验证指标和关键取舍。"
    )
    metadata = empty_question_metadata().to_dict()
    metadata.update(
        {
            "question_pattern": "follow_up_targeted",
            "expected_answer_dimensions": [target_dimension],
            "quality_score": 90,
            "quality_warnings": [],
            "confidence_level": "medium",
            "low_confidence_flags": [],
            "source_availability": "available",
            "focus_dimension": target_dimension,
            "focus_key": focus_key,
            "template_signature": f"tpl:follow_up_targeted:{focus_key}",
            "blueprint_signature": _follow_up_blueprint_signature(
                parent_turn.question_id,
                parent_answer.answer_id,
                focus_key,
            ),
            "duplicate_gate_result": "follow_up_parent_bound",
            "similarity_checked": True,
            "max_similarity_in_same_category": 0.0,
            "mastery_exception_used": True,
            "follow_up_reason": follow_up_reason,
            "follow_up_target_dimension": target_dimension,
        }
    )
    return PolishQuestionDraft(
        question_text=question_text,
        question_sources=(
            PolishQuestionSource(
                index=1,
                source_type="history_feedback",
                title="上一轮回答与反馈",
                excerpt=_follow_up_source_excerpt(parent_answer),
                ref_id=parent_answer.feedback_id or parent_answer.answer_id,
                availability="available",
            ),
        ),
        progress_node_ref=progress_node_ref,
        evidence_refs=parent_turn.evidence_refs,
        context_digest=parent_turn.context_digest or detail.progress_context.get("content_digest"),
        question_pattern="follow_up_targeted",
        quality_score=90,
        confidence_level="medium",
        expected_answer_dimensions=(target_dimension,),
        question_metadata=metadata,
    )


def _find_turn(turns: tuple[PolishSessionTurn, ...], question_id: str | None) -> PolishSessionTurn | None:
    if question_id is None:
        return None
    return next((turn for turn in turns if turn.question_id == question_id), None)


def _find_turn_answer(
    turn: PolishSessionTurn,
    answer_id: str | None,
) -> PolishSessionAnswerDetail | None:
    if answer_id is None:
        return None
    return next((answer for answer in turn.answers if answer.answer_id == answer_id), None)


def _select_follow_up_target(
    parent_turn: PolishSessionTurn,
    parent_answer: PolishSessionAnswerDetail,
) -> tuple[str, str]:
    payload = parent_answer.feedback_payload if isinstance(parent_answer.feedback_payload, dict) else {}
    for item in _dict_list(payload.get("missing_answer_dimensions")):
        target = _compact_follow_up_target(
            item.get("title") or item.get("dimension_id") or item.get("expected_dimension")
        )
        if target:
            return target, "missing_answer_dimension"
    for key, reason in (("technical_gaps", "technical_gap"), ("communication_gaps", "communication_gap")):
        for item in payload.get(key) or []:
            target = _compact_follow_up_target(item)
            if target:
                return target, reason
    for item in _dict_list(payload.get("loss_points")):
        target = _compact_follow_up_target(item.get("title") or item.get("reason"))
        if target:
            return target, "loss_point"
    for dimension in parent_turn.question_metadata.get("expected_answer_dimensions") or []:
        target = _compact_follow_up_target(dimension)
        if target and target not in parent_answer.answer_text:
            return target, "unanswered_expected_dimension"
    return "失败路径、边界和验证指标", "category_uncovered_direction"


def _compact_follow_up_target(value: object) -> str | None:
    text = _clean_question_request_text(value, max_chars=80)
    return text or None


def _follow_up_excerpt(answer_text: str) -> str:
    return _clean_question_request_text(answer_text, max_chars=80) or "上一轮回答"


def _follow_up_source_excerpt(parent_answer: PolishSessionAnswerDetail) -> str:
    feedback_text = _clean_question_request_text(parent_answer.feedback_text, max_chars=120)
    answer_text = _follow_up_excerpt(parent_answer.answer_text)
    if feedback_text:
        return f"回答：{answer_text}；反馈：{feedback_text}"
    return f"回答：{answer_text}"


def _question_request_focus_key(target_dimension: str) -> str:
    seed = _clean_question_request_text(target_dimension, max_chars=160) or "follow_up"
    return f"focus_{sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _follow_up_blueprint_signature(parent_question_id: str, parent_answer_id: str, focus_key: str) -> str:
    seed = f"{parent_question_id}:{parent_answer_id}:{focus_key}"
    return f"bp:{sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def _validate_question_generation_request(command: CreatePolishQuestionTaskCommand) -> DomainError | None:
    mode = _question_generation_mode(command)
    if mode not in QUESTION_GENERATION_MODES:
        return DomainError(
            code="validation_failed",
            message="Invalid question generation mode",
            details={"field": "generation_mode"},
        )
    if command.generation_mode is not None and mode == QUESTION_GENERATION_MODE_NEW:
        if _question_generation_requested_ref(command) is None:
            return DomainError(
                code="validation_failed",
                message="new_question requires a selected progress node",
                details={"field": "selected_progress_node_ref"},
            )
    if mode == QUESTION_GENERATION_MODE_FOLLOW_UP:
        if _clean_question_request_text(command.parent_question_id) is None:
            return DomainError(
                code="validation_failed",
                message="follow_up requires parent_question_id",
                details={"field": "parent_question_id"},
            )
        if _clean_question_request_text(command.parent_answer_id) is None:
            return DomainError(
                code="validation_failed",
                message="follow_up requires parent_answer_id",
                details={"field": "parent_answer_id"},
            )
    return None


def _question_generation_mode(command: CreatePolishQuestionTaskCommand) -> str:
    return _clean_question_request_text(command.generation_mode) or QUESTION_GENERATION_MODE_NEW


def _question_generation_requested_ref(command: CreatePolishQuestionTaskCommand) -> str | None:
    return (
        _clean_question_request_text(command.selected_progress_node_ref)
        or _clean_question_request_text(command.selected_secondary_category_ref)
        or _clean_question_request_text(command.progress_node_ref)
    )


def _question_generation_request_metadata(
    command: CreatePolishQuestionTaskCommand,
    *,
    requested_progress_node_ref: str | None,
    resolved_progress_node_ref: str | None,
) -> dict[str, Any]:
    mode = _question_generation_mode(command)
    selected_progress_node_ref = (
        _clean_question_request_text(command.selected_progress_node_ref)
        or requested_progress_node_ref
        or _clean_question_request_text(resolved_progress_node_ref)
    )
    return {
        "generation_mode": mode,
        "request_source": _question_generation_request_source(command, mode),
        "selected_primary_category_ref": _clean_question_request_text(command.selected_primary_category_ref),
        "selected_secondary_category_ref": _clean_question_request_text(command.selected_secondary_category_ref),
        "selected_progress_node_ref": selected_progress_node_ref,
        "selected_category_path": list(_clean_question_request_list(command.selected_category_path)),
        "parent_question_id": _clean_question_request_text(command.parent_question_id),
        "parent_answer_id": _clean_question_request_text(command.parent_answer_id),
        "parent_feedback_id": _clean_question_request_text(command.parent_feedback_id),
        "exclude_question_refs": list(_clean_question_request_list(command.exclude_question_refs)),
        "completed_focus_refs": list(_clean_question_request_list(command.completed_focus_refs)),
    }


def _question_generation_request_source(command: CreatePolishQuestionTaskCommand, mode: str) -> str:
    if command.generation_mode is None:
        return "legacy_progress_node_ref" if _clean_question_request_text(command.progress_node_ref) else "legacy_fallback"
    if mode == QUESTION_GENERATION_MODE_FOLLOW_UP:
        return "explicit_follow_up"
    return "explicit_selected_category"


def _clean_question_request_list(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for value in values:
        text = _clean_question_request_text(value)
        if text is not None and text not in cleaned:
            cleaned.append(text)
    return tuple(cleaned)


def _clean_question_request_text(value: object, *, max_chars: int = 240) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    return text[:max_chars]


def _validate_topic_selection(topic_id: str | None, subtopic_id: str | None) -> DomainError | None:
    if topic_id is None:
        if subtopic_id is not None:
            return DomainError(
                code="validation_failed",
                message="subtopic_id requires topic_id",
                details={"field": "subtopic_id"},
            )
        return None

    topic = next((item for item in POLISH_TOPICS if item.topic_id == topic_id), None)
    if topic is None:
        return DomainError(
            code="validation_failed",
            message="Invalid polish topic",
            details={"field": "topic_id"},
        )
    if subtopic_id is None:
        return None
    if not any(item.subtopic_id == subtopic_id for item in topic.subtopics):
        return DomainError(
            code="validation_failed",
            message="Invalid polish subtopic",
            details={"field": "subtopic_id"},
        )
    return None


def _validate_answer_text(answer_text: str) -> DomainError | None:
    if not answer_text:
        return DomainError(
            code="validation_failed",
            message="Answer text cannot be empty",
            details={
                "field": "answer_text",
                "min_length": ANSWER_TEXT_MIN_LENGTH,
                "max_length": ANSWER_TEXT_MAX_LENGTH,
            },
        )
    if len(answer_text) < ANSWER_TEXT_MIN_LENGTH:
        return DomainError(
            code="validation_failed",
            message="Answer text is too short",
            details={
                "field": "answer_text",
                "min_length": ANSWER_TEXT_MIN_LENGTH,
                "actual_length": len(answer_text),
            },
        )
    if len(answer_text) > ANSWER_TEXT_MAX_LENGTH:
        return DomainError(
            code="validation_failed",
            message="Answer text is too long",
            details={
                "field": "answer_text",
                "max_length": ANSWER_TEXT_MAX_LENGTH,
                "actual_length": len(answer_text),
            },
        )
    return None


def _validate_answer_idempotency_key(raw_key: object) -> DomainError | None:
    key = _normalize_answer_idempotency_key(raw_key)
    if key is None:
        return None
    if len(key) > ANSWER_IDEMPOTENCY_KEY_MAX_LENGTH:
        return DomainError(
            code="validation_failed",
            message="Idempotency key is too long",
            details={
                "field": "idempotency_key",
                "max_length": ANSWER_IDEMPOTENCY_KEY_MAX_LENGTH,
                "actual_length": len(key),
            },
        )
    return None


def _normalize_answer_idempotency_key(raw_key: object) -> str | None:
    if raw_key is None:
        return None
    key = str(raw_key).strip()
    return key or None


def _answer_submission_lock(*, owner_id: str, session_id: str, question_id: str) -> threading.Lock:
    lock_key = (owner_id, session_id, question_id)
    with _ANSWER_SUBMISSION_LOCKS_GUARD:
        lock = _ANSWER_SUBMISSION_LOCKS.get(lock_key)
        if lock is None:
            lock = threading.Lock()
            _ANSWER_SUBMISSION_LOCKS[lock_key] = lock
        return lock


def _cached_answer_idempotency_record(
    *,
    owner_id: str,
    session_id: str,
    question_id: str,
    idempotency_key: str,
) -> tuple[str, str] | None:
    with _ANSWER_IDEMPOTENCY_CACHE_GUARD:
        return _ANSWER_IDEMPOTENCY_CACHE.get((owner_id, session_id, question_id, idempotency_key))


def _remember_answer_idempotency_record(
    *,
    owner_id: str,
    session_id: str,
    question_id: str,
    idempotency_key: str,
    answer_id: str,
    answer_text: str,
) -> None:
    with _ANSWER_IDEMPOTENCY_CACHE_GUARD:
        _ANSWER_IDEMPOTENCY_CACHE[(owner_id, session_id, question_id, idempotency_key)] = (
            answer_id,
            answer_text,
        )


def _build_feedback_input(
    *,
    session: PolishSession,
    question: PolishQuestion,
    answer: PolishAnswer,
    previous_answers: tuple[PolishAnswer, ...],
    previous_feedbacks: tuple[PolishFeedback, ...],
) -> FeedbackInput:
    strategy = _session_theme_strategy(session)
    question_metadata = _safe_question_metadata(question.question_metadata)
    previous_feedback_payloads = _previous_feedback_payloads(previous_feedbacks)
    previous_loss_points = _previous_loss_points_from_payloads(previous_feedback_payloads)
    current_missing_dimensions = _feedback_missing_dimension_ids(answer.answer_text)
    repeated_gaps = tuple(
        point["loss_point_id"]
        for point in previous_loss_points
        if point.get("dimension_id") in current_missing_dimensions and point.get("loss_point_id")
    )
    fixed_gaps = tuple(
        point["loss_point_id"]
        for point in previous_loss_points
        if point.get("dimension_id") not in current_missing_dimensions and point.get("loss_point_id")
    )
    previous_loss_dimensions = {
        str(point.get("dimension_id"))
        for point in previous_loss_points
        if point.get("dimension_id")
    }
    regression_signals = tuple(
        dimension_id
        for dimension_id in current_missing_dimensions
        if dimension_id not in previous_loss_dimensions
    )
    base_kwargs = {
        "owner_id": answer.owner_id,
        "actor_id": answer.actor_id,
        "session_id": answer.session_id,
        "question_id": question.question_id,
        "answer_id": answer.answer_id,
        "answer_round": answer.answer_round,
        "question_text": _or_fallback_text(question.question_text, UNNAMED_QUESTION_TEXT),
        "question_metadata": question_metadata,
        "question_pattern": _metadata_text(question_metadata, "question_pattern", "fallback_general"),
        "expected_answer_dimensions": _expected_answer_dimensions(question_metadata),
        "interview_intent": _metadata_text(question_metadata, "interview_intent", strategy.question_intent),
        "question_sources": _question_sources_for_feedback_input(question),
        "evidence_refs": _evidence_refs_for_feedback_input(question),
        "answer_text": _or_fallback_text(answer.answer_text, UNNAMED_ANSWER_TEXT),
        "polish_theme": strategy.theme,
        "source_availability": _metadata_text(question_metadata, "source_availability", "unknown"),
        "low_confidence_flags": _feedback_input_low_confidence_flags(
            question_metadata=question_metadata,
            answer_text=answer.answer_text,
            metadata_missing=_is_question_metadata_missing(question.question_metadata),
        ),
        "feedback_generation_mode": "deterministic_retry" if answer.answer_round > 1 else "deterministic_initial",
    }
    if answer.answer_round <= 1:
        return FeedbackInput(**base_kwargs)
    return RetryFeedbackInput(
        **base_kwargs,
        previous_answer_rounds=tuple(
            {
                "answer_id": previous_answer.answer_id,
                "answer_round": previous_answer.answer_round,
                "answer_text": previous_answer.answer_text,
                "created_at": previous_answer.created_at.isoformat(),
            }
            for previous_answer in previous_answers
        ),
        previous_feedbacks=previous_feedback_payloads,
        previous_score_results=tuple(
            payload.get("score_result")
            for payload in previous_feedback_payloads
            if isinstance(payload.get("score_result"), dict)
        ),
        previous_dimension_scores=tuple(
            {
                **dimension,
                "feedback_id": payload.get("feedback_id"),
            }
            for payload in previous_feedback_payloads
            for dimension in _dict_list(payload.get("scoring_dimensions"))
        ),
        previous_loss_points=previous_loss_points,
        previous_reference_answer=_latest_payload_text(previous_feedback_payloads, "p7_reference_answer"),
        previous_oral_script=_latest_payload_text(previous_feedback_payloads, "oral_script"),
        repeated_gaps=repeated_gaps,
        fixed_gaps=fixed_gaps,
        regression_signals=regression_signals,
        mastery_threshold="score>=80_and_no_remaining_critical_loss",
    )


def _build_deterministic_structured_feedback_payload(
    *,
    feedback_input: FeedbackInput,
    session: PolishSession,
    question: PolishQuestion,
    answer: PolishAnswer,
    feedback_id: str,
    ai_task_id: str,
    score_result_id: str,
    created_at,
) -> dict[str, Any]:
    strategy = _session_theme_strategy(session)
    theme_profile = _theme_feedback_profile(strategy)
    answer_text = _or_fallback_text(feedback_input.answer_text, UNNAMED_ANSWER_TEXT)
    scoring_dimensions = _structured_scoring_dimensions(answer_text)
    score_result = compute_score_result_from_dimensions(scoring_dimensions)
    score_result = {
        **score_result,
        "score_result_id": score_result_id,
        "score_type": str(ScoreType.POLISH_ANSWER),
        "score_version": f"polish_answer.{strategy.theme}.deterministic.v1",
        "rubric_version": "polish_round_score.structured.v1",
        "contract_id": "P-POLISH-004",
        "confidence_level": "low" if feedback_input.low_confidence_flags else "medium",
    }
    score_value = int(score_result["score_value"])
    explicit_score, implicit_score = _theme_scores(strategy, score_value)
    loss_points = _structured_loss_points(
        feedback_id=feedback_id,
        answer=answer,
        scoring_dimensions=scoring_dimensions,
    )
    positive_evidence_points = _structured_positive_evidence_points(
        answer=answer,
        answer_text=answer_text,
        scoring_dimensions=scoring_dimensions,
    )
    p7_reference_answer = _structured_reference_answer(
        theme_profile=theme_profile,
        loss_points=loss_points,
        question_text=feedback_input.question_text,
    )
    oral_script = _structured_oral_script(
        theme_profile=theme_profile,
        loss_points=loss_points,
    )
    feedback_text = (
        f"polish_answer / {strategy.label} structured feedback {score_value}/100："
        f"{theme_profile['summary']}"
    )
    candidate_refs = _feedback_candidate_refs(feedback_id)
    payload: dict[str, Any] = {
        "schema_id": FEEDBACK_SCHEMA_ID,
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "contract_id": "P-POLISH-005",
        "contract_ids": list(FEEDBACK_CONTRACT_IDS),
        "status": FEEDBACK_STATUS_GENERATED,
        "feedback_id": feedback_id,
        "ai_task_id": ai_task_id,
        "polish_theme": strategy.theme,
        "polish_theme_label": strategy.label,
        "explicit_weight": strategy.explicit_weight,
        "implicit_weight": strategy.implicit_weight,
        "weight_explanation": (
            f"本轮按显性技术 {strategy.explicit_weight}%、隐性表达 {strategy.implicit_weight}% 综合打磨；"
            "structured feedback 由回答、题目 metadata 和同题历史轮次确定性生成。"
        ),
        "interview_intent": feedback_input.interview_intent,
        "explicit_score": explicit_score,
        "implicit_score": implicit_score,
        "feedback_text": feedback_text,
        "feedback_summary": feedback_text,
        "answer_diagnosis": {
            "strengths": _answer_strengths(answer_text),
            "weaknesses": [point["title"] for point in loss_points],
            "risks": _answer_risks(loss_points),
            "recommendations": [
                "下一轮优先修复 critical loss_points。",
                "口述时先给结论，再补技术链路、失败路径和指标。",
            ],
        },
        "scoring_dimensions": scoring_dimensions,
        "score_result": score_result,
        "score_result_ref": {"resource_type": "score_result", "resource_id": score_result_id},
        "positive_evidence_points": positive_evidence_points,
        "loss_points": loss_points,
        "missing_answer_dimensions": [
            {
                "dimension": point["dimension_id"],
                "reason": point["reason"],
                "impact_scope": "score_result, reference_answer, oral_script",
            }
            for point in loss_points
        ],
        "technical_gaps": [
            point["title"] for point in loss_points if point.get("dimension_id") == "technical_depth"
        ],
        "communication_gaps": [
            point["title"] for point in loss_points if point.get("dimension_id") == "answer_structure"
        ],
        "p7_reference_answer": p7_reference_answer,
        "reference_answer": {
            "contract_id": "P-POLISH-006",
            "summary": p7_reference_answer,
            "outline": list(theme_profile["reference_outline"]),
        },
        "reference_answer_requirements": _reference_requirements(loss_points),
        "oral_script": oral_script,
        "oral_script_requirements": _oral_script_requirements(loss_points),
        "knowledge_points": [
            {
                "title": theme_profile["knowledge_title"],
                "explanation": theme_profile["knowledge_explanation"],
            }
        ],
        "technical_principles": [
            {
                "title": theme_profile["principle_title"],
                "explanation": theme_profile["principle_explanation"],
            }
        ],
        "next_training_suggestions": list(theme_profile["next_training_suggestions"]),
        "next_recommended_actions": _feedback_next_actions(
            "answer_again" if loss_points else "generate_next_question"
        ),
        "polish_session_ref": {"resource_type": "polish_session", "resource_id": session.session_id},
        "question_ref": {"resource_type": "question", "resource_id": question.question_id},
        "answer_ref": {"resource_type": "answer", "resource_id": answer.answer_id},
        "candidate_refs": candidate_refs,
        "weakness_candidates": [
            {
                "candidate_ref": candidate_refs[0],
                "status": "candidate",
                "source_loss_points": [point["loss_point_id"] for point in loss_points],
            }
        ],
        "asset_candidates": [
            {
                "candidate_ref": candidate_refs[1],
                "status": "candidate",
                "source_positive_points": [point["point_id"] for point in positive_evidence_points],
            }
        ],
        "validation_result_ref": {"resource_type": "validation_result", "resource_id": f"{feedback_id}_validation"},
        "trace_refs": [
            {
                "trace_ref_id": answer.answer_id,
                "trace_type": "answer",
                "created_at": answer.created_at.isoformat(),
                "redaction_boundary": "none",
            },
            {
                "trace_ref_id": feedback_id,
                "trace_type": "feedback",
                "created_at": created_at.isoformat(),
                "redaction_boundary": "none",
            },
            {
                "trace_ref_id": score_result_id,
                "trace_type": "score_result",
                "created_at": created_at.isoformat(),
                "redaction_boundary": "none",
            },
        ],
        "low_confidence_flags": list(feedback_input.low_confidence_flags),
        "user_confirmation_required": False,
        "feedback_metadata": {
            "feedback_input_type": type(feedback_input).__name__,
            "feedback_generation_mode": feedback_input.feedback_generation_mode,
            "question_pattern": feedback_input.question_pattern,
            "source_availability": feedback_input.source_availability,
            "previous_answer_rounds_count": (
                len(feedback_input.previous_answer_rounds)
                if isinstance(feedback_input, RetryFeedbackInput)
                else 0
            ),
        },
        "legacy_compatibility": {"feedback_text": feedback_text},
        "answer_id": answer.answer_id,
        "question_id": question.question_id,
        "question_text": feedback_input.question_text,
        "answer_text": answer_text,
        "score_delta": 0,
        "dimension_delta": {},
        "improved_points": [],
        "remaining_gaps": [],
        "repeated_loss_points": [],
        "regressed_points": [],
        "mastery_status": None,
        "should_continue_same_question": bool(loss_points),
        "should_generate_next_question": not bool(loss_points),
        "next_retry_focus": [],
        "updated_reference_answer": None,
        "updated_oral_script": None,
        "previous_loss_points": [],
    }
    if isinstance(feedback_input, RetryFeedbackInput):
        payload.update(
            _retry_delta_payload(
                feedback_input=feedback_input,
                score_result=score_result,
                scoring_dimensions=scoring_dimensions,
                loss_points=loss_points,
                p7_reference_answer=p7_reference_answer,
                oral_script=oral_script,
            )
        )
    return payload


def _ensure_feedback_legacy_compatibility(
    payload: dict[str, Any],
    *,
    session: PolishSession,
    question: PolishQuestion,
    answer: PolishAnswer,
    feedback_id: str,
    ai_task_id: str,
    score_result_id: str,
    validation_result: dict[str, Any],
    created_at,
) -> dict[str, Any]:
    strategy = _session_theme_strategy(session)
    theme_profile = _theme_feedback_profile(strategy)
    result = dict(payload)
    result.setdefault("schema_id", FEEDBACK_SCHEMA_ID)
    result.setdefault("schema_version", FEEDBACK_SCHEMA_VERSION)
    result.setdefault("contract_id", "P-POLISH-005")
    result.setdefault("contract_ids", list(FEEDBACK_CONTRACT_IDS))
    result.setdefault("feedback_id", feedback_id)
    result.setdefault("ai_task_id", ai_task_id)
    result.setdefault("status", FEEDBACK_STATUS_GENERATED)
    result.setdefault("polish_theme", strategy.theme)
    result.setdefault("polish_theme_label", strategy.label)
    result.setdefault("explicit_weight", strategy.explicit_weight)
    result.setdefault("implicit_weight", strategy.implicit_weight)
    result.setdefault(
        "weight_explanation",
        f"本轮按显性技术 {strategy.explicit_weight}%、隐性表达 {strategy.implicit_weight}% 综合打磨。",
    )
    result.setdefault("interview_intent", strategy.question_intent)
    result.setdefault("p7_reference_answer", theme_profile["p7_reference_answer"])
    result.setdefault("oral_script", theme_profile["oral_script"])
    result.setdefault("next_training_suggestions", list(theme_profile["next_training_suggestions"]))
    result.setdefault("technical_gaps", [])
    result.setdefault("communication_gaps", [])
    score_result = result.get("score_result")
    if not isinstance(score_result, dict):
        score_result = {
            **compute_score_result_from_dimensions(result.get("scoring_dimensions", [])),
            "score_result_id": score_result_id,
            "score_type": str(ScoreType.POLISH_ANSWER),
            "score_version": FEEDBACK_SCHEMA_VERSION,
            "rubric_version": "polish_round_score.structured.v1",
            "contract_id": "P-POLISH-004",
            "confidence_level": "low",
        }
        result["score_result"] = score_result
    score_value = int(score_result.get("score_value", 0))
    explicit_score, implicit_score = _theme_scores(strategy, score_value)
    result.setdefault("explicit_score", explicit_score)
    result.setdefault("implicit_score", implicit_score)
    result.setdefault("score_result_ref", {"resource_type": "score_result", "resource_id": score_result_id})
    feedback_text = str(result.get("feedback_text") or result.get("feedback_summary") or UNNAMED_FEEDBACK_TEXT)
    result["feedback_text"] = feedback_text
    result["feedback_summary"] = str(result.get("feedback_summary") or feedback_text)
    result.setdefault(
        "reference_answer",
        {
            "contract_id": "P-POLISH-006",
            "summary": result["p7_reference_answer"],
            "outline": list(theme_profile["reference_outline"]),
        },
    )
    result.setdefault("knowledge_points", [])
    result.setdefault("technical_principles", [])
    result.setdefault("next_recommended_actions", _feedback_next_actions("answer_again"))
    if not isinstance(result.get("candidate_refs"), list) or not result["candidate_refs"]:
        result["candidate_refs"] = _feedback_candidate_refs(feedback_id)
    result.setdefault("validation_result_ref", {"resource_type": "validation_result", "resource_id": f"{feedback_id}_validation"})
    result.setdefault(
        "trace_refs",
        [
            {
                "trace_ref_id": answer.answer_id,
                "trace_type": "answer",
                "created_at": answer.created_at.isoformat(),
                "redaction_boundary": "none",
            },
            {
                "trace_ref_id": feedback_id,
                "trace_type": "feedback",
                "created_at": created_at.isoformat(),
                "redaction_boundary": "none",
            },
        ],
    )
    result.setdefault("low_confidence_flags", [])
    result.setdefault("polish_session_ref", {"resource_type": "polish_session", "resource_id": session.session_id})
    result.setdefault("question_ref", {"resource_type": "question", "resource_id": question.question_id})
    result.setdefault("answer_ref", {"resource_type": "answer", "resource_id": answer.answer_id})
    result.setdefault("legacy_compatibility", {})
    if isinstance(result["legacy_compatibility"], dict):
        result["legacy_compatibility"]["feedback_text"] = feedback_text
    if answer.answer_round > 1 and result.get("mastery_status") not in {"regressed", "stuck", "improving", "mastered"}:
        result["mastery_status"] = "stuck"
    result.setdefault("score_delta", 0)
    result.setdefault("dimension_delta", {})
    result.setdefault("improved_points", [])
    result.setdefault("remaining_gaps", [])
    result.setdefault("repeated_loss_points", [])
    result.setdefault("regressed_points", [])
    result.setdefault("should_continue_same_question", False)
    result.setdefault("should_generate_next_question", False)
    result.setdefault("next_retry_focus", [])
    result.setdefault("updated_reference_answer", None)
    result.setdefault("updated_oral_script", None)
    result.setdefault("previous_loss_points", [])
    metadata = result.get("feedback_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    metadata["validation_allow_emit"] = bool(validation_result.get("allow_emit"))
    metadata["validation_blocking_issues"] = list(validation_result.get("blocking_issues", []))
    metadata["validation_warnings"] = list(validation_result.get("warnings", []))
    result["feedback_metadata"] = metadata
    return result


def _safe_question_metadata(raw_metadata: object) -> dict[str, Any]:
    try:
        return normalize_question_metadata(raw_metadata)
    except Exception:
        return empty_question_metadata().to_dict()


def _is_question_metadata_missing(raw_metadata: object) -> bool:
    return (
        not isinstance(raw_metadata, dict)
        or not raw_metadata.get("question_pattern")
        or not raw_metadata.get("expected_answer_dimensions")
    )


def _metadata_text(metadata: dict[str, Any], key: str, fallback: str) -> str:
    value = metadata.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _expected_answer_dimensions(metadata: dict[str, Any]) -> tuple[str, ...]:
    raw_dimensions = metadata.get("expected_answer_dimensions")
    if isinstance(raw_dimensions, (list, tuple)):
        dimensions = tuple(str(item).strip() for item in raw_dimensions if str(item).strip())
        if dimensions:
            return dimensions
    return ("technical_depth", "answer_structure", "evidence_alignment")


def _question_sources_for_feedback_input(question: PolishQuestion) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "index": source.index,
            "source_type": source.source_type,
            "title": source.title,
            "excerpt": source.excerpt,
            "ref_id": source.ref_id,
            "availability": source.availability,
        }
        for source in question.question_sources
    )


def _evidence_refs_for_feedback_input(question: PolishQuestion) -> tuple[dict[str, Any], ...]:
    return tuple(
        {"resource_type": "evidence", "resource_id": evidence_ref}
        for evidence_ref in question.evidence_refs
    )


def _feedback_input_low_confidence_flags(
    *,
    question_metadata: dict[str, Any],
    answer_text: str,
    metadata_missing: bool,
) -> tuple[dict[str, Any], ...]:
    flags: list[dict[str, Any]] = []
    raw_flags = question_metadata.get("low_confidence_flags", [])
    if isinstance(raw_flags, (list, tuple)):
        for index, raw_flag in enumerate(raw_flags, start=1):
            if isinstance(raw_flag, dict):
                flags.append(dict(raw_flag))
            elif str(raw_flag).strip():
                flags.append(
                    {
                        "flag_id": str(raw_flag).strip(),
                        "reason": "question_metadata_low_confidence",
                        "impact_scope": "feedback_input",
                        "recommended_action": "use_safe_structured_feedback",
                    }
                )
            elif index == 1:
                continue
    if metadata_missing:
        flags.append(
            {
                "flag_id": "question_metadata_missing",
                "reason": "question_metadata_missing_or_legacy_question",
                "impact_scope": "question_pattern, expected_answer_dimensions, source_availability",
                "recommended_action": "fallback_to_empty_question_metadata",
            }
        )
    flags.extend(_feedback_low_confidence_flags(answer_text))
    return tuple(flags)


def _previous_feedback_payloads(previous_feedbacks: tuple[PolishFeedback, ...]) -> tuple[dict[str, Any], ...]:
    payloads: list[dict[str, Any]] = []
    for feedback in previous_feedbacks[-PREVIOUS_FEEDBACK_SUMMARY_LIMIT:]:
        payload = _feedback_payload_from_summary(feedback.feedback_summary)
        if payload is not None:
            payloads.append(_compact_previous_feedback_summary(payload))
    return tuple(payloads)


def _compact_previous_feedback_summary(payload: dict[str, Any]) -> dict[str, Any]:
    reference_answer = _compact_text(payload.get("p7_reference_answer"))
    oral_script = _compact_text(payload.get("oral_script"))
    return {
        "feedback_id": payload.get("feedback_id"),
        "score_result": _compact_score_result(payload.get("score_result")),
        "scoring_dimensions": _compact_scoring_dimensions(payload.get("scoring_dimensions")),
        "loss_points": _compact_loss_points(payload.get("loss_points")),
        "p7_reference_answer": reference_answer,
        "reference_answer_summary": reference_answer,
        "oral_script": oral_script,
        "oral_script_summary": oral_script,
        "next_recommended_actions": [
            str(action)
            for action in (payload.get("next_recommended_actions") or [])
            if isinstance(action, str)
        ],
    }


def _compact_score_result(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    allowed_keys = {
        "score_result_id",
        "score_type",
        "score_value",
        "score_version",
        "rubric_version",
        "contract_id",
        "confidence_level",
        "weight_total",
    }
    return {key: value[key] for key in allowed_keys if key in value}


def _compact_scoring_dimensions(value: object) -> list[dict[str, Any]]:
    dimensions: list[dict[str, Any]] = []
    for dimension in _dict_list(value)[:PREVIOUS_FEEDBACK_DIMENSION_LIMIT]:
        dimensions.append(
            {
                key: dimension[key]
                for key in (
                    "dimension_id",
                    "score_value",
                    "max_score",
                    "weight",
                    "is_critical",
                    "rationale",
                )
                if key in dimension
            }
        )
    return dimensions


def _compact_loss_points(value: object) -> list[dict[str, Any]]:
    loss_points: list[dict[str, Any]] = []
    for point in _dict_list(value)[:PREVIOUS_FEEDBACK_LOSS_POINT_LIMIT]:
        loss_points.append(
            {
                key: point[key]
                for key in (
                    "loss_point_id",
                    "title",
                    "deducted_points",
                    "reason",
                    "critical",
                    "dimension_id",
                    "required_reference_terms",
                    "required_oral_terms",
                )
                if key in point
            }
        )
    return loss_points


def _compact_text(value: object) -> str:
    text = str(value or "").strip()
    if len(text) <= PREVIOUS_FEEDBACK_TEXT_LIMIT:
        return text
    return text[:PREVIOUS_FEEDBACK_TEXT_LIMIT]


def _previous_loss_points_from_payloads(payloads: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(point for payload in payloads for point in _dict_list(payload.get("loss_points")))


def _latest_payload_text(payloads: tuple[dict[str, Any], ...], key: str) -> str:
    for payload in reversed(payloads):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, dict)]


def _structured_scoring_dimensions(answer_text: str) -> list[dict[str, Any]]:
    return [
        {
            "dimension_id": "technical_depth",
            "score_value": _score_by_terms(
                answer_text,
                base=56,
                increment=8,
                terms=("幂等", "失败", "补偿", "指标", "取舍", "状态", "监控", "一致性"),
            ),
            "max_score": 100,
            "weight": 0.5,
            "is_critical": True,
            "rationale": "评估技术链路、失败路径、工程约束和指标验证。",
        },
        {
            "dimension_id": "answer_structure",
            "score_value": _score_by_terms(
                answer_text,
                base=62,
                increment=5,
                terms=("背景", "负责", "先", "结果", "复盘", "说明", "为什么", "方案"),
            ),
            "max_score": 100,
            "weight": 0.3,
            "is_critical": False,
            "rationale": "评估回答是否先结论、再结构化展开。",
        },
        {
            "dimension_id": "evidence_alignment",
            "score_value": _score_by_terms(
                answer_text,
                base=58,
                increment=7,
                terms=("指标", "上线", "业务", "项目", "核心", "接口", "验证", "数据"),
            ),
            "max_score": 100,
            "weight": 0.2,
            "is_critical": False,
            "rationale": "评估回答是否绑定题目证据和可验证结果。",
        },
    ]


def _score_by_terms(answer_text: str, *, base: int, increment: int, terms: tuple[str, ...]) -> int:
    compact_answer = answer_text.lower()
    hits = sum(1 for term in terms if term.lower() in compact_answer)
    return _clamp_score(base + hits * increment)


def _feedback_missing_dimension_ids(answer_text: str) -> set[str]:
    dimensions = _structured_scoring_dimensions(answer_text)
    return {
        str(dimension["dimension_id"])
        for dimension in dimensions
        if int(dimension["score_value"]) < 70
    }


def _structured_loss_points(
    *,
    feedback_id: str,
    answer: PolishAnswer,
    scoring_dimensions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    dimensions_by_id = {str(dimension["dimension_id"]): dimension for dimension in scoring_dimensions}
    loss_points: list[dict[str, Any]] = []
    technical_score = int(dimensions_by_id["technical_depth"]["score_value"])
    if technical_score < 70:
        loss_points.append(
            {
                "loss_point_id": f"{feedback_id}_loss_technical_depth",
                "title": "失败路径和指标验证不足",
                "deducted_points": max(8, 80 - technical_score),
                "reason": "需要补充幂等、失败补偿、状态收敛和指标验证，而不是只描述做了功能。",
                "critical": True,
                "dimension_id": "technical_depth",
                "related_answer_ref": {"resource_type": "answer", "resource_id": answer.answer_id},
                "required_reference_terms": ["失败补偿", "指标"],
                "required_oral_terms": ["失败补偿", "指标"],
            }
        )
    structure_score = int(dimensions_by_id["answer_structure"]["score_value"])
    if structure_score < 70:
        loss_points.append(
            {
                "loss_point_id": f"{feedback_id}_loss_answer_structure",
                "title": "回答结构不足",
                "deducted_points": max(6, 78 - structure_score),
                "reason": "建议先给结论，再按背景、职责、动作、结果和复盘展开。",
                "critical": False,
                "dimension_id": "answer_structure",
                "related_answer_ref": {"resource_type": "answer", "resource_id": answer.answer_id},
                "required_reference_terms": ["背景", "结果"],
                "required_oral_terms": ["先给结论"],
            }
        )
    evidence_score = int(dimensions_by_id["evidence_alignment"]["score_value"])
    if evidence_score < 70:
        loss_points.append(
            {
                "loss_point_id": f"{feedback_id}_loss_evidence_alignment",
                "title": "证据和结果绑定不足",
                "deducted_points": max(6, 76 - evidence_score),
                "reason": "需要把项目证据、业务目标、上线结果或验证指标讲清楚。",
                "critical": False,
                "dimension_id": "evidence_alignment",
                "related_answer_ref": {"resource_type": "answer", "resource_id": answer.answer_id},
                "required_reference_terms": ["验证指标"],
                "required_oral_terms": ["验证指标"],
            }
        )
    return loss_points


def _structured_positive_evidence_points(
    *,
    answer: PolishAnswer,
    answer_text: str,
    scoring_dimensions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    best_dimension = max(scoring_dimensions, key=lambda item: int(item["score_value"]))
    return [
        {
            "point_id": f"{answer.answer_id}_positive_001",
            "title": "回答中已有可复用表达",
            "evidence_excerpt": answer_text[:80],
            "dimension_id": best_dimension["dimension_id"],
            "related_dimension": best_dimension["dimension_id"],
            "evidence_source": "answer_text",
            "location": "answer",
        }
    ]


def _structured_reference_answer(
    *,
    theme_profile: dict[str, object],
    loss_points: list[dict[str, Any]],
    question_text: str,
) -> str:
    required_terms = _required_terms_from_loss_points(loss_points, "required_reference_terms")
    required_text = "、".join(required_terms) if required_terms else "业务目标、技术取舍和验证指标"
    return (
        f"{theme_profile['p7_reference_answer']} 针对题目“{question_text[:80]}”，"
        f"参考答案必须补齐 {required_text}，并按结论、约束、方案、结果复盘的顺序展开。"
    )


def _structured_oral_script(
    *,
    theme_profile: dict[str, object],
    loss_points: list[dict[str, Any]],
) -> str:
    required_terms = _required_terms_from_loss_points(loss_points, "required_oral_terms")
    required_text = "、".join(required_terms) if required_terms else "业务目标和验证指标"
    return (
        f"{theme_profile['oral_script']} 面试现场我会先给结论，再用一句话补充 {required_text}，"
        "最后说明复盘和下一步优化。"
    )


def _required_terms_from_loss_points(loss_points: list[dict[str, Any]], key: str) -> list[str]:
    terms: list[str] = []
    for point in loss_points:
        raw_terms = point.get(key)
        if not isinstance(raw_terms, (list, tuple)):
            continue
        for term in raw_terms:
            text = str(term).strip()
            if text and text not in terms:
                terms.append(text)
    return terms


def _reference_requirements(loss_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": f"{point['loss_point_id']}_reference_requirement",
            "requirement": point["reason"],
            "required_coverage_terms": list(point.get("required_reference_terms", [])),
        }
        for point in loss_points
        if point.get("required_reference_terms")
    ]


def _oral_script_requirements(loss_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": f"{point['loss_point_id']}_oral_requirement",
            "requirement": point["reason"],
            "required_coverage_terms": list(point.get("required_oral_terms", [])),
        }
        for point in loss_points
        if point.get("required_oral_terms")
    ]


def _answer_strengths(answer_text: str) -> list[str]:
    strengths: list[str] = []
    if any(term in answer_text for term in ("背景", "负责", "先")):
        strengths.append("回答具备基础结构意识。")
    if any(term in answer_text for term in ("幂等", "失败", "补偿", "指标", "取舍")):
        strengths.append("回答开始覆盖工程约束或技术取舍。")
    return strengths or ["回答已提供可继续打磨的基础信息。"]


def _answer_risks(loss_points: list[dict[str, Any]]) -> list[str]:
    if any(point.get("critical") for point in loss_points):
        return ["critical loss_points 未修复前，不应进入正式 ScoreResult 或正式 Weakness 写入。"]
    if loss_points:
        return ["仍有非关键缺口，需要继续同题打磨。"]
    return []


def _feedback_candidate_refs(feedback_id: str) -> list[dict[str, str]]:
    return [
        {"resource_type": "weakness_candidate", "resource_id": f"{feedback_id}_weakness_001"},
        {"resource_type": "asset_candidate", "resource_id": f"{feedback_id}_asset_001"},
    ]


def _retry_delta_payload(
    *,
    feedback_input: RetryFeedbackInput,
    score_result: dict[str, Any],
    scoring_dimensions: list[dict[str, Any]],
    loss_points: list[dict[str, Any]],
    p7_reference_answer: str,
    oral_script: str,
) -> dict[str, Any]:
    previous_payload = feedback_input.previous_feedbacks[-1] if feedback_input.previous_feedbacks else {}
    previous_score = _score_value_from_payload(previous_payload)
    previous_dimensions = {
        str(dimension.get("dimension_id")): int(dimension.get("score_value", 0))
        for dimension in _dict_list(previous_payload.get("scoring_dimensions"))
        if dimension.get("dimension_id")
    }
    current_dimensions = {
        str(dimension["dimension_id"]): int(dimension["score_value"])
        for dimension in scoring_dimensions
    }
    dimension_delta = {
        dimension_id: current_score - previous_dimensions.get(dimension_id, 0)
        for dimension_id, current_score in current_dimensions.items()
    }
    current_loss_dimensions = {
        str(point.get("dimension_id"))
        for point in loss_points
        if point.get("dimension_id")
    }
    previous_loss_dimensions = {
        str(point.get("dimension_id"))
        for point in feedback_input.previous_loss_points
        if point.get("dimension_id")
    }
    repeated_loss_points = tuple(
        str(point["loss_point_id"])
        for point in feedback_input.previous_loss_points
        if point.get("dimension_id") in current_loss_dimensions and point.get("loss_point_id")
    )
    improved_points = tuple(
        str(point["loss_point_id"])
        for point in feedback_input.previous_loss_points
        if point.get("dimension_id") not in current_loss_dimensions and point.get("loss_point_id")
    )
    regressed_points = tuple(
        str(point["loss_point_id"])
        for point in loss_points
        if point.get("dimension_id") not in previous_loss_dimensions and point.get("loss_point_id")
    )
    remaining_gaps = tuple(
        str(point["loss_point_id"])
        for point in loss_points
        if point.get("loss_point_id")
    )
    score_delta = int(score_result.get("score_value", 0)) - previous_score
    mastery_status = _retry_mastery_status(
        score_value=int(score_result.get("score_value", 0)),
        score_delta=score_delta,
        loss_points=loss_points,
        repeated_loss_points=repeated_loss_points,
        improved_points=improved_points,
        regressed_points=regressed_points,
    )
    should_generate_next_question = mastery_status == "mastered"
    should_continue_same_question = not should_generate_next_question
    return {
        "score_delta": score_delta,
        "dimension_delta": dimension_delta,
        "improved_points": list(improved_points),
        "remaining_gaps": list(remaining_gaps),
        "repeated_loss_points": list(repeated_loss_points),
        "regressed_points": list(regressed_points),
        "mastery_status": mastery_status,
        "should_continue_same_question": should_continue_same_question,
        "should_generate_next_question": should_generate_next_question,
        "next_retry_focus": _next_retry_focus(loss_points, remaining_gaps),
        "updated_reference_answer": p7_reference_answer,
        "updated_oral_script": oral_script,
        "previous_loss_points": list(feedback_input.previous_loss_points),
    }


def _score_value_from_payload(payload: dict[str, Any]) -> int:
    score_result = payload.get("score_result")
    if isinstance(score_result, dict):
        try:
            return int(score_result.get("score_value", 0))
        except (TypeError, ValueError):
            return 0
    return 0


def _retry_mastery_status(
    *,
    score_value: int,
    score_delta: int,
    loss_points: list[dict[str, Any]],
    repeated_loss_points: tuple[str, ...],
    improved_points: tuple[str, ...],
    regressed_points: tuple[str, ...],
) -> str:
    if regressed_points:
        return "regressed"
    if repeated_loss_points:
        return "stuck"
    if not loss_points and score_value >= 80:
        return "mastered"
    if score_delta > 0 or improved_points:
        return "improving"
    return "stuck"


def _next_retry_focus(
    loss_points: list[dict[str, Any]],
    remaining_gaps: tuple[str, ...],
) -> list[dict[str, Any]]:
    if not loss_points or not remaining_gaps:
        return []
    first_loss = loss_points[0]
    return [
        {
            "focus_area": remaining_gaps[0],
            "priority": 1,
            "related_dimension": first_loss.get("dimension_id"),
        }
    ]


def _build_contract_shaped_feedback_payload(
    *,
    session: PolishSession,
    answer: PolishAnswer,
    feedback_id: str,
    ai_task_id: str,
    score_result_id: str,
    created_at,
) -> dict[str, Any]:
    strategy = _session_theme_strategy(session)
    answer_text = _or_fallback_text(answer.answer_text, UNNAMED_ANSWER_TEXT)
    low_confidence_flags = _feedback_low_confidence_flags(answer_text)
    score_value = 58 if low_confidence_flags else 72
    explicit_score, implicit_score = _theme_scores(strategy, score_value)
    deducted_points = 100 - score_value
    primary_action = "provide_more_answer_detail" if low_confidence_flags else "continue_same_question"
    theme_profile = _theme_feedback_profile(strategy)
    feedback_text = (
        f"polish_answer / {strategy.label} 评分 {score_value}/100："
        f"{theme_profile['summary']}"
    )
    loss_points = [
        {
            "loss_point_id": f"{feedback_id}_loss_001",
            "title": theme_profile["primary_loss_title"],
            "deducted_points": min(16, deducted_points),
            "reason": theme_profile["primary_loss_reason"],
            "answer_excerpt": answer_text[:160],
            "related_answer_ref": {"resource_type": "answer", "resource_id": answer.answer_id},
        },
        {
            "loss_point_id": f"{feedback_id}_loss_002",
            "title": theme_profile["secondary_loss_title"],
            "deducted_points": max(deducted_points - 16, 0),
            "reason": theme_profile["secondary_loss_reason"],
            "related_answer_ref": {"resource_type": "answer", "resource_id": answer.answer_id},
        },
    ]
    return {
        "schema_id": "polish_feedback_payload_v1",
        "schema_version": "1.0",
        "contract_id": "P-POLISH-005",
        "contract_ids": list(FEEDBACK_CONTRACT_IDS),
        "status": FEEDBACK_STATUS_GENERATED,
        "feedback_id": feedback_id,
        "ai_task_id": ai_task_id,
        "polish_theme": strategy.theme,
        "polish_theme_label": strategy.label,
        "explicit_weight": strategy.explicit_weight,
        "implicit_weight": strategy.implicit_weight,
        "weight_explanation": (
            f"本轮按显性技术 {strategy.explicit_weight}%、隐性表达 {strategy.implicit_weight}% 综合打磨；"
            "显性分看技术链路和工程约束，隐性分看表达结构和 owner 视角。"
        ),
        "interview_intent": strategy.question_intent,
        "explicit_score": explicit_score,
        "implicit_score": implicit_score,
        "technical_gaps": list(theme_profile["technical_gaps"]),
        "communication_gaps": list(theme_profile["communication_gaps"]),
        "p7_reference_answer": theme_profile["p7_reference_answer"],
        "oral_script": theme_profile["oral_script"],
        "next_training_suggestions": list(theme_profile["next_training_suggestions"]),
        "polish_session_ref": {"resource_type": "polish_session", "resource_id": session.session_id},
        "question_ref": {"resource_type": "question", "resource_id": answer.question_id},
        "answer_ref": {"resource_type": "answer", "resource_id": answer.answer_id},
        "feedback_text": feedback_text,
        "feedback_summary": feedback_text,
        "score_result": {
            "score_result_id": score_result_id,
            "score_type": str(ScoreType.POLISH_ANSWER),
            "score_value": score_value,
            "score_version": f"polish_answer.{strategy.theme}.runtime_fake.v1",
            "rubric_version": "polish_round_score.v1",
            "contract_id": "P-POLISH-004",
            "confidence_level": "low" if low_confidence_flags else "medium",
        },
        "score_result_ref": {"resource_type": "score_result", "resource_id": score_result_id},
        "loss_points": loss_points,
        "reference_answer": {
            "contract_id": "P-POLISH-006",
            "summary": theme_profile["reference_summary"],
            "outline": list(theme_profile["reference_outline"]),
        },
        "knowledge_points": [
            {
                "title": theme_profile["knowledge_title"],
                "explanation": theme_profile["knowledge_explanation"],
            }
        ],
        "technical_principles": [
            {
                "title": theme_profile["principle_title"],
                "explanation": theme_profile["principle_explanation"],
            }
        ],
        "next_recommended_actions": _feedback_next_actions(primary_action),
        "candidate_refs": [
            {"resource_type": "weakness_candidate", "resource_id": f"{feedback_id}_weakness_001"},
            {"resource_type": "asset_candidate", "resource_id": f"{feedback_id}_asset_001"},
        ],
        "validation_result_ref": {"resource_type": "validation_result", "resource_id": f"{feedback_id}_validation"},
        "trace_refs": [
            {
                "trace_ref_id": answer.answer_id,
                "trace_type": "answer",
                "created_at": answer.created_at.isoformat(),
                "redaction_boundary": "none",
            },
            {
                "trace_ref_id": feedback_id,
                "trace_type": "feedback",
                "created_at": created_at.isoformat(),
                "redaction_boundary": "none",
            },
            {
                "trace_ref_id": score_result_id,
                "trace_type": "score_result",
                "created_at": created_at.isoformat(),
                "redaction_boundary": "none",
            },
        ],
        "low_confidence_flags": low_confidence_flags,
        "user_confirmation_required": False,
        "legacy_compatibility": {"feedback_text": feedback_text},
    }


def _session_theme_strategy(session: PolishSession) -> PolishThemeStrategy:
    try:
        return resolve_polish_theme_strategy(session.polish_theme)
    except ValueError:
        return resolve_polish_theme_strategy(None)


def _progress_artifacts_with_theme(
    artifacts: dict[str, Any],
    strategy: PolishThemeStrategy,
) -> dict[str, Any]:
    return {
        **artifacts,
        "progress_tree_plan": _progress_payload_with_theme(artifacts.get("progress_tree_plan"), strategy),
        "progress_tree_state": _progress_payload_with_theme(artifacts.get("progress_tree_state"), strategy),
    }


def _progress_payload_with_theme(payload: object, strategy: PolishThemeStrategy) -> dict[str, Any]:
    result = dict(payload) if isinstance(payload, dict) else {}
    result["polish_theme"] = strategy.theme
    result["polish_theme_label"] = strategy.label
    result["explicit_weight"] = strategy.explicit_weight
    result["implicit_weight"] = strategy.implicit_weight
    return result


def _theme_scores(strategy: PolishThemeStrategy, score_value: int) -> tuple[int, int]:
    if strategy.theme == "technical":
        return score_value, _clamp_score(score_value - 8)
    if strategy.theme == "communication":
        return _clamp_score(score_value - 10), score_value
    return _clamp_score(score_value - 2), _clamp_score(score_value + 2)


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _theme_feedback_profile(strategy: PolishThemeStrategy) -> dict[str, object]:
    if strategy.theme == "technical":
        return {
            "summary": "重点看技术链路、异常路径和指标验证；当前回答需要把状态流转、幂等和补偿方案讲实。",
            "primary_loss_title": "工程链路拆解不足",
            "primary_loss_reason": "需要补充状态机、幂等键、失败路径、对账补偿和性能指标，而不是只描述做了功能。",
            "secondary_loss_title": "技术 trade-off 与指标不足",
            "secondary_loss_reason": "建议说明限流、降级、成本控制、可观测性和上线验证指标。",
            "technical_gaps": ["状态机边界不够清晰", "幂等和失败补偿需要具体设计", "缺少性能、成本或可观测性指标"],
            "communication_gaps": ["技术结论需要先给 owner 判断，再展开细节"],
            "p7_reference_answer": "从 owner 视角先定义链路状态机，再说明幂等键、重试收敛、对账补偿、降级限流和观测指标，最后给出成本上限与 trade-off。",
            "oral_script": "我会先说这个链路最怕部分成功，因此我把状态机和幂等键作为收敛核心，再讲失败路径、补偿任务和监控指标。",
            "next_training_suggestions": ["下一轮只讲状态机和幂等设计", "补一版失败路径、对账和补偿的 owner 方案"],
            "reference_summary": "按链路完整性、状态机、幂等、失败兜底、指标验证和 trade-off 组织答案。",
            "reference_outline": ["链路与状态机", "幂等和失败路径", "对账补偿与降级", "性能/成本/可观测性指标"],
            "knowledge_title": "工程一致性表达",
            "knowledge_explanation": "技术打磨需要把状态、失败收敛和验证指标串成可追问的工程闭环。",
            "principle_title": "异常收敛优先",
            "principle_explanation": "复杂链路先保证状态可判定、操作可重试、结果可对账，再谈性能和成本优化。",
        }
    if strategy.theme == "communication":
        return {
            "summary": "重点看 STAR、背景压缩、职责边界和复盘表达；当前回答需要更像面试现场的一分钟版本。",
            "primary_loss_title": "表达结构不够清晰",
            "primary_loss_reason": "建议用 STAR 组织，30 秒压缩背景，突出个人职责边界和关键行动。",
            "secondary_loss_title": "复盘收束不足",
            "secondary_loss_reason": "需要用指标、取舍和复盘总结收束，避免流水账。",
            "technical_gaps": ["技术细节需要挑一个关键取舍作为表达支点"],
            "communication_gaps": ["背景压缩不够", "个人职责边界不够明确", "复盘总结缺少口语化收束"],
            "p7_reference_answer": "先用一句话给结论，再按 STAR 讲背景、任务、个人行动和结果，用一个技术取舍支撑能力深度。",
            "oral_script": "我先用 30 秒交代背景和目标，然后讲我负责的动作，最后用指标和复盘说明这件事为什么有效。",
            "next_training_suggestions": ["下一轮限定 90 秒回答", "先写出 STAR 四句骨架再口述"],
            "reference_summary": "按 STAR、背景压缩、个人职责、关键动作、指标结果和复盘总结组织答案。",
            "reference_outline": ["Situation 背景压缩", "Task 职责边界", "Action 关键动作", "Result 指标与复盘"],
            "knowledge_title": "STAR + 口语化表达",
            "knowledge_explanation": "表达打磨要让面试官快速听到背景、职责、动作、结果和复盘，而不是堆项目细节。",
            "principle_title": "先结论后展开",
            "principle_explanation": "面试表达先给判断和贡献边界，再展开证据，最后用指标收束。",
        }
    return {
        "summary": "同时看技术深度和表达结构；当前回答需要补足 owner 视角、失败兜底和结构化复盘。",
        "primary_loss_title": "技术链路与表达结构未完全合流",
        "primary_loss_reason": "需要把方案链路、失败兜底、技术取舍放进背景、约束、方案、指标、复盘的表达顺序里。",
        "secondary_loss_title": "显性/隐性权重感不足",
        "secondary_loss_reason": "建议明确哪些内容支撑显性技术分，哪些表达方式支撑隐性表达分。",
        "technical_gaps": ["失败兜底和技术取舍还不够具体", "owner 视角下的指标验证需要加强"],
        "communication_gaps": ["表达结构需要显式分层", "复盘总结可以更有收束感"],
        "p7_reference_answer": "从 owner 视角讲背景和约束，展开方案链路、失败兜底、技术取舍和指标复盘，同时说明为什么这套方案能支撑业务目标。",
        "oral_script": "这题我会按背景、约束、方案、指标、复盘来讲：先说业务目标，再说我作为 owner 如何处理链路和失败兜底。",
        "next_training_suggestions": ["下一轮按显性技术 60%、隐性表达 40% 再答", "把技术取舍压进 2 分钟口语化版本"],
        "reference_summary": "按 owner 视角同时覆盖方案链路、失败兜底、技术取舍、指标和复盘。",
        "reference_outline": ["背景与约束", "owner 方案链路", "失败兜底与取舍", "指标结果与复盘"],
        "knowledge_title": "技术深度 + 表达结构",
        "knowledge_explanation": "混合主题要求显性技术内容和隐性表达质量同时在线。",
        "principle_title": "权重驱动回答取舍",
        "principle_explanation": "先满足技术链路的可信度，再用清晰结构降低面试官理解成本。",
    }


def _feedback_next_actions(primary_action: str) -> list[str]:
    actions: list[str] = []
    for action in (primary_action, *FEEDBACK_NEXT_RECOMMENDED_ACTIONS):
        if action not in actions:
            actions.append(action)
    return actions


def _feedback_low_confidence_flags(answer_text: str) -> list[dict[str, str]]:
    if len(answer_text.strip()) >= 18:
        return []
    return [
        {
            "flag_id": "answer_detail_insufficient",
            "reason": "answer_too_short_for_full_scoring",
            "impact_scope": "score_result, loss_points, reference_answer",
            "recommended_action": "provide_more_answer_detail",
        }
    ]


def _validate_contract_shaped_feedback_payload(payload: dict[str, Any]) -> DomainError | None:
    required_keys = {
        "contract_id",
        "status",
        "loss_points",
        "reference_answer",
        "knowledge_points",
        "technical_principles",
        "next_recommended_actions",
        "candidate_refs",
        "validation_result_ref",
        "trace_refs",
        "low_confidence_flags",
        "polish_theme",
        "polish_theme_label",
        "explicit_weight",
        "implicit_weight",
        "weight_explanation",
        "interview_intent",
        "explicit_score",
        "implicit_score",
        "technical_gaps",
        "communication_gaps",
        "p7_reference_answer",
        "oral_script",
        "next_training_suggestions",
    }
    missing = sorted(key for key in required_keys if key not in payload)
    if missing:
        return DomainError(
            code="validation_failed",
            message="Feedback payload is missing required contract fields",
            details={"fields": missing},
        )
    if not isinstance(payload.get("loss_points"), list):
        return DomainError(
            code="validation_failed",
            message="Feedback payload loss_points must be a list",
            details={"field": "loss_points"},
        )
    actions = payload.get("next_recommended_actions")
    if not isinstance(actions, list) or not all(isinstance(action, str) for action in actions):
        return DomainError(
            code="validation_failed",
            message="Feedback payload next_recommended_actions must be contract enum strings",
            details={"field": "next_recommended_actions"},
        )
    return None


def _serialize_feedback_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _feedback_payload_from_summary(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _feedback_text_from_summary(value: str | None) -> str | None:
    payload = _feedback_payload_from_summary(value)
    if payload is None:
        return value
    legacy = payload.get("legacy_compatibility")
    if isinstance(legacy, dict) and legacy.get("feedback_text"):
        return str(legacy["feedback_text"])
    for key in ("feedback_text", "feedback_summary"):
        text = payload.get(key)
        if isinstance(text, str) and text.strip():
            return text
    return value


def _should_regenerate_progress_tree(detail: PolishSessionDetail) -> bool:
    if not _has_valid_progress_tree_plan(detail.progress_tree_plan):
        return True
    return detail.progress_tree_status in {
        PROGRESS_TREE_STATUS_FAILED,
        PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
    }


def _has_valid_progress_tree_plan(plan: dict[str, object]) -> bool:
    return plan.get("status") == PROGRESS_TREE_STATUS_READY and bool(plan.get("nodes"))


def _custom_topic_summary(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = " ".join(value.split())
    return stripped[:240] if stripped else None


def _to_session_answer_detail(
    *,
    answer: PolishAnswer,
    feedback: PolishFeedback | None,
) -> PolishSessionAnswerDetail:
    feedback_payload = _feedback_payload_from_summary(feedback.feedback_summary) if feedback is not None else None
    feedback_text = _feedback_text_from_summary(feedback.feedback_summary) if feedback is not None else None
    return PolishSessionAnswerDetail(
        answer_id=answer.answer_id,
        answer_round=answer.answer_round,
        answer_text=_or_fallback_text(answer.answer_text, UNNAMED_ANSWER_TEXT),
        answer_created_at=answer.created_at,
        feedback_text=_or_fallback_text(feedback_text, UNNAMED_FEEDBACK_TEXT),
        feedback_id=feedback.feedback_id if feedback is not None else None,
        score_result_id=feedback.score_result_id if feedback is not None else None,
        feedback_created_at=feedback.created_at if feedback is not None else None,
        feedback_payload=feedback_payload,
    )


def _latest_feedback_by_answer_id(
    feedbacks: tuple[PolishFeedback, ...],
) -> dict[str, PolishFeedback]:
    """
    Keep only the latest feedback for each answer_id, using:
    1) created_at
    2) feedback_id
    """
    latest_by_answer_id: dict[str, PolishFeedback] = {}
    for feedback in feedbacks:
        current = latest_by_answer_id.get(feedback.answer_id)
        if (
            current is None
            or (feedback.created_at, feedback.feedback_id) > (current.created_at, current.feedback_id)
        ):
            latest_by_answer_id[feedback.answer_id] = feedback
    return latest_by_answer_id


def _or_fallback_text(value: str | None, fallback: str) -> str:
    if value is None:
        return fallback
    stripped = value.strip()
    return stripped if stripped else fallback
