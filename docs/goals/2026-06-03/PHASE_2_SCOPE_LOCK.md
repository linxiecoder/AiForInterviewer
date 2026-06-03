---
title: PHASE_2_SCOPE_LOCK
type: scope-lock
status: evidence-only
owner: P2-W0-SCOPE-LOCK-RECON
permalink: ai-for-interviewer/docs/goals/2026-06-03/phase-2-scope-lock
---

# Phase 2 Scope Lock

本文件是 `P2-W0-SCOPE-LOCK-RECON` 的 evidence-only 输出。它不替代 active requirement、active design、delivery plan、ADR 或当前代码事实；当本文与当前代码或 active docs 冲突时，以当前代码和 active docs 为准。

## 1. Scope Lock

| Item | Value |
| --- | --- |
| Window ID | `P2-W0-SCOPE-LOCK-RECON` |
| Phase | Phase 2 - Canonical Evidence / Interview Context |
| Capability IDs | `CTX-001`, `CTX-002`, `CTX-003`, `FAG-001`, `WIN-001`, `SRC-001` |
| Allowed write files | `docs/goals/2026-06-03/PHASE_2_SCOPE_LOCK.md`, `docs/goals/2026-06-03/PHASE_2_ENTRY_GAP_REGISTER.md` |
| Forbidden writes | `apps/api/**`, `tests/**`, database migrations, prompt assets, provider implementation, API contracts |
| Behavior change | No |
| Prompt / schema / provider change | No |
| DB schema change | No |
| Rollback strategy | Delete the two W0 documents if forbidden-file audit or validation fails. |

## 2. Source Hierarchy Used

| Priority | Source | W0 result |
| --- | --- | --- |
| 1 | User explicit confirmation | The user authorized unattended sequential Phase 2 execution through `docs/tmp/goal0603/phase2_autorun.md`. |
| 2 | Current GitHub code | Worktree `phase2-autopilot` starts at `d806585`, aligned with `origin/main` and `main` before W0 edits. |
| 3 | Current tests / eval results | Existing test files were located; W0 did not run application tests because W0 is docs-only. |
| 4 | Project source docs | `AGENTS.md`, `DOCS_INDEX.md`, `DELIVERY_PLAN.md`, `BACKLOG.md`, `docs/goals/README.md`, Phase 1 closeout docs. |
| 5 | GOAL0531 historical intent | Not used as direct execution fact in W0. |

## 3. Recon Summary

### 3.1 Existing Project Sources

| Path | Exists | Note |
| --- | --- | --- |
| `docs/goals/README.md` | Yes | Confirms `docs/goals/` is execution evidence only. |
| `docs/goals/2026-06-03/PHASE_1_CLOSEOUT_ASSESSMENT.md` | Yes | Recommends Phase 1 close as `close_with_deferred_gaps`; maps Canonical Evidence / `SourceSupportSummary` to Phase 2. |
| `docs/goals/2026-06-03/PHASE_1_CLOSEOUT_GAP_REGISTER.md` | Yes | Lists Phase 2 deferred item for Canonical Evidence / `SourceSupportSummary`; provider sanitizer gaps are Phase 7; runtime wiring is Phase 5/6/8. |
| `docs/goals/2026-06-03/PHASE_2_SCOPE_LOCK.md` | Created in W0 | This document. |
| `docs/tmp/goal0603/phase2_goal.md` | Yes | Authoritative Phase 2 window plan. |
| `docs/tmp/goal0603/phase2_autorun.md` | Yes | Sequential unattended wrapper for P2-W0 through P2-W6. |

The named Project source pack files (`00_PROJECT_BRIEF.md`, `07_CANONICAL_EVIDENCE_CONTRACT.md`, `09_REFACTOR_TRACEABILITY_MATRIX.md`, etc.) were not present at repository root during W0 recon. P2-W6 may update them only if later recon discovers an actual path.

### 3.2 Current Code Paths

