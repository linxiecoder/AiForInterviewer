---
title: P7_D_IMPLEMENTATION_REPORT
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-d-implementation-report
---

# P7 D Implementation Report

## Status

`validated_with_deferred_gaps`

本报告只记录 Agent D 单写者实现与本地验证结果，不声明 Phase 7 done。Agent E audit、Agent F source backfill、`docs/project-sources/**` 回填均未执行。

## Root Cause

- [GITHUB_CODE] Question / Feedback provider path 在 `LlmTransportRequest.evidence_bundle` 前缺少共享 compact provider boundary。
- [GITHUB_CODE] `FeedbackGenerationAgent._provider_prompt()` 在缺失 `provider_prompt` 时会 fallback 到完整 `prompt_asset`。
- [GITHUB_CODE] `FeedbackGenerationService(FakeLlmTransport()).generate(...)` 仍会返回 `succeeded=True` 与 `status="generated"`。
- [GITHUB_CODE] `ai_runtime.contracts` 的敏感 key catalog 未覆盖 `developer_prompt` / `full_asset_body`。

## What Changed

- [GITHUB_CODE] 新增 `app.application.llm.provider_boundary`，包含 P7 forbidden key catalog、递归 provider request validator、schema top-level key 校验、credential-like value redaction、validated `LlmTransportRequest` builder。
- [GITHUB_CODE] Question `_generate_llm_question` 在调用 transport 前校验 compact request；命中 forbidden key / schema error 时返回 `QuestionGenerationResult(succeeded=False)`，错误为 `provider_request_validation_failed`，不调用 transport。
- [GITHUB_CODE] Feedback `FeedbackGenerationAgent.generate` 在调用 transport 前校验 compact `provider_prompt`；缺失 compact prompt 或 forbidden key 时返回 failed `AgentOutputEnvelope`，`provider_status=not_called`，不调用 transport。
- [GITHUB_CODE] Feedback `_provider_prompt` 不再 fallback 到完整 `prompt_asset`。
- [GITHUB_CODE] Feedback direct-service 显式 fake transport 改为 fake-visible non-success：`validation_errors=("fake_transport_not_runtime_provider",)`，`provider_status=fake_transport`，`llm_called=False`。
- [GITHUB_CODE] `ai_runtime.contracts` 与 `AgentOutputEnvelope` metadata denylist 对齐 P7 key catalog。

## Files Changed

- `apps/api/app/application/llm/provider_boundary.py`
- `apps/api/app/application/ai_runtime/contracts.py`
- `apps/api/app/application/llm/agent_io.py`
- `apps/api/app/application/polish/question_generation_service.py`
- `apps/api/app/application/polish/feedback_agent.py`
- `apps/api/app/application/polish/feedback_generation_service.py`
- `tests/architecture/test_provider_boundary_static.py`
- `tests/api/test_provider_boundary.py`
- `tests/api/test_polish_question_refactor_phase1.py`
- `tests/api/test_polish_feedback_agent_io_alignment.py`
- `tests/api/test_polish_feedback_generation_service.py`
- `docs/goals/2026-06-05/P7_D_IMPLEMENTATION_REPORT.md`

## TDD Red Commands And Results

| Command | Result |
|---|---|
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/architecture/test_provider_boundary_static.py tests/api/test_provider_boundary.py -q` | RED: exit 2; `ModuleNotFoundError: No module named 'app.application.llm.provider_boundary'`. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_question_refactor_phase1.py -k provider_boundary_blocks -q` | RED: exit 1; unsafe provider request still reached `llm_call` and failed later as `llm_question_kind_mismatch`, not provider boundary failure. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_generation_service.py -k fake_transport -q` | RED: exit 1; fake direct service still returned `succeeded=True`. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_agent_io_alignment.py -k 'compact_provider_prompt_missing or forbidden_provider_prompt' -q` | RED: exit 1; missing / unsafe provider prompt still returned succeeded envelope and called transport. |

## Green Commands And Results

| Command | Result |
|---|---|
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/architecture/test_provider_boundary_static.py -q` | PASS: `2 passed`. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_provider_boundary.py tests/api/test_fake_llm_boundary.py tests/api/test_llm_runtime.py -q` | PASS: `15 passed`. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_question_refactor_phase1.py -q` | PASS: `65 passed`. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_generation_service.py tests/api/test_polish_feedback_agent_io_alignment.py tests/api/test_polish_feedback_runtime.py -q` | PASS: `44 passed`. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_*provider*.py -q` | PASS: `19 passed`. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/api/test_polish_feedback*.py -q` | PASS: `63 passed`. |
| `PYTHONPATH=.:apps/api PYTHONDONTWRITEBYTECODE=1 AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1 .venv/bin/python -m pytest -p no:cacheprovider tests/architecture -q` | PASS: `22 passed`. |
| `git diff --check` | PASS: no output. |

## Grep Gate Results

| Command | Result / Interpretation |
|---|---|
| `rg -n "raw_prompt|system_prompt|developer_prompt|provider_payload|raw_provider_payload|raw_completion|full_resume|full_jd|full_answer|full_asset_body|api_key|token|secret|cookie" apps/api/app tests docs -S` | RUN: exit 0. Full output is large and includes expected denylist/catalog entries, tests asserting rejection, auth/session `token` / `cookie` fields, API schema null boundary fields, current/historical docs, and safety-rule text. Not sufficient by itself to prove no gap; scoped interpretation below was used. |
| same pattern scoped to changed files | RUN: exit 0. Hits are expected P7 catalog/regex entries, existing safety metadata strings, new rejection tests, existing tests asserting non-leakage, and `provider_payload_diagnostic` failure metadata. No changed-file hit shows provider request sending raw/full fields as runtime payload. |
| `rg -n "LLM_PROVIDER.*fake|fake.*LLM_PROVIDER|FakeLLM|FakeProvider|fake_provider|FakeTransport" apps/api/app tests -S` | RUN: exit 0. Hits are runtime rejection text, tests, eval env check, and `tests.fakes` facade. |
| same fake pattern scoped to changed files | PASS-LIKE: exit 1 / no matches. Agent D changed files did not add fake runtime wiring. |

## Known Gaps / Not Done Claims

- [UNKNOWN] Agent E audit has not run; this report is not independently verified audit evidence.
- [UNKNOWN] Agent F source backfill has not run; `docs/project-sources/**` intentionally unchanged.
- [UNKNOWN] Full grep output is broad and contains historical docs / tests / safety text; Agent D only interpreted changed-file scoped hits.
- [GITHUB_CODE] Local raw IO debug path in `openai_compatible.py` was not changed in this minimal implementation slice.
- [INFERENCE] Feedback compact prompt still includes a bounded current answer excerpt; Agent D did not change prompt business wording or product semantics, so no claim is made that every short answer can never equal a full answer by content.
- [USER_CONFIRMED] No public API shape, DB schema, domain policy, frontend, migration, Phase 8 runtime, Phase 9 CI gate, or L5 work was intentionally changed.
- [USER_CONFIRMED] Phase 7 is not claimed done by Agent D.
