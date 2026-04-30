---
title: DESIGN_DECISIONS
type: note
permalink: ai-for-interviewer/design-decisions
---

# AI 模拟面试项目设计决策入口

## 1. 文档定位

本文档只作为设计决策索引，记录已确认口径、影响范围和事实落点。需求正文归入 `docs/requirements/workbench-mvp/**`，设计正文归入 `docs/design/workbench-mvp/**`。

## 2. 当前决策表

| id | status | decision | affected domain | source path |
| --- | --- | --- | --- | --- |
| DD-001 | confirmed | 一期工作台采用文本优先的模拟面试闭环 | requirement / design | `docs/requirements/workbench-mvp/scope-and-acceptance.md`、`docs/design/workbench-mvp/**` |
| DD-002 | confirmed | Workbench MVP 需求层与设计层职责分离 | requirement / governance | `docs/requirements/workbench-mvp/**` |
| DD-003 | confirmed | Workbench MVP 设计由五份正式设计文档承载 | design | `docs/design/workbench-mvp/**` |
| DD-004 | confirmed | 当前任务是否可实施必须由状态层 gate 判定 | governance / task | `docs/governance/DOC_STATE.yaml`、`TASK_INDEX.md` |
| DD-005 | confirmed | planning/task 文档从旧 plans 目录迁出，`DOC_STATE.yaml` 已同步新路径，`docs/superpowers/**` 不再作为 active 文档区 | planning / task | `docs/planning/**`、`docs/tasks/workbench-mvp/**`、`docs/governance/DOC_STATE.yaml` |
| DD-006 | confirmed | 过程记录只进入 execution log 或归档材料，不作为当前需求或设计依据 | process | `EXECUTION_LOG.md` |

## 3. 决策使用规则

- 决策表只保留决策摘要，不展开完整设计。
- 决策影响的需求事实引用需求层。
- 决策影响的设计事实引用设计层。
- 决策影响的任务状态引用 `DOC_STATE.yaml` 与任务文档。
- 本文档不打开 formal window，不生成 implementation packet。