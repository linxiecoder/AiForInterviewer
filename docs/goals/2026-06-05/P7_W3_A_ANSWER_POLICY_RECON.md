---
title: P7_W3_A_ANSWER_POLICY_RECON
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w3-a-answer-policy-recon
---

# P7-W3-A Answer Policy Recon

Window ID: `P7-W3-ANSWER-EXCERPT-POLICY-AND-IMPLEMENTATION`

Mode: read-only recon

## Scope

- Inspect feedback prompt / provider request construction.
- Identify `current_answer`, `answer_text`, `same_question_answers`, historical answers, and `full_answer` surfaces.
- Classify each surface as allowed bounded current-answer primary input, compact historical answer summary, forbidden full/raw answer, or unrelated test fixture.

## Evidence Table

| Surface | Evidence | Classification |
|---|---|---|
| Feedback context required `answer_text` | `apps/api/app/application/polish/feedback_generation_service.py:21-29` | allowed bounded current-answer primary input |
| Prompt asset `current_answer.answer_text` | `apps/api/app/application/polish/feedback_prompt_assets.py:116-123` | allowed bounded current-answer primary input |
| Provider prompt `current_answer.answer_text` | `apps/api/app/application/polish/feedback_prompt_assets.py:335-345` | allowed bounded current-answer primary input |
| Current answer evidence item | `apps/api/app/application/polish/feedback_prompt_assets.py:483-526` | allowed bounded current-answer primary input |
| Provider evidence excerpt limits | `apps/api/app/application/polish/feedback_prompt_assets.py:408-421` | current answer bounded to `1200`; other evidence bounded to `300` |
| Provider `same_question_answers` compact shape | `apps/api/app/application/polish/feedback_prompt_assets.py:450-464` | compact historical answer summary |
| Historical evidence construction | `apps/api/app/application/polish/feedback_prompt_assets.py:528-540` | compact historical answer summary; no `answer_text` fallback after W3 |
| Feedback provider request top-level allowlist | `apps/api/app/application/polish/feedback_agent.py:21-45` | allows `current_answer` / `same_question_answers`; does not allow `full_answer` |
| Provider boundary recursive validator | `apps/api/app/application/llm/provider_boundary.py:39-57` and `apps/api/app/application/llm/provider_boundary.py:93-105` | forbidden full/raw answer fail-closed |
| DTO-level forbidden catalog | `apps/api/app/application/llm/types.py:10-26` | `full_answer` remains forbidden |
| Current answer policy tests | `tests/api/test_polish_feedback_generation_service.py:226-244` | proves short current answer can equal task input and carries policy metadata |
| Historical answer leak tests | `tests/api/test_polish_feedback_generation_service.py:247-342` and `tests/api/test_polish_feedback_generation_service.py:524-541` | proves historical raw answer text is not sent |
| Feedback agent `full_answer` rejection | `tests/api/test_polish_feedback_agent_io_alignment.py:274-287` | recursive fail-closed before transport |

## Surface Classification

### a. Allowed bounded current-answer primary input

`current_answer.answer_text` is Feedback Agent primary task input. It is bounded with `_CURRENT_ANSWER_TEXT_MAX_CHARS = 1200` and tagged with `answer_text_policy = current_answer_bounded_primary_input`, `answer_text_is_bounded = True`, and `full_answer_forbidden = True`.

Short current answers may equal the user-submitted answer text because this is the current primary task input, not a `full_answer` fallback.

### b. Compact historical answer summary

`same_question_answers` and historical turn surfaces are compact summaries. Provider-facing `same_question_answers` keeps only summary-style fields and does not include `answer_text`.

W3 removed the historical evidence fallback from `answer_text`; when a historical answer has no `answer_summary` / `summary`, it is omitted instead of sent as a raw answer excerpt.

### c. Forbidden full/raw answer

`full_answer` is still forbidden by the shared P7 provider catalog and recursively rejected by both `ProviderRequestValidator` and `LlmTransportRequest`.

Forbidden keys remain fail-closed: `raw_prompt`, `system_prompt`, `developer_prompt`, `raw_completion`, `provider_payload`, `raw_provider_payload`, `full_resume`, `full_jd`, `full_answer`, `full_asset_body`, `token`, `secret`, `cookie`, `api_key`.

### d. Unrelated test fixture

Fixture strings such as `PREVIOUS_FULL_ANSWER_*_SHOULD_NOT_BE_INCLUDED`, `FULL_JD_SHOULD_NOT_BE_INCLUDED`, and nested `full_answer` injections are test probes, not allowed provider payload fields.

## Risk / UNKNOWN

- This recon does not claim Phase 7 `done`; `P7-GAP-005` full-repo / web / e2e validation remains deferred to P7-W4.
- `docs/project-sources/20_PHASE7_CLOSEOUT.md` did not exist before W3 and must be created only as an authorized P7 closeout source backfill record.

## Conclusion

Controller Decision B is implementable without removing current answer from Feedback provider input. The required closure action is explicit policy metadata plus tests proving current answer is bounded primary input, historical answers remain summaries, and `full_answer` remains recursively fail-closed.
