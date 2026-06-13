---
title: P7_CONTROLLER_SCOPE_LOCK
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-controller-scope-lock
---

# P7 Controller Scope Lock

## Scope Lock

```text
task_id: P7-W1-PROVIDER-FAIL-CLOSED-FAKE-CLEANUP [GOAL_SOURCE]
capability_ids: PRO-001, PRO-002, FAKE-001, WIN-001, SRC-001 [GOAL_SOURCE]
active_backlog_mapping: UNKNOWN exact AIFI mapping; nearest active backlog entries are AIFI-BE-001 and AIFI-QA-001, but this window does not rewrite BACKLOG or create a new task entry [GITHUB_CODE/INFERENCE]
files:
  READ:
    - AGENTS.md
    - docs/00-governance/DOCS_INDEX.md
    - docs/03-implementation/BACKLOG.md
    - docs/03-implementation/DELIVERY_PLAN.md
    - docs/tmp/goal0605/phase7_provider_fail_closed/**
    - docs/project-sources/**
    - apps/api/app/application/llm/**
    - apps/api/app/application/ai_runtime/**
    - apps/api/app/application/polish/**
    - apps/api/app/infrastructure/llm/**
    - apps/api/app/infrastructure/ai_runtime/**
    - tests/architecture/**
    - tests/api/test_fake_llm_boundary.py
    - tests/api/test_llm_runtime.py
    - tests/api/test_*provider*.py
    - tests/api/test_polish_question_refactor_phase1.py
    - tests/api/test_polish_feedback*.py
    - tests/fakes/**
    - tests/evals/**
  WRITE_CODE:
    - apps/api/app/application/llm/**
    - apps/api/app/application/ai_runtime/**
    - apps/api/app/application/polish/question_generation_service.py
    - apps/api/app/application/polish/feedback_agent.py
    - apps/api/app/application/polish/feedback_generation_service.py
    - apps/api/app/application/polish/feedback_prompt_assets.py
    - apps/api/app/infrastructure/llm/**
    - apps/api/app/infrastructure/ai_runtime/llm_trace/**
    - tests/architecture/**
    - tests/api/test_fake_llm_boundary.py
    - tests/api/test_llm_runtime.py
    - tests/api/test_*provider*.py
    - tests/api/test_polish_question_refactor_phase1.py
    - tests/api/test_polish_feedback*.py
  WRITE_DOCS:
    - docs/goals/2026-06-05/**
    - docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
    - docs/project-sources/12_ACCEPTANCE_GATES.md
    - docs/project-sources/13_DECISION_LOG.md
    - docs/project-sources/14_RISK_REGISTER.md
    - docs/project-sources/17_PHASE_ROADMAP_LOCK.md
figma_nodes: none
allowed_ops:
  - READ_ONLY recon through Agents A/B/C
  - EDIT_LISTED_FILES by exactly one implementation writer
  - READ_ONLY audit/diff after implementation
  - docs/source backfill only after audit does not return FAIL
forbidden_ops:
  - modify apps/api/app/api/v1/**
  - modify apps/api/app/domain/**
  - modify apps/api/app/infrastructure/db/**
  - modify frontend/**
  - modify migrations or alembic/**
  - public API contract change
  - DB schema change
  - prompt business rule expansion
  - domain policy migration or rewrite
  - Phase 8 LangGraph / multi-agent runtime migration
  - Phase 9 full Eval / CI regression gate finalization
  - Phase 11 / Phase 12 L5 implementation
  - Agent formal write behavior change
  - Tool repository exposure
  - committing, pushing, publishing, or destructive git commands
final_artifact:
  - docs/goals/2026-06-05/P7_A_PROVIDER_BOUNDARY_RECON.md
  - docs/goals/2026-06-05/P7_B_QF_INTEGRATION_RECON.md
  - docs/goals/2026-06-05/P7_C_FAKE_SECURITY_RECON.md
  - docs/goals/2026-06-05/P7_D_IMPLEMENTATION_REPORT.md
  - docs/goals/2026-06-05/P7_E_AUDIT_REPORT.md
  - docs/goals/2026-06-05/P7_F_SOURCE_BACKFILL_REPORT.md
  - final claim-ledger report using FINAL_REPORT_TEMPLATE.md
done_condition:
  - provider boundary exists and is wired to active Question and Feedback provider paths
  - recursive forbidden-key rejection is tested for the full P7 key catalog
  - full prompt / full resume / full JD / full answer / full asset fallback is absent or blocked
  - provider unavailable, parser failure, validation failure, redaction failure, and forbidden-key detection are not generated success
  - runtime fake provider remains rejected or unreachable in production runtime wiring
  - fake remains available only for tests/evals/replay and is status-visible when explicitly injected
  - trace/request metadata stores safe refs and failure reason only
  - required tests and grep gates are run and interpreted
  - changed files stay within Scope Lock
  - source backfill records exact status without unsupported done claim
```

## Controller Recon Decision

| Item | Evidence | Decision |
|---|---|---|
| Goal pack path | User requested `tmp/goal0605/...`; repo path exists at `docs/tmp/goal0605/phase7_provider_fail_closed/**` and root `tmp/` does not exist. | Continue with repo-local `docs/tmp/...` as goal source; record path mismatch. |
| Multi-agent recon | `P7_A_PROVIDER_BOUNDARY_RECON.md`, `P7_B_QF_INTEGRATION_RECON.md`, `P7_C_FAKE_SECURITY_RECON.md` exist. | Recon-first gate satisfied. |
| Exact AIFI task | `BACKLOG.md` only has broad `AIFI-BE-001`, `AIFI-QA-001`; no exact `PRO-001` / `FAKE-001` AIFI row. | Treat as governance gap; do not edit BACKLOG in implementation slice. |
| Minimal code target | Agent A/B/C agree on shared provider boundary around `LlmTransportRequest.evidence_bundle`, `ai_runtime` sensitive key completion, Question `_generate_llm_question`, Feedback `FeedbackGenerationAgent.generate`, and Feedback fake success semantics. | Proceed only within listed files. |
| Forbidden scope | No recon evidence requires API v1, DB schema, domain policy, frontend, Phase 8, Phase 9, or L5 files. | No stop condition triggered. |

## Single Writer Implementation Plan

1. Add focused red tests first:
   - remove provider boundary xfail for `developer_prompt` and `full_asset_body`;
   - add recursive forbidden-key / full prompt fallback tests for provider boundary;
   - add Question/Feedback provider invocation fail-closed tests;
   - update Feedback fake direct-service expectation to non-generated failure or fake-visible non-success.
2. Implement the smallest shared provider boundary in `apps/api/app/application/llm/`.
3. Wire Question and Feedback active provider paths through that boundary before `transport.generate()`.
4. Extend `application/ai_runtime/contracts.py` sensitive catalog to match P7 required keys.
5. Preserve existing fake test/eval/replay fixtures while preventing runtime generated-success semantics.
6. Run focused tests, grep gates, then audit/diff.

## Completion Status

`recon_done`

No implementation, validation, audit, or source backfill claim is made by this Scope Lock.