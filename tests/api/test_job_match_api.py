from __future__ import annotations

from fastapi import FastAPI

from app.api.deps import get_db_session_factory, get_job_match_analyzer, require_authenticated_actor
from app.api.errors import ApiHttpError, api_http_error_handler
from app.api.v1.job_match_analyses import router as job_match_router
from app.application.job_match.commands import CreateJobMatchAnalysisCommand
from app.application.job_match.use_cases import JobMatchUseCases, build_source_bundle
from app.application.job_match.ports import JobMatchAnalyzerOutput, JobMatchAnalyzerUnavailableError
from app.domain.auth.entities import CurrentActor
from app.domain.bindings.entities import ResumeJobBinding
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.domain.shared.refs import OwnerRef, VersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.job_match import SqlAlchemyJobMatchAnalysisRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from tests.fakes.llm_transport import FakeLlmTransport
from app.infrastructure.llm.job_match import LlmJobMatchAnalyzer
from app.infrastructure.llm.types import LlmTransportResult
from app.schemas.job_match import DimensionScore, JobMatchResultPayload, MatchedRequirement, ResumeEvidence, SourceEvidenceRef
from app.schemas.job_match import validate_job_match_result_payload
from tests.api.asgi_client import call_json


OWNER_A = "usr_job_match_owner_a"
OWNER_B = "usr_job_match_owner_b"
ACTOR_A = CurrentActor(
    actor_id=OWNER_A,
    owner_id=OWNER_A,
    roles=("user",),
    email_normalized="owner-a@example.com",
    display_name="Owner A",
)
ACTOR_B = CurrentActor(
    actor_id=OWNER_B,
    owner_id=OWNER_B,
    roles=("user",),
    email_normalized="owner-b@example.com",
    display_name="Owner B",
)


class _UnavailableAnalyzer:
    def analyze(self, _source_bundle):
        raise JobMatchAnalyzerUnavailableError("LLM provider test unavailable")


class _LooseShapeTransport:
    status = "loose_shape_test"

    def generate(self, request):
        resume_chunk_id = request.evidence_bundle["resume_chunks"][0]["chunk_id"]
        return LlmTransportResult(
            result={
                "prompt_version": "loose-shape-test.v1",
                "model_name": "deepseek-test",
                "job_match_result_payload": {
                    "overall_score": 76,
                    "overall_level": "medium_match",
                    "confidence": "medium",
                    "summary": "大模型判断候选人的后端经验与岗位要求中度匹配。",
                    "dimension_scores": {
                        "requirement_alignment": 18,
                        "experience_evidence": 23,
                        "skill_coverage": 12,
                        "gap_risk": 13,
                        "readiness_actions": 8,
                    },
                    "matched_requirements": ["FastAPI 后端开发经验与岗位要求相关"],
                    "missing_requirements": ["需要继续确认 Linux 与 Shell 经验"],
                    "resume_evidence": {"FastAPI 项目经验": [resume_chunk_id]},
                    "risk_flags": ["Linux 与 Shell 经验证据不够明确"],
                    "interview_focus": "确认候选人在后端项目中的真实负责范围。",
                    "suggested_questions": "请说明你在 FastAPI 项目中的具体职责。",
                    "markdown_report": "# 岗位匹配分析\n\n大模型已完成分析。",
                },
            },
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_loose_shape",),
            evidence_refs=("trace_loose_evidence",),
        )


