---
title: PHASE_3_SCOPE_LOCK
type: scope-lock
status: evidence-only
owner: P3-W0-DOMAIN-POLICY-SCOPE-LOCK
permalink: ai-for-interviewer/docs/goals/2026-06-03/phase-3-scope-lock
---

# Phase 3 Scope Lock

本文件是 `P3-W0-DOMAIN-POLICY-SCOPE-LOCK` 的 docs-only recon / scope-lock 记录。它只作为 `docs/goals/` execution evidence，不替代 active requirement、active design、`BACKLOG.md`、`DELIVERY_PLAN.md`、ADR、Project source 或当前代码事实。

## 1. Window Boundary

| Item | Value |
| --- | --- |
| Window ID | `P3-W0-DOMAIN-POLICY-SCOPE-LOCK` |
| Phase | Phase 3 - Domain Policies |
| Mode | Recon / scope-lock / window catalog only |
| Behavior change allowed | No |
| Implementation change allowed | No |
| Allowed write files | `docs/goals/**` only |
| Forbidden write files | `apps/**`, `tests/**`, prompt assets, provider / infrastructure, DB schema / migrations, API routes / contracts, Agent runtime wiring |
| Commit scope | docs-goals planning artifacts only |

## 2. Source Hierarchy

| Label | Meaning for this window |
| --- | --- |
| USER_CONFIRMED | User requested Phase 3 P3-W0 scope-lock and multi-agent execution. |
| GITHUB_CODE | Current workspace code at `75dce4346c717dc38ac62ef544b53f4c425c419d` is implementation truth. |
| TEST_RESULT | Current tests and eval files are behavior evidence only if executed or directly inspected. |
| PROJECT_SOURCE | `docs/tmp/goal0603_phase3/*` and registered active docs define target governance for this window; `docs/goals/` remains evidence-only. |
| GOAL_SOURCE | GOAL0531 / old goal material is historical intent only. |
| SUBAGENT_OUTPUT | Used only after controller audit; it does not override code or docs. |
| UNKNOWN | Missing files or unproven claims stay explicit gaps. |

Conflict rule: current code describes current implementation; Project source describes target architecture; differences are recorded as gaps and must not be resolved by assumption.

## 3. Root Cause

Phase 3 aims to move deterministic business rules into pure Domain Policy modules while preserving application orchestration, prompt rendering, provider behavior, DB schema, API contracts, and Agent runtime boundaries. P3-W0 is required because current repository evidence shows a mixed state:

- `SourceSupportPolicy` already exists in `apps/api/app/domain/polish/policies/source_support_policy.py`.
- Existing `docs/goals/2026-06-03/PHASE_3_CLOSEOUT_ASSESSMENT.md` records a prior `P3-W1-SOURCE-SUPPORT-POLICY` closeout with a deferred summary gap.
- Phase 2 closeout docs requested by the Phase 3 prompt are absent from `docs/goals/2026-06-03/`.
- Question grounding, follow-up coverage, feedback review rules, and feedback next-action decisions still have substantial policy-like logic in application modules.

Therefore this window locks scope, records gaps, and identifies the next safe window. It does not start implementation.

## 4. Current Evidence Summary

| Area | Current evidence | Label |
| --- | --- | --- |
| Phase 2 closeout docs | `PHASE_2_CLOSEOUT_ASSESSMENT.md`, `PHASE_2_CLOSEOUT_GAP_REGISTER.md`, and `PHASE_2_SOURCE_BACKFILL_STATUS.md` were not present under `docs/goals/2026-06-03/`. | UNKNOWN / GAP |
| Source pack files | Root source-pack files such as `00_PROJECT_BRIEF.md`, `01_SOURCE_OF_TRUTH_POLICY.md`, and `17_PHASE_ROADMAP_LOCK.md` were not present at repo root. `docs/tmp/goal0603_phase3/source_refs/PHASE3_SOURCE_EXCERPTS.md` exists as condensed Project-source excerpt. | PROJECT_SOURCE / GAP |
| P3-W1 source support | `SourceSupportPolicy` exists and is imported by `canonical_evidence.py` and `question_generation_service.py`. Existing Phase 3 closeout docs record `implemented_and_validated_with_deferred_summary_gap`. | GITHUB_CODE / PROJECT_SOURCE |
| `SourceSupportSummary` | No `SourceSupportSummary` symbol was found. Current object is `SourceSupportDecision`, and payloads still propagate legacy `source_support_level`. | GITHUB_CODE / GAP |
| Question grounding | `validate_question_grounding()` remains in `apps/api/app/application/polish/question_grounding.py`; it blocks unsupported factual claims, adjacent evidence as completed experience, job-gap factual claims, empty factual evidence, and unsupported technology stack claims. | GITHUB_CODE |
| Follow-up coverage | Follow-up focus and coverage selection remains in application code, especially `question_metadata.py` and `use_cases.py`; prompt/context compaction occurs in question prompt/service modules. | GITHUB_CODE |
| Feedback review rules | `apply_feedback_core_rules()` and helpers in `feedback_rules.py` still own asset consistency, answer coverage, answer change, feedback cards, and next-action rewrite logic. | GITHUB_CODE |
| Boundary tests | `tests/architecture/test_domain_polish_policy_boundary.py` exists and checks domain policy imports against forbidden dependencies. `tests/domain/polish/` does not exist. | TEST_RESULT / GAP |
| Feedback tests / evals | Existing API tests cover asset conflict, archived exclusion, unsupported claim, missing coverage, answer change, and next-action removal. Evals are deterministic offline code-rule evidence, not production AI quality proof. | TEST_RESULT |

