---
title: 后端 Agent Runtime 与 LangGraph 接入实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-agent-runtime-plan
---

# 后端 Agent Runtime 与 LangGraph 接入实施计划

## 1. 文档目的

本文规划后端 Agent Runtime 与 LangGraph 接入的最小骨架，确保 Core Business 不依赖 LangGraph，所有 AI graph 调度都经由 `AiOrchestrationFacade`、`AgentGraphRunner` port 和 `LangGraphAgentRunner` adapter。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_MULTIAGENT_README.md`
- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- `02_RECOMMENDED_ARCHITECTURE.md`
- `03_TARGET_DIRECTORY_STRUCTURE.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`

## 3. 当前状态

当前 active docs 已有 `AiTask`、LLM call plan、Prompt contract、trace/evidence、candidate/formal handoff 等设计，但还缺统一 Agent Runtime 层、graph runner port、LangGraph adapter、checkpoint factory、interrupt/resume 和 runtime timeline。

## 4. 目标输出

目标规划对象：

- `apps/api/app/application/ai/orchestration_facade.py`
- `apps/api/app/application/agents/contracts.py`
- `apps/api/app/application/agents/state.py`
- `apps/api/app/application/agents/registry.py`
- `apps/api/app/application/agents/checkpointer_factory.py`
- `apps/api/app/application/agents/trace_bridge.py`
- `apps/api/app/infrastructure/agent_runtime/langgraph/runner.py`

## 5. 必须覆盖范围

### 5.1 Runtime 边界

- `AiOrchestrationFacade` 是 Core UseCase 与 AI Runtime 的唯一交界面。
- `AgentGraphRunner` 是 application port，封装 start/resume/replay/status/timeline。
- `LangGraphAgentRunner` 是唯一直接依赖 LangGraph 的 adapter。
- `contracts.py` 定义 enum、DTO、port 和 error。
- `state.py` 定义可序列化 graph state，只保存 refs / summaries / flags，不作为业务事实源。
- `registry.py` 负责 task type、graph name、contract ids、prompt version、schema id 映射。
- `checkpointer_factory.py` 负责 thread id、checkpoint namespace、checkpoint backend。
- `trace_bridge.py` 将 run、node、LLM、validation、low confidence、interrupt、checkpoint ref 写入 runtime trace。

### 5.2 方法级计划表

| File | Symbol | Kind | Action | Responsibility | Inputs | Outputs | Side Effects | Errors | Tests | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `application/ai/orchestration_facade.py` | `AiOrchestrationFacade.start_resume_analysis` | method | add | 启动 resume analysis graph | resume refs | `AiTaskStatusRef` | create `ai_task` / `agent_run` | owner/source/idempotency | facade tests | Core 不感知 LangGraph |
| same | `start_job_match_analysis` | method | add | 启动 job match graph | binding/version refs | task ref | runtime rows | source/validation | unit + API | PR5 补齐 |
| same | `start_polish_question_generation` | method | add | 启动题目生成 | session/topic refs | task ref | question handoff | duplicate/source | unit + flow | PR6 补齐 |
| same | `start_polish_feedback_generation` | method | add | 启动反馈生成 | answer refs | task ref | feedback/score/candidate handoff | validation/fallback | unit + flow | answer save 不触发 LLM |
| same | `start_report_generation` | method | add | 启动报告生成 | session/report refs | task ref | report handoff | insufficient sources | API + graph | no exact probability |
| same | `start_mock_review_generation` | method | add | 启动模拟复盘 | session/report refs | task ref | review candidate refs | source unavailable | API + graph | candidate-only |
| same | `start_real_review_generation` | method | add | 启动真实复盘 | confirmed input refs | task ref | review handoff | privacy/validation | API + graph | no outcome prediction |
| same | `start_candidate_generation` | method | add | 启动 weakness/asset/training candidate graph | source refs | task ref | candidate rows | formal write blocked | graph tests | 不写 formal |
| same | `resume_interrupted_run` | method | add | 恢复 interrupt | run id, interrupt id, payload | task status | audit + resume | stale/owner/schema | API + runner | payload validation |
| same | `get_agent_run_status` | method | add | 查询 run summary | run id | sanitized status | read only | not found/denied | API | 不返回 AgentState |
| same | `get_agent_run_timeline` | method | add | 查询 timeline | run id, cursor | sanitized events | read only | denied | API | 不返回 raw payload |
| `application/agents/contracts.py` | `AgentGraphRunner` | port | add | runtime 抽象接口 | context/state | result/status | adapter-specific | runner errors | contract tests | Core 只依赖 port |
| `infrastructure/agent_runtime/langgraph/runner.py` | `LangGraphAgentRunner` | adapter | add | 调用 LangGraph | graph spec/context | result | checkpoint/node trace | checkpoint/interrupt | fake graph tests | 唯一 LangGraph import |
| `application/agents/state.py` | `AgentGraphState` | schema | add | 定义可序列化 state | refs only | state snapshot | checkpoint only | schema invalid | serialization tests | 不放业务正文 |
| `application/agents/registry.py` | `AgentGraphRegistry` | service | add | task type -> graph 映射 | task type | graph spec | none | unknown graph | registry tests | contract ids |
| `application/agents/checkpointer_factory.py` | `build_checkpointer` | function | add | 构造 checkpointer | config/run context | checkpointer | checkpoint tables | config error | integration | checkpoint ref only |
| `application/agents/trace_bridge.py` | `AgentTraceBridge` | service | add | runtime 事件转 trace rows | run/node/llm events | trace refs | writes runtime trace | write failure | trace tests | fail closed for formal write |

### 5.3 interrupt / resume 计划占位

- interrupt 必须绑定 `owner_id`、`actor_id`、`agent_run_id`、`interrupt_id`、`resume_schema_id`。
- resume payload 必须 schema validate、version validate、owner enforce、idempotency enforce。
- approve/edit/reject/merge/skip 都必须写 audit。
- formal object 写入只能通过 Core Business command 或显式 API。

### 5.4 checkpoint / replay 计划占位

- checkpoint 用于 resume/replay/time travel，不作为业务事实源。
- Core Business table 只保存业务结果和 trace/evidence refs。
- `agent_checkpoint_refs` 只保存 checkpoint namespace、thread id、checkpoint id、sequence 和 status。

## 6. 与 active docs 的关系

本文承接 active `APPLICATION_FLOW_SPEC.md` 的 orchestration，承接 `PERSISTENCE_MODEL.md` / `DATA_MODEL.md` 的 task、trace、candidate/formal 边界，承接 `PROMPT_SPEC.md` 的 contract registry，承接 `SECURITY_PRIVACY.md` 的 raw payload 禁止暴露规则。

## 7. 非目标

- 不实现 LangGraph graph。
- 不创建 migration。
- 不迁移现有业务 use case。
- 不保存 raw prompt、raw completion 或 provider payload。
- 不把 checkpoint 当业务 source of truth。
- 不新增前端 UI。

## 8. 后续 PR 使用方式

- PR2：落 runtime 表、migration/rollback、repository tests。
- PR3：落 facade、runner port、registry、contracts。
- PR4：落 LangGraph adapter、checkpointer、trace bridge、fake graph、interrupt/resume。

## 9. Definition of Done

- 方法级计划表覆盖核心 symbols。
- Core Business 不依赖 LangGraph。
- checkpoint 不成为业务事实源。
- interrupt/resume owner、schema、audit 边界明确。
- trace bridge 不写 raw prompt/completion/provider payload。

