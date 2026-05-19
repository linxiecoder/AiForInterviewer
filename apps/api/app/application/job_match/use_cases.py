"""Job match application use cases."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from app.application.common.result import ApplicationResult
from app.application.job_match.commands import CreateJobMatchAnalysisCommand
from app.application.job_match.entities import JobMatchAnalysis
from app.application.job_match.ports import (
    JobMatchAnalyzer,
    JobMatchAnalyzerOutput,
    JobMatchAnalyzerUnavailableError,
    JobMatchRepository,
)
from app.application.job_match.queries import GetJobMatchAnalysisQuery, GetLatestJobMatchAnalysisQuery
from app.application.resumes.ports import ResumeRepository
from app.domain.bindings.ports import BindingRepository
from app.domain.jobs.ports import JobRepository
from app.domain.resumes.entities import ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.schemas.job_match import (
    JobMatchContractValidationError,
    JobMatchResultPayload,
    JobMatchSourceBundle,
    JobRequirementChunk,
    ResumeChunk,
    compute_source_digest,
    make_source_chunk_id,
    validate_job_match_result_payload,
)


SCORE_RULE_VERSION = "job_match.v1"
EXPLICIT_TEST_BUILDER_PROMPT_VERSION = "explicit_job_match_test_builder.v1"
EXPLICIT_TEST_BUILDER_MODEL_NAME = "explicit_job_match_test_builder"
COMPLETED_STATUS = "completed"

ResultBuilder = Callable[[JobMatchSourceBundle], JobMatchResultPayload | dict[str, Any]]


class JobMatchUseCases:
    def __init__(
        self,
        *,
        job_match_repository: JobMatchRepository,
        binding_repository: BindingRepository,
        resume_repository: ResumeRepository,
        job_repository: JobRepository,
        job_match_analyzer: JobMatchAnalyzer | None = None,
        result_builder: ResultBuilder | None = None,
    ) -> None:
        self._job_match_repository = job_match_repository
        self._binding_repository = binding_repository
        self._resume_repository = resume_repository
        self._job_repository = job_repository
        self._job_match_analyzer = job_match_analyzer
        self._result_builder = result_builder

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="job_match_skeleton")

    def create(self, command: CreateJobMatchAnalysisCommand) -> ApplicationResult[JobMatchAnalysis]:
        binding = self._binding_repository.get(command.binding_id)
        if binding is None or binding.owner_id != command.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Binding not found")
            )
        if binding.status != "active":
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Binding must be active")
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

        job = self._job_repository.get(binding.job_id)
        job_version = self._job_repository.get_job_version(binding.job_version_id)
        if job is None or job.owner_id != command.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job not found")
            )
        if (
            job_version is None
            or job_version.owner_id != command.owner_id
            or job_version.job_id != binding.job_id
        ):
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job version not found")
            )

        try:
            source_bundle = build_source_bundle(
                resume_version=resume_version,
                job_version_id=binding.job_version_id,
                job_requirements=job_version.requirements,
                job_responsibilities=job_version.responsibilities,
                job_other_notes=job_version.other_notes,
            )
            analysis_output = self._analyze_source_bundle(source_bundle)
            payload = validate_job_match_result_payload(
                analysis_output.payload,
                source_bundle,
            )
        except JobMatchAnalyzerUnavailableError as exc:
            return ApplicationResult(
                error=DomainError(
                    code="provider_unavailable",
                    message="岗位匹配分析模型服务不可用",
                    details={"reason": str(exc)},
                )
            )
        except (JobMatchContractValidationError, ValidationError, ValueError) as exc:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="岗位匹配分析结果校验失败",
                    details={"reason": str(exc)},
                )
            )

        now = utc_now()
        analysis = JobMatchAnalysis(
            analysis_id=generate_resource_id(ResourceIdPrefix.SCORE),
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            binding_id=binding.binding_id,
            resume_id=binding.resume_id,
            resume_version_id=binding.resume_version_id,
            job_id=binding.job_id,
            job_version_id=binding.job_version_id,
            status=COMPLETED_STATUS,
            overall_score=payload.overall_score,
            overall_level=str(payload.overall_level),
            confidence=str(payload.confidence),
            result_payload_json=payload.model_dump(mode="json"),
            markdown_report_text=payload.markdown_report,
            score_rule_version=SCORE_RULE_VERSION,
            prompt_version=analysis_output.prompt_version,
            model_name=analysis_output.model_name,
            source_digest=source_bundle.source_digest,
            created_at=now,
            updated_at=now,
        )
        self._job_match_repository.add(analysis)
        return ApplicationResult(value=analysis)

    def get(self, query: GetJobMatchAnalysisQuery) -> ApplicationResult[JobMatchAnalysis]:
        analysis = self._job_match_repository.get(query.analysis_id)
        if analysis is None or analysis.owner_id != query.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job match analysis not found")
            )
        return ApplicationResult(value=analysis)

    def get_latest(self, query: GetLatestJobMatchAnalysisQuery) -> ApplicationResult[JobMatchAnalysis]:
        analysis = self._job_match_repository.get_latest_by_binding(
            query.owner_id,
            query.binding_id,
        )
        if analysis is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job match analysis not found")
            )
        return ApplicationResult(value=analysis)

    def _analyze_source_bundle(self, source_bundle: JobMatchSourceBundle) -> JobMatchAnalyzerOutput:
        if self._job_match_analyzer is not None:
            return self._job_match_analyzer.analyze(source_bundle)
        if self._result_builder is not None:
            return JobMatchAnalyzerOutput(
                payload=self._result_builder(source_bundle),
                prompt_version=EXPLICIT_TEST_BUILDER_PROMPT_VERSION,
                model_name=EXPLICIT_TEST_BUILDER_MODEL_NAME,
            )
        raise ValueError("job match analyzer is not configured")


def build_source_bundle(
    *,
    resume_version: ResumeVersion,
    job_version_id: str,
    job_requirements: list[str],
    job_responsibilities: list[str],
    job_other_notes: str | None,
) -> JobMatchSourceBundle:
    resume_chunks = _resume_chunks(resume_version)
    job_chunks = _job_requirement_chunks(
        job_version_id=job_version_id,
        requirements=job_requirements,
        responsibilities=job_responsibilities,
        other_notes=job_other_notes,
    )
    return JobMatchSourceBundle(
        resume_chunks=resume_chunks,
        job_requirement_chunks=job_chunks,
        source_digest=compute_source_digest(resume_chunks, job_chunks),
    )


def _resume_chunks(resume_version: ResumeVersion) -> list[ResumeChunk]:
    sections = _markdown_sections(resume_version.markdown_text)
    if not sections:
        sections = [("summary", resume_version.markdown_text)]
    return [
        ResumeChunk(
            chunk_id=make_source_chunk_id("resume", label, index),
            resume_version_id=resume_version.resume_version_id,
            section_label=label,
            text=text,
        )
        for index, (label, text) in enumerate(sections, start=1)
        if text.strip()
    ]


def _job_requirement_chunks(
    *,
    job_version_id: str,
    requirements: list[str],
    responsibilities: list[str],
    other_notes: str | None,
) -> list[JobRequirementChunk]:
    chunks: list[JobRequirementChunk] = []
    for index, requirement in enumerate([item for item in requirements if item.strip()], start=1):
        chunks.append(
            JobRequirementChunk(
                chunk_id=make_source_chunk_id("job", "requirement", index),
                job_version_id=job_version_id,
                requirement_type="requirement",
                text=requirement,
            )
        )
    for index, responsibility in enumerate([item for item in responsibilities if item.strip()], start=1):
        chunks.append(
            JobRequirementChunk(
                chunk_id=make_source_chunk_id("job", "responsibility", index),
                job_version_id=job_version_id,
                requirement_type="responsibility",
                text=responsibility,
            )
        )
    if other_notes and other_notes.strip():
        chunks.append(
            JobRequirementChunk(
                chunk_id=make_source_chunk_id("job", "note", 1),
                job_version_id=job_version_id,
                requirement_type="note",
                text=other_notes,
            )
        )
    return chunks


def _markdown_sections(markdown_text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    current_label = "summary"
    current_lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if current_lines:
                sections.append((current_label, current_lines))
                current_lines = []
            current_label = line.lstrip("#").strip() or "summary"
            continue
        current_lines.append(line)
    if current_lines:
        sections.append((current_label, current_lines))
    return [(label, "\n".join(lines)) for label, lines in sections]
