"""Polish use cases."""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from typing import Any

from app.application.common.logging import LogUtil
from app.application.common.result import ApplicationResult
from app.application.assets.ports import AssetRepository
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentTaskStatusRef,
    GraphDisabledError,
    RuntimeConflictError,
    RuntimePolicyError,
    RuntimeValidationError,
    classify_agent_runtime_status,
)
from app.application.ai_runtime.facade import AiOrchestrationFacade
from app.application.ai_runtime.handoff import AgentPersistenceHandoff, build_question_result_write_plan
from app.application.job_match.entities import JobMatchAnalysis
from app.application.job_match.ports import JobMatchRepository
from app.application.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.application.polish.canonical_evidence import CanonicalEvidenceService
from app.application.polish.commands import (
    CompletePolishQuestionCommand,
    CreatePolishAnswerCommand,
    CreatePolishFeedbackTaskCommand,
    CreatePolishQuestionTaskCommand,
    CreatePolishSessionCommand,
    EndPolishSessionCommand,
    GeneratePolishSessionReportCommand,
    GenerateInitialPolishProgressTreeCommand,
    RefreshPolishProgressTreeStateCommand,
    SoftDeletePolishSessionCommand,
)
from app.application.polish.answer_application_service import (
    AnswerSubmissionBoundaryBuilder,
    PolishAnswerApplicationService,
)
from app.application.polish.entities import (
    PolishAnswer,
    PolishFeedback,
    PolishQuestion,
    PolishQuestionDraft,
    PolishSessionAnswerDetail,
    PolishSessionDetail,
    PolishSessionTurn,
    PolishSession,
    PolishTaskStatus,
    PolishTopic,
)
from app.application.polish.feedback_application_service import PolishFeedbackApplicationService
from app.application.polish.agents.question import (
    build_direct_question_agent_run_id,
    build_question_candidate_validation_task,
    run_question_planned_workflow,
)
from app.application.polish.feedback_generation_service import (
    FeedbackGenerationService,
)
from app.application.polish.next_question_authorization import (
    build_next_question_execution_grant,
    consume_next_question_execution_grant,
    validate_consumed_next_question_execution_grant_snapshot,
    validate_feedback_next_question_authorization_payload,
    validate_next_question_intent,
)
from app.application.polish.ports import PolishRepository
from app.application.polish.progress_application_service import PolishProgressApplicationService
from app.application.polish.question_generation_policy import (
    DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY,
    QuestionGenerationPolicyResolutionContext,
    QuestionGenerationRuntimePolicy,
    QuestionGenerationRuntimePolicyResolver,
    resolve_question_generation_runtime_policy,
    with_question_generation_policy_resolution,
)
from app.application.polish.question_application_service import PolishQuestionApplicationService
from app.application.polish.question_generation_service import QuestionGenerationResult, QuestionGenerationService
from app.application.polish.question_metadata import (
    empty_question_metadata,
    merge_follow_up_completed_focus_refs,
    next_question_execution_grant_snapshot_to_metadata,
    normalize_question_metadata,
    sync_follow_up_completed_focus_refs,
)
from app.application.polish.report_application_service import PolishReportApplicationService
from app.application.polish.session_application_service import POLISH_TOPICS, PolishSessionApplicationService
from app.application.polish.theme_strategy import PolishThemeStrategy, resolve_polish_theme_strategy
from app.application.polish.progress_context import build_polish_progress_context
from app.application.polish.progress_evidence import select_progress_tree_evidence_chunks
from app.application.polish.progress_prompts import PROGRESS_TREE_STATE_REFRESH_PROMPT_CONTRACT
from app.application.polish.progress_tree import (
    PROGRESS_TREE_STATUS_FAILED,
    PROGRESS_TREE_STATUS_GENERATING,
    PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
    PROGRESS_TREE_STATUS_PENDING,
    PROGRESS_TREE_STATUS_READY,
    PROGRESS_TREE_STATUS_REFRESH_FAILED,
    PolishProgressTreeLlmService,
)
from app.application.polish.queries import GetPolishSessionQuery, ListPolishSessionsQuery, ListPolishTopicsQuery
from app.application.resumes.ports import ResumeRepository
from app.usecases.polish import PolishApplyFeedbackUseCase
from app.domain.bindings.ports import BindingRepository
from app.domain.jobs.entities import Job, JobVersion
from app.domain.jobs.ports import JobRepository
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.polish.policies.follow_up_coverage_policy import (
    FollowUpAssetConflict,
    FollowUpCoverageInput,
    FollowUpCoveragePolicy,
)
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.domain.shared.refs import ResourceRef, TraceRef


SESSION_STATUS_RUNNING = "running"
SESSION_STATUS_ENDED = "ended"
SESSION_STATUS_DELETED = "deleted"
QUESTION_STATUS_GENERATED = "generated"
QUESTION_GENERATION_MODE_NEW = "new_question"
QUESTION_GENERATION_MODE_FOLLOW_UP = "follow_up"
QUESTION_GENERATION_MODE_REGENERATE_CURRENT_NODE = "regenerate_current_node"
QUESTION_GENERATION_MODES = {
    QUESTION_GENERATION_MODE_NEW,
    QUESTION_GENERATION_MODE_FOLLOW_UP,
    QUESTION_GENERATION_MODE_REGENERATE_CURRENT_NODE,
}
QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT = "feedback_next_question_intent"

UNNAMED_JOB_TITLE = "未命名岗位"
UNNAMED_RESUME_TITLE = "未命名简历"
UNNAMED_COMPANY_TITLE = "未命名公司"
UNNAMED_QUESTION_TEXT = "题干缺失"
UNNAMED_ANSWER_TEXT = "暂无回答"
UNNAMED_FEEDBACK_TEXT = "本轮反馈尚未生成"


