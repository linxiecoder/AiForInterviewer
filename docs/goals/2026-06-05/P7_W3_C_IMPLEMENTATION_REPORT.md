---
title: P7_W3_C_IMPLEMENTATION_REPORT
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w3-c-implementation-report
---

# P7-W3-C Implementation Report

Mode: single-writer implementation

## Scope Lock

- Phase: `Phase 7 - Provider request fail-closed`
- Window ID: `P7-W3-ANSWER-EXCERPT-POLICY-AND-IMPLEMENTATION`
- Allowed implementation files touched: `apps/api/app/application/polish/feedback_prompt_assets.py`, `tests/api/test_polish_feedback_generation_service.py`, `tests/api/test_polish_feedback_agent_io_alignment.py`, and W3 evidence docs.
- Forbidden scope respected: no API routes, DB migrations, frontend, domain policies, scoring semantics, persistence behavior, Phase 8 runtime, or Phase 9 eval / CI gate changes.

## Red Evidence

| Test | Red Result |
|---|---|
| `test_feedback_request_marks_current_answer_as_bounded_primary_input` | failed with `KeyError: 'answer_text_policy'` before implementation |
| `test_prompt_asset_does_not_fallback_to_historical_answer_text_when_summary_missing` | failed because historical `answer_text` fallback reached evidence serialization before implementation |

Command:

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_generation_service.py::test_feedback_request_marks_current_answer_as_bounded_primary_input tests/api/test_polish_feedback_generation_service.py::test_prompt_asset_does_not_fallback_to_historical_answer_text_when_summary_missing -q
```

Result: `2 failed`.

## What Changed

- Added `_CURRENT_ANSWER_TEXT_MAX_CHARS = 1200` and `_CURRENT_ANSWER_TEXT_POLICY = "current_answer_bounded_primary_input"`.
- Added `answer_text_policy`, `answer_text_max_chars`, `answer_text_is_bounded`, and `full_answer_forbidden` to prompt asset `current_answer` and `input_contract`.
- Added the same policy metadata to provider prompt `current_answer` and `input_contract`.
- Removed historical same-question evidence fallback from `answer_text`; only `answer_summary` / `summary` may become historical evidence.
- Added `raw_provider_payload`, `full_answer`, and `full_asset_body` to Feedback prompt asset forbidden markers / unsafe context filtering.
- Added focused tests for short current answer policy metadata, historical answer fallback removal, provider prompt no-forbidden-key recursion, and nested `full_answer` fail-closed.

## Green Evidence

Focused red/green validation after implementation:

```bash
PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_generation_service.py::test_feedback_request_marks_current_answer_as_bounded_primary_input tests/api/test_polish_feedback_generation_service.py::test_prompt_asset_does_not_fallback_to_historical_answer_text_when_summary_missing tests/api/test_polish_feedback_agent_io_alignment.py::test_feedback_agent_sends_compact_provider_prompt_with_required_contract_fields tests/api/test_polish_feedback_agent_io_alignment.py::test_feedback_agent_blocks_full_answer_before_transport -q
```

Result: `4 passed`.

## Claim Ledger

| Claim | Status | Evidence |
|---|---|---|
| `current_answer.answer_text` is explicitly allowed as bounded primary input | validated | policy metadata in code and tests |
| Short current answer may equal submitted text | validated | `test_feedback_request_marks_current_answer_as_bounded_primary_input` |
| Historical same-question answers do not send raw `answer_text` fallback | validated | `test_prompt_asset_does_not_fallback_to_historical_answer_text_when_summary_missing` |
| `full_answer` remains fail-closed | validated | `test_feedback_agent_blocks_full_answer_before_transport` |
| Phase 7 is done | not claimed | `P7-GAP-005` remains deferred |

## Final Implementation Status

`validated_with_deferred_gaps`
