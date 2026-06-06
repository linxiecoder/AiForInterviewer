---
title: P11-W5-L5-INTEGRATION-BOUNDARY-TESTS-BACKFILL
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p11-w5-l5-integration-boundary-tests-backfill
---

# P11-W5-L5-INTEGRATION-BOUNDARY-TESTS-BACKFILL

## Activation rule

Execute after P11-W1 through P11-W4 are implemented or explicitly deferred by 总控.

## Window ID

`P11-W5-L5-INTEGRATION-BOUNDARY-TESTS-BACKFILL`

## Phase

Phase 11 — L5 Controlled Multi-Agent Orchestration

## Capability IDs

- L5-002
- L5-003
- L5-004
- L5-005
- AGT-002
- AGT-003
- AGT-004
- AGT-005
- AGT-006
- AGT-007
- WIN-001

## Goal

Add integration/boundary tests and source backfill for Phase 11 closure. Do not implement new product behavior unless required only for testability and explicitly scoped.

## Must recon first

- all Phase 11 changed files
- architecture tests
- eval tests
- Project sources: Matrix, Decision Log, Risk Register, Acceptance Gates, Phase Roadmap

## Allowed files

```text
tests/architecture/**
tests/evals/**
tests/api/**
docs/**
project_sources/**
```

Minimal implementation touch is allowed only if a test exposes a small bug inside Phase 11 allowed scope.

## Forbidden files

```text
prompt asset files
provider behavior implementation files
DB implementation files
database migrations
API contract files
unrelated business implementation files
```

## Behavior change allowed

No new behavior except bug fixes explicitly tied to Phase 11 boundaries.

## Prompt/schema/provider change allowed

No.

## DB schema change allowed

No.

## Implementation requirements

Tests must cover:

- Supervisor / Orchestrator registered.
- Cross-agent handoff/state/trace contract exists.
- Three-or-more-agent workflow uses typed handoff.
- Controlled loop has max_steps / retries / timeout / stop_conditions.
- HITL triggers exist for asset conflict, formal write, low confidence, ownership ambiguity.
- Agent output remains candidate/suggestion only.
- Formal write remains Application Service -> Domain Policy -> Handoff.
- Tool does not expose repository directly.
- No unbounded autonomous loop.

Source backfill must update/propose:

- Traceability Matrix
- Decision Log
- Risk Register
- Acceptance Gates
- Phase Roadmap

## Validation commands

```bash
pytest tests/architecture
pytest tests/evals
pytest tests/api
```

## Rollback

Revert tests/docs changed in this window. Revert any scoped bug fixes if necessary.

## Done criteria

- Phase 11 tests pass.
- Phase 11 capability statuses are evidence-backed.
- Any deferred gaps are explicit and user-confirmable.
- Source backfill complete or patch proposed.
- Ready to enter Phase 12 only if 总控 accepts Phase 11 closure.

## Stop conditions

Stop and return to 总控 if source backfill reveals unclosed candidate/formal, provider fail-open, fake contamination, or missing trace/replay blockers.