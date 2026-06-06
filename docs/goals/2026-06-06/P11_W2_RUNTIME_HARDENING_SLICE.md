---
title: P11_W2_RUNTIME_HARDENING_SLICE
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/p11-w2-runtime-hardening-slice
---

# P11-W2 Runtime-hardening Slice

Window ID: P11-W2-RUNTIME-HARDENING-SLICE

Workspace Name: AiForInterviewer-P11-W2-RUNTIME-HARDENING-SLICE

Phase:
- Phase 11
- L5 Controlled Multi-Agent Orchestration
- Runtime-hardening slice after P11-W1 contract-first Orchestrator

Capability IDs:
- L5-003 Cross-agent handoff / state / trace
- L5-005 Controlled tool loop hardening
- AGT-005 AgentExecutor port
- AGT-006 Handoff contract
- AGT-007 Agent Trace Contract
- RTE-001 LangGraph runtime adapter / AgentExecutor integration
- RTE-002 Controlled tool loop bounds
- RTE-003 Interrupt / resume / checkpoint / replay
- RTE-004 Replay read-only by default
- RTE-005 Runtime trace / timeline completeness
- RTE-006 Typed multi-agent handoff
- SRC-001 Source backfill
- WIN-001 Execution window protocol

## Goal

Implement a narrow runtime-hardening slice for future controlled multi-agent orchestration.

This window must harden runtime-facing primitives that P11-W3 product workflow would need, without implementing the product workflow itself.

Target hardening areas:

1. Cross-agent handoff execution guard.
2. Cross-agent checkpoint / resume input validation.
3. Cross-agent replay safety and read-only enforcement.
4. Cross-agent trace / timeline ref completeness.
5. HITL trigger validation for handoff / formal write / asset conflict / low confidence / ambiguous ownership.
6. Failure semantics for invalid cross-agent handoff.
7. Owner-scope and idempotency validation for handoff and resume surfaces.

This window must not:

1. Implement a three-agent product vertical slice.
2. Execute `interview_orchestrator_agent` as a runtime agent.
3. Wire Orchestrator into API routes, application polish services, Question workflow, Feedback workflow, provider, prompt, DB, frontend or domain policies.
4. Claim L5 release.
5. Claim real-provider quality certification.
6. Close Phase 12 release gate.
7. Rewrite eval reports.
8. Close Phase 8 runtime gaps by wording only.

## Source of Truth

Use this order:

1. User-confirmed decision: P11-W2 Runtime-hardening slice.
2. GitHub main current code and docs.
3. Current tests / eval results.
4. Project source documents.
5. P11-W0 / P11-W1 / P11-W1.fix.01 evidence.
6. GOAL0531 only as historical intent.
7. Child-agent output only after audit.

If sources conflict:

- GitHub main describes current implementation.
- Project source describes target.
- Difference must be recorded as a gap.
- Do not normalize runtime/product/release gaps by wording.

## Required Precondition

P11-W1.fix.01 must be accepted as:

- source_backfill_wording_reconciled

Current expected status before this window:

- `L5-002`: `contract_slice_complete_with_deferred_runtime_gaps`
- `L5-003`: `contract_slice_complete_with_deferred_runtime_gaps`
- `L5-004`: `not_started`
- `L5-005`: `implementation_planned`
- `L5-006`: `not_started`

This window may update `L5-005` to a runtime-hardening slice status only if runtime hardening is implemented and locally validated.

Do not mark any L5 capability as `done`.

## Must Recon First

Read before patch:

Project sources:
- docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md
- docs/project-sources/04_AGENT_DEFINITION_STANDARD.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

P11 evidence:
- docs/goals/2026-06-06/P11_W0_GAP_RECONCILIATION.md
- docs/goals/2026-06-06/P11_W1_CONTRACT_FIRST_ORCHESTRATOR.md
- docs/goals/2026-06-06/P11_W1_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P11_W1_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P11_W1_SOURCE_BACKFILL_REPORT.md
- docs/goals/2026-06-06/P11_W1_FIX01_VALIDATION_REPORT.md

Runtime / contract code:
- apps/api/app/application/agents/contracts/__init__.py
- apps/api/app/application/agents/definitions/catalog.py
- apps/api/app/application/agents/definitions/orchestrator.py
- apps/api/app/application/agents/registry/__init__.py
- apps/api/app/application/agents/handoff/__init__.py
- apps/api/app/application/agents/runtime/__init__.py
- apps/api/app/application/ai_runtime/contracts.py

