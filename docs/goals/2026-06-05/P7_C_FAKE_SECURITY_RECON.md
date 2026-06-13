---
title: P7_C_FAKE_SECURITY_RECON
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-c-fake-security-recon
---

# P7 Fake / Security Boundary Recon Report

## 1. Evidence Header

- [GITHUB_CODE] branch: `main`
- [GITHUB_CODE] HEAD: `be30e8b13ac863c18a1238005c3cf97a941f07d2`
- [GITHUB_CODE] dirty state: clean；`git status --short` 无输出。
- [GOAL_SOURCE] Window: `P7-W1-PROVIDER-FAIL-CLOSED-FAKE-CLEANUP`；Agent C 为只读 Fake / Security Boundary Recon。
- [GOAL_SOURCE] 本轮未运行 pytest；报告中没有 `TEST_RESULT`，测试结论仅来自当前测试文件内容。

读取路径：

| Label | Path |
|---|---|
| GITHUB_CODE | `AGENTS.md`, `docs/00-governance/DOCS_INDEX.md`, `docs/03-implementation/BACKLOG.md` |
| GOAL_SOURCE | `docs/tmp/goal0605/phase7_provider_fail_closed/GOAL_P7_PROVIDER_FAIL_CLOSED.md`, `P7_ACCEPTANCE_CHECKLIST.md` |
| PROJECT_SOURCE | `docs/project-sources/07_CANONICAL_EVIDENCE_CONTRACT.md`, `08_DDD_TARGET_ARCHITECTURE.md`, `docs/02-design/SECURITY_PRIVACY.md` |
| GITHUB_CODE | `apps/api/app/infrastructure/llm/**`, `apps/api/app/application/ai_runtime/**`, `apps/api/app/application/polish/**`, `tests/fakes/**`, `tests/evals/**`, `tests/api/test_fake_llm_boundary.py`, `tests/api/test_llm_runtime.py` |

## 2. Fake Provider / Transport Inventory

| Item | Location | Status |
|---|---|---|
| Fake LLM transport | `apps/api/app/infrastructure/llm/fake_transport.py:43` | [GITHUB_CODE] `FakeLlmTransport.status = "deterministic_fake_only"`；支持 job_match、question、feedback、progress 等 deterministic outputs。 |
| Test fake facade | `tests/fakes/llm_transport.py:1` | [GITHUB_CODE] 明确 “Test-only”；从 infra fake re-export，供测试显式注入。 |
| Supported fake task list | `tests/fakes/llm_transport.py:11` | [GITHUB_CODE] `SUPPORTED_FAKE_TASK_TYPES` 包含 job_match、feedback、progress、question、report/review/weakness/asset/training 等测试任务。 |
| Runtime fake skeleton | `apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py:51` | [GITHUB_CODE] in-memory runtime 仍有 `pr4_fake_runtime` / `pr6_polish_feedback_fake_runtime` namespaces。 |
| Polish question fake runtime namespace | `apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py:75` | [GITHUB_CODE] checkpoint namespace 为 `pr5_polish_question_fake_runtime`。 |
| Eval fakes | `tests/evals/test_ai_eval_runners.py:175` | [GITHUB_CODE] eval runner 测试设置 `LLM_PROVIDER=fake` 后仍断言不依赖 `LLM_PROVIDER` / `FakeLlmTransport`。 |
| Missing package | `apps/api/app/application/ai_provider/**` | [UNKNOWN] 该目录当前不存在；未发现 application-level `ai_provider` package。 |

## 3. Runtime Wiring Fake-Rejection Status

