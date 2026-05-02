---
title: TASK_INDEX
type: note
permalink: ai-for-interviewer/task-index
---

> 强引用：有效文档白名单见 `docs/governance/ACTIVE_DOC_CANON.md`。


# AI 模拟面试项目任务索引

## 1. 文档定位

本文档只作为任务索引，记录任务入口、依赖、阻断状态和当前任务文档位置。本文档不承载需求正文、设计正文、执行日志或归档说明。

## 2. 当前任务入口与状态绑定引用

| task layer | current entry | notes |
| --- | --- | --- |
| current task entry | `TASK_INDEX.md` | 本文档是当前任务入口 |
| structured task state | `docs/governance/DOC_STATE.yaml` | 正式状态真值 |
| delegated state-bound task remap | `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | 已被本文档替代为任务入口，但仍被 official state 的 `meta.path` / `source_doc` 引用；state / source_doc migration 前不得移动或删除 |
| ST13 task docs | `docs/tasks/workbench-mvp/st13-task-packages/**` | delegated / state-bound / historical task evidence；`ST13_*` 仅作为任务 ID、`source_doc` 引用和 required doc slot 保留，不作为阶段体系 |
| state-bound migration plan | `docs/governance/STATE_BOUND_MIGRATION_PLAN.md` | 归档迁移前置计划；不是任务事实源，不授权移动或删除任务包 |
| module task indexes | `docs/modules/<module-dir>/MODULE_TASK_INDEX.md` | 模块级任务索引，真实路径见 `MODULE_INDEX.md` |

## 3. 当前任务组

| group | scope | 阶段主标签 | active entry | status |
| --- | --- | --- | --- | --- |
| ST13_20 | 服务端保存 / 数据库边界 | `R1` | `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/` | `formal_window_status=open`；`implementation_approval_status=approved`；`implementation_ready=false`；`candidate_status=none`；`readiness=downstream_ready`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |
| ST13_21 | API / 后端服务边界 | `R1` | `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/` | `formal_window_status=open`；`implementation_approval_status=approved`；`implementation_ready=false`；`candidate_status=none`；`readiness=downstream_ready`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |
| ST13_24 | 测试 / 验收 / DoD | `R0` | `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/` | `formal_window_status=closed`（未写入 open）；`implementation_approval_status=none`（未写入 approved）；`implementation_ready=false`；`candidate_status=none`；`readiness=blocked`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |
| ST13_25 | 文档治理 / 收口 / 长期上下文 | `R0` | `docs/tasks/workbench-mvp/st13-task-packages/ST13_25/` | `formal_window_status=closed`（未写入 open）；`implementation_approval_status=none`（未写入 approved）；`implementation_ready=false`；`candidate_status=none`；`readiness=blocked`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |
| ST01_01 | 运行环境与仓库基线 | 历史流程噪声（归档） | `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/` | `formal_window_status=open`；`implementation_approval_status=approved`；`implementation_ready` 以 `evaluate-state` 当前输出为准；`candidate_status=none`；`readiness=downstream_ready`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |

## 4. 任务使用规则

- 任务是否可实施以 `DOC_STATE.yaml` 和 doc-governor gate 为准。
- 若文本与 `DOC_STATE.yaml` 冲突，以 `DOC_STATE.yaml` 为准。
- ST13 双文档已迁入 `docs/tasks/workbench-mvp/st13-task-packages/**`，并已同步 `DOC_STATE.yaml` required doc slot。
- `ST13_*` 只作为任务 ID、source_doc 引用或 state key，不作为阶段体系；阶段主标签只使用 `R0/R1/R2`。
- `ST13_20` / `ST13_21` 双文档属于 state-bound task package / historical task evidence。当前 API / DB 实现事实以 `TECHNICAL_STANDARDS.md`、`docs/development/**`、`apps/api/**` 和 official state 为准；任务包内历史 gate 或 readiness 叙述不得覆盖当前结论。
- task remap 和 ST13 task packages 是 delegated / state-bound / historical task evidence；当前任务入口仍是 `TASK_INDEX.md`，迁移前不得直接移动或删除相关任务包。
- `ST13_21` 的历史实现/验收记录仅作过程证据，不代表当前 gate 已放行后续实现；是否可实施仍以 `DOC_STATE.yaml` 与 doc-governor 判定为准。
- 本索引不把历史任务文档重新解释为当前任务入口；`ST01_01` 是从历史骨架重建并已登记正式状态 entry 的例外。其可实施结论必须以 `DOC_STATE.yaml` 与 `evaluate-state` 当前输出为准；历史实施记录仅作过程证据，不代表自动放行新窗口。
- `ST01_01` 与其他任务的 implementation-ready 结论均以 official state 与 doc-governor gate 为准；本索引不通过 Markdown 自行声明 implementation-ready。
- generated reports、preview、packet 和 archive 审计包不得作为任务事实源；只能作为生成产物、历史证据或归档台账。

- 阶段主标签统一使用 `R0/R1/R2`；`P0/P1/P2/P3`、`W13-*`、旧 `STxx_*` 仅可作为历史追溯信息，不得作为新任务主标签。
- 新任务命名固定为 `R{n}-W{nn}`，禁止引入新体系。

## 5. 关联输入

| input | purpose |
| --- | --- |
| `docs/requirements/workbench-mvp/**` | 任务验收依据 |
| `docs/design/workbench-mvp/**` | 任务设计依据 |
| `PLAN_LATEST.md` | 当前推进顺序 |
| `MODULE_INDEX.md` | 模块文档入口 |
## 6. 历史过程归档入口

- 历史过程细节与旧体系迁移说明已归档至：`archive/governance/archive-ledger.md`。
- 需追溯 W13 过程细节时，优先查看：`archive/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.history-2026-05-01.md`；该历史快照不替代本文档的当前任务入口职责。
