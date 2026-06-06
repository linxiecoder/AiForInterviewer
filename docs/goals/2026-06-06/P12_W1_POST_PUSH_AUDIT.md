---
title: P12_W1_POST_PUSH_AUDIT
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/p12-w1-post-push-audit
---

# P12-W1 Post-push Audit and Source Sanity Check

Window ID: P12-W1-POST-PUSH-AUDIT-SOURCE-SANITY

Workspace Name: AiForInterviewer-P12-W1-POST-PUSH-AUDIT

Phase:
- Phase 12
- Post-push audit
- Read-only source sanity check
- Docs-only audit report

Commit under audit:
- 929d56f phase12: add eval contract slice

Base commit:
- 086f6ad

Audit range:
- 086f6ad..929d56f

Capability IDs:
- L5-006 L5 eval / replay / release gate
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

Perform a post-push audit of P12-W1.

The audit must verify:

1. Commit range is exactly P12-W1:
   - base: 086f6ad
   - head: 929d56f
2. Changed files are inside P12-W1 allowed scope.
3. No forbidden paths changed.
4. Phase 9 eval artifacts were not modified.
5. eval reports were not rewritten.
6. Phase 12 artifacts are contract-only:
   - suite manifest
   - dataset skeletons
   - grader contract
   - release report schema
7. No eval runner behavior was implemented or changed.
8. No CI workflow behavior was implemented or changed.
9. No release report was generated.
10. Static tests validate contract shape only.
11. L5-006 is not marked implemented / validated / done.
12. No L5 release, Phase 12 release gate complete, real-provider quality certification, remote CI success, or release report completion is claimed.
13. Existing non-claims remain explicit.

## Source of Truth

Use this order:

1. GitHub main / local HEAD at 929d56f.
2. Git diff 086f6ad..929d56f.
3. P12-W1 validation report.
4. Current Project source docs after P12-W1.
5. P12-W0 release gate scope lock.
6. P11-W4 closeout and accepted P11 post-push audits.
7. User-provided push output only as supporting evidence.

If sources conflict:

- Git diff and current files describe implementation facts.
- Project sources describe target / claims.
- Differences must be recorded as gaps.
- Do not normalize release / quality / CI / eval gaps by wording.

## Audit Mode

This is an audit window.

Allowed:
- Read files.
- Run validation commands.
- Create audit report:
  - docs/goals/2026-06-06/P12_W1_POST_PUSH_AUDIT_REPORT.md

Forbidden:
- Modify app code.
- Modify tests.
- Modify eval artifacts.
- Modify Project source docs.
- Modify scripts.
- Modify workflows.
- Modify eval reports.
- Fix issues in this window.
- Reformat files.
- Stage implementation changes.

If a problem is found, record it as PASS / WARN / FAIL with required remediation. Do not patch it.

## Must Recon First

Read these P12-W1 evidence files:

- docs/goals/2026-06-06/P12_W1_EVAL_CONTRACT_FIRST.md
- docs/goals/2026-06-06/P12_W1_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P12_W1_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P12_W1_SOURCE_BACKFILL_REPORT.md

Read P12-W0 evidence:

- docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_LOCK.md
- docs/goals/2026-06-06/P12_W0_RELEASE_GATE_SCOPE_REPORT.md
- docs/goals/2026-06-06/P12_W0_RELEASE_EVIDENCE_CONTRACT.md
- docs/goals/2026-06-06/P12_W0_DECISION_OPTIONS.md
- docs/goals/2026-06-06/P12_W0_SOURCE_BACKFILL_REPORT.md

Read Project sources:

- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md

Read P12-W1 eval contract artifacts:

- evals/suites/phase12.json
- evals/datasets/phase12/multi_agent_product_slice.jsonl
- evals/datasets/phase12/replay_and_failure_modes.jsonl
- evals/datasets/phase12/release_non_claims.jsonl
- evals/graders/phase12_contract.json
- evals/schemas/phase12_release_report_schema.json
- tests/evals/test_phase12_eval_contracts.py

Read protected Phase 9 surfaces for factual sanity only:

- evals/suites/phase9.json
- evals/datasets/phase9/
- evals/graders/code_rules.py
- evals/reports/phase9_eval_report.json
- docs/goals/2026-06-06/P9_EVAL_REPORT.md
- scripts/evals/run_eval_gate.py
- .github/workflows/eval-gate.yml

## Required Diff Audit

Run:

