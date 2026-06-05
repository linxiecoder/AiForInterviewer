---
title: P7_A_PROVIDER_BOUNDARY_RECON
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-05/p7-a-provider-boundary-recon
---

# P7 Provider Boundary Recon Report

## 1. Evidence Header

| 项 | 证据 |
| --- | --- |
| branch | `main` [GITHUB_CODE] |
| HEAD | `be30e8b13ac863c18a1238005c3cf97a941f07d2` [GITHUB_CODE] |
| dirty state | `git status --short` 无输出，工作区干净 [GITHUB_CODE] |
| 已读规则/目标 | `AGENTS.md`, `docs/00-governance/DOCS_INDEX.md`, `docs/tmp/goal0605/phase7_provider_fail_closed/GOAL_P7_PROVIDER_FAIL_CLOSED.md`, `P7_ACCEPTANCE_CHECKLIST.md`, `reference_project_sources_snapshot/SOURCE_SNAPSHOT_MANIFEST.md` [GOAL_SOURCE] |
| 已检查代码/测试范围 | `apps/api/app/application/llm/**`, `apps/api/app/infrastructure/llm/**`, `apps/api/app/application/polish/**`, `apps/api/app/application/ai_runtime/**`, `apps/api/app/infrastructure/ai_runtime/**`, `apps/api/app/api/v1/polish.py`, `apps/api/app/main.py`, `tests/**` provider/prompt/llm/runtime 相关文件 [GITHUB_CODE] |
| 路径存在性 | `apps/api/app/application/ai_provider/**` 不存在；`application/polish`, `application/ai_runtime`, `infrastructure/llm`, `infrastructure/ai_runtime` 存在 [GITHUB_CODE] |

## 2. Provider Construction Map

- 共享传输 DTO 是 `LlmTransportRequest`，字段包括 `contract_ids`, `task_type`, `input_refs`, `evidence_bundle`, `graph_name`, `node_name`, `prompt_version`, `schema_id`；DTO 本身没有 schema-bound compact 校验或 forbidden-key 递归拒绝逻辑。见 `apps/api/app/application/llm/types.py:9` [GITHUB_CODE]。
- API 入口通过 `_use_cases(..., llm_transport)` 注入同一个 `LlmTransport`，并传入 `PolishProgressTreeLlmService`, `QuestionGenerationService`, `FeedbackGenerationService`。见 `apps/api/app/api/v1/polish.py:573` [GITHUB_CODE]。
- Question 路径：`QuestionGenerationService.generate()` 构造 `prompt_asset`，校验 anchor contract，然后 `_generate_llm_question()` 调用 `build_question_provider_request()`，再放入 `LlmTransportRequest.evidence_bundle`。见 `question_generation_service.py:131`, `:381` [GITHUB_CODE]。
- Question compact request 的当前等价 builder 是 `build_question_provider_request()`，输出顶层字段为 `task_type`, `schema_id`, `schema_version`, `prompt_version`, `progress_node`, `source_support_level`, `canonical_evidence`, `history_summary`, `expected_output_contract`, `safety_rules_summary`。它避免发送 full prompt asset，但没有集中式递归 forbidden-key rejection。见 `question_generation_prompts.py:632` [GITHUB_CODE]。
- Feedback 路径：`build_feedback_prompt_asset()` 生成完整 `prompt_asset`，同时附加 `provider_prompt`；`FeedbackGenerationAgent.generate()` 使用 `_provider_prompt(prompt_asset)` 放入 `LlmTransportRequest.evidence_bundle`。见 `feedback_prompt_assets.py:84`, `feedback_agent.py:26` [GITHUB_CODE]。
- Feedback compact request 当前分散在 `_provider_compact_prompt()`，包含 `task_type`, `feedback_mode`, `input_contract`, `current_question`, `current_answer`, `evidence`, `canonical_project_assets`, `output_schema` 等。见 `feedback_prompt_assets.py:237` [GITHUB_CODE]。
- OpenAI-compatible transport 会把 `request.evidence_bundle` 原样嵌入 chat user message 的 JSON：`task_type`, `input_refs`, `evidence_bundle`。见 `openai_compatible.py:417` [GITHUB_CODE]。

