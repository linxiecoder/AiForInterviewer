from __future__ import annotations

import pytest

from app.domain.bindings.entities import ResumeJobBinding
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.refs import OwnerRef, VersionRef
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from tools.testing.temp_artifacts import ManagedTempArtifacts


def test_uow_commits_multiple_repository_writes_together() -> None:
    temp_artifacts = ManagedTempArtifacts(test_id="api-uow-commit")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        session_factory = _sqlite_session_factory(workspace / "uow-commit.sqlite")
        owner_id = "usr_uow_commit"
        now = utc_now()

        with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
            uow.jobs.create_job(_job(owner_id, now))
            uow.jobs.create_job_version(_job_version(owner_id, now))
            uow.resumes.create_with_version(_resume(owner_id, now), _resume_version(owner_id, now))
            uow.bindings.add(_binding(owner_id, now))
            uow.commit()

        job_repo = SqlAlchemyJobRepository(session_factory=session_factory)
        assert [item.job_id for item in job_repo.list_by_owner(owner_id)] == ["job_uow"]
        assert job_repo.get_job_version("job_ver_uow") is not None
    finally:
        temp_artifacts.cleanup()


def test_uow_rolls_back_when_context_exits_without_commit() -> None:
    temp_artifacts = ManagedTempArtifacts(test_id="api-uow-rollback")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        session_factory = _sqlite_session_factory(workspace / "uow-rollback.sqlite")
        owner_id = "usr_uow_rollback"

        with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
            uow.jobs.create_job(_job(owner_id, utc_now()))

        job_repo = SqlAlchemyJobRepository(session_factory=session_factory)
        assert job_repo.list_by_owner(owner_id) == []
    finally:
        temp_artifacts.cleanup()


def test_uow_rolls_back_when_exception_occurs() -> None:
    temp_artifacts = ManagedTempArtifacts(test_id="api-uow-exception")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        session_factory = _sqlite_session_factory(workspace / "uow-exception.sqlite")
        owner_id = "usr_uow_exception"

        with pytest.raises(RuntimeError):
            with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
                uow.jobs.create_job(_job(owner_id, utc_now()))
                raise RuntimeError("force rollback")

        job_repo = SqlAlchemyJobRepository(session_factory=session_factory)
        assert job_repo.list_by_owner(owner_id) == []
    finally:
        temp_artifacts.cleanup()


def _sqlite_session_factory(path):
    settings = DbSettings(database_url=f"sqlite+pysqlite:///{path.as_posix()}")
    session_factory = build_session_factory(settings)
    initialize_schema(session_factory=session_factory)
    return session_factory


def _job(owner_id: str, now) -> Job:
    return Job(
        job_id="job_uow",
        owner_id=owner_id,
        title="UoW Job",
        company="ACME",
        department="Engineering",
        application_status="draft",
        status="active",
        current_version_id="job_ver_uow",
        record_version=1,
        created_at=now,
        updated_at=now,
    )


def _job_version(owner_id: str, now) -> JobVersion:
    return JobVersion(
        job_version_id="job_ver_uow",
        owner_id=owner_id,
        job_id="job_uow",
        version_number=1,
        responsibilities=["Build UoW"],
        requirements=["SQLAlchemy"],
        other_notes=None,
        status="current",
        created_at=now,
    )


def _resume(owner_id: str, now) -> Resume:
    return Resume(
        resume_id="res_uow",
        owner_ref=OwnerRef(owner_id=owner_id),
        current_version_ref=VersionRef(
            resource_type="resume",
            resource_id="res_uow",
            version_id="res_ver_uow",
        ),
        status="active",
        title="UoW Resume",
        file_name="resume.md",
        created_at=now,
        updated_at=now,
    )


def _resume_version(owner_id: str, now) -> ResumeVersion:
    return ResumeVersion(
        resume_version_id="res_ver_uow",
        owner_id=owner_id,
        resume_id="res_uow",
        version_number=1,
        markdown_text="# Resume",
        status="current",
        created_at=now,
    )


def _binding(owner_id: str, now) -> ResumeJobBinding:
    return ResumeJobBinding(
        binding_id="bind_uow",
        owner_id=owner_id,
        resume_id="res_uow",
        job_id="job_uow",
        resume_version_id="res_ver_uow",
        job_version_id="job_ver_uow",
        status="active",
        record_version=1,
        created_at=now,
        updated_at=now,
    )