class _WeightedSourceCoverageTransport:
    status = "weighted_source_coverage_test"

    def __init__(self, matched_job_chunk_ids: list[str]) -> None:
        self._matched_job_chunk_ids = tuple(matched_job_chunk_ids)

    def generate(self, request):
        resume_chunk_id = request.evidence_bundle["resume_chunks"][0]["chunk_id"]
        return LlmTransportResult(
            result={
                "prompt_version": "weighted-source-test.v1",
                "model_name": "deepseek-test",
                "job_match_result_payload": {
                    "overall_score": 100,
                    "overall_level": "strong_match",
                    "confidence": "medium",
                    "summary": "测试模型输出：用于验证岗位来源权重。",
                    "dimension_scores": {
                        "requirement_alignment": 30,
                        "experience_evidence": 25,
                        "skill_coverage": 20,
                        "gap_risk": 15,
                        "readiness_actions": 10,
                    },
                    "matched_requirements": [
                        {
                            "requirement_chunk_id": chunk_id,
                            "resume_evidence_chunk_ids": [resume_chunk_id],
                            "rationale": "测试模型输出：该岗位项有简历证据支撑。",
                            "confidence": "medium",
                        }
                        for chunk_id in self._matched_job_chunk_ids
                    ],
                    "missing_requirements": [],
                    "resume_evidence": [
                        {
                            "chunk_id": resume_chunk_id,
                            "summary": "测试模型输出：主要简历证据。",
                            "confidence": "medium",
                        }
                    ],
                    "risk_flags": [],
                    "interview_focus": ["测试模型输出：继续核验关键缺口。"],
                    "suggested_questions": ["测试模型输出：请说明最相关的项目证据。"],
                    "markdown_report": "# 岗位匹配分析\n\n测试模型输出。",
                },
            },
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_weighted_source",),
            evidence_refs=("trace_weighted_source_evidence",),
        )


class _RecordingAnalyzer:
    prompt_version = "job-match-preservation-test.v1"
    model_name = "job-match-preservation-analyzer"

    def __init__(self, *, invalid_evidence_ref: bool = False) -> None:
        self.calls = 0
        self.source_digest_seen: str | None = None
        self.invalid_evidence_ref = invalid_evidence_ref

    def analyze(self, source_bundle):
        self.calls += 1
        self.source_digest_seen = source_bundle.source_digest
        result = _test_result_payload(source_bundle)
        result.summary = "测试 analyzer contract：仅验证契约落库，不声明真实 AI 质量。"
        if self.invalid_evidence_ref:
            result.dimension_scores[0].supporting_evidence = [
                SourceEvidenceRef(chunk_id="resume:missing:001")
            ]
        return JobMatchAnalyzerOutput(
            payload=result,
            prompt_version=self.prompt_version,
            model_name=self.model_name,
        )


def test_create_analysis_persists_completed_result_payload_and_source_digest() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    app = _isolated_job_match_app(session_factory, ACTOR_A)

    status_code, body = call_json(
        app,
        "/api/v1/job-match-analyses",
        "POST",
        json_body={"resume_job_binding_id": binding_id},
    )

    assert status_code == 200
    assert body["resource_type"] == "job_match_analysis"
    data = body["data"]
    assert data["status"] == "completed"
    assert data["resume_job_binding_id"] == binding_id
    assert data["overall_score"] == data["result_payload"]["overall_score"]
    assert data["result_payload"]["overall_level"] in {
        "strong_match",
        "medium_match",
        "weak_match",
    }
    assert data["source_digest"].startswith("sha256:")
    assert data["model_name"] == "fake_llm_job_match_v1"
    assert data["prompt_version"] == "P-JOBMATCH-001+P-JOBMATCH-002+P-JOBMATCH-003.v1"
    assert data["overall_score"] != 82
    assert "LLM" in data["result_payload"]["summary"]
    assert data["result_payload"]["interview_focus"] == ["围绕匹配度最高的证据追问候选人的真实参与深度。"]
    assert data["result_payload"]["suggested_questions"] == ["请结合岗位要求说明这段经历中最能证明匹配度的具体产出。"]
    assert "LLM" in data["result_payload"]["dimension_scores"][0]["rationale"]

    stored = SqlAlchemyJobMatchAnalysisRepository(session_factory).get(data["analysis_id"])
    assert stored is not None
    assert stored.result_payload_json["overall_score"] == data["overall_score"]
    assert stored.source_digest == data["source_digest"]


