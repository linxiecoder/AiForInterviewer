---
title: 后端测试脚本实施计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/test-plan-backend
---

# 后端测试脚本实施计划

## 1. 文档目的

本文规划 PR2-PR8 后端测试文件骨架，保证 AI Runtime、Facade、LangGraph adapter、LLM trace、interrupt/replay、API、redaction 和 architecture boundary 可验证。

## 2. 输入来源

- active docs：`API_SPEC.md`、`PERSISTENCE_MODEL.md`、`APPLICATION_FLOW_SPEC.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`
- 当前 `tests/api` 结构只读盘点
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`、`05_BACKEND_LLM_TRACE_PERSISTENCE_PLAN.md`、`10_DATA_MODEL_AND_MIGRATION_PLAN.md`、`11_BACKEND_API_AND_SCHEMA_PLAN.md`

## 3. 当前状态

当前后端已有 API、architecture boundary、LLM runtime、polish、candidate、route inventory、DB schema bootstrap 等测试线索。PR1 不新增测试文件，只规划目标测试。

## 4. 目标输出

输出每个目标测试文件的测试目标、关键 method 名称占位、arrange/act/assert、fake data、expected DB writes、expected redaction behavior 和运行命令。

## 5. 必须覆盖范围

| Test file | 测试目标 | 关键 test method 名称占位 | Arrange / Act / Assert 占位 | Fake data 占位 | Expected DB writes 占位 | Expected redaction behavior | 运行命令占位 |
|---|---|---|---|---|---|---|---|
| `tests/api/test_agent_contracts.py` | DTO/enum/port contract | `test_agent_contracts_do_not_expose_langgraph_state_to_core` | arrange contract DTO -> act serialize -> assert no raw fields | fake graph/task ids | none | no AgentState/raw payload | `.venv/bin/python -m pytest tests/api/test_agent_contracts.py -q` |
| `tests/api/test_agent_graph_runner.py` | `AgentGraphRunner` port | `test_agent_graph_runner_start_resume_replay_contract` | fake runner start/resume/replay -> assert status/timeline | fake graph events | `agent_runs` optional in integration | sanitized result | same |
| `tests/api/test_langgraph_checkpointer_factory.py` | checkpointer factory | `test_checkpointer_factory_returns_ref_not_business_truth` | config -> build -> assert namespace/thread id | fake run context | `agent_checkpoint_refs` | no checkpoint payload in API | same |
| `tests/api/test_persisted_llm_transport.py` | persisted transport | `test_persisted_transport_records_summary_without_raw_payload` | fake request/response -> call -> assert db summary | fake completion with forbidden text | `llm_calls`, sanitized `llm_call_payloads` | raw prompt/completion absent | same |
| `tests/api/test_llm_call_repository.py` | LLM call repository | `test_llm_call_repository_enforces_owner_and_retention` | owner A/B calls -> query -> assert isolation | fake calls | `llm_calls`, `llm_call_payloads` | raw refs hidden | same |
| `tests/api/test_agent_run_repository.py` | run/node/interrupt repository | `test_agent_run_repository_records_node_timeline` | create run/node/interrupt -> read timeline | fake node events | `agent_runs`, `agent_node_runs`, `agent_interrupts` | timeline sanitized | same |
| `tests/api/test_agent_graphs.py` | graph skeleton contract | `test_graph_registry_maps_task_types_to_graphs_and_contracts` | registry -> resolve -> assert contract ids | graph names | none | no raw prompt | same |
| `tests/api/test_agent_interrupt_replay.py` | interrupt/resume/replay | `test_resume_interrupt_requires_owner_schema_and_audit` | interrupt -> resume -> replay -> assert audit | fake resume payload | `agent_interrupts`, audit, checkpoint refs | no raw resume payload in log | same |
| `tests/api/test_agent_runtime_api.py` | runtime endpoints | `test_agent_run_timeline_is_owner_scoped_and_sanitized` | API client owner A/B -> get timeline | fake run | read only or runtime rows | no AgentState/checkpoint/raw | same |
| `tests/api/test_sensitive_payload_redaction.py` | sensitive payload redaction | `test_sensitive_payload_never_reaches_logs_checkpoint_or_api` | inject forbidden tokens -> run fake graph -> scan response/logs | raw prompt/completion/provider payload | sanitized summary only | forbidden strings absent | same |
| `tests/api/test_architecture_boundaries.py` | import boundary | `test_core_business_does_not_import_langgraph` | scan imports -> assert allowed paths only | N/A | none | N/A | `.venv/bin/python -m pytest tests/api/test_architecture_boundaries.py -q` |

PR2-PR8 可追加业务 graph tests，但以上文件是 runtime 最小回归骨架。

## 6. 与 active docs 的关系

测试断言以 active API/DATA/PROMPT/SECURITY/PERSISTENCE 为依据，不从 checkpoint 推导业务事实，不把 fake provider 输出质量当真实 provider 验收。

## 7. 非目标

- 不默认调用真实 provider。
- 不要求 PR2 一次完成所有业务 graph。
- 不把测试全绿等同 security/privacy release Go。

## 8. 后续 PR 使用方式

每个 PR 只开启本 PR 对应测试。未实现的跨 PR 测试可以保留为后续计划，但不能伪装通过。

## 9. Definition of Done

- 用户指定测试文件清单已覆盖。
- 每个文件有目标、method、arrange/act/assert、fake data、DB writes、redaction 和运行命令占位。
- redaction、candidate/formal、checkpoint 非 truth source 均有负例。

