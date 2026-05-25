"""AI Runtime graph descriptor registry for PR3 contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.ai_runtime.contracts import RuntimeValidationError


@dataclass(frozen=True)
class GraphDescriptor:
    graph_name: str
    graph_version: str
    capability: str
    lifecycle_status: str
    runtime_flag_key: str
    default_enabled: bool
    supported_entrypoints: tuple[str, ...]
    supported_outputs: tuple[str, ...]
    prompt_contract_ids: tuple[str, ...]
    eval_suite_ids: tuple[str, ...]
    resume_schema_ids: dict[str, str] = field(default_factory=dict)
    interrupt_types: tuple[str, ...] = field(default_factory=tuple)
    required_permissions: tuple[str, ...] = field(default_factory=tuple)
    visibility: str = "owner_only"
    health_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    config_schema_ref: str | None = None
    implementation_pr: str = "PR3"
    migration_status: str = "not_started"
    provider_enabled: bool = False
    formal_write_targets: tuple[str, ...] = field(default_factory=tuple)
    db_business_write_targets: tuple[str, ...] = field(default_factory=tuple)
    rollback_safe: bool = True
    disabled_behavior: str = "legacy_direct_path_retained"

    def __post_init__(self) -> None:
        allowed_lifecycle = frozenset({"active", "disabled", "planned", "placeholder", "deferred"})
        if self.lifecycle_status not in allowed_lifecycle:
            raise RuntimeValidationError(f"unsupported graph lifecycle: {self.lifecycle_status}")
        if self.default_enabled:
            raise RuntimeValidationError("graph descriptors must be default-off in PR3")


class AgentGraphRegistry:
    def __init__(self, descriptors: dict[str, GraphDescriptor], task_map: dict[str, str] | None = None) -> None:
        self._descriptors = dict(descriptors)
        self._task_map = dict(task_map or {})

    @classmethod
    def default(cls) -> "AgentGraphRegistry":
        from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
            build_polish_feedback_graph_descriptor,
        )
        from app.application.ai_runtime.business_graphs.polish_question_graph import (
            build_polish_question_graph_descriptor,
        )

        descriptors = {
            "polish_question_graph": build_polish_question_graph_descriptor(),
            "polish_feedback_graph": build_polish_feedback_graph_descriptor(),
            "job_match_graph": GraphDescriptor(
                graph_name="job_match_graph",
                graph_version="pr3-contract",
                capability="job_match",
                lifecycle_status="deferred",
                runtime_flag_key="AIFI_GRAPH_JOB_MATCH_ENABLED",
                default_enabled=False,
                supported_entrypoints=("start", "timeline", "cancel"),
                supported_outputs=("result_refs", "candidate_refs", "suggestion_refs"),
                prompt_contract_ids=("P-JOBMATCH-001",),
                eval_suite_ids=("EVAL-JOBMATCH-001",),
                required_permissions=("owner",),
                visibility="hidden_placeholder",
                health_summary_refs=("health.job_match.deferred",),
                config_schema_ref="graph_config.job_match.v1",
                implementation_pr="PR8",
                migration_status="not_started",
            ),
            "resume_analysis_graph": GraphDescriptor(
                graph_name="resume_analysis_graph",
                graph_version="pr3-contract",
                capability="resume_analysis",
                lifecycle_status="deferred",
                runtime_flag_key="AIFI_GRAPH_RESUME_ANALYSIS_ENABLED",
                default_enabled=False,
                supported_entrypoints=("start", "timeline", "cancel"),
                supported_outputs=("result_refs", "candidate_refs", "suggestion_refs"),
                prompt_contract_ids=("P-RESUME-ANALYSIS-001",),
                eval_suite_ids=("EVAL-RESUME-ANALYSIS-001",),
                required_permissions=("owner",),
                visibility="hidden_placeholder",
                health_summary_refs=("health.resume_analysis.deferred",),
                config_schema_ref="graph_config.resume_analysis.v1",
                implementation_pr="PR8",
                migration_status="not_started",
            ),
            "report_generation_graph": GraphDescriptor(
                graph_name="report_generation_graph",
                graph_version="pr3-contract",
                capability="report_generation",
                lifecycle_status="deferred",
                runtime_flag_key="AIFI_GRAPH_REPORT_GENERATION_ENABLED",
                default_enabled=False,
                supported_entrypoints=("start", "resume", "replay", "timeline", "cancel"),
                supported_outputs=("result_refs", "candidate_refs", "suggestion_refs", "interrupt_refs"),
                prompt_contract_ids=("P-REPORT-001",),
                eval_suite_ids=("EVAL-REPORT-001",),
                resume_schema_ids={"user_confirmation": "agent.resume.user_confirmation.v1"},
                interrupt_types=("user_confirmation",),
                required_permissions=("owner",),
                visibility="hidden_placeholder",
                health_summary_refs=("health.report_generation.deferred",),
                config_schema_ref="graph_config.report_generation.v1",
                implementation_pr="PR8",
                migration_status="not_started",
            ),
            "review_generation_graph": GraphDescriptor(
                graph_name="review_generation_graph",
                graph_version="pr3-contract",
                capability="review_generation",
                lifecycle_status="deferred",
                runtime_flag_key="AIFI_GRAPH_REVIEW_GENERATION_ENABLED",
                default_enabled=False,
                supported_entrypoints=("start", "resume", "replay", "timeline", "cancel"),
                supported_outputs=("candidate_refs", "suggestion_refs", "interrupt_refs"),
                prompt_contract_ids=("P-REVIEW-001",),
                eval_suite_ids=("EVAL-REVIEW-001",),
                resume_schema_ids={"user_confirmation": "agent.resume.user_confirmation.v1"},
                interrupt_types=("user_confirmation",),
                required_permissions=("owner",),
                visibility="hidden_placeholder",
                health_summary_refs=("health.review_generation.deferred",),
                config_schema_ref="graph_config.review_generation.v1",
                implementation_pr="PR8",
                migration_status="not_started",
            ),
        }
        task_map = {
            "polish_question_generation": "polish_question_graph",
            "polish_feedback_generation": "polish_feedback_graph",
            "job_match_analysis": "job_match_graph",
            "resume_analysis": "resume_analysis_graph",
            "report_generation": "report_generation_graph",
            "review_generation": "review_generation_graph",
        }
        return cls(descriptors=descriptors, task_map=task_map)

    def get_graph_descriptor(self, task_type: str) -> GraphDescriptor:
        graph_name = self._task_map.get(task_type, task_type)
        try:
            return self._descriptors[graph_name]
        except KeyError as exc:
            raise RuntimeValidationError(f"unknown graph descriptor: {task_type}") from exc

    def list_graph_descriptors(self) -> tuple[GraphDescriptor, ...]:
        return tuple(self._descriptors.values())

    def get_contract_ids(self, task_type: str) -> tuple[str, ...]:
        return self.get_graph_descriptor(task_type).prompt_contract_ids

    def validate_requested_outputs(self, task_type: str, requested_outputs: tuple[str, ...]) -> tuple[str, ...]:
        descriptor = self.get_graph_descriptor(task_type)
        unsupported = tuple(output for output in requested_outputs if output not in descriptor.supported_outputs)
        if unsupported:
            raise RuntimeValidationError(f"unsupported output: {', '.join(unsupported)}")
        return requested_outputs

    def resolve_feature_flag(self, task_type: str) -> str:
        return self.get_graph_descriptor(task_type).runtime_flag_key

    def resolve_resume_schema_descriptor(self, interrupt_type: str) -> dict[str, Any]:
        for descriptor in self._descriptors.values():
            schema_id = descriptor.resume_schema_ids.get(interrupt_type)
            if schema_id:
                return {
                    "schema_id": schema_id,
                    "interrupt_type": interrupt_type,
                    "graph_name": descriptor.graph_name,
                    "visibility": descriptor.visibility,
                }
        raise RuntimeValidationError(f"unknown resume schema: {interrupt_type}")