def test_create_analysis_uses_analyzer_contract_and_preserves_readback_payload() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    analyzer = _RecordingAnalyzer()
    app = _isolated_job_match_app(session_factory, ACTOR_A, job_match_analyzer=analyzer)

    status_code, body = call_json(
        app,
        "/api/v1/job-match-analyses",
        "POST",
        json_body={"resume_job_binding_id": binding_id},
    )

    assert status_code == 200
    assert body["resource_type"] == "job_match_analysis"
    data = body["data"]
    assert analyzer.calls == 1
    assert analyzer.source_digest_seen == data["source_digest"]
    assert data["status"] == "completed"
    assert data["overall_score"] == data["result_payload"]["overall_score"] == 82
    assert data["prompt_version"] == _RecordingAnalyzer.prompt_version
    assert data["model_name"] == _RecordingAnalyzer.model_name
    assert (
        data["result_payload"]["summary"]
        == "测试 analyzer contract：仅验证契约落库，不声明真实 AI 质量。"
    )
    assert "ai_task_id" not in data

    stored = SqlAlchemyJobMatchAnalysisRepository(session_factory).get(
        data["analysis_id"]
    )
    assert stored is not None
    assert stored.result_payload_json == data["result_payload"]
    assert stored.markdown_report_text == data["markdown_report_text"]
    assert stored.prompt_version == data["prompt_version"]
    assert stored.model_name == data["model_name"]
    assert stored.source_digest == data["source_digest"]

    read_status, read_body = call_json(
        app,
        f"/api/v1/job-match-analyses/{data['analysis_id']}",
    )
    latest_status, latest_body = call_json(
        app,
        f"/api/v1/job-match-analyses/latest?resume_job_binding_id={binding_id}",
    )
    assert read_status == 200
    assert latest_status == 200
    assert read_body["data"]["result_payload"] == data["result_payload"]
    assert latest_body["data"]["result_payload"] == data["result_payload"]
    assert latest_body["data"]["analysis_id"] == data["analysis_id"]


def test_create_analysis_requires_llm_analyzer_or_explicit_test_builder() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    use_cases = JobMatchUseCases(
        job_match_repository=SqlAlchemyJobMatchAnalysisRepository(session_factory),
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        resume_repository=SqlAlchemyResumeRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
    )

    result = use_cases.create(
        CreateJobMatchAnalysisCommand(
            owner_id=OWNER_A,
            actor_id=OWNER_A,
            binding_id=binding_id,
        )
    )

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "validation_failed"
    assert result.error.details == {"reason": "job match analyzer is not configured"}


def test_create_analysis_maps_llm_provider_unavailable_to_domain_error() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    use_cases = JobMatchUseCases(
        job_match_repository=SqlAlchemyJobMatchAnalysisRepository(session_factory),
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        resume_repository=SqlAlchemyResumeRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
        job_match_analyzer=_UnavailableAnalyzer(),
    )

    result = use_cases.create(
        CreateJobMatchAnalysisCommand(
            owner_id=OWNER_A,
            actor_id=OWNER_A,
            binding_id=binding_id,
        )
    )

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "provider_unavailable"
    assert result.error.details == {"reason": "LLM provider test unavailable"}


def test_llm_analyzer_normalizes_loose_provider_payload_shapes() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    binding = SqlAlchemyBindingRepository(session_factory).get(binding_id)
    assert binding is not None
    resume_version = SqlAlchemyResumeRepository(session_factory).get_version(binding.resume_version_id)
    job_version = SqlAlchemyJobRepository(session_factory).get_job_version(binding.job_version_id)
    assert resume_version is not None
    assert job_version is not None
    source_bundle = build_source_bundle(
        resume_version=resume_version,
        job_version_id=binding.job_version_id,
        job_requirements=job_version.requirements,
        job_responsibilities=job_version.responsibilities,
        job_other_notes=job_version.other_notes,
    )

    output = LlmJobMatchAnalyzer(_LooseShapeTransport()).analyze(source_bundle)
    validated = validate_job_match_result_payload(output.payload, source_bundle)

    assert validated.overall_score == 72
    assert [score.key for score in validated.dimension_scores] == [
        "requirement_alignment",
        "experience_evidence",
        "skill_coverage",
        "gap_risk",
        "readiness_actions",
    ]
    assert validated.matched_requirements[0].requirement_chunk_id.startswith("job:")
    assert validated.resume_evidence[0].chunk_id.startswith("resume:")
    assert validated.interview_focus == ["确认候选人在后端项目中的真实负责范围。"]
    assert validated.suggested_questions == ["请说明你在 FastAPI 项目中的具体职责。"]


