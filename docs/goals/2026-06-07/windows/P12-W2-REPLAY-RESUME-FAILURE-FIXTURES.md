---
title: P12-W2-REPLAY-RESUME-FAILURE-FIXTURES
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/windows/p12-w2-replay-resume-failure-fixtures
---
Current Accepted State:
P11-W5 accepted by 总控.
Phase 11 is closeable as closed_with_l5_release_gate_deferred.

Capability State:
- L5-002 validated/high
- L5-003 validated/high
- L5-004 validated/high
- L5-005 validated/high
- L5-006 remains release-blocking

Non-Claims:
- Do not claim L5 release.
- Do not claim real-provider quality certification.
- Do not claim remote CI success unless remote artifact exists.
- Do not claim Phase 12 release gate closure.

P12-W2 Preflight:
Before patching replay/resume/failure fixtures, inspect existing Phase 12 eval artifacts:
- evals/suites/phase12.json
- tests/evals/test_phase12_eval_contracts.py
- tests/evals/**
- scripts/**
- .github/workflows/**

Decision:
- If existing Phase 12 suite has sufficient dataset / grader / regression cases for replay fixture integration, continue P12-W2.
- If it is contract-only and cannot support replay fixture validation, stop and report that P12-W1-MULTI-AGENT-EVAL-SUITE must be inserted before P12-W2.

Forbidden:
- No provider behavior change.
- No prompt rewrite.
- No DB schema / migration.
- No frontend / API contract change.
- No fake-only L5 quality claim.
- No raw prompt / raw provider payload persistence.
- No L5 release claim.

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

## Window Result

Status: `complete_preflight_stop`.

Blocker: `blocked_by_missing_executable_phase12_eval_suite`.

Accepted result:

- P12-W2 preflight stop is accepted by 总控.
- P12-W2 replay / resume / failure fixtures were not implemented.
- Existing Phase 12 eval artifacts are contract-only and cannot support replay fixture validation.
- `P12-W1-MULTI-AGENT-EVAL-SUITE` must be inserted before retrying P12-W2.
- `L5-006` remains release-blocking.
- This is not L5 release.
- This is not Phase 12 release gate closure.

Preflight evidence preserved:

- `evals/suites/phase12.json` is `contract_only`.
- Phase 12 suite flags remain false: `eval_runner_required=false` and `release_gate_pass_required=false`.
- `evals/graders/phase12_contract.json` is a data contract, not an executable Python grader.
- Current grader contract declares `python_grader`, `runner_integration`, `ci_binding`, `report_generation` and `negative_control_execution` not created in P12-W1.
- `.github/workflows/eval-gate.yml` is still bound to the Phase 9 eval gate only.

Validation evidence preserved:

- `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/evals -q` -> `35 passed`.
- `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q` -> `33 passed`.

Source-of-truth treatment:

- `USER_CONFIRMED`: 总控已接受本 preflight stop 结论。
- `GITHUB_CODE`: 当前仓库文件是当前实现事实源。
- `TEST_RESULT`: 当前测试 / eval 结果是行为证据源。
- `PROJECT_SOURCE`: Project source 是目标架构、窗口协议和验收规则源。
- `GOAL0531`: 历史目标和阶段意图源，不得当作当前代码事实源。

Non-claims:

- P12-W2 does not implement replay fixtures.
- P12-W2 does not implement resume fixtures.
- P12-W2 does not implement failure fixtures.
- P12-W2 does not modify code, tests, CI, provider, prompt, DB, API or frontend.
- P12-W2 does not mark `L5-006` implemented, validated or done.
