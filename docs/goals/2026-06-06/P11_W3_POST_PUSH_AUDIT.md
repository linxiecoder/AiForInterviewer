---
title: P11_W3_POST_PUSH_AUDIT
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/p11-w3-post-push-audit
---

# P11-W3 Post-push Audit and Source Sanity Check

Window ID: P11-W3-POST-PUSH-AUDIT-SOURCE-SANITY

Workspace Name: AiForInterviewer-P11-W3-POST-PUSH-AUDIT

Phase:
- Phase 11
- Post-push audit
- Read-only source sanity check
- Docs-only audit report

Commit under audit:
- c0294b1 phase11: add candidate-only three-agent product slice

Base commit:
- e49300d phase11: add p11-w2 post-push audit

Capability IDs:
- L5-002 Supervisor / Orchestrator Agent
- L5-003 Cross-agent handoff / state / trace
- L5-004 Multi-agent product workflow
- L5-005 Controlled tool loop hardening
- L5-006 L5 eval / replay / release gate
- AGT-002 AgentDefinitionRegistry
- AGT-003 SkillRegistry
- AGT-004 ToolRegistry
- AGT-006 Handoff contract
- AGT-007 Agent Trace Contract
- RTE-006 Typed multi-agent handoff
- SRC-001 Source backfill
- WIN-001 Execution window protocol

## Goal

Perform a post-push audit of P11-W3.

The audit must verify:

1. Commit range is exactly P11-W3:
   - base: e49300d
   - head: c0294b1
2. Changed files are inside P11-W3 allowed scope.
3. No forbidden paths changed.
4. C1 catalog remains unchanged and still contains only:
   - polish_question_agent
   - polish_feedback_agent
5. L5 catalog includes at least:
   - polish_feedback_agent
   - interview_orchestrator_agent
   - asset_candidate_agent
   - training_plan_agent
6. Minimal three-agent product slice exists and is candidate-only.
7. Product slice participant business agents include:
   - polish_feedback_agent
   - asset_candidate_agent
   - training_plan_agent
8. Product slice does not call:
   - LLM
   - provider
   - prompt builder
   - DB
   - repository
   - API
   - domain policy
   - frontend
9. Product slice does not write formal business facts.
10. Asset update candidate requires user confirmation.
11. Formal write remains blocked.
12. Trace refs, validation refs and handoff refs remain separated.
13. Asset conflict blocks or interrupts.
14. Formal write requested blocks or interrupts.
15. Source backfill does not overclaim:
   - no L5 release
   - no Phase 12 release gate
   - no real-provider quality certification
   - no remote CI success
   - no formal write completion
16. Matrix states are sane:
   - L5-002 remains not done
   - L5-003 remains not done
   - L5-004 may be candidate_product_slice_complete_with_deferred_formal_write_and_release_gate
   - L5-005 remains runtime-hardening slice status or weaker
   - L5-006 remains not_started
   - no L5 capability is marked done
17. Validation evidence is present and consistent.

## Source of Truth

Use this order:

1. GitHub main / local HEAD at c0294b1.
2. Git diff e49300d..c0294b1.
3. P11-W3 validation report.
4. Current Project source docs after P11-W3.
5. User-provided push output only as supporting evidence.

If sources conflict:

- Git diff and current files describe implementation facts.
- Project sources describe target / claims.
- Differences must be recorded as gaps.
- Do not normalize gaps by wording.

## Audit Mode

This is an audit window.

Allowed:
- Read files.
- Run validation commands.
- Create audit report:
  - docs/goals/2026-06-06/P11_W3_POST_PUSH_AUDIT_REPORT.md

Forbidden:
- Modify code.
- Modify tests.
- Modify Project source docs.
- Modify eval files.
- Modify reports other than the new audit report.
- Fix issues in this window.
- Stage implementation changes.
- Reformat files.

If a problem is found, record it as PASS / WARN / FAIL with required remediation. Do not patch it.

## Must Recon First

Read these files:

P11-W3 evidence:
- docs/goals/2026-06-06/P11_W3_MINIMAL_THREE_AGENT_PRODUCT_SLICE.md
- docs/goals/2026-06-06/P11_W3_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P11_W3_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P11_W3_SOURCE_BACKFILL_REPORT.md

P11-W2 evidence:
- docs/goals/2026-06-06/P11_W2_POST_PUSH_AUDIT_REPORT.md
- docs/goals/2026-06-06/P11_W2_SOURCE_BACKFILL_REPORT.md

Current Project sources:
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

