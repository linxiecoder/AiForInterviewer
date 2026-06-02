---
title: PHASE_2_ENTRY_GAP_REGISTER
type: gap-register
status: evidence-only
owner: P2-W0-SCOPE-LOCK-RECON
permalink: ai-for-interviewer/docs/goals/2026-06-03/phase-2-entry-gap-register
---

# Phase 2 Entry Gap Register

本文件登记 P2-W0 recon 发现的 Phase 2 入口缺口。它只作为 execution evidence，不授权绕过 `phase2_goal.md` 的窗口边界，也不替代 active docs 或当前代码事实。

## 1. Status Model

Allowed statuses:

- `open`
- `closed`
- `deferred`
- `blocked`

Allowed source labels:

- `USER_CONFIRMED`
- `GITHUB_CODE`
- `TEST_RESULT`
- `PROJECT_SOURCE`
- `GOAL_SOURCE`
- `INFERENCE`
- `UNKNOWN`

## 2. Gap Register

| Gap ID | Capability | Status | Source label | Current evidence | Target | Owner window | Risk | Mitigation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2-GAP-CTX-001 | `CTX-001` CanonicalEvidencePack | `open` | `GITHUB_CODE` | `CanonicalEvidenceService.build_pack()` returns target-adjacent dict but lacks `source_support_summary`; digest payload covers legacy `source_support_level`, not full summary / blocking issues. | Align or compatibility-adapt pack to target shape and stable digest rules. | P2-W1 | Medium | Add contract tests before implementation; preserve legacy `source_support_level` as derived view. |
| P2-GAP-CTX-002 | `CTX-002` SourceSupportSummary | `open` | `GITHUB_CODE` | No `SourceSupportSummary` object/function exists; canonical service only returns direct/insufficient; question service independently computes all four levels. | Add required fields: level, primary/adjacent/job_gap refs, missing_context, reason_codes, confidence, policy_version, computed_at. | P2-W1, P2-W2 | High | TDD around validation/defaults and pure deterministic builder. |
| P2-GAP-CTX-003 | Source support single interpretation | `open` | `GITHUB_CODE` | `question_generation_service._source_support_level()` classifies support from chunks/assets independently of canonical evidence summary. | Question/Feedback consume summary from unified context entry; legacy level remains derived only. | P2-W2, P2-W3, P2-W4 | High | Add context builder tests and caller tests; keep prompt assets untouched. |
| P2-GAP-CTX-004 | Interview Context | `open` | `GITHUB_CODE` | No `apps/api/app/application/polish/context/` package exists. Progress context is current transport. | Add context-level unified entry or compatibility adapter without API/provider behavior changes. | P2-W2, P2-W3, P2-W4 | Medium | Keep service pure and feed already-loaded app data only. |
| P2-GAP-CTX-005 | Feedback canonical pack usage | `open` | `GITHUB_CODE` | `_build_feedback_generation_context()` passes `canonical_project_assets` but not full `CanonicalEvidencePack` or summary. | Feedback context receives canonical evidence and source support summary from unified entry. | P2-W4 | Medium | Extend `FeedbackGenerationContext` additively; preserve existing fields and prompt payload behavior. |
| P2-GAP-FAG-001 | Expected points builder | `open` | `GITHUB_CODE` | `feedback_rules._expected_points()` builds points directly from metadata/progress/assets/job inside feedback policy file. | Move/delegate expected-point construction to context-owned builder or explicit adapter. | P2-W4 | Medium | Only move expected-point construction; do not migrate feedback domain policies. |
| P2-GAP-TEST-001 | Contract tests missing | `open` | `GITHUB_CODE` | W1 target tests do not exist. | Add direct tests for pack/summary serialization, invalid level, refs, reason codes. | P2-W1 | Medium | Red/green tests first. |
| P2-GAP-TEST-002 | Shared summary service tests missing | `open` | `GITHUB_CODE` | W2 target summary-service test does not exist. | Cover direct / adjacent / job_gap / insufficient and asset status/conflict rules. | P2-W2, P2-W5 | High | Pure fixture tests; no DB/LLM. |
| P2-GAP-TEST-003 | Question/Feedback context tests missing | `open` | `GITHUB_CODE` | W3/W4 target tests do not exist. | Prove real callers consume unified context entry. | P2-W3, P2-W4 | High | Use focused application/service-level tests without provider rewrite. |
| P2-GAP-SEED-001 | Eval seed convention needs mapping | `open` | `GITHUB_CODE` | `tests/evals/` contains Python code-rule tests, not discovered YAML/JSON fixtures. | Add deterministic eval seeds only if they fit existing convention; otherwise defer with reason. | P2-W5 | Low | Prefer Python eval-rule tests or explicit deferral; do not claim full AI quality gate. |
| P2-GAP-SRC-001 | Project source pack path absent | `open` | `GITHUB_CODE` | Root-level source pack files named in `phase2_goal.md` were not found during W0 recon. | Backfill actual discovered Project source files or explicitly defer absent paths in closeout. | P2-W6 | Medium | Re-run path discovery in W6 before source backfill. |
| P2-GAP-P1-001 | Remaining Polish ownership extraction | `deferred` | `PROJECT_SOURCE` | Phase 1 closeout marks remaining ownership extraction as deferred. | Do not continue broad ownership extraction in Phase 2. | N/A | Medium | Limit edits to context/canonical slices authorized by each window. |
| P2-GAP-PRO-001 | Provider sanitizer gaps | `deferred` | `PROJECT_SOURCE` | Phase 1 closeout maps `developer_prompt` and `full_asset_body` sanitizer gaps to Phase 7. | Keep provider/prompt scope untouched in Phase 2. | N/A | Medium | Stop if validation requires provider or prompt asset changes. |
| P2-GAP-AGT-001 | Agent runtime wiring | `deferred` | `PROJECT_SOURCE` | Phase 1 closeout maps question/feedback runtime wiring to later runtime phases. | No LangGraph / Agent runtime migration in Phase 2. | N/A | High | Stop if unified context requires runtime migration. |

## 3. No-False-Done Watch List

Phase 2 must not be marked `complete_validated` while any of these remain true:

- `source_support_summary` is missing required fields.
- Question or Feedback core path independently interprets source support outside the shared summary, except derived compatibility mapping.
- `asset_archived` can become canonical evidence by default.
- Current answer new facts can become formal canonical assets.
- Asset conflicts do not create blocking / HITL state.
- `context_digest` is nondeterministic or omits summary/blocking issues.
- Direct / adjacent / job_gap / insufficient cases lack deterministic tests.
- Project source backfill is omitted without explicit deferred reason.

## 4. Window Status

| Window | Status | Notes |
| --- | --- | --- |
| P2-W0 | `validated_pending_commit` | Scope lock and gap register created; W0 validation passed before commit. |
| P2-W1 | `not_started` | Actionable path: `canonical_evidence.py` plus new contract tests. |
| P2-W2 | `not_started` | Actionable path: new context summary builder/service and tests. |
| P2-W3 | `not_started` | Actionable path: route question context through unified entry. |
| P2-W4 | `not_started` | Actionable path: route feedback context and centralize expected points. |
| P2-W5 | `not_started` | Actionable path: regression/eval seed coverage. |
| P2-W6 | `not_started` | Actionable path: closeout and source backfill. |
