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

#### 3.3.1 `GraphDescriptor` DTO

`GraphDescriptor` 是 PR3 registry / PR6 Graph Configuration Backend 的 project-owned DTO，不包含 LangGraph internals、compiled graph、AgentState、checkpoint payload、provider secret、model key、raw prompt、raw completion 或 provider payload。

| Field | Required rule |
|---|---|
| `graph_name` | Stable graph id, e.g. `polish_question_graph`; no dynamic Python import path |
| `graph_version` | Version string for descriptor compatibility |
| `capability` | Registered capability, e.g. polish_question / pressure_session / report_generation |
| `lifecycle_status` | enum: active / disabled / planned / placeholder / deferred |
| `runtime_flag_key` | Flag resolved by facade / registry / runner entry only |
| `default_enabled` | Always false unless later PR explicitly accepts enablement |
| `supported_entrypoints` | start / resume / replay / timeline as applicable |
| `supported_outputs` | result refs, candidate refs, suggestion refs, interrupt refs; no formal object body |
| `prompt_contract_ids` | Canonical `P-*` contract ids |
| `eval_suite_ids` | Prompt / graph evaluation suite refs |
| `resume_schema_ids` | Resume payload schema refs by interrupt type |
| `interrupt_types` | Registered interrupt taxonomy |
| `required_permissions` | Owner/admin/user permissions required to start/resume/read |
| `visibility` | owner_only / admin_config / hidden_placeholder |
| `health_summary_refs` | Sanitized health refs only |
| `config_schema_ref` | PR6 graph config schema ref |
| `implementation_pr` | PR number / phase expected to implement or migrate |
| `migration_status` | not_started / direct_path_retained / parity_testing / migrated / rolled_back |

Current descriptor status:

- JobMatch / ResumeAnalysis descriptors are PR8 deferred / placeholder.
- Polish can become active only after PR5 migration and parity gates.
- Pressure remains PR8 or separate authorized Pressure PR.
- PR3 / PR4 must not create `business_graphs` implementation from descriptor metadata.

### 3.3.2 `runtime_flags.py`

All runtime / graph flags default false. Graph nodes do not read flags directly; only facade, registry, or runner entry can resolve enablement and must audit enable decisions.

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `resolve_runtime_flag` | flag key, actor, graph descriptor, test override context | resolved decision | write sanitized enablement audit when decision enables runtime | unknown flag, unauthorized persisted config | default false; audit enabled decision |
| `resolve_graph_flag` | graph descriptor, actor, optional persisted config | resolved graph decision | write graph enablement audit | graph disabled, unauthorized config | graph node never reads flag directly |
| `is_real_provider_enabled` | provider gate context | boolean | audit only when enabled | unauthorized real provider use | real provider gate independent and default false |
| `explain_flag_decision` | decision ref | sanitized explanation | read only | not found | no secrets in explanation |

Flag source priority:

1. test override.
2. explicit environment / settings override.
3. persisted graph config if authorized in PR6+.
4. hardcoded default false.

Rollback disable behavior:

- Disabling `AIFI_AI_RUNTIME_ENABLED` must route new work back to legacy direct path or return sanitized disabled status.
- Disabling `AIFI_AI_RUNTIME_LANGGRAPH_ENABLED` must prevent concrete adapter / fake graph execution while keeping contract DTOs importable.
- Disabling graph-specific flags must leave descriptor metadata readable but not executable.
- Real provider gate remains independent from graph enablement and defaults false.

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

PR3 / PR4 only define `AgentPersistenceHandoff` contract, interface, DTO and validation. Real Core formal write paths are PR5+ or the corresponding authorized business migration PR. PR3 / PR4 must not call Core formal write repositories, and PR4 LangGraph adapter must not bypass handoff to write Core Business tables directly.

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `prepare_handoff` | validated run result, candidate refs, trace refs | handoff plan | none | missing validation/trace | requires validation and trace |
| `write_question_result` | accepted question plan | question ref | PR5+ Core question command only; PR3 / PR4 stub validates and rejects real write | duplicate/source unavailable | PR3 / PR4 no formal write repository call |
| `write_feedback_result` | feedback / score / candidate plan | feedback / score refs | PR5+ Core feedback/scoring command only; PR3 / PR4 stub validates and rejects real write | validation failed | candidates stay non-formal |
| `write_report_result` | report sections and score refs | report refs | PR8 or authorized report PR Core command only; PR3 / PR4 stub validates and rejects real write | copy boundary violation | no export artifact |
| `write_review_result` | review plan and candidate refs | review refs | PR8 or authorized review PR Core command only; PR3 / PR4 stub validates and rejects real write | privacy validation failed | candidate-only |
| `write_candidate_result` | weakness/asset/training candidate plan | candidate refs | PR8 or authorized candidate PR candidate/suggestion write only; PR3 / PR4 stub validates and rejects real write | formal write attempted | no formal object |
| `finalize_after_confirmation` | confirmation action and target command | formal ref | PR5+ / PR8 Core confirmation/formal command only; PR3 / PR4 stub validates and rejects real write | stale candidate | user confirmation required |

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

### 3.9 Checkpointer / serializer contracts

PR4 fake graph checkpoint only verifies ref / metadata behavior. Checkpoint payload never enters `AgentCheckpointRef`, API response, normal trace, timeline, copy content, or Core Business read model.

