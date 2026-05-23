---
title: PR 拆分与实施顺序
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/pr-breakdown-and-implementation-sequence
---

# PR 拆分与实施顺序

## 1. 文档目的

本文定义 PR1-PR8 的实施顺序、scope、allowed files、forbidden files、tests、validation、rollback 和 DoD，避免一次性大范围重构。

## 2. 输入来源

- `README.md`
- `01_ARCHITECTURE_OPTIONS.md`
- `02_RECOMMENDED_ARCHITECTURE.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- `10_DATA_MODEL_AND_MIGRATION_PLAN.md`
- `12_FRONTEND_IMPLEMENTATION_PLAN.md`
- `15_VALIDATION_PLAN.md`
- active docs：`BACKLOG.md`、`DELIVERY_PLAN.md`、`APPLICATION_FLOW_SPEC.md`、`SECURITY_PRIVACY.md`

## 3. 当前状态

PR1 只创建文档登记与设计包骨架。PR2-PR8 均未启动；任何实现必须先进入受权 AIFI 任务或明确 PR scope。

## 4. 目标输出

输出 PR1-PR8 拆分表，支撑后续 Scope Lock。

## 5. 必须覆盖范围

| PR | PR 目标 | 架构意义 | Scope | Allowed files | Forbidden files | Tests | Validation | Rollback | DoD |
|---|---|---|---|---|---|---|---|---|---|
| PR1 文档登记与设计包骨架 | 新增 backlog/docs index 登记，创建专题规划包 | 先冻结双域边界和 PR 顺序 | docs only | `docs/03-delivery/refactor-multiagent-langgraph/**`, `BACKLOG.md`, `DOCS_INDEX.md` | `apps/**`, `tests/**`, dependencies, migrations, config except docs index | doc checks | git status/stat/check + doc governor | revert docs-only diff | planning package 完整且不替代 active docs |
| PR2 AI Runtime 基础模型 | 新增 runtime data model、repository、migration/rollback plan | Core tables / runtime tables / checkpoint tables 分离 | backend models/repos/schema tests | `apps/api/app/infrastructure/db/**`, runtime repositories, backend tests, active docs as authorized | frontend, business graph, real provider | repository/schema/redaction tests | pytest subset + diff check | rollback migration/backfill | raw-off、owner、retention、checkpoint ref 通过 |
| PR3 AI Orchestration Facade | 新增 facade、runner port、registry、contracts | Core 只依赖 facade/port | application AI layer + minimal usecase wiring | `apps/api/app/application/ai/**`, `application/agents/contracts.py`, tests | LangGraph concrete import in Core | facade/contract/boundary tests | pytest + import scan | restore legacy usecase path | Core 不 import LangGraph |
| PR4 LangGraph Runtime + Fake Graph | 新增 LangGraph adapter、checkpointer、trace bridge、fake graph | 验证 runtime start/resume/replay/timeline | agent runtime infrastructure | `application/agents/**`, `infrastructure/agent_runtime/**`, tests | business graph migration | fake graph/runtime API/redaction tests | fake transport gate + redaction scan | disable runtime flag | fake graph deterministic and sanitized |
| PR5 Job Match Graph | 接入首个业务 graph | 验证真实业务 handoff | job match graph only | job match agents/usecase adapter/tests | polish/report/review/frontend | job match graph tests | pytest subset | fallback legacy/deterministic path | API 兼容，score/candidate 边界正确 |
| PR6 Polish Question / Feedback Graphs | 迁移 question/feedback | 验证高频 AI 链路 | polish graph + legacy service facade adapter | polish agents/tests | report/review/frontend | polish graph/API/candidate tests | pytest polish subset | legacy path fallback | answer save no LLM，feedback independent AI task |
| PR7 Frontend AI Runtime UI | 状态、timeline、interrupt、candidate UI | 前端 Core UI 与 Agent UI 分离 | frontend entities/features/widgets/hooks | `apps/web/src/entities/ai-task/**`, `agent-run/**`, feature/widget files, frontend tests | backend graph logic, deps unless authorized | web type/component tests | `npm run web:test`, `npm run web:build` | disable UI feature flag | 不暴露 internals，状态完整 |
| PR8 Report / Review / Candidate Closure | 闭合 report/review/candidate confirmation | 完成高级 AI result 到确认流 | report/review graphs, candidate closure, frontend panels | report/review/candidate backend + frontend files, tests, active docs as authorized | unrelated product scope, export/download | report/review/candidate backend tests + web tests | full subset + optional smoke | disable graph/candidate closure flag | copy boundary、确认流、redaction 全通过 |

## 6. 与 active docs 的关系

PR scope 必须映射 `BACKLOG.md` 的 AIFI 任务；长期设计事实必须回写 active docs；长期架构决策需要 ADR。本文不能替代正式任务入口。

## 7. 非目标

- 不合并 PR2-PR8。
- 不绕过 `BACKLOG.md` 开启实现。
- 不让 Core Business 直接依赖 LangGraph。
- 不让 checkpoint 成为业务 truth source。
- 不让 candidate 静默 formalize。

## 8. 后续 PR 使用方式

每个 PR 开始前复制对应行作为 Scope Lock，结束时填写实际 files changed、tests、validation evidence、rollback 说明和 residual risk。

## 9. Definition of Done

- PR1-PR8 表格完整覆盖 Scope / Allowed files / Forbidden files / Tests / Validation / Rollback / DoD。
- PR 顺序清晰且可分批回滚。
- PR2 AI Runtime 基础模型作为下一步推荐已明确。

