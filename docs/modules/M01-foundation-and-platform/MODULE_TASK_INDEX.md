# M01 基础平台与工作台壳层 - 模块任务索引

## 1. 模块任务总表

| Subtask ID | 子任务名称 | 当前目标 | 当前状态 | 主要输入 | 当前阻塞 | 下一步触发条件 | 是否具备子任务设计前置条件 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ST01_01 | 运行环境与仓库基线 | 收敛 monorepo 目录、环境模板、本地基础设施占位、FastAPI 最小入口与健康检查 | 等待模块 L5 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md` | 根目录脚本与最小 CI 命令矩阵未冻结；模块核心文档整体仍未到 `L5` | 冻结根目录脚本 / 验证矩阵，并将 M01 设计包推进到 `L5` | 否 |
| ST01_02 | 工作台壳层与 i18n 基线 | 收敛 Dashboard 壳层、Page Header、i18n seed、列表原语与 shared adapter 边界 | 等待模块 L5 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md` | shared adapter 职责边界虽已补写，但列表查询状态的实现级接口、locale 规则和视觉范围仍未冻结 | 吸收 shared adapter 默认口径，并继续冻结列表状态 / locale / 页面状态边界 | 否 |
| ST01_03 | 测试、日志与文档治理基线 | 收敛 pytest / vitest / 最小 CI、结构化日志入口和模块回写约束 | 等待模块 L5 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_DEPENDENCIES.md` | 最小验证矩阵与 CI 覆盖边界未冻结；shared adapter 相关验证面仍需与 ST01_02 对齐；与 M10 的治理加固边界仍需区分 | 冻结最小验证矩阵，并明确 shared adapter 与 M10 治理加固的职责切分 | 否 |

## 2. 推荐推进顺序

1. ST01_01：先固定目录、运行时和健康检查入口，否则后续壳层与验证基线无根可依。
2. ST01_02：在目录和入口稳定后，细化壳层、页面头部、shared adapter、i18n 和列表原语。
3. ST01_03：在最小运行时和共享组件边界稳定后，冻结测试、日志和 CI 基线。

## 3. 当前进入子任务设计判断

- 三个子任务都还不能进入子任务设计阶段。
- 直接原因不是子任务目录缺失，而是 M01 的 `requirements / design / api / schema / logic` 仍未达到 `L5`。
- 其中最关键的上游缺口是：
  - 根目录脚本与最小 CI 命令矩阵未冻结。
  - `PageHeader`、Dashboard 摘要区与 `ListQueryState` 的 shared adapter 职责边界已补写到模块层，但列表查询状态的完整实现级接口、request adapter 签名与 resolved copy 承载方式仍未冻结。
  - locale 最小 fallback / namespace 已形成默认冻结口径，但完整的 URL / 持久化级策略仍未冻结。

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