## 3. Invocation / Parser / Validation Map

- Provider 选择由 `build_llm_transport_from_env()` 控制：默认/openai/deepseek 使用 `OpenAICompatibleLlmTransport`；`LLM_PROVIDER=fake` 明确抛出 `LlmTransportConfigurationError`。见 `infrastructure/llm/runtime.py:23` [GITHUB_CODE]。
- API 启动时设置 `application.state.llm_transport = build_llm_transport_from_env()`；依赖读取 app state 中的 transport。见 `apps/api/app/main.py:103`, `api/deps.py:57` [GITHUB_CODE]。
- OpenAI invocation：`generate()` 检查 API key 后调用 `_generate_with_client()`，POST `/chat/completions`；解析 `choices[0].message.content` 为 JSON dict，不符合则抛 provider response error。见 `openai_compatible.py:127`, `:141`, `:739` [GITHUB_CODE]。
- Question parser/validation：LLM payload 经 `_parse_llm_question_payload()` 检查 envelope、字段、unsafe text marker；失败返回 `succeeded=False`。见 `question_generation_service.py:606` [GITHUB_CODE]。
- Question 无 transport 时当前会生成 deterministic degraded question，并返回 `succeeded=True`、`provider_status=not_configured`、`fallback_visible=True`。见 `question_generation_service.py:230` [GITHUB_CODE]。planned workflow 会把 `not_configured`、`fake_transport`、`failed`、`not_called`、deterministic/fake mode 收为 non-success reasons。见 `planned_workflow.py:435` [GITHUB_CODE]。
- Feedback 无 transport 当前 fail closed：`succeeded=False`, `validation_errors=("llm_transport_unavailable",)`, `llm_called=False`。见 `feedback_generation_service.py:88` [GITHUB_CODE]。
- Feedback provider exception / invalid envelope / validation error 均返回 failed，不持久化 generated feedback。API runtime 测试覆盖 provider unavailable 和 timeout 为 `generation_failed`、`retryable=True`。见 `feedback_generation_service.py:101`, `use_cases.py:1044`, `tests/api/test_polish_feedback_runtime.py:493`, `:541` [GITHUB_CODE]。
- `FailClosedPersistedLlmTransport` 在 trace/persisted runtime 前会调用 `contains_sensitive_payload(request.evidence_bundle)`，命中敏感内容则 provider invocation 前失败。见 `infrastructure/ai_runtime/llm_trace/persisted_transport.py:31` [GITHUB_CODE]。

## 4. Forbidden-Key Leakage Risks

- `LlmTransportRequest` 无自带 forbidden-key 校验，任何调用方只要构造 DTO 就能携带敏感 key。风险位置：`apps/api/app/application/llm/types.py:9` [GITHUB_CODE]。
- `OpenAICompatibleLlmTransport._chat_completion_payload()` 发送 `evidence_bundle` 前未见递归 forbidden-key rejection；当前依赖上游 builder。风险位置：`openai_compatible.py:417` [GITHUB_CODE]。
- Question builder 有 credential-like value redaction，但不是 P7 完整 forbidden-key catalog 的递归拒绝；例如 nested key `developer_prompt` / `full_asset_body` 没有在 builder 出口统一 fail closed。风险位置：`question_generation_prompts.py:632`, `:962` [GITHUB_CODE]。
- Feedback `_provider_prompt()` 若缺少 dict 类型 `provider_prompt`，会 fallback 返回完整 `prompt_asset`，这是 full prompt asset fallback 的直接风险。见 `feedback_agent.py:183` [GITHUB_CODE]。
- Feedback `_get_clean_text()` 只压缩和截断文本，未对 `api_key`, `token`, `secret`, `cookie` 等值做 redaction；`_safe_value()` 虽有递归 key 移除逻辑，但当前搜索未发现实际调用点。见 `feedback_prompt_assets.py:951` [GITHUB_CODE]。
- AI runtime sanitizer 的 `_SENSITIVE_KEYS` 缺少 `developer_prompt` 和 `full_asset_body`；现有架构测试把这两个 key 标记为 strict xfail known gap。见 `application/ai_runtime/contracts.py:33`, `tests/architecture/test_provider_boundary_static.py:45` [GITHUB_CODE]。
- `AgentOutputEnvelope` metadata unsafe key 集合只包含 `provider_payload`, `raw_completion`, `system_prompt`, `token`, `secret`，缺少 `raw_prompt`, `developer_prompt`, `raw_provider_payload`, `full_resume`, `full_jd`, `full_answer`, `full_asset_body`, `api_key`, `cookie`，且只过滤 metadata 顶层 key。见 `application/llm/agent_io.py:38` [GITHUB_CODE]。
- `feedback` planned workflow 的 `_safe_generation_metadata()` 以 key substring 过滤 `prompt/completion/payload/token/secret`，未覆盖 `api_key`, `cookie`, `full_resume`, `full_jd`, `full_answer`, `full_asset_body`。见 `feedback/planned_workflow.py:218` [GITHUB_CODE]。
- `_maybe_dump_local_raw_llm_io()` 在显式启用本地 raw IO 时会写入 `chat_completion_payload`, `response`, `parsed_result` 等 raw 内容到 `.local/llm-raw`。这是 debug/local 持久化风险，不等同默认 trace，但属于 P7 需要明确封口的边界。见 `openai_compatible.py:497` [GITHUB_CODE]。

