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
| ST13_20 | 服务端保存 / 数据库边界 | `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/` | formal window not open |
| ST13_21 | API / 后端服务边界 | `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/` | formal window not open |
| ST13_24 | 测试 / 验收 / DoD | `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/` | formal window not open |
| ST13_25 | 文档治理 / 收口 / 长期上下文 | `docs/tasks/workbench-mvp/st13-task-packages/ST13_25/` | formal window not open |
| ST01_01 | 运行环境与仓库基线 | `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/` | 已存在正式状态 entry；`maturity=L4`；`readiness=downstream_ready`；scoped `formal_window_status=open`；`global_policy.formal_window_open=false`；`candidate_status=none`；`implementation_approval_status=approved`；`implementation_ready=true`；`can_generate_implementation_packet=true`；当前 implementation packet 已生成但允许范围仍仅限 ST01_01 文档 / 索引基线收口；尚未进入 runtime code 实现 |

## 4. 任务使用规则

- 任务是否可实施以 `DOC_STATE.yaml` 和 doc-governor gate 为准。
- ST13 双文档已迁入 `docs/tasks/workbench-mvp/st13-task-packages/**`，并已同步 `DOC_STATE.yaml` required doc slot。
- 本索引不把历史任务文档重新解释为当前任务入口；`ST01_01` 是从历史骨架重建并已登记正式状态 entry 的例外，当前 scoped formal window 已打开，`implementation_approval_status=approved`，`implementation_ready=true`，`can_generate_implementation_packet=true`；当前已生成的 implementation packet 只能用于文档 / 索引基线收口，不得直接创建 `apps/api/**`、修改 runtime code 或启动 M02/M03。
- `ST01_01` 的 `implementation_ready=true` 仅来自 official state 与 doc-governor gate；本索引不通过 Markdown 自行声明其他任务 implementation-ready。

## 5. 关联输入

| input | purpose |
| --- | --- |
| `docs/requirements/workbench-mvp/**` | 任务验收依据 |
| `docs/design/workbench-mvp/**` | 任务设计依据 |
| `PLAN_LATEST.md` | 当前推进顺序 |
| `MODULE_INDEX.md` | 模块文档入口 |
