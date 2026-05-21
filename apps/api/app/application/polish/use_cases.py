"""Polish use cases."""

from __future__ import annotations

import json
import threading
from dataclasses import replace
from typing import Any

from app.application.common.result import ApplicationResult
from app.application.job_match.entities import JobMatchAnalysis
from app.application.job_match.ports import JobMatchRepository
from app.application.polish.commands import (
    CreatePolishAnswerCommand,
    CreatePolishFeedbackTaskCommand,
    CreatePolishQuestionTaskCommand,
    CreatePolishSessionCommand,
    RefreshPolishProgressTreeStateCommand,
)
from app.application.polish.entities import (
    PolishAnswer,
    PolishFeedback,
    PolishQuestion,
    PolishSessionAnswerDetail,
    PolishSessionDetail,
    PolishSessionTurn,
    PolishSession,
    PolishSubtopic,
    PolishTaskStatus,
    PolishTopic,
)
from app.application.polish.ports import PolishRepository
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
    build_progress_node_question,
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


SESSION_STATUS_RUNNING = "running"
QUESTION_STATUS_GENERATED = "generated"
ANSWER_STATUS_SAVED = "saved"
FEEDBACK_STATUS_GENERATED = "generated"

QUESTION_CONTRACT_IDS = ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")
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
    ) -> None:
        self._polish_repository = polish_repository
        self._binding_repository = binding_repository
        self._resume_repository = resume_repository
        self._job_repository = job_repository
        self._job_match_repository = job_match_repository
        self._progress_tree_service = progress_tree_service or PolishProgressTreeLlmService(None)

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
        task_id = generate_resource_id(ResourceIdPrefix.TASK)
        question_id = generate_resource_id(ResourceIdPrefix.QUESTION)
        question_draft = build_progress_node_question(
            session=session,
            context=detail.progress_context,
            plan=detail.progress_tree_plan,
            state=detail.progress_tree_state,
            requested_ref=command.progress_node_ref,
        )
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

    def create_answer(self, command: CreatePolishAnswerCommand) -> ApplicationResult[PolishAnswer]:
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
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

        now = utc_now()
        task_id = generate_resource_id(ResourceIdPrefix.TASK)
        feedback_id = generate_resource_id(ResourceIdPrefix.TRACE)
        score_result_id = generate_resource_id(ResourceIdPrefix.SCORE)
        feedback_payload = _build_contract_shaped_feedback_payload(
            session=session,
            answer=answer,
            feedback_id=feedback_id,
            ai_task_id=task_id,
            score_result_id=score_result_id,
            created_at=now,
        )
        payload_error = _validate_contract_shaped_feedback_payload(feedback_payload)
        if payload_error is not None:
            return ApplicationResult(error=payload_error)
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
