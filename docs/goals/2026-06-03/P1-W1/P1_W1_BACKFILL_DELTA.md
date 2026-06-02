---
title: P1_W1_BACKFILL_DELTA
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-03/p1-w1/backfill-delta
---

# P1-W1 Backfill Delta

## Purpose

本文件只记录 P1-W1 执行后建议回填到 source-pack Matrix / Risk / Decision 的 delta。按本窗口约束，本轮不直接修改 source-pack docs、active delivery docs 或 archive。

## Proposed Matrix Updates

| ID | Proposed status | Evidence | Remaining gap |
| --- | --- | --- | --- |
| AGT-001 | C0_DONE | `app.application.agents.contracts` 新增 Agent / Skill / Tool / Plan / Trace / Handoff / Eval contracts；`tests/architecture/test_agent_platform_c0_boundary.py` 通过 | 未注册业务默认 definitions；未接入 Question / Feedback runtime |
| AGT-002 | C0_DONE | `AgentDefinition`、`SkillDefinition`、`ToolDefinition` 字段覆盖 P1-W1 contract requirements | 字段语义尚未映射到完整 source-pack registry；无 production prompt / provider integration |
| AGT-003 | C0_DONE | `AgentDefinitionRegistry`、`SkillRegistry`、`ToolRegistry` 支持 non-empty ID、duplicate fail-closed、`get()`、`list()`；architecture tests 通过 | 暂无持久化 registry、配置加载或 default registry bootstrap |
| AGT-004 | C0_DONE | `app.application.agents.runtime.AgentExecutor` Protocol 包含 `start`、`resume`、`replay`、`get_status`、`get_timeline`、`cancel`，且与 `ai_runtime.AgentGraphRunner` 独立 | 只定义 port，不实现 executor，不接 LangGraph，不写 formal business facts |
| AGT-005 | C0_DONE | `HandoffContract`、`EvalContract`、`AgentExecutionTrace`、candidate-only `AgentExecutionResult` 已存在并由 tests 锁定 | 未实现 handoff executor、confirmation flow 或 eval runner |
| DDD-001 | PARTIAL_DONE | 新增 architecture rails：agent platform 禁止 infra/API/DB/LLM/provider/LangGraph imports；domain 禁止 infra/API/application.llm imports | 仍不是全仓架构矩阵；未覆盖所有 application/domain dependency directions |
| DDD-002 | PARTIAL_DONE | `PolishSessionApplicationService.bootstrap()` owns `polish_skeleton` behavior；split regression 通过 | `PolishUseCases` 仍持有大部分 orchestration；Question/Feedback 迁移明确不在 P1-W1 |
| DDD-003 | DONE_FOR_C0 | `tests/architecture` 新增 C0 boundary tests；required API regression tests 通过 | 后续窗口需为 default definitions、handoff、runtime wiring 增加更具体 tests |
| WIN-001 | DONE | Scope stayed within GOAL0603 allowlist；forbidden prompt/provider/DB/API/runtime files were not modified | 未运行 broad suite；后续窗口如扩大行为面需补 broad smoke |

## Proposed Risk Updates

| Risk | Proposed disposition | Evidence / rationale |
| --- | --- | --- |
| Agent Platform mistaken as complete runtime | Keep Open | P1-W1 only adds C0 contracts / registries / port. Report explicitly states no runtime wiring. |
| ToolRegistry exposing repositories | Mitigated for C0 | Registry only stores `ToolDefinition`; tests reject arbitrary object registration and assert no repository attributes. |
| Agent output bypassing Handoff into formal facts | Mitigated for C0 contract shape | `AgentExecutionResult` has `candidate_refs` and no `formal_refs` / `formal_outputs`; formal boundary is represented on `AgentDefinition` and `HandoffContract`. |
| Agent platform importing infra / provider / DB | Mitigated for C0 | Architecture test and `rg` scan found no forbidden imports under `app.application.agents`. |
| Polish facade convergence causing behavior drift | Mitigated for P1-W1 | Only `bootstrap()` constant ownership moved; targeted split and question phase1 tests passed. |
| DDD rails false sense of full coverage | Keep Open | New rails cover agent platform and domain forbidden imports only; they do not replace future full dependency matrix checks. |

## Proposed Decision Updates

- Decision: `app.application.agents` is the project-level Agent Platform namespace for C0 contracts, definitions, registries, runtime port and handoff contract.
- Decision: C0 Agent Platform remains pure application code and must not import infrastructure, FastAPI, DB/migration libraries, provider SDKs, `app.application.llm`, or LangGraph.
- Decision: `app.application.ai_runtime` remains the existing graph runtime namespace; P1-W1 does not rename, replace, or break existing graph runtime APIs.
- Decision: AgentExecutor is a port only in P1-W1. Runtime implementation, persistence, LangGraph bridge, eval runner and formal handoff writer require later explicit windows.
- Decision: Polish facade convergence proceeds by moving low-risk behavior into focused services while keeping `PolishUseCases` as compatibility facade. Question/Feedback orchestration remains out of scope for P1-W1.

## Validation Evidence

- `tests/architecture` -> `6 passed`
- `tests/api/test_polish_application_service_split.py` -> `4 passed`
- `tests/api/test_polish_question_refactor_phase1.py` -> `60 passed`
- `compileall` for new agent package and changed session service -> passed
- `git diff --check` -> passed
- forbidden import scan for `app.application.agents` and `app.domain` -> no matches

## Remaining Gaps

- No default AgentDefinition / SkillDefinition / ToolDefinition catalog entries.
- No AgentExecutor implementation.
- No registry persistence or configuration loading.
- No Question / Feedback integration into Agent Platform runtime.
- No provider, prompt, DB, API, LangGraph, or domain policy changes by design.
- No broad suite validation in this window.
