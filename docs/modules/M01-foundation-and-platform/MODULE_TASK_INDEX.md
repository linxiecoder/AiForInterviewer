# M01 基础平台与工作台壳层 - 模块任务索引

## 0. Workbench MVP Design Canon 承接

- 当前正式设计事实源：`docs/design/workbench-mvp/`。
- 重点引用：`README.md`、`scope.md`、`information-architecture.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：工作台壳层、运行时边界、i18n、测试与文档治理基线。
- 后续补齐项：复核当前仓库与未来 monorepo 边界，保持不创建业务代码目录。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 0. W13 事实源与父级索引边界

- 当前产品范围事实只引用 Workbench MVP 正式设计事实源；本文件中的 `ST01_*` 仅用于模块内历史索引和结构归属说明，不激活旧任务，不新增正式子任务 ID。
- W10 `apps/web` 原型只能作为参考证据；当前仍暂停代码开发，回到设计文档补齐。
- 旧 `SUBTASK_DESIGN.md` / `SUBTASK_IMPLEMENTATION.md` 若仍为骨架或模板，不因被本索引链接而获得正式入口、candidate 或开窗资格。

| 历史 / 骨架文档 | 父级索引 | 当前用途 |
| --- | --- | --- |
| [`ST01_01/SUBTASK_DESIGN.md`](sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_DESIGN.md)、[`ST01_01/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST01_01-runtime-and-repo-baseline/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST01_01` | 历史结构归属与骨架留存，不作为正式子任务入口 |
| [`ST01_02/SUBTASK_DESIGN.md`](sub_modules/ST01_02-workspace-shell-and-i18n/SUBTASK_DESIGN.md)、[`ST01_02/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST01_02-workspace-shell-and-i18n/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST01_02` | 历史结构归属与骨架留存，不作为正式子任务入口 |
| [`ST01_03/SUBTASK_DESIGN.md`](sub_modules/ST01_03-testing-logging-and-doc-governance/SUBTASK_DESIGN.md)、[`ST01_03/SUBTASK_IMPLEMENTATION.md`](sub_modules/ST01_03-testing-logging-and-doc-governance/SUBTASK_IMPLEMENTATION.md) | 本文件第 1 节 `ST01_03` | 历史结构归属与骨架留存，不作为正式子任务入口 |

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 当前目标 | 当前状态 | 主要输入 | 当前阻塞 | 下一步触发条件 | 是否具备子任务设计前置条件 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ST01_01 | 运行环境与仓库基线 | 收敛 monorepo 目录、环境模板、本地基础设施占位、FastAPI 最小入口与健康检查 | 模块层继续收口 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` | `MQ-001` 已压缩到共享最小层，但 M01 整体仍是高 `L4`、接近整体 `L5` 候选但未接受；完整 workflow / lint / E2E 继续后置到 M10 | 需先由总控统一回写全局文档并复核整体接受条件；本轮不据此开放子任务设计 | 否 |
| ST01_02 | 工作台壳层与 i18n 基线 | 收敛 Dashboard 壳层、Page Header、i18n seed、列表原语与 shared adapter 边界 | 模块层继续收口 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` | `MQ-003`、`MQ-005` 已压缩到共享最小层，但 M01 整体仍未被接受；精确 props / callback / hook 细节继续后置 | 需先由总控完成整体复核与全局回写；本轮不据此开放 ST01_02 设计 | 否 |
| ST01_03 | 测试、日志与文档治理基线 | 收敛 pytest / vitest / 最小 CI、结构化日志入口和模块回写约束 | 模块层继续收口 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md` | `MQ-001` 与 shared adapter 最小验证面虽已压缩，但 M01 整体仍未被接受；完整 workflow / E2E / 可观测性治理边界仍由 M10 承接 | 需先由总控完成整体复核与全局回写；本轮不据此开放子任务设计 | 否 |

## 2. 推荐推进顺序

1. ST01_01：先固定目录、运行时和健康检查入口，否则后续壳层与验证基线无根可依。
2. ST01_02：在目录和入口稳定后，细化壳层、页面头部、shared adapter、i18n 和列表原语。
3. ST01_03：在最小运行时和共享组件边界稳定后，冻结测试、日志和 CI 基线。

## 3. 当前进入子任务设计判断

- 三个子任务都还不能进入子任务设计阶段。
- 直接原因不是子任务目录缺失，而是 M01 的 `requirements / design / api / schema / logic` 仍未达到 `L5`。
- 其中最关键的上游缺口是：
  - `MQ-001`、`MQ-003`、`MQ-005` 已压缩到共享最小层，但仍不足以把 M01 从高 `L4` 推进到已接受状态。
  - 当前未开子任务设计，主要因为 M01 仍只是高 `L4`、接近整体 `L5` 候选但未接受，总控也尚未完成全局回写。
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