- git rev-parse HEAD
- git log --oneline -8
- git diff --name-only 086f6ad..929d56f
- git diff --stat 086f6ad..929d56f
- git diff --check 086f6ad..929d56f

Changed files must be limited to:

Allowed eval contract artifacts:
- evals/suites/phase12.json
- evals/datasets/phase12/multi_agent_product_slice.jsonl
- evals/datasets/phase12/replay_and_failure_modes.jsonl
- evals/datasets/phase12/release_non_claims.jsonl
- evals/graders/phase12_contract.json
- evals/schemas/phase12_release_report_schema.json
- tests/evals/test_phase12_eval_contracts.py

Allowed docs:
- docs/goals/2026-06-06/P12_W1_EVAL_CONTRACT_FIRST.md
- docs/goals/2026-06-06/P12_W1_IMPLEMENTATION_REPORT.md
- docs/goals/2026-06-06/P12_W1_VALIDATION_REPORT.md
- docs/goals/2026-06-06/P12_W1_SOURCE_BACKFILL_REPORT.md
- docs/goals/README.md
- docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
- docs/project-sources/12_ACCEPTANCE_GATES.md
- docs/project-sources/13_DECISION_LOG.md
- docs/project-sources/14_RISK_REGISTER.md
- docs/project-sources/17_PHASE_ROADMAP_LOCK.md