- [GITHUB_CODE] `build_llm_transport_from_env()` 只允许 `openai/openai_compatible/openai-compatible/deepseek`，当 `LLM_PROVIDER=fake` 时抛 `LlmTransportConfigurationError`：`apps/api/app/infrastructure/llm/runtime.py:23-38`。
- [GITHUB_CODE] `create_app()` 在 app 启动时调用 `build_llm_transport_from_env()` 注入 `application.state.llm_transport`，所以 env-level fake 会阻断 app 构建：`apps/api/app/main.py:105`。
- [GITHUB_CODE] `tests/api/test_llm_runtime.py:33-56` 覆盖 runtime env fake rejection、`create_app()` fake rejection、以及显式 test fake injection 仍可用。
- [GITHUB_CODE] `tests/api/test_fake_llm_boundary.py:107-148` 覆盖 fake env rejection、`app.infrastructure.llm` 不导出 fake、生产代码不直接 import fake transport、测试必须经 `tests.fakes` facade 使用 fake。
- [GITHUB_CODE] 生产代码搜索 `FakeLlmTransport` 只命中 runtime error string 和 fake module 本体；未发现 `apps/api/app` 直接 import `app.infrastructure.llm.fake_transport`。
- [GITHUB_CODE] Question provider-enabled path 会拒绝 fake/deterministic provider draft：`apps/api/app/infrastructure/ai_runtime/langgraph/polish_question_runtime.py:339-349`。
- [GITHUB_CODE] Feedback direct service 当前仍允许显式 fake transport 生成 `succeeded=True` 且 payload `status == "generated"`：`tests/api/test_polish_feedback_generation_service.py:176-203`。这是 Phase 7 fake cleanup 必须处理的边界，不能标为 done。

## 4. Fake Allowed-Scope Inventory（tests/evals/replay）

- [GITHUB_CODE] Allowed tests: `tests/fakes/llm_transport.py` 是唯一 test fake facade；多个 API 测试从 `tests.fakes.llm_transport` 显式注入 fake。
- [GITHUB_CODE] Allowed eval: eval runners 基于 JSONL grader，不依赖 app LLM provider 或 fake runtime：`tests/evals/test_ai_eval_runners.py:175-197`。
- [GITHUB_CODE] Allowed replay/runtime skeleton: PR4 replay test 断言 replay read-only、不突变 checkpoint：`tests/api/test_pr4_fake_runtime_replay_resume.py:55-71`。
- [GITHUB_CODE] PR6 feedback fake runtime payload 明确 `provider_calls: 0`、`formal_business_writes: 0`、`db_business_writes: 0`：`apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py:221-245`。
- [GITHUB_CODE] Checkpointer 拒绝 raw graph state 和 sensitive metadata：`apps/api/app/infrastructure/ai_runtime/langgraph/checkpointer.py:59-90`。
- [UNKNOWN] 当前未执行测试，不能确认上述 gates 在本机当前环境通过。

## 5. Trace/Log/Persistence Safety Risk Register

| Risk | Severity | Evidence | Finding |
|---|---:|---|---|
| Unified provider request gate missing | High | [GITHUB_CODE] `OpenAICompatibleLlmTransport` 直接序列化 `request.evidence_bundle` 到 user message：`openai_compatible.py:420-447`；搜索未发现 `CompactProviderRequestBuilder`。 | 依赖上游各 builder 自律；Phase 7 需要 invocation 前统一 recursive forbidden-key rejection。 |
| Generic sanitizer gaps | High | [GITHUB_CODE] `ai_runtime/contracts.py:33-52` 不含 `developer_prompt`、`full_asset_body`；`tests/architecture/test_provider_boundary_static.py:45-80` 对这两个 key 标为 strict xfail known gap。 | 不能宣称 recursive forbidden-key gate complete。 |
| Feedback fake success semantics | High | [GITHUB_CODE] `test_service_with_fake_transport_returns_succeeded_generated_payload` 断言 fake 生成成功：`tests/api/test_polish_feedback_generation_service.py:176-183`。 | 与 Phase 7 “fake cannot be runtime provider / fallback cannot be generated success” 不一致。 |
| Local raw IO dump | Medium | [GITHUB_CODE] `AIFI_LOCAL_LLM_RAW_IO_ENABLED` 开启后写完整 request/response JSON：`openai_compatible.py:497-584`；测试确认会写 full request/response：`test_openai_compatible_raw_debug.py:33-64`。 | 默认 off 且排除 Authorization/API key，但仍是 raw payload dump；需生产禁用 gate / accepted-risk。 |
| Denylist drift | Medium | [GITHUB_CODE] question、feedback、ai_runtime、db repo、API response 各自维护 forbidden markers。 | 容易出现模块间漏项；Phase 7 应收敛到共享 forbidden-key catalog。 |
| Persistence raw fields exist but fail-closed | Low | [GITHUB_CODE] `LlmCallPayload.raw_enabled` / `raw_payload_ciphertext_ref` 字段存在：`models/ai_runtime.py:142-160`；repository 写入时 `raw_enabled=False` 且 debug raw capture 直接 raise：`repositories/ai_runtime/__init__.py:753-815`。 | 当前防护存在；仍需 gate 防止后续启用绕过。 |

