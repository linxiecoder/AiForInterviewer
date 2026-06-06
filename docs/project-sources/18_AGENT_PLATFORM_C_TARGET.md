---
title: 18_AGENT_PLATFORM_C_TARGET
type: note
permalink: ai-for-interviewer/docs/project-sources/18-agent-platform-c-target
---

# 18 Agent Platform C Target

## Purpose

锁定 Agent Platform 目标态 C，防止后续退化为仅 contracts + registry skeleton。

## Target C Definition

Agent Platform C 包含：

- AgentExecutor
- AgentDefinitionRegistry
- SkillRegistry
- ToolRegistry
- AgentExecutionPlan
- AgentExecutionTrace
- HandoffContract
- EvalContract
- Question / Feedback 接入该平台

C 不是单个类。
C 是一套可演进 Agent 运行契约。

## C0 / C1 / C2 / C3 / C4

### C0

Phase:

Phase 1

Scope:

- contracts
- definitions
- registry skeleton
- executor port
- handoff contract skeleton
- DDD rails
- boundary tests

Non-goal:

- 不替换 Question / Feedback runtime。
- 不改 prompt/provider/DB/API。

### C1

Phase:

Phase 4

Scope:

- Question / Feedback AgentDefinition 注册。
- Skills 注册。
- Tools 注册。
- Trace contract 对齐。
- Handoff contract 对齐。

Non-goal:

- 不必完成 LangGraph runtime。
- 不必完成 all Agent migration。

### C2

Phase:

Phase 5

Scope:

- Question Agent planned workflow。
- Question planner。
- Question skills/tools。
- Question candidate handoff。
- Question eval cases。

### C3

Phase:

Phase 6

Scope:

- Feedback Agent planned workflow。
- Feedback planner。
- Feedback skills/tools。
- Feedback candidate handoff。
- Feedback eval cases。

### C4

Phase:

Phase 8

Scope:

- LangGraph / multi-agent runtime。
- Controlled tool loop。
- Resume / replay / interrupt。
- Multi-agent handoff。

Current P8 foundation status:

- `partial_with_deferred_gaps` from `P8-GOAL-ONE-SHOT-C4-RUNTIME`.
- Validated foundation: `AgentGraphRunnerExecutorAdapter`, facade-created start routed through the adapter, facade-created status/timeline/cancel adapter routing with owner-scope preservation, descriptor-supported timeline/cancel fail-closed guard and Question/Feedback timeline/cancel descriptor declarations, P8 application-layer AgentExecutor adapter gate, adapter result preservation for output / interrupt / typed candidate payload refs, adapter formal-ref, formal-write-counter and repository/DB business-write metadata fail-closed guards, adapter fake-provider / fail-open fallback metadata fail-closed guard, `AgentRuntimeLoopPolicy` complete P8 required stop-condition fail-closed validation, facade-created start/resume/replay command `runtime_loop_policy` metadata, generic direct runtime missing-policy fail-closed gate, descriptor-supported resume/replay fail-closed guard, Feedback direct in-memory runner descriptor policy metadata fail-closed gate, Polish question direct runtime `interrupt_required` stop-condition coverage, Polish question concrete loop-policy caller/side-effect/tool-declared-forbidden-data enforcement, facade checkpoint-bound strict-base resume control-field/action/formal-ref gate, mandatory registered ToolDefinition authorization, Polish question concrete runtime ToolDefinition lookup, Polish question concrete checkpoint-bound HITL resume validation, Feedback PR8 provider trace gate runtime ToolDefinition lookup plus caller/permission/owner/side-effect/forbidden-data negative coverage, direct `authorize_tool_call()` architecture gate, `AgentSideEffectGuard` ToolDefinition caller / permission / side-effect / forbidden-data checks, read-only `AiOrchestrationFacade.replay_agent_run()` with original failure/interruption status metadata, refs-only trace comparison preservation including Feedback validation refs and replay side-effect counter fail-closed validation, P8 HITL service trigger matrix with checkpoint-bound resume validation, generic in-memory checkpoint-bound user-confirmation resume validation, generic direct `run_started` / `run_resumed` / `run_succeeded`, Feedback direct `run_started` / `run_succeeded`, and Question direct `run_started` / `interrupt_opened` / `run_resumed` / resumed `run_succeeded` P8 command ref matrix preservation, Feedback in-memory runner-bound five-trigger HITL emission with low-confidence trace refs, service-backed in-memory runner resume validation plus candidate/validation resume timeline refs, `AgentHandoffEnvelope`, AgentExecutor-bound source-result to target-plan handoff foundation, `execute_agent_handoff()` target AgentExecutor start, refs-only asset body descriptor handoff, target timeline handoff envelope ref visibility, adapter result/status handoff ref propagation, Feedback in-memory typed `feedback_candidate` and `asset_update_candidate` payloads, expanded `AgentExecutionTrace` plus recursive nested metadata filtering, Feedback status validation-ref trace surface and adapter P8 trace/timeline ref mapping including command metadata `tool_refs` / `policy_refs` / `provider_refs` / `validation_refs` / `handoff_refs` / `low_confidence_flags`, generic runtime start/resume/cancel refs metadata, concrete Question start/resume/cancel-event refs metadata including Question cancel checkpoint/validation ref separation, Feedback start/resume/cancel-event refs metadata, cancel zero-provider/formal-write counters, runtime DTO status taxonomy guard, Polish question application status taxonomy mapping, `AgentTraceBridge` non-DTO status guard, adapter metadata event status taxonomy guard, default-off `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED=false`, and full backend validation.
- Deferred: raw asset body transfer and formal asset composition/write semantics, future / indirect graph tool-loop expansion outside the covered facade start surfaces and Question/Feedback direct paths, remaining product-level runtime/orchestration wiring and runner-bound HITL emission / resume validation outside the already covered facade/generic/Question/Feedback paths, DB persistence/API status taxonomy beyond the runtime DTO and Polish question application status mapping, product-level Supervisor / L5 orchestration and proving complete trace population for remaining product/future runtime events outside current generic start/resume/cancel plus Feedback service-backed resume/start/cancel, Question start/resume/cancel and target handoff timeline coverage.
- Non-goal remains: Phase 11 Supervisor / Orchestrator, Phase 12 L5 release gate, formal F8/M8 release, prompt/provider/API/DB/frontend/domain-policy changes.