Forbidden if present in diff:
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
- evals/suites/phase9.json
- evals/datasets/phase9/**
- evals/graders/code_rules.py
- docs/goals/2026-06-06/P9_EVAL_REPORT.md
- evals/reports/P9_EVAL_REPORT.md
- evals/reports/phase9_eval_report.json

## Eval Contract Artifact Audit

Audit `evals/suites/phase12.json`.

Required PASS conditions:

1. suite_id exists.
2. phase is Phase 12 or equivalent.
3. lifecycle_status is contract_only or implementation_planned.
4. evidence_type is contract-only / not executable release gate.
5. dataset_refs point only to phase12 dataset skeletons.
6. grader_contract_refs point to phase12 contract artifact.
7. report_schema_ref points to phase12 release report schema.
8. ci_gate_status is not_bound or deferred, not passed.
9. provider_evidence_policy says replay/fake/local evidence is not real-provider quality certification.
10. non_claims include:
    - no L5 release
    - no real-provider quality certification
    - no remote CI success
    - no Phase 12 release gate complete

Audit dataset skeletons:

- evals/datasets/phase12/multi_agent_product_slice.jsonl
- evals/datasets/phase12/replay_and_failure_modes.jsonl
- evals/datasets/phase12/release_non_claims.jsonl

Required PASS conditions:

1. each line is valid JSON.
2. each case has required fields:
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
3. required case coverage exists:
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
   - fake / replay non-claim
   - release non-claim
4. cases use refs / expected assertions, not raw prompt or raw business payloads.
5. deferred_if_not_executable is true where the case is skeleton-only.

Audit grader contract:

- evals/graders/phase12_contract.json

Required PASS conditions:

1. contract exists.
2. lifecycle_status is contract_only or equivalent.
3. it does not imply Python grader implementation.
4. it includes non_claim_assertions.
5. it includes forbidden_data_assertions.
6. it includes replay_assertions.
7. it includes trace_assertions.
8. it includes hitl_assertions.
9. it includes release_decision_assertions.

Audit report schema:

- evals/schemas/phase12_release_report_schema.json

Required PASS conditions:

1. schema exists.
2. it requires release decision evidence.
3. it requires rollback evidence.
4. it requires artifact refs.
5. it requires negative-control result.
6. it requires non_claims.
7. it requires forbidden_data_scan.
8. it does not generate or update a report.

## Protected Phase 9 Audit

Verify no Phase 9 artifact changed in `086f6ad..929d56f`.

Forbidden if changed:

- evals/suites/phase9.json
- evals/datasets/phase9/**
- evals/graders/code_rules.py
- evals/reports/**
- docs/goals/2026-06-06/P9_EVAL_REPORT.md

If changed, classify FAIL unless the diff proves documentation-only reference outside protected path. Protected paths themselves must not change.

## Static Test Audit

Audit `tests/evals/test_phase12_eval_contracts.py`.

Required PASS conditions:

1. It validates JSON / JSONL shape.
2. It validates required cases.
3. It validates required fields.
4. It validates non-claims.
5. It validates forbidden payload keys.
6. It validates grader contract.
7. It validates release report schema.
8. It does not call live provider.
9. It does not run eval gate.
10. It does not write reports.
11. It does not modify Phase 9 artifacts.

## Source Sanity Audit

Check `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`.

Expected:

- L5-006 may be eval_contract_slice_complete_with_deferred_runner_ci_release.
- L5-006 is not implemented.
- L5-006 is not validated.
- L5-006 is not done.
- EVAL-001 is not upgraded to done.
- No L5 capability is marked done due to P12-W1.
- Remote CI gap remains open.
- Real-provider quality certification remains unclaimed.
- Phase 12 release gate remains incomplete.

Check source docs for forbidden claims:

Run:

- rg "L5 release|real-provider quality certification|remote CI success|Phase 12 release gate complete|release gate passed|release approved|L5-006.*done" docs/project-sources docs/goals evals tests

Allowed:
- non-claims
- forbidden wording
- stop conditions
- audit wording
- future requirements

Forbidden:
- positive claim that P12-W1 achieved L5 release, real-provider quality, remote CI success, release approval, or gate completion

## Validation Commands

Run required commands:

- PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals/test_phase12_eval_contracts.py -q
- PYTHONPATH=.:apps/api .venv/bin/pytest tests/evals -q
- .venv/bin/python -m json.tool evals/suites/phase12.json
- .venv/bin/python -m json.tool evals/graders/phase12_contract.json
- .venv/bin/python -m json.tool evals/schemas/phase12_release_report_schema.json
- .venv/bin/python -c "import json, pathlib; [json.loads(line) for path in pathlib.Path('evals/datasets/phase12').glob('*.jsonl') for line in path.read_text().splitlines() if line.strip()]"

Do not use bare `python` as a required command in this environment. The accepted P12-W1 warning says global `python` may be unavailable; `.venv/bin/python` is the expected interpreter.

Required grep checks:

- rg "L5 release|real-provider quality certification|remote CI success|Phase 12 release gate complete|release gate passed|release approved" evals docs tests
- rg "raw_prompt|raw_completion|provider_payload|raw_provider_payload|full_resume|full_jd|full_answer|full_asset_body|api_key|token|secret|cookie" evals/datasets/phase12 evals/suites/phase12.json evals/graders/phase12_contract.json evals/schemas/phase12_release_report_schema.json tests/evals/test_phase12_eval_contracts.py
- rg "evals/reports|phase9_eval_report|P9_EVAL_REPORT" evals docs/goals/2026-06-06 docs/project-sources

Interpret grep results in context. Forbidden-data catalogs and non-claims are allowed. Raw payloads or report rewrites are not allowed.

## Audit Classification

Return one of:

PASS:
- diff scope clean
- no forbidden paths changed
- Phase 9 artifacts protected
- Phase 12 artifacts are contract-only
- static tests pass
- tests/evals pass
- JSON / JSONL checks pass
- source claims sane
- L5-006 not implemented / validated / done
- no L5 release / Phase 12 gate / real-provider / remote CI claim

WARN:
- code and tests pass, but source wording is too strong
- validation incomplete but no behavior risk found
- grep results need interpretation
- environment command issue remains but `.venv/bin/python` equivalents pass

FAIL:
- forbidden paths modified
- Phase 9 artifacts modified
- eval reports rewritten
- runner behavior modified
- CI workflow modified
- release report generated
- L5 release or Phase 12 gate claimed
- real-provider quality claimed
- remote CI success claimed
- L5-006 marked implemented / validated / done
- relevant tests fail

## Audit Report Required

Create:

- docs/goals/2026-06-06/P12_W1_POST_PUSH_AUDIT_REPORT.md

Report format:

1. Audit Verdict
2. Commit Range
3. Diff Scope Audit
4. Forbidden Path Audit
5. Eval Contract Artifact Audit
6. Protected Phase 9 Audit
7. Static Test Audit
8. Source Sanity Audit
9. Validation Commands and Results
10. Remaining Risks
11. Required Remediation, if any
12. Final Status

Final status must be one of:

- post_push_audit_passed
- post_push_audit_warn_with_environment_note
- post_push_audit_warn_with_remediation
- post_push_audit_failed

## Stop Conditions

Stop and report FAIL if:

- forbidden files were modified
- Phase 9 eval artifacts were modified
- eval reports were rewritten
- runner behavior changed
- CI workflow changed
- app code changed
- release report was generated
- L5 release was claimed
- Phase 12 release gate was claimed complete
- real-provider quality was claimed
- remote CI success was claimed
- L5-006 was marked implemented / validated / done