## 5. Full Prompt / Full Asset Fallback Risks

- Feedback 存在明确 full asset fallback：`_provider_prompt()` 在 `provider_prompt` 缺失或非 dict 时返回完整 `prompt_asset`。见 `feedback_agent.py:183` [GITHUB_CODE]。
- Question 当前 provider path 未见 full prompt asset fallback；测试覆盖 provider request 不包含 `input_data`, `input_contract`, prompt body。见 `tests/api/test_polish_question_refactor_phase1.py:1040` [GITHUB_CODE]。
- Feedback compact prompt 仍包含 `prompt` 和 `output_schema` 字段；当前它们是 compact provider prompt 的静态任务说明/输出约束，不是完整 `AgentPromptBundle`，但 P7 builder 需要显式允许或改名，避免与 `raw_prompt/system_prompt/developer_prompt` 混淆。见 `feedback_prompt_assets.py:237` [GITHUB_CODE]。
- Feedback `current_answer.answer_text` 最大 1200 字；若用户答案短于限制，实际可能等于 full answer。P7 是否允许 bounded answer excerpt 需要控制器明确；当前无法证明 “no full answer fallback” 已满足。见 `feedback_prompt_assets.py:301` [UNKNOWN/GITHUB_CODE]。
- Question 无 transport 时 deterministic degraded generation 返回成功 draft；这不是 full prompt fallback，但属于 provider unavailable 被包装成 generated success 的 active-path 风险。见 `question_generation_service.py:230` [GITHUB_CODE]。

## 6. Recommended Compact Boundary Insertion Points

- 首选共享边界：在 `apps/api/app/application/llm/` 增加 `CompactProviderRequest` / `ProviderBoundaryValidator` 等等价模块，作为 `LlmTransportRequest.evidence_bundle` 的唯一入口；若后续决定引入 `application/ai_provider/**`，需注意当前目录不存在。 [INFERENCE]
- Transport 前 fail-closed：在 `OpenAICompatibleLlmTransport.generate()` 或 `_chat_completion_payload()` 前对 `request.evidence_bundle` 做 schema-bound + recursive forbidden-key rejection，确保任何上游遗漏都不会触达 provider。 [INFERENCE]
- Question builder 出口：`build_question_provider_request()` 返回前或 `_generate_llm_question()` 构造 `LlmTransportRequest` 前调用共享 validator，并把 forbidden hit 转成 `llm_validation_failed` / generation failed。 [INFERENCE]
- Feedback builder 出口：替换 `_provider_prompt()` 的 full prompt fallback；缺失 `provider_prompt` 应 fail closed，不应返回完整 `prompt_asset`。 [INFERENCE]
- Trace/persistence 对齐：扩展 `application.ai_runtime.contracts._SENSITIVE_KEYS` 与测试 catalog，覆盖 P7 checklist 全量 forbidden keys，移除 `developer_prompt` / `full_asset_body` xfail。 [INFERENCE]
- Metadata 出口：扩展 `AgentOutputEnvelope` 与 planned workflow metadata sanitizer，使用同一 forbidden-key catalog 递归处理，不保留散落 allow/deny 规则。 [INFERENCE]
- Local raw IO：若保留 `_maybe_dump_local_raw_llm_io()`，应限定为本地开发显式开关，并确保不能写 full provider payload、secret 或 raw completion；生产路径默认 fail closed。 [INFERENCE]

