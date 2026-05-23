---
title: 后端 API 与 Schema 重构实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-api-and-schema-plan
---

# 后端 API 与 Schema 重构实施计划

## 1. 文档目的

本文规划 LangGraph MultiAgent 重构后的 API 分类、endpoint 级 request / response schema、owner enforcement、错误语义和普通用户可见性边界。目标是让 PR3 / PR4 / PR8 可以按现有 API envelope 与 FastAPI 依赖模式实现，不把 LangGraph checkpoint、AgentState 或未脱敏 LLM 内容暴露到业务 API。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`：仅作为 PR1 输入和边界提示，不作为 canonical。
- active docs：`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- `10_DATA_MODEL_AND_MIGRATION_PLAN.md`
- 当前代码映射：`apps/api/app/api/v1/polish.py` 已使用 `success_envelope(...)`、`require_authenticated_actor` 和 `actor.owner_id`；`apps/api/app/schemas/polish.py` 已承载 `PolishTaskStatus`、反馈 payload、candidate refs、low confidence 和 trace refs。

## 3. 当前状态

当前 active docs 已冻结：

- 成功 envelope 字段：`request_id`、`trace_id`、`status`、`resource_type`、`resource_ref`、`data`、`meta`、`candidate_refs`、`suggestion_refs`、`confirmation_required`、`ai_task_id`、`validation_result_ref`、`low_confidence_flags`、`source_availability`、`evidence_refs`、`trace_refs`、`score_version`、`rubric_version`、`confidence_level`、`pass_tendency_level`、`risk_level`、`next_actions`。
- 错误 envelope 字段：`request_id`、`trace_id`、`error.code`、`error.message`、`error.details`、`error.retryable`、`error.user_action`、`error.audit_event_ref`。
- 稳定错误码：`validation_failed=422`、`not_found_or_inaccessible=404`、`idempotency_conflict=409`、`stale_version_conflict=409`。
- owner enforcement：API 层使用 `require_authenticated_actor` 解析 actor；application / repository 查询必须带 `owner_id`，跨 owner 详情读取返回 `not_found_or_inaccessible` 或等价不可访问语义。

缺口是 Agent Runtime API、timeline、interrupt resume 和 sanitized LLM call summary 尚未有 endpoint-level schema；本文件冻结实现输入，不替代 `API_SPEC.md`。

## 4. 目标输出

API 分三类：

- Core Business API：返回业务对象或 AI task ref。
- Agent Runtime API：返回 task/run/timeline/interrupt status。
- LLM trace sanitized summary API：只返回脱敏摘要、hash、validation、fallback 和 usage summary。

## 5. 统一实现约束

### 5.1 API envelope 映射

所有成功响应必须通过现有 `success_envelope(...)` 或等价 helper 生成，最低字段如下：

| 场景 | HTTP | `status` | `resource_type` | `data` | 必须包含 |
|---|---:|---|---|---|---|
| 同步读取成功 | 200 | `success` / `partial` / `low_confidence` | 具体资源类型 | 结构化 read model | `request_id`、`trace_id` |
| 异步任务创建或 resume accepted | 202 | `accepted` / `queued` | `ai_task` | `AiTaskStatusResponse` | `ai_task_id`、`resource_ref` |
| AI task 查询 | 200 | task 当前 status | `ai_task` | `AiTaskStatusResponse` | `request_id`、`trace_id` |
| timeline 查询 | 200 | `success` | `agent_run_timeline` | `AgentRunTimelineResponse` | `meta.next_cursor` |
| sanitized LLM summary 查询 | 200 | `success` | `llm_call_summary` | `LlmCallSummaryResponse` | `trace_refs` |

`data`、`meta`、`trace_refs` 和 `error.details` 均不得包含未脱敏 Prompt、completion、provider request / response、checkpoint payload、完整 AgentState、token、cookie、secret、数据库 DSN 或隐藏评分规则。

### 5.2 Owner dependency

新增 endpoint 必须沿用当前 FastAPI 形态：

