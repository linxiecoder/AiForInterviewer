---
title: 后端 Agent Runtime 与 LangGraph 接入实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/backend-agent-runtime-plan
---

# 后端 Agent Runtime 与 LangGraph 接入实施计划

## 1. 文档目的

本文规划后端 Agent Runtime 与 LangGraph 接入的 implementation-ready contract，确保 Core Business 不依赖 LangGraph，所有 AI graph 调度都经由 `AiOrchestrationFacade`、`AgentGraphRunner` port 和 `LangGraphAgentRunner` infrastructure adapter。

AIFI-ARCH-008 关闭后的冻结点：

- `AiOrchestrationFacade` 是 Core UseCase 触达 AI Runtime 的唯一入口。
- `AgentGraphRunner` 是 application port。
- `LangGraphAgentRunner`、checkpointer factory、serializer factory 只能位于 `apps/api/app/infrastructure/ai_runtime/langgraph/**`。
- `AgentTraceBridge` 是 application contract；实际 DB write 由 `apps/api/app/infrastructure/db/repositories/ai_runtime/**` adapter / repository 完成。
- LangGraph checkpoint 不是业务事实源；formal object 写入只能通过 Core Business command / confirmation API。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- `02_RECOMMENDED_ARCHITECTURE.md`
- `03_TARGET_DIRECTORY_STRUCTURE.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`
- 当前代码映射：`application/llm` port、`infrastructure/llm` fake / OpenAI-compatible transport、`tests/api/test_architecture_boundaries.py`

## 3. 当前状态

当前 active docs 已有 `AiTask`、LLM call plan、Prompt contract、trace/evidence、candidate/formal handoff 等设计；当前代码已有 LLM transport protocol 与 deterministic fake transport。缺口是统一 Agent Runtime 层、graph runner port、LangGraph adapter、checkpointer factory、interrupt/resume、timeline 和 runtime side-effect policy。

AIFI-ARCH-008 不实现这些 symbol，只把每个 symbol 的 inputs / outputs / side effects / errors / tests 冻结到可直接落 PR3 / PR4 的粒度。

## 4. 目标输出

| File | Symbol | PR | 归属 |
|---|---|---:|---|
| `apps/api/app/application/ai_runtime/facade.py` | `AiOrchestrationFacade` | PR3 | application AI Runtime boundary |
| `apps/api/app/application/ai_runtime/contracts.py` | `AgentGraphRunner`、`AgentGraphState`、runtime DTO / errors | PR3 | application port / DTO |
| `apps/api/app/application/ai_runtime/registry.py` | `AgentGraphRegistry` | PR3 | application service |
| `apps/api/app/application/ai_runtime/trace_bridge.py` | `AgentTraceBridge` | PR3 | application contract |
| `apps/api/app/application/ai_runtime/side_effect_guard.py` | `AgentSideEffectGuard` | PR3 | application policy |
| `apps/api/app/application/ai_runtime/handoff.py` | `AgentPersistenceHandoff` | PR3-PR4 | application handoff contract |
| `apps/api/app/application/ai_runtime/interrupts.py` | `AgentInterruptService` | PR3-PR4 | application service |
| `apps/api/app/application/ai_runtime/runtime_flags.py` | runtime default-off / per-graph / real-provider gate policy | PR3 | application policy |
| `apps/api/app/infrastructure/ai_runtime/langgraph/runner.py` | `LangGraphAgentRunner` | PR4 | infrastructure adapter |
| `apps/api/app/infrastructure/ai_runtime/langgraph/checkpointer_factory.py` | `build_langgraph_checkpointer` | PR4 | infrastructure adapter |
| `apps/api/app/infrastructure/ai_runtime/langgraph/serializer.py` | `build_encrypted_serializer` | PR4 | infrastructure adapter |

## 5. Runtime 边界

### 5.0 AIFI-ARCH-008 目录决策

