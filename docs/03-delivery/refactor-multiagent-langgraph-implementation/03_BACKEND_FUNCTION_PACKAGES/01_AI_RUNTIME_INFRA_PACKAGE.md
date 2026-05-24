---
title: AI Runtime Infra Package
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 后端架构 / AI 架构
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/backend-function-packages/ai-runtime-infra-package
---

# AI Runtime Infra Package

## 1. Package 目标

本 package 冻结 AI Runtime infrastructure 的 method-level implementation plan。它覆盖 `AiOrchestrationFacade`、`AgentGraphRunner` port、registry、trace bridge、side-effect guard、handoff、interrupt service 和 concrete LangGraph adapter contract。

PR2 不实现本 package 的 runtime symbols。PR2 只可使用 `02_LLM_TRACE_PERSISTENCE_PACKAGE.md` 中的 inert data/repository/test scope。

## 2. 目标文件与 PR

| File | Symbol | PR | Layer |
|---|---|---:|---|
| `apps/api/app/application/ai_runtime/facade.py` | `AiOrchestrationFacade` | PR3 | application boundary |
| `apps/api/app/application/ai_runtime/contracts.py` | `AgentGraphRunner`, runtime DTO, errors | PR3 | application port |
| `apps/api/app/application/ai_runtime/registry.py` | `AgentGraphRegistry` | PR3 | application service |
| `apps/api/app/application/ai_runtime/trace_bridge.py` | `AgentTraceBridge` | PR3 | application contract |
| `apps/api/app/application/ai_runtime/side_effect_guard.py` | `AgentSideEffectGuard` | PR3 | policy |
| `apps/api/app/application/ai_runtime/handoff.py` | `AgentPersistenceHandoff` | PR3 / PR4 | application handoff |
| `apps/api/app/application/ai_runtime/interrupts.py` | `AgentInterruptService` | PR3 / PR4 | application service |
| `apps/api/app/application/ai_runtime/runtime_flags.py` | runtime default-off policy | PR3 | policy |
| `apps/api/app/infrastructure/ai_runtime/langgraph/runner.py` | `LangGraphAgentRunner` | PR4 | infrastructure adapter |
| `apps/api/app/infrastructure/ai_runtime/langgraph/checkpointer_factory.py` | `build_langgraph_checkpointer` | PR4 | infrastructure adapter |
| `apps/api/app/infrastructure/ai_runtime/langgraph/serializer.py` | `build_encrypted_serializer` | PR4 | infrastructure adapter |

## 3. Method-level plan

### 3.1 `AiOrchestrationFacade`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `start_job_match_analysis` | owner-checked binding/resume/job refs, score rule ref, idempotency key | `AiTaskStatusRef` with `ai_task_id` / `agent_run_id` | create or reuse `AiTask`; create `AgentRun`; call runner port | owner mismatch, source unavailable, idempotency conflict, graph disabled | facade returns refs and no LangGraph object |
| `start_polish_question_generation` | session ref, progress node refs, completed focus refs, idempotency key | `AiTaskStatusRef` | create task/run; no answer write | session denied, duplicate in-flight task, validation failed | answer-save boundary preserved |
| `start_polish_feedback_generation` | session/question/answer refs, requested outputs | `AiTaskStatusRef` | create task/run; candidate refs only until confirmation | answer missing, stale version, validation failed | no formal write before confirmation |
| `start_report_generation` | session/report type refs, score refs, idempotency key | `AiTaskStatusRef` | create task/run; pass report input refs | score refs missing, source unavailable | report generation uses refs only |
| `start_review_generation` | mock or real source refs, review scope, privacy flags | `AiTaskStatusRef` | create task/run; candidate refs only | real input not confirmed, privacy validation failed | no outcome prediction |
| `resume_interrupted_run` | run ref, interrupt ref, resume payload, base version, idempotency key | `AiTaskStatusRef` | validate resume; write audit; call runner `resume` | stale interrupt, schema invalid, owner mismatch | resume is idempotent and audited |
| `get_agent_run_status` | run ref, actor | sanitized status | read only | not found or inaccessible | no AgentState/checkpoint/raw payload |
| `get_agent_run_timeline` | run ref, cursor, limit, actor | sanitized timeline page | read only | invalid cursor, denied | timeline hides raw internals |

### 3.2 `AgentGraphRunner` port

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `start` | `AgentRunContext`, project-owned state | `AgentRunResult` | adapter may write trace/checkpoint refs | graph disabled, validation, execution error | port signatures contain no LangGraph types |
| `resume` | context, interrupt ref, validated resume payload | `AgentRunResult` | adapter resumes graph and appends trace | interrupt missing, resume invalid | resume idempotency |
| `replay` | context, checkpoint ref, replay mode | `AgentReplayResult` | debug timeline only; no formal write | checkpoint unavailable, replay not allowed | replay is read-only |
| `get_status` | run ref | `AgentRunStatus` | read only | not found | sanitized status |
| `get_timeline` | run ref, cursor, limit | `AgentRunTimelinePage` | read only | cursor invalid | sanitized page |
| `cancel` | run ref, reason, actor | `AgentRunStatus` | mark cancellable run cancelled; block late formal write | cancel not allowed | late formal write blocked |

