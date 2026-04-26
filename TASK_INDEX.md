# AI 模拟面试项目任务索引

## 1. 文档定位

本文档只作为任务索引，记录任务入口、依赖、阻断状态和当前任务文档位置。本文档不承载需求正文、设计正文、执行日志或归档说明。

## 2. 当前任务事实源

| task layer | current entry | notes |
| --- | --- | --- |
| structured task state | `docs/governance/DOC_STATE.yaml` | 正式状态真值 |
| current task remap | `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` | 被状态层引用，保持原路径 |
| ST13 task docs | `docs/superpowers/plans/st13-task-packages/**` | 被状态层引用，保持原路径 |
| module task indexes | `docs/modules/M01-M10/MODULE_TASK_INDEX.md` | 模块级任务索引 |

## 3. 当前任务组

| group | scope | active entry | status |
| --- | --- | --- | --- |
| ST13_20 | 服务端保存 / 数据库边界 | `docs/superpowers/plans/st13-task-packages/ST13_20/` | formal window not open |
| ST13_21 | API / 后端服务边界 | `docs/superpowers/plans/st13-task-packages/ST13_21/` | formal window not open |
| ST13_24 | 测试 / 验收 / DoD | `docs/superpowers/plans/st13-task-packages/ST13_24/` | formal window not open |
| ST13_25 | 文档治理 / 收口 / 长期上下文 | `docs/superpowers/plans/st13-task-packages/ST13_25/` | formal window not open |

## 4. 任务使用规则

- 任务是否可实施以 `DOC_STATE.yaml` 和 doc-governor gate 为准。
- ST13 双文档当前仍在 plans 子目录下，因为状态层引用了这些路径。
- 本索引不把历史任务文档重新解释为当前任务入口。
- 本索引不声明任何任务 implementation-ready。

## 5. 关联输入

| input | purpose |
| --- | --- |
| `docs/requirements/workbench-mvp/**` | 任务验收依据 |
| `docs/design/workbench-mvp/**` | 任务设计依据 |
| `PLAN_LATEST.md` | 当前推进顺序 |
| `MODULE_INDEX.md` | 模块文档入口 |