AIFI-ARCH-008 采用聚合 AI Runtime 目录：

- `apps/api/app/application/ai_runtime/**` 取代 PR1.5 中的 `application/ai/**` 与 `application/agents/**`。
- `apps/api/app/infrastructure/ai_runtime/langgraph/**` 取代 PR1.5 中的 `infrastructure/agent_runtime/langgraph/**`。
- `application` 层不得存在 `langgraph_adapters/**`；adapter descriptor 只能作为 project-owned DTO 存放在 `contracts.py` 或 `registry.py`。
- 唯一 LangGraph import root 是 `apps/api/app/infrastructure/ai_runtime/langgraph/**`。
- graph / node / tool / validator 的共享 contract 先按 technical layer 放在 `application/ai_runtime` 根目录；业务 graph 只能在 PR5-PR8 受权后按 `application/ai_runtime/graphs/<business-domain>/**` 创建，PR2 和 PR3 不创建业务 graph 目录。

### 5.1 允许调用链

```text
Core UseCase
  -> AiOrchestrationFacade
    -> AgentGraphRegistry
    -> AgentSideEffectGuard
    -> AgentGraphRunner port
      -> LangGraphAgentRunner
        -> LangGraph compiled graph
        -> LlmTransport / PersistedLlmTransport
        -> AgentTraceBridge contract
          -> infrastructure/db/repositories runtime write adapter
        -> AgentPersistenceHandoff
          -> Core Business command port
```

### 5.2 禁止调用链

```text
Core UseCase -> LangGraph
Core UseCase -> checkpointer
Repository -> LangGraph
DB Model -> LangGraph
Repository / DB Model -> AgentGraphState
application/ai_runtime -> SQLAlchemy concrete session
application/ai_runtime -> infrastructure/ai_runtime/langgraph
Graph node -> formal object direct write
Graph node -> provider SDK direct call
Frontend -> AgentState / checkpoint payload / raw prompt / completion / provider payload
```

### 5.3 状态与持久化边界

- `AgentGraphState` 只保存 refs、safe summaries、validation flags、low confidence flags、candidate refs、checkpoint refs；默认不保存简历全文、回答全文、raw prompt、raw completion、provider payload。
- `agent_runs` / `agent_node_runs` / `agent_interrupts` / `llm_calls` / `agent_checkpoint_refs` 是 AI Runtime facts，不替代业务事实表。
- LangGraph checkpoint tables 只用于 resume / replay / fault tolerance，不作为 API read model 或 formal object source。
- formal object 写入只允许通过 `AgentPersistenceHandoff` 调用 Core Business command，且必须满足 owner、schema、validation、confirmation、audit 规则。

## 6. 方法级 Contract

