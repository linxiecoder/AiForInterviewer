---
title: 后端 API 与 Schema 重构实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-api-and-schema-plan
---

# 后端 API 与 Schema 重构实施计划

## 1. 文档目的

本文规划 LangGraph MultiAgent 重构后的 API 分类、endpoint 骨架和 schema 边界，避免业务 API 暴露 LangGraph checkpoint、AgentState 或 raw LLM payload。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active docs：`API_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- `10_DATA_MODEL_AND_MIGRATION_PLAN.md`

## 3. 当前状态

当前 active docs 已定义异步 `AiTask` 语义和 response envelope。缺口是 Agent Runtime API、timeline、interrupt resume 和 sanitized LLM summary API 尚未正式进入 active API spec。

## 4. 目标输出

API 分三类：

- Core Business API：返回业务对象或 AI task ref。
- Agent Runtime API：返回 task/run/timeline/interrupt status。
- LLM trace sanitized summary API：只返回脱敏摘要、hash、validation、fallback 和 usage summary。

## 5. 必须覆盖范围

| Endpoint | Method | Path | Request schema 占位 | Response schema 占位 | Owner enforcement | Async behavior | Error mapping | Tests |
|---|---|---|---|---|---|---|---|---|
| AI task status | GET | `/api/v1/ai-tasks/{task_id}` | path + auth | `AiTaskStatusResponse` | task owner | read current async status | 401/403/404 | owner/status enum |
| Agent run status | GET | `/api/v1/agent-runs/{agent_run_id}` | path + auth | `AgentRunSummaryResponse` | run owner | read only | 401/403/404 | no AgentState/raw |
| Agent timeline | GET | `/api/v1/agent-runs/{agent_run_id}/timeline` | cursor/filter | `AgentRunTimelineResponse` | run owner | read only | 401/403/404 | sanitized node events |
| Interrupt resume | POST | `/api/v1/agent-runs/{agent_run_id}/interrupts/{interrupt_id}/resume` | `AgentInterruptResumeRequest` + idempotency | `AiTaskStatusResponse` | run owner | async resume | 400/401/403/409/422 | stale interrupt/idempotency |
| LLM call summary | GET | `/api/v1/llm-calls/{llm_call_id}/summary` | path + auth | `LlmCallSummaryResponse` | call owner | read only | 401/403/404 | no raw payload |
| Report generation API | POST | `/api/v1/reports` | source refs, report type, idempotency key | `AiTaskAcceptedResponse` | session owner | async generation | 400/401/403/409/422 | no exact probability |
| Mock review generation API | POST | `/api/v1/reviews/mock` | session/report refs, idempotency key | `AiTaskAcceptedResponse` | source owner | async generation | 400/401/403/409/422 | candidate-only |
| Real review input API | POST | `/api/v1/reviews/real-inputs` | structured real interview input | `RealInterviewInputResponse` | actor owner | sync save, no LLM | 400/401/403/422 | privacy redaction |
| Real review generation API | POST | `/api/v1/reviews/real` | confirmed input ref, idempotency key | `AiTaskAcceptedResponse` | input owner | async generation | 400/401/403/409/422 | confirmed input only |

Schema 禁止字段：

- raw prompt
- raw completion
- provider payload
- checkpoint payload
- full AgentState
- hidden scoring rules

## 6. 与 active docs 的关系

本文不替代 `API_SPEC.md`。后续 PR3/PR4/PR8 必须把稳定 endpoint 和 schema 回写 `API_SPEC.md`，并与 `SECURITY_PRIVACY.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md` 保持一致。

## 7. 非目标

- 不定义完整 Pydantic schema。
- 不实现 endpoint。
- 不新增前端页面。
- 不暴露 checkpoint payload。
- 不暴露 raw prompt/completion/provider payload。

## 8. 后续 PR 使用方式

- PR3：冻结 facade command/result 与 API service contract。
- PR4：实现 agent runtime status/timeline/interrupt fake graph API。
- PR8：实现 report/review generation API 与 candidate closure API。

## 9. Definition of Done

- endpoint table 覆盖 method/path/request/response/owner/async/error/tests。
- Core Business API、Agent Runtime API、LLM trace summary API 分离。
- LLM summary sanitized-only。
- API response 不暴露 raw payload、checkpoint payload 或 AgentState。

