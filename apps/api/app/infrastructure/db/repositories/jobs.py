"""SQLAlchemy repository implementations for Job aggregates."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.jobs.entities import Job, JobVersion
from app.domain.jobs.ports import JobRepository
from app.domain.shared.clock import utc_now
from app.infrastructure.db.models.job import Job as JobModel
from app.infrastructure.db.models.job import JobVersion as JobVersionModel
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyJobRepository(JobRepository):
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def list_by_owner(self, owner_id: str) -> list[Job]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(JobModel)
                .where(JobModel.owner_id == owner_id)
                .order_by(JobModel.created_at, JobModel.id)
            ).all()
            return [_to_domain_job(row) for row in rows]

    def get(self, job_id: str) -> Job | None:
        with self._session_factory() as session:
            found = session.get(JobModel, job_id)
            return _to_domain_job(found) if found is not None else None

    def create_job(self, job: Job) -> None:
        with self._session_factory() as session:
            session.merge(_to_job_model(job))
            session.commit()

    def update_job(self, job: Job) -> None:
        with self._session_factory() as session:
            session.merge(_to_job_model(job))
            session.commit()

    def create_job_version(self, version: JobVersion) -> None:
        with self._session_factory() as session:
            session.merge(_to_job_version_model(version))
            session.commit()

    def update_job_version(self, version: JobVersion) -> None:
        with self._session_factory() as session:
            session.merge(_to_job_version_model(version))
            session.commit()

    def get_job_version(self, job_version_id: str) -> JobVersion | None:
        with self._session_factory() as session:
            found = session.get(JobVersionModel, job_version_id)
            return _to_domain_job_version(found) if found is not None else None

    @classmethod
    def clear_state(cls) -> None:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(delete(JobVersionModel))
            session.execute(delete(JobModel))
            session.commit()


def _to_job_model(job: Job) -> JobModel:
    return JobModel(
        id=job.job_id,
        owner_id=job.owner_id,
        actor_id=None,
        record_version=job.record_version,
        status=job.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=job.created_at,
        updated_at=job.updated_at,
        title=job.title,
        company=job.company,
        department=job.department,
        application_status=job.application_status,
        current_version_id=job.current_version_id,
        archived_at=job.archived_at,
    )


def _to_domain_job(model: JobModel) -> Job:
    assert model.current_version_id is not None
    return Job(
        job_id=model.id,
        owner_id=model.owner_id,
        title=model.title,
        company=model.company,
        department=model.department,
        application_status=model.application_status,
        status=model.status,
        current_version_id=model.current_version_id,
        record_version=model.record_version,
        created_at=model.created_at,
        updated_at=model.updated_at,
        archived_at=model.archived_at,
    )


def _to_job_version_model(version: JobVersion) -> JobVersionModel:
    created_at = version.created_at or utc_now()
    return JobVersionModel(
        id=version.job_version_id,
        owner_id=version.owner_id,
        actor_id=None,
        record_version=1,
        status=version.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=created_at,
        updated_at=created_at,
        job_id=version.job_id,
        version_number=version.version_number,
        responsibilities=list(version.responsibilities),
        requirements=list(version.requirements),
        other_notes=version.other_notes,
    )


def _to_domain_job_version(model: JobVersionModel) -> JobVersion:
    return JobVersion(
        job_version_id=model.id,
        owner_id=model.owner_id,
        job_id=model.job_id,
        version_number=model.version_number,
        responsibilities=list(model.responsibilities),
        requirements=list(model.requirements),
        other_notes=model.other_notes,
        status=model.status,
        created_at=model.created_at,
    )
