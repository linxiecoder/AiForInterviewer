# AI 模拟面试 P1 模块索引

## 1. 文档定位

- 本文档用于索引所有模块目录、模块职责、上游依赖、当前成熟度概况和阶段推进判断。
- 本文档用于让总控 Codex 快速判断：
  - 当前哪些模块成熟度最低
  - 哪些模块适合本轮优先推进
  - 哪些模块已具备进入子任务设计阶段的候选条件
- 详细任务状态见 [TASK_INDEX.md](TASK_INDEX.md)
- 详细成熟度见 [DOCUMENT_MATURITY.md](DOCUMENT_MATURITY.md)
- 当前轮次并行计划见 [DOCUMENT_PROGRESS.md](DOCUMENT_PROGRESS.md)
- 全局待确认问题见 [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

## 2. 模块表

| Module ID | 模块名称 | 模块目标 | 上游依赖 | 关联待确认问题 | 模块目录 | 当前整体成熟度 | 当前最低成熟度文档 | 是否可支撑下游 | 是否可进入子任务设计 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | 基础平台与工作台壳层 | 建立仓库结构、运行时、工作台壳层、i18n、测试与文档治理基线 | - | OQ-001、OQ-002、OQ-003 | `docs/modules/M01-foundation-and-platform/` | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M02 | 鉴权、团队与成员 | 定义身份模型、团队隔离、成员目录和权限矩阵 | M01 | OQ-004、OQ-005 | `docs/modules/M02-identity-and-team/` | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M03 | 岗位、简历与文档处理 | 定义岗位、简历、文档版本、上传、转换、预览与导出边界 | M01、M02 | OQ-006、OQ-007 | `docs/modules/M03-jobs-resumes-and-documents/` | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M04 | 匹配分析与训练证据 | 定义绑定关系、匹配分析、评分依据和训练证据输出 | M03 | OQ-008 | `docs/modules/M04-match-analysis-and-evidence/` | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M05 | 资产库、归档与检索 | 定义资产类型、资产对象、归档来源和检索入库机制 | M03、M04 | OQ-009、OQ-010 | `docs/modules/M05-assets-and-retrieval/` | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M06 | 模拟面试、上下文与导出 | 定义面试会话、上下文包、问题来源、消息流、报告与导出 | M03、M04、M05 | OQ-011、OQ-012、OQ-018 | `docs/modules/M06-simulated-interview-and-context/` | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M07 | 打磨模式、评估与进度 | 定义主题推荐、能力树、逐题评估和进度快照 | M06 | OQ-013、OQ-014 | `docs/modules/M07-polish-assessment-and-progress/` | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M08 | 复盘与回放 | 定义复盘对象、真实面试导入、回放与导出 | M06、M07 | OQ-015 | `docs/modules/M08-review-and-replay/` | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M09 | 训练中心与薄弱项生命周期 | 定义薄弱项聚合、训练抽屉、消减与停练规则 | M04、M07、M08 | OQ-014、OQ-016 | `docs/modules/M09-training-and-weakness-lifecycle/` | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |
| M10 | 管理台、治理与可观测性 | 定义成员治理、模型与规则配置、可观测性与运维入口 | M02、M03、M06、M09 | OQ-017、OQ-018 | `docs/modules/M10-admin-governance-and-observability/` | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 否 |

## 3. 当前成熟度与 readiness 总览

| Module ID | 当前主阶段 | 整体成熟度 | 当前最低成熟度文档 | 是否可进入子任务设计 | 主要阻塞 | 下一步优先动作 |
| --- | --- | --- | --- | --- | --- | --- |
| M01 | 需求初稿 + 设计骨架 | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | monorepo、最小基线、视觉粒度未收敛 | 先冻结默认平台口径，再推进模块设计与 schema / logic 骨架 |
| M02 | 需求初稿 + 设计骨架 | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 鉴权机制与权限矩阵未收敛 | 优先冻结默认鉴权口径和权限边界 |
| M03 | 需求初稿 + 设计骨架 | L2 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 渲染链与异步边界未收敛 | 优先收敛渲染链和异步边界 |
| M04 | 需求初稿 + 模块骨架 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | versioning、评分契约与异常路径未收敛 | 先收敛评分/versioning 默认口径 |
| M05 | 需求初稿 + 模块骨架 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | provider、归档粒度、检索入库链路未收敛 | 先明确 provider 与资产粒度口径 |
| M06 | 需求初稿 + 模块骨架 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | context pack、trace、snapshot/admin 边界未收敛 | 先拆清上下文包和 snapshot/admin ownership |
| M07 | 需求初稿 + 模块骨架 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 推荐机制、评估口径、能力树状态未收敛 | 先冻结推荐策略与共享评估口径 |
| M08 | 需求初稿 + 模块骨架 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | review 输入模型、复盘对象与导出边界未收敛 | 先冻结 review 输入模型和导出边界 |
| M09 | 需求初稿 + 模块骨架 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 聚合 key、生命周期规则、共享评估口径未收敛 | 先冻结弱项聚合和生命周期默认规则 |
| M10 | 需求初稿 + 模块骨架 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 否 | 管理台治理边界、模型来源、snapshot 运维职责未收敛 | 先冻结管理台范围和模型来源默认口径 |

## 4. 当前低成熟度重点模块

> 该节用于让总控 Codex 快速排序本轮优先推进模块。每轮评估后必须更新。

| 优先级 | Module ID | 当前整体判断 | 关键问题 | 是否建议本轮推进 |
| --- | --- | --- | --- | --- |
| P1 | M01 | 平台基础未定会放大后续返工 | monorepo、最小运行时、视觉基线未收敛 | 是 |
| P1 | M02 | 鉴权与权限矩阵会影响多个后续模块 | 鉴权方式与权限边界未定 | 是 |
| P1 | M03 | 文档处理边界会影响多个核心流程 | 渲染链与异步边界未定 | 是 |
| P2 | M04 | 依赖 M03 收敛后才能稳定深化 | versioning 与评分契约未定 | 条件推进 |
| P2 | M06 | 与 snapshot / admin 边界高度耦合 | context pack 和 ownership 未定 | 条件推进 |

## 5. 当前可进入子任务设计的模块

> 只有当模块整体达到 L5 候选且主要阻塞已收敛时，模块才应出现在这里。

- 暂无

## 6. 使用说明

- 模块状态变化后，应同步更新本文件、`TASK_INDEX.md`、`DOCUMENT_MATURITY.md` 和 `DOCUMENT_PROGRESS.md`。
- 模块边界变化后，应先更新对应模块目录下的 `MODULE_REQUIREMENTS.md` 与 `MODULE_DESIGN.md`。
- 若模块是否可进入子任务设计发生变化，必须同步更新：
  - `DOCUMENT_PROGRESS.md`
  - 对应模块的 `MODULE_TASK_INDEX.md`
- 总控 Codex 每轮必须在本文件中显式回写：
  - 当前最低成熟度模块
  - 当前是否可进入子任务设计
  - 当前下一步优先动作