- route 依赖 `actor: CurrentActor = Depends(require_authenticated_actor)`。
- application command/query 必须显式传入 `owner_id=actor.owner_id`。
- repository read / write 必须 owner scoped；不得先读全量再在 API 层过滤。
- path id 只作为 resource ref，不作为授权依据。
- 详情类跨 owner 返回 `not_found_or_inaccessible=404`；明确 mutation owner mismatch 可返回 `permission_denied` 或 `owner_mismatch`，但不得泄露他人资源存在性。

### 5.3 用户可见性与 debug/admin 边界

| 字段 / 概念 | 普通用户 API 可见 | debug/admin 可见 | 规则 |
|---|---|---|---|
| `agent_run_id` | 可见 | 可见 | 仅作为运行引用、timeline 查询 key 和客服排障引用；不代表业务 truth source |
| `llm_call_id` | 默认不可直接列表展示；可通过 `trace_refs` 或 summary ref 间接出现 | 可见 | 普通用户只能读取 owner scoped sanitized summary；不得看到 provider payload |
| timeline node event | 可见 sanitized 摘要 | 可见更多运行摘要 | 普通用户事件只含 `node_key`、`status`、`started_at`、`finished_at`、`duration_ms`、`summary`、`validation_status`、`low_confidence_flags`、`safe_trace_refs` |
| checkpoint ref | 不可见 | 仅 debug/admin 安全摘要可见 | 普通用户 API 不返回 checkpoint namespace、payload 或 state |
| AgentState | 不可见 | 不返回完整 state | debug/admin 也只能按字段白名单读摘要 |
| Prompt / completion / provider payload | 不可见 | 不可见原文 | debug/admin 只能读 redaction hash、schema id、usage 和 failure category |

## 6. Endpoint-level schema

### 6.1 `GET /api/v1/ai-tasks/{ai_task_id}`

| 项 | 规格 |
|---|---|
| Request | path `ai_task_id: string`; auth actor；无 body |
| Response | envelope `resource_type=ai_task`, `status=data.status`, `data=AiTaskStatusResponse` |
| `AiTaskStatusResponse` | `ai_task_id`, `task_type`, `status`, `contract_ids[]`, `retryable`, `result_ref?`, `user_visible_status` |
| Owner | `ai_task.owner_id == actor.owner_id` |
| Errors | 401 `unauthenticated`; 404 `not_found_or_inaccessible`; 422 `validation_failed` for invalid id shape |
| Tests | `tests/api/test_agent_runtime_api.py::test_ai_task_status_requires_owner_and_envelope_shape` |

### 6.2 `GET /api/v1/agent-runs/{agent_run_id}`

| 项 | 规格 |
|---|---|
| Request | path `agent_run_id: string`; auth actor |
| Response | envelope `resource_type=agent_run`, `status=data.status`, `data=AgentRunSummaryResponse` |
| `AgentRunSummaryResponse` | `agent_run_id`, `ai_task_id`, `task_type`, `graph_name`, `status`, `started_at`, `finished_at?`, `interrupted`, `interrupt_refs[]`, `result_ref?`, `validation_result_ref?`, `low_confidence_flags[]`, `user_visible_status` |
| Forbidden response fields | `state`, `agent_state`, `checkpoint_payload`, `messages`, `prompt`, `completion`, `provider_payload` |
| Owner | run owner from `agent_runs.owner_id` or linked `ai_tasks.owner_id` |
| Errors | 401; 404 `not_found_or_inaccessible`; 422 invalid id |
| Tests | `tests/api/test_agent_runtime_api.py::test_agent_run_status_is_owner_scoped_and_hides_internal_state` |

### 6.3 `GET /api/v1/agent-runs/{agent_run_id}/timeline`

