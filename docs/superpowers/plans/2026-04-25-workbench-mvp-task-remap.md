# AI 模拟面试一期工作台 MVP 任务重映射草案

## 1. 文档定位

本文档是 Workbench MVP 任务重映射 planning/task 文档。该路径被 `docs/governance/DOC_STATE.yaml` 的 `source_doc` 引用，本轮保持原路径。

本文档不承载需求正文、设计正文、执行日志、状态写回、formal window 或 implementation packet。

## 2. 上游输入

| input | use |
| --- | --- |
| `docs/requirements/workbench-mvp/**` | 需求范围、边界、验收口径 |
| `docs/design/workbench-mvp/**` | 设计分解依据 |
| `TASK_INDEX.md` | 当前任务索引 |
| `docs/governance/DOC_STATE.yaml` | 正式状态和 gate |

## 3. 当前任务分层

| layer | scope | entry |
| --- | --- | --- |
| product requirement | MVP 范围、边界、验收 | `docs/requirements/workbench-mvp/**` |
| product design | 信息架构、对象模型、RAG、多轮、评分、复盘、导出 | `docs/design/workbench-mvp/**` |
| implementation task candidate | 服务端保存、API 边界、测试验收、文档收口 | `docs/superpowers/plans/st13-task-packages/**` |
| state gate | formal window、packet、readiness | `docs/governance/DOC_STATE.yaml` |

## 4. 当前 ST13 任务包

| task | scope | docs | current gate status |
| --- | --- | --- | --- |
| ST13_20 | 服务端保存 / 数据库 | `docs/superpowers/plans/st13-task-packages/ST13_20/` | formal window not open |
| ST13_21 | API / 后端服务边界 | `docs/superpowers/plans/st13-task-packages/ST13_21/` | formal window not open |
| ST13_24 | 测试 / 验收 / DoD | `docs/superpowers/plans/st13-task-packages/ST13_24/` | formal window not open |
| ST13_25 | 文档治理 / 收口 / Basic Memory | `docs/superpowers/plans/st13-task-packages/ST13_25/` | formal window not open |

## 5. State-blocked 路径

以下路径被状态层引用，本轮不移动：

- `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`
- `docs/superpowers/plans/st13-task-packages/**`

## 6. 使用规则

- 任务拆分不得替代需求事实源或设计事实源。
- 任务文档不得因存在 required docs 自动成为 implementation-ready。
- formal window 和 implementation packet 必须由后续状态流程单独处理。
- 若后续要迁移 ST13 task docs 目录，必须先做状态层迁移计划。