| Area | Current path | Current fact |
| --- | --- | --- |
| Canonical evidence service | `apps/api/app/application/polish/canonical_evidence.py` | `CanonicalEvidenceService.build_pack()` returns a dict pack with `schema_version`, owner/session/job/resume refs, `canonical_project_assets`, empty RAG/prior refs, legacy `source_support_level`, warnings, blocking issues and `context_digest`. |
| Source support level | `canonical_evidence.py`, `question_generation_service.py` | `canonical_evidence._source_support_level()` only emits `direct_project_evidence` or `insufficient_context`. `question_generation_service._source_support_level()` independently classifies direct / adjacent / job_gap / insufficient from selected chunks and canonical assets. |
| Progress context | `apps/api/app/application/polish/progress_context.py` | `build_polish_progress_context()` stores compact `canonical_evidence_pack`, `canonical_project_assets`, and digest inputs based on legacy `source_support_level`. |
| Question context | `apps/api/app/application/polish/use_cases.py`, `question_generation_service.py` | `_PolishUseCaseOperations.create_question_task()` passes `progress_context` to `QuestionGenerationService.generate()`. `_build_evidence_scope()` derives `EvidenceScope` and source support internally. |
| Feedback context | `apps/api/app/application/polish/use_cases.py`, `feedback_generation_service.py` | `_build_feedback_generation_context()` builds `FeedbackGenerationContext` from turn/answer/progress context and passes canonical assets only, not a full canonical pack or `SourceSupportSummary`. |
| Expected points | `apps/api/app/application/polish/feedback_rules.py` | `_expected_points()` reads `question_metadata`, progress node, canonical assets and job snapshot directly inside feedback rules. |
| Prompt assets | `question_generation_prompts.py`, `feedback_prompt_assets.py` | Read-only / forbidden for Phase 2 unless explicitly allowed by a later owner confirmation; W0 did not modify them. |
| Provider / DB / API | `apps/api/app/infrastructure/llm/**`, `apps/api/app/infrastructure/db/**`, `apps/api/app/api/v1/**` | Forbidden for Phase 2 normal autopilot. |

### 3.3 Existing Tests and Gaps

| Path | Exists | W0 classification |
| --- | --- | --- |
| `tests/api/test_polish_canonical_evidence.py` | Yes | Existing legacy canonical evidence tests. |
| `tests/api/test_polish_canonical_evidence_contract.py` | No | P2-W1 target test. |
| `tests/api/test_polish_source_support_summary.py` | No | P2-W1 target test. |
| `tests/api/test_polish_source_support_summary_service.py` | No | P2-W2/W5 target test. |
| `tests/api/test_polish_interview_context_question.py` | No | P2-W3/W5 target test. |
| `tests/api/test_polish_interview_context_feedback.py` | No | P2-W4/W5 target test. |
| `tests/api/test_polish_feedback_expected_points_context.py` | No | P2-W4/W5 target test. |
| `tests/api/test_polish_application_service_split.py` | Yes | Required regression command. |
| `tests/api/test_polish_question_refactor_phase1.py` | Yes | Required regression command. |
| `tests/architecture/` | Yes | Contains architecture boundary tests; run when changed or at W5. |
| `tests/evals/` | Yes | Existing eval convention is Python code-rule tests, not fixture-only data. |

## 4. Phase 1 Deferred Gaps Affecting Phase 2

| Deferred item | Phase 2 impact | Handling |
| --- | --- | --- |
| Canonical Evidence / `SourceSupportSummary` not implemented | Direct input to P2-W1 and P2-W2. | Implement within canonical/context files and tests only. |
| Remaining Polish ownership extraction | `use_cases.py` still orchestrates context entry. | Phase 2 may add compatibility adapters but must not restart broad ownership extraction. |
| Provider sanitizer gaps (`developer_prompt`, `full_asset_body`) | Not a Phase 2 blocker. | Keep deferred to Phase 7; do not edit provider/prompt assets. |
| Agent default catalog and runtime wiring | Not a Phase 2 blocker. | Keep deferred to later runtime phases; do not migrate LangGraph or agent runtime. |

## 5. Locked Phase 2 Windows

