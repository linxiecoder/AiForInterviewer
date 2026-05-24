---
title: LangGraph MultiAgent Consolidated Implementation README
type: delivery-planning
status: draft-f5-langgraph-implementation-consolidation
owner: 项目交付 / 后端架构 / 前端架构
source_task: AIFI-BE-005 / AIFI-BE-006 follow-up consolidation
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph-implementation/readme
---

# LangGraph MultiAgent Consolidated Implementation README

## 1. 文档定位

本文是 `docs/03-delivery/refactor-multiagent-langgraph-implementation/` 的唯一 implementation entry。后续阅读、执行、评审和 PR Scope Lock 必须先从本文进入，再跳转到下游子文档。

本目录把旧 `docs/03-delivery/refactor-multiagent-langgraph/` 中分散的 PR1 / PR1.5 / PR1.6 planning evidence 合并为新的实施文档集。旧目录大部分文件保留为 evidence-only，不再作为实施 source of truth；只有 `DOCS_INDEX.md` 明确登记为 active 的旧目录文件或被本目录明确引用为 scope-lock 证据的文件保留特殊状态。

## 2. 权威规则

| 事项 | 当前 source of truth |
|---|---|
| 本实施文档集入口 | 本 README |
| 架构 as-is / to-be 和所有架构图 | `01_ARCHITECTURE_ASIS_TOBE.md` |
| 后端迁移总计划、PR 顺序、PR2 exact scope 约束 | `02_BACKEND_REFACTOR_MASTER_PLAN.md`，其中 §4 / §5 已内联 PR2 exact scope 和 launch gates |
| 后端 method / field / Agent / Graph / Prompt / Skill / Trace 实施细节 | `03_BACKEND_FUNCTION_PACKAGES/*.md` |
| 前端 LangGraph / AI Runtime Graph Configuration Console 实施计划 | `04_FRONTEND_LANGGRAPH_UI_PLAN.md` |
| PR2 是否可开始代码实现 | `02_BACKEND_REFACTOR_MASTER_PLAN.md` §4 / §5 + 旧 `20_PR2_PREFLIGHT_READINESS_REPORT.md` 的 evidence |
| 旧专题包处理 | `docs/03-delivery/refactor-multiagent-langgraph/` 大部分只作 evidence，不作为实施入口；特殊状态见 §6 |

## 3. 目录结构

| 文件 | 职责 | 禁止承载内容 |
|---|---|---|
| `README.md` | 唯一入口、阅读顺序、source-of-truth 边界、PR2 状态和旧目录处理 | 不放架构图、后端迁移总计划、方法级实现表或前端状态机细节 |
| `01_ARCHITECTURE_ASIS_TOBE.md` | as-is / to-be 架构、依赖方向、表边界、运行时事件流图 | 不放 PR 迁移任务表或方法级实现计划 |
| `02_BACKEND_REFACTOR_MASTER_PLAN.md` | 后端 PR2-PR8 总计划、scope、门禁、验证和回滚 | 不放 graph node 级实现表、字段级 ORM 表或前端 UI 状态机 |
| `03_BACKEND_FUNCTION_PACKAGES/README.md` | 后端功能包索引和跨包规则 | 不作为实施入口替代根 README |
| `03_BACKEND_FUNCTION_PACKAGES/01_AI_RUNTIME_INFRA_PACKAGE.md` | AI Runtime facade / runner / registry / interrupt / handoff / guard 的方法级计划 | 不写 LLM trace 表字段细节 |
| `03_BACKEND_FUNCTION_PACKAGES/02_LLM_TRACE_PERSISTENCE_PACKAGE.md` | AI Runtime tables、LLM trace、payload、repository、retention 和 PR2 测试 | 不写业务 graph node 计划 |
| `03_BACKEND_FUNCTION_PACKAGES/03_JOB_MATCH_AGENT_PACKAGE.md` | Job Match / ResumeAnalysis descriptor、placeholder、direct path retention、PR8 conditional graph sketch | 不写 Polish / Pressure 计划；不把 Job Match 提前为 PR5 |
| `03_BACKEND_FUNCTION_PACKAGES/04_POLISH_AGENT_PACKAGE.md` | PR5 Polish first migration target；progress tree / question / feedback graph | 不写 Pressure 或 report/review 计划；不把 candidate enhancement / formal closure 放入 PR5 |
| `03_BACKEND_FUNCTION_PACKAGES/05_PRESSURE_AGENT_PACKAGE.md` | Pressure Mode graph、turn、pace、end condition、report handoff | 不写 report body generation 计划 |
| `03_BACKEND_FUNCTION_PACKAGES/06_REPORT_REVIEW_AGENT_PACKAGE.md` | Report / mock review / real review graph、copy boundary、privacy redaction | 不写 candidate formal write package 细节 |
| `03_BACKEND_FUNCTION_PACKAGES/07_CANDIDATE_SKILL_TRAINING_PACKAGE.md` | Candidate / Skill / Weakness / Asset / Training suggestion / confirmation | 不写 frontend drawer 实现细节 |
| `03_BACKEND_FUNCTION_PACKAGES/08_GRAPH_CONFIGURATION_PACKAGE.md` | Graph Configuration Backend、descriptor/config API、default-off enablement、policy refs、config audit | 不写业务 graph execution、provider call 或 LangGraph debug internals |
| `04_FRONTEND_LANGGRAPH_UI_PLAN.md` | PR7 AI Runtime graph configuration console、route、API client、hook、component、状态机、测试 | 不写后端 graph node 级计划 |