## 7. Tests/Gates to Add or Reuse

可复用：

- `tests/architecture/test_provider_boundary_static.py`：provider forbidden-key catalog 与 sanitizer 静态门；当前含 `developer_prompt` / `full_asset_body` known gap。 [GITHUB_CODE]
- `tests/api/test_fake_llm_boundary.py` 与 `tests/api/test_llm_runtime.py`：`LLM_PROVIDER=fake` runtime 禁用边界。 [GITHUB_CODE]
- `tests/api/test_polish_question_refactor_phase1.py`：question compact request、敏感值 redaction、无 full prompt fields、parse failure 不记录 raw output。 [GITHUB_CODE]
- `tests/api/test_polish_feedback_generation_service.py` 与 `test_polish_feedback_agent_io_alignment.py`：feedback compact provider prompt、无 transport fail closed、invalid payload fail closed、metadata unsafe key 过滤。 [GITHUB_CODE]
- `tests/api/test_pr8_polish_provider_trace_gate.py` 与 `test_sensitive_payload_redaction.py`：trace/persisted transport sensitive payload 阻断与 sanitizer。 [GITHUB_CODE]

建议新增或收紧：

- 全量 P7 forbidden-key catalog 的递归单测：dict/list/tuple 嵌套 key 与 string marker 都应 provider invocation 前失败。 [INFERENCE]
- Question/Feedback spy transport 测试：注入 nested forbidden key 后断言 `transport.generate()` 未被调用。 [INFERENCE]
- Feedback `provider_prompt` 缺失测试：断言 `_provider_prompt()` 不再 fallback full `prompt_asset`，而是 fail closed。 [INFERENCE]
- Feedback credential-like value redaction 测试：`answer_text/evidence/project asset` 中出现 `api_key=`, bearer token, cookie, secret 时不得进入 provider request。 [INFERENCE]
- Question no-transport/fake injection 测试：若 P7 口径要求 provider unavailable 不得 generated success，应把 deterministic degraded success 改为 fail/候选非成功并加门。 [INFERENCE]
- 移除 `developer_prompt` / `full_asset_body` xfail 前先补 sanitizer 与 architecture gate。 [INFERENCE]

## 8. Unknowns / Deferred Gaps

- 本次只读 recon 未运行测试；所有结论来自当前代码、当前测试文件、goal/source docs 的静态读取。 [UNKNOWN]
- 当前没有 `CompactProviderRequestBuilder` 命名实现；Question/Feedback 有分散的等价 compact builder，但尚未统一为共享边界。 [GITHUB_CODE]
- `application/ai_provider/**` 不存在；P7 实施应在现有 `application/llm` 下集中，还是新建 `application/ai_provider`，需要控制器决策。 [UNKNOWN]
- API 正常路径会注入 `llm_transport`，但 `PolishUseCases` 构造器仍允许缺省 `QuestionGenerationService`，该非 API active path 是否仍可触发 persisted generated fallback 未完全穷尽。 [UNKNOWN]
- Feedback `answer_text` 1200 字 bounded excerpt 是否满足 P7 “no full answer” 口径需要产品/控制器确认；当前不能证明完全满足。 [UNKNOWN]
- Direct OpenAI transport 与 persisted graph trace 的 fail-closed 程度不一致：persisted transport 有 `contains_sensitive_payload()`，direct OpenAI path 主要依赖上游 builder。 [GITHUB_CODE]
- 因 `developer_prompt` / `full_asset_body` sanitizer known gap 仍存在，P7 forbidden-key leakage 不能标记为 done。 [GITHUB_CODE]