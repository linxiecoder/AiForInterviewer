---
title: P12_W1_EVAL_CONTRACT_FIRST
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/p12-w1-eval-contract-first-1
---

# P12-W1 Eval-contract-first

Window ID: P12-W1-EVAL-CONTRACT-FIRST

Workspace Name: AiForInterviewer-P12-W1-EVAL-CONTRACT-FIRST

Phase:
- Phase 12
- L5 Eval, Hardening, and Release Gate
- Option A from P12-W0: Eval-contract-first

Capability IDs:
- L5-006 L5 eval / replay / release gate
- L5-004 Multi-agent product workflow
- L5-005 Controlled tool loop hardening
- EVAL-001 AI Eval gate
- AGT-006 Handoff contract
- AGT-007 Agent Trace Contract
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

Create Phase 12 eval contract artifacts before implementing an executable Phase 12 gate.

This window must create:

1. Phase 12 suite manifest.
2. Multi-agent dataset skeleton.
3. Grader contract.
4. Release report schema.
5. Static tests validating the contract shape.
6. Source backfill recording the contract-first slice.

This window must not:

1. Implement eval runner behavior.
2. Modify CI workflows.
3. Generate release reports.
4. Rewrite existing eval reports.
5. Run release gate.
6. Claim L5 release.
7. Claim real-provider quality certification.
8. Claim remote CI success.
9. Claim Phase 12 release gate complete.
10. Modify runtime / provider / prompt / API / DB / frontend / domain behavior.

## Source of Truth

Use this order:

1. User-confirmed decision: P12-W1 selects Option A Eval-contract-first.
2. GitHub main / local HEAD after P12-W0.
3. P12-W0 release gate scope lock.
4. Phase 11 closeout and P11-W3 candidate product slice evidence.
5. Current Project source documents.
6. Existing Phase 9 eval gate artifacts.
7. GOAL0531 only as historical intent.

If sources conflict:

- Current repository files describe implementation facts.
- Project sources describe target / claims.
- P12-W0 describes Phase 12 scope.
- Differences must be recorded as gaps.
- Do not normalize release / quality / CI / eval gaps by wording.

## Required Preconditions

P12-W0 must be accepted as:

- release_gate_scope_locked_with_deferred_implementation

If P12-W0 has not been committed and pushed, stop and return to Controller.

Expected status before this window:

- Phase 11 = closed_with_deferred_release_gate
- L5-004 = candidate product slice status, not release
- L5-005 = runtime-hardening slice status, not full runtime closure
- L5-006 = not_started or release_gate_scope_locked only
- L5 release = not claimed
- real-provider quality certification = not claimed
- remote CI success = not claimed

## Window Type

This is a contract-first eval window.

Allowed:

- Add eval suite manifest.
- Add dataset skeleton.
- Add grader contract.
- Add release report schema.
- Add static tests validating these artifacts.
- Update Project source docs and goals docs.

Forbidden:

- Implement or modify eval runner.
- Modify scripts.
- Modify workflows.
- Modify eval reports.
- Modify runtime code.
- Modify provider / prompt / API / DB / frontend / domain behavior.
- Execute release gate.
- Claim release readiness.

## Must Recon First

Read before patch:

Phase 12 scope:

- docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_LOCK.md
- docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_REPORT.md
- docs/goals/2026-06-06/P12_W0_RELEASE_EVIDENCE_CONTRACT.md
- docs/goals/2026-06-06/P12_W0_DECISION_OPTIONS.md
- docs/goals/2026-06-06/P12_W0_SOURCE_BACKFILL_REPORT.md

Phase 11 evidence:

- docs/goals/2026-06-06/P11_W4_PHASE11_CLOSEOUT_REPORT.md
- docs/goals/2026-06-06/P11_W4_SOURCE_SANITY_AUDIT_REPORT.md
- docs/goals/2026-06-06/P11_W4_PHASE12_ENTRY_CRITERIA.md
- docs/goals/2026-06-06/P11_W3_POST_PUSH_AUDIT_REPORT.md
- docs/goals/2026-06-06/P11_W2_POST_PUSH_AUDIT_REPORT.md

Project sources:

- docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md
- docs/project-sources/04_AGENT_DEFINITION_STANDARD.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

Existing eval artifacts:

- evals/suites/phase9.json
- evals/datasets/phase9/
- evals/graders/code_rules.py
- scripts/evals/run_eval_gate.py
- .github/workflows/eval-gate.yml
- evals/reports/phase9_eval_report.json

Current multi-agent surfaces for factual recon only:

- apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py
- tests/application/agents/test_phase11_three_agent_product_slice.py
- tests/application/agents/test_phase11_runtime_hardening.py

## Allowed Files

Allowed to create:

- evals/suites/phase12.json
- evals/datasets/phase12/multi_agent_product_slice.jsonl
- evals/datasets/phase12/replay_and_failure_modes.jsonl
- evals/datasets/phase12/release_non_claims.jsonl
- evals/graders/phase12_contract.json
- evals/schemas/phase12_release_report_schema.json
- tests/evals/test_phase12_eval_contracts.py
- docs/goals/2026-06-06/P12_W1_EVAL_CONTRACT_FIRST.md
- docs/goals/2026-06-06/P12_W1_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P12_W1_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P12_W1_SOURCE_BACKFILL_REPORT.md

