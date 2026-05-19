"""SQLAlchemy repository implementation for resumes."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.resumes.ports import ResumeRepository
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.refs import OwnerRef, ResourceRef, VersionRef
from app.infrastructure.db.models.resume import Resume as ResumeModel
from app.infrastructure.db.models.resume import ResumeVersion as ResumeVersionModel
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyResumeRepository(ResumeRepository):
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def get(self, resume_id: str) -> Resume | None:
        with self._session_factory() as session:
            found = session.get(ResumeModel, resume_id)
            return _to_domain_resume(found) if found is not None else None

    def get_version(self, resume_version_id: str) -> ResumeVersion | None:
        with self._session_factory() as session:
            found = session.get(ResumeVersionModel, resume_version_id)
            return _to_domain_resume_version(found) if found is not None else None

    def get_ref(self, resume_id: str) -> ResourceRef | None:
        with self._session_factory() as session:
            found = session.get(ResumeModel, resume_id)
        if found is None:
            return None
        return ResourceRef(resource_type="resume", resource_id=resume_id)

    def list_by_owner(self, owner_id: str) -> list[Resume]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(ResumeModel)
                .where(ResumeModel.owner_id == owner_id)
                .order_by(ResumeModel.created_at, ResumeModel.id)
            ).all()
            return [_to_domain_resume(row) for row in rows]

    def add(self, resume: Resume) -> None:
        with self._session_factory() as session:
            session.merge(_to_resume_model(resume))
            session.commit()

    def add_version(self, version: ResumeVersion) -> None:
        with self._session_factory() as session:
            session.merge(_to_resume_version_model(version))
            session.commit()

    def create_with_version(self, resume: Resume, version: ResumeVersion) -> None:
        with self._session_factory() as session:
            session.merge(_to_resume_model(resume))
            session.merge(_to_resume_version_model(version))
            session.commit()

    @classmethod
    def clear_state(cls) -> None:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(delete(ResumeVersionModel))
            session.execute(delete(ResumeModel))
            session.commit()


def _to_resume_model(resume: Resume) -> ResumeModel:
    created_at = resume.created_at or utc_now()
    updated_at = resume.updated_at or created_at
    return ResumeModel(
        id=resume.resume_id,
        owner_id=resume.owner_ref.owner_id,
        actor_id=None,
        record_version=1,
        status=resume.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=created_at,
        updated_at=updated_at,
        title=resume.title,
        file_name=resume.file_name,
        current_version_id=resume.current_version_ref.version_id,
    )


def _to_domain_resume(model: ResumeModel) -> Resume:
    return Resume(
        resume_id=model.id,
        owner_ref=OwnerRef(owner_id=model.owner_id),
        current_version_ref=VersionRef(
            resource_type="resume",
            resource_id=model.id,
            version_id=model.current_version_id or "",
        ),
        status=model.status,
        title=model.title,
        file_name=model.file_name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_resume_version_model(version: ResumeVersion) -> ResumeVersionModel:
    created_at = version.created_at or utc_now()
    return ResumeVersionModel(
        id=version.resume_version_id,
        owner_id=version.owner_id,
        actor_id=None,
        record_version=1,
        status=version.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=created_at,
        updated_at=created_at,
        resume_id=version.resume_id,
        version_number=version.version_number,
        markdown_text=version.markdown_text,
    )


def _to_domain_resume_version(model: ResumeVersionModel) -> ResumeVersion:
    return ResumeVersion(
        resume_version_id=model.id,
        owner_id=model.owner_id,
        resume_id=model.resume_id,
        version_number=model.version_number,
        markdown_text=model.markdown_text,
        status=model.status,
        created_at=model.created_at,
    )