## L5 Controlled Multi-Agent Orchestration Target

Phase:

Phase 11

Status:

- Target locked by P11-W0.
- P11-W1 Option A contract-first Orchestrator slice is `contract_slice_complete_with_deferred_runtime_gaps`.
- P11-W2 runtime-hardening slice is `runtime_hardening_slice_complete_with_deferred_product_workflow`.
- Product workflow implementation not started.
- Not L5 release.

Required capabilities:

- registered Supervisor / Orchestrator Agent
- typed cross-agent goal decomposition
- cross-agent plan contract
- typed cross-agent handoff contract
- cross-agent state / checkpoint / replay contract
- cross-agent trace timeline
- bounded tool loop with `max_steps` / `max_retries` / `timeout` / `stop_conditions`
- HITL triggers for asset conflict, formal write, low confidence, ambiguous ownership and validation failed with partial result
- at least one end-to-end product workflow with three or more business agents
- candidate-only output boundary
- formal write remains Application Service -> Domain Policy -> Handoff

Non-claims:

- P8 typed handoff primitive is not product-level Supervisor / L5 orchestration.
- Question / Feedback planned workflows are not a three-or-more-business-agent product workflow.
- P11-W0 source wording is not implementation evidence.
- P11-W1 contract-only Orchestrator is not product multi-agent workflow or runtime execution evidence.
- P11-W1 does not close Phase 8 runtime gaps, `deferred_remote_ci_gap`, stale eval report metadata risk, real-provider quality certification or Phase 12 release gate.

P11-W1 contract catalog evidence:

- `interview_orchestrator_agent` is registered only through `build_default_agent_platform_l5_contract_registries()`.
- Cross-agent plan / step / handoff route / state / trace contracts are in `app.application.agents.contracts`.
- Orchestrator skills and tools are contract-only definitions and validate through the project-level registries.
- Phase 4 C1 Question / Feedback catalog remains backward-compatible and separate from the L5 contract builder.

P11-W2 runtime-hardening evidence:

- Route-bound cross-agent handoff validation fails closed on source/target mismatch, invalid candidate type, missing required trace refs, missing required validation refs, formal refs and unsafe metadata.
- Cross-agent resume validation requires checkpoint ref, non-negative base version, idempotency key, owner scope, interrupt ref and supported action.
- Cross-agent replay validation requires read-only, formal-write-blocked and zero provider/tool/repository/DB/formal-write metadata.
- Cross-agent trace/timeline mapping preserves plan, handoff, validation and candidate refs separately.
- HITL trigger validation covers formal write requested, asset conflict, low confidence, ambiguous ownership and validation-failed partial result control events.
- Evidence remains internal Agent Platform runtime-hardening only; it does not execute Orchestrator, implement product workflow, persist cross-agent state or change provider/prompt/API/DB/frontend/domain behavior.

