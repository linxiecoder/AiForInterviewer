---
title: PHASE7_CLOSEOUT
type: project-source
status: active
permalink: ai-for-interviewer/docs/project-sources/20-phase7-closeout
---

# Phase 7 Closeout Source Backfill

This file records active Project source backfill for Phase 7 provider request fail-closed windows. It does not replace `docs/03-delivery/BACKLOG.md`, `docs/03-delivery/DELIVERY_PLAN.md`, code truth, or tests.

## P7-W3 Answer Excerpt Policy

Window ID: `P7-W3-ANSWER-EXCERPT-POLICY-AND-IMPLEMENTATION`

Status: `validated_with_deferred_gaps`

Controller Decision B:

- Current answer is an allowed bounded primary task input for Feedback Agent.
- `current_answer.answer_text` may be sent to provider only as a bounded current-answer field required for feedback generation.
- This must not be represented as `full_answer`.

Implementation evidence:

- `apps/api/app/application/polish/feedback_prompt_assets.py` records `answer_text_policy=current_answer_bounded_primary_input`, `answer_text_max_chars=1200`, `answer_text_is_bounded=true`, and `full_answer_forbidden=true` under both `current_answer` and `input_contract`.
- Historical / same-question answers remain compact summaries; W3 removes same-question evidence fallback from raw `answer_text`.
- `full_answer` remains forbidden by shared P7 provider forbidden-key catalog and recursive provider / DTO validation.

Test evidence:

- `tests/api/test_polish_feedback_generation_service.py` covers bounded current answer policy metadata, short current answer equality, provider prompt forbidden-key absence, and historical no-raw-answer fallback.
- `tests/api/test_polish_feedback_agent_io_alignment.py` covers provider request policy metadata and nested `full_answer` fail-closed before transport.
- `tests/api/test_provider_boundary.py`, `tests/api/test_provider_global_backstop.py`, and `tests/architecture/test_provider_boundary_static.py` continue to cover shared forbidden-key catalog and recursive fail-closed behavior.
- Required P7-W3 narrow suite result: `51 passed`.
- `git diff --check`: clean.
- Required `rg` scans completed; hits are forbidden catalogs, safety rules, policy metadata, application/domain answer fields, and test fixtures. No new raw/full provider payload allowance is claimed from grep output alone.

Gap result:

| Gap ID | Status | Evidence |
|---|---|---|
| `P7-GAP-003` | `closed_by_policy_and_tests` | Controller Decision B + W3 policy metadata + focused tests |
| `P7-GAP-005` | `deferred` | full-repo pytest、web tests、e2e tests remain out of scope for P7-W3 and are deferred to P7-W4 |

## Non-Claims

- Phase 7 is not `done`.
- Phase 8 runtime is not started.
- Phase 9 eval / CI gate is not started.
- Full-repo pytest、web tests、e2e tests have not been claimed by this source record.
