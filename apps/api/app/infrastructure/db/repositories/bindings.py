"""SQLAlchemy repository implementations for resume-job bindings."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.bindings.entities import ResumeJobBinding
from app.domain.bindings.ports import BindingRepository
from app.domain.shared.clock import utc_now
from app.infrastructure.db.models.binding import ResumeJobBinding as BindingModel
from app.infrastructure.db.models.resume import Resume as ResumeModel
from app.infrastructure.db.repositories.base import SqlAlchemyRepository
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyBindingRepository(SqlAlchemyRepository, BindingRepository):
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        *,
        session: Session | None = None,
    ) -> None:
        super().__init__(session_factory, session=session)

    def get(self, binding_id: str) -> ResumeJobBinding | None:
        with self.session_scope() as session:
            binding = session.get(BindingModel, binding_id)
            return _to_domain_binding(binding) if binding is not None else None

    def add(self, binding: ResumeJobBinding) -> None:
        with self.session_scope(commit=True) as session:
            session.merge(_to_binding_model(binding))

    def update(self, binding: ResumeJobBinding) -> None:
        with self.session_scope(commit=True) as session:
            session.merge(_to_binding_model(binding))

    def list_by_owner(self, owner_id: str) -> list[ResumeJobBinding]:
        with self.session_scope() as session:
            rows = session.scalars(
                select(BindingModel)
                .where(BindingModel.owner_id == owner_id)
                .order_by(BindingModel.created_at, BindingModel.id)
            ).all()
            return [_to_domain_binding(row) for row in rows]

    def list_by_job(self, owner_id: str, job_id: str) -> list[ResumeJobBinding]:
        with self.session_scope() as session:
            rows = session.scalars(
                select(BindingModel)
                .where(BindingModel.owner_id == owner_id, BindingModel.job_id == job_id)
                .order_by(BindingModel.created_at, BindingModel.id)
            ).all()
            return [_to_domain_binding(row) for row in rows]

    def find_active_binding(self, owner_id: str, resume_id: str, job_id: str) -> ResumeJobBinding | None:
        with self.session_scope() as session:
            binding = session.scalar(
                select(BindingModel)
                .where(
                    BindingModel.owner_id == owner_id,
                    BindingModel.resume_id == resume_id,
                    BindingModel.job_id == job_id,
                    BindingModel.status == "active",
                )
                .order_by(BindingModel.created_at.desc(), BindingModel.id.desc())
            )
            if binding is not None:
                return _to_domain_binding(binding)
        return None

    def register_resume(self, owner_id: str, resume_id: str, resume_version_id: str) -> None:
        with self.session_scope(commit=True) as session:
            resume = session.get(ResumeModel, resume_id)
            now = utc_now()
            if resume is None:
                resume = ResumeModel(
                    id=resume_id,
                    owner_id=owner_id,
                    actor_id=None,
                    record_version=1,
                    status="active",
                    trace_ref_ids=None,
                    evidence_ref_ids=None,
                    created_at=now,
                    updated_at=now,
                    title=None,
                    file_name=None,
                    current_version_id=resume_version_id,
                )
            else:
                resume.current_version_id = resume_version_id
                resume.updated_at = now
            session.merge(resume)

    def get_resume_current_version(self, owner_id: str, resume_id: str) -> str | None:
        with self.session_scope() as session:
            resume = session.scalar(
                select(ResumeModel).where(
                    ResumeModel.id == resume_id,
                    ResumeModel.owner_id == owner_id,
                )
            )
            return resume.current_version_id if resume is not None else None

    @classmethod
    def clear_state(cls) -> None:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(delete(BindingModel))
            session.commit()


def _to_binding_model(binding: ResumeJobBinding) -> BindingModel:
    return BindingModel(
        id=binding.binding_id,
        owner_id=binding.owner_id,
        actor_id=None,
        record_version=binding.record_version,
        status=binding.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=binding.created_at,
        updated_at=binding.updated_at,
        resume_id=binding.resume_id,
        job_id=binding.job_id,
        resume_version_id=binding.resume_version_id,
        job_version_id=binding.job_version_id,
        unbound_at=binding.unbound_at,
        unbound_by=binding.unbound_by,
    )


def _to_domain_binding(model: BindingModel) -> ResumeJobBinding:
    return ResumeJobBinding(
        binding_id=model.id,
        owner_id=model.owner_id,
        resume_id=model.resume_id,
        job_id=model.job_id,
        resume_version_id=model.resume_version_id,
        job_version_id=model.job_version_id,
        status=model.status,
        record_version=model.record_version,
        created_at=model.created_at,
        updated_at=model.updated_at,
        unbound_at=model.unbound_at,
        unbound_by=model.unbound_by,
    )
