---
title: P11_W1_CONTRACT_FIRST_ORCHESTRATOR
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/p11-w1-contract-first-orchestrator
---

# P11-W1 Contract-first Orchestrator

Window ID: P11-W1-CONTRACT-FIRST-ORCHESTRATOR

Workspace Name: AiForInterviewer-P11-W1-CONTRACT-FIRST-ORCHESTRATOR

Phase:
- Phase 11
- L5 Controlled Multi-Agent Orchestration
- Option A from P11-W0: Contract-first Orchestrator

Capability IDs:
- L5-001 Final L5 target lock
- L5-002 Supervisor / Orchestrator Agent
- L5-003 Cross-agent handoff / state / trace
- L5-004 Multi-agent product workflow
- L5-005 Controlled tool loop hardening
- AGT-002 AgentDefinitionRegistry
- AGT-003 SkillRegistry
- AGT-004 ToolRegistry
- AGT-006 Handoff contract
- AGT-007 Agent Trace Contract
- RTE-001 to RTE-007 carried runtime foundation gaps
- SRC-001 Source backfill
- WIN-001 Execution window protocol

## Goal

Implement the contract-first Orchestrator foundation for Phase 11 without product workflow execution.

This window must create or reconcile:
1. A contract-only Supervisor / Orchestrator Agent definition.
2. Cross-agent plan contract.
3. Cross-agent handoff route / envelope contract.
4. Cross-agent state / checkpoint / replay contract.
5. Cross-agent trace / timeline contract.
6. Orchestrator SkillDefinition records.
7. Orchestrator ToolDefinition records, contract-only and non-runtime.
8. Project-level registry / catalog wiring for the L5 contract catalog.
9. Architecture and contract tests proving candidate-only, no direct repository exposure, no runtime behavior, and no L5 release claim.

This window must not:
1. Implement a product vertical slice.
2. Execute multiple agents.
3. Change runtime behavior.
4. Change provider, prompt, API, DB, frontend, or domain policy behavior.
5. Claim L5 release.
6. Claim real-provider quality certification.
7. Close Phase 8 runtime gaps by wording.

## Source of Truth

Use this order:
1. User-confirmed decision: P11-W1 selects Option A Contract-first Orchestrator.
2. GitHub main current code and docs.
3. Current tests / eval results.
4. Project source documents.
5. GOAL0531 historical intent.
6. Historical chats only as clues.
7. Child-agent output only after audit.

If sources conflict:
- GitHub main describes current implementation.
- Project source describes target.
- Difference must be recorded as a gap.
- Do not normalize the conflict by wording only.

## Required Precondition

P11-W0 must be accepted as:
- accepted_as_scope_lock_complete_with_deferred_gaps

P11-W1 must carry forward:
- deferred_remote_ci_gap
- Phase 8 runtime deferred gaps
- stale committed eval report metadata risk
- Supervisor / Orchestrator was not implemented before this window
- Phase 12 L5 release gate not started
- real-provider quality certification not claimed

## Must Recon First

Read these files before writing any patch:

Project sources:
- docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md
- docs/project-sources/04_AGENT_DEFINITION_STANDARD.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

P11-W0 docs:
- docs/goals/2026-06-06/P11_W0_SCOPE_LOCK_AND_GAP_RECONCILIATION.md
- docs/goals/2026-06-06/P11_W0_GAP_RECONCILIATION.md
- docs/goals/2026-06-06/P11_W0_DECISION_OPTIONS.md
- docs/goals/2026-06-06/P11_W0_SOURCE_BACKFILL_AUDIT.md

Phase 8 / 9 / 10 evidence:
- docs/goals/2026-06-05/P8_FINAL_RUNTIME_AUDIT.md
- docs/goals/2026-06-05/P8_FINAL_EXECUTION_REPORT.md
- docs/goals/2026-06-06/P9_EVAL_REPORT.md
- docs/goals/2026-06-06/P10_CLOSEOUT_REPORT.md
- docs/goals/2026-06-06/P10_DEFERRED_GAP_REGISTER.md