## 4. 阅读顺序

1. 先读本 README，确认入口、旧目录处理和 PR2 状态。
2. 需要架构图时读 `01_ARCHITECTURE_ASIS_TOBE.md`。
3. 需要启动或评审后端 PR 时读 `02_BACKEND_REFACTOR_MASTER_PLAN.md`。
4. 进入具体后端实现前，只读对应的 backend function package。
5. 进入前端实现前，只读 `04_FRONTEND_LANGGRAPH_UI_PLAN.md`。

## 5. PR2 当前状态

PR2 仍是 `CONDITIONAL GO`。PR2 exact scope 已内联到 `02_BACKEND_REFACTOR_MASTER_PLAN.md` §4 / §5；旧 `docs/03-delivery/refactor-multiagent-langgraph/20_PR2_PREFLIGHT_READINESS_REPORT.md` 只作为 scope-lock evidence，不再作为实施入口。

PR2 不授权以下事项：

- LangGraph runtime enablement。
- graph execution。
- real provider calls。
- business graph migration。
- runtime facade / runner / adapter / checkpointer / serializer implementation。
- runtime flag enablement。
- frontend UI。
- active docs 全量 backfill。
- 修改 PR2 exact scope 外文件。

## 6. 旧目录处理

`docs/03-delivery/refactor-multiagent-langgraph/` 保留为历史 evidence 和 planning package。它不再是本轮 consolidated implementation 的入口，也不替代本目录。

当前特殊状态：

- `19_AI_PRODUCT_PROMPT_SKILL_PRESSURE_REMEDIATION_PLAN.md` 仍在 `DOCS_INDEX.md` 中作为 PR1.6 blocker identification / remediation planning active 特殊文档登记；它不是本 implementation set 的实施入口。
- `20_PR2_PREFLIGHT_READINESS_REPORT.md` 未在 `DOCS_INDEX.md` 中作为独立 active 文档行登记，但仍被 `BACKLOG.md` 和本目录引用为 PR2 exact scope lock 的 evidence；PR2 exact scope 已内联到 `02_BACKEND_REFACTOR_MASTER_PLAN.md` §4 / §5。
- 除 `DOCS_INDEX.md` 明确 active 的旧目录文件和本目录明确引用的 scope-lock evidence 外，旧目录不得作为 PR2-PR8 implementation source of truth。

## 7. 接受前风险

如果 PR2 在本 consolidation 被接受前启动，主要风险是：

- implementer 继续从旧 00-20 分散文档取数，导致入口混乱。
- PR2 scope 被误读为完整 LangGraph runtime GO。
- `application/ai_runtime/**`、`infrastructure/ai_runtime/langgraph/**` 和旧 `application/ai/**` / `application/agents/**` 命名边界再次分裂。
- Method / field / Prompt / Skill / Trace 计划分散，测试只能覆盖局部而无法证明 raw-off、owner scope、checkpoint non-truth-source 和 candidate/formal boundary。
- PR3 / PR4 前仍需 active docs backfill 或新的 accepted risk；PR2 提前宣称完整架构接受会越权。

## 8. 非目标

- 不修改 `apps/**`、`tests/**`、依赖、migration、CI、后端代码、前端代码或业务代码。
- 不调用真实 LLM provider。
- 不移动、删除或重命名旧文档。
- 不创建新的 roadmap、parallel plan 或替代 `BACKLOG.md` / `DELIVERY_PLAN.md` 的任务体系。

## 9. 完成定义

- 本目录下 12 个允许文件全部创建。
- README 是唯一 implementation entry。
- PR2 exact scope 已内联到 `02_BACKEND_REFACTOR_MASTER_PLAN.md` §4 / §5。
- 架构图只出现在 `01_ARCHITECTURE_ASIS_TOBE.md`。
- 后端迁移总计划只出现在 `02_BACKEND_REFACTOR_MASTER_PLAN.md`。
- 后端 method / field / Agent / Graph / Prompt / Skill / Trace 计划只出现在 function package docs。
- 前端计划只出现在 `04_FRONTEND_LANGGRAPH_UI_PLAN.md`。
- 旧 `refactor-multiagent-langgraph/` 已说明为大部分 evidence-only，并明确 19 / 20 的特殊状态。
- PR2 保持 `CONDITIONAL GO`，且未扩大 `20_PR2_PREFLIGHT_READINESS_REPORT.md` 的 exact scope。
