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

## Window Result

Status: `accepted_conditionally / implementation_slice_complete / source_backfill_pending`.

Initial controller accepted state:

`accepted_conditionally / implementation_slice_complete / source_backfill_pending`

Implemented scope:

- Added executable deterministic L5 eval runner: `scripts/evals/run_l5_eval_suite.py`.
- Added executable Phase 12 L5 suite manifest: `tests/evals/phase12/suite.json`.
- Added blocking datasets under `tests/evals/phase12/datasets/`:
  - `multi_agent_core.jsonl`
  - `failure_and_replay.jsonl`
  - `quality_lanes.jsonl`
  - `negative_control.jsonl`
- Added pytest coverage: `tests/evals/test_phase12_l5_eval_gate.py`.
- Added CI workflow binding in `.github/workflows/eval-gate.yml`.

Coverage:

- happy path: `p12_l5_happy_path_multi_agent`
- insufficient context: `p12_l5_insufficient_context_fail_closed`
- asset conflict: `p12_l5_asset_conflict_hitl`
- provider failure: `p12_l5_provider_failure_fail_closed`
- validation failure: `p12_l5_validation_failure_partial_result`
- HITL: `p12_l5_hitl_low_confidence_review`
- replay: `p12_l5_replay_read_only_trace_match`
- cross-agent handoff failure: `p12_l5_cross_agent_handoff_failure`
- fake / replay non-claim: `p12_l5_fake_replay_non_claim_visible`

Gate policy:

- `eval_failure_blocks_l5_release_path=true`.
- deterministic regression and replay regression are CI-safe and provider-free.
- provider-quality evidence is a separate non-CI default lane and is not claimed by this window.
- passing this gate is not an L5 release claim, not remote CI success, and not Phase 12 release gate closure.

Validation evidence:

```bash
PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals/test_phase12_l5_eval_gate.py -q
# 6 passed

PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals -q
# 41 passed

PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q
# 33 passed

PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic
# blocking_failures=0, total_cases=9, passed=9

PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_l5_eval_suite.py --mode deterministic --expect-fail-fixture
# negative_control_result.observed_expected_failure=true

PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_eval_gate.py --suite phase9 --mode replay
# blocking_failures=0, total_cases=30, passed=30, deferred=2

PYTHONPATH=.:apps/api .venv/bin/python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --expect-fail-fixture
# negative_control_result.observed_expected_failure=true
```

Source Backfill:

- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md updated.
- docs/project-sources/13_DECISION_LOG.md updated.
- docs/project-sources/14_RISK_REGISTER.md updated.
- docs/project-sources/12_ACCEPTANCE_GATES.md updated.
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md updated.

Post-backfill status:

`accepted_by_total_control / executable_eval_suite_foundation_committed_pending_p12w2_retry`

Non-claims:

- This window does not claim L5 release.
- This window does not claim real-provider quality certification.
- This window does not claim remote CI success.
- This window does not close the full Phase 12 release gate.