Current code:
- apps/api/app/application/agents/contracts/__init__.py
- apps/api/app/application/agents/registry/__init__.py
- apps/api/app/application/agents/definitions/catalog.py
- apps/api/app/application/agents/definitions/polish/
- apps/api/app/application/agents/runtime/__init__.py
- apps/api/app/application/agents/handoff/__init__.py
- apps/api/app/application/ai_runtime/contracts.py
- tests/architecture/test_agent_platform_c0_boundary.py
- tests/architecture/test_agent_platform_c1_boundary.py
- tests/api/test_agent_contracts.py
- tests/application/agents/test_phase8_agent_executor_adapter.py

## Allowed Files

Code allowed:

- apps/api/app/application/agents/contracts/__init__.py
- apps/api/app/application/agents/contracts/
- apps/api/app/application/agents/definitions/catalog.py
- apps/api/app/application/agents/definitions/
- apps/api/app/application/agents/registry/__init__.py

Tests allowed:

- tests/architecture/test_agent_platform_l5_orchestrator_contract.py
- tests/architecture/test_agent_platform_c1_boundary.py
- tests/api/test_agent_contracts.py

Docs allowed:

- docs/goals/2026-06-06/P11_W1_CONTRACT_FIRST_ORCHESTRATOR.md
- docs/goals/2026-06-06/P11_W1_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P11_W1_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P11_W1_SOURCE_BACKFILL_REPORT.md
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

