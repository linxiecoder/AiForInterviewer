---
title: OPEN_QUESTIONS
type: note
permalink: ai-for-interviewer/open-questions
---

# AI 模拟面试项目开放问题入口

## 1. 文档定位

本文档只作为需求问题、设计问题和待确认事项的归并入口。已确认并需要长期复用的需求正文应沉淀到 `docs/requirements/workbench-mvp/**`，设计正文应沉淀到 `docs/design/workbench-mvp/**`。

## 2. 当前问题分组

| group | meaning | target destination when confirmed |
| --- | --- | --- |
| requirement | 产品范围、边界、角色、验收口径 | `docs/requirements/workbench-mvp/**` |
| design | 信息架构、对象模型、交互、数据、质量门禁 | `docs/design/workbench-mvp/**` |
| planning | 推进顺序、窗口拆分、状态迁移 | `PLAN_LATEST.md` 或当前 planning 文档 |
| task | 任务拆分、依赖、required docs、阻断 | `TASK_INDEX.md` 或当前任务文档 |
| governance | 文档治理、状态规则、工具边界 | `AGENTS.md`、`docs/DOC_GOVERNANCE.md`、`docs/governance/**` |

## 3. 当前已确认口径

| id | status | summary | destination |
| --- | --- | --- | --- |
| OQ-REQ-001 | confirmed | Workbench MVP 需求范围和验收口径从设计层抽出，归入独立需求层 | `docs/requirements/workbench-mvp/**` |
| OQ-DOC-001 | confirmed | Workbench MVP 当前设计仍由 `docs/design/workbench-mvp/**` 承载 | `docs/design/workbench-mvp/**` |
| OQ-STATE-001 | confirmed | planning/task 文档迁移已通过 `DOC_STATE.yaml` 路径同步完成 | `docs/governance/DOC_STATE.yaml` |
| OQ-STATE-002 | resolved | ST13 task docs 已迁入专用 task 目录，required doc slot 已同步 | `docs/tasks/workbench-mvp/st13-task-packages/**` |
| OQ-STATE-003 | resolved | current-repo execution plan 已迁入 planning 目录，state document path 已同步 | `docs/planning/2026-04-25-current-repo-execution-plan.md` |
| OQ-GOV-001 | resolved | `DOC_GOVERNOR_REPORT.md` 已基于迁移后的 `DOC_STATE.yaml` 重渲染，未保留旧 active path | `docs/governance/DOC_GOVERNOR_REPORT.md` |
| OQ-TASK-001 | confirmed | ST13 当前任务文档不因文档重构自动进入 implementation-ready | `TASK_INDEX.md` |

## 4. 当前未关闭问题

| id | status | question | recommended owner |
| --- | --- | --- | --- |

## 5. 使用规则

- 本文档可以记录问题状态和确认结论摘要。
- 本文档不复制需求正文和设计正文。
- 本文档不替代 `DOC_STATE.yaml` 的 gate 判定。