## 6. Required Phase 7 Fake Cleanup Slice

1. [GITHUB_CODE] 新增或收敛 `CompactProviderRequestBuilder` / equivalent，统一输出 compact、schema-bound、redacted、safe-ref-only request；禁止 fallback 到 full prompt asset / full resume / full JD / full answer / full asset body。
2. [GITHUB_CODE] 在 provider invocation 前增加 recursive forbidden-key rejection；至少覆盖 checklist 中全部 key：`raw_prompt`, `system_prompt`, `developer_prompt`, `raw_completion`, `provider_payload`, `raw_provider_payload`, `full_resume`, `full_jd`, `full_answer`, `full_asset_body`, `api_key`, `token`, `secret`, `cookie`。
3. [GITHUB_CODE] 保留 `LLM_PROVIDER=fake` runtime rejection，并禁止 production wiring import fake；fake 仅经 `tests.fakes`、eval fixture、replay/in-memory skeleton 使用。
4. [GITHUB_CODE] 修改 Feedback fake direct-service 语义：fake injection 可用于测试 fixture，但不得映射为 runtime generated success；至少要 fixture-labeled / fake-visible / non-runtime-provider。
5. [GITHUB_CODE] 对 local raw IO dump 增加生产禁用或明确 release accepted-risk gate；默认 off 不等于 release-safe。
6. [PROJECT_SOURCE] 对齐 `07_CANONICAL_EVIDENCE_CONTRACT.md` provider boundary 与 `08_DDD_TARGET_ARCHITECTURE.md` Provider Boundary 职责，不把目标契约误标为当前已实现。

## 7. Tests/Gates to Add or Reuse

- Reuse: `tests/api/test_llm_runtime.py`
- Reuse: `tests/api/test_fake_llm_boundary.py`
- Reuse: `tests/architecture/test_provider_boundary_static.py`
- Reuse/add: provider request builder unit tests，覆盖 nested dict/list forbidden-key rejection。
- Add/update: feedback fake transport boundary test，禁止 fake direct path 被标为 runtime generated success。
- Reuse: `tests/api/test_pr7_polish_readonly_parity_gate.py` refs-only/raw input rejection gates。
- Reuse: `tests/api/test_pr8_polish_provider_trace_gate.py` fail-closed trace gate；该文件通过 `globals()["test_..."]` 暴露 raw-input rejection 测试。
- Reuse: `tests/api/test_openai_compatible_raw_debug.py`，补生产禁用或 release-risk gate。
- Not run: 本轮只读 recon 未执行 pytest，所有测试状态为 `UNKNOWN`。

## 8. Unknowns / Deferred Gaps

- [UNKNOWN] 未运行 `pytest tests/architecture`、`pytest tests/api/test_fake_llm_boundary.py`、`pytest tests/api/test_llm_runtime.py`，不能确认当前环境通过。
- [UNKNOWN] `apps/api/app/application/ai_provider/**` 不存在；是否应在 Phase 7 创建统一 provider boundary package 需由实施窗口决定。
- [UNKNOWN] 未审计外部 CI 配置是否会运行 fake boundary / provider boundary gates。
- [UNKNOWN] 未验证生产部署环境是否可能开启 `AIFI_LOCAL_LLM_RAW_IO_ENABLED`。
- [UNKNOWN] 未验证所有 Question / Feedback runtime provider call sites 是否已统一经过同一个 compact builder；当前证据只支持“存在多个分散 builder / validator / denylist”。
- [UNKNOWN] Phase 7 不能标记 done；当前最多可作为 Agent C `recon_done` 输入。