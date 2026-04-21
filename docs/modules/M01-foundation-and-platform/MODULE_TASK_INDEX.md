# M01 基础平台与工作台壳层 - 模块任务索引

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 当前目标 | 当前状态 | 主要输入 | 当前阻塞 | 下一步触发条件 | 是否具备子任务设计前置条件 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ST01_01 | 运行环境与仓库基线 | 收敛 monorepo 目录、环境模板、本地基础设施占位、FastAPI 最小入口与健康检查 | 等待模块 L5 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` | 根目录最小脚本命名、health check 与 API / Web 双 lane 已冻结；当前仍等待 M01 整体 `L5` 候选判断，以及把完整 workflow / lint / E2E 后置到 M10 | 总控接受 M01 进入 `L5` 候选，并保持完整治理矩阵留在 M10 / 后续轮次 | 否 |
| ST01_02 | 工作台壳层与 i18n 基线 | 收敛 Dashboard 壳层、Page Header、i18n seed、列表原语与 shared adapter 边界 | 等待模块 L5 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` | shared adapter 共享最小层已冻结；当前仍等待 M01 整体 `L5` 候选判断，精确 props / callback / hook 细节留待子任务设计收敛 | 总控接受 M01 共享最小层为下游输入，并正式开放 ST01_02 设计 | 否 |
| ST01_03 | 测试、日志与文档治理基线 | 收敛 pytest / vitest / 最小 CI、结构化日志入口和模块回写约束 | 等待模块 L5 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md` | API / Web 双 lane 已冻结；shared adapter 最小验证面已可引用；当前仍等待 M01 整体 `L5` 候选判断，且完整 workflow / E2E / 可观测性治理边界需由 M10 承接 | 总控接受 M01 进入 `L5` 候选，并明确 M10 承接完整治理强化边界 | 否 |

## 2. 推荐推进顺序

1. ST01_01：先固定目录、运行时和健康检查入口，否则后续壳层与验证基线无根可依。
2. ST01_02：在目录和入口稳定后，细化壳层、页面头部、shared adapter、i18n 和列表原语。
3. ST01_03：在最小运行时和共享组件边界稳定后，冻结测试、日志和 CI 基线。

## 3. 当前进入子任务设计判断

- 三个子任务都还不能进入子任务设计阶段。
- 直接原因不是子任务目录缺失，而是 M01 的 `requirements / design / api / schema / logic` 仍未达到 `L5`。
- 其中最关键的上游缺口是：
  - `MQ-001`、`MQ-003`、`MQ-005` 已压缩到共享最小层，不再要求继续扩张 M01 共享契约。
  - 当前未开子任务设计，主要因为 M01 整体 `L5` 候选尚待总控复核与全局回写，而不是因为这三项仍缺少方向级口径。
  - 完整 workflow / lint / E2E、多平台矩阵、精确 props / callback / hook 与完整 locale 持久化策略仍故意后置，不属于本轮 M01 共享前置。

## 4. 受 shared adapter 边界调整影响的旧入口与下游任务

| 入口 / 任务 | 类型 | 受影响原因 | 当前处理要求 |
| --- | --- | --- | --- |
| `ST01_02` | M01 模块内入口 | 需要吸收页面容器、request adapter、shared primitive 与 i18n 消费的职责切分 | 继续停留在模块层收口，不开放子任务设计 |
| `ST02_01`、`ST02_02` | M02 旧入口 | 历史上把 auth backend、page adapter 与 list contract 混在同一入口 | 仅保留历史来源，不再作为正式新入口 |
| `MT02_05`、`MT02_06` | M02 下游任务 | 需要直接引用 M01 的 i18n / shared page primitive / list adapter 边界 | 等 M02 继续吸收 `OQ-020~022` 后再开 |
| `ST03_01`、`ST03_02` | M03 旧入口 | 历史上混合页面投影、共享列表 contract 与渲染承接 | 保持历史入口，不直接开窗 |
| `MT03_02`、`MT03_05` | M03 下游任务 | 依赖 `PageHeader` / 摘要区 / `ListQueryState` / shared render boundary | 等共享契约继续稳定后再推进设计 |

## 5. 使用规则

- 模块内推进顺序应优先参考依赖关系和开放问题数量。
- 子任务设计先成熟，再推进子任务实施。
- 任何子任务若需要补模块级共享契约，应先回写 M01 模块文档，而不是在子任务文档中临时发明。
