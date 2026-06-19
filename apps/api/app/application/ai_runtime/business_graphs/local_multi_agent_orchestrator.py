"""Default-off local multi-agent orchestrator graph descriptor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.agents.contracts import P8_REQUIRED_RUNTIME_STOP_CONDITIONS
from app.application.agents.definitions.orchestrator import INTERVIEW_ORCHESTRATOR_AGENT_ID

if TYPE_CHECKING:
    from app.application.ai_runtime.registry import GraphDescriptor


LOCAL_MULTI_AGENT_TASK_TYPE = "local_multi_agent_orchestration"
LOCAL_MULTI_AGENT_GRAPH_NAME = INTERVIEW_ORCHESTRATOR_AGENT_ID
LOCAL_MULTI_AGENT_GRAPH_VERSION = "option-d-local-runtime"
LOCAL_MULTI_AGENT_GRAPH_FLAG = "AIFI_ENABLE_LOCAL_MULTI_AGENT_ORCHESTRATION"
LOCAL_MULTI_AGENT_RUNTIME_TOOL = "local_multi_agent_orchestrator_entry"


def build_local_multi_agent_orchestrator_graph_descriptor() -> "GraphDescriptor":
    from app.application.ai_runtime.registry import GraphDescriptor

    return GraphDescriptor(
        graph_name=LOCAL_MULTI_AGENT_GRAPH_NAME,
        graph_version=LOCAL_MULTI_AGENT_GRAPH_VERSION,
        capability="local_multi_agent_orchestration",
        lifecycle_status="active",
        runtime_flag_key=LOCAL_MULTI_AGENT_GRAPH_FLAG,
        default_enabled=False,
        supported_entrypoints=("start", "replay", "timeline", "cancel"),
        supported_outputs=("candidate_refs", "interrupt_refs"),
        prompt_contract_ids=("LOCAL-MULTI-AGENT-REFS-ONLY",),
        eval_suite_ids=("EVAL-PHASE12-L5-LOCAL",),
        runtime_max_steps=4,
        runtime_max_retries=1,
        runtime_timeout_seconds=20,
        runtime_stop_conditions=P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
        runtime_allowed_tools=(LOCAL_MULTI_AGENT_RUNTIME_TOOL,),
        runtime_allowed_callers=(INTERVIEW_ORCHESTRATOR_AGENT_ID,),
        runtime_side_effect_policy="candidate_write",
        resume_schema_ids={"user_confirmation": "agent.resume.user_confirmation.v1"},
        interrupt_types=("user_confirmation",),
        required_permissions=("owner",),
        visibility="owner_only",
        health_summary_refs=("health.local_multi_agent.option_d",),
        config_schema_ref="graph_config.local_multi_agent.option_d.v1",
        implementation_pr="Option-D",
        migration_status="local_default_off_runtime_path",
        provider_enabled=False,
        formal_write_targets=(),
        db_business_write_targets=(),
        rollback_safe=True,
        disabled_behavior="adapter_only_unavailable",
    )


__all__ = [
    "LOCAL_MULTI_AGENT_GRAPH_FLAG",
    "LOCAL_MULTI_AGENT_GRAPH_NAME",
    "LOCAL_MULTI_AGENT_GRAPH_VERSION",
    "LOCAL_MULTI_AGENT_RUNTIME_TOOL",
    "LOCAL_MULTI_AGENT_TASK_TYPE",
    "build_local_multi_agent_orchestrator_graph_descriptor",
]