| 项 | 规格 |
|---|---|
| Request | path `agent_run_id`; query `cursor?`, `limit?`, `event_type?`, `status?`; auth actor |
| Response | envelope `resource_type=agent_run_timeline`, `status=success`, `data=AgentRunTimelineResponse`, `meta.next_cursor`, `meta.has_more`, `meta.limit` |
| `AgentRunTimelineResponse` | `agent_run_id`, `events[]` |
| `AgentTimelineEvent` | `event_id`, `event_type=node_started/node_completed/node_failed/interrupt_created/resumed/validation_failed/low_confidence/result_persisted`, `node_key`, `status`, `started_at?`, `finished_at?`, `duration_ms?`, `summary`, `safe_trace_refs[]`, `validation_status?`, `low_confidence_flags[]`, `user_visible` |
| Owner | run owner scoped |
| Errors | 401; 404 `not_found_or_inaccessible`; 422 `validation_failed` for cursor / filter |
| Tests | `tests/api/test_agent_runtime_api.py::test_agent_run_timeline_is_owner_scoped_and_sanitized` |

### 6.4 `POST /api/v1/agent-runs/{agent_run_id}/interrupts/{interrupt_id}/resume`

| 项 | 规格 |
|---|---|
| Headers | `Idempotency-Key` required |
| Request | `AgentInterruptResumeRequest` |
| `AgentInterruptResumeRequest` | `action: approve/edit/reject`, `resume_payload: object`, `base_interrupt_version_ref`, `user_message?`, `correction_refs[]?` |
| Response | HTTP 202 envelope `resource_type=ai_task`, `status=accepted`, `data=AiTaskStatusResponse`, `ai_task_id` |
| Owner | run owner scoped；interrupt must belong to run |
| Async | resume creates or reuses an AI task; repeated same idempotency body returns same task status |
| Errors | 401; 404 `not_found_or_inaccessible`; 409 `idempotency_conflict`; 409 `stale_version_conflict`; 422 `validation_failed` |
| Audit | audit event records actor, run, interrupt, action, result; no sensitive resume payload body |
| Tests | `tests/api/test_agent_interrupt_replay.py::test_resume_interrupt_requires_owner_schema_and_audit`; `tests/api/test_agent_interrupt_replay.py::test_resume_interrupt_replays_idempotent_same_body_and_conflicts_different_body` |

### 6.5 `GET /api/v1/llm-calls/{llm_call_id}/summary`

| 项 | 规格 |
|---|---|
| Request | path `llm_call_id`; auth actor |
| Response | envelope `resource_type=llm_call_summary`, `status=success`, `data=LlmCallSummaryResponse` |
| `LlmCallSummaryResponse` | `llm_call_id`, `ai_task_id`, `agent_run_id?`, `contract_ids[]`, `provider_name_hash?`, `model_name?`, `request_hash`, `response_hash`, `usage_summary`, `validation_status`, `failure_category?`, `fallback_used`, `redaction_applied`, `safe_error_summary?`, `created_at` |
| Owner | call owner scoped through `llm_calls.owner_id` or linked `ai_task` |
| Forbidden response fields | prompt body, completion body, provider payload, request body, response body, messages |
| Errors | 401; 404 `not_found_or_inaccessible`; 422 invalid id |
| Tests | `tests/api/test_llm_call_repository.py::test_llm_call_summary_enforces_owner_and_never_returns_raw_payload` |

### 6.6 `POST /api/v1/reports`

| 项 | 规格 |
|---|---|
| Headers | `Idempotency-Key` required |
| Request | `CreateReportTaskRequest`: `report_type=polish_summary/pressure_full`, `session_ref`, `input_refs[]`, `base_session_version_ref?`, `requested_sections[]?` |
| Response | HTTP 202 envelope `resource_type=ai_task`, `status=accepted`, `data=AiTaskStatusResponse`, `ai_task_id` |
| Owner | session/input refs owner scoped |
| Errors | 401; 404 `not_found_or_inaccessible`; 409 `idempotency_conflict`; 409 `stale_version_conflict`; 422 `validation_failed` |
| Boundary | no exact probability; no file/export artifact; report result may be `partial` / `low_confidence` |
| Tests | `tests/api/test_report_api.py::test_create_report_task_returns_ai_task_envelope_and_requires_owner_scope` |

### 6.7 `POST /api/v1/reviews/mock`

