---
title: P12-W1-MULTI-AGENT-EVAL-SUITE
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p12-w1-multi-agent-eval-suite
---

# P12-W1-MULTI-AGENT-EVAL-SUITE

## Activation rule

Execute only after Phase 11 closure is accepted by 总控. This window must return to 总控 after completion because it defines the L5 quality gate.

## Window ID

`P12-W1-MULTI-AGENT-EVAL-SUITE`

## Phase

Phase 12 — L5 Eval, Hardening, and Release Gate

## Capability IDs

- L5-006
- EVAL-001
- L5-002
- L5-003
- L5-004
- L5-005

## Goal

Build the L5 multi-agent eval suite, datasets, graders, and minimum pass criteria.

## Must recon first

- existing tests/evals layout
- eval runners / graders / datasets
- CI config
- Phase 11 workflow tests
- replay/trace artifacts
- provider/fake boundaries

## Allowed files

```text
tests/evals/**
scripts/**
.github/workflows/**
docs/**
project_sources/**
```

Implementation code may be changed only for eval hooks if explicitly scoped and non-product behavior.

## Forbidden files

```text
production prompt rewrites
provider behavior implementation files
DB implementation files
database migrations
API contract files
unrelated product implementation files
```

## Behavior change allowed

No product behavior change.

## Prompt/schema/provider change allowed

No provider behavior change. Eval dataset/schema additions allowed.

## DB schema change allowed

No.

## Implementation requirements

Eval suite must cover at least:

- happy path;
- insufficient context;
- asset conflict;
- provider failure;
- validation failure;
- HITL;
- replay;
- cross-agent handoff failure.

Each case must identify:

- capability IDs covered;
- dataset refs;
- grader refs;
- expected trace refs;
- pass/fail criteria;
- triage owner or category.

Do not claim L5 quality with fake-only eval. If real-provider eval cannot run in CI, define clear separation between deterministic regression, replay, and provider-quality eval.

## Validation commands

```bash
pytest tests/evals
pytest tests/architecture
```

Run eval runner command if present and record result.

## Rollback

Revert eval/dataset/CI/doc changes in allowed scope.

## Done criteria

- L5 eval suite exists.
- Dataset/grader/pass criteria are explicit.
- Eval failure blocks L5 release path.
- Fake-only limitations are documented.
- Tests/evals pass or blockers return to 总控.
- Source backfill updated or proposed.

## Stop conditions

Stop and return to 总控 if eval requires product behavior changes, raw provider payload persistence, fake-only quality claims, or unresolved Phase 11 gaps.