### 6.1 `AiOrchestrationFacade`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `start_resume_analysis(command, actor)` | owner-checked resume/version refs、idempotency key、requested contracts | `AiTaskStatusRef` with `ai_task_id` / `agent_run_id` | create or reuse `AiTask`; create `agent_run`; call runner start | `owner_mismatch`、`source_unavailable`、`idempotency_conflict`、`unknown_graph` | `test_start_resume_analysis_creates_task_and_run_without_langgraph_import` |
| `start_job_match_analysis(command, actor)` | binding id、resume/job version refs、score rule ref、idempotency key | `AiTaskStatusRef` | create/reuse task; create run; enqueue / invoke `job_match_graph` | owner mismatch across binding inputs、source unavailable、validation failed | `test_start_job_match_analysis_uses_registry_contracts` |
| `start_polish_question_generation(command, actor)` | session id、topic/subtopic/progress refs、recent turn refs、idempotency key | `AiTaskStatusRef` | create/reuse task; pass forbidden repeat refs; no answer write | session denied、duplicate in-flight task、source unavailable | `test_start_polish_question_generation_keeps_answer_save_separate` |
| `start_polish_feedback_generation(command, actor)` | session id、question id、answer id、session summary ref、requested outputs | `AiTaskStatusRef` | create/reuse task; call feedback graph; candidate refs only until confirmation | answer not found、stale question version、validation failed、provider unavailable | `test_start_feedback_generation_returns_task_ref_and_no_formal_write` |
| `start_report_generation(command, actor)` | session/report type refs、turn refs、score refs、idempotency key | `AiTaskStatusRef` | create/reuse task; generate report candidate/result through handoff | insufficient sources、score refs missing、source unavailable | `test_start_report_generation_requires_generation_refs` |
| `start_mock_review_generation(command, actor)` | session/report refs、review scope、idempotency key | `AiTaskStatusRef` | create/reuse task; write review candidate refs; no formal weakness/asset/training write | report unavailable、source conflict、owner mismatch | `test_start_mock_review_generation_candidate_only` |
| `start_real_review_generation(command, actor)` | confirmed real input refs、trust flags、optional job/resume refs | `AiTaskStatusRef` | create/reuse task; generate review with third-party privacy flags | missing confirmed input、privacy validation failed、source unavailable | `test_start_real_review_generation_requires_confirmed_input` |
| `start_candidate_generation(command, actor)` | source refs、candidate target type、contract ids、idempotency key | `AiTaskStatusRef` | create/reuse task; write candidate / suggestion refs only | unsupported target type、formal write blocked、low confidence | `test_start_candidate_generation_never_writes_formal_object` |
| `resume_interrupted_run(command, actor)` | `agent_run_id`、`interrupt_id`、resume payload、idempotency key、base interrupt version | `AiTaskStatusRef` | validate resume payload; write audit; call runner resume; may call handoff | stale interrupt、schema invalid、owner mismatch、resume conflict | `test_resume_interrupted_run_validates_schema_owner_and_audit` |
| `get_agent_run_status(query, actor)` | run id、actor、visibility scope | `AgentRunStatus` | read only | not found / inaccessible、owner mismatch | `test_get_agent_run_status_returns_sanitized_summary` |
| `get_agent_run_timeline(query, actor)` | run id、cursor、limit、actor | `AgentRunTimelinePage` | read only | denied、invalid cursor | `test_get_agent_run_timeline_hides_agent_state_and_raw_payload` |

Facade contract constraints:

- Inputs must already be API-level validated, but facade re-checks owner/source invariants before runtime start.
- Outputs are task/run refs and sanitized summaries, not LangGraph state.
- Facade does not import LangGraph, compile graph, create checkpointer, or call provider SDK.

### 6.2 `AgentGraphRunner` port

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `start(context, initial_state)` | `AgentRunContext`、project-owned `AgentGraphState` | `AgentRunResult` | adapter may write runtime trace/checkpoint refs through injected contracts | `GraphNotFoundError`、`GraphValidationError`、`GraphExecutionError` | `test_agent_graph_runner_start_contract_is_langgraph_free` |
| `resume(context, interrupt_ref, resume_payload)` | run context、interrupt ref、validated payload | `AgentRunResult` | adapter resumes graph; writes node/timeline events | `InterruptNotFoundError`、`ResumePayloadInvalidError`、`GraphExecutionError` | `test_agent_graph_runner_resume_contract` |
| `replay(context, checkpoint_ref, mode)` | run context、checkpoint ref、replay mode read-only flag | `AgentReplayResult` | read-only timeline / debug events; no formal write | `CheckpointUnavailableError`、`ReplayNotAllowedError` | `test_agent_graph_runner_replay_is_read_only` |
| `get_status(run_ref)` | run ref | `AgentRunStatus` | read only | `AgentRunNotFoundError` | `test_agent_graph_runner_status_sanitized` |
| `get_timeline(run_ref, cursor, limit)` | run ref、pagination | `AgentRunTimelinePage` | read only | `TimelineCursorInvalidError` | `test_agent_graph_runner_timeline_sanitized` |
| `cancel(run_ref, reason)` | run ref、reason、actor | `AgentRunStatus` | mark cancellable run cancelled; block late formal write | `CancelNotAllowedError`、`AgentRunNotFoundError` | `test_agent_graph_runner_cancel_blocks_late_write` |

