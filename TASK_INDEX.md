---
title: TASK_INDEX
type: note
permalink: ai-for-interviewer/task-index
---

# AI 模拟面试项目任务索引

## 1. 文档定位

本文档只作为任务索引，记录任务入口、依赖、阻断状态和当前任务文档位置。本文档不承载需求正文、设计正文、执行日志或归档说明。

## 2. 当前任务事实源

| task layer | current entry | notes |
| --- | --- | --- |
| structured task state | `docs/governance/DOC_STATE.yaml` | 正式状态真值 |
| current task remap | `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md` | 路径已迁移，状态层引用已同步 |
| ST13 task docs | `docs/tasks/workbench-mvp/st13-task-packages/**` | 路径已迁移，状态层 required doc slot 已同步 |
| module task indexes | `docs/modules/<module-dir>/MODULE_TASK_INDEX.md` | 模块级任务索引，真实路径见 `MODULE_INDEX.md` |

## 3. 当前任务组

| group | scope | active entry | status |
| --- | --- | --- | --- |
| ST13_20 | 服务端保存 / 数据库边界 | `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/` | `formal_window_status=open`；`implementation_approval_status=approved`；`implementation_ready=false`；`candidate_status=none`；`readiness=downstream_ready`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |
| ST13_21 | API / 后端服务边界 | `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/` | `formal_window_status=open`；`implementation_approval_status=approved`；`implementation_ready=false`；`candidate_status=none`；`readiness=downstream_ready`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |
| ST13_24 | 测试 / 验收 / DoD | `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/` | `formal_window_status=closed`（未写入 open）；`implementation_approval_status=none`（未写入 approved）；`implementation_ready=false`；`candidate_status=none`；`readiness=blocked`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |
| ST13_25 | 文档治理 / 收口 / 长期上下文 | `docs/tasks/workbench-mvp/st13-task-packages/ST13_25/` | `formal_window_status=closed`（未写入 open）；`implementation_approval_status=none`（未写入 approved）；`implementation_ready=false`；`candidate_status=none`；`readiness=blocked`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |
| ST01_01 | 运行环境与仓库基线 | `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/` | `formal_window_status=open`；`implementation_approval_status=approved`；`implementation_ready` 以 `evaluate-state` 当前输出为准；`candidate_status=none`；`readiness=downstream_ready`；历史动作记录（如实现/验收叙述）不代表当前 gate 放行 |

## 4. 任务使用规则

- 任务是否可实施以 `DOC_STATE.yaml` 和 doc-governor gate 为准。
- 若文本与 `DOC_STATE.yaml` 冲突，以 `DOC_STATE.yaml` 为准。
- ST13 双文档已迁入 `docs/tasks/workbench-mvp/st13-task-packages/**`，并已同步 `DOC_STATE.yaml` required doc slot。
- `ST13_21` 的历史实现/验收记录仅作过程证据，不代表当前 gate 已放行后续实现；是否可实施仍以 `DOC_STATE.yaml` 与 doc-governor 判定为准。
- 本索引不把历史任务文档重新解释为当前任务入口；`ST01_01` 是从历史骨架重建并已登记正式状态 entry 的例外。其可实施结论必须以 `DOC_STATE.yaml` 与 `evaluate-state` 当前输出为准；历史实施记录仅作过程证据，不代表自动放行新窗口。
- `ST01_01` 与其他任务的 implementation-ready 结论均以 official state 与 doc-governor gate 为准；本索引不通过 Markdown 自行声明 implementation-ready。

## 5. 关联输入

| input | purpose |
| --- | --- |
| `docs/requirements/workbench-mvp/**` | 任务验收依据 |
| `docs/design/workbench-mvp/**` | 任务设计依据 |
| `PLAN_LATEST.md` | 当前推进顺序 |
| `MODULE_INDEX.md` | 模块文档入口 |
## 6. 历史过程归档入口

- 历史过程细节与旧体系迁移说明已归档至：`archive/governance/archive-ledger.md`。
- 需追溯 W13 过程细节时，优先查看：`archive/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.history-2026-05-01.md`。
