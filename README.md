---
title: README
type: note
permalink: ai-for-interviewer/readme
---

# AI 模拟面试项目文档入口

本文档只作为当前仓库入口导航，不承载需求正文、设计正文、执行日志或任务流水。

## 当前入口

| 类型 | 当前入口 | 职责 |
| --- | --- | --- |
| 需求 | [Workbench MVP 需求入口](docs/requirements/workbench-mvp/README.md) | 产品目标、范围边界、用户角色、验收口径 |
| 设计 | [Workbench MVP 设计入口](docs/design/workbench-mvp/README.md) | 信息架构、对象模型、RAG、多轮、后端边界、评分、复盘、导出设计 |
| 规划 | [PLAN_LATEST.md](PLAN_LATEST.md) | 当前仓库执行入口和下一步推进顺序 |
| 任务 | [TASK_INDEX.md](TASK_INDEX.md) | 当前任务索引、依赖、阻断状态和任务文档入口 |
| 模块 | [MODULE_INDEX.md](MODULE_INDEX.md) | 模块目录、模块文档入口和模块状态摘要 |
| 开放问题 | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) | 需求问题、设计问题和待确认事项的归并入口 |
| 决策 | [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) | 已确认设计决策与影响范围索引 |
| 进展 | [DOCUMENT_PROGRESS.md](DOCUMENT_PROGRESS.md) | 文档体系进展与当前阻断摘要 |
| 成熟度 | [DOCUMENT_MATURITY.md](DOCUMENT_MATURITY.md) | 文档成熟度等级、可用性和风险摘要 |
| 过程 | [EXECUTION_LOG.md](EXECUTION_LOG.md) | 执行记录、归档动作和验证结果 |
| 治理 | [AGENTS.md](AGENTS.md)、[docs/DOC_GOVERNANCE.md](docs/DOC_GOVERNANCE.md) | 协作规则、文档治理规则和状态自动化边界 |

## 当前事实源

| domain | canonical path | doc type |
| --- | --- | --- |
| Workbench MVP requirements | `docs/requirements/workbench-mvp/**` | requirement |
| Workbench MVP design | `docs/design/workbench-mvp/**` | design |
| current planning | `PLAN_LATEST.md`、`docs/planning/2026-04-25-current-repo-execution-plan.md` | planning |
| current task index | `TASK_INDEX.md`、`docs/tasks/workbench-mvp/st13-task-packages/**` | task |
| process log | `EXECUTION_LOG.md` | process |
| governance rules | `AGENTS.md`、`docs/DOC_GOVERNANCE.md`、`docs/governance/**` | governance |
| module docs | `docs/modules/**` | module requirement / design / task |

## 当前执行约束

- `docs/governance/DOC_STATE.yaml` 是正式结构化状态真值，本入口不替代状态层。
- 当前文档体系重构不打开 formal window，不生成 implementation packet，不授权业务实现。
- 当前 planning 文档已迁入 `docs/planning/**`，当前 task 文档已迁入 `docs/tasks/**`，状态层路径已同步。
- 归档材料不作为当前需求、设计、规划或任务依据。