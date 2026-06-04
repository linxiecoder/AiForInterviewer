"""Aggregation-only public builder for the Agent Platform C1 catalog."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.agents.contracts import AgentDefinition, SkillDefinition, ToolDefinition
from app.application.agents.definitions.polish import (
    build_polish_feedback_agent_definition,
    build_polish_feedback_skill_definitions,
    build_polish_feedback_tool_definitions,
    build_polish_question_agent_definition,
    build_polish_question_skill_definitions,
    build_polish_question_tool_definitions,
)
from app.application.agents.definitions.versions import CATALOG_REVISION
from app.application.agents.registry import AgentDefinitionRegistry, SkillRegistry, ToolRegistry


@dataclass(frozen=True)
class AgentPlatformC1Registries:
    """Container for project-level C1 registries built from contract-only definitions."""

    agent_definitions: AgentDefinitionRegistry
    skills: SkillRegistry
    tools: ToolRegistry


def build_phase4_c1_agent_definitions() -> tuple[AgentDefinition, ...]:
    """Return P4-W1.fix.01 C1 agent contracts without runtime wiring."""

    return (
        build_polish_question_agent_definition(),
        build_polish_feedback_agent_definition(),
    )


def build_phase4_c1_skill_definitions() -> tuple[SkillDefinition, ...]:
    """Return P4-W1.fix.01 C1 skill contracts for project-level registration."""

    return (
        *build_polish_question_skill_definitions(),
        *build_polish_feedback_skill_definitions(),
    )


def build_phase4_c1_tool_definitions() -> tuple[ToolDefinition, ...]:
    """Return P4-W1.fix.01 C1 tool contracts with no direct formal write path."""

    return (
        *build_polish_question_tool_definitions(),
        *build_polish_feedback_tool_definitions(),
    )


def build_default_agent_platform_c1_registries() -> AgentPlatformC1Registries:
    """Build and validate the project-level C1 contract registries."""

    agent_registry = AgentDefinitionRegistry(build_phase4_c1_agent_definitions())
    skill_registry = SkillRegistry(build_phase4_c1_skill_definitions())
    tool_registry = ToolRegistry(build_phase4_c1_tool_definitions())
    agent_registry.validate_references(skill_registry, tool_registry)
    return AgentPlatformC1Registries(
        agent_definitions=agent_registry,
        skills=skill_registry,
        tools=tool_registry,
    )


__all__ = [
    "AgentPlatformC1Registries",
    "CATALOG_REVISION",
    "build_default_agent_platform_c1_registries",
    "build_phase4_c1_agent_definitions",
    "build_phase4_c1_skill_definitions",
    "build_phase4_c1_tool_definitions",
]