| 项 | 规格 |
|---|---|
| Headers | `Idempotency-Key` required |
| Request | `CreateReviewTaskRequest`: `review_type=mock`, `source_session_ref?`, `report_ref?`, `input_refs[]`, `base_source_version_ref?` |
| Response | HTTP 202 envelope `resource_type=ai_task`, `status=accepted`, `data=AiTaskStatusResponse` |
| Owner | session/report/input refs owner scoped |
| Errors | 401; 404; 409 `idempotency_conflict` / `stale_version_conflict`; 422 `validation_failed` |
| Boundary | produced Asset / Weakness / Training items are candidate / suggestion refs only |
| Tests | `tests/api/test_review_api.py::test_create_mock_review_task_is_candidate_only_and_owner_scoped` |

### 6.8 `POST /api/v1/reviews/real-inputs`

| 项 | 规格 |
|---|---|
| Headers | `Idempotency-Key` required |
| Request | `CreateRealInterviewInputRequest`: `job_ref`, `resume_ref`, `interview_transcript_summary`, `question_answer_items[]`, `source_completeness`, `third_party_redaction_confirmed`, `base_job_version_ref`, `base_resume_version_ref` |
| Response | HTTP 201 envelope `resource_type=real_interview_input`, `status=success`, `data=RealInterviewInputResponse` |
| Owner | job/resume/input owner scoped |
| Async | sync save; must not call LLM |
| Errors | 401; 404; 409 `idempotency_conflict` / `stale_version_conflict`; 422 `validation_failed` |
| Boundary | third-party sensitive text is minimized; no generation side effect |
| Tests | `tests/api/test_review_api.py::test_real_review_input_save_is_sync_no_llm_and_redacts_third_party_fields` |

### 6.9 `POST /api/v1/reviews/real`

| 项 | 规格 |
|---|---|
| Headers | `Idempotency-Key` required |
| Request | `CreateReviewTaskRequest`: `review_type=real`, `real_interview_input_ref`, `input_refs[]`, `base_input_version_ref` |
| Response | HTTP 202 envelope `resource_type=ai_task`, `status=accepted`, `data=AiTaskStatusResponse` |
| Owner | real interview input owner scoped |
| Errors | 401; 404; 409 `idempotency_conflict` / `stale_version_conflict`; 422 `validation_failed` |
| Boundary | only confirmed real input can start generation; no real outcome prediction |
| Tests | `tests/api/test_review_api.py::test_real_review_generation_requires_confirmed_input_and_returns_task_ref` |

## 7. Schema 禁止字段

- raw prompt
- raw completion
- provider payload
- checkpoint payload
- full AgentState
- hidden scoring rules

以上语义进入 Pydantic / TypeScript DTO 时，字段名不得以等价别名绕过，例如 `messages_raw`、`provider_response_body`、`checkpoint_state_json`、`internal_rubric_weights` 同样禁止。

## 8. 与 active docs 的关系

本文不替代 `API_SPEC.md`。PR3/PR4/PR8 必须把稳定 endpoint 和 schema 回写 `API_SPEC.md`，并与 `SECURITY_PRIVACY.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md` 保持一致。

## 9. 非目标

- 不定义最终 DDL、ORM 或 migration。
- 不实现 endpoint。
- 不新增前端页面。
- 不暴露 checkpoint payload。
- 不暴露 raw prompt/completion/provider payload。

## 10. 目标 PR 使用方式

- PR3：冻结 facade command/result 与 API service contract。
- PR4：实现 agent runtime status/timeline/interrupt fake graph API。
- PR8：实现 report/review generation API 与 candidate closure API。

## 11. Definition of Done

- endpoint table 覆盖 method/path/request/response/owner/async/error/tests。
- Core Business API、Agent Runtime API、LLM trace summary API 分离。
- LLM summary sanitized-only。
- API response 不暴露 raw payload、checkpoint payload 或 AgentState。
- 普通用户可见 `agent_run_id`、`llm_call_id`、timeline 的边界已冻结。
- 所有新增 endpoint 明确沿用 `success_envelope`、`request_id`、`trace_id`、`resource_type`、`data` 和现有 owner dependency。
