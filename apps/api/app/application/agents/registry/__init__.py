from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from app.application.agents.contracts import AgentDefinition, SkillDefinition, ToolDefinition


class RegistryValidationError(ValueError):
    """Raised when a C0 registry definition is missing, duplicated, or wrong-shaped."""


DefinitionT = TypeVar("DefinitionT")


def _validate_id(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryValidationError(f"{label} must be a non-empty string")
    return value


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


class SkillRegistry(_DefinitionRegistry[SkillDefinition]):
    _id_attr = "skill_id"
    _definition_type = SkillDefinition
    _id_label = "skill_id"


class ToolRegistry(_DefinitionRegistry[ToolDefinition]):
    _id_attr = "tool_id"
    _definition_type = ToolDefinition
    _id_label = "tool_id"


__all__ = [
    "AgentDefinitionRegistry",
    "RegistryValidationError",
    "SkillRegistry",
    "ToolRegistry",
]
