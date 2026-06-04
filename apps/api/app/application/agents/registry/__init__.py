from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Generic, TypeVar

from app.application.agents.contracts import AgentDefinition, SkillDefinition, ToolDefinition


class RegistryValidationError(ValueError):
    """Raised when a C0 registry definition is missing, duplicated, or wrong-shaped."""


DefinitionT = TypeVar("DefinitionT")

ALLOWED_CANDIDATE_OUTPUTS = frozenset(
    {
        "question_candidate",
        "feedback_candidate",
        "asset_update_candidate",
        "progress_update_candidate",
        "weakness_candidate",
        "training_plan_candidate",
        "report_candidate",
        "review_candidate",
    }
)
ALLOWED_TOOL_SIDE_EFFECT_POLICIES = frozenset(
    {
        "read_only",
        "candidate_write",
        "formal_write_handoff_only",
        "forbidden",
    }
)
REQUIRED_TOOL_FORBIDDEN_DATA = frozenset(
    {
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "raw_provider_payload",
        "raw_completion",
        "full_resume",
        "full_jd",
        "secrets",
        "tokens",
        "cookies",
        "api_keys",
    }
)
_FORBIDDEN_DIRECT_EXPOSURE_TOKENS = frozenset(
    {
        "repository",
        "repositories",
        "db",
        "database",
        "sqlalchemy",
        "session",
        "unit_of_work",
        "uow",
        "formal_writer",
        "formal_write",
        "raw_prompt",
        "provider_payload",
        "full_resume",
        "full_jd",
        "secrets",
    }
)


def _validate_id(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryValidationError(f"{label} must be a non-empty string")
    return value


def _metadata_tokens(*values: str) -> set[str]:
    return {token for value in values for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _has_direct_exposure(*values: str) -> bool:
    lowered_values = {value.lower() for value in values}
    tokens = _metadata_tokens(*values)
    normalized_tokens = "_".join(tokens)
    for forbidden in _FORBIDDEN_DIRECT_EXPOSURE_TOKENS:
        if forbidden in tokens or forbidden in lowered_values:
            return True
        if "_" in forbidden and forbidden in normalized_tokens:
            return True
    return False


class _DefinitionRegistry(Generic[DefinitionT]):
    _id_attr: str
    _definition_type: type[DefinitionT]
    _id_label: str

    def __init__(self, definitions: Iterable[DefinitionT] = ()) -> None:
        self._items: dict[str, DefinitionT] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: DefinitionT) -> DefinitionT:
        if not isinstance(definition, self._definition_type):
            raise RegistryValidationError(
                f"expected {self._definition_type.__name__}, got {definition.__class__.__name__}"
            )
        definition_id = _validate_id(getattr(definition, self._id_attr), label=self._id_label)
        if definition_id in self._items:
            raise RegistryValidationError(f"duplicate {self._id_label}: {definition_id}")
        self._items[definition_id] = definition
        return definition

    def get(self, definition_id: str) -> DefinitionT:
        normalized_id = _validate_id(definition_id, label=self._id_label)
        try:
            return self._items[normalized_id]
        except KeyError as exc:
            raise RegistryValidationError(f"unknown {self._id_label}: {normalized_id}") from exc

    def list(self) -> tuple[DefinitionT, ...]:
        return tuple(self._items.values())


class AgentDefinitionRegistry(_DefinitionRegistry[AgentDefinition]):
    _id_attr = "agent_id"
    _definition_type = AgentDefinition
    _id_label = "agent_id"

    def register(self, definition: AgentDefinition) -> AgentDefinition:
        if not isinstance(definition, self._definition_type):
            return super().register(definition)
        invalid_outputs = set(definition.candidate_outputs) - ALLOWED_CANDIDATE_OUTPUTS
        if invalid_outputs:
            raise RegistryValidationError(f"invalid candidate_outputs: {sorted(invalid_outputs)}")
        return super().register(definition)

    def get_agent_id_for_task_type(self, task_type: str) -> str:
        normalized_task_type = _validate_id(task_type, label="task_type")
        matches = tuple(
            definition.agent_id for definition in self.list() if normalized_task_type in definition.task_types
        )
        if not matches:
            raise RegistryValidationError(f"unknown task_type: {normalized_task_type}")
        if len(matches) > 1:
            raise RegistryValidationError(f"duplicate task_type mapping: {normalized_task_type}")
        return matches[0]

    def validate_references(self, skill_registry: "SkillRegistry", tool_registry: "ToolRegistry") -> None:
        for agent_definition in self.list():
            for skill_id in agent_definition.skills:
                skill_registry.get(skill_id)
            for tool_id in agent_definition.tools:
                tool_registry.get(tool_id)
            for skill_definition in skill_registry.list_by_agent_id(agent_definition.agent_id):
                for tool_id in skill_definition.tool_refs:
                    tool_registry.get(tool_id)


class SkillRegistry(_DefinitionRegistry[SkillDefinition]):
    _id_attr = "skill_id"
    _definition_type = SkillDefinition
    _id_label = "skill_id"

    def list_by_agent_id(self, agent_id: str) -> tuple[SkillDefinition, ...]:
        normalized_agent_id = _validate_id(agent_id, label="agent_id")
        return tuple(item for item in self.list() if normalized_agent_id in item.owner_agent_ids)


class ToolRegistry(_DefinitionRegistry[ToolDefinition]):
    _id_attr = "tool_id"
    _definition_type = ToolDefinition
    _id_label = "tool_id"

    def register(self, definition: ToolDefinition) -> ToolDefinition:
        if not isinstance(definition, self._definition_type):
            return super().register(definition)
        if definition.side_effect_policy not in ALLOWED_TOOL_SIDE_EFFECT_POLICIES:
            raise RegistryValidationError(f"invalid side_effect_policy: {definition.side_effect_policy}")
        missing_forbidden_data = REQUIRED_TOOL_FORBIDDEN_DATA - set(definition.forbidden_data)
        if missing_forbidden_data:
            raise RegistryValidationError(f"missing forbidden_data: {sorted(missing_forbidden_data)}")
        if _has_direct_exposure(
            definition.tool_id,
            definition.tool_name,
            definition.input_schema_id,
            definition.output_schema_id,
            definition.permission_scope,
            definition.owner_scope,
            " ".join(definition.allowed_callers),
            " ".join(definition.trace_events),
        ):
            raise RegistryValidationError(f"direct exposure is forbidden for tool_id: {definition.tool_id}")
        return super().register(definition)

    def list_by_agent_id(self, agent_id: str) -> tuple[ToolDefinition, ...]:
        normalized_agent_id = _validate_id(agent_id, label="agent_id")
        return tuple(item for item in self.list() if normalized_agent_id in item.allowed_callers)


__all__ = [
    "ALLOWED_CANDIDATE_OUTPUTS",
    "ALLOWED_TOOL_SIDE_EFFECT_POLICIES",
    "AgentDefinitionRegistry",
    "REQUIRED_TOOL_FORBIDDEN_DATA",
    "RegistryValidationError",
    "SkillRegistry",
    "ToolRegistry",
]
