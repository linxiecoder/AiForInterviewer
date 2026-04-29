# M01 基础平台与工作台壳层 - 模块任务索引

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`README.md`、`scope.md`、`information-architecture.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：工作台壳层、运行时边界、i18n、测试与文档治理基线。
- 后续补齐项：复核当前仓库与未来 monorepo 边界，保持不创建业务代码目录。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不自动提升正式状态层成熟度，不放行 formal window、implementation packet 或代码实现。

## 0. 当前输入与父级索引边界

- 当前产品范围事实只引用 Workbench MVP 当前设计输入；本文件中的 `ST01_*` 用于 M01 模块内结构归属、正式入口重建或历史索引说明，是否具备正式状态仍以 `docs/governance/DOC_STATE.yaml` 为准。
- 历史 frontend prototype 只作为 historical context；当前任务状态以 `TASK_INDEX.md`、`docs/governance/DOC_STATE.yaml` 和当前任务文档为准。
- `ST01_01` 双文档已由历史骨架重建为 approval readiness 审查输入；正式 `DOC_STATE.yaml` 已存在 `subtasks.ST01_01` entry，且 `implementation_doc_state=active_working_doc`、`maturity=L4`、`readiness=downstream_ready`、scoped `formal_window_status=open`、`global_policy.formal_window_open=false`、`candidate_status=none`、`implementation_approval_status` 未登记 / 未批准、`implementation_ready=false`。
- `ST01_02` / `ST01_03` 的旧 `SUBTASK_DESIGN.md` / `SUBTASK_IMPLEMENTATION.md` 若仍为骨架或模板，不因被本索引链接而获得正式入口、candidate 或开窗资格。

| 子任务文档 | 父级索引 | 当前用途 |
| --- | --- | --- |
| [`ST01_01/SUBTASK_DESIGN.md`](sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_DESIGN.md)、[`ST01_01/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST01_01` | 已存在正式状态 entry；`implementation_doc_state=active_working_doc`；scoped formal window 已打开；仍未写 implementation approval，`implementation_ready=false` |
| [`ST01_02/SUBTASK_DESIGN.md`](sub_modules/ST01_02-workspace-shell-and-i18n/SUBTASK_DESIGN.md)、[`ST01_02/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST01_02-workspace-shell-and-i18n/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST01_02` | 历史结构归属与骨架留存，不作为正式子任务入口 |
| [`ST01_03/SUBTASK_DESIGN.md`](sub_modules/ST01_03-testing-logging-and-doc-governance/SUBTASK_DESIGN.md)、[`ST01_03/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST01_03-testing-logging-and-doc-governance/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST01_03` | 历史结构归属与骨架留存，不作为正式子任务入口 |

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 当前目标 | 当前状态 | 主要输入 | 当前阻塞 | 下一步触发条件 | 是否具备子任务设计前置条件 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ST01_01 | 运行环境与仓库基线 | 收敛 monorepo 目录、环境模板、本地基础设施占位、FastAPI 最小入口与健康检查 | approval readiness 审查输入；`maturity=L4`；`readiness=downstream_ready`；scoped `formal_window_status=open`；`candidate_status=none`；`implementation_ready=false` | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`SUBTASK_DESIGN.md`、`SUBTASK_IMPLEMENTATION.md` | `implementation_approval_status` 未登记 / 未批准；当前仅剩 `gate:implementation_approval_missing`；不得创建 `apps/api/**`、`infra/**` 或运行时代码 | 由独立 state-only approval confirmation 或 approval preview 窗口处理 implementation approval；通过 gate 后才可判断 packet | 是，仅限 ST01_01 approval readiness 审查；不代表 implementation-ready |
| ST01_02 | 工作台壳层与 i18n 基线 | 收敛 Dashboard 壳层、Page Header、i18n seed、列表原语与 shared adapter 边界 | 模块层继续收口 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` | M01 已是 `maturity=L5`、`readiness=downstream_ready`，但只支撑 ST01 入口和后续审查；精确 props / callback / hook 细节继续后置 | 需先完成 ST01_01 formal window 结果回写；本轮不开放 ST01_02 设计 | 否 |
| ST01_03 | 测试、日志与文档治理基线 | 收敛 pytest / vitest / 最小 CI、结构化日志入口和模块回写约束 | 模块层继续收口 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md` | `MQ-001` 与 shared adapter 最小验证面虽已压缩，但 ST01_03 仍未正式开放；完整 workflow / E2E / 可观测性治理边界仍由 M10 承接 | 需等待 ST01_01 最小运行时和 ST01_02 壳层边界稳定；本轮不开放 ST01_03 设计 | 否 |

## 2. 推荐推进顺序

1. ST01_01：先固定目录、运行时和健康检查入口，否则后续壳层与验证基线无根可依。
2. ST01_02：在目录和入口稳定后，细化壳层、页面头部、shared adapter、i18n 和列表原语。
3. ST01_03：在最小运行时和共享组件边界稳定后，冻结测试、日志和 CI 基线。

## 3. 当前进入子任务设计判断

- ST01_01 已存在正式状态 entry，可作为后续 approval readiness 审查输入；当前 `maturity=L4`、`readiness=downstream_ready`、scoped `formal_window_status=open`、`candidate_status=none`、`implementation_approval_status` 未登记 / 未批准、`implementation_ready=false`。
- ST01_01 scoped formal window 已打开，但不代表 `candidate_status=candidate`，不代表 implementation approval，不能生成 implementation packet，也不代表 `implementation_ready`。
- ST01_02 / ST01_03 当前仍不能进入正式子任务设计阶段。
- M01 的根目录脚本命名、health check 与 API / Web 双 lane 已收敛为共享最小层；当前 M01 已是 `maturity=L5`、`readiness=downstream_ready`，但该状态只支撑 ST01 子任务入口与后续审查。
- 完整 workflow / lint / E2E、多平台矩阵、精确 props / callback / hook 与完整 locale 持久化策略仍故意后置，不属于本轮 M01 共享前置。

## 4. 受 shared adapter 边界调整影响的旧入口与下游任务

| 入口 / 任务 | 类型 | 受影响原因 | 当前处理要求 |
| --- | --- | --- | --- |
| `ST01_02` | M01 模块内入口 | 需要吸收页面容器、request adapter、shared primitive 与 i18n 消费的职责切分 | 继续停留在模块层收口，不开放子任务设计 |
| `ST02_01`、`ST02_02` | M02 旧入口 | 历史上把 auth backend、page adapter 与 list contract 混在同一入口 | 仅保留历史来源，不再作为正式新入口 |
| `MT02_05`、`MT02_06` | M02 下游任务 | 需要直接引用 M01 的 i18n / shared page primitive / list adapter 边界 | 继续等待上游与 M01 口径稳定，不应据此判断可进入下一阶段 |
| `ST03_01`、`ST03_02` | M03 旧入口 | 历史上混合页面投影、共享列表 contract 与渲染承接 | 保持历史入口，不据此新增窗口 |
| `MT03_02`、`MT03_05` | M03 下游任务 | 依赖 `PageHeader` / 摘要区 / `ListQueryState` / shared render boundary | 继续等待共享契约稳定，不应据此判断可进入下一阶段 |

## 5. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。
- 任何子任务若需要补模块级共享契约，应先回写 M01 模块文档，而不是在子任务文档中临时发明。
- ST01_01 的 formal entry rebuilt 只改变该子任务的文档入口状态，不扩大到 ST01_02 / ST01_03。
