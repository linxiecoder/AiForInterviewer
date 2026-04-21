# AI 模拟面试 P1 模块索引

## 1. 文档定位

- 本文档用于索引所有模块目录、模块职责、上游依赖、当前成熟度概况以及是否具备继续下游拆分的条件。
- 本文档是总控 Codex 判断“当前哪些模块优先推进”的核心入口之一。
- 详细任务状态见 [TASK_INDEX.md](TASK_INDEX.md)，详细成熟度见 [DOCUMENT_MATURITY.md](DOCUMENT_MATURITY.md)，详细阶段与并行计划见 [DOCUMENT_PROGRESS.md](DOCUMENT_PROGRESS.md)。
- 当模块边界、模块成熟度、最低成熟度文档、是否可进入子任务设计发生变化时，应同步更新本文件。

## 2. 模块表

| Module ID | 模块名称 | 模块目标 | 上游依赖 | 关联待确认问题 | 模块目录 | 当前成熟度 | 是否可支撑下游 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | 基础平台与工作台壳层 | 建立仓库结构、运行时、工作台壳层、i18n、测试与文档治理基线 | - | OQ-001、OQ-002、OQ-003、OQ-019、OQ-020、OQ-021、OQ-022 | `docs/modules/M01-foundation-and-platform/` | L4 | 否 |
| M02 | 鉴权、团队与成员 | 定义身份模型、团队隔离、成员目录和权限矩阵 | M01 | OQ-004、OQ-005、OQ-021、OQ-022、OQ-023、OQ-024 | `docs/modules/M02-identity-and-team/` | L4 | 否 |
| M03 | 岗位、简历与文档处理 | 定义岗位、简历、文档版本、上传、转换、预览与导出边界 | M01、M02 | OQ-006、OQ-007、OQ-020、OQ-021、OQ-024、OQ-025 | `docs/modules/M03-jobs-resumes-and-documents/` | L4 | 否 |
| M04 | 匹配分析与训练证据 | 定义绑定关系、匹配分析、评分依据和训练证据输出 | M03 | OQ-008 | `docs/modules/M04-match-analysis-and-evidence/` | L1 | 否 |
| M05 | 资产库、归档与检索 | 定义资产类型、资产对象、归档来源和检索入库机制 | M03、M04 | OQ-009、OQ-010 | `docs/modules/M05-assets-and-retrieval/` | L1 | 否 |
| M06 | 模拟面试、上下文与导出 | 定义面试会话、上下文包、问题来源、消息流、报告与导出 | M03、M04、M05 | OQ-011、OQ-012、OQ-018 | `docs/modules/M06-simulated-interview-and-context/` | L1 | 否 |
| M07 | 打磨模式、评估与进度 | 定义主题推荐、能力树、逐题评估和进度快照 | M06 | OQ-013、OQ-014 | `docs/modules/M07-polish-assessment-and-progress/` | L1 | 否 |
| M08 | 复盘与回放 | 定义复盘对象、真实面试导入、回放与导出 | M06、M07 | OQ-015 | `docs/modules/M08-review-and-replay/` | L1 | 否 |
| M09 | 训练中心与薄弱项生命周期 | 定义薄弱项聚合、训练抽屉、消减与停练规则 | M04、M07、M08 | OQ-014、OQ-016 | `docs/modules/M09-training-and-weakness-lifecycle/` | L1 | 否 |
| M10 | 管理台、治理与可观测性 | 定义成员治理、模型与规则配置、可观测性与运维入口 | M02、M03、M06、M09 | OQ-017、OQ-018、OQ-019、OQ-023 | `docs/modules/M10-admin-governance-and-observability/` | L1 | 否 |

## 3. 当前成熟度与 readiness 总览

> 本节用于让总控 Codex 一眼判断：
> - 哪些模块最低成熟度最低
> - 哪些模块适合本轮优先推进
> - 哪些模块已经具备进入子任务设计阶段的候选条件
>
> 本轮（`R-Refactor-01` / 计划重构执行轮）结论：
> - 当前最低成熟度模块为 `M04-M10`
> - `M01/M02/M03` 已整体提升到 `L4`，但推进方式已从“普通模块主写”切换为“共享契约冻结 + 模块重切”
> - 当前接近“可进入子任务设计候选”的观察顺序调整为：`M02` > `M03`（仅简历聚合根链局部接近） > `M01`

| Module ID | 整体成熟度 | 最低成熟度文档 | 当前阶段 | 是否可进入子任务设计 | 主要阻塞 |
| --- | --- | --- | --- | --- | --- |
| M01 | L4 | `MODULE_TASK_INDEX.md` / `MODULE_DEPENDENCIES.md` / `MODULE_OPEN_QUESTIONS.md` 维持高 `L4` | 共享契约收口 / 上游稳定化 | 否 | `OQ-019~OQ-022` 已全部形成 `proposed-default`，但共享下载 / 对象存储口径与 shared adapter 实现级边界仍待收口 |
| M02 | L4 | `MODULE_API_DESIGN.md` 仍是最低位（高 `L4`） | 模块重切 / `L5` 候选前复核 | 否 | 页面 adapter 仍受 `OQ-020/OQ-021/OQ-022` 吸收完成度与 `OQ-024` 入口映射策略约束 |
| M03 | L4 | `MODULE_SCHEMA_DESIGN.md` 仍是最低位（`L4`） | 模块重切 / 局部候选收紧 | 否 | `jobs.requirement_items_json` 仍缺最小输入契约；只有简历聚合根链局部接近候选，上传 / 导出链仍依赖 `M01` 共享下载口径 |
| M04 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | versioning、评分契约与异常路径未收敛 |
| M05 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | provider、归档粒度、检索入库链路未收敛 |
| M06 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | context pack、trace、snapshot/admin 边界未收敛 |
| M07 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | 推荐机制、评估口径、能力树状态未收敛 |
| M08 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | review 输入模型、复盘对象与导出边界未收敛 |
| M09 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | 聚合 key、生命周期规则、共享评估口径未收敛 |
| M10 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | 管理台治理边界、模型来源、snapshot 运维职责未收敛 |

