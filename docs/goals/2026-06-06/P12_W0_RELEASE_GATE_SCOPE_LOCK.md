---
title: P12_W0_RELEASE_GATE_SCOPE_LOCK
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/p12-w0-release-gate-scope-lock
---

# P12-W0 Release Gate Scope Lock

Window ID: P12-W0-RELEASE-GATE-SCOPE-LOCK

Workspace Name: AiForInterviewer-P12-W0-RELEASE-GATE-SCOPE-LOCK

Phase:
- Phase 12
- L5 Eval, Hardening, and Release Gate
- Scope lock / release-gate design only
- Docs-only governance window

Expected current HEAD:
- d3a98d3 phase11: close out controlled multi-agent foundation

Capability IDs:
- L5-006 L5 eval / replay / release gate
- L5-004 Multi-agent product workflow
- L5-005 Controlled tool loop hardening
- EVAL-001 AI Eval gate
- RTE-003 Interrupt / resume / checkpoint / replay
- RTE-004 Replay read-only by default
- RTE-005 Runtime trace / timeline completeness
- RTE-006 Typed multi-agent handoff
- PRO-001 Compact provider request
- PRO-002 Provider boundary tests
- FAKE-001 Fake cleanup
- SRC-001 Source backfill
- WIN-001 Execution window protocol

## Goal

Create a docs-only Phase 12 release-gate scope lock before any Phase 12 implementation.

This window must:

1. Define Phase 12 release-gate scope.
2. Define multi-agent eval evidence requirements.
3. Define replay / resume evidence requirements.
4. Define CI artifact and report requirements.
5. Define trace / observability report requirements.
6. Define failure triage policy.
7. Define rollback policy.
8. Define human release decision requirements.
9. Define real-provider quality evidence boundary.
10. Define non-claims and stop conditions.
11. Reconcile P11 closeout state into Phase 12 entry criteria.
12. Update Project sources only where needed to record Phase 12 scope lock.

This window must not:

1. Implement eval datasets.
2. Implement eval graders.
3. Implement eval runner behavior.
4. Modify CI workflow.
5. Modify runtime behavior.
6. Modify provider behavior.
7. Modify prompt behavior.
8. Modify API / DB / frontend / domain behavior.
9. Rewrite eval reports.
10. Claim L5 release.
11. Claim real-provider quality certification.
12. Claim remote CI success.
13. Claim Phase 12 release gate completion.

## Source of Truth

Use this order:

1. GitHub main / local HEAD at latest pushed commit.
2. P11-W4 closeout and Phase 12 entry criteria.
3. Current Project source documents.
4. P11-W0 to P11-W3 post-push audit reports.
5. Current tests / eval results.
6. User-confirmed decisions.
7. GOAL0531 only as historical intent.

If sources conflict:

- Current repository files describe implementation facts.
- Project sources describe target architecture and claims.
- P11 audit reports describe accepted evidence.
- Differences must be recorded as gaps.
- Do not normalize release / quality / CI / eval gaps by wording.

## Audit / Planning Mode

This is a scope-lock and planning window.

Allowed:

- Read files.
- Run git and grep checks.
- Create Phase 12 scope-lock documents.
- Update Project source docs to record Phase 12 entry / gate semantics.

Forbidden:

- Modify code.
- Modify tests.
- Modify eval datasets.
- Modify eval suites.
- Modify eval graders.
- Modify eval runners.
- Modify eval reports.
- Modify scripts.
- Modify workflows.
- Modify provider / prompt / API / DB / frontend / domain files.
- Reformat unrelated docs.
- Fix implementation issues in this window.
- Claim release readiness.

If a problem is found, record it as gap / risk / stop condition. Do not patch behavior.

## Must Recon First

Read these Phase 11 closeout files:

- docs/goals/2026-06-06/P11_W4_PHASE11_CLOSEOUT_REPORT.md
- docs/goals/2026-06-06/P11_W4_SOURCE_SANITY_AUDIT_REPORT.md
- docs/goals/2026-06-06/P11_W4_PHASE12_ENTRY_CRITERIA.md
- docs/goals/2026-06-06/P11_W3_POST_PUSH_AUDIT_REPORT.md
- docs/goals/2026-06-06/P11_W2_POST_PUSH_AUDIT_REPORT.md
- docs/goals/2026-06-06/P11_W1_SOURCE_BACKFILL_REPORT.md
- docs/goals/2026-06-06/P11_W1_FIX01_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P11_W0_GAP_RECONCILIATION.md