Existing tests:
- tests/architecture/test_agent_platform_l5_orchestrator_contract.py
- tests/application/agents/test_phase8_agent_executor_adapter.py
- tests/api/test_agent_contracts.py
- tests/api/test_agent_graph_runner.py

## Allowed Files

Code allowed:

- apps/api/app/application/agents/contracts/__init__.py
- apps/api/app/application/agents/handoff/__init__.py
- apps/api/app/application/agents/runtime/__init__.py

Tests allowed:

- tests/application/agents/test_phase11_runtime_hardening.py
- tests/application/agents/test_phase8_agent_executor_adapter.py
- tests/architecture/test_agent_platform_l5_orchestrator_contract.py
- tests/api/test_agent_contracts.py

Docs allowed:

- docs/goals/2026-06-06/P11_W2_RUNTIME_HARDENING_SLICE.md
- docs/goals/2026-06-06/P11_W2_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P11_W2_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P11_W2_SOURCE_BACKFILL_REPORT.md
- docs/goals/README.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

## Forbidden Files

Do not modify:

- apps/api/app/application/ai_runtime/**
- apps/api/app/application/polish/**
- apps/api/app/application/llm/**
- apps/api/app/domain/**
- apps/api/app/infrastructure/**
- apps/api/app/api/**
- frontend files
- DB migrations
- prompt assets
- provider boundary implementation
- eval datasets
- eval graders
- eval suites
- eval reports
- scripts
- .github/workflows
- package.json

Exception:
- apps/api/app/application/ai_runtime/contracts.py may be read for recon only. Do not modify it.

If the desired runtime hardening requires changing `apps/api/app/application/ai_runtime/**`, stop and return to Controller.

## Behavior Change Allowed

Only internal Agent Platform runtime-hardening behavior is allowed.

Allowed behavior changes are limited to:

- fail-closed validation for invalid cross-agent handoff input
- fail-closed validation for missing trace refs
- fail-closed validation for missing validation refs
- fail-closed validation for owner-scope mismatch
- fail-closed validation for missing checkpoint / base_version / idempotency_key on cross-agent resume payloads
- read-only replay guard for cross-agent replay metadata
- refs-only trace and timeline mapping for cross-agent handoff events

No product business behavior change is allowed.

## Runtime Change Allowed

Narrow runtime hardening is allowed only inside:

- apps/api/app/application/agents/handoff/__init__.py
- apps/api/app/application/agents/runtime/__init__.py

Forbidden runtime behavior:

- no Orchestrator runtime execution
- no new LangGraph graph
- no new graph descriptor for Orchestrator
- no API route wiring
- no Question / Feedback product path change
- no persistence change
- no provider call
- no prompt rendering
- no DB access
- no formal write

## Implementation Requirements

### 1. Cross-agent handoff hardening

Harden existing handoff helpers or add new helpers under the Agent Platform handoff boundary.

Required behavior:

- Validate source agent id.
- Validate target agent id.
- Validate candidate type is allowed by `CrossAgentHandoffRoute`.
- Validate trace refs are present.
- Validate validation refs are present.
- Validate side effect policy is `read_only`, `candidate_write`, or `formal_write_handoff_only`.
- Reject `formal_refs` and any formal-write metadata.
- Reject raw prompt, raw completion, provider payload, full resume, full JD, full answer, full asset body, token, secret, cookie, API key.
- Preserve only refs-only handoff metadata.
- Return a candidate / plan / blocked result, not a formal write.

If an existing `execute_agent_handoff()` exists, harden it. Do not duplicate a parallel implementation unless necessary.

### 2. Checkpoint / resume validation

Add contract or helper validation for cross-agent resume payloads.

Required fields:

- checkpoint_ref
- base_version
- idempotency_key
- owner_id or owner_ref
- interrupt_ref when resuming an interrupt
- allowed_action or resume_action

Rules:

- base_version must be a non-negative integer.
- idempotency_key must be non-empty.
- checkpoint_ref must be non-empty.
- owner scope must match expected owner.
- unsupported resume action must fail closed.
- resume payload must be sanitized and must not include raw payloads.

Do not persist checkpoint state in this window.

### 3. Replay hardening

Add validation that cross-agent replay metadata remains:

- read_only
- formal_write_blocked
- zero provider calls
- zero tool external calls unless explicitly replay-local and read-only
- zero repository writes
- zero DB business writes
- zero formal business writes

Replay result must not include raw prompt, raw completion, provider payload or full business bodies.

Do not add new replay storage in this window.

### 4. Trace / timeline hardening

Add refs-only cross-agent trace or timeline mapping helpers if needed.

Required refs:

- plan_refs
- handoff_refs
- validation_refs
- candidate_refs
- policy_refs
- tool_refs where applicable
- low_confidence_flags where applicable
- failure_reason when blocked or failed
- interrupt_refs when HITL is required

Rules:

- trace / timeline metadata must be sanitized.
- validation refs and handoff refs must not be collapsed into output refs.
- no raw prompt, raw provider payload or full body metadata.

### 5. HITL trigger validation

Validate these trigger types as refs-only control events:

- asset_conflict
- formal_write_requested
- low_confidence
- ambiguous_ownership
- validation_failed_partial_result

Rules:

- any formal_write_requested trigger must interrupt or block; it must not return success.
- asset_conflict must interrupt or block.
- low_confidence may interrupt or mark low confidence, but must be trace-visible.
- validation_failed_partial_result must not be reported as generated success.

### 6. Status and failure semantics

Use fail-closed statuses.

Allowed examples:

- blocked
- validation_failed
- interrupted
- requires_user_confirmation
- replayed
- cancelled

Do not return success-like statuses when `failure_reason` is present.

### 7. Matrix status

If this window passes, update Matrix:

- Add status `runtime_hardening_slice_complete_with_deferred_product_workflow` if missing.
- Set `L5-005` to `runtime_hardening_slice_complete_with_deferred_product_workflow` only if implementation and tests pass.
- Keep `L5-004` as `not_started`.
- Keep `L5-006` as `not_started`.
- Keep `L5-002` and `L5-003` as `contract_slice_complete_with_deferred_runtime_gaps` unless this window directly updates their contract wording without claiming runtime completion.

Do not mark any L5 capability as done.

## Architecture / Safety Gates

Add or update tests proving:

1. Cross-agent handoff fails closed when trace refs are missing.
2. Cross-agent handoff fails closed when validation refs are missing.
3. Cross-agent handoff fails closed when candidate type is not allowed by route.
4. Cross-agent handoff fails closed on source / target mismatch.
5. Cross-agent handoff rejects formal refs.
6. Cross-agent handoff rejects raw prompt / provider payload / full body metadata.
7. Cross-agent resume validation fails closed without checkpoint_ref.
8. Cross-agent resume validation fails closed without base_version.
9. Cross-agent resume validation fails closed without idempotency_key.
10. Cross-agent replay validation rejects non-read-only or formal-write metadata.
11. HITL formal_write_requested does not return success.
12. HITL asset_conflict does not return success.
13. Trace mapping preserves plan / handoff / validation / candidate refs separately.
14. Orchestrator is still not runtime-wired into ai_runtime, polish, API, domain or infrastructure.
15. No product workflow is executed.

## Required Non-Claims

Every report and source backfill must state:

- P11-W2 does not implement product multi-agent workflow.
- P11-W2 does not execute `interview_orchestrator_agent` as a runtime agent.
- P11-W2 does not close all Phase 8 runtime gaps.
- P11-W2 does not close `deferred_remote_ci_gap`.
- P11-W2 does not rewrite stale eval reports.
- P11-W2 does not certify real-provider quality.
- P11-W2 does not claim L5 release.
- P11-W2 does not implement Phase 12 release gate.
- P11-W2 does not change provider, prompt, API, DB, frontend, domain policy or business persistence behavior.

## Validation Commands

Required:

- git status --short --untracked-files=all
- git diff --check
- git diff --stat
- git diff --name-only
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_runtime_hardening.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase8_agent_executor_adapter.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_l5_orchestrator_contract.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_agent_contracts.py -q

Recommended if runtime surface is touched:

- PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_agent_graph_runner.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture -q

Required forbidden path check:

- git diff --name-only

Changed files must not include forbidden paths.

Required grep checks:

- rg "interview_orchestrator_agent" apps/api/app/application/ai_runtime apps/api/app/application/polish apps/api/app/api apps/api/app/domain apps/api/app/infrastructure
- rg "L5 release|real-provider quality certification|Phase 12 release gate done|product multi-agent workflow done" docs/project-sources docs/goals apps tests
- rg "raw_prompt|raw_provider_payload|provider_payload|full_resume|full_jd|full_answer|full_asset_body|api_key|token|secret|cookie" apps/api/app/application/agents tests/application/agents tests/architecture

Interpret grep results in context. Contract forbidden-data catalogs and negative tests are allowed. Runtime leaks or completion claims are not allowed.

## Done Criteria

P11-W2 is accepted only if:

1. Cross-agent handoff hardening exists and fails closed.
2. Cross-agent resume/checkpoint validation exists and fails closed.
3. Cross-agent replay safety validation exists and fails closed.
4. Cross-agent trace/timeline refs remain refs-only and separated.
5. HITL trigger validation blocks or interrupts formal_write_requested and asset_conflict.
6. Tests cover negative cases.
7. No product multi-agent workflow is implemented.
8. Orchestrator remains not runtime-wired.
9. No provider/prompt/API/DB/frontend/domain/business persistence behavior changes.
10. No eval reports are rewritten.
11. Phase 8 remaining gaps are explicitly carried.
12. `deferred_remote_ci_gap` remains open.
13. L5 release is not claimed.
14. Source backfill updates Matrix / Acceptance Gates / Risk Register / Roadmap as needed.
15. Final status is one of:
    - runtime_hardening_slice_complete_with_deferred_product_workflow
    - blocked_needs_controller_decision
    - failed_scope_violation

## Stop Conditions

Stop and return to Controller if any of these are required:

- modifying apps/api/app/application/ai_runtime/**
- modifying apps/api/app/application/polish/**
- modifying provider / prompt / API / DB / domain / frontend files
- modifying eval datasets, suites, graders, reports or workflow files
- adding a new LangGraph graph
- adding Orchestrator runtime descriptor
- adding API entrypoint
- adding product multi-agent workflow
- changing Question or Feedback business behavior
- persisting cross-agent state
- storing raw payloads
- direct repository or DB access
- formal writes from Agent output
- claiming L5 release
- closing Phase 8 gaps by wording only
- marking L5-004 or L5-006 implemented / validated / done
- marking L5-005 done

## Final Output Required

Return:

1. Root Cause
2. What Changed
3. Files Changed
4. Behavior Before / After
5. Runtime Hardening Added
6. Tests Added / Updated
7. Source Backfill
8. Validation Commands and Results
9. Remaining Risks
10. Follow-up Goal

Allowed final status:

- runtime_hardening_slice_complete_with_deferred_product_workflow
- blocked_needs_controller_decision
- failed_scope_violation

## P11-W2 Execution Result

Status: `runtime_hardening_slice_complete_with_deferred_product_workflow`

P11-W2 implemented the selected Runtime-hardening slice only. The slice hardens route-bound cross-agent handoff validation, cross-agent resume/checkpoint validation, read-only/formal-write-blocked replay validation, refs-only trace/timeline mapping and HITL trigger validation.

Implemented hardening evidence:

- Route-bound cross-agent handoff validates source agent id, target agent id, allowed candidate type, payload schema, required trace refs and required validation refs.
- Handoff rejects formal refs, unsafe metadata and raw/full/provider/security metadata keys.
- Cross-agent resume strict mode validates `checkpoint_ref`, non-negative integer `base_version`, `idempotency_key`, owner scope, `interrupt_ref` and supported resume action.
- Cross-agent replay strict mode validates `read_only`, `formal_write_blocked` and zero provider/tool/repository/DB/formal-write metadata.
- Cross-agent trace/timeline mapping preserves plan, handoff, validation and candidate refs separately.
- HITL validation covers `formal_write_requested`, `asset_conflict`, `low_confidence`, `ambiguous_ownership` and `validation_failed_partial_result`.

Validation summary:

- `tests/application/agents/test_phase11_runtime_hardening.py`: `9 passed`.
- `tests/application/agents/test_phase8_agent_executor_adapter.py`: `2 passed`.
- `tests/architecture/test_agent_platform_l5_orchestrator_contract.py`: `5 passed`.
- `tests/api/test_agent_contracts.py`: `16 passed`.
- Recommended runtime adapter regression `tests/api/test_agent_graph_runner.py`: `23 passed`.
- Recommended architecture regression `tests/architecture`: `29 passed`.

Non-claims:

- P11-W2 does not implement product multi-agent workflow.
- P11-W2 does not execute `interview_orchestrator_agent` as a runtime agent.
- P11-W2 does not close all Phase 8 runtime gaps.
- P11-W2 does not close `deferred_remote_ci_gap`.
- P11-W2 does not rewrite stale eval reports.
- P11-W2 does not certify real-provider quality.
- P11-W2 does not claim L5 release.
- P11-W2 does not implement Phase 12 release gate.
- P11-W2 does not change provider, prompt, API, DB, frontend, domain policy or business persistence behavior.
