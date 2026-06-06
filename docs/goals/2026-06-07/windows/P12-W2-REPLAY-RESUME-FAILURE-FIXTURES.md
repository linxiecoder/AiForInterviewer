---
title: P12-W2-REPLAY-RESUME-FAILURE-FIXTURES
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p12-w2-replay-resume-failure-fixtures
---

# P12-W2-REPLAY-RESUME-FAILURE-FIXTURES

## Activation rule

Execute after P12-W1 eval suite is accepted or explicitly approved to proceed.

## Window ID

`P12-W2-REPLAY-RESUME-FAILURE-FIXTURES`

## Phase

Phase 12 — L5 Eval, Hardening, and Release Gate

## Capability IDs

- L5-006
- L5-003
- L5-004
- L5-005
- EVAL-001

## Goal

Add cross-agent replay/resume/failure fixtures proving at least one full multi-agent scenario can be reproduced without persisting raw prompt or raw provider payload.

## Must recon first

- replay/checkpoint/resume code
- trace contract
- Phase 11 workflow trace output
- tests/evals fixtures
- existing fake/replay separation

## Allowed files

```text
tests/evals/**
tests/fixtures/**
tests/architecture/**
scripts/**
docs/**
project_sources/**
```

Runtime hook changes only if explicitly scoped and non-invasive.

## Forbidden files

```text
production DB schema
migrations
provider behavior implementation
prompt rewrites
raw prompt/provider payload persistence
API contract changes
```

## Behavior change allowed

No product behavior change except replay/test hooks explicitly isolated from production.

## Prompt/schema/provider change allowed

No provider behavior change.

## DB schema change allowed

No.

## Implementation requirements

- Add replay fixture for one full cross-agent scenario.
- Add resume fixture for interrupted/HITL scenario.
- Add failure fixtures for provider failure, validation failure, and handoff failure.
- Ensure replay stores refs/digests, not raw prompts or raw provider payloads.
- Ensure replay default is read-only.
- Ensure resume validates owner scope / base version / interrupt ref if applicable.

## Validation commands

```bash
pytest tests/evals
pytest tests/architecture
```

## Rollback

Revert fixtures/tests/docs in allowed scope.

## Done criteria

- Replay fixture can reproduce at least one full multi-agent scenario.
- Failure fixtures exist and are tested.
- No raw prompt/provider payload persistence.
- Replay/resume semantics documented.
- Source backfill updated or proposed.

## Stop conditions

Stop and return to 总控 if reproducible replay requires storing raw prompt, provider payload, secrets, full resume, full JD, or full asset body.