Read current Project sources:

- docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md
- docs/project-sources/04_AGENT_DEFINITION_STANDARD.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

Read current eval / CI surfaces for factual recon only:

- evals/suites/phase9.json
- evals/datasets/phase9/
- evals/graders/code_rules.py
- scripts/evals/run_eval_gate.py
- .github/workflows/eval-gate.yml
- evals/reports/phase9_eval_report.json
- docs/goals/2026-06-06/P9_EVAL_REPORT.md

Read current candidate multi-agent surfaces for factual recon only:

- apps/api/app/application/agents/definitions/catalog.py
- apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py
- apps/api/app/application/agents/handoff/__init__.py
- apps/api/app/application/agents/runtime/__init__.py
- tests/application/agents/test_phase11_three_agent_product_slice.py
- tests/application/agents/test_phase11_runtime_hardening.py

## Allowed Files

Allowed to create:

- docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_LOCK.md
- docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_REPORT.md
- docs/goals/2026-06-06/P12_W0_RELEASE_EVIDENCE_CONTRACT.md
- docs/goals/2026-06-06/P12_W0_DECISION_OPTIONS.md
- docs/goals/2026-06-06/P12_W0_SOURCE_BACKFILL_REPORT.md

Allowed to update:

- docs/goals/README.md
- docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md
- docs/project-sources/04_AGENT_DEFINITION_STANDARD.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

## Forbidden Files

Do not modify:

- apps/**
- tests/**
- evals/**
- scripts/**
- .github/**
- package.json
- frontend files
- DB migrations
- prompt files
- provider files
- runtime implementation files
- API routes
- domain policy files
- eval reports

This window may read those files, but must not edit them.

## Behavior Change Allowed

No.

## Runtime / Provider / Prompt / API / DB Change Allowed

No.

## Eval / CI Change Allowed

No.

Do not rewrite:

- evals/reports/**
- docs/goals/2026-06-06/P9_EVAL_REPORT.md
- evals/reports/P9_EVAL_REPORT.md
- evals/reports/phase9_eval_report.json

## Phase 12 Scope to Define

Phase 12 name:

- L5 Eval, Hardening, and Release Gate

Phase 12 goal:

- Prove that the controlled multi-agent system can be considered for L5 product release through eval, replay, CI, observability, failure triage, rollback and human release decision.

Phase 12 must cover:

1. Multi-agent eval datasets.
2. Multi-agent graders.
3. Cross-agent replay fixtures.
4. Failure-mode regression cases.
5. CI gate and artifact requirements.
6. Trace / observability report.
7. Failure triage policy.
8. Rollback policy.
9. Human release decision.
10. Release readiness audit.

Phase 12 must not cover unless separately scoped:

1. New product features.
2. New provider behavior.
3. Prompt rewrites.
4. API contract changes.
5. DB migrations.
6. Domain policy changes.
7. Frontend release changes.
8. Formal business writes by Agent.
9. Unbounded autonomous loops.

## Required Release Evidence Contract

Create `P12_W0_RELEASE_EVIDENCE_CONTRACT.md`.

It must define these evidence categories:

### 1. Eval Evidence

Required:

- multi-agent dataset manifest
- capability IDs covered
- case IDs
- input refs
- expected candidate refs
- expected handoff refs
- expected validation refs
- expected HITL refs
- expected failure mode
- expected non-claims
- grader refs
- minimum pass criteria

Must include cases for:

- happy path candidate product slice
- insufficient context
- asset conflict
- formal write requested
- low confidence
- provider failure
- validation failure
- cross-agent handoff failure
- replay mismatch
- forbidden data
- fake/replay non-claim
- release non-claim

### 2. Replay Evidence

Required:

- replay fixture refs
- checkpoint refs
- read_only true
- formal_write_blocked true
- zero provider calls
- zero DB writes
- zero formal writes
- trace comparison
- candidate refs preserved
- validation refs preserved
- handoff refs preserved

### 3. CI Evidence

Required:

- CI workflow name
- command list
- report artifact name
- artifact retention expectation
- blocking failure behavior
- negative-control behavior
- no live provider credentials required for default gate
- optional real-provider advisory mode must be explicit and non-default

### 4. Observability Evidence

Required:

- trace report schema
- agent_id
- run_id
- plan_refs
- skill_refs
- tool_refs
- policy_refs
- candidate_refs
- handoff_refs
- validation_refs
- HITL refs
- failure_reason
- fallback_reason
- forbidden data scan result

### 5. Release Decision Evidence

Required:

- human/controller release decision
- accepted risk list
- deferred gaps list
- rollback plan
- release version / tag ref
- date / actor
- evidence links
- non-claims

## Required Phase 12 Gate

Update Acceptance Gates with a Phase 12 Release Gate if missing.

Gate must require:

1. Phase 11 closeout accepted.
2. L5-006 implementation scoped.
3. Multi-agent eval suite exists.
4. Multi-agent replay fixtures exist.
5. Failure-mode cases exist.
6. CI gate runs and records artifact.
7. Blocking failures fail the gate.
8. Negative-control proves gate can fail.
9. Trace report generated.
10. Report output scanned for forbidden data.
11. Fake/replay evidence not represented as real-provider quality.
12. Real-provider quality, if claimed, has separately scoped evidence.
13. Formal writes remain blocked unless formal release scope explicitly authorizes and proves Application Service -> Domain Policy -> Handoff.
14. Human release decision recorded.
15. Rollback policy documented.
16. L5 release cannot be claimed until all required evidence passes.

## Required Decision Options

Create `P12_W0_DECISION_OPTIONS.md`.

It must contain 2-4 proposed options for the next window. Do not confirm any option.

Minimum options:

### Option A: Eval-contract-first

Next window creates Phase 12 suite manifest, dataset skeleton, grader contract and report schema, but does not run CI or generate release report.

Pros:
- safest
- avoids fake release claims
- makes evidence shape explicit

Cons:
- no executable gate yet

### Option B: Replay-gate-first

Next window implements replay fixtures and replay gate for P11 candidate product slice.

Pros:
- directly tests multi-agent reproducibility
- closes replay evidence gap first

Cons:
- may leave broader eval coverage incomplete

### Option C: CI-artifact-first

Next window wires Phase 12 CI gate with placeholder / deterministic test commands and artifact upload policy.

Pros:
- establishes release evidence logistics early
- prevents local-only quality claims

Cons:
- risk of CI plumbing before substantive eval coverage

### Option D: Full Phase 12 eval gate slice

Next window implements minimal multi-agent dataset, grader, runner integration, replay report and CI artifact in one window.

Pros:
- fastest path to an executable gate

Cons:
- highest scope risk
- must be tightly scoped to avoid release overclaim

The document may recommend a preferred option, but status must remain proposed and require Controller/user confirmation.

## Matrix Requirements

Update Matrix if needed:

- L5-006 remains not_started or implementation_planned in P12-W0.
- Do not mark L5-006 implemented / validated / done.
- Add P12-W0 as design_done or implementation_planned only if the Matrix uses such status for release-gate scope lock.
- Do not mark L5 release done.
- Do not upgrade EVAL-001 to done.
- Keep remote CI gap open unless visible CI evidence is cited.
- Preserve stale eval metadata risk unless a separate report refresh window resolves it.

Allowed status if missing:

- release_gate_scope_locked

Use only for P12-W0 planning, not release completion.

## Risk Register Requirements

Add or update risks for:

1. Phase 12 release overclaim.
2. Fake/replay eval mistaken as real-provider quality.
3. CI workflow existence mistaken as passing artifact evidence.
4. Local eval pass mistaken as remote CI pass.
5. Trace report storing forbidden payloads.
6. Release without rollback plan.
7. Release without human decision.
8. Formal write boundary weakened during release.
9. Negative-control omitted.
10. Multi-agent eval coverage too narrow.

## Phase Roadmap Requirements

Update Phase 12 section if needed:

- P12-W0 = Release Gate Scope Lock.
- Phase 12 implementation has not started.
- L5 release has not been claimed.
- First implementation window remains pending Controller option choice.
- Phase 12 is release evidence and hardening, not new product feature scope.

## Required Git Checks

Run:

- git status --short --untracked-files=all
- git rev-parse HEAD
- git log --oneline -8
- git diff --check
- git diff --stat
- git diff --name-only

Final diff must contain only allowed docs files.

## Required Grep Checks

Run:

- rg "L5-001|L5-002|L5-003|L5-004|L5-005|L5-006" docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- rg "L5 release|real-provider quality certification|remote CI success|Phase 12 release gate done|formal write completed|product workflow release|full L5 validation complete" docs/project-sources docs/goals apps tests
- rg "evals/reports|phase9_eval_report|P9_EVAL_REPORT" docs/goals/2026-06-06 docs/project-sources
- rg "fake-only|replay-only|unit-test-only|negative-control|artifact|rollback|human release decision" docs/goals/2026-06-06 docs/project-sources

Expected:

- Overclaim matches must be non-claims, forbidden wording, stop conditions or audit text.
- Eval report mentions must not imply rewriting.
- Release evidence terms must be scope / requirement, not completion claim.

## Optional Validation Commands

Because this is docs-only, pytest is optional.

If environment is available, run:

- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_three_agent_product_slice.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_runtime_hardening.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_l5_orchestrator_contract.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_agent_contracts.py -q

If not run, state that P12-W0 is docs-only and relies on accepted P11-W4 closeout evidence.

## Classification

Return one of:

PASS:

- Scope lock created.
- Release evidence contract created.
- Decision options created.
- Phase 12 entry / gate semantics updated.
- No implementation files changed.
- No eval files changed.
- No release or quality overclaim.
- L5-006 not marked done.
- Phase 12 implementation remains pending.

WARN:

- Scope lock created, but Project sources still have wording risk.
- Optional tests not run but no behavior changed.
- Some evidence gaps need explicit follow-up.

FAIL:

- Implementation files changed.
- Eval runner/datasets/reports/workflows changed.
- L5 release claimed.
- Real-provider quality claimed.
- Remote CI success claimed without visible artifact.
- L5-006 marked implemented / validated / done.
- Phase 12 gate marked complete.
- Eval reports rewritten.

## Reports Required

Create:

- docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_REPORT.md
- docs/goals/2026-06-06/P12_W0_RELEASE_EVIDENCE_CONTRACT.md
- docs/goals/2026-06-06/P12_W0_DECISION_OPTIONS.md
- docs/goals/2026-06-06/P12_W0_SOURCE_BACKFILL_REPORT.md

Update allowed Project sources as needed.

## P12_W0_RELEASE_GATE_SCOPE_REPORT.md format

1. Executive Verdict
2. Source of Truth Applied
3. Phase 12 Scope
4. Allowed / Forbidden Scope
5. Release Evidence Categories
6. Current Gaps
7. Non-Claims
8. Validation Commands and Results
9. Final Status

## P12_W0_RELEASE_EVIDENCE_CONTRACT.md format

1. Purpose
2. Eval Evidence Contract
3. Replay Evidence Contract
4. CI Evidence Contract
5. Observability Evidence Contract
6. Release Decision Evidence Contract
7. Forbidden Data Rules
8. Non-Claims
9. Closure Criteria

## P12_W0_DECISION_OPTIONS.md format

1. Decision Status
2. Option A Eval-contract-first
3. Option B Replay-gate-first
4. Option C CI-artifact-first
5. Option D Full Phase 12 eval gate slice
6. Recommendation
7. Required Controller Confirmation

## P12_W0_SOURCE_BACKFILL_REPORT.md format

1. Backfill Scope
2. Project Source Updates
3. Matrix Status Treatment
4. Risk Treatment
5. Phase 12 Entry Treatment
6. Non-Claims
7. Final Status

## Done Criteria

P12-W0 is accepted only if:

1. Release gate scope is locked.
2. Release evidence contract exists.
3. Decision options exist and remain proposed.
4. Project sources are updated where necessary.
5. L5-006 is not marked implemented / validated / done.
6. L5 release is not claimed.
7. Real-provider quality is not claimed.
8. Remote CI success is not claimed.
9. Eval reports are not rewritten.
10. No code / tests / evals / scripts / workflows / provider / prompt / API / DB / domain / frontend files changed.
11. Final status is one of:
    - release_gate_scope_locked_with_deferred_implementation
    - release_gate_scope_warn_with_remediation
    - release_gate_scope_failed

## Stop Conditions

Stop and report FAIL if any of these are required:

- modifying code
- modifying tests
- modifying eval files
- modifying scripts or workflows
- modifying provider / prompt / API / DB / domain / frontend files
- rewriting eval reports
- claiming L5 release
- claiming Phase 12 release gate complete
- claiming real-provider quality certification
- claiming remote CI success without visible artifact
- marking L5-006 implemented / validated / done
- implementing eval runner / dataset / grader / CI behavior in this window