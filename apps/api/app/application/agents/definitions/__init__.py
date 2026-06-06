"""Public imports for Agent Platform contract catalog definitions."""

from app.application.agents.contracts import AgentDefinition, SkillDefinition, ToolDefinition
from app.application.agents.definitions.asset_candidate import (
    ASSET_CANDIDATE_AGENT_ID,
    build_asset_candidate_agent_definition,
    build_asset_candidate_skill_definitions,
    build_asset_candidate_tool_definitions,
)
from app.application.agents.definitions.catalog import (
    AgentPlatformC1Registries,
    AgentPlatformL5ContractRegistries,
    CATALOG_REVISION,
    build_default_agent_platform_c1_registries,
    build_default_agent_platform_l5_contract_registries,
    build_phase4_c1_agent_definitions,
    build_phase4_c1_skill_definitions,
    build_phase4_c1_tool_definitions,
    build_phase11_l5_agent_definitions,
    build_phase11_l5_skill_definitions,
    build_phase11_l5_tool_definitions,
)
from app.application.agents.definitions.training_plan import (
    TRAINING_PLAN_AGENT_ID,
    build_training_plan_agent_definition,
    build_training_plan_skill_definitions,
    build_training_plan_tool_definitions,
)

__all__ = [
    "AgentDefinition",
    "AgentPlatformC1Registries",
    "AgentPlatformL5ContractRegistries",
    "ASSET_CANDIDATE_AGENT_ID",
    "CATALOG_REVISION",
    "SkillDefinition",
    "TRAINING_PLAN_AGENT_ID",
    "ToolDefinition",
    "build_asset_candidate_agent_definition",
    "build_asset_candidate_skill_definitions",
    "build_asset_candidate_tool_definitions",
    "build_default_agent_platform_c1_registries",
    "build_default_agent_platform_l5_contract_registries",
    "build_phase4_c1_agent_definitions",
    "build_phase4_c1_skill_definitions",
    "build_phase4_c1_tool_definitions",
    "build_phase11_l5_agent_definitions",
    "build_phase11_l5_skill_definitions",
    "build_phase11_l5_tool_definitions",
    "build_training_plan_agent_definition",
    "build_training_plan_skill_definitions",
    "build_training_plan_tool_definitions",
]
