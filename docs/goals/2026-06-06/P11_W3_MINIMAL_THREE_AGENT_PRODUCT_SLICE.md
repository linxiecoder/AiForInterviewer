---
title: P11_W3_MINIMAL_THREE_AGENT_PRODUCT_SLICE
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/p11-w3-minimal-three-agent-product-slice
---

# P11-W3 Minimal Three-Agent Product Vertical Slice

Window ID: P11-W3-MINIMAL-THREE-AGENT-PRODUCT-SLICE

Workspace Name: AiForInterviewer-P11-W3-THREE-AGENT-SLICE

Phase:
- Phase 11
- L5 Controlled Multi-Agent Orchestration
- Minimal candidate-only three-business-agent product vertical slice

Capability IDs:
- L5-002 Supervisor / Orchestrator Agent
- L5-003 Cross-agent handoff / state / trace
- L5-004 Multi-agent product workflow
- L5-005 Controlled tool loop hardening
- AGT-002 AgentDefinitionRegistry
- AGT-003 SkillRegistry
- AGT-004 ToolRegistry
- AGT-006 Handoff contract
- AGT-007 Agent Trace Contract
- RTE-006 Typed multi-agent handoff
- SRC-001 Source backfill
- WIN-001 Execution window protocol

## Goal

Implement the first minimal product-facing multi-agent vertical slice, but candidate-only.

The slice must prove that one controlled orchestration scenario can coordinate three business agents through typed refs and handoff metadata without formal writes.

Required participant business agents:

1. polish_feedback_agent
2. asset_candidate_agent
3. training_plan_agent

Coordinator:

- interview_orchestrator_agent

The workflow should be:

1. Orchestrator builds a cross-agent candidate plan.
2. Feedback Agent contributes or is represented by a feedback_candidate ref.
3. AssetCandidate Agent produces an asset_update_candidate ref.
4. TrainingPlan Agent produces a training_plan_candidate ref from refs-only context.
5. Trace / handoff / validation refs remain separated.
6. Formal writes remain blocked.
7. Asset update requires user confirmation.
8. HITL blocks or interrupts asset conflict / formal write / low confidence / validation failed partial result.

This window must not:

1. Call LLM.
2. Call provider.
3. Render prompt.
4. Read or write DB.
5. Modify API routes.
6. Modify domain policies.
7. Modify application polish runtime behavior.
8. Modify frontend.
9. Implement Phase 12 release gate.
10. Claim L5 release or real-provider quality certification.

## Source of Truth

Use this order:

1. User-confirmed decision: P11-W3 Minimal three-agent product vertical slice.
2. GitHub main current code and docs.
3. Current tests / eval results.
4. Project source documents.
5. P11-W0 / P11-W1 / P11-W1.fix.01 / P11-W2 / P11-W2 audit evidence.
6. GOAL0531 only as historical intent.
7. Child-agent output only after audit.

If sources conflict:

- GitHub current files describe implementation facts.
- Project sources describe target architecture.
- Difference must be recorded as a gap.
- Do not normalize product/runtime/release gaps by wording.

## Required Preconditions

Before patching, verify P11-W2 is accepted as:

- runtime_hardening_slice_complete_with_deferred_product_workflow

Expected status before P11-W3:

- L5-002: contract_slice_complete_with_deferred_runtime_gaps
- L5-003: contract_slice_complete_with_deferred_runtime_gaps
- L5-004: not_started
- L5-005: runtime_hardening_slice_complete_with_deferred_product_workflow or equivalent P11-W2 slice status
- L5-006: not_started

Do not proceed if P11-W2 post-push audit is missing or failed.

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
- docs/goals/2026-06-06/P11_W1_SOURCE_BACKFILL_REPORT.md
- docs/goals/2026-06-06/P11_W1_FIX01_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P11_W2_SOURCE_BACKFILL_REPORT.md
- docs/goals/2026-06-06/P11_W2_POST_PUSH_AUDIT_REPORT.md