Port constraints:

- `AgentGraphRunner` lives in `application/ai_runtime/contracts.py`.
- It exposes project DTO only; no LangGraph type in signature, docstring example, return type, exception type, or test fixture.

### 6.3 `LangGraphAgentRunner`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `start(context, initial_state)` | runner context, graph descriptor, safe state | `AgentRunResult` | compile / invoke graph; write node events; persist checkpoint refs; call trace bridge | LangGraph compile/invoke error mapped to `GraphExecutionError`; checkpointer error; serializer error | `test_langgraph_agent_runner_fake_graph_start_records_checkpoint_ref` |
| `resume(context, interrupt_ref, resume_payload)` | run context, interrupt ref, validated payload | `AgentRunResult` | call LangGraph resume / command API; write interrupt resolved audit ref | missing checkpoint、stale interrupt、LangGraph API mismatch | `test_langgraph_agent_runner_fake_graph_resume_records_audit` |
| `replay(context, checkpoint_ref, mode)` | checkpoint ref, read-only replay policy | `AgentReplayResult` | replay timeline only; no business handoff | checkpoint unavailable、replay write attempted | `test_langgraph_agent_runner_replay_does_not_call_handoff` |
| `stream_events(context, initial_state_or_resume)` | run context and start/resume payload | iterator/list of sanitized events | writes runtime events; redacts raw payload | stream unsupported、event schema mismatch | `test_langgraph_agent_runner_stream_events_are_sanitized` |
| `map_langgraph_error(exc)` | concrete LangGraph exception | project error | none | unknown exception maps to generation failed | `test_langgraph_errors_map_to_project_errors` |

Infrastructure constraints:

- This is the only concrete runner allowed to import `langgraph`.
- It does not write Core Business tables directly.
- It can write AI Runtime trace via repositories and can request formal write only through `AgentPersistenceHandoff`.

### 6.4 `AgentGraphRegistry`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `get_graph_descriptor(task_type)` | `task_type` | `AgentGraphDescriptor` | none | `UnknownGraphError` | `test_registry_maps_known_task_types` |
| `get_contract_ids(task_type)` | `task_type` | tuple of P-* contract ids | none | `UnknownGraphError` | `test_registry_returns_prompt_contract_ids` |
| `validate_requested_outputs(task_type, requested_outputs)` | task type、requested outputs | `ValidatedGraphRequest` | none | `UnsupportedOutputError` | `test_registry_rejects_unsupported_outputs` |
| `resolve_feature_flag(task_type)` | task type | flag key / enabled policy | none | `GraphDisabledError` | `test_registry_feature_flag_blocks_runtime` |
| `get_resume_schema(interrupt_type)` | interrupt type | schema id / version / validator ref | none | `UnknownInterruptSchemaError` | `test_registry_returns_resume_schema` |

Registry constraints:

- Registry stores descriptors and ids, not compiled LangGraph objects.
- Contract ids must match `PROMPT_SPEC.md` / prompt-contracts registry before business graph PR starts.

