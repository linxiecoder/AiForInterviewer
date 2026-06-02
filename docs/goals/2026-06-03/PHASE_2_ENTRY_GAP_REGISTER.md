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
| P2-GAP-CTX-001 | `CTX-001` CanonicalEvidencePack | `closed` | `TEST_RESULT` | W1 added `source_support_summary` to `CanonicalEvidenceService.build_pack()`, included it in stable digest input with `blocking_issues`, and kept legacy `source_support_level` derived from the summary. | Align or compatibility-adapt pack to target shape and stable digest rules. | P2-W1 | Medium | Closed by `tests/api/test_polish_canonical_evidence_contract.py`; caller routing remains separate W2-W4 work. |
| P2-GAP-CTX-002 | `CTX-002` SourceSupportSummary | `closed` | `TEST_RESULT` | W1 added `SourceSupportSummary`, allowed levels, validation, serialization and pack compatibility. W2 added `SourceSupportSummaryService` under `application/polish/context`, with deterministic direct / adjacent / job_gap / insufficient classification and asset status / conflict / current-answer guards. | Add required fields: level, primary/adjacent/job_gap refs, missing_context, reason_codes, confidence, policy_version, computed_at. | P2-W1, P2-W2 | High | Closed by W1 contract tests and W2 service tests; caller routing remains W3/W4. |
| P2-GAP-CTX-003 | Source support single interpretation | `closed` | `TEST_RESULT` | W3 routed Question support level through `SourceSupportSummaryService`; W4 routed Feedback context through `InterviewContextBuilder.build_feedback_context()` and additive `FeedbackGenerationContext.source_support_summary`. | Question/Feedback consume summary from unified context entry; legacy level remains derived only. | P2-W2, P2-W3, P2-W4 | High | Closed by W3 Question context tests and W4 Feedback context tests; prompt/provider assets remained untouched. |
| P2-GAP-CTX-004 | Interview Context | `closed` | `TEST_RESULT` | W3 added `InterviewContextBuilder.build_question_context()`; W4 added `build_feedback_context()` and uses it before `FeedbackGenerationContext` construction. | Add context-level unified entry or compatibility adapter without API/provider behavior changes. | P2-W2, P2-W3, P2-W4 | Medium | Closed with pure context builder and already-loaded app data only. |
| P2-GAP-CTX-005 | Feedback canonical pack usage | `closed` | `TEST_RESULT` | W4 adds `canonical_evidence_pack`, `source_support_summary`, and derived `source_support_level` to `FeedbackGenerationContext` while preserving existing canonical asset fields. | Feedback context receives canonical evidence and source support summary from unified entry. | P2-W4 | Medium | Closed by `tests/api/test_polish_interview_context_feedback.py`; existing feedback generation and canonical evidence tests passed. |
| P2-GAP-FAG-001 | Expected points builder | `closed` | `TEST_RESULT` | W4 added `ExpectedPointsBuilder` under `application/polish/context` and changed `feedback_rules._expected_points()` to delegate to it without moving other feedback policies. | Move/delegate expected-point construction to context-owned builder or explicit adapter. | P2-W4 | Medium | Closed by `tests/api/test_polish_feedback_expected_points_context.py`; feedback domain policies were not migrated. |
| P2-GAP-TEST-001 | Contract tests missing | `closed` | `TEST_RESULT` | W1 added `tests/api/test_polish_canonical_evidence_contract.py` and `tests/api/test_polish_source_support_summary.py`; both passed after RED/GREEN. | Add direct tests for pack/summary serialization, invalid level, refs, reason codes. | P2-W1 | Medium | Closed by W1 validation. |
| P2-GAP-TEST-002 | Shared summary service tests missing | `closed` | `TEST_RESULT` | W2 added `tests/api/test_polish_source_support_summary_service.py`, covering direct / adjacent / job_gap / insufficient, archived exclusion, conflict HITL marker and current-answer non-canonical rule. | Cover direct / adjacent / job_gap / insufficient and asset status/conflict rules. | P2-W2, P2-W5 | High | Closed by W2 validation; W5 may add broader regression seed coverage. |
| P2-GAP-TEST-003 | Question/Feedback context tests missing | `closed` | `TEST_RESULT` | W3 added `tests/api/test_polish_interview_context_question.py`; W4 added `tests/api/test_polish_interview_context_feedback.py` and `tests/api/test_polish_feedback_expected_points_context.py`. | Prove real callers consume unified context entry. | P2-W3, P2-W4 | High | Closed by focused application/service-level tests without provider rewrite. |
| P2-GAP-SEED-001 | Eval seed convention needs mapping | `closed` | `TEST_RESULT` | W5 added `tests/evals/test_phase2_canonical_evidence_rules.py` as a Python eval-rule seed, matching the existing `tests/evals` convention instead of creating a new fixture system. | Add deterministic eval seeds only if they fit existing convention; otherwise defer with reason. | P2-W5 | Low | Closed by W5 eval seed validation; no claim that full AI quality gate is complete. |
| P2-GAP-SRC-001 | Project source pack path absent | `deferred` | `GITHUB_CODE` | W6 re-ran discovery for all root-level source pack files named in `phase2_goal.md`; all remain missing and no alternate same-name path was found. | Backfill actual discovered Project source files or explicitly defer absent paths in closeout. | P2-W6 | Medium | Deferred in `PHASE_2_CLOSEOUT_GAP_REGISTER.md`; owner must provide source pack path before matrix / risk / acceptance / roadmap backfill. |
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
| P2-W0 | `validated_committed` | Scope lock and gap register committed in `84dc0e2`. |
| P2-W1 | `validated_committed` | `SourceSupportSummary` contract and `CanonicalEvidencePack` compatibility shape committed in `f49203e`. |
| P2-W2 | `validated_committed` | Shared source support summary service committed in `57b8abc`. |
| P2-W3 | `validated_committed` | Question context routing committed in `8bc3d46`. |
| P2-W4 | `validated_committed` | Feedback context routing and expected points builder committed in `f966251`. |
| P2-W5 | `validated_committed` | Deterministic Phase 2 eval seed and context boundary architecture test committed in `5049ff1`. |
| P2-W6 | `validated_pending_commit` | Closeout docs created; source pack backfill deferred because source files are absent. |
