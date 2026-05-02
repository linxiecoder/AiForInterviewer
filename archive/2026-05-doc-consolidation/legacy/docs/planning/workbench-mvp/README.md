---
title: workbench-mvp 规划索引
type: note
permalink: ai-for-interviewer/docs/planning/workbench-mvp-1
---

# workbench-mvp 规划索引

## 目的

本文档只作为 `docs/planning/workbench-mvp/` 目录索引，帮助定位当前执行计划、长期实施计划和历史规划材料。本文档不是计划事实源，不新增计划内容，也不复述完整计划。

## 当前规划入口

| 类型 | 路径 | 职责 |
| --- | --- | --- |
| 当前执行计划 | `PLAN_LATEST.md` | 承载当前阶段、当前窗口、下一窗口、阻断项和下一步窗口卡 |
| 长期实施计划 | `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` | 承载 R0/R1/R2 完整长期阶段计划 |
| 任务入口 | `TASK_INDEX.md` | 承载当前任务索引、依赖和阻断状态 |
| 结构化状态真值 | `docs/governance/DOC_STATE.yaml` | 承载 official state、required docs 和 gate 判断 |
| 归档迁移前置计划 | `docs/governance/STATE_BOUND_MIGRATION_PLAN.md` | 说明 state-bound 文档解除引用、generated artifact policy 和后续归档前置条件；不作为当前计划源 |

## 文档职责

- `PLAN_LATEST.md` 是当前执行计划入口。
- `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md` 是长期实施计划。
- 本 README 只维护 planning 目录导航，不替代 `PLAN_LATEST.md` 或长期实施计划。
- 技术事实以 `TECHNICAL_STANDARDS.md`、`docs/development/**` 和当前实现目录事实为准；本文档不复制技术细节。

## 阶段体系

- 当前唯一阶段体系为 R0 / R1 / R2。
- R0 表示可运行主链路，R1 表示可信工作台闭环，R2 表示训练闭环与资产沉淀。
- 旧 P0/P1/P2/P3、W13 只能作为历史映射、任务包来源或归档说明，不作为当前计划语言。
- `ST13_*` 只能作为任务 ID、source_doc 引用或 state key，不作为阶段体系。

## 历史和归档边界

- `archive/**` 和本轮 `archive/governance/2026-05-02-doc-convergence-audit/**` 只作为历史证据或治理证据，不是当前事实源。
- generated reports、previews 和 packets 只作为生成产物或历史证据，不替代当前规划入口。
- superseded 但仍被 `DOC_STATE.yaml`、required doc slot、`meta.path` 或 `source_doc` 引用的 state-bound 历史文档，不能直接移动、删除或归档；必须先完成 state / source_doc migration。
- `docs/governance/STATE_BOUND_MIGRATION_PLAN.md` 是归档迁移前置计划，不替代 `PLAN_LATEST.md`、`TASK_INDEX.md` 或 `DOC_STATE.yaml`。

## 使用规则

- Daily Check 或开窗前应读取 `PLAN_LATEST.md`、`TASK_INDEX.md`、`docs/governance/ACTIVE_DOC_CANON.md` 和 `docs/governance/DOC_STATE.yaml`。
- 需要完整阶段计划时读取 `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md`。
- 需要追溯历史计划时只能把 archive 或 superseded 文档作为历史证据，不得恢复为当前入口。
- 新增正式 planning 文档必须登记到 `docs/governance/ACTIVE_DOC_CANON.md` 或本目录 README，且不得创建第二套当前执行计划入口。