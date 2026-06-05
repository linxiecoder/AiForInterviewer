---
title: P7_B_QF_INTEGRATION_RECON
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-b-qf-integration-recon
---

# P7 Question / Feedback Integration Recon Report

## 1. Evidence Header

- `GITHUB_CODE` workspace: `/home/administrator/code/AiForInterviewer`
- `GITHUB_CODE` branch: `main`
- `GITHUB_CODE` HEAD: `be30e8b13ac863c18a1238005c3cf97a941f07d2`
- `GITHUB_CODE` dirty state: clean, `git status --short` 为空
- `TEST_RESULT`: 本轮未运行 pytest；只读 recon，避免测试缓存/临时产物写入
- `GOAL_SOURCE`: 已读 `docs/tmp/goal0605/phase7_provider_fail_closed/GOAL_P7_PROVIDER_FAIL_CLOSED.md`、`P7_ACCEPTANCE_CHECKLIST.md`
- `PROJECT_SOURCE`: 已读 `AGENTS.md`、`docs/00-governance/DOCS_INDEX.md`、`docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md`、`docs/project-sources/08_DDD_TARGET_ARCHITECTURE.md`
- `GITHUB_CODE` 候选代码已读/核查：`question_generation_service.py`、`feedback_generation_service.py`、Q/F `planned_workflow.py`、`use_cases.py`、指定 `tests/api/test_polish_feedback*.py`、`tests/api/test_polish_question_refactor_phase1.py`
- `GITHUB_CODE` mapping: `apps/api/app/application/ai_provider/**` 不存在；当前 provider path 在 `application.llm`、`application.polish`、`infrastructure.llm`、部分 `infrastructure.ai_runtime` 下

## 2. P5/P6 Current-Code State

- `GITHUB_CODE` P5 Question planned workflow 存在且接入当前 question create path：`run_question_planned_workflow` 生成 `question_candidate`、validation refs、candidate refs，并在 fallback/fake/deterministic provider 状态下返回 non-success reasons（`agents/question/planned_workflow.py:78`, `:124`, `:141`, `:435`）。
- `GITHUB_CODE` Question 应用路径先尝试 graph facade；graph disabled 时进入 direct service path；direct path 再通过 planned workflow，若有 validation errors 写 `VALIDATION_FAILED` task，否则经 `AgentPersistenceHandoff` formal write（`use_cases.py:492`, `:509`, `:767`, `:780`, `:796`）。
- `GITHUB_CODE` P6 Feedback planned handoff 存在并接入成功生成路径，添加 `feedback_candidate`、`asset_update_candidate_refs`、`asset_update_user_confirmation_required`、`fallback_reported_as_generated_success=False`（`agents/feedback/planned_workflow.py:37`, `:67`, `:78`, `:81`, `:119`）。
- `GITHUB_CODE` Feedback 当前 API 生成路径没有调用 `start_polish_feedback_generation`；`create_feedback_task` 直接调用 `FeedbackGenerationService.generate`，成功后持久化 `PolishFeedback.status="generated"` 和 `AiTaskStatus.SUCCEEDED`（`use_cases.py:1044`, `:1093`, `:1110`, `:1117`）。
- `UNKNOWN` P5/P6 不能标记 done：本轮未执行测试，且 Phase 7 provider boundary 仍有明确 deferred gaps。

## 3. Question Provider Path Map

