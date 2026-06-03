---
title: P3_W2_FINAL_REPORT
type: execution-evidence
status: evidence-only
owner: P3-W2-QUESTION-DOMAIN-POLICIES
permalink: ai-for-interviewer/docs/goals/2026-06-03/p3-w2-final-report
---

# P3-W2 Final Report

本文件记录 `P3-W2-QUESTION-DOMAIN-POLICIES` 的执行证据。它不替代 active requirements、active design docs、`BACKLOG.md`、`DELIVERY_PLAN.md`、ADR 或当前代码事实。

## 1. Controller Decisions Applied

| Decision | Treatment |
| --- | --- |
| Missing Phase 2 closeout evidence | Accepted only as Phase 3 deferred input / known gap. |
| P3-W1 source support | Accepted as `partial_with_deferred_gap`; no duplicate P3-W1 implementation. |
| CTX-002 / `SourceSupportSummary` | Kept as `deferred_gap`; not marked done. |
| Next window | Executed P3-W2 before Phase 2 backfill / CTX-002 repair. |

## 2. Scope

| Area | Result |
| --- | --- |
| Question grounding | Extracted to pure domain policy and kept `validate_question_grounding()` as application adapter. |
| Follow-up coverage | Extracted matrix / focus decision to pure domain policy; `use_cases.py` maps feedback payload into value input and calls the policy. |
| Prompt / provider / DB / API / Agent runtime / frontend | Not modified. |
| `question_metadata.py` public helper | Not modified because it was not in the P3-W2 allowed write set; recorded as residual compatibility gap. |

## 3. Files Changed

| File | Purpose |
| --- | --- |
| `apps/api/app/domain/polish/policies/question_grounding_policy.py` | New pure question grounding policy. |
| `apps/api/app/domain/polish/policies/follow_up_coverage_policy.py` | New pure follow-up coverage policy. |
| `apps/api/app/domain/polish/policies/__init__.py` | Export new policy types. |
| `apps/api/app/application/polish/question_grounding.py` | Thin adapter from `QuestionBlueprint` to domain policy input and back to `GroundingResult`. |
| `apps/api/app/application/polish/use_cases.py` | Follow-up context now calls domain coverage policy through a local input-mapping adapter. |
| `tests/domain/polish/test_question_grounding_policy.py` | Domain tests for direct / adjacent / job gap / insufficient / canonical conflict semantics. |
| `tests/domain/polish/test_follow_up_coverage_policy.py` | Domain tests for completed focus, used focus, asset conflict, weak / missing focus behavior. |

## 4. Validation Evidence

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall apps/api/app/domain/polish apps/api/app/application/polish` | Passed. |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/domain/polish/test_question_grounding_policy.py tests/domain/polish/test_follow_up_coverage_policy.py -q` | `10 passed`. |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/api/test_polish_question_refactor_phase1.py -q` | `64 passed`. |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/architecture -q` | `22 passed, 2 xfailed`; xfails are existing P1-W3 provider boundary known gaps. |
| `PYTHONPATH=.:apps/api AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -s tests/api/test_polish_application_service_split.py -q` | `7 passed`. |
| `git diff --check` | Passed. |

## 5. Boundary Scan Notes

| Scan | Result |
| --- | --- |
| `rg -n "from app\\.infrastructure|import app\\.infrastructure|FastAPI|sqlalchemy|Session\\(|openai|anthropic|LLM|Prompt|prompt" apps/api/app/domain/polish` | Only `FastAPI` appears as a technology-stack literal in source-support / grounding term lists; no forbidden import was introduced. |
| `rg -n "raw_prompt|system_prompt|developer_prompt|raw_completion|provider_payload|raw_provider_payload|full_resume|full_jd|full_asset_body|token|secret|cookie|api_key" apps/api/app/domain/polish apps/api/app/application/polish` | Hits are existing prompt/sanitizer/validation strings or technical variable names; no new raw prompt/provider payload persistence path was introduced by P3-W2. |

## 6. Remaining Gaps

| Gap | Status | Reason |
| --- | --- | --- |
| Phase 2 closeout evidence | `deferred_gap` | Accepted as deferred input by controller; not backfilled in P3-W2. |
| SRC-001 / source pack backfill | `deferred_gap` | Not in P3-W2 scope. |
| CTX-002 / `SourceSupportSummary` | `deferred_gap` | No full summary object or payload propagation added; not marked complete. |
| P3-W1 source support | `partial_with_deferred_gap` | No duplicate implementation; only used as existing bridge context. |
| `question_metadata.py` follow-up helper | `residual_application_helper` | File was not in P3-W2 allowed write set, so old helper was not converted to a thin adapter. Main follow-up use case now calls domain policy. |
| `next_question_agent.py` post-check guardrail | `residual_contract_validator_guardrail` | File was not in P3-W2 allowed write set; remains as provider-output contract validation, not a domain policy. |

## 7. Non-Claims

This report does not claim:

- Phase 2 is done.
- SRC-001 is done.
- CTX-002 or `SourceSupportSummary` is done.
- P3-W1 is complete beyond `partial_with_deferred_gap`.
- All Phase 3 Domain Policies are done.
- P3-W3 / P3-W4 / P3-W5 / P3-W6 are complete.