### 3.3 `AgentGraphRegistry`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `get_graph_descriptor` | task type | graph descriptor | none | unknown graph | known task map |
| `get_contract_ids` | task type | prompt contract ids | none | unknown graph | prompt ids match registry |
| `validate_requested_outputs` | task type, requested outputs | validated request | none | unsupported output | rejects output drift |
| `resolve_feature_flag` | task type | flag policy | none | graph disabled | default-off behavior |
| `get_resume_schema` | interrupt type | schema descriptor | none | unknown schema | resume schema stable |

### 3.4 `AgentTraceBridge`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `record_run_started` | run/task/graph/owner refs | trace ref | write runtime run event | write failure | fail closed before formal write |
| `record_node_started` | run/node/input refs | trace ref | write node start | write failure | no raw state |
| `record_node_finished` | node status/output refs/validation | trace ref | update node and flags | write failure | validation visible |
| `record_llm_call` | LLM context/model/usage/validation | trace ref | write sanitized LLM call summary | raw payload detected | raw markers rejected |
| `record_interrupt` | interrupt schema/candidate refs/action summary | trace ref | write interrupt row | missing owner/schema | owner-scoped interrupt |
| `record_checkpoint_ref` | namespace/thread/checkpoint id/metadata | trace ref | write checkpoint ref only | payload present | no checkpoint payload |
| `record_run_finished` | final status/result refs/failure | trace ref | update run status | write failure | terminal status |

### 3.5 `AgentSideEffectGuard`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `authorize_node_start` | run context, node descriptor | decision | none | undeclared side effect | blocks undeclared side effects |
| `assert_no_raw_payload` | trace/timeline/checkpoint summary | sanitized summary | none | raw payload policy violation | raw prompt/completion/provider denied |
| `authorize_handoff` | result descriptor, target type, confirmation status | decision | none | formal write blocked | no formal write without confirmation |
| `authorize_tool_call` | tool descriptor, input refs | decision | none | owner/tool policy violation | owner-scoped tool input |
| `verify_checkpoint_write` | checkpoint metadata summary | decision | none | checkpoint contains business payload | checkpoint non-truth-source |

### 3.6 `AgentPersistenceHandoff`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `prepare_handoff` | validated run result, candidate refs, trace refs | handoff plan | none | missing validation/trace | requires validation and trace |
| `write_question_result` | accepted question plan | question ref | Core question command | duplicate/source unavailable | writes via Core command only |
| `write_feedback_result` | feedback / score / candidate plan | feedback / score refs | Core feedback/scoring command | validation failed | candidates stay non-formal |
| `write_report_result` | report sections and score refs | report refs | Core report command | copy boundary violation | no export artifact |
| `write_review_result` | review plan and candidate refs | review refs | Core review command | privacy validation failed | candidate-only |
| `write_candidate_result` | weakness/asset/training candidate plan | candidate refs | candidate/suggestion write only | formal write attempted | no formal object |
| `finalize_after_confirmation` | confirmation action and target command | formal ref | Core confirmation/formal command | stale candidate | user confirmation required |

### 3.7 `AgentInterruptService`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `create_interrupt` | run context, schema id, candidate refs, required action | interrupt ref | write interrupt and audit summary | schema missing, owner mismatch | drawer payload sanitized |
| `get_interrupt` | interrupt id, actor | interrupt detail | read only | inaccessible | hides AgentState |
| `validate_resume_payload` | interrupt ref, payload, base version | validated payload | none | schema invalid, stale version | preserves input on 422/409 |
| `resume_interrupt` | run ref, interrupt ref, payload, idempotency key | task ref | audit and runner resume | idempotency conflict | repeated same body returns same ref |
| `reject_interrupt` | run/interrupt refs, reason | interrupt ref | mark rejected, audit | stale/owner mismatch | no formal write |
| `expire_interrupts` | run ref, reason | count/refs | mark expired | write failure | stale interrupts expire |

### 3.8 `LangGraphAgentRunner`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `start` | context, descriptor, safe state | run result | compile/invoke graph, write events, persist checkpoint refs | compile/invoke/checkpointer/serializer errors | fake graph start records checkpoint ref |
| `resume` | context, interrupt ref, validated payload | run result | call LangGraph resume, audit resolved interrupt | missing checkpoint, stale interrupt | fake graph resume audited |
| `replay` | checkpoint ref, read-only policy | replay result | debug timeline only | checkpoint unavailable | no handoff call |
| `stream_events` | start/resume payload | sanitized events | runtime events | event schema mismatch | events sanitized |
| `map_langgraph_error` | concrete exception | project error | none | unknown maps generation failed | error mapping stable |

## 4. Import and dependency constraints

| Layer | Allowed | Forbidden |
|---|---|---|
| `application/ai_runtime/**` | project DTO, ports, policy, Core command ports by abstraction | `langgraph`, `langchain`, SQLAlchemy concrete session, provider SDK |
| `infrastructure/ai_runtime/langgraph/**` | LangGraph / LangChain runtime API, checkpointer, serializer, application runtime contracts | Core formal write bypass, API response assembly |
| Core Business | `AiOrchestrationFacade` contract when AI generation is needed | graph node, AgentState, checkpoint schema, provider payload |

## 5. Tests

Minimum PR3 / PR4 tests:

- `tests/api/test_agent_contracts.py`
- `tests/api/test_ai_orchestration_facade.py`
- `tests/api/test_agent_graph_runner.py`
- `tests/api/test_agent_runtime_api.py`
- `tests/api/test_agent_interrupt_replay.py`
- `tests/api/test_architecture_boundaries.py`

Each test must include raw-off, owner scope, checkpoint non-truth-source, idempotency or candidate/formal negative assertions where applicable.
