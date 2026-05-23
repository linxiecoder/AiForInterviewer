---
title: PR 拆分与实施顺序
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/pr-breakdown-and-implementation-sequence
---

# PR 拆分与实施顺序

## 1. 文档目的

本文定义 PR1-PR8 的实施顺序、scope、allowed files、forbidden files、tests、validation、rollback、DoD 和启动门槛，避免一次性大范围重构，并防止 PR2 在 data model / repository / tests 未冻结时提前启动。

## 2. 输入来源

- `README.md`
- `01_ARCHITECTURE_OPTIONS.md`
- `02_RECOMMENDED_ARCHITECTURE.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- `10_DATA_MODEL_AND_MIGRATION_PLAN.md`
- `12_FRONTEND_IMPLEMENTATION_PLAN.md`
- `15_VALIDATION_PLAN.md`
- active docs：`BACKLOG.md`、`DELIVERY_PLAN.md`、`APPLICATION_FLOW_SPEC.md`、`SECURITY_PRIVACY.md`
- `11_BACKEND_API_AND_SCHEMA_PLAN.md`
- `12_FRONTEND_IMPLEMENTATION_PLAN.md`
- `13_TEST_PLAN_BACKEND.md`
- `14_TEST_PLAN_FRONTEND.md`
- `18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md`

## 3. 当前状态

PR1 只创建文档登记与设计包骨架。PR2-PR8 均未启动；任何实现必须先进入受权 AIFI 任务或明确 PR scope。PR2 当前不可启动，除非 PR1.5 的冻结 DoD 全部满足。

## 4. 目标输出

输出 PR1、PR1.5、PR2-PR8 拆分表，支撑每个实现窗口的 Scope Lock。

## 5. 必须覆盖范围

| PR | PR 目标 | 架构意义 | Scope | Allowed files | Forbidden files | Tests | Validation | Rollback | DoD |
|---|---|---|---|---|---|---|---|---|---|
| PR1 文档登记与设计包骨架 | 新增 backlog/docs index 登记，创建专题规划包 | 先冻结双域边界和 PR 顺序 | docs only | `docs/03-delivery/refactor-multiagent-langgraph/**`, `BACKLOG.md`, `DOCS_INDEX.md` | `apps/**`, `tests/**`, dependencies, migrations, config except docs index | doc checks | git status/stat/check + doc governor | revert docs-only diff | planning package 完整且不替代 active docs |
| PR1.5 实施前冻结包 | 冻结 PR2 输入：data model / repository contract / API schema / test method / migration rollback / feature flag / active docs 回写清单 | 把 PR2 从架构设计工作变成实现工作 | docs only, owned planning package plus authorized active docs sync by main Agent | `docs/03-delivery/refactor-multiagent-langgraph/**`; main Agent 授权时可同步 `BACKLOG.md`, `DOCS_INDEX.md`, active design docs | `apps/**`, `tests/**`, dependencies, migrations, CI | doc checks + forbidden wording scan | `git diff --check`, doc governor, owned-file whitelist | revert docs-only PR1.5 diff | PR2 DoD、runtime table/repository symbols、test method names、migration rollback contract、feature flag name、owner/redaction/idempotency assertions全部冻结 |
| PR2 AI Runtime 基础模型 | 只实现 PR1.5 已冻结的 runtime data model、repository、schema tests 和 migration / rollback plan | Core tables / runtime tables / checkpoint tables 分离 | backend models/repos/schema tests only | `apps/api/app/infrastructure/db/**`, runtime repositories, backend tests, authorized active docs sync | frontend, business graph, facade design, real provider, LangGraph concrete graph migration | repository/schema/redaction/idempotency tests from `13_TEST_PLAN_BACKEND.md` | pytest subset + import scan + diff check | rollback migration/backfill plan from PR1.5 | raw-off、owner、retention、checkpoint ref、idempotency replay 通过；不得新增架构设计事实 |
| PR3 AI Orchestration Facade + fake vertical slice contract | 新增 facade、runner port、registry、contracts，并用 fake runner 贯通一个无业务写入 vertical slice | Core 只依赖 facade/port | application AI layer + minimal usecase wiring to fake runner | `apps/api/app/application/ai/**`, `application/agents/contracts.py`, tests | LangGraph concrete import in Core, DB migration, frontend | facade/contract/boundary tests | pytest + import scan | restore legacy usecase path | Core 不 import LangGraph；fake vertical slice 返回 `ai_task_id/agent_run_id` 且无业务 formal write |
| PR4-LG-DEP LangGraph dependency spike gate | 只引入并锁定 LangGraph / checkpointer / serializer 依赖，完成 minimal fake graph spike 和官方 API 二次核验 | 在真实 runtime adapter 前证明 dependency、Python、CI、encrypted serializer 和 checkpointer 可用 | dependency files + fake graph spike only | 后端依赖文件、`apps/api/app/infrastructure/agent_runtime/langgraph/**`、dependency / fake graph tests、授权 active docs sync | business graph migration, frontend, real provider, raw payload persistence | dependency dry-run、memory checkpointer fake graph、PG checkpointer compatibility、encrypted serializer tests | `18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md` 中 PR4-LG-DEP 命令 + import scan + redaction scan | revert dependency files and disable fake adapter flag | exact pin、官方 API 二次核验、`LANGGRAPH_AES_KEY` serializer gate、CI dry-run、fake graph deterministic 全部通过 |
| PR4 LangGraph Runtime + Fake Graph | 新增 LangGraph adapter、checkpointer、trace bridge、fake graph runtime API | 验证 runtime start/resume/replay/timeline，不迁移真实业务 graph | agent runtime infrastructure + fake graph API | `application/agents/**`, `infrastructure/agent_runtime/**`, runtime API files, tests | business graph migration, frontend, real provider | fake graph/runtime API/redaction/interrupt tests | fake transport gate + redaction scan | disable runtime flag | fake graph deterministic、timeline sanitized、interrupt resume idempotent；fake vertical slice 可从 API 查 status/timeline |
| PR5 Job Match Graph | 接入首个业务 graph：`job_match_graph` | 验证一个真实业务 handoff；不代表完整 MultiAgent 验证完成 | job match graph only | job match agents/usecase adapter/tests | polish/report/review/frontend, full MultiAgent acceptance claims | job match graph tests | pytest subset | fallback legacy/deterministic path | API 兼容，score/candidate 边界正确；只声明 JobMatch graph 通过 |
| PR6 Polish Question / Feedback Graphs | 迁移 question/feedback | 验证高频 AI 链路 | polish graph + legacy service facade adapter | polish agents/tests | report/review/frontend | polish graph/API/candidate tests | pytest polish subset | legacy path fallback | answer save no LLM，feedback independent AI task |
| PR7 Frontend AI Runtime UI | 状态、timeline、interrupt、candidate UI | 前端 Core UI 与 Agent UI 分离 | frontend entities/features/widgets/hooks | `apps/web/src/entities/ai-task/**`, `apps/web/src/entities/agent-run/**`, feature/widget files, frontend tests, authorized package files if test runner decision requires | backend graph logic, deps without explicit PR7 authorization, provider calls | web type/component tests from `14_TEST_PLAN_FRONTEND.md` | `npm run web:test`, `npm run web:build` | disable UI feature flag | runner/dependency 决策关闭：要么复用现有测试命令且不加依赖，要么在 PR7 明确授权并提交 package/lock/test config；不暴露 internals，状态完整 |
| PR8 Report / Review / Candidate Closure | 闭合 report/review/candidate confirmation | 完成高级 AI result 到确认流 | report/review graphs, candidate closure, frontend panels | report/review/candidate backend + frontend files, tests, active docs as authorized | unrelated product scope, export/download | report/review/candidate backend tests + web tests | full subset + optional smoke | disable graph/candidate closure flag | copy boundary、确认流、redaction 全通过 |

## 6. PR2 启动门槛

PR2 必须同时满足以下条件才可启动：

| Gate | 关闭标准 | 验证 |
|---|---|---|
| G1 PR1.5 merged | PR1.5 DoD 全部完成并被主 Agent 汇总 | PR1.5 diff / review evidence |
| G2 runtime tables frozen | `ai_tasks`、`ai_task_results`、`agent_runs`、`agent_node_runs`、`agent_interrupts`、`llm_calls`、`llm_call_payloads` 或等价命名、字段组、owner、retention、redaction、checkpoint ref 已冻结 | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` / PR1.5 patch |
| G3 repository symbols frozen | repository class / method 名、owner scoped query、idempotency replay、timeline read、LLM summary read 已冻结 | PR1.5 symbol table |
| G4 tests frozen | `13_TEST_PLAN_BACKEND.md` 中 PR2 tests 的文件名、方法名、arrange/act/assert 已冻结 | test plan review |
| G5 migration rollback frozen | migration / rollback / backfill / in-flight task handling 已冻结；当前仓库没有 Alembic 时必须写明 SQLAlchemy bootstrap 与 rollback 验证方式 | PR1.5 migration section |
| G6 feature flag frozen | runtime enablement flag、default-off 行为、real-provider gate 已冻结 | PR1.5 config section |
| G7 active docs sync decision | 需要回写 `API_SPEC.md` / `PERSISTENCE_MODEL.md` / `SECURITY_PRIVACY.md` / `BACKLOG.md` / `DOCS_INDEX.md` 的项目已由主 Agent 决定并登记 | 主 Agent 汇总 |

若任一 gate 未关闭，PR2 只能做只读 recon 或 PR1.5 文档修复，不能修改 `apps/**` 或 `tests/**`。

## 7. PR3 / PR4 fake vertical slice 定义

| PR | Fake vertical slice | 输入 | 输出 | 不允许声明 |
|---|---|---|---|---|
| PR3 | Core UseCase -> `AiOrchestrationFacade` -> fake `AgentGraphRunner` -> `AiTaskStatusResponse` | owner scoped command, target ref, fake task type | `ai_task_id`, optional `agent_run_id`, facade result refs | 不声明 LangGraph runtime 已接入；不写业务 formal object |
| PR4 | API -> runtime repository -> LangGraph adapter fake graph -> timeline / interrupt / replay | fake graph request, interrupt resume body | status、timeline、sanitized LLM summary、interrupt resume accepted | 不声明业务 graph 已迁移；不声明完整 MultiAgent 验证完成 |

## 8. 与 active docs 的关系

PR scope 必须映射 `BACKLOG.md` 的 AIFI 任务；长期设计事实必须回写 active docs；长期架构决策需要 ADR。本文不能替代正式任务入口。

## 9. 非目标

- 不合并 PR2-PR8。
- 不绕过 `BACKLOG.md` 开启实现。
- 不让 Core Business 直接依赖 LangGraph。
- 不让 checkpoint 成为业务 truth source。
- 不让 candidate 静默 formalize。

## 10. 目标 PR 使用方式

每个 PR 开始前复制对应行作为 Scope Lock，结束时填写实际 files changed、tests、validation evidence、rollback 说明和 residual risk。

## 11. Definition of Done

- PR1、PR1.5、PR2-PR8 表格完整覆盖 Scope / Allowed files / Forbidden files / Tests / Validation / Rollback / DoD。
- PR 顺序清晰且可分批回滚。
- PR2 启动门槛清晰，且 PR1.5 DoD 未满足时 PR2 不可启动。
- PR3 / PR4 fake vertical slice 和 PR5 JobMatch graph 的验收语义已区分。
