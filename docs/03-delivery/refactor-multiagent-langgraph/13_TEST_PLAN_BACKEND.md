---
title: 后端测试脚本实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/test-plan-backend
---

# 后端测试脚本实施计划

## 1. 文档目的

本文规划 PR2-PR8 后端测试文件、方法名、arrange / act / assert、fake data、DB writes、redaction 和运行命令，保证 AI Runtime、Facade、LangGraph adapter、LLM trace、interrupt / replay、API、redaction 和 architecture boundary 可直接进入实现。

## 2. 输入来源

- active docs：`API_SPEC.md`、`PERSISTENCE_MODEL.md`、`APPLICATION_FLOW_SPEC.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`
- 当前 `tests/api` 结构只读盘点
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`、`05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md`、`10_DATA_MODEL_AND_MIGRATION_PLAN.md`、`11_BACKEND_API_AND_SCHEMA_PLAN.md`
- 当前测试映射：已有 `tests/api/test_architecture_boundaries.py`、`test_job_match_api.py`、`test_polish_api.py`、`test_polish_feedback_contract.py`、`test_polish_question_llm.py`、`test_persistence_repositories.py`、`test_llm_runtime.py`、`test_route_inventory.py`。

## 3. 当前状态

当前后端已有 API、architecture boundary、LLM runtime、polish、candidate、route inventory、DB schema bootstrap 等测试线索。PR1 不新增测试文件，只规划目标测试。

## 4. 目标输出

输出每个目标测试文件的测试目标、关键 method 名称占位、arrange/act/assert、fake data、expected DB writes、expected redaction behavior 和运行命令。

## 5. 必须覆盖范围

### 5.1 PR2 runtime repository tests

| Test file | Test method | Arrange | Act | Assert | Fake data | Expected DB writes | Redaction |
|---|---|---|---|---|---|---|---|
| `tests/api/test_agent_run_repository.py` | `test_agent_run_repository_records_node_timeline_and_interrupts` | build SQLite session factory; create owner A run, two node runs, one interrupt | call repository `create_run`, `record_node_started`, `record_node_completed`, `create_interrupt`, `list_timeline` | timeline sorted by time; node status preserved; interrupt event has `interrupt_id`; `agent_run_id` returned | `run_owner_a`, `graph=job_match_graph`, `node=score_resume_fit` | `agent_runs`, `agent_node_runs`, `agent_interrupts` | event summary has no checkpoint / AgentState fields |
| `tests/api/test_agent_run_repository.py` | `test_agent_run_repository_filters_by_owner` | seed owner A and owner B runs with same graph | owner A repository query for owner B run | returns `None` or domain not found; no cross-owner timeline rows | `run_owner_a`, `run_owner_b` | runtime rows for both owners | no cross-owner data in result |
| `tests/api/test_llm_call_repository.py` | `test_llm_call_repository_records_summary_without_raw_payload` | create fake LLM call with forbidden strings in request / response body | save sanitized summary and fetch by owner | `request_hash` / `response_hash` exist; `prompt`, `completion`, `provider_payload`, `messages` absent | text markers: `RAW_PROMPT_SHOULD_NOT_LEAK`, `RAW_COMPLETION_SHOULD_NOT_LEAK`, `PROVIDER_PAYLOAD_SHOULD_NOT_LEAK` | `llm_calls`, `llm_call_payloads` or equivalent summary rows | forbidden markers absent from fetched DTO |
| `tests/api/test_llm_call_repository.py` | `test_llm_call_repository_enforces_retention_and_owner` | seed expired and active calls for owner A/B | call repository retention filter and owner get | expired hidden or marked expired; owner A cannot fetch owner B | `llm_active_a`, `llm_expired_a`, `llm_active_b` | `llm_calls` | no raw payload in expired or denied result |
| `tests/api/test_idempotency_records.py` | `test_idempotency_replays_same_body_and_conflicts_different_body` | seed idempotency key for actor/method/path/body hash | replay same body then different body | same body returns first response ref; different body returns domain `idempotency_conflict` | `Idempotency-Key=idem_runtime_001` | idempotency record table or equivalent `api_request_traces` | request body hash only; no body text |

Run command:

```bash
.venv/bin/python -m pytest tests/api/test_agent_run_repository.py tests/api/test_llm_call_repository.py tests/api/test_idempotency_records.py -q
```

### 5.2 PR3 facade / contract / architecture tests

| Test file | Test method | Arrange | Act | Assert | Fake data | Expected DB writes | Redaction |
|---|---|---|---|---|---|---|---|
| `tests/api/test_agent_contracts.py` | `test_agent_contracts_do_not_expose_langgraph_state_to_core` | instantiate `AiTaskStatusResponse`, `AgentRunSummaryResponse`, `AgentTimelineEvent` | serialize DTOs | serialized keys exclude forbidden set | fake task/run refs | none | no `AgentState`, checkpoint, Prompt, completion, provider payload |
| `tests/api/test_ai_orchestration_facade.py` | `test_facade_start_job_match_returns_task_ref_without_langgraph_leak` | fake runner, fake repository, owner scoped command | call `start_job_match_analysis` | result has `ai_task_id`, `agent_run_id`, no concrete LangGraph object | `binding_ref`, `resume_version_ref`, `job_version_ref` | `ai_tasks`, `agent_runs` if integration mode | no raw prompt |
| `tests/api/test_architecture_boundaries.py` | `test_core_business_does_not_import_langgraph_or_agent_runtime` | AST scan `apps/api/app/domain`, core `application/*` excluding `application/ai` and `application/agents` | collect imports | violations list empty | N/A | none | N/A |
| `tests/api/test_architecture_boundaries.py` | `test_api_schema_does_not_import_langgraph_state` | AST scan `apps/api/app/schemas` and `apps/api/app/api/v1` | collect imports | schemas do not import `langgraph`, `AgentState`, checkpoint modules | N/A | none | N/A |

Run command:

```bash
.venv/bin/python -m pytest tests/api/test_agent_contracts.py tests/api/test_ai_orchestration_facade.py tests/api/test_architecture_boundaries.py -q
```

### 5.3 PR4 runtime API / fake graph / redaction tests

| Test file | Test method | Arrange | Act | Assert | Fake data | Expected DB writes | Redaction |
|---|---|---|---|---|---|---|---|
| `tests/api/test_agent_graph_runner.py` | `test_agent_graph_runner_start_resume_replay_contract` | fake graph emits queued, running, interrupt, resumed, succeeded events | start run, resume interrupt, replay timeline | status transitions match; replay deterministic; result refs stable | `fake_runtime_graph`, interrupt `int_fake_001` | `agent_runs`, `agent_node_runs`, `agent_interrupts`, checkpoint refs | timeline sanitized |
| `tests/api/test_langgraph_checkpointer_factory.py` | `test_checkpointer_factory_returns_ref_not_business_truth` | configure checkpointer namespace and thread id | build checkpoint ref and store via fake checkpointer | API-facing ref has namespace hash / thread ref only; no payload | `run_fake_checkpoint_001` | checkpoint table managed by adapter or ref table | no checkpoint payload |
| `tests/api/test_agent_runtime_api.py` | `test_agent_run_status_is_owner_scoped_and_hides_internal_state` | isolated FastAPI app with owner A/B; seed run for owner A | owner A GET status; owner B GET status | owner A 200 envelope; owner B 404 `not_found_or_inaccessible`; response has `request_id`, `trace_id`, `resource_type=agent_run` | `run_owner_a` | read only | forbidden keys absent |
| `tests/api/test_agent_runtime_api.py` | `test_agent_run_timeline_is_owner_scoped_and_sanitized` | seed node events containing forbidden marker in internal payload | GET timeline | events contain summary/status refs; forbidden marker absent; cursor meta present | `RAW_AGENT_STATE_SHOULD_NOT_LEAK` | read only | no AgentState/checkpoint/raw |
| `tests/api/test_agent_interrupt_replay.py` | `test_resume_interrupt_requires_owner_schema_and_audit` | seed interrupted run for owner A; build resume request | POST resume with idempotency key | 202 envelope `resource_type=ai_task`; audit ref exists; interrupt version checked | `base_interrupt_version_ref=int_ver_1` | `agent_interrupts`, audit, idempotency | resume payload body not logged |
| `tests/api/test_agent_interrupt_replay.py` | `test_resume_interrupt_replays_idempotent_same_body_and_conflicts_different_body` | first resume accepted | repeat same key/body; repeat same key/different body | same returns same `ai_task_id`; different returns 409 `idempotency_conflict` | `idem_interrupt_001` | idempotency record | body hash only |
| `tests/api/test_sensitive_payload_redaction.py` | `test_sensitive_payload_never_reaches_logs_checkpoint_or_api` | fake graph node tries to emit forbidden markers into timeline, LLM summary and checkpoint summary | run fake graph then fetch API status/timeline/summary | every API/log-like captured string lacks forbidden markers | `RAW_PROMPT_SHOULD_NOT_LEAK`, `RAW_COMPLETION_SHOULD_NOT_LEAK`, `PROVIDER_PAYLOAD_SHOULD_NOT_LEAK` | sanitized summaries only | forbidden markers absent |

Run command:

```bash
.venv/bin/python -m pytest tests/api/test_agent_graph_runner.py tests/api/test_langgraph_checkpointer_factory.py tests/api/test_agent_runtime_api.py tests/api/test_agent_interrupt_replay.py tests/api/test_sensitive_payload_redaction.py -q
```

### 5.4 PR5 JobMatch Graph tests

| Test file | Test method | Arrange | Act | Assert | Fake data | Expected DB writes | Redaction |
|---|---|---|---|---|---|---|---|
| `tests/api/test_job_match_graph.py` | `test_job_match_graph_builds_owner_scoped_source_bundle_and_result_refs` | seed owner scoped resume/job/binding; fake runner | start `job_match_graph` through facade | result refs include `JobMatchAnalysis` and `ScoreResult`; no direct formal Weakness write | owner A binding | `ai_tasks`, `agent_runs`, job match result tables | no Prompt/provider payload |
| `tests/api/test_job_match_graph.py` | `test_job_match_graph_low_confidence_is_visible_and_not_exact_probability` | fake graph returns low evidence and no exact probability | run graph and read result API | `status=low_confidence` or low confidence flags visible; no exact pass probability field | low evidence resume/job | `low_confidence_flags`, score candidate/result as designed | no hidden scoring rules |
| `tests/api/test_job_match_api.py` | `test_job_match_graph_preserves_existing_api_owner_and_validation_errors` | reuse existing isolated job match app | create and read analysis with owner A/B and invalid payload | existing 404/422 behavior preserved | current fixtures | current job match rows | no new raw fields |

Run command:

```bash
.venv/bin/python -m pytest tests/api/test_job_match_graph.py tests/api/test_job_match_api.py -q
```

### 5.5 PR6 Polish Question Graph tests

| Test file | Test method | Arrange | Act | Assert | Fake data | Expected DB writes | Redaction |
|---|---|---|---|---|---|---|---|
| `tests/api/test_polish_question_graph.py` | `test_polish_question_graph_keeps_existing_question_api_contract` | seed polish session and progress node; fake graph output | POST `/api/v1/polish-sessions/{session_id}/questions` | 202 envelope shape compatible with current `PolishTaskStatus`; detail contains generated question | owner A session | `ai_tasks`, `agent_runs`, `questions` | no raw LLM fields |
| `tests/api/test_polish_question_graph.py` | `test_polish_question_graph_rejects_cross_owner_session` | owner A session; owner B actor | POST question generation | 404 `not_found_or_inaccessible` or owner-safe error | owner A/B actors | none | no session data leaked |
| `tests/api/test_polish_question_graph.py` | `test_polish_question_graph_timeline_contains_sanitized_question_generation_events` | fake graph with internal Prompt marker | start question graph and fetch timeline | timeline shows node summaries and validation refs; marker absent | `RAW_PROMPT_SHOULD_NOT_LEAK` | runtime rows | no Prompt/completion/provider payload |
| `tests/api/test_polish_api.py` | `test_polish_question_generation_records_selected_category_context` | keep existing test fixture | call existing endpoint | metadata behavior preserved under graph adapter | current fixture | current question metadata | no regression |
| `tests/api/test_polish_question_llm.py` | `test_polish_question_llm_output_is_not_exposed_as_raw_provider_payload` | fake LLM output with extra provider fields | generate question | API data has question text / refs only; provider fields absent | fake provider payload | question + trace summary | no raw provider payload |

Run command:

```bash
.venv/bin/python -m pytest tests/api/test_polish_question_graph.py tests/api/test_polish_api.py tests/api/test_polish_question_llm.py -q
```

### 5.6 LLM summary API tests

| Test file | Test method | Arrange | Act | Assert | Fake data | Expected DB writes | Redaction |
|---|---|---|---|---|---|---|---|
| `tests/api/test_llm_call_summary_api.py` | `test_llm_call_summary_requires_owner_and_returns_sanitized_hashes` | isolated app; seed owner A/B LLM calls | owner A GET own summary; owner B GET owner A summary | owner A gets `request_hash`, `response_hash`, `usage_summary`; owner B 404 | fake llm ids | read only | no raw body |
| `tests/api/test_llm_call_summary_api.py` | `test_llm_call_summary_never_returns_prompt_completion_or_provider_payload` | seed call with forbidden internal payload | GET summary | serialized response lacks forbidden keys and marker values | forbidden markers | read only | marker absent in JSON |

Run command:

```bash
.venv/bin/python -m pytest tests/api/test_llm_call_summary_api.py -q
```

PR2-PR8 可追加业务 graph tests，但以上文件是 runtime 最小回归骨架。

## 6. 与 active docs 的关系

测试断言以 active API/DATA/PROMPT/SECURITY/PERSISTENCE 为依据，不从 checkpoint 推导业务事实，不把 fake provider 输出质量当真实 provider 验收。

## 7. 非目标

- 不默认调用真实 provider。
- 不要求 PR2 一次完成所有业务 graph。
- 不把测试全绿等同 security/privacy release Go。

## 8. 目标 PR 使用方式

每个 PR 只开启本 PR 对应测试。跨 PR 测试在对应 PR 启动前只能作为计划项，不能伪装通过。

## 9. Definition of Done

- 用户指定测试文件清单已覆盖。
- 每个文件有目标、method、arrange/act/assert、fake data、DB writes、redaction 和运行命令占位。
- redaction、candidate/formal、checkpoint 非 truth source 均有负例。