## 4. 当前优先推进建议

> 本节由总控 Codex 每轮更新，用于明确“本轮先开哪些模块 Codex”。

| 优先级 | Module ID | 当前判断 | 建议本轮动作 | 原因 |
| --- | --- | --- | --- | --- |
| P1 | M01 | 本轮最高优先级 | 开启共享下载 / 对象存储口径收口与 shared adapter 边界补写两个模块窗口，不进入子任务层 | `M01` 仍是共享契约承接中心，其冻结结果继续决定 `M02-M10` 的稳定输入 |
| P1 | M02 | 本轮最高优先级 | 继续收紧 `MODULE_API_DESIGN.md`、同步 `OQ-024` 入口映射，并把页面类微任务明确留在后置队列 | 模块整体最接近 `L5` 候选，但页面面仍未 ready |
| P1 | M03 | 本轮最高优先级 | 继续细化岗位链 / 编辑器链边界，并为 `OQ-025` 提供可冻结输入 | 其结果决定 `M04/M06` 能否获得稳定岗位输入，并决定模块是否还能被视为整体候选 |
| P2 | M04 | 暂不主写 | 保持准备性阅读或轻量评审 | 依赖 M03 正式形成稳定输入 |
| P2 | M05 | 暂不主写 | 保持准备性阅读或轻量评审 | `OQ-009/OQ-010` 仍 open，且依赖 M03、M04 |
| P2 | M06 | 暂不主写 | 保持准备性阅读或轻量评审 | `OQ-012` 仍 open，且依赖 M03-M05 |
| P3 | M07 | 暂缓主写 | 先校准共享评估口径默认方案及其下游影响 | 依赖 M06 与跨模块评估框架 |
| P3 | M08 | 暂缓主写 | 先明确 review 输入模型默认方案与复盘对象边界 | 依赖 M06、M07 |
| P3 | M09 | 暂缓主写 | 先识别薄弱项聚合默认口径仍缺哪些关键规则 | `OQ-016` 仍 open，当前不宜进入主写 |
| P3 | M10 | 暂缓主写 | 先校准治理与 catalog 默认口径对范围的影响 | 依赖 M02、M03、M06、M09 |

## 5. 可进入子任务设计的模块

> 只有当模块核心文档至少达到 L5 候选时，模块才应出现在这里。
> 本轮（`R-Refactor-01`）复核结论：
> - 本轮不开放任何子任务 Codex，因此这里仍不登记正式可进入子任务设计的模块
> - `M02` 是当前最接近整体 `L5` 候选的模块；`M03` 只有简历聚合根链局部接近候选；`M01` 仍需先完成共享契约稳定化
> - 在 `OQ-024` 完成全局入口映射、`OQ-025` 至少形成可下发的默认口径、且 `M01` 共享下载 / 对象存储口径稳定前，不建议把任何模块放入正式候选名单

- 暂无

| 候选观察顺序 | Module ID | 当前判断 | 尚缺条件 |
| --- | --- | --- | --- |
| 1 | M02 | 模块整体接近 `L5` 候选，但页面 adapter 与入口映射仍未 ready | `MODULE_API_DESIGN.md` 继续收紧、`OQ-022` 页面吸收完成、`OQ-024` 明确全局映射后仍维持“不直开子任务”的一致口径 |
| 2 | M03 | 只有 `MT03_03/MT03_04` 所在简历聚合根链局部接近候选，模块整体未 ready | `OQ-025` 至少形成默认口径、`MT03_02/MT03_05` 继续拆细、`M01` 共享下载 / 对象存储口径成熟 |
| 3 | M01 | 仍不建议进入候选 | 共享下载 / 对象存储与 shared adapter 边界形成稳定上游输入，且不再承担本轮主共享契约收口角色 |

## 6. 使用说明

- 模块状态变化后，应同步更新本文件、`TASK_INDEX.md` 和 `DOCUMENT_MATURITY.md`。
- 模块边界变化后，应先更新对应模块目录下的 `MODULE_REQUIREMENTS.md` 与 `MODULE_DESIGN.md`。
- 模块从“不可进入子任务设计”切换到“可进入子任务设计”前，必须同步更新：
  - `DOCUMENT_MATURITY.md`
  - `DOCUMENT_PROGRESS.md`
  - `MODULE_INDEX.md`
- 总控 Codex 每轮至少要检查：
  - 当前最低成熟度模块是否变化
  - 当前优先推进建议是否变化
  - 是否已有模块可进入子任务设计阶段
