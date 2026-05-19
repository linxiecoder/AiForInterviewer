"""Polish use cases."""

from __future__ import annotations

from app.application.common.result import ApplicationResult
from app.application.polish.commands import (
    CreatePolishAnswerCommand,
    CreatePolishFeedbackTaskCommand,
    CreatePolishQuestionTaskCommand,
    CreatePolishSessionCommand,
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
from app.application.polish.queries import GetPolishSessionQuery, ListPolishSessionsQuery, ListPolishTopicsQuery
from app.application.resumes.ports import ResumeRepository
from app.domain.bindings.ports import BindingRepository
from app.domain.jobs.ports import JobRepository
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus, ScoreType
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.domain.shared.refs import TraceRef


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
UNNAMED_JOB_TITLE = "未命名岗位"
UNNAMED_RESUME_TITLE = "未命名简历"
UNNAMED_COMPANY_TITLE = "未命名公司"
UNNAMED_QUESTION_TEXT = "题干缺失"
UNNAMED_ANSWER_TEXT = "暂无回答"
UNNAMED_FEEDBACK_TEXT = "本轮反馈尚未生成"

POLISH_TOPICS: tuple[PolishTopic, ...] = (
    PolishTopic(
        topic_id="topic_project_depth",
        title="项目经历表达",
        description="围绕简历项目经历的职责、证据、结果和取舍进行表达打磨。",
        requires_job_binding=True,
        subtopics=(
            PolishSubtopic(
                subtopic_id="subtopic_project_impact",
                topic_id="topic_project_depth",
                title="业务影响与个人贡献",
                description="说明你负责了什么、产生了什么结果，以及如何证明。",
            ),
            PolishSubtopic(
                subtopic_id="subtopic_project_challenge",
                topic_id="topic_project_depth",
                title="难点与解决方案",
                description="梳理挑战、约束、备选方案和最终选择。",
            ),
        ),
    ),
    PolishTopic(
        topic_id="topic_system_design",
        title="系统设计与技术取舍",
        description="打磨架构拆分、接口边界、可观测性、性能和风险控制表达。",
        requires_job_binding=True,
        subtopics=(
            PolishSubtopic(
                subtopic_id="subtopic_tradeoff",
                topic_id="topic_system_design",
                title="技术取舍",
                description="解释方案比较、取舍依据、风险和回滚思路。",
            ),
            PolishSubtopic(
                subtopic_id="subtopic_reliability",
                topic_id="topic_system_design",
                title="可靠性与排障",
                description="说明监控、日志、降级和故障恢复设计。",
            ),
        ),
    ),
    PolishTopic(
        topic_id="topic_behavioral",
        title="行为面试表达",
        description="打磨协作、冲突、推进、复盘和成长类回答。",
        requires_job_binding=False,
        subtopics=(
            PolishSubtopic(
                subtopic_id="subtopic_collaboration",
                topic_id="topic_behavioral",
                title="协作与推进",
                description="用 STAR 结构表达协作场景、行动和结果。",
            ),
        ),
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
    ) -> None:
        self._polish_repository = polish_repository
        self._binding_repository = binding_repository
        self._resume_repository = resume_repository
        self._job_repository = job_repository

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

        now = utc_now()
        task_id = generate_resource_id(ResourceIdPrefix.TASK)
        question_id = generate_resource_id(ResourceIdPrefix.QUESTION)
        question = PolishQuestion(
            question_id=question_id,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            session_id=command.session_id,
            ai_task_id=task_id,
            question_text=_deterministic_question_text(session, command.progress_node_ref),
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
        if not answer_text:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Answer text cannot be empty",
                    details={"field": "answer_text"},
                )
            )

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
        feedback = PolishFeedback(
            feedback_id=feedback_id,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            session_id=command.session_id,
            answer_id=command.answer_id,
            ai_task_id=task_id,
            score_result_id=None,
            feedback_summary="测试可复现反馈：已保存回答，并生成 polish_answer 评分边界。",
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

    def _build_session_detail(
        self, *, owner_id: str, session: PolishSession, include_turns: bool = True
    ) -> PolishSessionDetail:
        job_title, job_company = self._resolve_job_labels(owner_id=owner_id, job_id=session.job_id)
        resume_title = self._resolve_resume_title(owner_id=owner_id, resume_id=session.resume_id)
        binding_label = self._build_binding_label(job_title=job_title, resume_title=resume_title)
        turns = self._build_session_turns(owner_id=owner_id, session_id=session.session_id) if include_turns else ()
        return PolishSessionDetail(
            session=session,
            job_title=job_title,
            job_company=job_company,
            resume_title=resume_title,
            binding_label=binding_label,
            turns=tuple(turns),
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
                answers=tuple(answers_by_question.get(question.question_id, ())),
            )
            for question in questions
        )

    def _resolve_job_labels(self, *, owner_id: str, job_id: str) -> tuple[str, str]:
        if not job_id:
            return (UNNAMED_JOB_TITLE, UNNAMED_COMPANY_TITLE)
        job = self._job_repository.get(job_id)
        if job is None or job.owner_id != owner_id:
            return (UNNAMED_JOB_TITLE, UNNAMED_COMPANY_TITLE)
        return (
            _or_fallback_text(job.title, UNNAMED_JOB_TITLE),
            _or_fallback_text(job.company, UNNAMED_COMPANY_TITLE),
        )

    def _resolve_resume_title(self, *, owner_id: str, resume_id: str) -> str:
        if not resume_id:
            return UNNAMED_RESUME_TITLE
        resume = self._resume_repository.get(resume_id)
        if resume is None or resume.owner_ref.owner_id != owner_id:
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
    feedback_text = feedback.feedback_summary if feedback is not None else None
    return PolishSessionAnswerDetail(
        answer_id=answer.answer_id,
        answer_round=answer.answer_round,
        answer_text=_or_fallback_text(answer.answer_text, UNNAMED_ANSWER_TEXT),
        answer_created_at=answer.created_at,
        feedback_text=_or_fallback_text(feedback_text, UNNAMED_FEEDBACK_TEXT),
        feedback_id=feedback.feedback_id if feedback is not None else None,
        score_result_id=feedback.score_result_id if feedback is not None else None,
        feedback_created_at=feedback.created_at if feedback is not None else None,
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


def _deterministic_question_text(session: PolishSession, progress_node_ref: str | None) -> str:
    topic = session.topic_id or "manual_topic"
    node = progress_node_ref or "current_progress"
    return f"请围绕 {topic} 说明一个具体案例，并补充你在 {node} 中的关键取舍。"