def test_llm_analyzer_fills_missing_entries_for_uncovered_job_chunks() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    binding = SqlAlchemyBindingRepository(session_factory).get(binding_id)
    assert binding is not None
    resume_version = SqlAlchemyResumeRepository(session_factory).get_version(binding.resume_version_id)
    job_version = SqlAlchemyJobRepository(session_factory).get_job_version(binding.job_version_id)
    assert resume_version is not None
    assert job_version is not None
    source_bundle = build_source_bundle(
        resume_version=resume_version,
        job_version_id=binding.job_version_id,
        job_requirements=job_version.requirements,
        job_responsibilities=job_version.responsibilities,
        job_other_notes=job_version.other_notes,
    )

    output = LlmJobMatchAnalyzer(_LooseShapeTransport()).analyze(source_bundle)
    validated = validate_job_match_result_payload(output.payload, source_bundle)

    covered_job_chunk_ids = {
        match.requirement_chunk_id for match in validated.matched_requirements
    } | {
        missing.requirement_chunk_id
        for missing in validated.missing_requirements
        if missing.requirement_chunk_id is not None
    }
    expected_job_chunk_ids = {
        chunk.chunk_id for chunk in source_bundle.job_requirement_chunks
    }
    gap_risk = next(score for score in validated.dimension_scores if score.key == "gap_risk")
    readiness_actions = next(score for score in validated.dimension_scores if score.key == "readiness_actions")

    assert covered_job_chunk_ids == expected_job_chunk_ids
    assert gap_risk.score <= 11
    assert readiness_actions.score <= 8
    assert any("未明确覆盖" in missing.reason for missing in validated.missing_requirements)
    assert any("未明确覆盖" in gap for gap in gap_risk.gaps)


def test_llm_analyzer_weights_requirement_sources_more_than_responsibilities() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    binding = SqlAlchemyBindingRepository(session_factory).get(binding_id)
    assert binding is not None
    resume_version = SqlAlchemyResumeRepository(session_factory).get_version(binding.resume_version_id)
    job_version = SqlAlchemyJobRepository(session_factory).get_job_version(binding.job_version_id)
    assert resume_version is not None
    assert job_version is not None
    source_bundle = build_source_bundle(
        resume_version=resume_version,
        job_version_id=binding.job_version_id,
        job_requirements=job_version.requirements,
        job_responsibilities=job_version.responsibilities,
        job_other_notes=job_version.other_notes,
    )
    chunk_ids_by_type = {
        chunk.requirement_type: chunk.chunk_id
        for chunk in source_bundle.job_requirement_chunks
    }

    responsibility_missing = validate_job_match_result_payload(
        LlmJobMatchAnalyzer(
            _WeightedSourceCoverageTransport(
                [
                    chunk_ids_by_type["requirement"],
                    chunk_ids_by_type["note"],
                ]
            )
        ).analyze(source_bundle).payload,
        source_bundle,
    )
    requirement_missing = validate_job_match_result_payload(
        LlmJobMatchAnalyzer(
            _WeightedSourceCoverageTransport(
                [
                    chunk_ids_by_type["responsibility"],
                    chunk_ids_by_type["note"],
                ]
            )
        ).analyze(source_bundle).payload,
        source_bundle,
    )

    responsibility_requirement_score = next(
        score for score in responsibility_missing.dimension_scores
        if score.key == "requirement_alignment"
    )
    requirement_requirement_score = next(
        score for score in requirement_missing.dimension_scores
        if score.key == "requirement_alignment"
    )
    responsibility_gap_score = next(
        score for score in responsibility_missing.dimension_scores
        if score.key == "gap_risk"
    )
    requirement_gap_score = next(
        score for score in requirement_missing.dimension_scores
        if score.key == "gap_risk"
    )

    assert responsibility_missing.overall_score > requirement_missing.overall_score
    assert responsibility_requirement_score.score > requirement_requirement_score.score
    assert responsibility_gap_score.score > requirement_gap_score.score