| Window | Main write scope | Behavior change | Validation |
| --- | --- | --- | --- |
| `P2-W0-SCOPE-LOCK-RECON` | Two Phase 2 evidence docs | No | `git diff --check`; `git status --short` |
| `P2-W1-CANONICAL-EVIDENCE-CONTRACT-ALIGN` | `canonical_evidence.py`, optional `context/**`, canonical/source-support tests, entry gap register | Internal additive compatibility only | W1 contract tests, Phase 1 regressions, `git diff --check` |
| `P2-W2-SOURCE-SUPPORT-SUMMARY-SERVICE` | `context/**`, canonical/source-support files, summary-service tests, entry gap register | Internal context classification only | W2 tests, W1 tests, Phase 1 regressions, `git diff --check` |
| `P2-W3-UNIFIED-INTERVIEW-CONTEXT-QUESTION` | context layer, `canonical_evidence.py`, `question_generation_service.py`, `use_cases.py`, question context tests, entry gap register | Internal context routing only | W3 tests, W2 tests, Phase 1 regressions, `git diff --check` |
| `P2-W4-FEEDBACK-CONTEXT-EXPECTED-POINTS` | context layer, feedback generation / application service, `question_metadata.py`, narrowly `feedback_rules.py`, feedback context tests, entry gap register | Internal context routing and expected-point extraction only | W4 tests, W2 tests, Phase 1 split regression, `git diff --check` |
| `P2-W5-EVIDENCE-SEEDS-BOUNDARY-REGRESSION` | Phase 2 tests, `tests/evals/**`, `tests/architecture/**`, entry gap register | No runtime behavior change | Phase 2 test matrix, Phase 1 regressions, `tests/architecture`, `git diff --check` |
| `P2-W6-SOURCE-BACKFILL-CLOSEOUT` | `docs/goals/**` and discovered Project source files only | No | Phase 2 test matrix, Phase 1 regressions, `git diff --check`, `git status --short` |

## 6. Global Forbidden Scope

The following remain forbidden through normal Phase 2 autopilot:

- `apps/api/app/application/polish/question_generation_prompts.py`
- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `apps/api/app/infrastructure/llm/**`
- `apps/api/app/infrastructure/db/**`
- `apps/api/app/api/v1/**`
- database migrations
- large-scale Agent runtime migration
- Phase 3 Domain Policy migration
- prompt/provider behavior rewrite
- formal asset update behavior changes
- Agent direct formal writes

## 7. Validation Commands

W0 validation:

```bash
git diff --check
git status --short
```

Baseline/regression commands used by later windows:

```bash
python -m pytest tests/api/test_polish_application_service_split.py tests/api/test_polish_question_refactor_phase1.py
python -m pytest tests/architecture
```

Window-specific tests must be run by exact path after they are created.

## 8. W0 Done Gate

| Gate | Status | Evidence |
| --- | --- | --- |
| Scope lock exists | `done` | This file. |
| Entry gap register exists | `done` | `PHASE_2_ENTRY_GAP_REGISTER.md`. |
| No app/test behavior changed | `validated` | `git status --short --untracked-files=all` showed only the two W0 docs; `git diff --check` passed. |
| P2-W1 actionable | `done` | `canonical_evidence.py` and W1 target tests identified. |

## 9. Exact P2-W1 Command

```text
/goal follow docs/tmp/goal0603/phase2_goal.md and execute only P2-W1
```

## 10. Phase 2 Closeout Backfill

W6 re-ran source pack discovery after P2-W1 through P2-W5 commits. All root-level source pack files named by `phase2_goal.md` remain absent in the current repository. No alternate same-name paths were found.

Closeout evidence:

- `docs/goals/2026-06-03/PHASE_2_CLOSEOUT_ASSESSMENT.md`
- `docs/goals/2026-06-03/PHASE_2_CLOSEOUT_GAP_REGISTER.md`
- `docs/goals/2026-06-03/PHASE_2_SOURCE_BACKFILL_STATUS.md`
- `docs/goals/2026-06-03/PHASE_3_ENTRY_SCOPE_LOCK.md`

Result: Phase 2 closes as `close_with_deferred_gaps` because code/test capabilities are validated and committed through P2-W6, but Project source pack backfill is `deferred_with_gap` pending owner-provided source paths.