Agent platform code:
- apps/api/app/application/agents/contracts/__init__.py
- apps/api/app/application/agents/definitions/catalog.py
- apps/api/app/application/agents/definitions/orchestrator.py
- apps/api/app/application/agents/registry/__init__.py
- apps/api/app/application/agents/handoff/__init__.py
- apps/api/app/application/agents/runtime/__init__.py

Existing planned workflow code, read-only:
- apps/api/app/application/polish/agents/feedback/planned_workflow.py
- apps/api/app/application/polish/agents/question/planned_workflow.py

Existing tests:
- tests/application/agents/test_phase11_runtime_hardening.py
- tests/architecture/test_agent_platform_l5_orchestrator_contract.py
- tests/api/test_agent_contracts.py

## Allowed Files

Code allowed:

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

Tests allowed:

- tests/application/agents/test_phase11_three_agent_product_slice.py
- tests/application/agents/test_phase11_runtime_hardening.py
- tests/architecture/test_agent_platform_l5_orchestrator_contract.py
- tests/api/test_agent_contracts.py

Docs allowed:

- docs/goals/2026-06-06/P11_W3_MINIMAL_THREE_AGENT_PRODUCT_SLICE.md
- docs/goals/2026-06-06/P11_W3_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P11_W3_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P11_W3_SOURCE_BACKFILL_REPORT.md
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

Read-only exception:

- existing polish planned workflow files may be read for recon only.
- Do not modify them.

If the desired slice requires modifying forbidden files, stop and return to Controller.

## Behavior Change Allowed

Only internal Agent Platform candidate orchestration behavior is allowed.

Allowed:

- deterministic refs-only construction of candidate product workflow result
- new agent definitions for asset_candidate_agent and training_plan_agent
- new typed candidate refs for asset_update_candidate and training_plan_candidate
- candidate-only handoff metadata
- trace / validation / handoff refs
- HITL / blocked result for asset conflict and formal write requested
- tests proving this behavior

Forbidden:

- no production API behavior change
- no database writes
- no formal business writes
- no provider calls
- no prompt rendering
- no Question / Feedback service behavior change
- no domain policy behavior change
- no frontend behavior change

## Implementation Requirements

### 1. Add business AgentDefinitions

Add contract definitions for:

- asset_candidate_agent
- training_plan_agent

Rules:

- They must be registered only through project-level AgentDefinitionRegistry.
- They must have skills and tools registered in SkillRegistry / ToolRegistry.
- They must output only allowed candidate types:
  - asset_candidate_agent -> asset_update_candidate
  - training_plan_agent -> training_plan_candidate
- They must not expose formal writes.
- They must not access repository / DB.
- They must not call LLM.
- They must not call provider.
- They must not render prompt.
- They must include eval refs as deferred or future Phase 12 refs.
- They must include trace and handoff contracts.
- Asset update candidate must require user confirmation.

### 2. Extend L5 contract catalog

Extend the Phase 11 L5 catalog builder so that it includes:

- polish_question_agent if currently part of L5 catalog
- polish_feedback_agent
- interview_orchestrator_agent
- asset_candidate_agent
- training_plan_agent

C1 catalog must remain unchanged:

- C1 catalog returns only Question / Feedback.
- L5 catalog returns C1 plus Orchestrator plus new business agents.

Do not replace C1 functions.

### 3. Add minimal deterministic product slice

Create a deterministic, refs-only product slice under:

- apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py

Recommended public function:

- build_minimal_three_agent_product_slice

Recommended input contract:

- owner_id
- session_ref
- feedback_candidate_ref
- answer_ref
- question_ref
- evidence_refs
- source_trace_refs
- validation_refs
- optional asset_conflict_ref
- optional low_confidence_flags
- optional idempotency_key

Recommended output contract:

- workflow_ref
- orchestrator_agent_id
- participant_agent_ids
- candidate_refs
- handoff_refs
- validation_refs
- trace_refs
- timeline_events
- hitl_required
- blocking_reasons
- formal_write_blocked
- asset_update_user_confirmation_required
- status
- failure_reason
- metadata

Rules:

- The happy path must include three business agents:
  - polish_feedback_agent
  - asset_candidate_agent
  - training_plan_agent
- It may include interview_orchestrator_agent as coordinator.
- It must not execute any LLM/provider.
- It must not call existing FeedbackGenerationService or QuestionGenerationService.
- It must not write formal feedback, asset, progress, weakness or training plan.
- It must not read DB.
- It must not call repository.
- It must produce candidate refs only.
- It must be idempotent based on refs.
- It must carry trace refs and validation refs separately.
- It must fail closed when required refs are missing.
- It must block or interrupt on asset conflict.
- It must block or interrupt on formal_write_requested.
- It must expose low confidence in trace metadata.
- It must never report success-like status when failure_reason is present.
- It must sanitize metadata.

### 4. Handoff requirements

The slice must create typed handoff refs for at least:

- feedback_candidate -> asset_update_candidate
- asset_update_candidate -> training_plan_candidate

Each handoff must include:

- source_agent_id
- target_agent_id
- candidate_type
- candidate_ref
- trace_refs
- validation_refs
- handoff_ref
- side_effect_policy
- formal_write_blocked
- user_confirmation_required when applicable

### 5. Trace requirements

Trace / timeline must include:

- plan_refs
- candidate_refs
- handoff_refs
- validation_refs
- policy_refs
- low_confidence_flags when present
- failure_reason when blocked or failed
- HITL refs when required

Trace must not include:

- raw_prompt
- raw_completion
- provider_payload
- raw_provider_payload
- full_resume
- full_jd
- full_answer
- full_asset_body
- token
- secret
- cookie
- api_key

### 6. HITL rules

Asset update candidate:

- must have user_confirmation_required true
- must have formal_write_blocked true
- must not be treated as confirmed asset

Asset conflict:

- blocks or interrupts the workflow
- must not produce a normal successful training_plan_candidate unless explicitly designed as blocked candidate
- must be trace-visible

Formal write requested:

- blocks or interrupts
- must not return success

Low confidence:

- must be trace-visible
- may produce candidate with low confidence, but not formal write

### 7. Matrix status

If implementation and tests pass, update Matrix:

- Add status candidate_product_slice_complete_with_deferred_formal_write_and_release_gate if missing.
- Set L5-004 to candidate_product_slice_complete_with_deferred_formal_write_and_release_gate.
- Keep L5-006 as not_started.
- Keep L5 release non-claim.
- Keep real-provider quality certification non-claim.
- Keep remote CI gap open unless a separate CI window verifies it.
- Do not mark any L5 capability done.

Do not upgrade Phase 12.

## Tests Required

Add focused tests in:

- tests/application/agents/test_phase11_three_agent_product_slice.py

Required tests:

1. Happy path creates candidate-only three-business-agent workflow.
2. participant_agent_ids includes polish_feedback_agent, asset_candidate_agent, training_plan_agent.
3. output includes feedback_candidate, asset_update_candidate, training_plan_candidate refs.
4. handoff refs include feedback to asset candidate and asset candidate to training plan.
5. asset_update_candidate requires user confirmation and formal_write_blocked.
6. formal writes are absent.
7. trace refs and validation refs are preserved separately.
8. missing feedback_candidate_ref fails closed.
9. missing validation refs fail closed.
10. asset_conflict blocks or interrupts and is trace-visible.
11. formal_write_requested blocks or interrupts and is not success.
12. low_confidence_flags are trace-visible.
13. unsafe metadata is rejected or sanitized.
14. no LLM/provider/repository/DB calls are made.
15. Orchestrator is not wired into API / ai_runtime / polish / domain / infrastructure.

Update existing tests if needed:

- tests/architecture/test_agent_platform_l5_orchestrator_contract.py
- tests/api/test_agent_contracts.py
- tests/application/agents/test_phase11_runtime_hardening.py

## Required Non-Claims

Every report and source backfill must state:

- P11-W3 implements only a minimal candidate-only product slice.
- P11-W3 does not write formal assets, progress, scores, feedback, reports or training plans.
- P11-W3 does not call LLM or provider.
- P11-W3 does not modify provider, prompt, API, DB, frontend, domain policy or persistence behavior.
- P11-W3 does not certify real-provider quality.
- P11-W3 does not close Phase 12 release gate.
- P11-W3 does not claim L5 release.
- P11-W3 does not close remote CI gap.
- P11-W3 does not replace Phase 12 multi-agent eval.

## Validation Commands

Required:

- git status --short --untracked-files=all
- git diff --check
- git diff --stat
- git diff --name-only
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_three_agent_product_slice.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_runtime_hardening.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_l5_orchestrator_contract.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_agent_contracts.py -q

Recommended:

- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture -q

Required forbidden path check:

- git diff --name-only

Changed files must not include forbidden paths.

Required grep checks:

- rg "interview_orchestrator_agent" apps/api/app/application/ai_runtime apps/api/app/application/polish apps/api/app/api apps/api/app/domain apps/api/app/infrastructure
- rg "LlmTransportRequest|provider_boundary|OpenAI|Anthropic|FakeLlmTransport" apps/api/app/application/agents tests/application/agents
- rg "repository|sqlalchemy|Session|unit_of_work|db_write|formal_write" apps/api/app/application/agents/orchestration tests/application/agents/test_phase11_three_agent_product_slice.py
- rg "L5 release|real-provider quality certification|Phase 12 release gate done|formal write completed|product workflow release" docs/project-sources docs/goals apps tests

Interpret grep results in context. Negative tests, forbidden lists and non-claims are allowed. Positive behavior claims are not allowed.

## Done Criteria

P11-W3 is accepted only if:

1. asset_candidate_agent is registered in L5 catalog.
2. training_plan_agent is registered in L5 catalog.
3. C1 catalog remains unchanged.
4. Minimal product slice produces candidate-only workflow with three business agents.
5. Asset candidate requires user confirmation.
6. Formal writes are blocked.
7. Handoff refs are typed and trace-visible.
8. Trace / validation refs are separated.
9. Asset conflict blocks or interrupts.
10. Low confidence is trace-visible.
11. No provider / LLM / prompt / DB / repository / API / domain / frontend behavior changes.
12. No eval reports are rewritten.
13. Matrix updates L5-004 to candidate product slice status only.
14. L5-006 remains not_started.
15. L5 release is not claimed.
16. Final status is one of:
    - candidate_product_slice_complete_with_deferred_formal_write_and_release_gate
    - blocked_needs_controller_decision
    - failed_scope_violation

## Stop Conditions

Stop and return to Controller if any of these are required:

- modifying application polish behavior
- modifying provider or prompt files
- modifying API routes
- modifying DB or repository logic
- modifying domain policies
- modifying frontend files
- modifying eval datasets, suites, graders, reports or workflows
- adding production API entrypoint
- calling LLM or provider
- writing formal asset / feedback / progress / score / training plan
- exposing repository through ToolDefinition
- using fake provider as runtime evidence
- claiming L5 release
- claiming real-provider quality
- claiming Phase 12 release gate
- marking L5-006 implemented / validated / done
- marking any L5 capability done

## Final Output Required

Return:

1. Root Cause
2. What Changed
3. Files Changed
4. Behavior Before / After
5. Product Slice Added
6. Agents / Handoffs / Candidates
7. Tests Added / Updated
8. Source Backfill
9. Validation Commands and Results
10. Remaining Risks
11. Follow-up Goal

Allowed final status:

- candidate_product_slice_complete_with_deferred_formal_write_and_release_gate
- blocked_needs_controller_decision
- failed_scope_violation