def test_get_analysis_by_id_is_owner_scoped() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    owner_a_app = _isolated_job_match_app(session_factory, ACTOR_A)
    owner_b_app = _isolated_job_match_app(session_factory, ACTOR_B)

    status_code, body = call_json(
        owner_a_app,
        "/api/v1/job-match-analyses",
        "POST",
        json_body={"resume_job_binding_id": binding_id},
    )
    assert status_code == 200
    analysis_id = body["data"]["analysis_id"]

    status_code, body = call_json(
        owner_a_app,
        f"/api/v1/job-match-analyses/{analysis_id}",
    )
    assert status_code == 200
    assert body["data"]["analysis_id"] == analysis_id

    status_code, body = call_json(
        owner_b_app,
        f"/api/v1/job-match-analyses/{analysis_id}",
    )
    assert status_code == 404
    assert body["error"]["code"] == "not_found_or_inaccessible"


def test_latest_by_binding_returns_newest_analysis() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    app = _isolated_job_match_app(session_factory, ACTOR_A)

    first_status, first_body = call_json(
        app,
        "/api/v1/job-match-analyses",
        "POST",
        json_body={"resume_job_binding_id": binding_id},
    )
    second_status, second_body = call_json(
        app,
        "/api/v1/job-match-analyses",
        "POST",
        json_body={"resume_job_binding_id": binding_id},
    )
    assert first_status == 200
    assert second_status == 200

    status_code, body = call_json(
        app,
        f"/api/v1/job-match-analyses/latest?resume_job_binding_id={binding_id}",
    )

    assert status_code == 200
    assert body["data"]["analysis_id"] == second_body["data"]["analysis_id"]
    assert body["data"]["analysis_id"] != first_body["data"]["analysis_id"]


def test_invalid_result_payload_is_not_saved_as_completed() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    repository = SqlAlchemyJobMatchAnalysisRepository(session_factory)

    def _invalid_result(source_bundle):
        result = _test_result_payload(source_bundle)
        result.dimension_scores[0].supporting_evidence = [
            SourceEvidenceRef(chunk_id="resume:missing:001")
        ]
        return result

    use_cases = _job_match_use_cases(session_factory, result_builder=_invalid_result)

    result = use_cases.create(
        CreateJobMatchAnalysisCommand(
            owner_id=OWNER_A,
            actor_id=OWNER_A,
            binding_id=binding_id,
        )
    )

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "validation_failed"
    assert repository.get_latest_by_binding(OWNER_A, binding_id) is None


def test_invalid_analyzer_payload_returns_validation_failed_without_persistence() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    analyzer = _RecordingAnalyzer(invalid_evidence_ref=True)
    app = _isolated_job_match_app(session_factory, ACTOR_A, job_match_analyzer=analyzer)
    repository = SqlAlchemyJobMatchAnalysisRepository(session_factory)

    status_code, body = call_json(
        app,
        "/api/v1/job-match-analyses",
        "POST",
        json_body={"resume_job_binding_id": binding_id},
    )

    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"
    assert body["error"]["retryable"] is False
    assert "unknown chunk_id" in body["error"]["details"]["reason"]
    assert analyzer.calls == 1
    assert repository.get_latest_by_binding(OWNER_A, binding_id) is None

    latest_status, latest_body = call_json(
        app,
        f"/api/v1/job-match-analyses/latest?resume_job_binding_id={binding_id}",
    )
    assert latest_status == 404
    assert latest_body["error"]["code"] == "not_found_or_inaccessible"


