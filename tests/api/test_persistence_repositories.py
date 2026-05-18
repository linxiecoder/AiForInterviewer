from __future__ import annotations

from app.domain.bindings.entities import ResumeJobBinding
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume
from app.domain.shared.clock import utc_now
from app.domain.shared.refs import OwnerRef, VersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from tools.testing.temp_artifacts import ManagedTempArtifacts


def test_jobs_resumes_and_bindings_persist_across_sqlite_session_factory_rebuilds() -> None:
    temp_artifacts = ManagedTempArtifacts(test_id="api-persistence-repositories")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        db_url = f"sqlite+pysqlite:///{(workspace / 'persistence.sqlite').as_posix()}"
        settings = DbSettings(database_url=db_url)
        initialize_schema(settings)

        first_factory = build_session_factory(settings)
        owner_id = "usr_persistence_owner"
        now = utc_now()

        job_repo = SqlAlchemyJobRepository(first_factory)
        job_repo.create_job(
            Job(
                job_id="job_persisted",
                owner_id=owner_id,
                title="持久化岗位",
                company="ACME",
                department="Engineering",
                application_status="draft",
                status="active",
                current_version_id="job_ver_persisted",
                record_version=1,
                created_at=now,
                updated_at=now,
            )
        )
        job_repo.create_job_version(
            JobVersion(
                job_version_id="job_ver_persisted",
                owner_id=owner_id,
                job_id="job_persisted",
                version_number=1,
                responsibilities=["Build persistent API"],
                requirements=["SQLAlchemy"],
                other_notes="keep me",
                status="current",
                created_at=now,
            )
        )

        resume_repo = SqlAlchemyResumeRepository(first_factory)
        resume_repo.add(
            Resume(
                resume_id="res_persisted",
                owner_ref=OwnerRef(owner_id=owner_id),
                current_version_ref=VersionRef(
                    resource_type="resume",
                    resource_id="res_persisted",
                    version_id="res_ver_persisted",
                ),
                status="active",
                title="持久化简历",
                file_name="resume.md",
                created_at=now,
                updated_at=now,
            )
        )

        binding_repo = SqlAlchemyBindingRepository(first_factory)
        binding_repo.register_resume(
            owner_id=owner_id,
            resume_id="res_persisted",
            resume_version_id="res_ver_persisted",
        )
        binding_repo.add(
            ResumeJobBinding(
                binding_id="bind_persisted",
                owner_id=owner_id,
                resume_id="res_persisted",
                job_id="job_persisted",
                resume_version_id="res_ver_persisted",
                job_version_id="job_ver_persisted",
                status="active",
                record_version=1,
                created_at=now,
                updated_at=now,
            )
        )

        second_factory = build_session_factory(settings)

        reloaded_job_repo = SqlAlchemyJobRepository(second_factory)
        assert [item.job_id for item in reloaded_job_repo.list_by_owner(owner_id)] == ["job_persisted"]
        assert reloaded_job_repo.get_job_version("job_ver_persisted").requirements == ["SQLAlchemy"]

        reloaded_resume_repo = SqlAlchemyResumeRepository(second_factory)
        assert [item.resume_id for item in reloaded_resume_repo.list_by_owner(owner_id)] == ["res_persisted"]
        assert reloaded_resume_repo.get("res_persisted").file_name == "resume.md"

        reloaded_binding_repo = SqlAlchemyBindingRepository(second_factory)
        assert reloaded_binding_repo.get_resume_current_version(owner_id, "res_persisted") == "res_ver_persisted"
        assert [item.binding_id for item in reloaded_binding_repo.list_by_job(owner_id, "job_persisted")] == [
            "bind_persisted"
        ]
    finally:
        temp_artifacts.cleanup()