| Method | Inputs | Outputs | Side effects | Errors | Tests |
|---|---|---|---|---|---|
| `build_langgraph_checkpointer` | DB/session factory, namespace policy, serializer | checkpointer instance | none until runtime writes checkpoint | missing namespace policy, unsafe serializer | LangGraph imports isolated to infra root |
| `record_checkpoint_ref` | agent_run ref, namespace, thread_id, checkpoint_id, version, metadata | `AgentCheckpointRef` | write checkpoint ref metadata only | payload present, owner mismatch | checkpoint ref stores no payload |
| `restore_checkpoint_ref` | checkpoint ref, actor, replay mode | checkpoint metadata / adapter handle | read only | ref expired, owner mismatch, payload unavailable | production resume fail-closed if unsafe |
| `expire_checkpoint_ref` | checkpoint ref, reason | expired ref | mark expired and audit summary | not found, owner mismatch | expired ref not used for resume |
| `build_encrypted_serializer` | encryption policy, redaction policy | serializer | none | raw debug disabled, missing key policy | serializer does not expose raw state |
| `serialize_state` | safe state, redaction profile | encrypted / adapter payload | adapter-internal only | raw prompt/completion/provider/source body detected | rejects raw state payload |
| `deserialize_state` | adapter payload, replay policy | safe state handle | adapter-internal only | raw field detected, schema mismatch | replay read-only unless authorized |
| `sanitize_checkpoint_metadata` | checkpoint metadata | sanitized metadata summary | none | raw markers detected | metadata contains only namespace/thread/checkpoint/version/hashes/timestamps |
| `reject_raw_state_payload` | state payload or metadata | rejection result | audit policy violation | N/A | raw prompt, raw completion, provider payload, full source body rejected |

Allowed checkpoint metadata fields:

- namespace.
- thread_id.
- checkpoint_id.
- checkpoint_version.
- state_hash / metadata_hash.
- serializer_version.
- created_at / expires_at.

Forbidden checkpoint / serializer content:

- raw prompt.
- raw completion.
- provider request / response payload.
- system prompt.
- token / cookie / secret.
- hidden scoring rule.
- full resume / JD / answer / report / review source body.

## 4. Import and dependency constraints

| Layer | Allowed | Forbidden |
|---|---|---|
| `application/ai_runtime/**` | project DTO, ports, policy, Core command ports by abstraction | `langgraph`, `langchain`, SQLAlchemy concrete session, provider SDK |
| `infrastructure/ai_runtime/langgraph/**` | LangGraph / LangChain runtime API, checkpointer, serializer, application runtime contracts | Core formal write bypass, API response assembly |
| Core Business | `AiOrchestrationFacade` contract when AI generation is needed | graph node, AgentState, checkpoint schema, provider payload |

## 5. PR3 / PR4 contract-to-test matrix

| PR | Test | Required assertion |
|---|---|---|
| PR3 | `tests/api/test_agent_contracts.py` | contract types contain no LangGraph / LangChain / AgentState concrete types |
| PR3 | `tests/api/test_ai_orchestration_facade.py` | facade returns refs only and never returns raw prompt、raw completion、provider payload、checkpoint payload or formal object body |
| PR3 | `tests/api/test_agent_graph_runner.py` | application port signatures are project-owned DTOs; no concrete adapter import |
| PR3 | `tests/api/test_agent_registry.py` | registry default-off; GraphDescriptor fields frozen; JobMatch / ResumeAnalysis placeholder/deferred; Polish not active before PR5 |
| PR3 | `tests/api/test_runtime_flags.py` | all runtime / graph flags default false; source priority is test override -> explicit environment/settings -> PR6 persisted config -> default false; enable decisions audited |
| PR3 | `tests/api/test_agent_interrupt_replay.py` | interrupt resume schema / owner / base version / idempotency enforced |
| PR3 | `tests/api/test_agent_handoff.py` | handoff no formal write; PR3 / PR4 stubs reject Core formal write repository calls |
| PR3 | `tests/api/test_agent_side_effect_guard.py` | raw-off and formal-write block enforced with `side_effect_key` idempotency |
| PR3 | `tests/api/test_architecture_boundaries.py` | application layer has no LangGraph import, infra import, provider SDK or SQLAlchemy concrete session |
| PR4 | `tests/api/test_architecture_boundaries.py` | LangGraph imports only under `apps/api/app/infrastructure/ai_runtime/langgraph/**` |
| PR4 | `tests/api/test_agent_fake_runtime.py` | fake graph start / resume / replay / timeline are sanitized and default-off |
| PR4 | `tests/api/test_agent_checkpointer.py` | checkpointer writes refs only; checkpoint payload never enters `AgentCheckpointRef` |
| PR4 | `tests/api/test_agent_serializer.py` | serializer rejects raw state containing prompt、completion、provider payload or full source body |
| PR4 | `tests/api/test_agent_runtime_api.py` | `stream_events` / status / timeline responses are sanitized; no AgentState or checkpoint payload |
| PR4 | `tests/api/test_persisted_llm_transport.py` | before-call trace write failure fail-closes and prevents provider call |
| PR4 | `tests/api/test_provider_gate.py` | real provider gate disabled by default and independent from graph enablement |
| PR4 | `tests/api/test_agent_replay.py` | replay is read-only; no handoff or formal write |
| PR4 | `tests/api/test_no_business_graph_implementation.py` | no business graph implementation, no Polish/Pressure/JobMatch migration, no formal write bypass |

Each PR3 / PR4 test must include raw-off, owner scope, checkpoint non-truth-source, idempotency or candidate/formal negative assertions where applicable.
