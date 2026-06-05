---
title: P7_W3_FINAL_REPORT
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w3-final-report
---

# P7-W3 Final Report

Window ID: `P7-W3-ANSWER-EXCERPT-POLICY-AND-IMPLEMENTATION`

Phase: `Phase 7 - Provider request fail-closed`

Capability IDs: `PRO-001`, `PRO-002`, `FAKE-001`, `WIN-001`, `SRC-001`

Final status: `validated_with_deferred_gaps`

This report does not mark Phase 7 `done`.

## 1. Root Cause

P7-W2 left `P7-GAP-003` deferred because bounded `current_answer.answer_text` could equal the complete text for a short answer. The gap was policy ambiguity, not an implementation requirement to remove current answer from Feedback provider input.

## 2. Controller Decision B

Controller selected Policy B:

- Current answer is allowed bounded primary task input for Feedback Agent.
- `current_answer.answer_text` may be sent to provider only as a bounded current-answer field required for feedback generation.
- It must not be represented as `full_answer`.
- Raw/full/provider/secrets keys remain forbidden and fail-closed.

## 3. Answer Policy Recon

Recon output: `docs/goals/2026-06-05/P7_W3_A_ANSWER_POLICY_RECON.md`.

Conclusion: current answer text is already a bounded Feedback primary input, historical answers are intended to be compact summaries, and `full_answer` is already in the shared P7 forbidden-key catalog. The recon identified one W3 implementation risk: historical same-question evidence could fallback to `answer_text` when no summary existed.

## 4. Policy Contract

Contract design output: `docs/goals/2026-06-05/P7_W3_B_POLICY_CONTRACT_DESIGN.md`.

Implemented contract metadata under existing `current_answer` and `input_contract` fields:

- `answer_text_policy`: `current_answer_bounded_primary_input`
- `answer_text_max_chars`: `1200`
- `answer_text_is_bounded`: `true`
- `full_answer_forbidden`: `true`

No new top-level provider request key was added.

## 5. What Changed

- Added explicit answer text policy metadata to Feedback prompt asset and provider prompt.
- Kept `current_answer.answer_text` bounded at 1200 chars.
- Removed historical same-question evidence fallback from raw `answer_text`.
- Added `raw_provider_payload`, `full_answer`, and `full_asset_body` to Feedback prompt asset forbidden markers / unsafe context filtering.
- Added focused tests for bounded current answer policy metadata, short answer equality, historical no-raw-answer fallback, forbidden-key absence, and nested `full_answer` fail-closed.

## 6. Files Changed

- `apps/api/app/application/polish/feedback_prompt_assets.py`
- `tests/api/test_polish_feedback_generation_service.py`
- `tests/api/test_polish_feedback_agent_io_alignment.py`
- `docs/goals/2026-06-05/P7_W3_A_ANSWER_POLICY_RECON.md`
- `docs/goals/2026-06-05/P7_W3_B_POLICY_CONTRACT_DESIGN.md`
- `docs/goals/2026-06-05/P7_W3_C_IMPLEMENTATION_REPORT.md`
- `docs/goals/2026-06-05/P7_W3_FINAL_REPORT.md`
- `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`
- `docs/project-sources/14_RISK_REGISTER.md`
- `docs/project-sources/17_PHASE_ROADMAP_LOCK.md`
- `docs/project-sources/20_PHASE7_CLOSEOUT.md`

## 7. Behavior Before / After

Before:

- `current_answer.answer_text` was bounded, but not explicitly tagged as allowed bounded primary input.
- A short current answer could equal submitted text without policy metadata explaining why this was allowed.
- Historical same-question evidence could fallback to `answer_text` when no summary was present.

After:

- `current_answer.answer_text` remains present and bounded for Feedback generation.
- Provider request carries auditable policy metadata proving Policy B.
- Historical same-question answers are summaries only; no raw historical answer text fallback remains.
- Actual `full_answer` keys still fail closed recursively before transport.

## 8. Validation Commands and Results

