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
| M04 | 匹配分析与训练证据 | 定义绑定关系、匹配分析、评分依据和训练证据输出 | M03 | OQ-008、OQ-025 | `docs/modules/M04-match-analysis-and-evidence/` | L1 | 否 |
| M05 | 资产库、归档与检索 | 定义资产类型、资产对象、归档来源和检索入库机制 | M03、M04 | OQ-009、OQ-010 | `docs/modules/M05-assets-and-retrieval/` | L1 | 否 |
| M06 | 模拟面试、上下文与导出 | 定义面试会话、上下文包、问题来源、消息流、报告与导出 | M03、M04、M05 | OQ-011、OQ-012、OQ-018、OQ-025 | `docs/modules/M06-simulated-interview-and-context/` | L1 | 否 |
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
> 当前轮次（最低位压缩轮）结论：
> - 当前最低成熟度模块为 `M04-M10`
> - `M01/M02/M03` 已整体提升到 `L4`，但当前推进方式已从“模块整体收口 + 候选白名单准备”切换为“最低位文档压缩 + 最小阻塞集合清理”
> - 当前接近“可进入子任务设计候选”的观察顺序调整为：`M02` > `M03`（仅简历聚合根链局部接近） > `M01`

| Module ID | 整体成熟度 | 最低成熟度文档 | 当前阶段 | 是否可进入子任务设计 | 主要阻塞 |
| --- | --- | --- | --- | --- | --- |
| M01 | L4 | `MODULE_OPEN_QUESTIONS.md` 仍是最低位（`L4`） | 最低位压缩 | 否 | 本轮只允许处理 `MQ-001`、`MQ-003`、`MQ-005`；`SC-05` 相关主题只保留为局部设计输入，不再回流为主阻塞 |
| M02 | L4 | `MODULE_API_DESIGN.md` 仍是最低位（高 `L4`） | 最低位 API 压缩 | 否 | 本轮只允许处理 `/members` 共享契约、`OQ-024` 映射引用与 `MT02_02` 权限消费边界；页面 / i18n / 验证面继续后置 |
| M03 | L4 | `MODULE_API_DESIGN.md` 仍是最低位（高 `L4`） | 最低位 API 压缩 | 否 | 本轮只允许处理共享最小映射与模块扩展边界、`OQ-025` 最小输入表述以及 route / callback 边界；上传 / 导出链继续后置 |
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
| P1 | M01 | 本轮最高优先级 | 只压缩 `MQ-001`、`MQ-003`、`MQ-005`，不再回到 `SC-05`、i18n 或共享页面原语主题 | `M01` 当前真正拖住成熟度判断的是最低位问题集合，而不是平台主题广度 |
| P1 | M02 | 本轮最高优先级 | 只压缩最低位 `MODULE_API_DESIGN.md`：`/members` 共享契约、映射引用、`MT02_02` 权限边界 | 模块整体最接近 `L5` 候选，但当前还没有任何正式可开窗任务 |
| P1 | M03 | 本轮最高优先级 | 只压缩最低位 `MODULE_API_DESIGN.md`：共享最小映射与模块扩展查询键边界、`OQ-025` 最小输入表述、route / callback 边界 | 其结果决定 `M04/M06` 可依赖的最小输入是否真正稳定 |
| P2 | M04 | 暂不主写 | 保持准备性阅读或轻量评审 | 依赖 M03 正式形成稳定输入 |
| P2 | M05 | 暂不主写 | 保持准备性阅读或轻量评审 | `OQ-009/OQ-010` 仍 open，且依赖 M03、M04 |
| P2 | M06 | 暂不主写 | 保持准备性阅读或轻量评审 | `OQ-012` 仍 open，且依赖 M03-M05 |
| P3 | M07 | 暂缓主写 | 先校准共享评估口径默认方案及其下游影响 | 依赖 M06 与跨模块评估框架 |
| P3 | M08 | 暂缓主写 | 先明确 review 输入模型默认方案与复盘对象边界 | 依赖 M06、M07 |
| P3 | M09 | 暂缓主写 | 先识别薄弱项聚合默认口径仍缺哪些关键规则 | `OQ-016` 仍 open，当前不宜进入主写 |
| P3 | M10 | 暂缓主写 | 先校准治理与 catalog 默认口径对范围的影响 | 依赖 M02、M03、M06、M09 |

## 5. 可进入子任务设计的模块

> 只有当模块核心文档至少达到 L5 候选时，模块才应出现在这里。
> 当前轮次（最低位压缩轮）复核结论：
> - 本轮不开放任何子任务 Codex，因此这里仍不登记正式可进入子任务设计的模块
> - `M02` 仍是当前最接近整体 `L5` 候选的模块；`M03` 只有少量链路接近候选；`M01` 继续停留在“接近整体 `L5` 候选但未到候选”的阶段
> - 在 `OQ-024` 完成正式映射、`OQ-021` 在三个模块最低位文档上完成稳定吸收、且评审再次确认“白名单候选不等于正式放行”前，不建议把任何模块放入正式候选名单
> - 白名单观察面只用于记录“当前允许继续收口的最小候选范围”，不等于“正式可进入子任务设计候选”

- 暂无

| 候选观察顺序 | Module ID | 当前判断 | 尚缺条件 |
| --- | --- | --- | --- |
| 1 | M02 | 模块整体接近 `L5` 候选，但当前只有 `MT02_01 / MT02_02` 属于条件性白名单观察面；`MT02_03 / MT02_07` 仍只是后续顺位 | `OQ-024` 的正式映射被写死、`OQ-021` 继续被最低位 API 文档完整吸收、`MT02_02` 的权限消费边界继续留在模块层 |
| 2 | M03 | 当前只有 `MT03_01 / MT03_03` 属于条件性白名单观察面；`MT03_02A / MT03_02B` 仍不进入当前白名单 | `OQ-025` 继续只被表述为最小共享输入、`OQ-021` 模块扩展漂移被稳定压实、最低位 API 文档不再承载关键共享歧义 |
| 3 | M01 | 接近整体 `L5` 候选，但仍不建议进入正式候选 | 模块整体完成 `MQ-001 / MQ-003 / MQ-005` 的最低位压缩，且 `MODULE_OPEN_QUESTIONS.md` 不再集中承载主阻塞 |

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