### 6.5 `AgentTraceBridge`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `record_run_started(event)` | run id、task id、graph name、owner、actor | `TraceRef` | write `agent_runs` start event through repository port | write failure -> runtime failure before formal write | `test_trace_bridge_records_run_started` |
| `record_node_started(event)` | run id、node key、input refs summary | `TraceRef` | write `agent_node_runs` started | write failure | `test_trace_bridge_records_node_started_without_raw_state` |
| `record_node_finished(event)` | node status、output refs、validation status | `TraceRef` | update node run; write low confidence flags | write failure | `test_trace_bridge_records_node_finished_sanitized` |
| `record_llm_call(event)` | llm trace context、model family、usage summary、validation refs | `TraceRef` | write `llm_calls` sanitized summary | raw payload detected -> validation error | `test_trace_bridge_rejects_raw_prompt_completion_provider_payload` |
| `record_validation(event)` | validation result、schema id、failure category | `TraceRef` | write validation trace summary | validation trace write failure | `test_trace_bridge_records_validation_failure_visible` |
| `record_interrupt(event)` | interrupt id、schema id、candidate refs、required action | `TraceRef` | write `agent_interrupts` | missing owner/schema | `test_trace_bridge_records_interrupt_with_owner` |
| `record_checkpoint_ref(event)` | namespace、thread id、checkpoint id、sequence、status | `TraceRef` | write `agent_checkpoint_refs`; no checkpoint payload | payload present -> validation error | `test_trace_bridge_checkpoint_ref_no_payload` |
| `record_run_finished(event)` | final status、result refs、failure category | `TraceRef` | update run status | write failure | `test_trace_bridge_records_run_finished` |

TraceBridge constraints:

- `AgentTraceBridge` is an application contract; concrete DB write adapter lives in `infrastructure/db/repositories/ai_runtime/**`.
- Trace write failure must fail closed before any formal write. It may leave task in `generation_failed` / `validation_failed`, but cannot silently continue to formal object creation.

### 6.6 `AgentSideEffectGuard`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `authorize_node_start(context, node_descriptor)` | run context、node descriptor、declared side effects | `SideEffectDecision` | none | `SideEffectPolicyViolation` | `test_guard_blocks_undeclared_side_effects` |
| `assert_no_raw_payload(payload_summary)` | candidate trace/checkpoint/timeline payload summary | sanitized payload summary | none | `RawPayloadPolicyViolation` | `test_guard_blocks_raw_prompt_completion_provider_payload` |
| `authorize_handoff(result_descriptor)` | graph result type、target type、confirmation status | `HandoffDecision` | none | `FormalWriteBlockedError` | `test_guard_blocks_formal_write_without_confirmation` |
| `authorize_tool_call(tool_descriptor, input_refs)` | tool name、input refs、owner context | `ToolCallDecision` | none | owner/source/tool policy violation | `test_guard_requires_owner_scoped_tool_inputs` |
| `verify_checkpoint_write(checkpoint_summary)` | checkpoint namespace/thread/checkpoint metadata | `CheckpointWriteDecision` | none | checkpoint contains business payload / raw payload | `test_guard_rejects_checkpoint_payload_as_business_truth` |

Guard constraints:

- Guard must be called by facade before runner start and by runner before handoff/checkpoint/timeline writes.
- Guard contains policy, not persistence.

### 6.7 `AgentPersistenceHandoff`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `prepare_handoff(run_result)` | validated graph result、candidate refs、trace refs | `HandoffPlan` | none | validation missing、low confidence needs manual review | `test_prepare_handoff_requires_validation_and_trace` |
| `write_question_result(plan)` | question candidate/result plan | `QuestionRef` / result ref | call Core question command; write audit | duplicate question、owner mismatch、source unavailable | `test_handoff_writes_question_via_core_command` |
| `write_feedback_result(plan)` | feedback / score / loss point plan | feedback / score refs | call Core feedback/scoring command; candidate refs remain candidate | validation failed、score invalid | `test_handoff_feedback_keeps_candidates_non_formal` |
| `write_report_result(plan)` | report sections、score refs、copy metadata | report refs | call Core report command | missing score refs、copy boundary violation | `test_handoff_report_requires_score_refs` |
| `write_review_result(plan)` | review summary/items/candidate refs | review refs | call Core review command; candidate refs only | privacy validation failed | `test_handoff_review_candidate_only` |
| `write_candidate_result(plan)` | weakness/asset/training candidate plan | candidate refs | create candidate/suggestion only | formal write attempted | `test_handoff_candidate_generation_never_creates_formal` |
| `finalize_after_confirmation(plan)` | confirmation ref、actor、target formal command | formal ref | call Core confirmation/formal command; audit | stale candidate、owner mismatch、validation failed | `test_finalize_after_confirmation_requires_user_confirmation` |

