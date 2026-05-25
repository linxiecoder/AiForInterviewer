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
from app.application.polish.feedback_reserved import build_reserved_feedback_artifacts
from app.application.polish.ports import PolishRepository
from app.application.polish.question_generation_service import QuestionGenerationResult, QuestionGenerationService
from app.application.polish.question_metadata import empty_question_metadata, normalize_question_metadata
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
)
from app.application.polish.queries import GetPolishSessionQuery, ListPolishSessionsQuery, ListPolishTopicsQuery
from app.application.resumes.ports import ResumeRepository
from app.domain.bindings.ports import BindingRepository
from app.domain.jobs.entities import Job, JobVersion
from app.domain.jobs.ports import JobRepository
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.domain.shared.refs import ResourceRef, TraceRef


SESSION_STATUS_RUNNING = "running"
SESSION_STATUS_ENDED = "ended"
QUESTION_STATUS_GENERATED = "generated"
ANSWER_STATUS_SAVED = "saved"
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
        progress_tree_service: PolishProgressTreeLlmService | None = None,
        ai_orchestration_facade: AiOrchestrationFacade | None = None,
    ) -> None:
        self._polish_repository = polish_repository
        self._binding_repository = binding_repository
        self._resume_repository = resume_repository
        self._job_repository = job_repository
        self._job_match_repository = job_match_repository
        self._progress_tree_service = progress_tree_service or PolishProgressTreeLlmService(None)
        self._question_generation_service = QuestionGenerationService()
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
        if requested_progress_node_ref is None:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="progress_node_ref is required",
                    details={"field": "progress_node_ref"},
                )
            )
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
        question_generation_result = self._question_generation_service.generate(
            session=session,
            context=progress_context,
            plan=detail.progress_tree_plan,
            state=detail.progress_tree_state,
            requested_ref=requested_progress_node_ref,
        )
        if not question_generation_result.succeeded or question_generation_result.draft is None:
            task = _polish_question_generation_validation_failed_task_status(
                task_id=task_id,
                result=question_generation_result,
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
        question_draft = question_generation_result.draft
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
        focus_seed = "|".join(
            (
                _question_generation_mode(command),
                question_draft.progress_node_ref or requested_progress_node_ref or "",
                question_draft.question_pattern or "",
                command.parent_question_id or "",
                command.parent_answer_id or "",
                command.parent_feedback_id or "",
                ",".join(command.exclude_question_refs),
                ",".join(completed_focus_refs),
            )
        )
        focus_key = f"focus_{sha256(focus_seed.encode('utf-8')).hexdigest()[:12]}"
        if not question_metadata.get("focus_key"):
            question_metadata["focus_key"] = focus_key
        if not question_metadata.get("focus_dimension"):
            question_metadata["focus_dimension"] = question_draft.question_pattern or "phase1_blueprint"
        if not question_metadata.get("template_signature"):
            question_metadata["template_signature"] = f"tpl:phase1_blueprint:{focus_key}"
        if not question_metadata.get("blueprint_signature"):
            question_metadata["blueprint_signature"] = f"bp:{sha256(focus_seed.encode('utf-8')).hexdigest()[:16]}"
        question_metadata["similarity_checked"] = True
        question_metadata["max_similarity_in_same_category"] = 0.0
        if _question_generation_mode(command) == QUESTION_GENERATION_MODE_FOLLOW_UP:
            if not question_metadata.get("follow_up_reason"):
                question_metadata["follow_up_reason"] = "phase1_reserved_follow_up"
            if not question_metadata.get("follow_up_target_dimension"):
                question_metadata["follow_up_target_dimension"] = question_metadata["focus_dimension"]
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

        now = utc_now()
        task_id = generate_resource_id(ResourceIdPrefix.TASK)
        feedback_id = generate_resource_id(ResourceIdPrefix.TRACE)
        artifacts = build_reserved_feedback_artifacts(
            session=session,
            question=question,
            answer=answer,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            task_id=task_id,
            feedback_id=feedback_id,
            created_at=now,
        )
        self._polish_repository.add_feedback(artifacts.feedback)
        self._polish_repository.add_task(
            artifacts.task,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            target_ref_id=command.answer_id,
        )
        return ApplicationResult(value=artifacts.task)

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


def _polish_question_generation_validation_failed_task_status(
    *,
    task_id: str,
    result: QuestionGenerationResult,
    requested_progress_node_ref: str | None,
    created_at: Any,
) -> PolishTaskStatus:
    progress_node_ref = result.progress_node_ref or requested_progress_node_ref
    candidate_refs = []
    if progress_node_ref:
        candidate_refs.append(ResourceRef(resource_type="progress_node", resource_id=progress_node_ref))
    candidate_refs.extend(ResourceRef(resource_type="evidence", resource_id=ref) for ref in result.evidence_refs)
    return PolishTaskStatus(
        ai_task_id=task_id,
        task_type="polish_question_generation",
        status=AiTaskStatus.VALIDATION_FAILED,
        contract_ids=QUESTION_CONTRACT_IDS,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=task_id, trace_type="validation_result", created_at=created_at),
        user_visible_status="题目 grounding 校验未通过",
        candidate_refs=tuple(candidate_refs),
        validation_errors=result.validation_errors,
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


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, dict)]


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