| Step | Evidence | State |
| --- | --- | --- |
| API transport wiring | `create_app` 用 `build_llm_transport_from_env()`，并传入 question runtime facade（`main.py:105`, `:108`）；`LLM_PROVIDER=fake` 被拒绝（`runtime.py:23`, `:30`） | `GITHUB_CODE` runtime env fake rejected |
| API use case wiring | `_use_cases` 将同一 `llm_transport` 注入 `QuestionGenerationService`（`api/v1/polish.py:589`） | `GITHUB_CODE` active API path |
| Service provider request | `_generate_llm_question` 调 `build_question_provider_request`，将结果放入 `LlmTransportRequest.evidence_bundle` 后 `transport.generate(request)`（`question_generation_service.py:392`, `:398`, `:419`） | `GITHUB_CODE` active provider call site |
| Compact request | `build_question_provider_request` 返回 compact dict，包含 progress node、canonical evidence、history summary、expected output contract、安全摘要；未见统一 named `CompactProviderRequestBuilder`（`question_generation_prompts.py:632`, `:662`, `:673`, `:695`, `:723`, `:744`） | `GITHUB_CODE` partial equivalent |
| Fail-closed | transport config/unavailable/response/timeout/unknown exception 转 `QuestionGenerationResult(succeeded=False)`（`question_generation_service.py:420`, `:430`, `:456`, `:573`） | `GITHUB_CODE` provider failure not generated success |
| False-success mitigation | direct no transport/fake 先可生成 draft metadata，但 use case planned workflow 把 `not_configured`、`fake_transport`、`deterministic_*` 映射为 validation task（`question_generation_service.py:214`, `:230`, `agents/question/planned_workflow.py:442`） | `GITHUB_CODE` use-case mitigated, service-level risk remains |
| Graph provider | graph provider draft 内部复用 `QuestionGenerationService`；fake/deterministic result 被 `RuntimePolicyError` 拒绝（`polish_question_runtime.py:308`, `:322`, `:345`） | `GITHUB_CODE` graph path fake rejected |

## 4. Feedback Provider Path Map

| Step | Evidence | State |
| --- | --- | --- |
| API transport wiring | `_use_cases` 将 `llm_transport` 注入 `FeedbackGenerationService`（`api/v1/polish.py:593`） | `GITHUB_CODE` active API path |
| Service provider request | `FeedbackGenerationService.generate` build prompt asset，再调用 `FeedbackGenerationAgent(...).generate`（`feedback_generation_service.py:82`, `:96`） | `GITHUB_CODE` active provider call site |
| Provider payload | `FeedbackGenerationAgent` 用 `_provider_prompt(prompt_asset)` 作为 `LlmTransportRequest.evidence_bundle`，再 `transport.generate(request)`（`feedback_agent.py:32`, `:36`, `:43`, `:183`） | `GITHUB_CODE` active provider call site |
| Compact prompt | `build_feedback_prompt_asset` 构建 `provider_prompt`；provider prompt 不带 full `input_data`，包含 compact current question/answer/evidence/snapshots 并做 budget trim（`feedback_prompt_assets.py:181`, `:237`, `:254`, `:313`, `:360`） | `GITHUB_CODE` partial compact boundary |
| Fail-closed | no transport 返回 `llm_transport_unavailable`；agent exception 返回 `provider_failed`；schema/unsafe validation failure 返回 `succeeded=False`（`feedback_generation_service.py:88`, `feedback_agent.py:44`, `feedback_generation_service.py:101`, `:115`） | `GITHUB_CODE` provider failure/validation failure not generated |
| Runtime graph note | `start_polish_feedback_generation` 存在，但 `create_feedback_task` 未使用；in-memory feedback graph 是 fake runtime（`facade.py:88`, `in_memory_runtime.py:84`, `:254`） | `GITHUB_CODE` not active API generation path |

## 5. False-Success Risk Register

| Risk | Label | Evidence | Impact |
| --- | --- | --- | --- |
| Feedback explicit fake transport returns generated success | `GITHUB_CODE` | test expects `FeedbackGenerationService(FakeLlmTransport()).generate(...)` -> `succeeded is True` and payload status `generated`（`test_polish_feedback_generation_service.py:176`） | Phase 7 fake cleanup gap unless explicit test/eval/replay marker gates runtime injection |
| Question service-level fake/degraded returns draft success | `GITHUB_CODE` | fake/no-transport service tests expect `result.succeeded` with `deterministic_fake_transport` or `deterministic_degraded_generation` metadata（`test_polish_question_refactor_phase1.py:1619`, `:1671`） | Use-case planned workflow mitigates, but direct service consumers can misread success |
| Feedback low-confidence may still persist as generated task | `INFERENCE` | schema test allows payload `status="low_confidence"`（`test_polish_feedback_generation_schema.py:312`）；storage wrapper sets metadata `generated=True` and create path writes `status="generated"` on any service success（`use_cases.py:2522`, `:2540`, `:1110`） | Needs explicit Phase 7 status-visible mapping test |
| Unified forbidden-key gate incomplete | `GITHUB_CODE` | `ai_runtime.contracts` sensitive keys omit `developer_prompt` and `full_asset_body`（`contracts.py:33`）；static test xfails both（`test_provider_boundary_static.py:50`, `:63`） | Cannot claim recursive forbidden-key gate done |
| Feedback graph helper overclaim | `GITHUB_CODE` | feedback trace request helper exists, but active feedback use case does not call facade; in-memory graph path says fake start（`business_graphs/polish_feedback_graph.py:323`, `in_memory_runtime.py:254`） | Do not treat graph helper as Phase 7 active wiring |

