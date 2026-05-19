"""SQLAlchemy repository for job match analyses."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.application.job_match.entities import JobMatchAnalysis
from app.application.job_match.ports import JobMatchRepository
from app.domain.shared.refs import ResourceRef
from app.infrastructure.db.models.job_match import JobMatchAnalysis as JobMatchAnalysisModel
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyJobMatchAnalysisRepository(JobMatchRepository):
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def add(self, analysis: JobMatchAnalysis) -> None:
        with self._session_factory() as session:
            session.merge(_to_model(analysis))
            session.commit()

    def get(self, analysis_id: str) -> JobMatchAnalysis | None:
        with self._session_factory() as session:
            found = session.get(JobMatchAnalysisModel, analysis_id)
            return _to_entity(found) if found is not None else None

    def get_latest_by_binding(self, owner_id: str, binding_id: str) -> JobMatchAnalysis | None:
        with self._session_factory() as session:
            found = session.scalar(
                select(JobMatchAnalysisModel)
                .where(
                    JobMatchAnalysisModel.owner_id == owner_id,
                    JobMatchAnalysisModel.binding_id == binding_id,
                    JobMatchAnalysisModel.status == "completed",
                )
                .order_by(
                    JobMatchAnalysisModel.created_at.desc(),
                    JobMatchAnalysisModel.updated_at.desc(),
                    JobMatchAnalysisModel.id.desc(),
                )
            )
            return _to_entity(found) if found is not None else None

    def get_ref(self, analysis_id: str) -> ResourceRef | None:
        with self._session_factory() as session:
            found = session.get(JobMatchAnalysisModel, analysis_id)
            if found is None:
                return None
            return ResourceRef(resource_type="job_match_analysis", resource_id=analysis_id)


def _to_model(analysis: JobMatchAnalysis) -> JobMatchAnalysisModel:
    return JobMatchAnalysisModel(
        id=analysis.analysis_id,
        owner_id=analysis.owner_id,
        actor_id=analysis.actor_id,
        record_version=1,
        status=analysis.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        binding_id=analysis.binding_id,
        resume_id=analysis.resume_id,
        resume_version_id=analysis.resume_version_id,
        job_id=analysis.job_id,
        job_version_id=analysis.job_version_id,
        overall_score=analysis.overall_score,
        overall_level=analysis.overall_level,
        confidence=analysis.confidence,
        result_payload_json=analysis.result_payload_json,
        markdown_report_text=analysis.markdown_report_text,
        score_rule_version=analysis.score_rule_version,
        prompt_version=analysis.prompt_version,
        model_name=analysis.model_name,
        source_digest=analysis.source_digest,
    )


def _to_entity(model: JobMatchAnalysisModel) -> JobMatchAnalysis:
    return JobMatchAnalysis(
        analysis_id=model.id,
        owner_id=model.owner_id,
        actor_id=model.actor_id or model.owner_id,
        binding_id=model.binding_id,
        resume_id=model.resume_id,
        resume_version_id=model.resume_version_id,
        job_id=model.job_id,
        job_version_id=model.job_version_id,
        status=model.status,
        overall_score=model.overall_score,
        overall_level=model.overall_level,
        confidence=model.confidence,
        result_payload_json=dict(model.result_payload_json),
        markdown_report_text=model.markdown_report_text,
        score_rule_version=model.score_rule_version,
        prompt_version=model.prompt_version,
        model_name=model.model_name,
        source_digest=model.source_digest,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