Focused red/green:

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_generation_service.py::test_feedback_request_marks_current_answer_as_bounded_primary_input tests/api/test_polish_feedback_generation_service.py::test_prompt_asset_does_not_fallback_to_historical_answer_text_when_summary_missing -q
```

Result before implementation: `2 failed`.

Focused green:

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_generation_service.py::test_feedback_request_marks_current_answer_as_bounded_primary_input tests/api/test_polish_feedback_generation_service.py::test_prompt_asset_does_not_fallback_to_historical_answer_text_when_summary_missing tests/api/test_polish_feedback_agent_io_alignment.py::test_feedback_agent_sends_compact_provider_prompt_with_required_contract_fields tests/api/test_polish_feedback_agent_io_alignment.py::test_feedback_agent_blocks_full_answer_before_transport -q
```

Result: `4 passed`.

Required suite:

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_provider_boundary.py tests/api/test_provider_global_backstop.py tests/architecture/test_provider_boundary_static.py tests/api/test_polish_feedback_agent_io_alignment.py tests/api/test_polish_feedback_generation_service.py -q
```

Result: `51 passed in 1.59s`.

Other checks:

- `git diff --check`: passed.
- Required forbidden-key `rg` scan: completed; hits are forbidden catalogs, filtering rules, policy metadata (`full_answer_forbidden`), auth/domain fields, and test fixtures.
- Required `current_answer` / `answer_text` `rg` scan: completed; hits include expected provider policy metadata, current answer fields, API/domain persistence fields, and tests.
- Markdown safety: `scripts/scan_md_mojibake.py` is not present in this repo; direct `rg` scan for replacement characters and typical mojibake fragments returned no hits.

## 9. Claim Ledger

| Claim | Status | Evidence |
|---|---|---|
| `current_answer.answer_text` is allowed bounded primary input | validated | policy metadata + tests |
| Short current answer may equal submitted text | validated | `test_feedback_request_marks_current_answer_as_bounded_primary_input` |
| `full_answer` remains forbidden recursively | validated | provider boundary / DTO tests + `test_feedback_agent_blocks_full_answer_before_transport` |
| Historical same-question answers do not gain raw answer fields | validated | provider prompt tests + no historical fallback test |
| Provider prompt does not include raw/full/provider/secrets payload allowance | validated | required suite + `rg` interpretation |
| P7-GAP-003 closed | validated | source backfill marks `closed_by_policy_and_tests` |
| Phase 7 done | not claimed | `P7-GAP-005` remains deferred |
| Phase 8 / Phase 9 started | not claimed | no runtime/eval/CI files changed |

## 10. P7-GAP-003 Closure Evidence

`P7-GAP-003` is closed by policy and tests:

- Controller Decision B formalized in provider request metadata.
- Short current answer equality is tested as allowed current primary input.
- Historical answer `answer_text` fallback is removed and tested.
- Actual `full_answer` key remains recursively fail-closed.

## 11. Remaining Gaps

- `P7-GAP-002`: still partially mitigated; per-task schema compactness is proven by builder / static gate rather than a universal runtime schema registry.
- `P7-GAP-004`: single-writer scope conformance recorded; machine proof of human worktree identity remains `UNKNOWN`.
- `P7-GAP-005`: full-repo pytest、web tests、e2e tests remain deferred to P7-W4.

## 12. Source Backfill Result

Updated Project sources:

- `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`
- `docs/project-sources/14_RISK_REGISTER.md`
- `docs/project-sources/17_PHASE_ROADMAP_LOCK.md`
- `docs/project-sources/20_PHASE7_CLOSEOUT.md`

Backfill result: `P7-GAP-003` is `closed_by_policy_and_tests`; Phase 7 remains `validated_with_deferred_gaps`.

## 13. Final Status

`validated_with_deferred_gaps`

## 14. Follow-up Goal

Execute P7-W4 to close `P7-GAP-005` with full-repo pytest, web tests, e2e validation, and release-grade source backfill. Do not start Phase 8 or Phase 9 from P7-W3 alone.