Handoff constraints:

- It never reads LangGraph checkpoint payload.
- It never writes SQLAlchemy models directly; it calls Core command ports or repositories already owned by Core Business.
- It converts AI output to candidate / suggestion / validated business result only after `AgentSideEffectGuard` allows the transition.

### 6.8 `AgentInterruptService`

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `create_interrupt(context, interrupt_request)` | run context、schema id、candidate refs、required action | `AgentInterruptRef` | write interrupt row; audit summary | schema missing、owner mismatch | `test_create_interrupt_requires_schema_owner_and_candidate_refs` |
| `get_interrupt(interrupt_id, actor)` | interrupt id、actor | sanitized interrupt detail | read only | not found/inaccessible | `test_get_interrupt_hides_agent_state` |
| `validate_resume_payload(interrupt_ref, payload)` | interrupt ref、payload、base version | `ValidatedResumePayload` | none | schema invalid、stale version、unsupported action | `test_validate_resume_payload_rejects_stale_or_invalid` |
| `resume_interrupt(command, actor)` | run id、interrupt id、validated payload、idempotency key | `AiTaskStatusRef` | audit; call `AgentGraphRunner.resume` | idempotency conflict、owner mismatch、runner error | `test_resume_interrupt_calls_runner_after_validation` |
| `reject_interrupt(command, actor)` | run id、interrupt id、reason | `AgentInterruptRef` | mark rejected; audit; block formal write | stale interrupt、owner mismatch | `test_reject_interrupt_blocks_formal_write` |
| `expire_interrupts(run_ref, reason)` | run ref、expiry reason | count / refs | mark stale interrupts expired | write failure | `test_expire_interrupts_marks_stale` |

Interrupt constraints:

- Resume payload is user input and must go through schema validation, owner validation and idempotency.
- approve / edit / merge / skip / reject all write audit.
- confirm/edit/merge may trigger formal writes only through `AgentPersistenceHandoff.finalize_after_confirmation`.

## 7. Checkpointer / serializer contract

| Symbol | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `build_langgraph_checkpointer(settings, serializer)` | runtime settings、DB connection config、serializer | checkpointer object scoped to LangGraph adapter | may create / connect checkpoint backend in PR4 test env | config missing、unsupported backend、API mismatch | `test_build_langgraph_checkpointer_memory_for_tests`、`test_build_langgraph_checkpointer_postgres_for_prod_config` |
| `build_encrypted_serializer(settings)` | `LANGGRAPH_AES_KEY` or equivalent secret ref | encrypted serializer | validates key material; no logging key | missing key in prod、invalid key length、serializer API mismatch | `test_langgraph_serializer_requires_key_in_prod` |
| `checkpoint_ref_from_event(event)` | LangGraph checkpoint metadata | `AgentCheckpointRef` | none | missing namespace/thread/checkpoint id | `test_checkpoint_ref_contains_no_payload` |

Production checkpointer policy is frozen in `18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md`: PR4 either chooses PG checkpointer with encrypted serializer or explicitly downgrades to no-production-checkpoint mode before business graph migration. Test environment uses memory checkpointer and deterministic fake graph.

## 8. Error Mapping