Code under audit:
- apps/api/app/application/agents/definitions/catalog.py
- apps/api/app/application/agents/definitions/__init__.py
- apps/api/app/application/agents/definitions/asset_candidate.py
- apps/api/app/application/agents/definitions/training_plan.py
- apps/api/app/application/agents/definitions/orchestrator.py
- apps/api/app/application/agents/orchestration/__init__.py
- apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py
- apps/api/app/application/agents/handoff/__init__.py
- apps/api/app/application/agents/runtime/__init__.py

Tests under audit:
- tests/application/agents/test_phase11_three_agent_product_slice.py
- tests/application/agents/test_phase11_runtime_hardening.py
- tests/architecture/test_agent_platform_l5_orchestrator_contract.py
- tests/api/test_agent_contracts.py

## Required Diff Audit

Run:

- git rev-parse HEAD
- git log --oneline -5
- git diff --name-only e49300d..c0294b1
- git diff --stat e49300d..c0294b1
- git diff --check e49300d..c0294b1

Changed files must be limited to:

Allowed code:
- apps/api/app/application/agents/contracts/__init__.py
- apps/api/app/application/agents/definitions/catalog.py
- apps/api/app/application/agents/definitions/__init__.py
- apps/api/app/application/agents/definitions/versions.py
- apps/api/app/application/agents/definitions/orchestrator.py
- apps/api/app/application/agents/definitions/asset_candidate.py
- apps/api/app/application/agents/definitions/training_plan.py
- apps/api/app/application/agents/orchestration/__init__.py
- apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py
- apps/api/app/application/agents/handoff/__init__.py
- apps/api/app/application/agents/runtime/__init__.py

Allowed tests:
- tests/application/agents/test_phase11_three_agent_product_slice.py
- tests/application/agents/test_phase11_runtime_hardening.py
- tests/architecture/test_agent_platform_l5_orchestrator_contract.py
- tests/api/test_agent_contracts.py

Allowed docs:
- docs/goals/README.md
- docs/goals/2026-06-06/P11_W3_MINIMAL_THREE_AGENT_PRODUCT_SLICE.md
- docs/goals/2026-06-06/P11_W3_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P11_W3_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P11_W3_SOURCE_BACKFILL_REPORT.md
- docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md
- docs/project-sources/04_AGENT_DEFINITION_STANDARD.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