Allowed to update:

- docs/goals/README.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md

Allowed only if necessary for consistency:

- docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md
- docs/project-sources/04_AGENT_DEFINITION_STANDARD.md
- docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md

## Forbidden Files

Do not modify:

- apps/**
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
- evals/reports/**
- evals/graders/code_rules.py
- evals/suites/phase9.json
- evals/datasets/phase9/**
- docs/goals/2026-06-06/P9_EVAL_REPORT.md
- evals/reports/P9_EVAL_REPORT.md
- evals/reports/phase9_eval_report.json

Do not modify existing eval runner or workflow files.

## Behavior Change Allowed

No.

## Eval Runner / CI Change Allowed

No.

This window may add static eval contract artifacts and tests only.

## Required Artifacts

### 1. Phase 12 Suite Manifest

Create:

- evals/suites/phase12.json

Required fields:

- suite_id
- suite_name
- phase
- lifecycle_status
- evidence_type
- capability_ids
- dataset_refs
- grader_contract_refs
- report_schema_ref
- default_mode
- ci_gate_status
- minimum_pass_criteria
- blocking_failure_policy
- negative_control_policy
- provider_evidence_policy
- non_claims
- forbidden_data
- deferred_implementation

Rules:

- lifecycle_status must be contract_only or implementation_planned.
- evidence_type must indicate contract_only / not executable release gate.
- default_mode must not imply live provider usage.
- ci_gate_status must be not_bound or deferred, not passed.
- provider_evidence_policy must state replay/fake/local evidence is not real-provider quality certification.
- non_claims must include no L5 release, no real-provider quality, no remote CI success, no Phase 12 gate complete.

### 2. Dataset Skeletons

Create JSONL files:

- evals/datasets/phase12/multi_agent_product_slice.jsonl
- evals/datasets/phase12/replay_and_failure_modes.jsonl
- evals/datasets/phase12/release_non_claims.jsonl

Each JSONL line must be valid JSON.

Each case must include:

- case_id
- capability_ids
- evidence_type
- input_refs
- expected_candidate_refs
- expected_handoff_refs
- expected_validation_refs
- expected_trace_refs
- expected_hitl_refs
- expected_failure_mode
- expected_non_claims
- grader_refs
- minimum_assertions
- forbidden_data
- owner_phase
- deferred_if_not_executable

Required cases must cover at least:

1. happy path candidate product slice
2. insufficient context
3. asset conflict
4. formal write requested
5. low confidence
6. provider failure
7. validation failure
8. cross-agent handoff failure
9. replay mismatch
10. forbidden data
11. fake / replay non-claim
12. release non-claim

Rules:

- Do not store raw prompt, raw completion, provider payload, full resume, full JD, full answer, full asset body, token, secret, cookie or API key.
- Dataset skeletons must use refs / reason codes / expected assertions, not raw business payloads.
- Cases may be non-executable skeletons in P12-W1, but must clearly say deferred_if_not_executable true.

### 3. Grader Contract

Create:

- evals/graders/phase12_contract.json

Required fields:

- grader_contract_id
- lifecycle_status
- supported_assertion_types
- required_case_fields
- blocking_assertion_types
- non_claim_assertions
- forbidden_data_assertions
- replay_assertions
- trace_assertions
- hitl_assertions
- release_decision_assertions
- deferred_implementation

Rules:

- This is data contract only.
- Do not modify Python grader implementation in P12-W1.
- Do not import this into runner in P12-W1.

### 4. Release Report Schema

Create:

- evals/schemas/phase12_release_report_schema.json

Required fields:

- schema_id
- schema_version
- required_top_level_fields
- required_summary_fields
- required_capability_fields
- required_case_result_fields
- required_trace_fields
- required_artifact_fields
- required_release_decision_fields
- forbidden_keys
- non_claim_fields
- closure_criteria
- deferred_implementation

Report schema must require:

- suite_id
- mode
- commit_sha
- dataset_digests
- grader_contract_refs
- total_cases
- passed
- failed
- skipped
- deferred
- blocking_failures
- negative_control_result
- artifact_refs
- trace_report_refs
- release_decision
- accepted_risks
- rollback_policy_ref
- non_claims
- forbidden_data_scan

Rules:

- This schema must not generate a report.
- This schema must not update evals/reports.
- This schema must not claim current release readiness.

### 5. Static Tests

Create:

- tests/evals/test_phase12_eval_contracts.py

Tests must verify:

1. phase12 suite manifest exists and is contract_only / not release gate complete.
2. dataset JSONL files are valid JSONL.
3. required cases exist.
4. every case has required fields.
5. every case includes non-claims where relevant.
6. forbidden data keys are not present as payload keys.
7. grader contract exists and is non-executable / contract-only.
8. report schema exists and requires release decision / rollback / artifacts.
9. no eval report files are created or modified.
10. phase9 suite / datasets / grader / reports are not modified by this window.

Tests must not call live provider.
Tests must not run eval gate.
Tests must not write reports.

## Source Backfill Requirements

Update Matrix:

- Add status eval_contract_slice_complete_with_deferred_runner_ci_release if missing.
- Set L5-006 to eval_contract_slice_complete_with_deferred_runner_ci_release only if all P12-W1 contract artifacts and static tests pass.
- Do not mark L5-006 implemented / validated / done.
- Do not mark L5 release done.
- Do not upgrade EVAL-001 to done.
- Keep remote CI gap open.
- Keep real-provider quality certification unclaimed.
- Keep Phase 12 release gate uncompleted.

Update Acceptance Gates:

- Add P12-W1 Eval Contract Gate.
- Gate must state contract artifacts are not executable release evidence.
- Gate must require P12-W2 or later for runner / replay / CI implementation.

Update Decision Log:

- Record Controller-confirmed Option A Eval-contract-first.
- Status can be confirmed for option selection only, not release completion.

Update Risk Register:

- Add / update risks:
  - contract-only eval mistaken for executable gate
  - dataset skeleton mistaken for eval pass
  - report schema mistaken for report artifact
  - grader contract mistaken for grader implementation
  - L5-006 overclaim
  - phase9 report rewrite risk

Update Roadmap:

- P12-W1 = Eval-contract-first.
- Phase 12 implementation remains incomplete.
- Next window option remains to be selected after P12-W1 audit.

## Required Non-Claims

Every P12-W1 report and source backfill must state:

- P12-W1 does not implement eval runner.
- P12-W1 does not run release gate.
- P12-W1 does not modify CI.
- P12-W1 does not generate release report.
- P12-W1 does not rewrite eval reports.
- P12-W1 does not certify real-provider quality.
- P12-W1 does not claim remote CI success.
- P12-W1 does not claim L5 release.
- P12-W1 does not complete Phase 12 release gate.
- P12-W1 does not change runtime/provider/prompt/API/DB/domain/frontend behavior.

## Validation Commands

Required:

- git status --short --untracked-files=all
- git diff --check
- git diff --stat
- git diff --name-only
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals/test_phase12_eval_contracts.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals -q

Required JSON checks:

- python -m json.tool evals/suites/phase12.json
- python -m json.tool evals/graders/phase12_contract.json
- python -m json.tool evals/schemas/phase12_release_report_schema.json

Required JSONL check:

- python -c "import json, pathlib; [json.loads(line) for path in pathlib.Path('evals/datasets/phase12').glob('*.jsonl') for line in path.read_text().splitlines() if line.strip()]"

Required forbidden path check:

- git diff --name-only

Changed files must not include forbidden paths.

Required grep checks:

- rg "L5 release|real-provider quality certification|remote CI success|Phase 12 release gate complete|release gate passed|release approved" evals docs tests
- rg "raw_prompt|raw_completion|provider_payload|raw_provider_payload|full_resume|full_jd|full_answer|full_asset_body|api_key|token|secret|cookie" evals/datasets/phase12 evals/suites/phase12.json evals/graders/phase12_contract.json evals/schemas/phase12_release_report_schema.json tests/evals/test_phase12_eval_contracts.py
- rg "evals/reports|phase9_eval_report|P9_EVAL_REPORT" evals docs/goals/2026-06-06 docs/project-sources

Interpret grep results in context. Forbidden-data catalogs and non-claims are allowed. Raw payloads or report rewrites are not allowed.

Recommended optional:

- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_three_agent_product_slice.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/application/agents/test_phase11_runtime_hardening.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/architecture/test_agent_platform_l5_orchestrator_contract.py -q

## Done Criteria

P12-W1 is accepted only if:

1. Phase 12 suite manifest exists.
2. Phase 12 dataset skeletons exist.
3. Phase 12 grader contract exists.
4. Phase 12 release report schema exists.
5. Static tests pass.
6. Existing tests/evals remain green.
7. No eval runner behavior changed.
8. No CI workflow changed.
9. No eval reports are rewritten.
10. No code / runtime / provider / prompt / API / DB / domain / frontend behavior changed.
11. L5-006 is not marked implemented / validated / done.
12. L5 release is not claimed.
13. Real-provider quality is not claimed.
14. Remote CI success is not claimed.
15. Final status is one of:
    - eval_contract_slice_complete_with_deferred_runner_ci_release
    - eval_contract_slice_warn_with_remediation
    - eval_contract_slice_failed

## Stop Conditions

Stop and return to Controller if any of these are required:

- modifying code
- modifying eval runner
- modifying scripts
- modifying workflows
- modifying eval reports
- modifying phase9 eval artifacts
- modifying provider / prompt / API / DB / domain / frontend files
- generating release report
- running release gate as evidence
- claiming L5 release
- claiming real-provider quality
- claiming remote CI success
- marking L5-006 implemented / validated / done
- treating dataset skeletons as eval pass