Forbidden unless separately scoped:

- unbounded autonomous swarm
- Agent direct DB / repository write
- Tool direct repository exposure
- infrastructure business policy
- provider full prompt / full resume / full JD fallback
- prompt/provider/API/DB/frontend/domain behavior changes
- committed eval report rewrite
- remote CI claim without visible run/artifact

## L5 Eval, Hardening, and Release Gate Target

Phase:

Phase 12

Status:

- Target locked by P11-W0.
- Release gate not started.

Required capabilities:

- multi-agent regression suite
- cross-agent replay fixtures
- failure-mode regression cases
- L5 CI gate
- observability / trace report
- rollback policy
- failure triage policy
- remote CI artifact evidence
- human release decision

Non-claims:

- P9 replay/fixture eval foundation is not real-provider quality certification.
- `complete_with_deferred_remote_ci_gap` is not remote CI success.
- Phase 12 cannot release with hidden candidate/formal or provider fail-open gaps.

## Required Contracts

### AgentDefinition

```yaml
agent_id:
agent_name:
domain:
version:
maturity_level:
lifecycle_status:
mission:
user_goal:
autonomous_goal:
non_goals:
input_contract:
output_contract:
candidate_outputs:
formal_write_boundary:
skills:
tools:
memory_state:
planning_strategy:
guardrails:
HITL_triggers:
failure_semantics:
trace_contract:
eval_contract:
handoff_contract:
versioning_policy:
```

### SkillDefinition

```yaml
skill_id:
skill_name:
owner_agent_ids:
input_schema_id:
output_schema_id:
implementation_type:
deterministic_policy_refs:
llm_refs:
tool_refs:
timeout_policy:
retry_policy:
failure_semantics:
trace_events:
eval_refs:
```

### ToolDefinition

```yaml
tool_id:
tool_name:
input_schema_id:
output_schema_id:
permission_scope:
owner_scope:
side_effect_policy:
timeout_seconds:
retry_policy:
allowed_callers:
forbidden_data:
trace_events:
```

### AgentExecutionPlan

```yaml
plan_id:
agent_id:
run_id:
goal:
steps:
max_steps:
max_retries:
timeout_seconds:
stop_conditions:
repair_strategy:
fallback_strategy:
```

### AgentExecutionTrace

```yaml
trace_id:
agent_id:
run_id:
ai_task_id:
input_refs:
plan_refs:
skill_refs:
tool_refs:
policy_refs:
provider_refs:
candidate_refs:
validation_refs:
handoff_refs:
output_refs:
events:
```

### HandoffContract

```yaml
handoff_schema_id:
candidate_ref:
candidate_type:
payload_schema_id:
validation_refs:
quality_gate:
side_effect_key:
idempotency_key:
formal_write_preconditions:
rollback_policy:
user_confirmation_required:
```

### EvalContract

```yaml
eval_suite_ids:
dataset_refs:
grader_refs:
regression_cases:
minimum_pass_criteria:
ci_gate:
failure_triage_policy:
```

## Required Registries

### AgentDefinitionRegistry

Responsibilities:

- register AgentDefinition
- validate agent_id uniqueness
- expose definitions by agent_id
- list lifecycle_status
- map task_type to agent_id
- bind eval_suite_ids
- bind handoff_contract

Forbidden:

- executing Agent
- calling LLM
- accessing DB
- storing runtime state

### SkillRegistry

Responsibilities:

- register SkillDefinition
- validate schema refs
- validate owner_agent_ids
- expose skill by skill_id
- list skills by agent_id

Forbidden:

- executing skill logic directly
- calling repository
- deciding formal write

### ToolRegistry

Responsibilities:

- register ToolDefinition
- validate permission_scope
- validate side_effect_policy
- validate owner_scope
- expose tool by tool_id
- list tools by agent_id

Forbidden:

- direct repository exposure
- bypassing Application Service
- returning forbidden data

## AgentExecutor Port

AgentExecutor is a port, not necessarily LangGraph.

Required methods:

```python
start(context, command) -> AgentRunResult
resume(context, interrupt_ref, resume_payload) -> AgentRunResult
replay(context, checkpoint_ref) -> AgentReplayResult
get_status(run_id, owner_id) -> AgentRunStatus
get_timeline(run_id, owner_id, cursor, limit) -> AgentRunTimelinePage
cancel(run_id, owner_id, reason, actor_id) -> AgentRunStatus
```

Rules:

- Executor executes plans.
- Executor records trace.
- Executor returns candidate refs.
- Executor does not write formal business facts.
- Executor does not bypass handoff.

## Candidate-Only Rule

Allowed Agent outputs:

- question_candidate
- feedback_candidate
- asset_update_candidate
- progress_update_candidate
- weakness_candidate
- training_plan_candidate
- report_candidate
- review_candidate

Forbidden:

- formal question write
- formal feedback write
- formal asset update
- formal score update
- formal progress update

## Handoff Rule

Formal write path:

Application Service -> Domain Policy -> Handoff -> Repository / Transaction

Agent cannot skip this path.

## Provider Boundary Rule

Provider request must be:

- compact
- schema-bound
- redacted
- traceable
- fail-closed

Forbidden:

- full prompt asset fallback
- raw prompt
- system prompt
- developer prompt
- full resume
- full JD
- provider payload
- secrets

## Tool Side Effect Policy

Allowed side_effect_policy values:

- read_only
- candidate_write
- formal_write_handoff_only
- forbidden

Default:

read_only

## Phase 1 C0 Acceptance

C0 accepted only when:

- AgentDefinition contract exists or is explicitly scaffolded.
- SkillDefinition contract exists or is explicitly scaffolded.
- ToolDefinition contract exists or is explicitly scaffolded.
- AgentDefinitionRegistry exists or is explicitly scaffolded.
- SkillRegistry exists or is explicitly scaffolded.
- ToolRegistry exists or is explicitly scaffolded.
- AgentExecutor port exists or is explicitly scaffolded.
- Candidate-only rule is documented and tested or gated.
- Tool no repository exposure rule is documented and tested or gated.
- B is not marked as final target.

## Phase 4 C1 Acceptance

C1 accepted only when:

- `polish_question_agent` and `polish_feedback_agent` are registered in project-level `AgentDefinitionRegistry`.
- `catalog.py` is only a C1 registry aggregator; concrete Question / Feedback skill and tool definitions are not kept in the catalog file.
- Agent definition versions are stable semantic versions, schema versions describe contract shape, and catalog revision is the only phase/window marker.
- Registered `SkillDefinition` records include purpose, implementation_ref, preconditions, postconditions, fail-closed fallback policy, lifecycle status, definition version, schema version, and architecture test refs.
- Question Agent exposes only `question_candidate`.
- Feedback Agent exposes only `feedback_candidate` and `asset_update_candidate`.
- Question Agent has 8 SkillDefinition refs and 8 ToolDefinition refs resolved by project-level registries.
- Feedback Agent has 10 SkillDefinition refs and 9 ToolDefinition refs resolved by project-level registries.
- `SkillRegistry.list_by_agent_id` and `ToolRegistry.list_by_agent_id` return agent-scoped definitions.
- `ToolRegistry` rejects invalid `side_effect_policy`, missing forbidden data, and repository / DB / SQLAlchemy direct exposure.
- `AgentDefinitionRegistry.validate_references` fails closed on unknown skill refs, unknown tool refs, duplicate IDs, and invalid candidate outputs.
- Handoff contract includes payload schema, validation refs, quality gate, side-effect key, idempotency key, formal write preconditions, rollback policy, and user confirmation where required.
- Trace contract includes input / plan / skill / tool / policy / provider / candidate / validation / handoff / output refs and events, and forbids raw prompt / raw provider / full sensitive context.
- Architecture tests pass and validation evidence is recorded.
- Source backfill is recorded in `docs/goals/` and `docs/project-sources/`.

C1 does not accept:

- Question / Feedback runtime wiring to AgentExecutor.
- LangGraph / multi-agent runtime migration.
- Provider request builder, transport, or prompt rewrite.
- API / DB schema / domain policy behavior changes.
- Eval / CI regression gate completion.

## Anti-Drift Rules

The following are drift:

1. Stopping at B and marking Agent Platform done.
2. Creating Question-only registries that cannot support future Agents.
3. Tool directly exposing repository.
4. Agent writing formal fact.
5. Provider boundary accepting full prompt asset fallback.
6. Eval omitted from AgentDefinition.
7. Trace omitted from Skill / Tool execution.