Forbidden if present in diff:
- apps/api/app/application/ai_runtime/**
- apps/api/app/application/polish/**
- apps/api/app/application/llm/**
- apps/api/app/domain/**
- apps/api/app/infrastructure/**
- apps/api/app/api/**
- evals/**
- scripts/**
- .github/**
- package.json
- frontend files
- DB migrations
- prompt assets
- provider boundary implementation
- eval reports

## Product Slice Audit

Audit `apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py`.

Required PASS conditions:

1. It is deterministic and refs-only.
2. It includes three business agents:
   - polish_feedback_agent
   - asset_candidate_agent
   - training_plan_agent
3. It may include `interview_orchestrator_agent` as coordinator, but must not runtime-wire it.
4. It returns candidate refs only.
5. It includes:
   - feedback_candidate ref
   - asset_update_candidate ref
   - training_plan_candidate ref
6. It has typed handoff refs for:
   - feedback candidate to asset update candidate
   - asset update candidate to training plan candidate
7. Asset update candidate has:
   - user_confirmation_required true
   - formal_write_blocked true
8. It does not write formal asset / feedback / progress / score / training plan.
9. It does not call LLM/provider/prompt/DB/repository/API/domain/frontend.
10. It fails closed on missing required refs.
11. It fails closed on missing validation refs.
12. It blocks or interrupts asset conflict.
13. It blocks or interrupts formal_write_requested.
14. It exposes low confidence flags in trace or metadata.
15. It sanitizes or rejects unsafe metadata.
16. It never returns a success-like status when failure_reason is present.
17. Trace refs, validation refs, handoff refs and candidate refs remain separated.

## Catalog Audit

Audit L5 catalog.

Required PASS conditions:

1. C1 catalog remains only:
   - polish_question_agent
   - polish_feedback_agent
2. L5 catalog includes:
   - polish_question_agent if already part of L5 catalog
   - polish_feedback_agent
   - interview_orchestrator_agent
   - asset_candidate_agent
   - training_plan_agent
3. `asset_candidate_agent` outputs only:
   - asset_update_candidate
4. `training_plan_agent` outputs only:
   - training_plan_candidate
5. Both new business agents have:
   - SkillDefinition refs
   - ToolDefinition refs
   - Trace contract
   - Handoff contract
   - Eval refs deferred or future Phase 12 refs
6. ToolRegistry blocks repository / DB exposure.
7. No local registry bypass is introduced.
8. No C1 public builder is replaced or renamed.

## Orchestrator Non-wiring Audit

Run:

- rg "interview_orchestrator_agent" apps/api/app/application/ai_runtime apps/api/app/application/polish apps/api/app/api apps/api/app/domain apps/api/app/infrastructure

Expected:
- no matches

If matches exist, classify:
- FAIL if runtime/API/domain/infrastructure wiring exists
- WARN only if comments or non-executing documentation inside forbidden paths exist
- PASS if no matches

## Provider / DB / Formal Write Audit

Run:

- rg "LlmTransportRequest|provider_boundary|OpenAI|Anthropic|FakeLlmTransport" apps/api/app/application/agents tests/application/agents
- rg "repository|sqlalchemy|Session|unit_of_work|db_write|formal_write" apps/api/app/application/agents/orchestration tests/application/agents/test_phase11_three_agent_product_slice.py

Allowed:
- negative tests
- forbidden-data lists
- non-claim text
- formal_write_blocked fields

Forbidden:
- provider construction
- actual LLM/provider calls
- repository access
- SQLAlchemy access
- DB writes
- formal write success
- formal write completion claim

## Source Sanity Audit

Check `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`.

Expected:
- L5-002 not done.
- L5-003 not done.
- L5-004 may be candidate_product_slice_complete_with_deferred_formal_write_and_release_gate.
- L5-005 remains runtime-hardening slice status or weaker.
- L5-006 remains not_started.
- No L5 capability is marked done.
- P11-W3 does not claim Phase 12 release gate.

Check source docs for forbidden claims:

Run:

- rg "L5 release|real-provider quality certification|remote CI success|Phase 12 release gate done|formal write completed|product workflow release|full L5 validation complete" docs/project-sources docs/goals apps tests

Allowed:
- non-claims
- forbidden wording
- stop conditions
- audit wording

Forbidden:
- positive claim that P11-W3 achieved L5 release, real-provider quality, remote CI success, Phase 12 release gate, formal write, or product release

## Validation Commands

Run required tests:

- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_three_agent_product_slice.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_runtime_hardening.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_l5_orchestrator_contract.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_agent_contracts.py -q

Run recommended sanity tests:

- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture -q

If any test cannot run, record reason and classify risk.

## Audit Classification

Return one of:

PASS:
- diff scope clean
- forbidden paths clean
- required tests pass
- recommended sanity tests pass or are explicitly deferred with reason
- source claims sane
- C1 catalog unchanged
- L5 catalog includes required agents
- product slice is candidate-only
- no Orchestrator runtime wiring
- no LLM/provider/DB/repository/formal write
- L5-006 not started
- no L5 release / Phase 12 / real-provider claim

WARN:
- code and tests pass, but source wording is too strong
- validation incomplete but no behavior risk found
- grep results need interpretation
- docs have stale but non-blocking risk
- product slice is candidate-only but not sufficiently product-representative

FAIL:
- forbidden paths modified
- Orchestrator runtime-wired
- product slice writes formal facts
- provider / API / DB / domain / polish behavior changed
- eval reports rewritten
- L5 release or Phase 12 gate claimed
- L5-006 upgraded from not_started
- tests fail in relevant areas

## Audit Report Required

Create:

- docs/goals/2026-06-06/P11_W3_POST_PUSH_AUDIT_REPORT.md

Report format:

1. Audit Verdict
2. Commit Range
3. Diff Scope Audit
4. Forbidden Path Audit
5. Product Slice Audit
6. Catalog Audit
7. Orchestrator Non-wiring Audit
8. Provider / DB / Formal Write Audit
9. Source Sanity Audit
10. Validation Commands and Results
11. Remaining Risks
12. Required Remediation, if any
13. Final Status

Final status must be one of:

- post_push_audit_passed
- post_push_audit_warn_with_remediation
- post_push_audit_failed

## Stop Conditions

Stop and report FAIL if:

- forbidden files were modified
- Orchestrator was wired into runtime/API/domain/infrastructure
- product slice writes formal facts
- provider/prompt/API/DB/domain/frontend behavior changed
- eval reports were rewritten
- L5 release was claimed
- Phase 12 release gate was claimed
- real-provider quality was claimed
- remote CI success was claimed without evidence
- L5-006 was upgraded from not_started