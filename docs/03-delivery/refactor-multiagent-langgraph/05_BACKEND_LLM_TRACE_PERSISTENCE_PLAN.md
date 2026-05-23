---
title: LLM 请求/响应持久化与质量分析实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-llm-trace-persistence-plan
---

# LLM 请求/响应持久化与质量分析实施计划

## 1. 文档目的

本文冻结 LLM trace、payload capture、sanitization、hash、retention、access audit 和 summary API 可见性。目标是在不泄露 raw prompt、raw completion、provider payload、system prompt、token、cookie、secret、无权限正文的前提下，稳定回答 contract、model、fallback、validation、low confidence、usage、replay 和质量问题。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- `10_DATA_MODEL_AND_MIGRATION_PLAN.md`
- active docs：`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`prompt-contracts/*.md`
- 当前代码映射：`LlmTransportRequest` 只承载 `contract_ids`、`task_type`、`input_refs`、`evidence_bundle`；`LlmTransportResult` 只承载结构化 `result`、validation、confidence、trace/evidence refs；`OpenAICompatibleLlmTransport` 已明确不记录 prompt、completion 或 provider payload；fake transport 已覆盖 raw leak marker。

## 3. 当前状态

普通日志不足以支撑 LLM 质量分析：它无法稳定追踪 `contract_ids`、`prompt_version`、`schema_id`、`configured_model`、`provider_model`、fallback reason、validation errors、low confidence flags、request/response hash、usage token 与 evidence hash。

普通日志也不能保存 raw prompt / raw completion：这些内容可能包含简历、JD、用户回答、第三方真实面试信息、系统提示词、provider payload 和安全敏感字段。

## 4. 目标输出

| Object / Symbol | File | Responsibility |
|---|---|---|
| `LlmTraceContext` | `apps/api/app/application/llm/trace_context.py` | 携带 owner、actor、ai task、agent run、node、contract、schema、prompt、replay mode 上下文；不携带 raw payload。 |
| `LlmPayloadCapturePolicy` | `apps/api/app/application/llm/payload_policy.py` | 解析 sanitized/raw 捕获策略、retention、feature flag、audit 要求和 fail-closed 行为。 |
| `LlmPayloadSanitizer` / `sanitize_llm_payload` | `apps/api/app/application/llm/sanitizer.py` | 递归执行 key + value redaction，生成 sanitized summary 和 hashes。 |
| `PersistedLlmTransport` | `apps/api/app/infrastructure/llm/persisted_transport.py` | 包装 `LlmTransport`，在调用前后写 `llm_calls` / `llm_call_payloads` sanitized summary。 |
| `LlmCallRepository` | `apps/api/app/infrastructure/db/repositories/llm_trace.py` | 写入 call lifecycle、hash、model、usage、validation、fallback、low confidence 和 replay reuse。 |
| `LlmTraceSummaryService` | `apps/api/app/application/ai/trace/summary_service.py` | owner scoped 读取 sanitized summary；禁止 raw payload 读取。 |

## 5. Trace context

`LlmTraceContext` 必须由 AI Orchestration Facade / Agent Runner 构造并传入 `PersistedLlmTransport`，不得由前端或 graph node 自行拼 owner。

| Field | Type | Required | Source | API Visible | Notes |
|---|---|---|---|---|---|
| `owner_id` | `str` | yes | auth / Core UseCase | no | 所有 trace 写入和读取的 owner scope。 |
| `actor_id` | `str | None` | yes | auth / system actor | no | 用户动作、resume、system task 都要可审计。 |
| `ai_task_id` | `str` | yes | `AiTask` | yes | 连接 API task status。 |
| `agent_run_id` | `str | None` | conditional | `agent_runs.id` | yes | legacy direct call 可为空；LangGraph call 必填。 |
| `agent_node_run_id` | `str | None` | conditional | `agent_node_runs.id` | yes | node timeline link。 |
| `graph_name` / `node_name` | `str | None` | conditional | graph registry | yes | 只允许 public-safe registry name。 |
| `contract_ids` | `tuple[str, ...]` | yes | `PROMPT_SPEC.md` registry | yes | 不允许 graph node 自造未登记 contract id。 |
| `prompt_version` / `schema_id` | `str | None` | yes | prompt bundle / output schema | yes | 用于质量分析和 replay compatibility。 |
| `replay_mode` | enum | yes | runner | yes sanitized | `production_resume / debug_replay / normal`。 |
| `source_refs` / `evidence_refs` | `tuple[str, ...]` | yes | Core query service | sanitized refs | refs only；不包含来源正文。 |
| `request_id` / `trace_id` | `str` | yes | API envelope | yes | 与 `api_request_traces` 关联。 |

## 6. Payload capture policy

| 策略项 | 冻结值 | 说明 |
|---|---|---|
| sanitized payload | 默认开启 | 记录 `payload_summary_json`、hash、schema、usage、validation、fallback、low confidence；API summary 只读 sanitized summary。 |
| raw payload | 默认关闭 | 不进入日志、checkpoint、API response、ordinary trace、payload summary。 |
| raw feature flag | PR2 固定为 `AIFI_LLM_DEBUG_RAW_PAYLOAD_ENABLED` | 默认 false；生产环境必须 false，debug 环境开启也不能绕过 encryption / TTL / audit。 |
| encryption | raw 如开启必须加密 | 只允许保存 `raw_payload_ciphertext_ref` 与 `encryption_key_ref`，不得把密钥或明文写入 DB。 |
| TTL | raw 如开启必须短 TTL | PR2 固定 raw TTL 上限为 24h；到期删除 encrypted raw object ref 并写 cleanup audit。 |
| audit | raw 如开启必须记录启用和访问 | `AuditEvent.event_type=llm_raw_payload_debug_enabled / llm_raw_payload_accessed / llm_raw_payload_expired`；访问必须说明 reason code。 |
| owner enforcement | 必须 | raw debug access 和 sanitized summary 均先校验 `owner_id`。 |
| fail closed | 必须 | sanitizer 失败、policy 配置冲突、raw gate 不完整时，LLM call 标记 failed，不写 raw，不返回 completion。 |
| API exposure | raw 永不暴露 | summary endpoint 不返回 raw ref、raw body、provider body、system prompt 或 completion text。 |

## 7. Sanitized payload allow / deny matrix

| Payload area | Sanitized payload 允许项 | Raw payload 禁止项 | Summary API 可见性 | Notes |
|---|---|---|---|---|
| Prompt bundle | `contract_ids`、`prompt_version`、`schema_id`、`task_type`、`input_ref_count`、`source_ref_count`、`evidence_hash`、`prompt_bundle_hash` | system prompt 原文、Prompt 模板全文、user message 正文、evidence bundle 原文、简历/JD/回答正文 | hash + counts + ids | `prompt_bundle_summary_json` 只能是摘要。 |
| Request metadata | `configured_model`、temperature、timeout、provider base host、request hash | API key、Authorization header、full provider request body、provider-specific raw payload | selected fields | host 不含 path query secret。 |
| Completion JSON | top-level schema id、contract result refs、validation status、low confidence flags、response hash、field presence map | raw completion text、provider message content、未校验 JSON body、模型自报的任意敏感字段 | sanitized validation/result summary | 结构化业务结果另写 Core tables / AiTaskResult。 |
| Provider response metadata | `provider_model`、provider response id hash、finish reason、status code、latency | provider full response body、choices message content、error body raw text | model/status/hash only | `provider_model` 只能来自 provider 外层 metadata 或本地配置。 |
| Provider error | error category、HTTP status、retryable、rate limited、timeout、provider unavailable | provider error body、request body、response body、stack with payload | sanitized category | 错误摘要不得复原用户正文。 |
| Usage token | prompt/completion/total token counts、estimated cost bucket | token content、prompt text、completion text | visible counts | usage 属低敏运营元数据。 |
| Validation | failed field path、rule id、contract id、low confidence category | invalid raw value、completion excerpt、source body excerpt | sanitized | value redaction 必须递归。 |
| Replay | replay mode、reused `llm_call_id`、hash match/mismatch、fail-closed reason | replay raw output、checkpoint state payload | sanitized | Production resume 不重新调用 provider。 |
| Debug raw | none by default | raw prompt、raw completion、provider payload | never | 仅 feature flag + encryption + TTL + audit 时保存 encrypted ref。 |

## 8. Sanitizer contract

`sanitize_llm_payload(payload, context, policy)` 必须满足：

1. 递归扫描 dict key、list item、string value；命中 deny key 或 deny pattern 时替换为 `"[REDACTED:<category>]"`。
2. deny key 至少包含：`raw_prompt`、`prompt`、`system_prompt`、`developer_message`、`messages`、`completion`、`raw_completion`、`provider_payload`、`provider_request`、`provider_response`、`api_key`、`authorization`、`token`、`cookie`、`secret`、`password`、`full_resume`、`full_jd`、`request_body`、`response_body`。
3. deny value pattern 至少覆盖：`RAW_PROMPT`、`provider_payload`、`system prompt`、`Bearer `、`sk-`、cookie-like header、DSN-like string、邮箱/手机号等 PII 摘要化规则。
4. 对允许保留的 structured result 只保存 schema presence map、field count、contract ids、trace/evidence refs、hash；不保存完整正文。
5. sanitizer 失败时返回 policy error，`PersistedLlmTransport` 标记 `llm_calls.status=failed`，不调用 raw capture fallback。

## 9. Hash strategy

| Hash | Input | Algorithm | Salt / version | Storage | Purpose |
|---|---|---|---|---|---|
| `request_hash` | canonical sanitized request summary | SHA-256 | `llm-trace-v1` + deployment salt ref | `llm_calls.request_hash` | 去重、排障、replay compatibility。 |
| `response_hash` | canonical sanitized response summary | SHA-256 | `llm-trace-v1` + deployment salt ref | `llm_calls.response_hash` | 结果一致性、resume reuse。 |
| `evidence_hash` | sorted `EvidenceRef` ids + source version refs + content digest refs | SHA-256 | `evidence-v1` | `llm_calls.evidence_hash` | 防止来源变更后误复用。 |
| `prompt_bundle_hash` | contract ids + prompt version + schema id + input ref ids + policy version | SHA-256 | `prompt-bundle-v1` | payload summary | 不保存 prompt body 也能判断兼容性。 |
| `payload_hash` | sanitized payload summary or encrypted raw blob digest | SHA-256 | `payload-v1` | `llm_call_payloads.payload_hash` | audit、cleanup、tamper check。 |

Hash 不能作为授权依据；它只用于一致性、排障和 replay compatibility。任何 hash mismatch 在 production resume 中都必须 fail closed。

## 10. PersistedLlmTransport contract

| Step | Behavior | Failure |
|---|---|---|
| `create_planned_call` | 在调用 provider 前写 `llm_calls(status=planned)`，记录 context、contract、model、prompt/schema、request hash。 | 无 owner / context 缺失时拒绝调用 provider。 |
| `mark_running` | provider 调用开始前标记 running。 | DB 写失败时不调用 provider，返回 generation failed。 |
| provider call | 调用底层 `LlmTransport.generate(request)`；不记录 raw request/response 到日志。 | timeout/rate limit/provider error 写 sanitized `error_summary_json`。 |
| sanitize result | 对 `LlmTransportResult.result` 与 provider metadata 摘要执行 sanitizer。 | sanitizer 失败时 fail closed，不写 raw。 |
| capture payload | 默认写 sanitized `llm_call_payloads(payload_kind=request_summary/response_summary/error_summary)`。 | policy denied 时只保留 `llm_calls` failure summary。 |
| mark final | 成功写 `status=succeeded`、hash、usage、validation、low confidence、provider_model。 | validation failed 写 `status=validation_failed`，不写 formal object。 |
| replay reuse | production resume 复用已有 `llm_call_id`，写 `status=replay_reused` 或返回 existing summary。 | 缺 summary/hash mismatch 时 `replay_blocked`。 |

## 11. API summary visibility

`GET /api/v1/llm-calls/{llm_call_id}/summary` 只允许返回：

- `llm_call_id`
- `ai_task_id`
- `agent_run_id`
- `agent_node_run_id`
- `status`
- `contract_ids`
- `prompt_version`
- `schema_id`
- `configured_model`
- `provider_model`
- `usage`
- `request_hash`
- `response_hash`
- `evidence_hash`
- `fallback_reason`
- `validation_summary`
- `low_confidence_flags`
- `error_category`
- `started_at`
- `completed_at`
- `trace_ref_ids`
- `evidence_ref_ids`

禁止返回：

- raw prompt
- raw completion
- provider payload
- provider error body
- system prompt
- Prompt 模板全文
- request / response body
- source正文
- hidden scoring rules
- token、cookie、secret、API key、DSN
- `raw_payload_ciphertext_ref`
- `encryption_key_ref`

## 12. Retention cleanup 与 access audit

| Flow | Trigger | Action | Audit |
|---|---|---|---|
| sanitized trace cleanup | trace retention 到期 | 删除或压缩 `payload_summary_json`，保留 `llm_calls` 最小 status/hash/model/usage summary | `llm_trace_cleanup_completed` |
| raw debug TTL cleanup | `retention_expires_at <= now` | 删除 encrypted raw object ref，清空 `raw_payload_ciphertext_ref`，状态改 `expired` | `llm_raw_payload_expired` |
| raw debug access | 人工批准 + owner/scope 校验 + reason code | 只在 debug admin/service path 解密，业务 API 不可用 | `llm_raw_payload_accessed` |
| policy violation | sanitizer / policy 发现 raw 泄露 | 阻断 API summary，标记 `llm_calls.status=failed` 或 `validation_failed` | `llm_payload_policy_violation` |
| owner mismatch | summary 或 raw access owner 不匹配 | deny，不透露资源存在性 | `llm_trace_access_denied` |

## 13. Replay / resume 策略

- Production resume 默认复用旧 `llm_calls` sanitized result summary、hash 和已写 Core Business result refs；不重新调用 provider。
- Production resume 如果缺少 sanitized summary、hash mismatch、prompt/schema/model incompatible、source version changed、checkpoint ref expired 或 validation failed，必须 fail closed；不得用新 provider call 填补缺口。
- Debug replay 不写业务表；可复用 fake transport 或旧 sanitized result 构造 debug timeline；真实 provider debug replay 需要单独人工批准、raw-off scan、feature flag 和 audit。
- `llm_calls.status=replay_reused` 表示复用旧 sanitized result；`replay_blocked` 表示缺证据或不兼容；两者都不是新的业务结果。

## 14. 方法级计划表

| File | Symbol | Kind | Action | Responsibility | Inputs | Outputs | Side Effects | Errors | Tests | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `application/llm/trace_context.py` | `LlmTraceContext` | dataclass | add | 携带 owner/run/node/contract/replay 上下文 | refs | context | none | missing owner/context | unit | no raw |
| `application/llm/payload_policy.py` | `LlmPayloadCapturePolicy.resolve` | method | add | 解析 sanitized/raw/TTL/audit 策略 | config/context | policy | audit if raw enabled | config conflict | unit | sanitized default |
| `application/llm/sanitizer.py` | `sanitize_llm_payload` | function | add | 递归 key + value redaction，生成 summary/hash input | payload/context/policy | sanitized summary | none | redaction failure | security tests | fail closed |
| `infrastructure/llm/persisted_transport.py` | `PersistedLlmTransport.generate` | method | add | 包装底层 transport 并持久化 call lifecycle | request + context | structured response | writes `llm_calls` | provider/validation/db write | fake transport tests | raw-off |
| same | `capture_payload` | method | add | 按 policy 捕获 sanitized/debug raw ref | request/response/error | payload refs | writes payload rows | policy denied | policy tests | raw gated |
| `application/ai/trace/summary_service.py` | `get_llm_call_summary` | method | add | 返回 owner scoped API sanitized summary | owner + llm_call_id | summary response | read only + audit denied | denied/not found | API tests | no raw |

## 15. 与 active docs 的关系

本文承接 `SECURITY_PRIVACY.md` 的 LLM trace、日志脱敏、retention、audit、raw payload 禁止暴露规则；承接 `PROMPT_SPEC.md` 的 contract/schema/validation/low confidence 规则；承接 `PERSISTENCE_MODEL.md` 的 trace/audit 不替代业务事实源规则；承接 `APPLICATION_FLOW_SPEC.md` 的 LLM 调用与持久化 handoff。

## 16. 非目标

- 不改 prompt 文案。
- 不选择 provider。
- 不实现 KMS。
- 不实现完整 SIEM。
- 不向前端暴露 raw payload。
- 不用 trace payload 替代业务结构化结果。
- 不让 debug replay 写业务表。

## 17. PR 使用方式

| PR | Scope |
|---|---|
| PR2 | 落 `llm_calls` / `llm_call_payloads` 表、repository、schema bootstrap、raw-off tests、payload policy constants。 |
| PR3 | 在 facade/runner command 中传播 `LlmTraceContext`，保持 Core UseCase 不依赖 LangGraph。 |
| PR4 | 在 LangGraph adapter 与 transport 中接入 `PersistedLlmTransport`、sanitizer、trace bridge、production resume reuse。 |

## 18. Definition of Done

- sanitized 默认开启，raw 默认关闭。
- 日志、API、checkpoint 不含 raw prompt、raw completion、provider payload、system prompt、token、cookie、secret。
- model、contract、schema、hash、fallback、validation、low confidence、usage token 可追踪。
- raw 如开启必须同时具备 feature flag、encryption、TTL、audit、owner access control，且 raw 永不进入业务 API。
- Production resume 复用旧 sanitized result 或 fail closed，不重新调用 provider；debug replay 不写业务表。