## 5. Policy-Like Logic Inventory

| Capability | Current owner | Classification | Target |
| --- | --- | --- | --- |
| QAG-001 source support classification | `SourceSupportPolicy`; bridge usage in `canonical_evidence.py` and `question_generation_service.py` | Domain policy already partial; application bridge | Keep as domain policy; keep CTX-002 full summary gap explicit |
| QAG-002 question grounding | `question_grounding.py`, `next_question_agent.py`, graph quality gate | Domain policy candidate plus adapter candidates | Move deterministic gate to pure `question_grounding_policy.py`; leave old function as compatibility adapter if needed |
| QAG-003 follow-up coverage | `question_metadata.py`, `use_cases.py`, `question_generation_service.py` metadata helpers | Domain policy candidate plus application orchestration | Move focus selection / completed-focus / repetition decisions to pure `follow_up_coverage_policy.py` |
| FAG-002 asset consistency | `feedback_rules.py` | Domain policy candidate | Move confirmed-only, archived exclusion, conflict, unsupported claim decisions to pure policy |
| FAG-003 answer coverage | `feedback_rules.py` | Domain policy candidate | Move expected / covered / missing / weak / contradicted decisions to pure policy |
| FAG-004 answer change | `feedback_rules.py` | Domain policy candidate | Move prior-attempt retained / regressed / fixed / repeated / trend decisions to pure policy |
| FAG-005 feedback next action | `feedback_rules.py`, `feedback_validation.py` | Domain policy candidate plus validation adapter | Move action rewrite / blocking / candidate confirmation decisions to pure policy |
| Prompt/provider boundary | `question_generation_prompts.py`, `feedback_prompt_assets.py`, `feedback_agent.py`, `feedback_schema.py` | Prompt-provider boundary | Do not edit in P3-W0; future windows may only ensure they render policy-decided context |
| Application orchestration | `use_cases.py`, `question_generation_service.py`, `feedback_generation_service.py`, application service wrappers | Application orchestration | Call policies, map DTOs, manage transactions and persistence; do not own core deterministic rules after extraction |

## 6. P3-W0 Scope Decision

P3-W0 is scope-locked as docs-only.

Allowed next actions in this window:

- Create `PHASE_3_SCOPE_LOCK.md`.
- Create `PHASE_3_WINDOW_CATALOG.md`.
- Create `PHASE_3_ENTRY_GAP_REGISTER.md`.
- Create `PHASE_3_DECISION_OPTIONS.md`.
- Update `docs/goals/README.md` index.
- Run docs-only validation and diff audit.
- Commit only these docs-goals planning changes.

Forbidden next actions in this window:

- Create or migrate Domain Policy code.
- Modify `apps/**` or `tests/**`.
- Change prompt assets, provider behavior, DB schema, API contracts, runtime wiring, formal asset write behavior, or frontend.
- Mark full `SourceSupportSummary`, CTX-002, or Phase 3 as closed.
- Treat `docs/goals/` evidence as active delivery state.

## 7. Validation Plan

P3-W0 validation is limited to scope and documentation safety:

| Command | Purpose |
| --- | --- |
| `git status --short --untracked-files=all` | Confirm changed files and ensure no implementation paths are changed. |
| `git diff --check` | Check whitespace and patch sanity. |
| Targeted Phase 2 overstatement scan | Ensure this window does not overstate Phase 2 state. |
| Targeted P3-W0 completion scan | Ensure P3-W0 does not claim code-window completion. |
| `git status --short --untracked-files=all apps tests` | Confirm no `apps/**` or `tests/**` changes. |

## 8. Next Safe Window

The next implementation window must wait for controller confirmation. The recommended path is resume-aware:

1. Treat existing P3-W1 as `partial_with_deferred_gap`; audit or repair only if controller chooses.
2. Start P3-W2 question grounding / follow-up policies only after accepting the Phase 2 closeout evidence gap and CTX-002 gap as explicit inputs, or after choosing to backfill them first.
3. Keep prompts, provider, DB, API, Agent runtime, and formal writes out of Phase 3 implementation windows unless the controller explicitly stops and expands scope.
