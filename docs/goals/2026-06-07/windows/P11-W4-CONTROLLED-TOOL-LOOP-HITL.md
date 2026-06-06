---
title: P11-W4-CONTROLLED-TOOL-LOOP-HITL
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p11-w4-controlled-tool-loop-hitl
---
Current Recon Result:
L5-READINESS-RECON-W1 returned GREEN for entering/continuing Phase 11 controlled windows only.

Accepted by 总控:
- Proceed to P11-W4.
- Do not claim L5 release.
- Do not implement Phase 12 release gate in this window.
- Preserve candidate-only outputs.
- Preserve formal write path: Application Service -> Domain Policy -> Handoff -> Repository / Transaction.
- No provider / prompt / API / DB / frontend behavior drift.

Known Carry-forward Risks:
- deferred_remote_ci_gap
- Phase 8 runtime gaps
- real-provider quality non-claim
- formal-write boundary
- Phase 12 release-gate deferral
- L5-006 remains release-blocking until executable eval/replay/CI/report/human decision evidence exists.

# P11-W4-CONTROLLED-TOOL-LOOP-HITL

## Activation rule

Execute only after P11-W3 proves a typed multi-agent workflow, or 总控 explicitly approves hardening before workflow completion.

## Window ID

`P11-W4-CONTROLLED-TOOL-LOOP-HITL`

## Phase

Phase 11 — L5 Controlled Multi-Agent Orchestration

## Capability IDs

- L5-005
- L5-003
- AGT-003
- AGT-004
- AGT-005
- AGT-007

## Goal

Harden the cross-agent tool loop with explicit bounds and HITL triggers.

## Must recon first

- AgentExecutor / runtime port
- SkillRegistry and ToolRegistry
- planner / execution plan code
- runtime state/checkpoint code
- Question / Feedback tool calls
- asset conflict and formal write policy code
- HITL / interrupt/resume code if present
- tests for runtime, fake boundary, provider boundary, and agent architecture

## Allowed files

```text
apps/api/app/application/agents/**
apps/api/app/application/polish/agents/**
apps/api/app/application/polish/services/**
tests/architecture/**
tests/evals/**
tests/api/**
docs/**
project_sources/**
```

## Forbidden files

```text
apps/api/app/infrastructure/db/**
database migrations
apps/api/app/infrastructure/llm/**
prompt asset files
provider behavior implementation files unless explicitly approved
```

## Behavior change allowed

Limited behavior change only for controlled L5 runtime path. Existing non-L5 paths must not regress.

## Prompt/schema/provider change allowed

No prompt/provider behavior change.

## DB schema change allowed

No.

## Implementation requirements

- Enforce max_steps.
- Enforce max_retries.
- Enforce timeout_seconds.
- Enforce stop_conditions.
- Define repair_strategy and fallback semantics.
- Add HITL triggers for:
  - asset conflict;
  - formal write;
  - low confidence;
  - ownership ambiguity.
- Ensure validation failed / provider unavailable / fallback cannot be reported as generated success.
- Ensure all tool calls are permission-scoped and do not expose repositories directly.
- Add tests for loop bound exhaustion, HITL interrupt, resume validation, and forbidden direct write.

## Validation commands

```bash
pytest tests/architecture
pytest tests/evals
pytest tests/api/test_fake_llm_boundary.py
pytest tests/api/test_llm_runtime.py
```

Run additional targeted runtime tests if available.

## Rollback

Revert changed files in allowed scope. No DB rollback.

## Done criteria

- Tool loop bounds are enforced and tested.
- HITL triggers are encoded and tested.
- Tool registry permissions prevent repository exposure.
- Candidate/formal boundary remains enforced.
- Tests/evals pass or blockers are returned to 总控.
- Source backfill updated or proposed.

## Stop conditions

Stop and return to 总控 if bounded loop requires infrastructure persistence changes, DB migrations, provider behavior changes, or direct formal writes.

## Result digest

Status: `runtime_bounds_hitl_slice_complete_with_deferred_release_gate`.

Scope result:

- Changed runtime contracts / adapter boundary only under `apps/api/app/application/agents/**`.
- Added focused API regression coverage under `tests/api/**`.
- Updated active source backfill in `docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md` and `docs/project-sources/12_ACCEPTANCE_GATES.md`.
- Did not modify provider, prompt asset, DB schema, API route contract, frontend, infrastructure LLM or domain policy files.

Implementation evidence:

- `AgentRuntimeLoopPolicy` now includes explicit `repair_strategy` and `fallback_semantics` alongside `max_steps`, `max_retries`, `timeout_seconds` and `stop_conditions`.
- `AgentGraphRunnerExecutorAdapter` injects runtime loop policy metadata and enforces runtime-reported max step, retry and timeout exhaustion.
- Bound exhaustion cannot be reported as success; non-success exhaustion requires a matching stop condition or failure reason.
- Runtime HITL trigger metadata is validated for formal write, asset conflict, low confidence, ambiguous ownership and validation-failed partial result.
- `hitl_required=true`, fallback generated-success markers, forbidden formal-write markers and repository/DB/tool exposure markers fail closed at the adapter boundary.
- Runtime tool calls must be scoped to allowed tool refs and cannot expose repository, DB, SQLAlchemy session, unit-of-work or formal writer handles.

Validation evidence:

```bash
PYTHONPATH=.:apps/api .venv/bin/pytest tests/api
PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture
PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals
PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_fake_llm_boundary.py
PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_llm_runtime.py
```

Observed result:

- `tests/api`: 725 passed.
- `tests/architecture`: 30 passed.
- `tests/evals`: 35 passed.
- `tests/api/test_fake_llm_boundary.py`: 5 passed.
- `tests/api/test_llm_runtime.py`: 6 passed.

Non-claims:

- Not L5 release.
- Not Phase 12 release gate.
- Not real-provider quality certification.
- Not remote CI success.
- Not formal write completion.
- Not provider / prompt / DB / API / frontend / domain behavior change.
