---
title: 数据模型与迁移实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/data-model-and-migration-plan
---

# 数据模型与迁移实施计划

## 1. 文档目的

本文规划 LangGraph MultiAgent 重构的数据模型和迁移边界，明确 Core Business Tables、AI Runtime Tables、LangGraph Checkpoint Tables 三类表的职责。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- `05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md`

## 3. 当前状态

当前 active docs 已定义业务对象、AI task、trace/evidence、candidate/formal、migration/rollback handoff 等规则，但缺 `agent_runs`、`agent_node_runs`、`agent_interrupts`、`llm_calls`、`llm_call_payloads`、`agent_checkpoint_refs` 的表级规划。

## 4. 目标输出

新增或等价新增 AI Runtime Tables：

- `agent_runs`
- `agent_node_runs`
- `agent_interrupts`
- `llm_calls`
- `llm_call_payloads`
- `agent_checkpoint_refs`

## 5. 必须覆盖范围

### 5.1 三类表边界

| Category | Tables | Truth Source | API 可见性 | Retention / Security |
|---|---|---|---|---|
| Core Business Tables | resumes, jobs, bindings, sessions, questions, answers, feedback, scores, reports, reviews, weaknesses, assets, training | 业务事实源 | 业务 API 返回结构化结果 | owner、version、trace、evidence、audit |
| AI Runtime Tables | `ai_tasks`, `agent_runs`, `agent_node_runs`, `agent_interrupts`, `llm_calls`, `llm_call_payloads`, `agent_checkpoint_refs` | AI 运行事实 | Agent Runtime API 返回 sanitized summary | raw-off、retention、audit |
| LangGraph Checkpoint Tables | checkpointer-managed tables | runtime recovery only | 不直接暴露 | checkpoint payload 不作为业务事实 |

### 5.2 字段级表格骨架

| Table | Column | Type | Nullable | Index | Source | Sensitivity | API Visible | Owner Scope | Retention | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `agent_runs` | `id` | uuid/string | no | pk | runtime | low | yes | owner | runtime retention | run id |
| `agent_runs` | `owner_id` | uuid/string | no | yes | auth | sensitive | no | owner | runtime retention | owner isolation |
| `agent_runs` | `actor_id` | uuid/string | no | yes | auth | sensitive | no | owner | runtime retention | user action actor |
| `agent_runs` | `ai_task_id` | uuid/string | no | yes | facade | low | yes | owner | runtime retention | task linkage |
| `agent_runs` | `graph_name` | string | no | yes | registry | low | yes | owner | runtime retention | graph id |
| `agent_runs` | `status` | enum | no | yes | runtime | low | yes | owner | runtime retention | queued/running/interrupted/succeeded/failed |
| `agent_runs` | `created_at` / `updated_at` | datetime | no | yes | db | low | yes | owner | runtime retention | timestamps |
| `agent_node_runs` | `id` / `owner_id` / `actor_id` / `agent_run_id` / `graph_name` / `node_name` / `status` / `created_at` / `updated_at` | mixed | no | yes | runtime | mixed | sanitized | owner | runtime retention | timeline base |
| `agent_interrupts` | `id` / `owner_id` / `actor_id` / `agent_run_id` / `node_name` / `status` / `resume_schema_id` / `created_at` / `updated_at` | mixed | no | yes | runtime | mixed | sanitized | owner | runtime retention | confirmation/resume |
| `llm_calls` | `id` / `owner_id` / `actor_id` / `ai_task_id` / `agent_run_id` / `graph_name` / `node_name` / `status` / `created_at` / `updated_at` | mixed | no | yes | transport | mixed | summary only | owner | trace retention | no raw |
| `llm_calls` | `provider_model` / `configured_model` / `prompt_version` / `schema_id` / `contract_ids` | string/json | yes | partial | transport/registry | low | yes | owner | trace retention | quality analysis |
| `llm_calls` | `request_hash` / `response_hash` / `evidence_hash` / `fallback_reason` / `validation_errors` / `low_confidence_flags` | mixed | yes | partial | transport/validators | medium | sanitized | owner | trace retention | no payload |
| `llm_call_payloads` | `id` / `owner_id` / `llm_call_id` / `payload_kind` / `sanitized` / `raw_enabled` / `payload_ref` / `retention_expires_at` / `created_at` / `updated_at` | mixed | no | yes | policy | high | sanitized only | owner | payload retention | raw default false |
| `agent_checkpoint_refs` | `id` / `owner_id` / `actor_id` / `agent_run_id` / `graph_name` / `node_name` / `checkpoint_namespace` / `thread_id` / `checkpoint_id` / `status` / `created_at` / `updated_at` | mixed | no | yes | LangGraph adapter | medium | ref only | owner | checkpoint retention | ref only, no payload |

### 5.3 Migration / rollback 占位

Migration / rollback 由 PR2 补齐：

- 新增表创建顺序。
- index 和 owner constraint。
- in-flight `AiTask` / `agent_run` 处理。
- rollback trigger、decision owner、backup restore validation。
- late graph result 禁止写 formal object。

PR1 先冻结三类表边界和 raw-off 规则，因此不需要执行 migration。

## 6. 与 active docs 的关系

本文扩展 `PERSISTENCE_MODEL.md` 和 `DATA_MODEL.md` 的 AI runtime 表规划，不改写 Core Business table 语义。长期表结构必须回写 active docs 或由 PR2 的 migration plan 承接。

## 7. 非目标

- 不写 DDL。
- 不执行 migration。
- 不选择 Alembic 或其他迁移工具。
- 不把 checkpoint 作为业务查询 source of truth。
- 不保存 raw prompt/completion/provider payload 到普通表。

## 8. 后续 PR 使用方式

- PR2：新增 AI runtime 表、repository、migration/rollback plan 和 tests。
- PR3：facade/runner 写入 `agent_runs` 生命周期。
- PR4：LangGraph adapter 写入 node runs、interrupts、checkpoint refs、LLM calls。

## 9. Definition of Done

- 三类表边界明确。
- 新增表有核心字段占位。
- owner、actor、status、timestamps、task/run/graph/node 字段已覆盖。
- migration / rollback 明确由 PR2 补齐。
- checkpoint 不进入业务 truth source，API 不暴露 checkpoint payload 或 raw LLM payload。