| Runtime error | API / task status | Formal write rule | User-visible rule |
|---|---|---|---|
| `GraphDisabledError` | `generation_failed` or `source_unavailable` by task type | no write | retry disabled until feature flag enabled |
| `GraphExecutionError` | `generation_failed` | no write unless previous confirmed handoff already committed | visible failure with retryable flag if safe |
| `GraphValidationError` | `validation_failed` | no write | show validation failed / manual review |
| `RawPayloadPolicyViolation` | `validation_failed` | no write | sanitized error only |
| `CheckpointUnavailableError` | `generation_failed` for resume/replay; start may proceed only if graph does not require resume | no late write | show resume unavailable |
| `InterruptNotFoundError` | `not_found_or_inaccessible` | no write | no resource existence leak |
| `FormalWriteBlockedError` | `validation_failed` or `manual_review_required` | no write | confirmation required |
| `TraceWriteFailure` | `generation_failed` | fail closed before formal write | trace failure visible by category only |

## 9. 与 active docs 的关系

本文承接 active `APPLICATION_FLOW_SPEC.md` 的 orchestration，承接 `PERSISTENCE_MODEL.md` / `DATA_MODEL.md` 的 task、trace、candidate/formal 边界，承接 `PROMPT_SPEC.md` 的 contract registry，承接 `SECURITY_PRIVACY.md` 的 raw payload 禁止暴露规则，承接 `API_SPEC.md` 的 async task、idempotency、owner、status 和 error envelope。

长期 runtime contract 若需成为 canonical 设计，必须由主 Agent 汇总回写：

- `APPLICATION_FLOW_SPEC.md`：facade、runner、interrupt/resume、timeline、handoff。
- `PERSISTENCE_MODEL.md` / `DATA_MODEL.md`：agent run、node run、interrupt、checkpoint ref、LLM call tables。
- `API_SPEC.md`：agent run status/timeline/interrupt API。
- `SECURITY_PRIVACY.md`：checkpoint、serializer key、timeline、trace retention。
- ADR：Option C / LangGraph runtime 被长期接受时。

## 10. 非目标

- 不实现 LangGraph graph。
- 不创建 migration。
- 不迁移现有业务 use case。
- 不保存 raw prompt、raw completion 或 provider payload。
- 不把 checkpoint 当业务 source of truth。
- 不新增前端 UI。
- 不安装依赖、不调用 provider。

## 11. 后续 PR 使用方式

| PR | 使用方式 | 必须验证 |
|---|---|---|
| PR2 | 落 runtime 表、repository、sanitized LLM persistence | runtime refs owner scoped；raw-off tests |
| PR3 | 落 `application/ai_runtime` facade、runner port、registry、contracts、guard、handoff、interrupt service | application layer no LangGraph import；Core only calls facade / port；不创建 `langgraph_adapters/**` |
| PR4 | 落 LangGraph adapter、checkpointer、serializer、fake graph、interrupt/resume/timeline | only `infrastructure/ai_runtime/langgraph/**` imports LangGraph；fake graph deterministic；checkpoint ref no payload |
| PR5-PR8 | 迁移业务 graph | graph nodes use ports/tools/handoff；no direct formal write |

## 12. Definition of Done

- `AiOrchestrationFacade`、`AgentGraphRunner`、`LangGraphAgentRunner`、`AgentGraphRegistry`、`AgentTraceBridge`、`AgentSideEffectGuard`、`AgentPersistenceHandoff`、`AgentInterruptService` 的方法级 inputs / outputs / side effects / errors / tests 已覆盖。
- `application/ai_runtime/**` 与 `infrastructure/ai_runtime/langgraph/**` 是唯一最终目录形态；`application/ai/**`、`application/agents/**`、`infrastructure/agent_runtime/**` 和 `langgraph_adapters/**` 不再作为 PR2-PR8 创建目标。
- checkpointer factory 和 serializer factory 归属 infrastructure LangGraph adapter。
- trace bridge 是 application contract，DB write adapter / repository 归属 infrastructure DB repositories。
- Core Business 不依赖 LangGraph。
- checkpoint 不成为业务事实源。
- interrupt/resume owner、schema、audit、idempotency 边界明确。
- trace bridge 和 timeline 不写 raw prompt / completion / provider payload。