## 6. Required Phase 7 Wiring Slice

- `GOAL_SOURCE` Required slice: protect active Question and Feedback provider paths without API/DB/domain/prompt-business-rule/Phase 8/9/L5 changes.
- `GITHUB_CODE` Add or consolidate a shared provider boundary around `LlmTransportRequest.evidence_bundle`: schema-bound, compact, recursive denylist, redacted, fail-closed before `transport.generate`.
- `GITHUB_CODE` Update central sanitizer denylist to include at least `developer_prompt` and `full_asset_body`; close existing strict xfails.
- `GITHUB_CODE` Question insertion point: immediately after `build_question_provider_request` and before `LlmTransportRequest` / `transport.generate` in `_generate_llm_question`.
- `GITHUB_CODE` Feedback insertion point: immediately after `_provider_prompt(prompt_asset)` and before `LlmTransportRequest` / `transport.generate` in `FeedbackGenerationAgent.generate`.
- `GITHUB_CODE` Fake cleanup: preserve explicit fake for tests/evals/replay, but active runtime/service path must not map fake transport output to normal generated success.
- `GITHUB_CODE` Feedback low-confidence/status mapping: ensure low-confidence is status-visible and not persisted/reported as normal generated success.

## 7. Tests/Gates to Add or Reuse

- Reuse: `tests/api/test_polish_question_refactor_phase1.py` for Question compact provider request, fake/degraded metadata, invalid LLM validation task.
- Reuse: `tests/api/test_polish_question_graph_integration.py` for graph provider-enabled fake rejection.
- Reuse: `tests/api/test_polish_feedback_generation_service.py` for no transport, provider exception, invalid schema, unsafe provider payload.
- Reuse: `tests/api/test_polish_feedback_runtime.py` for API-level provider unavailable/timeout no generated feedback.
- Reuse with gap: `tests/architecture/test_provider_boundary_static.py`; must remove xfails for `developer_prompt` and `full_asset_body`.
- Add: recursive forbidden-key tests for actual Question `build_question_provider_request` output and Feedback `provider_prompt` before provider invocation.
- Add: Feedback fake transport must fail closed in runtime/service path unless explicitly marked test/eval/replay.
- Add: Feedback `low_confidence` payload must not become normal generated success in task/API/persistence semantics.
- Add: grep gate from goal for forbidden provider keys and fake runtime wiring; interpret test-only hits separately.

## 8. Unknowns / Deferred Gaps

- `UNKNOWN` Tests were not executed in this read-only Agent B window.
- `UNKNOWN` Remote GitHub was not fetched; evidence is current local `main` worktree at `be30e8b...`, clean state.
- `deferred` Named `CompactProviderRequestBuilder` / `ProviderRequestValidator` is not present; current implementation is function-level partial equivalent.
- `deferred` `apps/api/app/application/ai_provider/**` absent; current mapping must use existing `application.llm` / `application.polish` / `infrastructure.llm`.
- `deferred` Central sanitizer recursive denylist has known xfail gaps for `developer_prompt` and `full_asset_body`.
- `deferred` Feedback graph/facade path is not active for `create_feedback_task`; current provider protection must target service path first.
- `deferred` Feedback fake and low-confidence false-success semantics need Phase 7 implementation + tests before any `done` claim.