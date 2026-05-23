---
title: 数据模型与迁移实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/data-model-and-migration-plan
---

# 数据模型与迁移实施计划

## 1. 文档目的

本文冻结 LangGraph MultiAgent 重构的数据模型、迁移顺序、replay / resume / side-effect idempotency 和验证边界。它只规划 AI Runtime Tables，不改写 `DATA_MODEL.md`、`PERSISTENCE_MODEL.md` 中的 Core Business truth source。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`
- 当前代码映射：`OwnedRecordMixin` 已提供 `id`、`owner_id`、`actor_id`、`record_version`、`status`、`created_at`、`updated_at`、`trace_ref_ids`、`evidence_ref_ids`；业务表已使用 `*_json` / `*_ids` 命名；`AiTask` / `AiTaskResult` 已存在；当前仓库没有 Alembic 目录，本地 schema 初始化由 `Base.metadata.create_all()` 与启动 backfill 路径承接。
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- `05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md`

## 3. 当前状态

当前 active docs 已冻结 owner、version、status、trace、evidence、candidate / suggestion / confirmation、raw payload 默认不保存、checkpoint 不作为业务事实源等规则。当前代码已有 `ai_tasks`、`ai_task_results`、`trace_refs`、`audit_events`、`questions`、`feedback`、`reports`、`reviews`、`assets`、`weaknesses`、`training_*` 等模型，但缺 `agent_runs`、`agent_node_runs`、`agent_interrupts`、`agent_checkpoint_refs`、`llm_calls`、`llm_call_payloads` 的字段级冻结。

## 4. 总体建模规则

| 项 | 冻结规则 |
|---|---|
| 表类别 | `agent_runs`、`agent_node_runs`、`agent_interrupts`、`agent_checkpoint_refs`、`llm_calls`、`llm_call_payloads` 均属于 AI Runtime Tables；不属于 Core Business Tables，不替代 `questions`、`feedback`、`reports`、`reviews`、`weaknesses`、`assets`、`training_*`。 |
| mixin | 六张表默认使用 `OwnedRecordMixin`，继承 `id`、`owner_id`、`actor_id`、`record_version`、`status`、`created_at`、`updated_at`、`trace_ref_ids`、`evidence_ref_ids`。如 PR2 因 SQLAlchemy 约束拆分 mixin，必须保留同名字段与语义。 |
| 主键列名 | ORM 列名统一使用 `id`，与现有 `OwnedRecordMixin` 一致；API / repository 可暴露 `agent_run_id`、`agent_node_run_id`、`llm_call_id` 等别名，但不得新增第二个主键列。 |
| ID prefix | `agent_runs.id=arun_*`、`agent_node_runs.id=anode_*`、`agent_interrupts.id=aint_*`、`agent_checkpoint_refs.id=chkref_*`、`llm_calls.id=llmcall_*`、`llm_call_payloads.id=llmpay_*`。 |
| JSON 命名 | 结构化 JSON 列统一使用 `*_json`；ID 列表沿用现有 mixin 的 `trace_ref_ids`、`evidence_ref_ids`；不得使用不可校验的逗号字符串保存列表。 |
| status enum | `agent_runs.status`：`queued / running / interrupted / succeeded / failed / cancelled / timed_out / replayed_debug`；`agent_node_runs.status`：`pending / running / interrupted / succeeded / failed / skipped / replayed_debug`；`agent_interrupts.status`：`open / resumed / cancelled / expired / failed`；`agent_checkpoint_refs.status`：`created / superseded / expired / restore_failed`；`llm_calls.status`：`planned / running / succeeded / failed / validation_failed / replay_reused / replay_blocked`；`llm_call_payloads.status`：`captured / redacted / expired / access_denied / deleted`. |
| owner scope | 所有查询、resume、replay、timeline、summary、cleanup 均必须带 `owner_id`；`actor_id` 记录触发者；请求体 `owner_id` 不作为授权依据。 |
| checkpoint truth source | LangGraph checkpoint 只用于 runtime recovery、resume、time travel 和 debug replay；业务 API 读取 `questions`、`feedback`、`reports` 等 Core Business Tables；不得从 checkpoint payload 派生业务事实。 |
| raw payload | 普通 runtime 表不保存 raw prompt、raw completion、provider payload、system prompt、token、cookie、secret 或 request / response body。 |

## 5. 三类表边界

| Category | Tables | Truth Source | API 可见性 | Retention / Security |
|---|---|---|---|---|
| Core Business Tables | resumes, jobs, bindings, sessions, questions, answers, feedback, scores, reports, reviews, weaknesses, assets, training | 业务事实源 | 业务 API 返回结构化结果 | owner、version、trace、evidence、audit |
| AI Runtime Tables | `ai_tasks`, `ai_task_results`, `agent_runs`, `agent_node_runs`, `agent_interrupts`, `llm_calls`, `llm_call_payloads`, `agent_checkpoint_refs` | AI 运行事实 | Agent Runtime API 只返回 sanitized summary / timeline / refs | raw-off、retention、audit、owner scoped |
| LangGraph Checkpoint Tables | checkpointer-managed tables | runtime recovery only | 不直接暴露 | checkpoint payload 不作为业务事实；只通过 `agent_checkpoint_refs` 暴露引用摘要 |

## 6. 字段级定义

字段表头固定为：`Table / Column / SQLAlchemy Type / Nullable / Default / Index / Unique / Logical Ref / Source / Sensitivity / API Visible / Owner Scope / Retention / Notes`。

### 6.1 `agent_runs`

| Table | Column | SQLAlchemy Type | Nullable | Default | Index | Unique | Logical Ref | Source | Sensitivity | API Visible | Owner Scope | Retention | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `agent_runs` | `id` | `String(80)` | no | generated `arun_*` | pk | yes | `AgentRunRef` | facade | low | yes as `agent_run_id` | owner scoped | runtime retention | Primary key from `OwnedRecordMixin`. |
| `agent_runs` | `owner_id` | `String(80)` | no | none | yes | no | `OwnerRef` | auth | sensitive | no | owner scoped | runtime retention | Required in every repository query. |
| `agent_runs` | `actor_id` | `String(80)` | yes | current actor | yes | no | `ActorRef` | auth | sensitive | no | owner scoped | runtime retention | System resume may use service actor summary. |
| `agent_runs` | `record_version` | `Integer` | no | `1` | no | no | optimistic lock | db | low | no | owner scoped | runtime retention | Prevent stale resume updates. |
| `agent_runs` | `status` | `String(64)` | no | `queued` | yes | no | run status | runner | low | yes | owner scoped | runtime retention | Enum in §4. |
| `agent_runs` | `created_at` / `updated_at` | `DateTime(timezone=True)` | no | `utc_now` | yes | no | timestamps | db | low | yes | owner scoped | runtime retention | Timeline sorting uses these columns. |
| `agent_runs` | `trace_ref_ids` / `evidence_ref_ids` | `JSON` | yes | `NULL` | no | no | `TraceRef[]` / `EvidenceRef[]` | facade | medium | sanitized refs only | owner scoped | runtime retention | No prompt or provider payload. |
| `agent_runs` | `ai_task_id` | `String(80)` | no | none | yes | no | `AiTask` | facade | low | yes | owner scoped | runtime retention | Links existing `ai_tasks.id`. |
| `agent_runs` | `graph_name` | `String(120)` | no | none | yes | no | graph registry id | runner | low | yes | owner scoped | runtime retention | Example: `polish_feedback_graph`. |
| `agent_runs` | `graph_version` | `String(64)` | no | registry version | yes | no | graph registry version | runner | low | yes | owner scoped | runtime retention | Required for replay compatibility. |
| `agent_runs` | `entrypoint_name` | `String(120)` | no | none | no | no | graph entrypoint | runner | low | yes | owner scoped | runtime retention | Does not expose internals beyond public timeline. |
| `agent_runs` | `thread_id` | `String(120)` | no | generated | yes | yes with owner | LangGraph thread | adapter | medium | ref only | owner scoped | checkpoint retention | `Unique(owner_id, thread_id)`. |
| `agent_runs` | `idempotency_key_hash` | `String(128)` | no | hash | yes | yes with owner/graph | idempotency | facade | medium | no | owner scoped | idempotency retention | Hash of actor/method/path/body key, not raw key. |
| `agent_runs` | `input_refs_json` | `JSON` | yes | `NULL` | no | no | typed input refs | facade | medium | sanitized summary | owner scoped | runtime retention | Source refs only, not full source body. |
| `agent_runs` | `output_refs_json` | `JSON` | yes | `NULL` | no | no | result refs | runner | medium | sanitized refs | owner scoped | runtime retention | Points to business tables or candidate refs. |
| `agent_runs` | `pending_writes_json` | `JSON` | yes | `NULL` | no | no | side-effect pending writes | side-effect wrapper | high | no | owner scoped | short runtime retention | Contains planned write refs and idempotency hashes, not payload bodies. |
| `agent_runs` | `error_summary_json` | `JSON` | yes | `NULL` | no | no | failure category | runner | medium | sanitized | owner scoped | runtime retention | No stack body, prompt, completion, provider payload. |
| `agent_runs` | `started_at` / `completed_at` / `interrupted_at` | `DateTime(timezone=True)` | yes | `NULL` | yes on `started_at` | no | lifecycle | runner | low | yes | owner scoped | runtime retention | Used for SLA and timeout cleanup. |

### 6.2 `agent_node_runs`

| Table | Column | SQLAlchemy Type | Nullable | Default | Index | Unique | Logical Ref | Source | Sensitivity | API Visible | Owner Scope | Retention | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `agent_node_runs` | `id` | `String(80)` | no | generated `anode_*` | pk | yes | `AgentNodeRunRef` | runner | low | yes | owner scoped | runtime retention | Primary key from `OwnedRecordMixin`. |
| `agent_node_runs` | `owner_id` / `actor_id` | `String(80)` | owner no / actor yes | inherited | yes | no | owner / actor | auth | sensitive | no | owner scoped | runtime retention | Same owner as parent run. |
| `agent_node_runs` | `record_version` | `Integer` | no | `1` | no | no | optimistic lock | db | low | no | owner scoped | runtime retention | Prevent double finalization. |
| `agent_node_runs` | `status` | `String(64)` | no | `pending` | yes | no | node status | runner | low | yes | owner scoped | runtime retention | Enum in §4. |
| `agent_node_runs` | `created_at` / `updated_at` | `DateTime(timezone=True)` | no | `utc_now` | yes | no | timestamps | db | low | yes | owner scoped | runtime retention | Timeline sorting. |
| `agent_node_runs` | `trace_ref_ids` / `evidence_ref_ids` | `JSON` | yes | `NULL` | no | no | trace/evidence refs | node | medium | sanitized refs | owner scoped | runtime retention | No checkpoint payload. |
| `agent_node_runs` | `agent_run_id` | `String(80)` | no | none | yes | no | `agent_runs.id` | runner | low | yes | owner scoped | runtime retention | Parent run. |
| `agent_node_runs` | `graph_name` | `String(120)` | no | none | yes | no | graph registry id | runner | low | yes | owner scoped | runtime retention | Denormalized for timeline filters. |
| `agent_node_runs` | `node_name` | `String(160)` | no | none | yes | no | node registry id | runner | low | yes | owner scoped | runtime retention | Public-safe node name only. |
| `agent_node_runs` | `node_version` | `String(64)` | no | registry version | no | no | node version | runner | low | yes | owner scoped | runtime retention | Required for replay compatibility. |
| `agent_node_runs` | `attempt_number` | `Integer` | no | `1` | yes | yes with run/node | retry attempt | runner | low | yes | owner scoped | runtime retention | `Unique(owner_id, agent_run_id, node_name, attempt_number)`. |
| `agent_node_runs` | `llm_call_ids_json` | `JSON` | yes | `NULL` | no | no | `LlmCallRef[]` | transport wrapper | medium | sanitized refs | owner scoped | trace retention | Ref list only. |
| `agent_node_runs` | `side_effect_keys_json` | `JSON` | yes | `NULL` | no | no | side-effect idempotency keys | side-effect wrapper | high | no | owner scoped | idempotency retention | Hashes only; used to block duplicate `persist_question` / `persist_feedback`. |
| `agent_node_runs` | `input_digest` / `output_digest` | `String(128)` | yes | `NULL` | yes | no | node hash | runner | medium | hash only | owner scoped | runtime retention | Canonical JSON SHA-256 digest; no body. |
| `agent_node_runs` | `validation_summary_json` | `JSON` | yes | `NULL` | no | no | validation result summary | validators | medium | sanitized | owner scoped | runtime retention | No full completion. |
| `agent_node_runs` | `started_at` / `completed_at` | `DateTime(timezone=True)` | yes | `NULL` | yes on `started_at` | no | lifecycle | runner | low | yes | owner scoped | runtime retention | Timeout and timeline. |

### 6.3 `agent_interrupts`

| Table | Column | SQLAlchemy Type | Nullable | Default | Index | Unique | Logical Ref | Source | Sensitivity | API Visible | Owner Scope | Retention | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `agent_interrupts` | `id` | `String(80)` | no | generated `aint_*` | pk | yes | `AgentInterruptRef` | runner | low | yes | owner scoped | runtime retention | Primary key from `OwnedRecordMixin`. |
| `agent_interrupts` | `owner_id` / `actor_id` | `String(80)` | owner no / actor yes | inherited | yes | no | owner / actor | auth | sensitive | no | owner scoped | runtime retention | Resume actor updates `actor_id` or audit. |
| `agent_interrupts` | `record_version` | `Integer` | no | `1` | no | no | optimistic lock | db | low | no | owner scoped | runtime retention | Prevent double resume. |
| `agent_interrupts` | `status` | `String(64)` | no | `open` | yes | no | interrupt status | runner | low | yes | owner scoped | runtime retention | Enum in §4. |
| `agent_interrupts` | `created_at` / `updated_at` | `DateTime(timezone=True)` | no | `utc_now` | yes | no | timestamps | db | low | yes | owner scoped | runtime retention | Timeline. |
| `agent_interrupts` | `agent_run_id` | `String(80)` | no | none | yes | no | `agent_runs.id` | runner | low | yes | owner scoped | runtime retention | Parent run. |
| `agent_interrupts` | `agent_node_run_id` | `String(80)` | no | none | yes | no | `agent_node_runs.id` | runner | low | yes | owner scoped | runtime retention | Node that requested human input. |
| `agent_interrupts` | `node_name` | `String(160)` | no | none | yes | no | node registry id | runner | low | yes | owner scoped | runtime retention | Public-safe node name. |
| `agent_interrupts` | `interrupt_type` | `String(80)` | no | none | yes | no | `human_confirmation / correction / target_selection` | node | low | yes | owner scoped | runtime retention | Maps to UI resume form. |
| `agent_interrupts` | `resume_schema_id` | `String(120)` | no | none | yes | no | resume schema | node | low | yes | owner scoped | runtime retention | API validates response shape. |
| `agent_interrupts` | `prompt_summary_json` | `JSON` | yes | `NULL` | no | no | user-visible prompt summary | node | medium | yes sanitized | owner scoped | runtime retention | No raw prompt or source body. |
| `agent_interrupts` | `resume_payload_summary_json` | `JSON` | yes | `NULL` | no | no | resume input summary | API | medium | sanitized | owner scoped | runtime retention | Raw resume form body not exposed. |
| `agent_interrupts` | `expires_at` / `resumed_at` | `DateTime(timezone=True)` | yes | `NULL` | yes | no | lifecycle | runner / API | low | yes | owner scoped | runtime retention | Expired interrupts cannot resume. |
| `agent_interrupts` | `idempotency_key_hash` | `String(128)` | yes | `NULL` | yes | yes with interrupt | resume idempotency | API | medium | no | owner scoped | idempotency retention | `Unique(owner_id, id, idempotency_key_hash)`. |

### 6.4 `agent_checkpoint_refs`

| Table | Column | SQLAlchemy Type | Nullable | Default | Index | Unique | Logical Ref | Source | Sensitivity | API Visible | Owner Scope | Retention | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `agent_checkpoint_refs` | `id` | `String(80)` | no | generated `chkref_*` | pk | yes | `AgentCheckpointRef` | adapter | medium | ref only | owner scoped | checkpoint retention | Reference row only; no checkpoint payload. |
| `agent_checkpoint_refs` | `owner_id` / `actor_id` | `String(80)` | owner no / actor yes | inherited | yes | no | owner / actor | auth | sensitive | no | owner scoped | checkpoint retention | Same owner as run. |
| `agent_checkpoint_refs` | `record_version` | `Integer` | no | `1` | no | no | optimistic lock | db | low | no | owner scoped | checkpoint retention | For cleanup state. |
| `agent_checkpoint_refs` | `status` | `String(64)` | no | `created` | yes | no | checkpoint ref status | adapter | low | ref only | owner scoped | checkpoint retention | Enum in §4. |
| `agent_checkpoint_refs` | `created_at` / `updated_at` | `DateTime(timezone=True)` | no | `utc_now` | yes | no | timestamps | db | low | ref only | owner scoped | checkpoint retention | Cleanup ordering. |
| `agent_checkpoint_refs` | `agent_run_id` | `String(80)` | no | none | yes | no | `agent_runs.id` | adapter | low | ref only | owner scoped | checkpoint retention | Parent run. |
| `agent_checkpoint_refs` | `agent_node_run_id` | `String(80)` | yes | `NULL` | yes | no | node checkpoint | adapter | low | ref only | owner scoped | checkpoint retention | Null only for run-level checkpoint. |
| `agent_checkpoint_refs` | `graph_name` | `String(120)` | no | none | yes | no | graph registry id | adapter | low | ref only | owner scoped | checkpoint retention | Not a business query key. |
| `agent_checkpoint_refs` | `node_name` | `String(160)` | yes | `NULL` | yes | no | node registry id | adapter | low | ref only | owner scoped | checkpoint retention | Null for graph checkpoint. |
| `agent_checkpoint_refs` | `checkpoint_namespace` | `String(160)` | no | none | yes | no | LangGraph namespace | adapter | medium | no | owner scoped | checkpoint retention | Internal namespace, not API body. |
| `agent_checkpoint_refs` | `thread_id` | `String(120)` | no | none | yes | no | LangGraph thread | adapter | medium | ref only | owner scoped | checkpoint retention | Must match `agent_runs.thread_id`. |
| `agent_checkpoint_refs` | `checkpoint_id` | `String(160)` | no | none | yes | yes with namespace/thread | LangGraph checkpoint | adapter | medium | ref only | owner scoped | checkpoint retention | `Unique(owner_id, checkpoint_namespace, thread_id, checkpoint_id)`. |
| `agent_checkpoint_refs` | `checkpoint_metadata_json` | `JSON` | yes | `NULL` | no | no | sanitized metadata | adapter | medium | ref only | owner scoped | checkpoint retention | Hashes, version, timestamps only; no state payload. |
| `agent_checkpoint_refs` | `retention_expires_at` | `DateTime(timezone=True)` | no | policy timestamp | yes | no | retention | policy | low | no | owner scoped | checkpoint retention | Cleanup deletes refs after checkpoint cleanup. |

### 6.5 `llm_calls`

| Table | Column | SQLAlchemy Type | Nullable | Default | Index | Unique | Logical Ref | Source | Sensitivity | API Visible | Owner Scope | Retention | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `llm_calls` | `id` | `String(80)` | no | generated `llmcall_*` | pk | yes | `LlmCallRef` | persisted transport | low | yes | owner scoped | trace retention | Primary key from `OwnedRecordMixin`. |
| `llm_calls` | `owner_id` / `actor_id` | `String(80)` | owner no / actor yes | inherited | yes | no | owner / actor | trace context | sensitive | no | owner scoped | trace retention | Owner required before capture. |
| `llm_calls` | `record_version` | `Integer` | no | `1` | no | no | optimistic lock | db | low | no | owner scoped | trace retention | Prevent double finalization. |
| `llm_calls` | `status` | `String(64)` | no | `planned` | yes | no | call status | transport | low | yes | owner scoped | trace retention | Enum in §4. |
| `llm_calls` | `created_at` / `updated_at` | `DateTime(timezone=True)` | no | `utc_now` | yes | no | timestamps | db | low | yes | owner scoped | trace retention | Timeline and cleanup. |
| `llm_calls` | `ai_task_id` | `String(80)` | no | none | yes | no | `AiTask` | trace context | low | yes | owner scoped | trace retention | Links task. |
| `llm_calls` | `agent_run_id` | `String(80)` | yes | `NULL` | yes | no | `agent_runs.id` | trace context | low | yes | owner scoped | trace retention | Null only for legacy direct LLM calls. |
| `llm_calls` | `agent_node_run_id` | `String(80)` | yes | `NULL` | yes | no | `agent_node_runs.id` | trace context | low | yes | owner scoped | trace retention | Node-level timeline link. |
| `llm_calls` | `graph_name` / `node_name` | `String(120/160)` | yes | `NULL` | yes | no | graph/node | trace context | low | yes | owner scoped | trace retention | Sanitized names. |
| `llm_calls` | `contract_ids_json` | `JSON` | no | `[]` | no | no | Prompt contract ids | request | low | yes | owner scoped | trace retention | Must come from canonical registry. |
| `llm_calls` | `configured_model` | `String(120)` | no | config model | yes | no | configured model | transport | low | yes | owner scoped | trace retention | From server config. |
| `llm_calls` | `provider_model` | `String(120)` | yes | `NULL` | yes | no | provider actual model | provider response metadata | low | yes | owner scoped | trace retention | Only provider metadata, not completion body. |
| `llm_calls` | `prompt_version` / `schema_id` | `String(120)` | yes | `NULL` | yes | no | prompt/schema | prompt registry | low | yes | owner scoped | trace retention | Visible for quality analysis. |
| `llm_calls` | `request_hash` / `response_hash` / `evidence_hash` | `String(128)` | yes | `NULL` | yes | no | content digest | sanitizer | medium | hash only | owner scoped | trace retention | Canonical SHA-256 with salt/version; no raw body. |
| `llm_calls` | `usage_json` | `JSON` | yes | `NULL` | no | no | token usage summary | provider metadata | low | yes | owner scoped | trace retention | prompt/completion/total tokens only; no text. |
| `llm_calls` | `fallback_reason` | `String(160)` | yes | `NULL` | yes | no | fallback category | transport/facade | medium | sanitized | owner scoped | trace retention | No provider body. |
| `llm_calls` | `validation_errors_json` | `JSON` | yes | `NULL` | no | no | validation summary | validators | medium | sanitized | owner scoped | trace retention | Field paths and categories only. |
| `llm_calls` | `low_confidence_flags_json` | `JSON` | yes | `NULL` | no | no | low confidence | validators | medium | yes | owner scoped | trace retention | User-visible categories allowed. |
| `llm_calls` | `error_summary_json` | `JSON` | yes | `NULL` | no | no | provider/error category | transport | medium | sanitized | owner scoped | trace retention | Provider error body is denied; category/status only. |
| `llm_calls` | `started_at` / `completed_at` | `DateTime(timezone=True)` | yes | `NULL` | yes on `started_at` | no | lifecycle | transport | low | yes | owner scoped | trace retention | Duration can be derived. |

### 6.6 `llm_call_payloads`

| Table | Column | SQLAlchemy Type | Nullable | Default | Index | Unique | Logical Ref | Source | Sensitivity | API Visible | Owner Scope | Retention | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `llm_call_payloads` | `id` | `String(80)` | no | generated `llmpay_*` | pk | yes | `LlmCallPayloadRef` | capture policy | high | no | owner scoped | payload retention | Primary key from `OwnedRecordMixin`. |
| `llm_call_payloads` | `owner_id` / `actor_id` | `String(80)` | owner no / actor yes | inherited | yes | no | owner / actor | trace context | sensitive | no | owner scoped | payload retention | Required for cleanup and audit. |
| `llm_call_payloads` | `record_version` | `Integer` | no | `1` | no | no | optimistic lock | db | low | no | owner scoped | payload retention | Cleanup updates status. |
| `llm_call_payloads` | `status` | `String(64)` | no | `captured` | yes | no | payload status | policy | high | no | owner scoped | payload retention | Enum in §4. |
| `llm_call_payloads` | `created_at` / `updated_at` | `DateTime(timezone=True)` | no | `utc_now` | yes | no | timestamps | db | low | no | owner scoped | payload retention | Cleanup ordering. |
| `llm_call_payloads` | `llm_call_id` | `String(80)` | no | none | yes | yes with kind | `llm_calls.id` | persisted transport | low | no | owner scoped | payload retention | `Unique(owner_id, llm_call_id, payload_kind)`. |
| `llm_call_payloads` | `payload_kind` | `String(80)` | no | none | yes | yes with call | `request_summary / response_summary / error_summary / debug_raw_ref` | policy | high | no | owner scoped | payload retention | Debug raw ref row only when raw gate passes. |
| `llm_call_payloads` | `capture_policy_version` | `String(80)` | no | policy version | yes | no | policy | policy | low | no | owner scoped | payload retention | Enables retention migration. |
| `llm_call_payloads` | `sanitized` | `Boolean` | no | `true` | yes | no | capture flag | sanitizer | low | no | owner scoped | payload retention | Raw rows have `sanitized=false` and require raw gate. |
| `llm_call_payloads` | `raw_enabled` | `Boolean` | no | `false` | yes | no | raw gate | policy | high | no | owner scoped | short raw TTL | Must be false in production default. |
| `llm_call_payloads` | `payload_summary_json` | `JSON` | yes | `NULL` | no | no | sanitized summary | sanitizer | medium | no | owner scoped | payload retention | Allowed fields only: hashes, field counts, schema ids, token usage, validation categories. |
| `llm_call_payloads` | `payload_hash` | `String(128)` | no | hash | yes | no | payload digest | sanitizer | medium | hash only through summary service | owner scoped | payload retention | Canonical SHA-256 digest of sanitized summary or encrypted raw blob. |
| `llm_call_payloads` | `raw_payload_ciphertext_ref` | `String(240)` | yes | `NULL` | no | no | encrypted raw object ref | raw debug store | critical | never | owner scoped | short raw TTL | Only if feature flag + encryption + TTL + audit pass. |
| `llm_call_payloads` | `encryption_key_ref` | `String(160)` | yes | `NULL` | no | no | key reference | raw debug store | critical | never | owner scoped | short raw TTL | Key ref only, never key material. |
| `llm_call_payloads` | `retention_expires_at` | `DateTime(timezone=True)` | no | policy timestamp | yes | no | retention | policy | low | no | owner scoped | payload retention | Cleanup deletes or redacts row by status. |
| `llm_call_payloads` | `access_audit_ref_id` | `String(80)` | yes | `NULL` | yes | no | `AuditEvent` | audit | medium | no | owner scoped | audit retention | Required for raw debug access. |

## 7. Index 与 unique constraints

| Table | Indexes | Unique constraints |
|---|---|---|
| `agent_runs` | `(owner_id, ai_task_id)`, `(owner_id, status, updated_at)`, `(owner_id, graph_name, created_at)`, `(owner_id, thread_id)` | `(owner_id, thread_id)`, `(owner_id, graph_name, idempotency_key_hash)` |
| `agent_node_runs` | `(owner_id, agent_run_id, created_at)`, `(owner_id, agent_run_id, node_name)`, `(owner_id, status, updated_at)` | `(owner_id, agent_run_id, node_name, attempt_number)` |
| `agent_interrupts` | `(owner_id, agent_run_id, status)`, `(owner_id, agent_node_run_id)`, `(owner_id, expires_at)` | `(owner_id, id, idempotency_key_hash)` when key exists |
| `agent_checkpoint_refs` | `(owner_id, agent_run_id, created_at)`, `(owner_id, thread_id)`, `(owner_id, retention_expires_at)` | `(owner_id, checkpoint_namespace, thread_id, checkpoint_id)` |
| `llm_calls` | `(owner_id, ai_task_id, created_at)`, `(owner_id, agent_run_id, created_at)`, `(owner_id, status, updated_at)`, `(owner_id, configured_model, provider_model)` | none in PR2; call id is primary key |
| `llm_call_payloads` | `(owner_id, llm_call_id)`, `(owner_id, payload_kind)`, `(owner_id, retention_expires_at)`, `(owner_id, raw_enabled, status)` | `(owner_id, llm_call_id, payload_kind)` |

## 8. Repository 方法

| Repository | Methods | Contract |
|---|---|---|
| `AgentRunRepository` | `create_run`, `get_run_for_owner`, `get_by_ai_task`, `mark_running`, `mark_interrupted`, `mark_succeeded`, `mark_failed`, `list_timeline_runs`, `cleanup_expired_runs` | 所有方法带 `owner_id`；状态更新校验 `record_version`。 |
| `AgentNodeRunRepository` | `start_node`, `finish_node`, `fail_node`, `append_llm_call_ref`, `record_side_effect_key`, `list_by_run` | `record_side_effect_key` 必须先查重复 hash；重复时返回 existing ref。 |
| `AgentInterruptRepository` | `create_interrupt`, `get_open_interrupt_for_owner`, `resume_interrupt_once`, `expire_interrupts` | `resume_interrupt_once` 使用 `(owner_id, interrupt_id, idempotency_key_hash)` 防重复 resume。 |
| `AgentCheckpointRefRepository` | `record_checkpoint_ref`, `list_refs_by_run`, `get_latest_ref`, `expire_refs` | 只保存 refs 和 metadata，不读取 checkpoint payload 作为业务结果。 |
| `LlmCallRepository` | `create_planned_call`, `mark_running`, `mark_succeeded`, `mark_failed`, `mark_replay_reused`, `get_summary_for_owner`, `list_by_run` | summary 只返回 sanitized 字段、hash、usage、model、validation、fallback、low confidence。 |
| `LlmCallPayloadRepository` | `capture_sanitized_summary`, `capture_debug_raw_ref`, `expire_payloads`, `audit_payload_access` | raw access 必须先创建 audit event；production summary API 不读取 raw ref。 |
| `AgentSideEffectRepository` 或等价 wrapper | `persist_question_once`, `persist_feedback_once`, `persist_report_once`, `persist_candidate_once`, `record_pending_write`, `finalize_pending_write`, `mark_pending_write_failed` | Core Business 写入只通过 wrapper；wrapper 生成 deterministic side-effect key 并复用已有业务对象。 |

## 9. Migration order 与 rollback order

### 9.1 Migration order

1. PR2 schema preflight：确认 `ai_tasks`、`ai_task_results`、`trace_refs`、`audit_events`、`questions`、`feedback` 已存在；确认 `OwnedRecordMixin` 字段名未变；确认 `test_model_imports.py` 需要新增 runtime model import。
2. 新增 `agent_runs`。
3. 新增 `agent_node_runs`。
4. 新增 `agent_interrupts`。
5. 新增 `agent_checkpoint_refs`。
6. 新增 `llm_calls`。
7. 新增 `llm_call_payloads`。
8. 新增 indexes 与 unique constraints。
9. 新增 repository 与 schema bootstrap backfill 测试。
10. PR2 数据 backfill：无历史 `agent_run` 时不回填业务结果；已有 `ai_tasks` 保持原状态，只有新 LangGraph runtime 创建新 run。

### 9.2 Rollback order

1. 停止新 Agent Runtime feature flag，保留 legacy / deterministic path。
2. 将 `queued` / `running` 的 `agent_runs` 标记为 `cancelled` 或 `failed`，并阻断 late formal write。
3. 清理未完成 `pending_writes_json`，不删除已写入 Core Business Tables；正式业务对象以 Core tables 为准。
4. 删除或过期 `llm_call_payloads` raw/debug refs。
5. 删除 `llm_call_payloads` indexes / table。
6. 删除 `llm_calls` indexes / table。
7. 删除 `agent_checkpoint_refs` indexes / table。
8. 删除 `agent_interrupts` indexes / table。
9. 删除 `agent_node_runs` indexes / table。
10. 删除 `agent_runs` indexes / table。
11. 保留 `ai_tasks`、`ai_task_results`、Core Business Tables、`trace_refs`、`audit_events`，并用 audit summary 记录 rollback。

## 10. Replay / resume / side-effect idempotency

### 10.1 Production resume

- Production resume 默认复用已有 `llm_calls` 的 sanitized result summary、`output_refs_json` 和 Core Business Tables 中已完成的结果。
- 如果需要的 LLM result 缺失、hash 不匹配、source version 不匹配、checkpoint ref 过期或 validation summary 缺失，resume 必须 `fail closed`：标记 `agent_runs.status=failed` 或 `agent_interrupts.status=failed`，返回 `resume_failed` / `source_unavailable` / `validation_failed`，不重新调用 provider。
- Production resume 不从 checkpoint payload 读取业务结果；checkpoint 只恢复 graph control state。
- Production resume 不重复执行已完成 side effect；它通过 side-effect key 查找已写 `Question`、`Feedback`、`Report`、candidate 或 `AiTaskResult`。

### 10.2 Debug replay

- Debug replay 只能在 dev/test feature flag 下运行，状态使用 `replayed_debug` 或 `replay_reused`。
- Debug replay 不写 Core Business Tables，不创建正式 `Question`、`Feedback`、`Report`、`Weakness`、`Asset`、`TrainingRecommendation` 或 `TrainingTask`。
- Debug replay 可写 `agent_node_runs`、`llm_calls` 的 replay summary，或写隔离的 debug-only artifact；不得把 replay 输出当成业务 API truth source。
- Debug replay 默认不调用 provider；如人工批准调用 fake transport，必须使用 deterministic fake。真实 provider debug replay 属于单独人工门禁，且 raw-off scan 先通过。

### 10.3 Side-effect wrapper contract

所有 graph node 写业务结果必须通过 side-effect wrapper，不允许 node 直接调用 Core repository 的 create 方法。

| Wrapper method | Idempotency key seed | Duplicate behavior | Business write boundary |
|---|---|---|---|
| `persist_question_once` | `owner_id + agent_run_id + node_name + "question" + session_id + progress_node_ref + input_digest + schema_id` | 返回已有 `question_id`，不创建第二题 | 只写 `questions`；重复题校验仍由 Core Business validation 承接 |
| `persist_feedback_once` | `owner_id + agent_run_id + node_name + "feedback" + answer_id + input_digest + schema_id` | 返回已有 `feedback_id`，不创建第二份点评 | 只写 `feedback` / `score_results` / loss point refs；validation failed 不写正式评分 |
| `persist_report_once` | `owner_id + agent_run_id + node_name + "report" + session_id + report_type + input_digest` | 返回已有 `report_id` | 写 `interview_reports` / `report_sections`，缺 evidence 时 partial |
| `persist_candidate_once` | `owner_id + agent_run_id + node_name + candidate_type + source_ref_hash + normalized_title + schema_id` | 返回已有 candidate ref 或 merge suggestion | 只写 candidate / suggestion；不写 formal object |
| `finalize_confirmation_once` | `owner_id + actor_id + target_ref + action + base_candidate_version_ref + request_body_hash` | 返回已有 confirmation result | 只有用户确认 API 可调用；graph replay 不调用 |

### 10.4 Pending writes

- Node 开始 side effect 前先在 `agent_runs.pending_writes_json` 或等价 repository 记录 `pending`：`side_effect_key_hash`、`target_table`、`target_ref_hint`、`agent_node_run_id`、`created_at`。
- 业务写入成功后将 pending write 标记为 `finalized` 并记录 `created_ref`。
- 写入失败后标记 `failed`，保留 sanitized error category；不得保存 request body、prompt、completion 或 provider payload。
- Resume 发现 `pending` 且无法证明业务写入成功时，必须查 Core Business Table 的 deterministic key；找到则 finalize，找不到则 fail closed，不重复创建。

## 11. Retention cleanup

| Object | Default retention | Cleanup action | Audit |
|---|---|---|---|
| `agent_runs` / `agent_node_runs` / `agent_interrupts` | 与 `ai_tasks` runtime retention 一致 | 过期后保留最小 status / hash / timing summary 或删除非必要 timeline | cleanup summary audit |
| `agent_checkpoint_refs` | 不长于 checkpoint store TTL | 先清 checkpoint store，再标记 refs `expired` 或删除 refs | cleanup summary audit |
| `llm_calls` | trace retention | 保留 sanitized summary、hash、model、usage、validation、fallback；删除不必要 error details | cleanup summary audit |
| `llm_call_payloads` sanitized | payload retention | 到期删除 `payload_summary_json` 或标记 `expired`，保留 `payload_hash` 供审计 | cleanup summary audit |
| `llm_call_payloads` debug raw refs | short raw TTL | TTL 到期立即删除 encrypted raw object ref，标记 `expired`；不得延长为普通 retention | raw cleanup audit |
| `pending_writes_json` | short runtime retention | run completed 后压缩为 finalized refs；failed run 保留 short TTL 后删除 detail | cleanup summary audit |

## 12. Tests

| Test file | Assertions |
|---|---|
| `tests/api/test_model_imports.py` | 新增 runtime model modules 后 `Base.metadata.tables` 包含六张表；不导入 LangGraph 到 Core Business model。 |
| `tests/api/test_db_schema_bootstrap.py` | schema 初始化包含字段、index、unique、JSON 列、DateTime 列；PostgreSQL / SQLite column SQL 编译通过。 |
| `tests/api/test_agent_run_repository.py` | owner scoped create/get/status transition/idempotent run create；stale `record_version` 失败。 |
| `tests/api/test_agent_interrupt_repository.py` | open/resume/expire；same `Idempotency-Key` resume 不重复执行。 |
| `tests/api/test_llm_call_repository.py` | sanitized summary 可查；raw payload 默认无行或无 ref；owner mismatch denied。 |
| `tests/api/test_sensitive_payload_redaction.py` | `raw_prompt`、`raw_completion`、`provider_payload`、`system prompt`、`token`、`cookie`、`secret` 不进入 API summary、logs、checkpoint refs、payload summary。 |
| `tests/api/test_agent_side_effect_idempotency.py` | replay/resume 不重复创建 `Question` / `Feedback` / candidate；pending write reconcile 不重复写业务表。 |
| `tests/api/test_agent_replay_resume_policy.py` | production resume 复用 sanitized result 或 fail closed；debug replay 不写 Core Business Tables；provider 不被调用。 |

## 13. Definition of Done

- 六张 AI Runtime Tables 均有字段级定义、owner scope、sensitivity、API visibility、retention 和 index / unique 规则。
- `OwnedRecordMixin`、主键列名、ID prefix、JSON 命名、status enum 与当前代码风格一致。
- Migration order、rollback order、repository 方法、retention cleanup 和 tests 可直接进入 PR2 scope lock。
- Replay / resume / side-effect idempotency 已冻结：production resume 不重新调用 provider，debug replay 不写业务表，`persist_question` / `persist_feedback` 不重复创建。
- Checkpoint refs 只作为 runtime ref，不成为业务 truth source。
