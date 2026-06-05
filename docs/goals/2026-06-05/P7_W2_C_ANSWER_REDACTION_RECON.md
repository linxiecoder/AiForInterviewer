---
title: P7_W2_C_ANSWER_REDACTION_RECON
type: goal-evidence
status: evidence-only
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-w2-c-answer-redaction-recon
---

# P7-W2-C Answer Redaction / Excerpt Policy Recon

Mode: read-only

## 结论

`full_answer` / `full_asset_body` / `full_resume` / `full_jd` 作为 forbidden keys 已由 provider boundary 递归阻断。但 Feedback provider prompt 会以 `current_answer.answer_text` 和 `answer_excerpt` 形式发送当前回答，最大 1200 字符；短回答若不超过 1200 字符，可能完整发送。

本轮不修改 prompt、scoring semantics 或 answer persistence，因此该项保留为 deferred product/security decision。

## Required Searches

| Command | Key Finding |
|---|---|
| `rg "current_answer|answer_excerpt|full_answer|full_asset_body|full_resume|full_jd" apps/api/app tests -n` | `feedback_prompt_assets.py` 使用 `current_answer.answer_text` `max_chars=1200`；`full_*` keys 是 forbidden catalog。 |
| `rg "FakeLlmTransport|FakeLLM|fake_transport|LLM_PROVIDER.*fake" apps/api/app tests -n` | feedback service 对 fake transport 返回 non-success；runtime env rejects fake。 |

## Evidence

| Path | Evidence | Classification |
|---|---|---|
| `apps/api/app/application/llm/provider_boundary.py` | `P7_PROVIDER_FORBIDDEN_KEYS` includes `full_answer`, `full_asset_body`, `full_resume`, `full_jd` | acceptable forbidden-key backstop |
| `apps/api/app/application/polish/feedback_prompt_assets.py` | `current_answer.answer_text` max 1200 chars in prompt asset and provider prompt | bounded excerpt, short answer may equal full text |
| `tests/api/test_polish_feedback_generation_service.py` | existing tests assert current answer is included in prompt asset | current behavior is locked by tests |
| `apps/api/app/application/polish/use_cases.py` | follow-up `parent_answer_excerpt` uses shorter excerpt | acceptable bounded excerpt with non-claim |

## Risk Classification

| Risk | Classification | Decision |
|---|---|---|
| forbidden `full_*` keys | acceptable bounded excerpt with explicit non-claim | covered by boundary |
| feedback `current_answer.answer_text` | needs stricter max length / digest / truncation if policy requires never-full short answers | deferred |
| product question: may provider see full short answer? | requires product/security decision | deferred |

## Deferred Reason

Current answer is core feedback input. Changing it to digest-only or forced partial truncation may affect feedback quality and scoring explanation. The user explicitly prohibited prompt rewrite, scoring semantics change, and answer persistence change in this window.