- apps/api/app/application/agents/runtime/**
- apps/api/app/application/ai_runtime/**
- apps/api/app/application/polish/**
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

## Behavior Change Allowed

No.

## Prompt / Provider / API / DB / Frontend Change Allowed

No.

## Runtime Change Allowed

No.

This window must not wire Orchestrator into AgentExecutor, LangGraph, AiOrchestrationFacade, Question runtime, Feedback runtime, application services, API routes, or persistence.

## Implementation Requirements

### Contract additions

Add contract-only types for cross-agent orchestration.

The exact names may vary if the existing code style requires it, but the contracts must cover these concepts:

1. CrossAgentPlan
   - plan_id
   - orchestrator_agent_id
   - owner_id
   - objective
   - participant_agent_ids
   - steps
   - max_steps
   - max_retries
   - timeout_seconds
   - stop_conditions
   - state_ref
   - trace_ref
   - handoff_policy
   - metadata

2. CrossAgentPlanStep
   - step_id
   - target_agent_id
   - input_refs
   - required_candidate_types
   - output_candidate_types
   - depends_on_step_ids
   - handoff_contract_id
   - policy_refs
   - validation_refs

3. CrossAgentHandoffRoute or equivalent
   - route_id
   - source_agent_id
   - target_agent_id
   - allowed_candidate_types
   - payload_schema_id
   - required_trace_refs
   - required_validation_refs
   - side_effect_policy
   - user_confirmation_required_when
   - forbidden_data

4. CrossAgentStateContract or equivalent
   - state_schema_id
   - checkpoint_policy
   - replay_policy
   - resume_policy
   - durable_state_refs
   - ephemeral_state_refs
   - owner_scope_policy
   - forbidden_data

5. CrossAgentTraceContract or equivalent
   - trace_schema_id
   - required_trace_refs
   - timeline_event_types
   - plan_refs
   - skill_refs
   - tool_refs
   - policy_refs
   - handoff_refs
   - validation_refs
   - candidate_refs
   - forbidden_data

All new contracts must:
- be immutable or treated as immutable if the existing code style allows it
- normalize tuple/list inputs
- fail closed for empty required IDs where appropriate
- filter or reject forbidden metadata keys consistently with existing agent contract conventions
- never include raw prompt, raw completion, raw provider payload, full resume, full JD, full answer, full asset body, token, secret, cookie, or API key

### Orchestrator AgentDefinition

Create a contract-only Supervisor / Orchestrator Agent definition.

Recommended agent_id:
- interview_orchestrator_agent

Required properties:
- lifecycle_status must be contract-only or implementation-planned, not production release
- maturity must indicate L5 target contract, not L5 release
- candidate_outputs only
- no formal outputs
- no direct formal write
- formal write boundary remains Application Service -> Domain Policy -> Handoff
- non_goals must include:
  - no L5 release claim
  - no runtime execution
  - no product workflow execution
  - no direct DB or repository write
  - no prompt/provider/API/DB/domain behavior change
  - no real-provider quality certification

The Orchestrator definition must reference project-level SkillDefinition and ToolDefinition records.

### Orchestrator Skills

Add contract-only SkillDefinition records for Orchestrator.

Recommended minimum skills:
- orch_goal_decomposition_skill
- orch_agent_route_planning_skill
- orch_cross_agent_handoff_validation_skill
- orch_state_checkpoint_planning_skill
- orch_trace_timeline_planning_skill
- orch_hitl_trigger_planning_skill

Rules:
- Skills are contract-only.
- Skills do not execute runtime logic.
- Skills do not call LLM.
- Skills do not access DB or repository.
- Skills do not write formal facts.
- Skills must include eval refs or explicit eval deferred refs.

### Orchestrator Tools

Add contract-only ToolDefinition records for Orchestrator.

Recommended minimum tools:
- orch_read_agent_catalog_contract
- orch_validate_cross_agent_plan_contract
- orch_validate_cross_agent_handoff_contract
- orch_validate_cross_agent_state_contract
- orch_validate_cross_agent_trace_contract
- orch_validate_hitl_trigger_contract

Rules:
- Tools are contract-only definitions.
- Tools must not directly expose repository, DB, SQLAlchemy, session, unit_of_work, or formal writer.
- Tool side_effect_policy must be read_only or forbidden unless there is a documented candidate-only reason.
- Tools must include required forbidden data keys.
- Tools must not imply runtime execution.

### Registry / catalog wiring

Do not mutate the existing Phase 4 C1 semantics.

Keep existing C1 builder behavior stable.

Add a separate L5 contract catalog builder, for example:
- build_phase11_l5_agent_definitions
- build_phase11_l5_skill_definitions
- build_phase11_l5_tool_definitions
- build_default_agent_platform_l5_contract_registries

The L5 catalog may compose:
- existing Question / Feedback contract definitions
- new Orchestrator contract definition
- new Orchestrator skills
- new Orchestrator tools

The L5 catalog must validate references using the project-level registries.

Do not rename existing public C1 functions unless tests already require it.

### Architecture gates

Add or update architecture tests to prove:

1. Orchestrator exists in L5 contract catalog.
2. Orchestrator is contract-only, not runtime wired.
3. Orchestrator candidate_outputs contain only allowed candidate types.
4. Orchestrator does not expose formal outputs.
5. Orchestrator non_goals include no L5 release and no product workflow execution.
6. Cross-agent contracts require trace refs and validation refs where applicable.
7. Cross-agent contracts forbid raw prompt, provider payload, full resume, full JD, full answer, full asset body and secrets.
8. ToolRegistry rejects direct repository / DB exposure for Orchestrator tools.
9. L5 catalog does not replace C1 catalog.
10. No runtime, provider, API, DB, domain, prompt, eval report or workflow files changed.

## Required Non-Claims

Every implementation report and source backfill must state:

- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close deferred_remote_ci_gap.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.

## Validation Commands

Required:

- git status --short --untracked-files=all
- git diff --check
- git diff --stat
- git diff --name-only
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_l5_orchestrator_contract.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_c1_boundary.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_agent_contracts.py -q

Recommended if available:

- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase8_agent_executor_adapter.py -q

Required forbidden change check:

- git diff --name-only

The changed file list must not include forbidden paths.

Required grep checks:

- rg "L5 release|real-provider quality certification|Supervisor / Orchestrator done|Phase 12 release gate done" docs/project-sources docs/goals apps tests
- rg "runtime wiring|AiOrchestrationFacade|LangGraph|provider_boundary|LlmTransportRequest" apps/api/app/application/agents tests/architecture tests/api

Interpret grep results in context. Non-claim wording is allowed. Claims of completion are not allowed.

## Done Criteria

P11-W1 is accepted only if:

1. Orchestrator AgentDefinition exists as contract-only.
2. Cross-agent plan / handoff / state / trace contracts exist.
3. Orchestrator skills and tools are registered as contract-only definitions.
4. L5 contract catalog builder exists and validates references.
5. Existing C1 catalog remains backward-compatible.
6. Architecture tests prove no fake L5 release, no product workflow execution, and no runtime wiring.
7. No forbidden code paths are modified.
8. No provider, prompt, API, DB, frontend, domain, runtime, eval dataset, eval runner, eval report or workflow files are changed.
9. Phase 8 runtime gaps remain visible and deferred.
10. Remote CI gap remains open unless separately verified.
11. Stale eval report metadata risk remains visible or unchanged.
12. Source backfill updates Matrix, Acceptance Gates, Decision Log, Risk Register and Roadmap.
13. Final report uses status:
    - contract_slice_complete_with_deferred_runtime_gaps
    or
    - blocked_needs_controller_decision
    or
    - failed_scope_violation

Do not use:
- L5 done
- L5 release done
- Supervisor runtime done
- Multi-agent product workflow done

## Stop Conditions

Stop and return to Controller if any of these are needed:

- modifying runtime files
- modifying provider files
- modifying prompt files
- modifying API routes
- modifying DB migrations
- modifying domain policies
- modifying application polish workflow behavior
- modifying eval datasets, eval suites, eval graders, eval reports or workflows
- adding product workflow execution
- wiring Orchestrator into AgentExecutor
- adding LangGraph runtime behavior
- creating formal writes from Agent output
- exposing repository or DB through ToolDefinition
- claiming L5 release
- closing Phase 8 runtime gaps by wording only
- marking L5-002 to L5-006 done

## Final Output Required

Return:

1. Root Cause
2. What Changed
3. Files Changed
4. Behavior Before / After
5. Contract Additions
6. Registry / Catalog Wiring
7. Architecture Gates
8. Validation Commands and Results
9. Remaining Risks
10. Follow-up Goal

Final status must be one of:

- contract_slice_complete_with_deferred_runtime_gaps
- blocked_needs_controller_decision
- failed_scope_violation

## P11-W1 Execution Result

Status: `contract_slice_complete_with_deferred_runtime_gaps`

P11-W1 selected Option A and implemented the contract-first Orchestrator foundation only.

Completed contract scope:

- Added contract-only `interview_orchestrator_agent`.
- Added cross-agent plan / step / handoff route / state / trace contract dataclasses.
- Added contract-only Orchestrator SkillDefinition records.
- Added contract-only Orchestrator ToolDefinition records.
- Added separate L5 contract catalog builder.
- Kept Phase 4 C1 Question / Feedback catalog behavior backward-compatible.
- Added architecture and API contract gates.
- Backfilled allowed Project source documents and goal evidence reports.

Validation:

- `git diff --check`: PASS.
- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_l5_orchestrator_contract.py -q`: PASS.
- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_c1_boundary.py -q`: PASS.
- `PYTHONPATH=.:apps/api .venv/bin/pytest tests/api/test_agent_contracts.py -q`: PASS.
- Required grep checks were interpreted as contextual non-claim / no-runtime-wiring evidence; see `P11_W1_VALIDATION_REPORT.md`.

Required non-claims:

- P11-W1 does not implement product multi-agent workflow.
- P11-W1 does not execute Supervisor / Orchestrator at runtime.
- P11-W1 does not close Phase 8 runtime gaps.
- P11-W1 does not close `deferred_remote_ci_gap`.
- P11-W1 does not rewrite stale eval reports.
- P11-W1 does not certify real-provider quality.
- P11-W1 does not claim L5 release.
- P11-W1 does not implement Phase 12 release gate.
