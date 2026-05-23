---
title: LLM 请求/响应持久化与质量分析实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-llm-trace-persistence-plan
---

# LLM 请求/响应持久化与质量分析实施计划

## 1. 文档目的

本文规划 LLM 请求/响应 trace、payload capture、sanitization、retention、audit 和质量分析持久化。目标是在不泄露 raw prompt / raw completion / provider payload 的前提下，回答 contract、model、fallback、validation、low confidence 与质量问题。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- active docs：`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`prompt-contracts/*.md`

## 3. 当前状态

普通日志不足以支撑 LLM 质量分析：它无法稳定追踪 `contract_id`、`prompt_version`、`schema_id`、`configured_model`、`provider_model`、fallback reason、validation errors、low confidence flags、request/response hash 与 evidence hash。

普通日志也不能保存 raw prompt / raw completion：这些内容可能包含简历、JD、用户回答、第三方真实面试信息、系统提示词、provider payload 和安全敏感字段。

## 4. 目标输出

规划以下对象：

- `PersistedLlmTransport`
- `LlmTraceContext`
- `LlmPayloadCapturePolicy`
- `LlmPayloadSanitizer`
- `LlmCall`
- `LlmCallPayload`
- `LlmTraceRepository`
- `LlmTraceSummaryService`

## 5. 必须覆盖范围

### 5.1 Payload policy

| 策略项 | PR1 冻结值 | 说明 |
|---|---|---|
| sanitized payload | 默认开启 | API summary 只返回 sanitized summary |
| raw payload | 默认关闭 | 不进入日志、checkpoint、API response |
| raw feature flag | 必须显式开启 | PR1 不定义开关名，由 PR2/PR4 补齐 |
| encryption | raw 如开启必须加密 | feature flag 不足以单独放行 |
| retention | raw 如开启必须有过期时间 | 默认短保留、可审计删除 |
| audit | raw 如开启必须记录访问与启用原因 | 默认无 raw 访问 |
| API exposure | 永不暴露 raw | summary endpoint 只返回 hash、status、validation |

### 5.2 字段策略

| 字段 | 用途 | API 可见性 | 敏感性 |
|---|---|---|---|
| `request_hash` / `response_hash` | 排障和去重 | 可见 hash | 不含原文 |
| `evidence_hash` | 绑定 evidence refs | 可见 hash | 不含正文 |
| `provider_model` / `configured_model` | 追踪实际模型与配置模型差异 | 可见 | 低敏 |
| `prompt_version` / `schema_id` / `contract_ids` | contract 追踪 | 可见 | 低敏 |
| `fallback_reason` | 降级原因 | 可见 | 中敏 |
| `validation_errors` | schema/semantic validation | sanitized 可见 | 中敏 |
| `low_confidence_flags` | 质量风险 | 可见 | 中敏 |
| `raw_payload_ref` | raw 存储引用 | 默认空或不可见 | 高敏 |

### 5.3 方法级计划表

| File | Symbol | Kind | Action | Responsibility | Inputs | Outputs | Side Effects | Errors | Tests | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `application/llm/trace_context.py` | `LlmTraceContext` | dataclass | add | 携带 owner/run/node/contract 上下文 | refs | context | none | missing refs | unit | no raw |
| `infrastructure/llm/persisted_transport.py` | `PersistedLlmTransport.call` | method | add | 包装底层 transport 并持久化 summary | request + context | structured response | writes `llm_calls` | provider/validation | fake transport tests | raw-off |
| same | `capture_payload` | method | add | 按 policy 捕获 sanitized/raw | request/response | payload refs | writes payload rows | policy denied | policy tests | raw gated |
| `application/llm/payload_policy.py` | `LlmPayloadCapturePolicy.resolve` | method | add | 解析捕获策略 | config/context | policy | audit if raw | config error | unit | sanitized default |
| `application/llm/sanitizer.py` | `sanitize_llm_payload` | function | add | 生成脱敏摘要 | payload | sanitized summary | none | redaction failure | security tests | fail closed |
| `application/ai/trace/summary_service.py` | `get_llm_call_summary` | method | add | 返回 API sanitized summary | llm_call_id | summary response | read only | denied/not found | API tests | no raw |

### 5.4 API 策略

- `GET /api/v1/llm-calls/{llm_call_id}/summary` 只返回 sanitized summary。
- response 不包含 raw prompt、raw completion、provider payload、checkpoint payload、hidden scoring rules。
- owner enforcement 必须先于 summary 读取。

## 6. 与 active docs 的关系

本文承接 `SECURITY_PRIVACY.md` 的 LLM trace、日志脱敏、retention、audit 和 raw payload 禁止暴露规则；承接 `PROMPT_SPEC.md` 的 contract/schema/validation/low confidence 规则；承接 `PERSISTENCE_MODEL.md` 的 trace/audit 不替代业务事实源规则。

## 7. 非目标

- 不改 prompt 文案。
- 不选择 provider。
- 不实现 KMS。
- 不实现完整 SIEM。
- 不向前端暴露 raw payload。
- 不用 trace payload 替代业务结构化结果。

## 8. 后续 PR 使用方式

- PR2：落 `llm_calls` / `llm_call_payloads` 表、repository、migration/rollback、raw-off tests。
- PR3：在 facade/runner command 中传播 `LlmTraceContext`。
- PR4：在 LangGraph adapter 与 transport 中接入 `PersistedLlmTransport`、sanitizer 和 trace bridge。

## 9. Definition of Done

- sanitized 默认开启，raw 默认关闭。
- 日志、API、checkpoint 不含 raw prompt/completion/provider payload。
- model、contract、schema、hash、fallback、validation、low confidence 可追踪。
- raw 如开启必须同时具备 feature flag、加密、retention、audit 和访问控制。

