# AI 模拟面试一期工作台 MVP 需求入口

## 1. 文档定位

本目录是 Workbench MVP 当前需求事实源，回答“要什么”“不要什么”“验收到什么程度”。

本目录不承载设计正文、执行日志、迁移过程、任务流水、状态写回或实施包内容。

## 2. 当前需求文档

| 文档 | 职责 | 当前事实源 |
| --- | --- | --- |
| [scope-and-acceptance.md](scope-and-acceptance.md) | 产品目标、范围边界、用户角色、in-scope / out-of-scope、验收口径 | yes |

## 3. 与其他文档层的关系

| 层级 | 回答的问题 | 当前入口 |
| --- | --- | --- |
| requirement | 要什么、不要什么、验收到什么程度 | 本目录 |
| design | 信息、对象、交互、数据和质量门禁如何设计 | `docs/design/workbench-mvp/**` |
| planning | 怎么推进、当前 planning 入口在哪里 | `PLAN_LATEST.md`、`docs/planning/**` |
| task | 怎么拆任务、哪些任务仍 blocked | `TASK_INDEX.md`、`docs/tasks/workbench-mvp/st13-task-packages/**` |
| process | 做过什么 | `EXECUTION_LOG.md` |
| governance | 规则、状态和 gate 约束 | `AGENTS.md`、`docs/DOC_GOVERNANCE.md`、`docs/governance/**` |

## 4. 使用规则

- 需求事实引用本目录。
- 设计事实引用 `docs/design/workbench-mvp/**`。
- 规划事实引用 `PLAN_LATEST.md` 或当前 planning 文档。
- 任务事实引用 `TASK_INDEX.md`、`DOC_STATE.yaml` 或当前任务文档。
- 历史过程只作为追溯材料，不作为当前需求依据。
