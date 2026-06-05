---
title: P7_W3_B_POLICY_CONTRACT_DESIGN
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w3-b-policy-contract-design
---

# P7-W3-B Policy Contract Design

Window ID: `P7-W3-ANSWER-EXCERPT-POLICY-AND-IMPLEMENTATION`

Mode: read-only first

## Contract Proposal

The provider request contract records Controller Decision B in existing Feedback provider prompt fields. No new top-level provider request key is required.

```python
provider_prompt["current_answer"] = {
    "answer_id": "...",
    "answer_text": "...",
    "answer_text_policy": "current_answer_bounded_primary_input",
    "answer_text_max_chars": 1200,
    "answer_text_is_bounded": True,
    "full_answer_forbidden": True,
    "answer_round": ...,
}

provider_prompt["input_contract"] = {
    "raw_model_io_storage": False,
    "context_mode": "quick_compact",
    "answer_text_policy": "current_answer_bounded_primary_input",
    "answer_text_max_chars": 1200,
    "answer_text_is_bounded": True,
    "full_answer_forbidden": True,
}
```

Evidence: `apps/api/app/application/polish/feedback_prompt_assets.py:282-289` and `apps/api/app/application/polish/feedback_prompt_assets.py:335-345`.

## Allowed / Forbidden Field Semantics

| Field | Semantics |
|---|---|
| `current_answer.answer_text` | Allowed bounded primary task input for Feedback Agent; not a `full_answer` fallback. |
| `answer_text_policy` | Fixed audit marker: `current_answer_bounded_primary_input`. |
| `answer_text_max_chars` | Fixed bound: `1200`. |
| `answer_text_is_bounded` | Must be `True`. |
| `full_answer_forbidden` | Must be `True`; this is a policy marker and does not allow any actual `full_answer` key. |
| `same_question_answers` | Compact historical summaries only; no `answer_text`, no raw/full answer payload. |

Forbidden keys remain: `raw_prompt`, `system_prompt`, `developer_prompt`, `raw_completion`, `provider_payload`, `raw_provider_payload`, `full_resume`, `full_jd`, `full_answer`, `full_asset_body`, `token`, `secret`, `cookie`, `api_key`.

## Validation Plan

| Requirement | Test Evidence |
|---|---|
| Bounded current answer is allowed | `tests/api/test_polish_feedback_generation_service.py:226-244` |
| Short current answer may equal submitted text | `tests/api/test_polish_feedback_generation_service.py:229-236` |
| `full_answer` still fails closed recursively | `tests/api/test_polish_feedback_agent_io_alignment.py:274-287`; `tests/api/test_provider_global_backstop.py:51-58` |
| Historical / same-question answers do not gain raw answer text | `tests/api/test_polish_feedback_generation_service.py:247-342`; `tests/api/test_polish_feedback_generation_service.py:524-541` |
| Provider prompt excludes raw/full/provider/secrets keys | `tests/api/test_polish_feedback_generation_service.py:331-342` |

## No-Go Boundaries

- Do not remove `current_answer.answer_text`.
- Do not rename current answer to `full_answer`.
- Do not allow historical `answer_text`, `full_answer`, or raw answer payloads.
- Do not change scoring semantics, output schema, API routes, DB schema, frontend, Phase 8 runtime, or Phase 9 eval / CI gate.
- Do not add prompt business-rule rewrites beyond explicit policy metadata.

## Conclusion

Policy B closes `P7-GAP-003` by documenting and testing a narrow contract: current answer text is allowed only as bounded current-answer primary input, while `full_answer` and all raw/full/provider/secrets keys remain recursively fail-closed.