class _PolishUseCaseOperations:
    def __init__(
        self,
        *,
        polish_repository: PolishRepository,
        binding_repository: BindingRepository,
        resume_repository: ResumeRepository,
        job_repository: JobRepository,
        job_match_repository: JobMatchRepository | None = None,
        asset_repository: AssetRepository | None = None,
        canonical_evidence_service: CanonicalEvidenceService | None = None,
        progress_tree_service: PolishProgressTreeLlmService | None = None,
        ai_orchestration_facade: AiOrchestrationFacade | None = None,
        question_generation_service: QuestionGenerationService | None = None,
        question_generation_policy: QuestionGenerationRuntimePolicy | None = None,
        question_generation_policy_resolver: QuestionGenerationRuntimePolicyResolver | None = None,
        feedback_generation_service: FeedbackGenerationService | None = None,
    ) -> None:
        self._polish_repository = polish_repository
        self._binding_repository = binding_repository
        self._resume_repository = resume_repository
        self._job_repository = job_repository
        self._job_match_repository = job_match_repository
        self._asset_repository = asset_repository
        self._canonical_evidence_service = (
            canonical_evidence_service
            if canonical_evidence_service is not None
            else (CanonicalEvidenceService(asset_repository) if asset_repository is not None else None)
        )
        self._progress_tree_service = progress_tree_service or PolishProgressTreeLlmService(None)
        self._question_generation_policy = (
            question_generation_policy or DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY
        )
        self._question_generation_service = question_generation_service or QuestionGenerationService(
            runtime_policy=self._question_generation_policy
        )
        self._question_generation_policy_resolver = (
            question_generation_policy_resolver or resolve_question_generation_runtime_policy
        )
        self._feedback_generation_service = feedback_generation_service or FeedbackGenerationService()
        self._ai_orchestration_facade = ai_orchestration_facade
        self._answer_submission_boundary_builder = AnswerSubmissionBoundaryBuilder()
        self._answer_submission_records: dict[tuple[str, str, str, str], tuple[str, str]] = {}

    def _resolve_question_generation_policy(
        self,
        *,
        command: CreatePolishQuestionTaskCommand,
        session: PolishSession,
        requested_progress_node_ref: str | None,
    ) -> QuestionGenerationRuntimePolicy:
        context = QuestionGenerationPolicyResolutionContext(
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            tenant_id=command.owner_id,
            session_id=command.session_id,
            job_id=session.job_id,
            job_version_id=session.job_version_id,
            generation_mode=_question_generation_mode(command),
            requested_progress_node_ref=requested_progress_node_ref,
            selected_progress_node_ref=command.selected_progress_node_ref,
        )
        resolved = self._question_generation_policy_resolver(context, self._question_generation_policy)
        if not isinstance(resolved, QuestionGenerationRuntimePolicy):
            raise RuntimePolicyError("question generation policy resolver returned invalid policy")
        if not resolved.resolution_context:
            resolved = with_question_generation_policy_resolution(resolved, context)
        return resolved

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
        progress_artifacts = _pending_progress_artifacts(session.session_id, theme_strategy)
        session = replace(
            session,
            progress_tree_status=progress_artifacts["status"],
            progress_percent=progress_artifacts["progress_percent"],
            progress_tree_plan=progress_artifacts["progress_tree_plan"],
            progress_tree_state=progress_artifacts["progress_tree_state"],
        )
        self._polish_repository.add_session(session)
        return ApplicationResult(value=session)

    def generate_initial_progress_tree(
        self,
        command: GenerateInitialPolishProgressTreeCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )

        detail = self._build_session_detail(owner_id=command.owner_id, session=session)
        if detail.progress_tree_status == PROGRESS_TREE_STATUS_READY and _has_valid_progress_tree_plan(
            detail.progress_tree_plan
        ):
            return ApplicationResult(value=detail)
        if detail.progress_tree_status == PROGRESS_TREE_STATUS_GENERATING:
            return ApplicationResult(value=detail)

        theme_strategy = _session_theme_strategy(session)
        generating_artifacts = _generating_progress_artifacts(detail, theme_strategy)
        generating_session = replace(
            session,
            updated_at=utc_now(),
            progress_tree_status=generating_artifacts["status"],
            progress_percent=generating_artifacts["progress_percent"],
            progress_tree_plan=generating_artifacts["progress_tree_plan"],
            progress_tree_state=generating_artifacts["progress_tree_state"],
        )
        self._polish_repository.update_progress_tree(generating_session)

        try:
            progress_artifacts = self._progress_tree_service.generate_initial(detail.progress_context)
        except Exception as exc:
            progress_artifacts = _failed_initial_generation_artifacts(
                detail,
                reason=_initial_progress_generation_exception_reason(exc),
            )
        progress_artifacts = _progress_artifacts_with_theme(progress_artifacts, theme_strategy)
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

    def get_session(self, query: GetPolishSessionQuery) -> ApplicationResult[PolishSessionDetail]:
        session = self._polish_repository.get_session(query.owner_id, query.session_id)
        if session is None or session.status == SESSION_STATUS_DELETED:
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
        detail = self._build_session_detail(owner_id=command.owner_id, session=session)
        feedbacks = self._polish_repository.list_feedbacks_for_session(
            owner_id=command.owner_id,
            session_id=command.session_id,
        )
        if _feedback_next_question_flow_active(command, feedbacks=feedbacks):
            feedback_gate_result = _authorize_feedback_next_question_execution(
                command=command,
                detail=detail,
                feedbacks=feedbacks,
                latest_feedback_for_answer=self._polish_repository.get_latest_feedback_for_answer,
            )
            if isinstance(feedback_gate_result, DomainError):
                return ApplicationResult(error=feedback_gate_result)
            command = feedback_gate_result
            trusted_execution_error = _feedback_next_question_trusted_execution_error(command)
            if trusted_execution_error is not None:
                return ApplicationResult(error=trusted_execution_error)
        request_error = _validate_question_generation_request(command)
        if request_error is not None:
            return ApplicationResult(error=request_error)
        requested_progress_node_ref = _question_generation_requested_ref(command)
        if requested_progress_node_ref is None:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="progress_node_ref is required",
                    details={"field": "progress_node_ref"},
                )
            )
        if _question_generation_mode(command) == QUESTION_GENERATION_MODE_REGENERATE_CURRENT_NODE:
            plan_progress_node_refs = _plan_progress_node_refs(detail.progress_tree_plan)
            if requested_progress_node_ref not in plan_progress_node_refs:
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="target progress node could not be located",
                        details={"field": "selected_progress_node_ref", "progress_node_ref": requested_progress_node_ref},
                    )
                )
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
        try:
            runtime_policy = self._resolve_question_generation_policy(
                command=command,
                session=session,
                requested_progress_node_ref=requested_progress_node_ref,
            )
        except RuntimePolicyError:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Polish question runtime policy resolution failed",
                    details={"reason": "runtime_policy_resolution_failed"},
                )
            )
        completed_focus_refs = _combined_completed_focus_refs(
            command.completed_focus_refs,
            detail.progress_tree_state,
            progress_node_ref=requested_progress_node_ref,
        )
        follow_up_context: dict[str, Any] | None = None
        if _question_generation_mode(command) == QUESTION_GENERATION_MODE_FOLLOW_UP:
            resolved_follow_up_context = _build_follow_up_generation_context(
                command=command,
                detail=detail,
                completed_focus_refs=completed_focus_refs,
            )
            if isinstance(resolved_follow_up_context, DomainError):
                return ApplicationResult(error=resolved_follow_up_context)
            follow_up_context = resolved_follow_up_context
            completed_focus_refs = merge_follow_up_completed_focus_refs(
                follow_up_context,
                completed_focus_refs,
            )
            sync_follow_up_completed_focus_refs(follow_up_context, completed_focus_refs)
        progress_context = _progress_context_with_completed_focus_refs(
            detail.progress_context,
            completed_focus_refs,
        )
        if follow_up_context is not None and follow_up_context.get("completion_status") == "all_focus_completed":
            task_id = generate_resource_id(ResourceIdPrefix.TASK)
            task = _follow_up_completed_task_status(
                task_id=task_id,
                runtime_policy=runtime_policy,
                requested_progress_node_ref=requested_progress_node_ref,
                focus_key=_clean_question_request_text(follow_up_context.get("focus_key")) or "focus_follow_up_completed",
                created_at=now,
            )
            self._polish_repository.add_task(
                task,
                owner_id=command.owner_id,
                actor_id=command.actor_id,
                target_ref_id=command.session_id,
            )
            return ApplicationResult(value=task)
        graph_fallback_reason: str | None = None
        if self._ai_orchestration_facade is not None:
            stable_idempotency_key = _stable_polish_question_generation_idempotency_key(
                owner_id=command.owner_id,
                session_id=command.session_id,
                requested_progress_node_ref=requested_progress_node_ref,
                completed_focus_refs=completed_focus_refs,
            )
            try:
                LogUtil.agent_runtime_step(
                    task_type=runtime_policy.task_type,
                    phase="graph_start",
                    status="started",
                    input_ref=requested_progress_node_ref,
                )
                graph_status = self._ai_orchestration_facade.start_polish_question_generation(
                    owner_id=command.owner_id,
                    actor_id=command.actor_id,
                    session_ref=command.session_id,
                    progress_node_refs=(requested_progress_node_ref,) if requested_progress_node_ref else (),
                    completed_focus_refs=completed_focus_refs,
                    idempotency_key=stable_idempotency_key,
                    context_snapshot=_polish_question_graph_context_snapshot(
                        command=command,
                        detail=detail,
                        progress_context=progress_context,
                        requested_progress_node_ref=requested_progress_node_ref,
                        completed_focus_refs=completed_focus_refs,
                        follow_up_context=follow_up_context,
                        runtime_policy=runtime_policy,
                    ),
                )
            except GraphDisabledError:
                graph_fallback_reason = "graph_disabled"
                LogUtil.agent_runtime_step(
                    task_type=runtime_policy.task_type,
                    phase="graph_start",
                    status="fallback",
                    input_ref=requested_progress_node_ref,
                    error_type="GraphDisabledError",
                )
                graph_status = None
            except RuntimeValidationError:
                LogUtil.agent_runtime_step(
                    task_type=runtime_policy.task_type,
                    phase="graph_start",
                    status="failed",
                    input_ref=requested_progress_node_ref,
                    error_type="RuntimeValidationError",
                )
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="Polish question graph request is invalid",
                        details={"reason": "runtime_validation_failed"},
                    )
                )
            except RuntimeConflictError:
                LogUtil.agent_runtime_step(
                    task_type=runtime_policy.task_type,
                    phase="graph_start",
                    status="failed",
                    input_ref=requested_progress_node_ref,
                    error_type="RuntimeConflictError",
                )
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="Polish question graph request conflicts",
                        details={"reason": "idempotency_conflict"},
                    )
                )
            except RuntimePolicyError:
                LogUtil.agent_runtime_step(
                    task_type=runtime_policy.task_type,
                    phase="graph_start",
                    status="failed",
                    input_ref=requested_progress_node_ref,
                    error_type="RuntimePolicyError",
                )
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="Polish question graph request blocked",
                        details={"reason": "runtime_policy_blocked"},
                    )
                )
            except Exception as exc:
                LogUtil.agent_runtime_step(
                    task_type=runtime_policy.task_type,
                    phase="graph_start",
                    status="failed",
                    input_ref=requested_progress_node_ref,
                    error_type=exc.__class__.__name__,
                )
                return ApplicationResult(
                    error=DomainError(code="generation_failed", message="Polish question graph failed")
                )
            if graph_status is not None:
                LogUtil.agent_runtime_step(
                    task_type=runtime_policy.task_type,
                    phase="graph_start",
                    status="succeeded",
                    input_ref=requested_progress_node_ref,
                    output_ref=graph_status.agent_run_id,
                )
                candidate_payload = _graph_status_candidate_payload(
                    graph_status,
                    runtime_policy=runtime_policy,
                )
                if candidate_payload is not None:
                    candidate_payload = _question_candidate_payload_with_request_metadata(
                        candidate_payload,
                        command=command,
                        requested_progress_node_ref=requested_progress_node_ref,
                    )
                    workflow_result = run_question_planned_workflow(
                        owner_id=command.owner_id,
                        session_id=command.session_id,
                        ai_task_id=graph_status.ai_task_id,
                        agent_run_id=graph_status.agent_run_id,
                        candidate_payload=candidate_payload,
                        progress_context=progress_context,
                        requested_progress_node_ref=requested_progress_node_ref,
                        graph_fallback_reason=None,
                        trace_refs=graph_status.trace_refs,
                        follow_up_context=follow_up_context,
                        runtime_policy=runtime_policy,
                    )
                    candidate_payload = workflow_result.candidate
                    if workflow_result.validation_errors:
                        task = build_question_candidate_validation_task(
                            ai_task_id=graph_status.ai_task_id,
                            workflow_result=workflow_result,
                            validation_errors=None,
                            created_at=now,
                            runtime_policy=runtime_policy,
                        )
                        self._polish_repository.add_task(
                            task,
                            owner_id=command.owner_id,
                            actor_id=command.actor_id,
                            target_ref_id=command.session_id,
                        )
                        return ApplicationResult(value=task)
                    trusted_metadata_error = _feedback_next_question_trusted_metadata_error(
                        command,
                        workflow_result.candidate.get("question_metadata"),
                    )
                    if trusted_metadata_error is not None:
                        return ApplicationResult(error=trusted_metadata_error)
                    try:
                        plan = build_question_result_write_plan(
                            owner_id=command.owner_id,
                            actor_id=command.actor_id,
                            session_id=command.session_id,
                            ai_task_id=graph_status.ai_task_id,
                            agent_run_id=graph_status.agent_run_id,
                            candidate=candidate_payload,
                            progress_node_ref=requested_progress_node_ref,
                            trace_refs=workflow_result.trace_refs,
                            contract_ids=runtime_policy.contract_ids,
                        )
                        write_result = AgentPersistenceHandoff().write_question_result(
                            plan,
                            question_repository=self._polish_repository,
                            now=now,
                        )
                    except RuntimeValidationError as exc:
                        task = build_question_candidate_validation_task(
                            ai_task_id=graph_status.ai_task_id,
                            workflow_result=workflow_result,
                            validation_errors=(str(exc),),
                            created_at=now,
                            runtime_policy=runtime_policy,
                        )
                        self._polish_repository.add_task(
                            task,
                            owner_id=command.owner_id,
                            actor_id=command.actor_id,
                            target_ref_id=command.session_id,
                        )
                        return ApplicationResult(value=task)
                    except RuntimeConflictError:
                        return ApplicationResult(
                            error=DomainError(
                                code="validation_failed",
                                message="Polish question graph persistence conflicts",
                                details={"reason": "question_final_write_conflict"},
                            )
                        )
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
                    runtime_policy=runtime_policy,
                )
                self._polish_repository.add_task(
                    task,
                    owner_id=command.owner_id,
                    actor_id=command.actor_id,
                    target_ref_id=command.session_id,
                )
                return ApplicationResult(value=task)

        task_id = generate_resource_id(ResourceIdPrefix.TASK)
        if graph_fallback_reason is None and self._ai_orchestration_facade is None:
            graph_fallback_reason = "agent_facade_absent"
        question_generation_result = self._question_generation_service.generate(
            session=session,
            context=progress_context,
            plan=detail.progress_tree_plan,
            state=detail.progress_tree_state,
            requested_ref=requested_progress_node_ref,
            follow_up_context=follow_up_context,
            runtime_policy=runtime_policy,
        )
        if not question_generation_result.succeeded or question_generation_result.draft is None:
            task = _polish_question_generation_validation_failed_task_status(
                task_id=task_id,
                result=question_generation_result,
                requested_progress_node_ref=requested_progress_node_ref,
                created_at=now,
                runtime_policy=runtime_policy,
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
        trusted_metadata_error = _feedback_next_question_trusted_metadata_error(command, question_metadata)
        if trusted_metadata_error is not None:
            return ApplicationResult(error=trusted_metadata_error)
        question_metadata["completed_focus_refs"] = list(completed_focus_refs)
        if graph_fallback_reason is not None:
            question_metadata["graph_fallback_reason"] = graph_fallback_reason
            question_metadata["fallback_reason"] = graph_fallback_reason
            question_metadata["graph_status"] = "disabled_fallback"
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
            question_metadata["focus_dimension"] = question_draft.question_pattern or "evidence_grounded_question"
        if not question_metadata.get("template_signature"):
            question_metadata["template_signature"] = f"tpl:evidence_grounded_question:{focus_key}"
        if not question_metadata.get("blueprint_signature"):
            question_metadata["blueprint_signature"] = f"bp:{sha256(focus_seed.encode('utf-8')).hexdigest()[:16]}"
        question_metadata["similarity_checked"] = True
        question_metadata["max_similarity_in_same_category"] = 0.0
        if _question_generation_mode(command) == QUESTION_GENERATION_MODE_FOLLOW_UP:
            if not question_metadata.get("follow_up_reason"):
                question_metadata["follow_up_reason"] = "business_follow_up_request"
            if not question_metadata.get("follow_up_target_dimension"):
                question_metadata["follow_up_target_dimension"] = question_metadata["focus_dimension"]
        question_draft = replace(question_draft, question_metadata=question_metadata)
        agent_run_id = build_direct_question_agent_run_id(
            owner_id=command.owner_id,
            session_id=command.session_id,
            ai_task_id=task_id,
            progress_node_ref=question_draft.progress_node_ref or requested_progress_node_ref,
        )
        workflow_result = run_question_planned_workflow(
            owner_id=command.owner_id,
            session_id=command.session_id,
            ai_task_id=task_id,
            agent_run_id=agent_run_id,
            generation_result=replace(question_generation_result, draft=question_draft),
            progress_context=progress_context,
            requested_progress_node_ref=requested_progress_node_ref,
            graph_fallback_reason=graph_fallback_reason,
            follow_up_context=follow_up_context,
            runtime_policy=runtime_policy,
        )
        candidate_payload = workflow_result.candidate
        if workflow_result.validation_errors:
            task = build_question_candidate_validation_task(
                ai_task_id=task_id,
                workflow_result=workflow_result,
                validation_errors=None,
                created_at=now,
                runtime_policy=runtime_policy,
            )
            self._polish_repository.add_task(
                task,
                owner_id=command.owner_id,
                actor_id=command.actor_id,
                target_ref_id=command.session_id,
            )
            return ApplicationResult(value=task)
        try:
            plan = build_question_result_write_plan(
                owner_id=command.owner_id,
                actor_id=command.actor_id,
                session_id=command.session_id,
                ai_task_id=task_id,
                agent_run_id=agent_run_id,
                candidate=candidate_payload,
                progress_node_ref=requested_progress_node_ref,
                trace_refs=workflow_result.trace_refs,
                contract_ids=runtime_policy.contract_ids,
            )
            write_result = AgentPersistenceHandoff().write_question_result(
                plan,
                question_repository=self._polish_repository,
                now=now,
            )
        except RuntimeValidationError as exc:
            task = build_question_candidate_validation_task(
                ai_task_id=task_id,
                workflow_result=workflow_result,
                validation_errors=(str(exc),),
                created_at=now,
                runtime_policy=runtime_policy,
            )
            self._polish_repository.add_task(
                task,
                owner_id=command.owner_id,
                actor_id=command.actor_id,
                target_ref_id=command.session_id,
            )
            return ApplicationResult(value=task)
        except RuntimeConflictError:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Polish question candidate handoff conflicts",
                    details={"reason": "question_final_write_conflict"},
                )
            )
        except RuntimePolicyError:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Polish question candidate handoff blocked",
                    details={"reason": "candidate_handoff_policy_blocked"},
                )
            )
        if write_result is None:
            return ApplicationResult(
                error=DomainError(
                    code="generation_failed",
                    message="Polish question candidate handoff failed",
                )
            )
        task = write_result.task_status
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
        if session is None or session.status == SESSION_STATUS_DELETED:
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
        boundary_result = self._answer_submission_boundary_builder.prepare(command)
        if not boundary_result.is_success:
            return ApplicationResult(error=boundary_result.error)
        boundary = boundary_result.value
        assert boundary is not None
        answer_text = boundary.answer_text
        idempotency_key = boundary.idempotency_key
        now = utc_now()
        answer = self._answer_submission_boundary_builder.build_answer(
            command=command,
            answer_id=generate_resource_id(ResourceIdPrefix.ANSWER),
            answer_round=0,
            answer_text=answer_text,
            timestamp=now,
        )
        add_answer_once = getattr(self._polish_repository, "add_answer_once", None)
        if not callable(add_answer_once):
            return self._create_answer_with_legacy_repository(
                command=command,
                answer=answer,
                idempotency_key=idempotency_key,
                request_body_hash=boundary.request_body_hash,
            )

        saved_answer = add_answer_once(
            answer=answer,
            idempotency_key=idempotency_key,
            request_body_hash=boundary.request_body_hash,
        )
        if (
            idempotency_key is not None
            and saved_answer.answer_id != answer.answer_id
            and saved_answer.request_body_hash != boundary.request_body_hash
        ):
            return ApplicationResult(
                error=DomainError(
                    code="idempotency_conflict",
                    message="Idempotency key conflicts with a different answer payload",
                    details={
                        "field": "idempotency_key",
                        "reason": "idempotency_conflict",
                    },
                )
            )
        return ApplicationResult(value=saved_answer)

    def _create_answer_with_legacy_repository(
        self,
        *,
        command: CreatePolishAnswerCommand,
        answer: PolishAnswer,
        idempotency_key: str | None,
        request_body_hash: str,
    ) -> ApplicationResult[PolishAnswer]:
        if idempotency_key is not None:
            record_key = (command.owner_id, command.session_id, command.question_id, idempotency_key)
            cached = self._answer_submission_records.get(record_key)
            if cached is not None:
                cached_answer_id, cached_request_body_hash = cached
                if cached_request_body_hash != request_body_hash:
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
        answer_to_save = replace(
            answer,
            answer_round=answer_round,
            idempotency_key=idempotency_key,
            request_body_hash=request_body_hash,
        )
        self._polish_repository.add_answer(answer_to_save)
        if idempotency_key is not None:
            self._answer_submission_records[(command.owner_id, command.session_id, command.question_id, idempotency_key)] = (
                answer_to_save.answer_id,
                request_body_hash,
            )
        return ApplicationResult(value=answer_to_save)

    def create_feedback_task(self, command: CreatePolishFeedbackTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        return self._feedback_service.create_feedback_task(command)

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

    def generate_session_report(
        self,
        command: GeneratePolishSessionReportCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None or session.status == SESSION_STATUS_DELETED:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        session_with_report = self._polish_repository.create_session_report(
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            session_id=command.session_id,
            report_id=generate_resource_id(ResourceIdPrefix.REPORT),
        )
        return ApplicationResult(
            value=self._build_session_detail(owner_id=command.owner_id, session=session_with_report)
        )

    def soft_delete_session(
        self,
        command: SoftDeletePolishSessionCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        if session.status == SESSION_STATUS_DELETED:
            return ApplicationResult(value=self._build_session_detail(owner_id=command.owner_id, session=session))
        now = utc_now()
        deleted_session = replace(session, status=SESSION_STATUS_DELETED, updated_at=now)
        self._polish_repository.save_session_status(deleted_session)
        return ApplicationResult(value=self._build_session_detail(owner_id=command.owner_id, session=deleted_session))

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
        canonical_evidence_pack = self._build_canonical_evidence_pack(
            owner_id=owner_id,
            detail=detail,
            job=job,
            job_version=job_version,
            resume=resume,
            resume_version=resume_version,
            match_analysis=match_analysis,
        )
        canonical_asset_items = _session_canonical_project_assets(canonical_evidence_pack)
        progress_context = build_polish_progress_context(
            detail,
            job=job,
            job_version=job_version,
            resume=resume,
            resume_version=resume_version,
            match_analysis=match_analysis,
            weaknesses=None,
            assets=canonical_asset_items,
            canonical_evidence_pack=canonical_evidence_pack,
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

    def _build_canonical_evidence_pack(
        self,
        *,
        owner_id: str,
        detail: PolishSessionDetail,
        job: Job | None,
        job_version: JobVersion | None,
        resume: Resume | None,
        resume_version: ResumeVersion | None,
        match_analysis: JobMatchAnalysis | None,
    ) -> dict[str, Any] | None:
        if self._canonical_evidence_service is None:
            return None
        return self._canonical_evidence_service.build_pack(
            owner_id=owner_id,
            session_id=detail.session.session_id,
            job_id=detail.session.job_id,
            job_version_id=detail.session.job_version_id,
            resume_id=detail.session.resume_id,
            resume_version_id=detail.session.resume_version_id,
            query_inputs=_canonical_evidence_query_inputs(
                detail=detail,
                job=job,
                job_version=job_version,
                resume=resume,
                resume_version=resume_version,
                match_analysis=match_analysis,
            ),
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


class _PolishOperationDelegate:
    def __init__(self, operations: _PolishUseCaseOperations) -> None:
        self._operations = operations

    def bind(self, operations: _PolishUseCaseOperations) -> None:
        self._operations = operations

    def bootstrap(self) -> ApplicationResult[str]:
        return _PolishUseCaseOperations.bootstrap(self._operations)

    def list_topics(self, query: ListPolishTopicsQuery) -> ApplicationResult[tuple[PolishTopic, ...]]:
        return _PolishUseCaseOperations.list_topics(self._operations, query)

    def list_sessions(self, query: ListPolishSessionsQuery) -> ApplicationResult[tuple[PolishSessionDetail, ...]]:
        return _PolishUseCaseOperations.list_sessions(self._operations, query)

    def create_session(self, command: CreatePolishSessionCommand) -> ApplicationResult[PolishSession]:
        return _PolishUseCaseOperations.create_session(self._operations, command)

    def generate_initial_progress_tree(
        self,
        command: GenerateInitialPolishProgressTreeCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return _PolishUseCaseOperations.generate_initial_progress_tree(self._operations, command)

    def get_session(self, query: GetPolishSessionQuery) -> ApplicationResult[PolishSessionDetail]:
        return _PolishUseCaseOperations.get_session(self._operations, query)

    def create_question_task(self, command: CreatePolishQuestionTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        return _PolishUseCaseOperations.create_question_task(self._operations, command)

    def complete_question(self, command: CompletePolishQuestionCommand) -> ApplicationResult[PolishSessionDetail]:
        return _PolishUseCaseOperations.complete_question(self._operations, command)

    def end_session(self, command: EndPolishSessionCommand) -> ApplicationResult[PolishSessionDetail]:
        return _PolishUseCaseOperations.end_session(self._operations, command)

    def create_answer(self, command: CreatePolishAnswerCommand) -> ApplicationResult[PolishAnswer]:
        return _PolishUseCaseOperations.create_answer(self._operations, command)

    def create_feedback_task(self, command: CreatePolishFeedbackTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        return _PolishUseCaseOperations.create_feedback_task(self._operations, command)

    def refresh_progress_tree_state(
        self,
        command: RefreshPolishProgressTreeStateCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return _PolishUseCaseOperations.refresh_progress_tree_state(self._operations, command)

    def generate_session_report(
        self,
        command: GeneratePolishSessionReportCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return _PolishUseCaseOperations.generate_session_report(self._operations, command)

    def soft_delete_session(
        self,
        command: SoftDeletePolishSessionCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return _PolishUseCaseOperations.soft_delete_session(self._operations, command)


class PolishUseCases(_PolishUseCaseOperations):
    def __init__(
        self,
        *,
        polish_repository: PolishRepository,
        binding_repository: BindingRepository,
        resume_repository: ResumeRepository,
        job_repository: JobRepository,
        job_match_repository: JobMatchRepository | None = None,
        asset_repository: AssetRepository | None = None,
        canonical_evidence_service: CanonicalEvidenceService | None = None,
        progress_tree_service: PolishProgressTreeLlmService | None = None,
        ai_orchestration_facade: AiOrchestrationFacade | None = None,
        question_generation_service: QuestionGenerationService | None = None,
        question_generation_policy: QuestionGenerationRuntimePolicy | None = None,
        question_generation_policy_resolver: QuestionGenerationRuntimePolicyResolver | None = None,
        feedback_generation_service: FeedbackGenerationService | None = None,
    ) -> None:
        super().__init__(
            polish_repository=polish_repository,
            binding_repository=binding_repository,
            resume_repository=resume_repository,
            job_repository=job_repository,
            job_match_repository=job_match_repository,
            asset_repository=asset_repository,
            canonical_evidence_service=canonical_evidence_service,
            progress_tree_service=progress_tree_service,
            ai_orchestration_facade=ai_orchestration_facade,
            question_generation_service=question_generation_service,
            question_generation_policy=question_generation_policy,
            question_generation_policy_resolver=question_generation_policy_resolver,
            feedback_generation_service=feedback_generation_service,
        )
        self._operation_delegate = _PolishOperationDelegate(self)
        self._session_service = PolishSessionApplicationService(
            self._operation_delegate,
            binding_repository=self._binding_repository,
        )
        self._question_service = PolishQuestionApplicationService(self._operation_delegate)
        self._answer_service = PolishAnswerApplicationService(self._operation_delegate)
        self._feedback_service = PolishFeedbackApplicationService(self)
        self._progress_service = PolishProgressApplicationService(self._operation_delegate)
        self._report_service = PolishReportApplicationService(
            self._operation_delegate,
            polish_repository=self._polish_repository,
            build_session_detail=self._build_session_detail,
        )

    def _sync_services(self) -> None:
        operation_delegate = getattr(self, "_operation_delegate", None)
        if operation_delegate is None:
            operation_delegate = _PolishOperationDelegate(self)
            self._operation_delegate = operation_delegate
        else:
            operation_delegate.bind(self)

        service_specs = (
            (
                "_session_service",
                PolishSessionApplicationService,
                {"binding_repository": self._binding_repository},
                self._operation_delegate,
            ),
            ("_question_service", PolishQuestionApplicationService, {}, self._operation_delegate),
            ("_answer_service", PolishAnswerApplicationService, {}, self._operation_delegate),
            ("_feedback_service", PolishFeedbackApplicationService, {}, self),
            ("_progress_service", PolishProgressApplicationService, {}, self._operation_delegate),
            (
                "_report_service",
                PolishReportApplicationService,
                {
                    "polish_repository": self._polish_repository,
                    "build_session_detail": self._build_session_detail,
                },
                self._operation_delegate,
            ),
        )
        for attr, service_cls, kwargs, operations in service_specs:
            service = getattr(self, attr, None)
            if service is None:
                setattr(self, attr, service_cls(operations, **kwargs))
                continue
            bind = getattr(service, "bind", None)
            if callable(bind):
                bind(operations)

    def bootstrap(self) -> ApplicationResult[str]:
        self._sync_services()
        return self._session_service.bootstrap()

    def list_topics(self, query: ListPolishTopicsQuery) -> ApplicationResult[tuple[PolishTopic, ...]]:
        self._sync_services()
        return self._session_service.list_topics(query)

    def list_sessions(self, query: ListPolishSessionsQuery) -> ApplicationResult[tuple[PolishSessionDetail, ...]]:
        self._sync_services()
        return self._session_service.list_sessions(query)

    def create_session(self, command: CreatePolishSessionCommand) -> ApplicationResult[PolishSession]:
        self._sync_services()
        return self._session_service.create_session(command)

    def generate_initial_progress_tree(
        self,
        command: GenerateInitialPolishProgressTreeCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        self._sync_services()
        return self._progress_service.generate_initial_progress_tree(command)

    def get_session(self, query: GetPolishSessionQuery) -> ApplicationResult[PolishSessionDetail]:
        self._sync_services()
        return self._session_service.get_session(query)

    def create_question_task(self, command: CreatePolishQuestionTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        self._sync_services()
        return self._question_service.create_question_task(command)

    def complete_question(self, command: CompletePolishQuestionCommand) -> ApplicationResult[PolishSessionDetail]:
        self._sync_services()
        return self._question_service.complete_question(command)

    def end_session(self, command: EndPolishSessionCommand) -> ApplicationResult[PolishSessionDetail]:
        self._sync_services()
        return self._session_service.end_session(command)

    def create_answer(self, command: CreatePolishAnswerCommand) -> ApplicationResult[PolishAnswer]:
        self._sync_services()
        return self._answer_service.create_answer(command)

    def create_feedback_task(self, command: CreatePolishFeedbackTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        self._sync_services()
        return PolishApplyFeedbackUseCase(self._polish_repository, self._feedback_service).execute(command)

    def refresh_progress_tree_state(
        self,
        command: RefreshPolishProgressTreeStateCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        self._sync_services()
        return self._progress_service.refresh_progress_tree_state(command)

    def generate_session_report(
        self,
        command: GeneratePolishSessionReportCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        self._sync_services()
        return self._report_service.generate_session_report(command)

    def soft_delete_session(
        self,
        command: SoftDeletePolishSessionCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        self._sync_services()
        return self._session_service.soft_delete_session(command)


def _session_canonical_project_assets(canonical_evidence_pack: dict[str, Any] | None) -> tuple[dict[str, Any], ...]:
    if not isinstance(canonical_evidence_pack, dict):
        return ()
    canonical_project_assets = canonical_evidence_pack.get("canonical_project_assets")
    if not isinstance(canonical_project_assets, dict):
        return ()
    items = canonical_project_assets.get("items")
    if not isinstance(items, list):
        return ()
    return tuple(item for item in items if isinstance(item, dict))


def _canonical_evidence_query_inputs(
    *,
    detail: PolishSessionDetail,
    job: Job | None,
    job_version: JobVersion | None,
    resume: Resume | None,
    resume_version: ResumeVersion | None,
    match_analysis: JobMatchAnalysis | None,
) -> tuple[object, ...]:
    session = detail.session
    values: list[object] = [
        session.topic_id,
        session.subtopic_id,
        session.custom_topic_text_summary,
        session.polish_theme,
        detail.job_title,
        detail.job_company,
        detail.resume_title,
        session.progress_tree_plan,
        session.progress_tree_state,
    ]
    if job is not None:
        values.extend([job.title, job.company, job.department, job.application_status])
    if job_version is not None:
        values.extend(job_version.responsibilities or [])
        values.extend(job_version.requirements or [])
        values.append(job_version.other_notes)
    if resume is not None:
        values.append(resume.title)
    if resume_version is not None:
        values.append(resume_version.markdown_text)
    if match_analysis is not None:
        values.append(match_analysis.result_payload_json)
    for turn in detail.turns[-8:]:
        values.extend([turn.question_text, turn.progress_node_ref, turn.question_metadata])
        for answer in turn.answers[-3:]:
            values.extend([answer.answer_text, answer.feedback_text, answer.feedback_payload])
    return tuple(value for value in values if value not in (None, ""))


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


def _polish_question_graph_context_snapshot(
    *,
    command: CreatePolishQuestionTaskCommand,
    detail: PolishSessionDetail,
    progress_context: dict[str, Any],
    requested_progress_node_ref: str,
    completed_focus_refs: tuple[str, ...],
    follow_up_context: dict[str, Any] | None,
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> dict[str, Any]:
    session = detail.session
    context_snapshot = {
        "context_source": "use_case_repository_snapshot",
        "context_source_version": "polish_question_graph_context.v1",
        "session": {
            "session_id": session.session_id,
            "owner_id": session.owner_id,
            "actor_id": session.actor_id,
            "status": session.status,
            "resume_id": session.resume_id,
            "resume_version_id": session.resume_version_id,
            "job_id": session.job_id,
            "job_version_id": session.job_version_id,
            "topic_id": session.topic_id,
            "subtopic_id": session.subtopic_id,
            "polish_theme": session.polish_theme,
        },
        "requested_progress_node_ref": requested_progress_node_ref,
        "completed_focus_refs": list(completed_focus_refs),
        "generation_mode": _question_generation_mode(command),
        "request_refs": {
            "progress_node_ref": _clean_question_request_text(command.progress_node_ref),
            "selected_progress_node_ref": _clean_question_request_text(
                command.selected_progress_node_ref
            ),
            "selected_primary_category_ref": _clean_question_request_text(
                command.selected_primary_category_ref
            ),
            "selected_secondary_category_ref": _clean_question_request_text(
                command.selected_secondary_category_ref
            ),
            "parent_question_id": _clean_question_request_text(command.parent_question_id),
            "parent_answer_id": _clean_question_request_text(command.parent_answer_id),
            "parent_feedback_id": _clean_question_request_text(command.parent_feedback_id),
        },
        "selected_category_path": list(_clean_question_request_list(command.selected_category_path)),
        "exclude_question_refs": list(_clean_question_request_list(command.exclude_question_refs)),
        "follow_up_context": follow_up_context or {},
        "selected_evidence_summaries": _polish_question_graph_selected_evidence_summaries(
            progress_context=progress_context,
            progress_tree_plan=detail.progress_tree_plan,
            progress_tree_state=detail.progress_tree_state,
            requested_progress_node_ref=requested_progress_node_ref,
            runtime_policy=runtime_policy,
        ),
        "progress_context": progress_context,
        "progress_tree_plan": detail.progress_tree_plan,
        "progress_tree_state": detail.progress_tree_state,
        "context_digest": str(
            detail.progress_tree_plan.get("context_digest")
            or progress_context.get("content_digest")
            or ""
        ),
        "runtime_policy": {
            "task_type": runtime_policy.task_type,
            "prompt_version": runtime_policy.prompt_version,
            "prompt_schema_id": runtime_policy.prompt_schema_id,
            "policy_version": runtime_policy.policy_version,
            "source": runtime_policy.source,
            "source_type": runtime_policy.source_type,
            "source_chain": list(runtime_policy.source_chain),
            "fallback": runtime_policy.fallback,
        },
    }
    context_snapshot.update(
        next_question_execution_grant_snapshot_to_metadata(
            command.next_question_execution_grant_snapshot
        )
    )
    return context_snapshot


def _polish_question_graph_selected_evidence_summaries(
    *,
    progress_context: dict[str, Any],
    progress_tree_plan: dict[str, Any],
    progress_tree_state: dict[str, Any],
    requested_progress_node_ref: str,
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> list[dict[str, Any]]:
    selection = select_progress_tree_evidence_chunks(
        progress_context,
        purpose="question_generation",
        max_chunks=4,
        max_chars=1800,
        existing_plan=progress_tree_plan,
        existing_state=progress_tree_state,
        progress_node_ref=requested_progress_node_ref,
        source_priority_policy=runtime_policy.source_priority_by_purpose,
    )
    return [
        {
            "ref": chunk.chunk_id,
            "summary": chunk.text[:360],
            "source_type": chunk.source_type,
        }
        for chunk in selection.selected_chunks
    ]


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
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> PolishTaskStatus:
    status = _graph_task_status_to_polish_status(status_ref.status)
    return PolishTaskStatus(
        ai_task_id=status_ref.ai_task_id,
        task_type=runtime_policy.task_type,
        status=status,
        contract_ids=runtime_policy.contract_ids,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=status_ref.agent_run_id, trace_type="agent_run", created_at=created_at),
        user_visible_status="题目生成中" if status == AiTaskStatus.RUNNING else "题目生成任务已启动",
        candidate_refs=_polish_question_graph_candidate_refs(
            status_ref,
            requested_progress_node_ref=requested_progress_node_ref,
        ),
    )


def _graph_status_candidate_payload(
    status_ref: object,
    *,
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> dict[str, Any] | None:
    candidate_payloads = getattr(status_ref, "candidate_payloads", ()) or ()
    if candidate_payloads:
        for candidate_payload in candidate_payloads:
            if _is_accepted_polish_question_candidate_payload(
                candidate_payload,
                runtime_policy=runtime_policy,
            ):
                return candidate_payload.payload
        return None
    for attribute in ("accepted_candidate", "candidate", "candidate_payload", "question_candidate"):
        candidate = getattr(status_ref, attribute, None)
        if isinstance(candidate, dict):
            return candidate
    return None


def _is_accepted_polish_question_candidate_payload(
    candidate_payload: object,
    *,
    runtime_policy: QuestionGenerationRuntimePolicy = DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY,
) -> bool:
    if not isinstance(candidate_payload, AgentCandidatePayload):
        return False
    if candidate_payload.status.strip().lower() not in runtime_policy.candidate_statuses:
        return False
    if candidate_payload.candidate_type.strip().lower() not in runtime_policy.candidate_types:
        return False
    if (
        candidate_payload.payload_schema_id.strip().lower()
        not in runtime_policy.candidate_payload_schema_ids
    ):
        return False
    return isinstance(candidate_payload.payload, dict)


def _polish_question_graph_validation_failed_task_status(
    status_ref: AgentTaskStatusRef,
    *,
    requested_progress_node_ref: str | None,
    created_at: Any,
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> PolishTaskStatus:
    return PolishTaskStatus(
        ai_task_id=status_ref.ai_task_id,
        task_type=runtime_policy.task_type,
        status=AiTaskStatus.VALIDATION_FAILED,
        contract_ids=runtime_policy.contract_ids,
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
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> PolishTaskStatus:
    progress_node_ref = result.progress_node_ref or requested_progress_node_ref
    candidate_refs = []
    if progress_node_ref:
        candidate_refs.append(ResourceRef(resource_type="progress_node", resource_id=progress_node_ref))
    candidate_refs.extend(ResourceRef(resource_type="evidence", resource_id=ref) for ref in result.evidence_refs)
    user_visible_status = (
        "题目生成配置未生效，请重启后端服务或检查 prompt contract。"
        if any(error.startswith("prompt_contract_") for error in result.validation_errors)
        else "题目生成校验未通过"
    )
    return PolishTaskStatus(
        ai_task_id=task_id,
        task_type=runtime_policy.task_type,
        status=AiTaskStatus.VALIDATION_FAILED,
        contract_ids=runtime_policy.contract_ids,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=task_id, trace_type="validation_result", created_at=created_at),
        user_visible_status=user_visible_status,
        candidate_refs=tuple(candidate_refs),
        validation_errors=result.validation_errors,
    )


def _follow_up_completed_task_status(
    *,
    task_id: str,
    runtime_policy: QuestionGenerationRuntimePolicy,
    requested_progress_node_ref: str | None,
    focus_key: str,
    created_at: Any,
) -> PolishTaskStatus:
    candidate_refs = [ResourceRef(resource_type="follow_up_focus", resource_id=focus_key)]
    if requested_progress_node_ref:
        candidate_refs.append(ResourceRef(resource_type="progress_node", resource_id=requested_progress_node_ref))
    return PolishTaskStatus(
        ai_task_id=task_id,
        task_type=runtime_policy.task_type,
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=runtime_policy.contract_ids,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=focus_key, trace_type="follow_up_decision", created_at=created_at),
        user_visible_status="当前追问焦点已完成，可进入下一题",
        candidate_refs=tuple(candidate_refs),
    )


def _graph_task_status_to_polish_status(raw_status: str) -> AiTaskStatus:
    normalized = str(raw_status or "").strip().lower()
    if normalized == "in_progress":
        return AiTaskStatus.RUNNING
    if normalized in {"timed_out", "timeout"}:
        return AiTaskStatus.TIMED_OUT
    category = classify_agent_runtime_status(normalized)
    if category in {"pending", "succeeded", "replayed"}:
        return AiTaskStatus.QUEUED
    if category in {"running", "interrupted"}:
        return AiTaskStatus.RUNNING
    if category == "cancelled":
        return AiTaskStatus.CANCELLED
    if category == "blocked":
        return AiTaskStatus.VALIDATION_FAILED
    if category == "failed":
        if "validation" in normalized or "invalid" in normalized:
            return AiTaskStatus.VALIDATION_FAILED
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


def _build_follow_up_generation_context(
    *,
    command: CreatePolishQuestionTaskCommand,
    detail: PolishSessionDetail,
    completed_focus_refs: tuple[str, ...],
) -> dict[str, Any] | DomainError:
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

    coverage_decision = _build_follow_up_coverage_decision_from_feedback(
        feedback_payload=parent_answer.feedback_payload,
        expected_answer_dimensions=parent_turn.question_metadata.get("expected_answer_dimensions"),
        completed_focus_refs=completed_focus_refs,
        used_focus_refs=_follow_up_used_focus_refs(detail.turns, parent_question_id=parent_turn.question_id),
    )
    coverage_matrix = coverage_decision["coverage_matrix"]
    focus = coverage_decision["focus"]
    progress_node_ref = _clean_question_request_text(command.selected_progress_node_ref) or parent_turn.progress_node_ref
    return {
        "parent_question_id": parent_turn.question_id,
        "parent_question_excerpt": _clean_question_request_text(parent_turn.question_text, max_chars=240),
        "parent_answer_id": parent_answer.answer_id,
        "parent_answer_excerpt": _follow_up_excerpt(parent_answer.answer_text),
        "parent_feedback_id": parent_answer.feedback_id,
        "parent_feedback_excerpt": _clean_question_request_text(parent_answer.feedback_text, max_chars=240),
        "target_dimension": focus["target_dimension"],
        "follow_up_reason": focus["follow_up_reason"],
        "progress_node_ref": progress_node_ref,
        "parent_evidence_refs": list(parent_turn.evidence_refs),
        "coverage_matrix": coverage_matrix,
        "focus_key": focus["focus_key"],
        "focus_source": focus["focus_source"],
        "recommended_action": focus["recommended_action"],
        "completed_focus_refs": list(coverage_matrix.get("completed_focus_refs") or []),
        "completion_status": focus["completion_status"],
    }


def _feedback_next_question_flow_active(
    command: CreatePolishQuestionTaskCommand,
    *,
    feedbacks: tuple[PolishFeedback, ...],
) -> bool:
    if command.execution_source == QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT:
        return True
    if _clean_question_request_text(command.authorized_feedback_id) is not None:
        return True
    if _clean_question_request_text(command.authorized_answer_id) is not None:
        return True
    if _clean_question_request_text(command.authorized_parent_question_id) is not None:
        return True
    if _question_generation_mode(command) != QUESTION_GENERATION_MODE_NEW:
        return False
    return any(_clean_question_request_text(feedback.status) == "generated" for feedback in feedbacks)


def _feedback_next_question_trusted_execution_error(command: CreatePolishQuestionTaskCommand) -> DomainError | None:
    if command.execution_source != QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT:
        return None
    result = validate_consumed_next_question_execution_grant_snapshot(
        command.next_question_execution_grant_snapshot,
        session_id=command.session_id,
        feedback_id=_clean_question_request_text(command.authorized_feedback_id) or "",
        answer_id=_clean_question_request_text(command.authorized_answer_id) or "",
        parent_question_id=_clean_question_request_text(command.authorized_parent_question_id) or "",
        selected_progress_node_ref=command.selected_progress_node_ref,
    )
    if result.is_valid:
        return None
    return DomainError(
        code="validation_failed",
        message="Feedback next-question execution grant is not trusted",
        details={"reason": result.reason, **result.details},
    )


def _feedback_next_question_trusted_metadata_error(
    command: CreatePolishQuestionTaskCommand,
    metadata: object,
) -> DomainError | None:
    if command.execution_source != QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT:
        return None
    safe_metadata = metadata if isinstance(metadata, dict) else {}
    result = validate_consumed_next_question_execution_grant_snapshot(
        safe_metadata.get("next_question_execution_grant"),
        session_id=command.session_id,
        feedback_id=_clean_question_request_text(command.authorized_feedback_id) or "",
        answer_id=_clean_question_request_text(command.authorized_answer_id) or "",
        parent_question_id=_clean_question_request_text(command.authorized_parent_question_id) or "",
        selected_progress_node_ref=command.selected_progress_node_ref,
    )
    if result.is_valid:
        return None
    return DomainError(
        code="validation_failed",
        message="Feedback next-question trusted output is missing consumed grant snapshot",
        details={"reason": result.reason, **result.details},
    )


def _feedback_next_question_selected_progress_node_ref(
    *,
    command: CreatePolishQuestionTaskCommand,
    detail: PolishSessionDetail,
    turn: PolishSessionTurn,
) -> str | DomainError:
    parent_progress_node_ref = _clean_question_request_text(turn.progress_node_ref)
    if parent_progress_node_ref is None:
        return DomainError(
            code="validation_failed",
            message="authorized feedback question has no progress node",
            details={"reason": "authorized_feedback_progress_node_missing", "field": "selected_progress_node_ref"},
        )

    plan_progress_node_refs = set(_plan_progress_node_refs(detail.progress_tree_plan))
    if plan_progress_node_refs and parent_progress_node_ref not in plan_progress_node_refs:
        return DomainError(
            code="validation_failed",
            message="authorized feedback progress node is stale",
            details={
                "reason": "stale_progress_selection",
                "field": "selected_progress_node_ref",
                "progress_node_ref": parent_progress_node_ref,
            },
        )

    requested_progress_node_ref = _clean_question_request_text(command.selected_progress_node_ref)
    if requested_progress_node_ref is None:
        return parent_progress_node_ref
    if plan_progress_node_refs and requested_progress_node_ref not in plan_progress_node_refs:
        return DomainError(
            code="validation_failed",
            message="selected progress node could not be located",
            details={
                "reason": "target_node_not_found",
                "field": "selected_progress_node_ref",
                "progress_node_ref": requested_progress_node_ref,
            },
        )
    if requested_progress_node_ref != parent_progress_node_ref:
        return DomainError(
            code="validation_failed",
            message="selected progress node is not allowed by feedback grant",
            details={
                "reason": "target_node_not_allowed",
                "field": "selected_progress_node_ref",
                "allowed_progress_node_refs": [parent_progress_node_ref],
                "progress_node_ref": requested_progress_node_ref,
            },
        )
    return requested_progress_node_ref


def _authorize_feedback_next_question_execution(
    *,
    command: CreatePolishQuestionTaskCommand,
    detail: PolishSessionDetail,
    feedbacks: tuple[PolishFeedback, ...],
    latest_feedback_for_answer: Any,
) -> CreatePolishQuestionTaskCommand | DomainError:
    if command.execution_source != QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT:
        return DomainError(
            code="validation_failed",
            message="Feedback next-question execution requires intent endpoint authorization",
            details={
                "reason": "feedback_next_question_requires_intent_endpoint",
                "field": "parent_feedback_id",
            },
        )

    authorized_feedback_id = _clean_question_request_text(command.authorized_feedback_id)
    if authorized_feedback_id is None:
        return DomainError(
            code="validation_failed",
            message="authorized_feedback_id is required",
            details={"reason": "authorized_feedback_id_required", "field": "authorized_feedback_id"},
        )
    explicit_parent_feedback_id = _clean_question_request_text(command.parent_feedback_id)
    if explicit_parent_feedback_id is not None and explicit_parent_feedback_id != authorized_feedback_id:
        return DomainError(
            code="validation_failed",
            message="parent_feedback_id does not match authorized feedback",
            details={"reason": "authorized_feedback_id_mismatch", "field": "parent_feedback_id"},
        )

    feedback = next((item for item in feedbacks if item.feedback_id == authorized_feedback_id), None)
    if feedback is None:
        return DomainError(
            code="not_found_or_inaccessible",
            message="Feedback not found",
            details={"reason": "authorized_feedback_not_in_session"},
        )

    turn, answer = _find_feedback_turn_answer(detail.turns, feedback)
    if turn is None or answer is None:
        return DomainError(
            code="not_found_or_inaccessible",
            message="Feedback answer not found in session",
            details={"reason": "authorized_feedback_answer_not_in_session"},
        )

    latest_feedback = latest_feedback_for_answer(
        owner_id=command.owner_id,
        answer_id=feedback.answer_id,
        status="generated",
    )
    if latest_feedback is None or latest_feedback.feedback_id != authorized_feedback_id:
        return DomainError(
            code="stale_version_conflict",
            message="Feedback is not the latest generated feedback",
            details={
                "reason": "stale_feedback_replay",
                "feedback_id": authorized_feedback_id,
                "latest_feedback_id": latest_feedback.feedback_id if latest_feedback is not None else None,
            },
        )

    if (
        _clean_question_request_text(command.authorized_answer_id) is not None
        and command.authorized_answer_id != feedback.answer_id
    ):
        return DomainError(
            code="validation_failed",
            message="authorized_answer_id does not match feedback",
            details={"reason": "authorized_answer_id_mismatch", "field": "authorized_answer_id"},
        )
    if (
        _clean_question_request_text(command.authorized_parent_question_id) is not None
        and command.authorized_parent_question_id != turn.question_id
    ):
        return DomainError(
            code="validation_failed",
            message="authorized_parent_question_id does not match feedback",
            details={"reason": "authorized_parent_question_id_mismatch", "field": "authorized_parent_question_id"},
        )

    feedback_payload = _feedback_payload_from_summary(feedback.feedback_summary)
    payload_guard = validate_feedback_next_question_authorization_payload(
        feedback_payload,
        feedback_id=authorized_feedback_id,
        session_id=command.session_id,
        answer_id=feedback.answer_id,
        parent_question_id=turn.question_id,
    )
    if not payload_guard.is_valid:
        return DomainError(
            code="validation_failed",
            message="Feedback payload cannot authorize next question generation",
            details={"reason": payload_guard.reason, **payload_guard.details},
        )

    decision = _feedback_next_action_decision(feedback_payload, feedback_status=feedback.status)
    if not decision["allowed"]:
        return DomainError(
            code="validation_failed",
            message="Feedback does not authorize next question generation",
            details={
                "reason": "feedback_next_question_not_allowed",
                "feedback_id": authorized_feedback_id,
                "outcome": decision["outcome"],
                "blocking_reason_codes": list(decision["blocking_reason_codes"]),
                "warning_reason_codes": list(decision["warning_reason_codes"]),
            },
        )

    selected_progress_node_ref = _feedback_next_question_selected_progress_node_ref(
        command=command,
        detail=detail,
        turn=turn,
    )
    if isinstance(selected_progress_node_ref, DomainError):
        return selected_progress_node_ref

    issued_at = utc_now()
    freshness_marker = _feedback_next_question_grant_freshness_marker(feedback)
    grant = build_next_question_execution_grant(
        session_id=command.session_id,
        feedback_id=authorized_feedback_id,
        answer_id=feedback.answer_id,
        parent_question_id=turn.question_id,
        selected_progress_node_ref=selected_progress_node_ref,
        allowed_progress_node_refs=(selected_progress_node_ref,),
        freshness_marker=freshness_marker,
        reason_codes=(QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT,),
        issued_at=issued_at,
    )
    validation_result = validate_next_question_intent(
        grant,
        session_id=command.session_id,
        feedback_id=authorized_feedback_id,
        answer_id=feedback.answer_id,
        parent_question_id=turn.question_id,
        selected_progress_node_ref=selected_progress_node_ref,
        freshness_marker=freshness_marker,
        now=issued_at,
    )
    if not validation_result.is_valid:
        return DomainError(
            code="validation_failed",
            message="Feedback next-question execution grant is invalid",
            details={"reason": validation_result.reason, **validation_result.details},
        )
    consumed_result = consume_next_question_execution_grant(grant, now=issued_at)
    if not consumed_result.is_valid or consumed_result.grant is None:
        return DomainError(
            code="validation_failed",
            message="Feedback next-question execution grant could not be consumed",
            details={"reason": consumed_result.reason, **consumed_result.details},
        )
    grant_snapshot = consumed_result.grant.to_snapshot(now=issued_at)

    return replace(
        command,
        generation_mode=QUESTION_GENERATION_MODE_NEW,
        progress_node_ref=None,
        selected_progress_node_ref=selected_progress_node_ref,
        parent_question_id=None,
        parent_answer_id=None,
        parent_feedback_id=None,
        authorized_feedback_id=authorized_feedback_id,
        authorized_answer_id=feedback.answer_id,
        authorized_parent_question_id=turn.question_id,
        next_question_execution_grant=consumed_result.grant,
        next_question_execution_grant_snapshot=grant_snapshot,
    )


def _find_feedback_turn_answer(
    turns: tuple[PolishSessionTurn, ...],
    feedback: PolishFeedback,
) -> tuple[PolishSessionTurn | None, PolishSessionAnswerDetail | None]:
    for turn in turns:
        for answer in turn.answers:
            if answer.answer_id == feedback.answer_id:
                return turn, answer
    return None, None


def _feedback_next_question_grant_freshness_marker(feedback: PolishFeedback) -> str:
    return f"{feedback.feedback_id}:{feedback.status}:{feedback.updated_at.isoformat()}"


def _feedback_next_action_decision(payload: dict[str, Any] | None, *, feedback_status: str) -> Any:
    safe_payload = payload if isinstance(payload, dict) else {}
    asset_check = _feedback_dict(safe_payload.get("asset_consistency_check"))
    answer_coverage = _feedback_dict(safe_payload.get("answer_coverage"))
    answer_change = _feedback_dict(safe_payload.get("answer_change_analysis"))
    candidates = _feedback_dict_list(safe_payload.get("project_asset_update_candidates"))
    blocking: list[str] = []
    warnings: list[str] = []
    generation_status = _clean_question_request_text(safe_payload.get("status"), max_chars=80) or feedback_status
    if generation_status not in {"generated", "partial", "low_confidence"} or feedback_status != "generated":
        blocking.append("feedback_generation_not_successful")
    if asset_check.get("status") == "conflict":
        blocking.append("asset_conflict_blocks_feedback_question_intent")
    if asset_check.get("user_clarification_required"):
        blocking.append("asset_clarification_blocks_feedback_question_intent")
    if _feedback_dict_list(asset_check.get("conflicts")):
        blocking.append("asset_conflict_blocks_feedback_question_intent")
    if any(answer_coverage.get(field_name) for field_name in ("missing_points", "weak_points", "contradicted_points")):
        blocking.append("unresolved_answer_points_block_feedback_question_intent")
    if answer_change.get("regressed_points"):
        blocking.append("answer_regression_blocks_feedback_question_intent")
    if _feedback_string_tuple(safe_payload.get("low_confidence_flags")):
        warnings.append("low_confidence_flags_present")
    if candidates:
        warnings.append("asset_update_candidate_requires_user_confirmation")
    return {
        "allowed": not blocking,
        "outcome": "question_execution_authorized" if not blocking else "question_execution_blocked",
        "blocking_reason_codes": tuple(dict.fromkeys(blocking)),
        "warning_reason_codes": tuple(dict.fromkeys(warnings)),
    }


def _feedback_dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _feedback_dict_list(value: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(dict(item) for item in value if isinstance(item, dict))


def _feedback_string_tuple(
    value: object,
    *,
    max_items: int = 20,
    max_item_chars: int = 240,
) -> tuple[str, ...]:
    if isinstance(value, str):
        raw_items: list[object] = [value]
    elif isinstance(value, (list, tuple)):
        raw_items = list(value)
    else:
        return ()
    cleaned: list[str] = []
    for item in raw_items:
        text = _clean_question_request_text(item, max_chars=max_item_chars)
        if text is not None:
            cleaned.append(text)
        if len(cleaned) >= max_items:
            break
    return tuple(cleaned)


def _follow_up_used_focus_refs(
    turns: tuple[PolishSessionTurn, ...],
    *,
    parent_question_id: str,
) -> tuple[str, ...]:
    refs: list[str] = []
    for turn in turns:
        metadata = turn.question_metadata if isinstance(turn.question_metadata, dict) else {}
        if _clean_question_request_text(metadata.get("parent_question_id")) != parent_question_id:
            continue
        focus_key = _clean_question_request_text(metadata.get("focus_key"), max_chars=160)
        if focus_key:
            refs.append(focus_key)
    return _clean_question_request_list(refs)




def _build_follow_up_coverage_decision_from_feedback(
    *,
    feedback_payload: object,
    expected_answer_dimensions: object,
    completed_focus_refs: tuple[str, ...],
    used_focus_refs: tuple[str, ...] = (),
) -> dict[str, Any]:
    payload = feedback_payload if isinstance(feedback_payload, dict) else {}
    answer_coverage = payload.get("answer_coverage") if isinstance(payload.get("answer_coverage"), dict) else {}
    answer_change = (
        payload.get("answer_change_analysis")
        if isinstance(payload.get("answer_change_analysis"), dict)
        else {}
    )
    asset_check = (
        payload.get("asset_consistency_check")
        if isinstance(payload.get("asset_consistency_check"), dict)
        else {}
    )

    expected_points = _follow_up_text_list(answer_coverage.get("expected_points"))
    if not expected_points:
        expected_points = _follow_up_text_list(expected_answer_dimensions)
    missing_points = _follow_up_text_list(answer_coverage.get("missing_points"))
    if not missing_points:
        legacy_missing = [
            _clean_question_request_text(
                item.get("title") or item.get("dimension_id") or item.get("expected_dimension"),
                max_chars=240,
            )
            for item in _dict_list(payload.get("missing_answer_dimensions"))
        ]
        missing_points = tuple(item for item in legacy_missing if item)

    decision = FollowUpCoveragePolicy.decide(
        FollowUpCoverageInput(
            expected_points=expected_points,
            covered_points=_follow_up_text_list(answer_coverage.get("covered_points")),
            missing_points=missing_points,
            weak_points=_follow_up_text_list(answer_coverage.get("weak_points")),
            contradicted_points=_follow_up_text_list(answer_coverage.get("contradicted_points")),
            regressed_points=_follow_up_text_list(answer_change.get("regressed_points")),
            fixed_loss_points=_follow_up_text_list(answer_change.get("fixed_loss_points"), max_chars=120),
            repeated_loss_points=_follow_up_text_list(answer_change.get("repeated_loss_points"), max_chars=120),
            asset_conflicts=_follow_up_asset_conflicts(asset_check),
            completed_focus_refs=_follow_up_text_list(completed_focus_refs, max_chars=160),
            used_focus_refs=_follow_up_text_list(used_focus_refs, max_chars=160),
            coverage_available=bool(answer_coverage),
        )
    )
    return decision.to_legacy_dict()


def _follow_up_asset_conflicts(asset_check: object) -> tuple[FollowUpAssetConflict, ...]:
    if not isinstance(asset_check, dict) or asset_check.get("status") != "conflict":
        return ()
    conflicts: list[FollowUpAssetConflict] = []
    for item in _dict_list(asset_check.get("conflicts"))[:6]:
        conflict = FollowUpAssetConflict(
            conflict_type=_clean_question_request_text(item.get("conflict_type"), max_chars=120),
            current_answer_claim=_clean_question_request_text(item.get("current_answer_claim"), max_chars=160),
            asset_claim=_clean_question_request_text(item.get("asset_claim"), max_chars=160),
            severity=_clean_question_request_text(item.get("severity"), max_chars=80),
        )
        if conflict.conflict_type or conflict.current_answer_claim or conflict.asset_claim or conflict.severity:
            conflicts.append(conflict)
    return tuple(conflicts)


def _follow_up_text_list(value: object, *, max_chars: int = 240) -> tuple[str, ...]:
    if value is None:
        return ()
    raw_items = value if isinstance(value, (list, tuple, set)) else [value]
    cleaned: list[str] = []
    for item in raw_items:
        text = str(item or "").strip()
        if text:
            cleaned.append(text[:max_chars])
    return tuple(dict.fromkeys(cleaned))


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


def _follow_up_excerpt(answer_text: str) -> str:
    return _clean_question_request_text(answer_text, max_chars=80) or "上一轮回答"


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
        if (
            _clean_question_request_text(command.parent_question_id) is not None
            or _clean_question_request_text(command.parent_answer_id) is not None
            or _clean_question_request_text(command.parent_feedback_id) is not None
        ):
            return DomainError(
                code="validation_failed",
                message="new_question must not include follow_up parent refs",
                details={"field": "generation_mode"},
            )
    if mode == QUESTION_GENERATION_MODE_REGENERATE_CURRENT_NODE and _question_generation_requested_ref(command) is None:
        return DomainError(
            code="validation_failed",
            message="regenerate_current_node requires a selected progress node",
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
    metadata = {
        "generation_mode": mode,
        "request_source": _question_generation_request_source(command, mode),
        "selected_primary_category_ref": _clean_question_request_text(command.selected_primary_category_ref),
        "selected_secondary_category_ref": _clean_question_request_text(command.selected_secondary_category_ref),
        "selected_progress_node_ref": selected_progress_node_ref,
        "selected_category_path": list(_clean_question_request_list(command.selected_category_path)),
        "parent_question_id": _clean_question_request_text(command.parent_question_id),
        "parent_answer_id": _clean_question_request_text(command.parent_answer_id),
        "parent_feedback_id": _clean_question_request_text(command.parent_feedback_id),
        "authorized_feedback_id": _clean_question_request_text(command.authorized_feedback_id),
        "authorized_answer_id": _clean_question_request_text(command.authorized_answer_id),
        "authorized_parent_question_id": _clean_question_request_text(command.authorized_parent_question_id),
        "exclude_question_refs": list(_clean_question_request_list(command.exclude_question_refs)),
        "completed_focus_refs": list(_clean_question_request_list(command.completed_focus_refs)),
    }
    metadata.update(
        next_question_execution_grant_snapshot_to_metadata(
            command.next_question_execution_grant_snapshot
        )
    )
    return metadata


def _question_candidate_payload_with_request_metadata(
    candidate_payload: dict[str, Any],
    *,
    command: CreatePolishQuestionTaskCommand,
    requested_progress_node_ref: str | None,
) -> dict[str, Any]:
    candidate = dict(candidate_payload)
    metadata = candidate.get("question_metadata") if isinstance(candidate.get("question_metadata"), dict) else {}
    metadata = dict(metadata)
    metadata.update(
        _question_generation_request_metadata(
            command,
            requested_progress_node_ref=requested_progress_node_ref,
            resolved_progress_node_ref=_clean_question_request_text(candidate.get("progress_node_ref")),
        )
    )
    candidate["question_metadata"] = metadata
    return candidate


def _question_generation_request_source(command: CreatePolishQuestionTaskCommand, mode: str) -> str:
    if command.execution_source == QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT:
        return QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT
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


def _pending_progress_artifacts(session_id: str, strategy: PolishThemeStrategy) -> dict[str, Any]:
    return _progress_artifacts_with_theme(
        {
            "status": PROGRESS_TREE_STATUS_PENDING,
            "progress_percent": 0,
            "progress_tree_plan": {
                "status": PROGRESS_TREE_STATUS_PENDING,
                "context_digest": f"pending:{session_id}",
                "nodes": [],
            },
            "progress_tree_state": {
                "status": PROGRESS_TREE_STATUS_PENDING,
                "node_states": [],
                "current_priority": None,
                "updated_from_turns_count": 0,
                "progress": {"progress_percent": 0},
                "summary": "进展树尚未生成",
            },
        },
        strategy,
    )


def _generating_progress_artifacts(
    detail: PolishSessionDetail,
    strategy: PolishThemeStrategy,
) -> dict[str, Any]:
    context_digest = detail.progress_context.get("content_digest") or f"generating:{detail.session.session_id}"
    plan = {
        **(detail.progress_tree_plan or {}),
        "status": PROGRESS_TREE_STATUS_GENERATING,
        "context_digest": context_digest,
        "nodes": detail.progress_tree_plan.get("nodes", []) if isinstance(detail.progress_tree_plan, dict) else [],
    }
    state = {
        **(detail.progress_tree_state or {}),
        "status": PROGRESS_TREE_STATUS_GENERATING,
        "node_states": detail.progress_tree_state.get("node_states", [])
        if isinstance(detail.progress_tree_state, dict)
        else [],
        "current_priority": detail.progress_tree_state.get("current_priority")
        if isinstance(detail.progress_tree_state, dict)
        else None,
        "updated_from_turns_count": detail.progress_tree_state.get("updated_from_turns_count", 0)
        if isinstance(detail.progress_tree_state, dict)
        else 0,
        "progress": {"progress_percent": detail.progress_percent},
        "summary": "进展树正在生成",
    }
    return _progress_artifacts_with_theme(
        {
            "status": PROGRESS_TREE_STATUS_GENERATING,
            "progress_percent": detail.progress_percent,
            "progress_tree_plan": plan,
            "progress_tree_state": state,
        },
        strategy,
    )


def _failed_initial_generation_artifacts(
    detail: PolishSessionDetail,
    *,
    reason: str,
) -> dict[str, Any]:
    context_digest = detail.progress_context.get("content_digest") or f"failed:{detail.session.session_id}"
    return {
        "status": PROGRESS_TREE_STATUS_FAILED,
        "progress_percent": 0,
        "progress_tree_plan": {
            "status": PROGRESS_TREE_STATUS_FAILED,
            "context_digest": context_digest,
            "nodes": [],
            "failure_reason": reason,
        },
        "progress_tree_state": {
            "status": PROGRESS_TREE_STATUS_FAILED,
            "node_states": [],
            "current_priority": None,
            "updated_from_turns_count": 0,
            "progress": {"progress_percent": 0},
            "failure_reason": reason,
        },
    }


def _initial_progress_generation_exception_reason(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "provider_timeout"
    if isinstance(exc, LlmTransportConfigurationError):
        return "provider_unavailable"
    if isinstance(exc, LlmTransportUnavailableError):
        message = str(exc).lower()
        if "timeout" in message or "超时" in message:
            return "provider_timeout"
        return "provider_unavailable"
    if isinstance(exc, LlmTransportResponseError):
        error_type = getattr(exc, "error_type", None)
        if error_type == "provider_output_truncated":
            return "provider_output_truncated"
        message = str(exc)
        if "输出被截断" in message or "JSON 不完整" in message:
            return "provider_output_truncated"
        return "provider_response_invalid"
    return "progress_tree_generation_failed"


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