def test_explicit_test_result_passes_slice_1_validation() -> None:
    session_factory = _session_factory()
    binding_id = _seed_match_sources(session_factory, OWNER_A)
    binding = SqlAlchemyBindingRepository(session_factory).get(binding_id)
    assert binding is not None
    resume_version = SqlAlchemyResumeRepository(session_factory).get_version(binding.resume_version_id)
    job_version = SqlAlchemyJobRepository(session_factory).get_job_version(binding.job_version_id)
    assert resume_version is not None
    assert job_version is not None

    source_bundle = build_source_bundle(
        resume_version=resume_version,
        job_version_id=binding.job_version_id,
        job_requirements=job_version.requirements,
        job_responsibilities=job_version.responsibilities,
        job_other_notes=job_version.other_notes,
    )
    result_payload = _test_result_payload(source_bundle)

    validated = validate_job_match_result_payload(result_payload, source_bundle)

    assert validated.overall_score == 82
    assert validated.matched_requirements[0].requirement_chunk_id.startswith("job:")


def test_job_match_slice_2a_does_not_depend_on_aitask_or_score_result() -> None:
    import app.api.v1.job_match_analyses as api_module
    import app.application.job_match.use_cases as use_case_module
    import app.infrastructure.db.models.job_match as model_module
    import app.infrastructure.db.repositories.job_match as repository_module

    imported_modules = {
        value.__name__
        for module in (api_module, use_case_module, model_module, repository_module)
        for value in module.__dict__.values()
        if getattr(value, "__name__", None)
    }

    assert "AiTask" not in imported_modules
    assert "AiTaskResult" not in imported_modules
    assert "ScoreResult" not in imported_modules


def _session_factory():
    settings = DbSettings(database_url="sqlite+pysqlite:///:memory:")
    session_factory = build_session_factory(settings)
    initialize_schema(session_factory=session_factory)
    return session_factory


def _isolated_job_match_app(
    session_factory, actor: CurrentActor, *, job_match_analyzer=None
) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(ApiHttpError, api_http_error_handler)
    app.include_router(job_match_router, prefix="/api/v1")

    async def _actor_override() -> CurrentActor:
        return actor

    async def _session_factory_override():
        return session_factory

    async def _job_match_analyzer_override():
        return (
            job_match_analyzer
            if job_match_analyzer is not None
            else LlmJobMatchAnalyzer(FakeLlmTransport())
        )

    app.dependency_overrides[require_authenticated_actor] = _actor_override
    app.dependency_overrides[get_db_session_factory] = _session_factory_override
    app.dependency_overrides[get_job_match_analyzer] = _job_match_analyzer_override
    return app


def _job_match_use_cases(session_factory, *, result_builder=None) -> JobMatchUseCases:
    return JobMatchUseCases(
        job_match_repository=SqlAlchemyJobMatchAnalysisRepository(session_factory),
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        resume_repository=SqlAlchemyResumeRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
        result_builder=result_builder,
    )


