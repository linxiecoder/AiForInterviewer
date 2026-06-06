---
title: P12-W3-CI-OBSERVABILITY-TRACE-REPORT
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p12-w3-ci-observability-trace-report
---

# P12-W3-CI-OBSERVABILITY-TRACE-REPORT

## Activation rule

Execute after P12-W1 and P12-W2 provide eval/replay evidence.

## Window ID

`P12-W3-CI-OBSERVABILITY-TRACE-REPORT`

## Phase

Phase 12 — L5 Eval, Hardening, and Release Gate

## Capability IDs

- L5-006
- EVAL-001
- AGT-007
- WIN-001

## Goal

Add or document L5 CI gate, observability/trace report, failure triage policy, and rollback policy.

## Must recon first

- CI workflow files
- eval runner scripts
- trace report generation or trace schema
- source docs for Acceptance Gates, Risk Register, Matrix, Roadmap

## Allowed files

```text
.github/workflows/**
scripts/**
tests/evals/**
tests/architecture/**
docs/**
project_sources/**
```

## Forbidden files

```text
production provider behavior
production DB implementation
database migrations
prompt rewrites
API contract changes
unrelated product code
```

## Behavior change allowed

No product behavior change.

## Prompt/schema/provider change allowed

No.

## DB schema change allowed

No.

## Implementation requirements

- Define or wire L5 CI command.
- Ensure eval failure blocks L5 release gate.
- Generate or document trace report fields:
  - agent_id;
  - run_id;
  - plan_refs;
  - skill_refs;
  - tool_refs;
  - policy_refs;
  - handoff_refs;
  - validation_refs;
  - failure_reason;
  - fallback_reason.
- Define failure triage categories.
- Define rollback policy for L5 release.
- Document limitations if CI cannot run provider-quality eval.

## Validation commands

```bash
pytest tests/evals
pytest tests/architecture
```

Run CI-equivalent script if present.

## Rollback

Revert CI/scripts/docs changes in allowed scope.

## Done criteria

- L5 CI gate exists or is explicitly documented with runnable command.
- Eval failure blocks release path.
- Trace report exists or is documented with required fields.
- Failure triage and rollback policy are explicit.
- Source backfill updated or proposed.

## Stop conditions

Stop and return to 总控 if CI gate would rely only on fake eval while claiming real AI quality, or if trace report requires persisting forbidden raw data.