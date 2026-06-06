---
title: P11-W1-SUPERVISOR-ORCHESTRATOR-DEFINITION
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p11-w1-supervisor-orchestrator-definition
---

# P11-W1-SUPERVISOR-ORCHESTRATOR-DEFINITION

## Activation rule

Execute only after `L5-READINESS-RECON-W1` returns GREEN, or after 总控 explicitly approves Phase 11 entry following AMBER blocker closure.

## Window ID

`P11-W1-SUPERVISOR-ORCHESTRATOR-DEFINITION`

## Phase

Phase 11 — L5 Controlled Multi-Agent Orchestration

## Capability IDs

- L5-002
- AGT-002
- AGT-003
- AGT-004
- AGT-005
- AGT-006
- AGT-007

## Goal

Define and register a bounded Supervisor / Orchestrator Agent. This window establishes the orchestration definition and contracts only; it does not implement an autonomous product workflow yet.

## Must recon first

- `apps/api/app/application/agents/`
- `apps/api/app/application/agents/definitions/`
- `apps/api/app/application/agents/registry/`
- `apps/api/app/application/agents/runtime/`
- `apps/api/app/application/agents/handoff/`
- existing AgentDefinition / SkillRegistry / ToolRegistry / AgentExecutor port files
- existing tests under `tests/architecture/` and `tests/evals/`
- Project sources for Agent Definition Standard, Agent Platform Architecture, Phase Roadmap, Acceptance Gates

## Allowed files

Candidate scope only; adjust to actual repository layout after recon:

```text
apps/api/app/application/agents/definitions/**
apps/api/app/application/agents/contracts/**
apps/api/app/application/agents/registry/**
apps/api/app/application/agents/handoff/**
apps/api/app/application/agents/runtime/**
tests/architecture/**
tests/evals/**
docs/**
project_sources/**
```

## Forbidden files

```text
apps/api/app/infrastructure/db/**
database migrations
apps/api/app/infrastructure/llm/**
prompt asset files
API route contract files
provider behavior implementation files
production DB implementation files
```

## Behavior change allowed

No product behavior change. Definition/contract registration only.

## Prompt/schema/provider change allowed

No provider behavior change. Schema additions only if they are Agent Platform contracts and are backward-compatible.

## DB schema change allowed

No.

## Implementation requirements

- Define `supervisor_orchestrator_agent` or equivalent ID.
- Set maturity as Phase 11 L5 orchestrator candidate, not unbounded autonomous swarm.
- Define mission, non-goals, input/output contract, candidate outputs, formal write boundary.
- Define planning strategy with `max_steps`, `max_retries`, `timeout_seconds`, `stop_conditions`.
- Define HITL triggers: asset conflict, formal write, low confidence, ownership ambiguity.
- Define allowed subordinate agent refs, but do not require all business agents to be implemented in this window.
- Ensure Agent cannot write formal business facts.
- Ensure ToolRegistry does not expose repository directly.
- Add architecture tests or registry tests proving registration and bounded contract.

## Validation commands

```bash
pytest tests/architecture
pytest tests/evals || true
```

If targeted tests exist, run them explicitly and report results.

## Rollback

Revert files changed in allowed scope. No DB rollback.

## Done criteria

- Supervisor / Orchestrator Agent definition exists and is registry-valid.
- Bounded planning fields are required and tested/gated.
- Candidate-only and formal-write handoff boundary remain enforced.
- No prompt/provider/DB/API behavior changed.
- Tests pass or inability is recorded with risk.
- Matrix / Decision / Risk / Acceptance source backfill updated or proposed.

## Stop conditions

Stop and return to 总控 if implementation requires:

- provider behavior change;
- DB schema change;
- API contract change;
- unbounded autonomous loop;
- Agent direct formal write;
- Tool direct repository exposure;
- redefining Phase 11 scope.

## Final output

Use `templates/WINDOW_RESULT_DIGEST.md` plus full details for changed contracts and tests.