def _test_result_payload(source_bundle) -> JobMatchResultPayload:
    resume_chunk_id = source_bundle.resume_chunks[0].chunk_id
    job_chunk_id = source_bundle.job_requirement_chunks[0].chunk_id
    evidence = [SourceEvidenceRef(chunk_id=resume_chunk_id)]
    return JobMatchResultPayload(
        overall_score=82,
        overall_level="strong_match",
        confidence="high",
        summary="测试 fixture：基于当前绑定的简历与岗位信息生成匹配分析。",
        dimension_scores=[
            DimensionScore(
                key="requirement_alignment",
                score=25,
                max_score=30,
                rationale="测试 fixture：岗位要求已找到简历证据。",
                supporting_evidence=evidence,
                gaps=[],
                confidence="high",
            ),
            DimensionScore(
                key="experience_evidence",
                score=20,
                max_score=25,
                rationale="测试 fixture：简历片段提供经历证据。",
                supporting_evidence=evidence,
                gaps=[],
                confidence="high",
            ),
            DimensionScore(
                key="skill_coverage",
                score=17,
                max_score=20,
                rationale="测试 fixture：简历片段覆盖相关技能。",
                supporting_evidence=evidence,
                gaps=[],
                confidence="high",
            ),
            DimensionScore(
                key="gap_risk",
                score=12,
                max_score=15,
                rationale="测试 fixture：缺口风险较低。",
                supporting_evidence=evidence,
                gaps=["面试中继续确认经验深度。"],
                confidence="medium",
            ),
            DimensionScore(
                key="readiness_actions",
                score=8,
                max_score=10,
                rationale="测试 fixture：可形成聚焦追问。",
                supporting_evidence=evidence,
                gaps=[],
                confidence="medium",
            ),
        ],
        matched_requirements=[
            MatchedRequirement(
                requirement_chunk_id=job_chunk_id,
                resume_evidence_chunk_ids=[resume_chunk_id],
                rationale="测试 fixture：岗位要求与简历证据已建立匹配关系。",
                confidence="high",
            )
        ],
        missing_requirements=[],
        resume_evidence=[
            ResumeEvidence(
                chunk_id=resume_chunk_id,
                summary="测试 fixture 使用的主要简历证据。",
                confidence="high",
            )
        ],
        risk_flags=[],
        interview_focus=["核实简历中最强证据与目标岗位要求的匹配深度。"],
        suggested_questions=["请具体说明这段经历中哪一部分最能对应岗位要求？"],
        markdown_report="# 岗位匹配分析\n\n测试 fixture 匹配分析。",
    )


def _seed_match_sources(session_factory, owner_id: str) -> str:
    now = utc_now()
    resume_id = f"res_match_{owner_id}"
    resume_version_id = f"res_ver_match_{owner_id}"
    job_id = f"job_match_{owner_id}"
    job_version_id = f"job_ver_match_{owner_id}"
    binding_id = f"bind_match_{owner_id}"

    SqlAlchemyResumeRepository(session_factory).create_with_version(
        Resume(
            resume_id=resume_id,
            owner_ref=OwnerRef(owner_id=owner_id),
            current_version_ref=VersionRef(
                resource_type="resume",
                resource_id=resume_id,
                version_id=resume_version_id,
            ),
            status="active",
            title="Backend Resume",
            file_name="resume.md",
            created_at=now,
            updated_at=now,
        ),
        ResumeVersion(
            resume_version_id=resume_version_id,
            owner_id=owner_id,
            resume_id=resume_id,
            version_number=1,
            markdown_text=(
                "# Summary\n"
                "Built interview workflow automation with Python and FastAPI.\n"
                "# Skills\n"
                "Python, FastAPI, React, PostgreSQL."
            ),
            status="current",
            created_at=now,
        ),
    )

    job_repository = SqlAlchemyJobRepository(session_factory)
    job_repository.create_job(
        Job(
            job_id=job_id,
            owner_id=owner_id,
            title="Backend Engineer",
            company="ACME",
            department="Engineering",
            application_status="draft",
            status="active",
            current_version_id=job_version_id,
            record_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    job_repository.create_job_version(
        JobVersion(
            job_version_id=job_version_id,
            owner_id=owner_id,
            job_id=job_id,
            version_number=1,
            responsibilities=["Own backend APIs for candidate assessment workflows."],
            requirements=["Python and FastAPI experience."],
            other_notes="PostgreSQL is a plus.",
            status="current",
            created_at=now,
        )
    )

    SqlAlchemyBindingRepository(session_factory).add(
        ResumeJobBinding(
            binding_id=binding_id,
            owner_id=owner_id,
            resume_id=resume_id,
            job_id=job_id,
            resume_version_id=resume_version_id,
            job_version_id=job_version_id,
            status="active",
            record_version=1,
            created_at=now,
            updated_at=now,
        )
    )
    return binding_id
