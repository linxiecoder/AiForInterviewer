# AI 模拟面试 P1 模块索引

## 1. 文档定位

- 本文档用于索引所有模块目录、模块职责、上游依赖、当前成熟度概况以及是否具备继续下游拆分的条件。
- 本文档是总控 Codex 判断“当前哪些模块优先推进”的核心入口之一。
- 详细任务状态见 [TASK_INDEX.md](TASK_INDEX.md)，详细成熟度见 [DOCUMENT_MATURITY.md](DOCUMENT_MATURITY.md)，详细阶段与并行计划见 [DOCUMENT_PROGRESS.md](DOCUMENT_PROGRESS.md)。
- 当模块边界、模块成熟度、最低成熟度文档、是否可进入子任务设计发生变化时，应同步更新本文档。

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

## 2.1 W10-C 首切片模块映射（历史参考）

- `RQ01` 和以下映射只用于解释 W10 原型探索期间的首切片关系层，不再作为当前一期工作台 MVP 的模块范围、模块优先级或正式开窗依据。
- 当前一期工作台 MVP 模块设计应回到 `PLAN_LATEST.md` 与四份 W13 唯一事实源。

| Module ID | 当前首切片角色 | 当前承接内容 | 本轮明确不做 |
| --- | --- | --- | --- |
| `M03` | 直接模块 | 承接岗位 JD 文本、简历 Markdown、最小对齐，以及面向 `M04 / M06` 的最小共享输入；`MT03_01 / MT03_03` 只作为观察蓝本 | 不重开 `ST03_*` 历史容器，不把观察蓝本写成正式开窗任务，不把上传 / 导出链重新拉回主链 |
| `M04` | 直接模块 | 承接岗位-简历绑定、首轮问题生成与最小证据组织；后续承接对象为 `ST04_01 / ST04_02` | 不在本轮确认完整评分标准、训练入口或正式子任务开窗 |
| `M06` | 直接模块 | 承接单轮会话创建、最小上下文包与 `1` 轮问答记录；后续承接对象为 `ST06_01 / ST06_02` | 不扩展到多轮会话、search snapshot、`ST06_03` 报告 / 导出链 |
| `M07` | 直接模块 | 承接简版反馈摘要与最小改进建议；后续承接对象为 `ST07_03` | 不扩展到训练中心、长期进度或跨场景统一评估框架定稿 |
| `M01` | 条件性支撑模块 | 仅在总控后续批准最小壳层 / 运行时 / 共享原语骨架时介入 | 当前不进入首切片主链，不单独开窗 |
| `M02 / M05 / M08 / M09 / M10` | W10 历史排除 | 登录与成员治理、资产 / RAG、复盘、训练中心、管理台 / 运维不进入 W10 首切片主链 | 不得外推为 W13 一期工作台 MVP 排除项；当前范围以 W13 唯一事实源为准 |

## 3. 当前成熟度与 readiness 总览

> 本节用于让总控 Codex 一眼判断：
> - 哪些模块最低成熟度最低
> - 哪些模块适合本轮优先推进
> - 哪些模块已经具备进入子任务设计阶段的候选条件
>
> 全量待确认模式补充：`FC-01~FC-19` 已完成用户确认；W13-E2 / State Remap dry-run 已收口，W13-E3 已创建 Preview YAML，W13-E4-B 阶段 1 已写入 `ST13_01~ST13_25`，W13-E4-C 阶段 2 已将旧 `STxx_*` facts 标记为 `historical-reference / superseded`，W13-E4-D 阶段 3 已完成 dry-run / 影响分析，W13-E4-E Stage3 Preview 已通过验证，W13-E4-F 已正式将 current 状态层任务入口收敛为 `ST13_01~ST13_25`。M01-M10 均不因确认卡完成、`WT13-xx` 候选任务域命名确认、preview 文件创建、阶段 1 状态层写入、阶段 2 旧任务历史化、阶段 3 dry-run、Stage3 Preview 通过或 Stage 3 正式写入而自动升级成熟度或放行下游，正式开窗仍需任务包、实施文档和用户确认共同闭合。
>
> 当前 W13 结论：
> - 当前最低成熟度模块仍为 `M04-M10`，但它们不再因为 W10 首切片被排除；真实原因是模块设计仍停留在骨架或初稿状态。
> - `M03 / M04 / M06 / M07` 的 W10 首切片直接模块身份只作历史参考，不等于 W13 当前优先级。
> - RAG / 知识库、多轮高阶面试、资产归档、复盘、训练抽屉和管理台入口已进入或影响一期工作台设计范围，不能继续按 W10 “后续排除”理解。
> - `OQ-024 / FC-16` 的正式映射已被总控写死，当前正式开窗层仍为空。

| Module ID | 整体成熟度 | 最低成熟度文档 | 当前阶段 | 是否可进入子任务设计 | 主要阻塞 |
| --- | --- | --- | --- | --- | --- |
| M01 | L4 | 模块核心文档当前整体并列高 `L4` | 收口复核 | 否 | 主口径已压回“接近整体 `L5` 候选但未接受”，且本轮目标项已清理完成；当前整体仍受核心文档并列高 `L4` 与总控未接受整体候选共同限制 |
| M02 | L4 | `MODULE_API_DESIGN.md`（高 `L4`） | 最低位 API 复核 | 否 | `GET /api/v1/members` 的共享最小层虽已在模块内闭合，且已通过 `FC-15A` 完成用户确认，但仍待 W13-F 回写；正式开窗层仍为空，且 `MT02_02` 的权限消费边界必须继续留在模块层 |
| M03 | L4 | `MODULE_API_DESIGN.md`（高 `L4`） | 最低位 API 复核 | 否 | `OQ-021 / OQ-025` 已稳定吸收，`OQ-024` 核心文档旧口径已清理；当前直接结构性主阻塞是正式开窗层为空、当前阶段关窗、上传 / 导出链依赖未变，最低位 API 继续为高 `L4` 是结果态 |
| M04 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | versioning、评分契约与异常路径未收敛 |
| M05 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | provider、归档粒度、检索入库链路未收敛 |
| M06 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | context pack、trace、snapshot/admin 边界未收敛 |
| M07 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | 推荐机制、评估口径、能力树状态未收敛 |
| M08 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | review 输入模型、复盘对象与导出边界未收敛 |
| M09 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | 聚合 key、生命周期规则、共享评估口径未收敛 |
| M10 | L1 | `MODULE_DESIGN.md` / `MODULE_API_DESIGN.md` / `MODULE_SCHEMA_DESIGN.md` / `MODULE_LOGIC_DESIGN.md` | 需求初稿 + 模块骨架 | 否 | 管理台治理边界、模型来源、snapshot 运维职责未收敛 |

## 4. 当前优先推进建议

> 本节由总控 Codex 每轮更新，用于明确“当前锁定的极窄任务包下先开哪些模块 Codex”。

| 优先级 | Module ID | 当前判断 | 建议本轮动作 | 原因 |
| --- | --- | --- | --- | --- |
| P0 | `global` | W13 事实源与任务索引仍需重构对齐 | 先完成引用审计、旧口径清理和 W13 任务重映射 | 当前正式开窗层为空，模块优先级不能继续沿用 W10 首切片 |
| P1 | `M06 / M08 / M09` | 与多轮、复盘、评分、训练闭环直接相关 | 后续由独立模块窗口按 W13 唯一事实源做模块侧同步，不开子任务窗口 | 这些能力已进入一期设计范围，但模块文档仍停留在 L1 或骨架状态 |
| P1 | `M05 / M10` | 与 RAG / 知识库、资产归档、管理台入口和运维边界相关 | 后续由独立模块窗口判断一期最小能力与后续增强边界 | W13 confirmed 范围已改变 W10 后置口径，需要模块层重新对齐 |
| P2 | `M01 / M02 / M03 / M04 / M07` | 仍需承接基础、权限、岗位简历、匹配分析和打磨模式 | 保持当前不放行实施；只在 W13 任务重映射后接收明确模块窗口 | 现有 L4/L1 判断不因 FC confirmed 自动升级 |

## 5. 可进入子任务设计的模块

> 只有当模块核心文档至少达到 L5 候选时，模块才应出现在这里。
> 当前轮次（W10-C 首切片关系补齐）复核结论：
> - 本轮不开放任何子任务 Codex，因此这里仍不登记正式可进入子任务设计的模块。
> - W10 首切片直接模块和后续承接对象只作历史参考，不等于 W13 正式子任务设计候选。
> - `M02 / M05 / M08 / M09 / M10` 不再按 W10 首切片排除项理解；是否进入后续模块同步窗口，取决于 W13 任务重映射。
> - 本轮只证明历史关系层已被降级和当前事实源已明确，未证明任何正式候选条件已闭合。

- 暂无

| 候选观察顺序 | Module ID | 当前判断 | 尚缺条件 |
| --- | --- | --- | --- |
| 1 | `global` | 先完成 W13 工作台级任务重映射 | `TASK_INDEX.md` 尚未按 W13 四份唯一事实源写入正式任务 ID 与开窗资格 |
| 2 | `M06 / M08 / M09` | 多轮、复盘、评分、训练闭环相关模块需要后续同步 | 模块文档仍未按 W13 confirmed 范围完成重切与成熟度提升 |
| 3 | `M05 / M10` | RAG / 知识库、资产归档、管理台与运维边界需要后续同步 | 一期最小能力与后续增强边界仍需模块窗口细化 |
| 4 | `M01 / M02 / M03 / M04 / M07` | 继续保持不放行实施；等待 W13 重映射后接收明确任务包 | 现有模块成熟度和正式开窗层均未满足子任务设计入口条件 |

## 6. W13-E / W13-E2 候选任务域到模块映射（阶段 3 已收敛 current 任务入口）

> 本节记录 W13 候选映射、W13-E4-B 阶段 1 正式状态层入口、W13-E4-C 阶段 2 旧 `STxx_*` 历史参考角色、W13-E4-D 阶段 3 dry-run 结论、W13-E4-E Stage3 Preview 结果，以及 W13-E4-F 正式 Stage 3 写入结果。不改变模块成熟度，不放行子任务设计或代码实施。用户已确认 `WT13-xx` 作为候选任务域命名；正式 `DOC_STATE.yaml.subtasks` 当前只使用 `ST13_01~ST13_25` 作为兼容状态层 ID。

| Module ID | W13 候选任务域 | 当前映射结论 | 后续模块窗口建议 |
| --- | --- | --- | --- |
| M01 | `WT13-02`、`WT13-20`、`WT13-21`、`WT13-22`、`WT13-23`、`WT13-24`、`WT13-25` | 承接工作台壳层、工程边界、API / 数据基础、测试和治理收口 | 先复核当前仓库与未来 monorepo 边界，不直接创建目录。 |
| M02 | `WT13-01`、`WT13-05`、`WT13-21` | 承接登录、session、角色、权限、记录可见范围 | 不把 `/members` 共享最小层闭合外推为正式实现 ready。 |
| M03 | `WT13-03`、`WT13-04`、`WT13-06`、`WT13-19` | 承接岗位、简历、发起必选输入和导出边界 | 不重开旧 `ST03_*`；上传 / 导出链仍需按 W13 重裁剪。 |
| M04 | `WT13-06`、`WT13-13`、`WT13-16` | 承接岗位-简历绑定、评分证据、评估版本和主题推荐输入 | 优先补评分证据与规则版本，避免沿用 W10 首轮问题生成口径。 |
| M05 | `WT13-10`、`WT13-18`、`WT13-20` | 承接 RAG / 知识库、检索引用、资产归档和动态 schema 子集 | 优先补知识库与资产边界，不把完整资产中心提前做大。 |
| M06 | `WT13-05`、`WT13-06`、`WT13-07`、`WT13-09`、`WT13-12`、`WT13-15` | 承接模拟记录列表、发起、面试台、压力面、状态机和模拟复盘 | 优先按记录列表默认入口与双模式重切，不沿用单轮会话主链。 |
| M07 | `WT13-08`、`WT13-12`、`WT13-13`、`WT13-17`、`WT13-19` | 承接打磨模式、进展树、题级反馈、训练入口和部分导出 | 明确打磨不固定轮次，和压力面评分分离。 |
| M08 | `WT13-05`、`WT13-09`、`WT13-14`、`WT13-15`、`WT13-18`、`WT13-19` | 承接真实 / 模拟复盘、逐题拆解、导出和归档入口 | 优先按 W13-D 补复盘模型，不沿用简版反馈。 |
| M09 | `WT13-08`、`WT13-14`、`WT13-15`、`WT13-16`、`WT13-17` | 承接 `WeaknessItem`、证据、消减、停练、训练抽屉和待打磨 | 区分薄弱项中心与待打磨执行层。 |
| M10 | `WT13-01`、`WT13-10`、`WT13-11`、`WT13-18`、`WT13-20`、`WT13-21`、`WT13-22`、`WT13-24`、`WT13-25` | 承接 provider、日志、模型 catalog、snapshot、审计、配置、部署和验收 | 先做最小运维 / 观测边界，完整管理台后置。 |

当前未发现必须立即重定义模块职责的硬冲突；后续模块窗口应在上述候选映射下同步模块文档，不直接开启子任务实现。旧 `STxx_*` 已从正式状态层 current `subtasks` 容器移出，仅作为历史结构、reusable evidence 和 archive candidate 保留在索引与阶段文档中。各模块当前正式任务入口指向 `ST13 / WT13`，不得误激活旧 `STxx_*`。

### 6.1 W13-E4-B 正式 `ST13_*` 模块映射

| Module ID | 已写入的正式状态层入口 | WT13 alias |
| --- | --- | --- |
| M01 | `ST13_01`、`ST13_02`、`ST13_20`、`ST13_21`、`ST13_22`、`ST13_23`、`ST13_24`、`ST13_25` | `WT13-01`、`WT13-02`、`WT13-20`、`WT13-21`、`WT13-22`、`WT13-23`、`WT13-24`、`WT13-25` |
| M02 | `ST13_05` | `WT13-05` |
| M03 | `ST13_03`、`ST13_04`、`ST13_06`、`ST13_17`、`ST13_19` | `WT13-03`、`WT13-04`、`WT13-06`、`WT13-17`、`WT13-19` |
| M04 | `ST13_11`、`ST13_13`、`ST13_16` | `WT13-11`、`WT13-13`、`WT13-16` |
| M05 | `ST13_07`、`ST13_10`、`ST13_18` | `WT13-07`、`WT13-10`、`WT13-18` |
| M06 | `ST13_08`、`ST13_09`、`ST13_12`、`ST13_15` | `WT13-08`、`WT13-09`、`WT13-12`、`WT13-15` |
| M07 | 暂无主模块归属；作为上游模块参与 `ST13_07`、`ST13_08`、`ST13_09`、`ST13_12`、`ST13_13`、`ST13_15`、`ST13_16`、`ST13_17`、`ST13_19` | 作为相关模块保留在 `facts.upstream_module_ids` |
| M08 | `ST13_14` | `WT13-14` |
| M09 | 暂无主模块归属；作为上游模块参与 `ST13_08`、`ST13_14`、`ST13_15`、`ST13_16`、`ST13_17` | 作为相关模块保留在 `facts.upstream_module_ids` |
| M10 | 暂无主模块归属；作为上游模块参与 `ST13_01`、`ST13_02`、`ST13_04`、`ST13_10`、`ST13_11`、`ST13_13`、`ST13_14`、`ST13_18`、`ST13_19`、`ST13_20`、`ST13_21`、`ST13_22`、`ST13_24`、`ST13_25` | 作为相关模块保留在 `facts.upstream_module_ids` |

### 6.2 W13-E4-F 旧 `STxx_*` 历史参考角色同步

> Stage 3 完成后，下表旧 `STxx_*` 不再是正式 `DOC_STATE.yaml.subtasks` current entity，只保留模块层历史参考和 archive-candidate 说明。

| Module ID | 旧 ST 范围 | 当前角色 | 当前 W13 承接入口 | 模块层结论 |
| --- | --- | --- | --- | --- |
| M01 | `ST01_01~ST01_03` | historical-reference / superseded | `ST13_02`、`ST13_20~ST13_25` | 旧工程与壳层骨架只作追溯；模块成熟度不升级。 |
| M02 | `ST02_01~ST02_03` | historical-reference / superseded | `ST13_01`、`ST13_21`、`ST13_22` | 旧鉴权 / 成员入口不再作为当前实现入口。 |
| M03 | `ST03_01~ST03_03` | historical-reference / superseded | `ST13_03`、`ST13_04`、`ST13_06`、`ST13_19`、`ST13_20`、`ST13_23` | 旧岗位 / 简历 / 导出链路需按 W13 事实源重切。 |
| M04 | `ST04_01~ST04_03` | historical-reference / superseded | `ST13_06`、`ST13_13`、`ST13_16`、`ST13_17`、`ST13_21`、`ST13_23` | 旧匹配分析骨架只保留历史价值。 |
| M05 | `ST05_01~ST05_03` | historical-reference / superseded | `ST13_10`、`ST13_18`、`ST13_20` | 旧资产 / 检索骨架不等于当前 RAG ready。 |
| M06 | `ST06_01~ST06_03` | historical-reference / superseded | `ST13_05~ST13_07`、`ST13_10~ST13_12`、`ST13_15`、`ST13_19`、`ST13_22` | 旧单轮会话链路不再作为当前模拟面试入口。 |
| M07 | `ST07_01~ST07_03` | historical-reference / superseded | `ST13_08`、`ST13_13`、`ST13_16`、`ST13_17` | 旧简版反馈 / 能力树骨架需按打磨模式重切。 |
| M08 | `ST08_01~ST08_03` | historical-reference / superseded | `ST13_14~ST13_16`、`ST13_18`、`ST13_19` | 旧复盘骨架只作历史参考，当前以真实 / 模拟复盘事实源为准。 |
| M09 | `ST09_01~ST09_03` | historical-reference / superseded | `ST13_16`、`ST13_17` | 旧训练中心骨架不等于训练抽屉 ready。 |
| M10 | `ST10_01~ST10_03` | historical-reference / superseded | `ST13_01`、`ST13_11`、`ST13_13`、`ST13_22`、`ST13_24`、`ST13_25` | 旧管理台 / 运维骨架需按 W13 最小运维边界重切。 |

### 6.3 W13-E5 ST13 到模块文档映射审计摘要

> 完整审计见 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`。本节只保留模块索引级结论，不改变任何模块成熟度，不创建 ST13 专属子任务文档。

| 模块 | W13-E5 结论 | 需要模块同步窗口 |
| --- | --- | --- |
| M01 | 支撑工作台壳层、数据 / API 基础、测试和治理入口；现有文档可作为高层输入，但不支撑 implementation-ready。 | 是，配合 `ST13_20/21/22/24/25` contract。 |
| M02 | 影响 `ST13_01/02/05/20/21/23`，且 `evaluate-state` 仍报告 `doc:api`、`doc:open_questions` template-like blocker。 | 是，优先级最高。 |
| M03 | 支撑岗位、简历、发起、导出和训练入口；旧 `ST03_*` 只能作为 reusable evidence。 | 是。 |
| M04 | 支撑评分证据、岗位简历绑定、WeaknessItem 输入；当前仍为 L1 骨架。 | 是。 |
| M05 | 支撑 RAG / 知识库、资产归档和数据持久化；当前仍需知识库与资产 contract。 | 是。 |
| M06 | 支撑模拟记录、发起、面试台、压力面、状态机和模拟复盘；不能沿用 W10 单轮主链。 | 是。 |
| M07 | 支撑打磨、进展树、评分反馈和训练入口；需明确不固定轮次。 | 是。 |
| M08 | 支撑真实 / 模拟复盘、导出和归档入口；需按 W13-D 重切复盘模型。 | 是。 |
| M09 | 支撑 WeaknessItem、训练抽屉、消减和停练规则；需区分薄弱项中心与待打磨执行层。 | 是。 |
| M10 | 支撑 provider、日志、模型 catalog、审计、配置、测试和治理收口；完整管理台后置。 | 是。 |

当前没有任何模块因 W13-E5 / W13-E8 / W13-E8.5 / W13-E9 而升级为可进入实现；`ST13_20`、`ST13_21`、`ST13_24`、`ST13_25` 已创建集中任务包双文档、登记 required doc slot，并完成第一批 contract 细化，但仍不是 implementation-ready。

### 6.4 W13-E6 第一批 contract 任务包草案模块影响

| ST13 | 草案主题 | 主要模块承载 | 当前结论 |
| --- | --- | --- | --- |
| `ST13_21` | API / 后端服务边界 | M01-M10；M02 需后续重点同步 | 已形成任务包草案；仍不是 implementation-ready |
| `ST13_20` | 服务端保存 / 数据库 | M01-M10；权限和持久化跨模块 | 已形成任务包草案；仍不是 implementation-ready |
| `ST13_24` | 测试 / 验收 / DoD | M01、M10、全模块 | 已形成任务包草案；仍不是 implementation-ready |
| `ST13_25` | 文档治理 / 收口 / Basic Memory | global、M01、M10 | 已形成任务包草案；仍不是 implementation-ready |

本轮不创建模块子任务目录，不修改 `docs/modules/**`，不改变旧 `STxx_*` 的历史参考定位。

### 6.5 W13-E7 第一批 contract 双文档准备模块影响

> 完整方案见 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`。本节只记录模块索引级映射，不创建模块子任务目录，不改变模块成熟度，不放行子任务设计或实现。

| ST13 | WT13 alias | 模块映射 | W13-E7 状态 | 模块层结论 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | M01-M10；M02 权限边界仍是重点 blocker | `double_doc_path_planned` | 可作为 API contract 双文档创建候选；不能实现 |
| `ST13_20` | `WT13-20` | M01-M10；权限、RAG、资产、导出和复盘均会消费数据 contract | `double_doc_path_planned` | 可作为数据 contract 双文档创建候选；不能实现 |
| `ST13_24` | `WT13-24` | M01、M10、全模块 | `double_doc_path_planned` | 可作为 testing / DoD 双文档创建候选；不能创建测试代码 |
| `ST13_25` | `WT13-25` | global、M01、M10 | `double_doc_path_planned` | 可作为治理双文档创建候选；不能写 `DOC_STATE.yaml` 或 Basic Memory |

当前推荐路径方案为方案 C：先只在 W13-E7 plan 中冻结路径和模板。若后续 W13-E8 采用方案 A 或用户自定义路径，应回写本节与 `TASK_INDEX.md`；若采用方案 B 创建模块子任务目录，必须额外防止被误读为 formal window open。

### 6.6 W13-E8 第一批 contract 双文档创建模块影响

> W13-E8 已采用 `OQ-111=A` 的集中任务包目录方案创建双文档。本节只做模块映射，不创建 `docs/modules/**` 子任务目录，不改变模块成熟度，不放行实现。

| ST13 | WT13 alias | 模块映射 | DESIGN 文档 | IMPLEMENTATION 文档 | 模块层结论 |
| --- | --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | M01-M10；M02 权限边界仍是重点 blocker | `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md` | `contract_refined`；不能实现 |
| `ST13_20` | `WT13-20` | M01-M10；权限、RAG、资产、导出和复盘均会消费数据 contract | `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md` | `contract_refined`；不能实现 |
| `ST13_24` | `WT13-24` | M01、M10、全模块 | `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_IMPLEMENTATION.md` | `contract_refined`；不能创建测试代码 |
| `ST13_25` | `WT13-25` | global、M01、M10 | `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md` | `contract_refined`；不能写 Basic Memory 或进入实现 |

W13-E8.5 已由单独 State Update 窗口完成 required doc slot 登记；该登记不改变模块成熟度，不创建 `docs/modules/**` 子任务目录，不打开 formal window。

### 6.7 W13-E9 第一批 contract 细化模块影响

> W13-E9 只细化集中任务包双文档，不修改 `docs/modules/**`，不改变模块成熟度，不放行子任务设计或代码实施。

| ST13 | WT13 alias | 模块映射 | W13-E9 状态 | 模块层结论 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | M01-M10；M02 权限边界仍需后续同步 | `contract_refined` | API contract 可作为 W13-E10 readiness 复核输入；不能创建 `apps/api/**`。 |
| `ST13_20` | `WT13-20` | M01-M10；权限、RAG、资产、导出和复盘均会消费数据 contract | `contract_refined` | 数据 contract 可作为 API / 测试复核输入；不能创建数据库、migration、ORM 或 SQL。 |
| `ST13_24` | `WT13-24` | M01、M10、全模块 | `contract_refined` | 测试 / DoD contract 可作为 required tests 拆分输入；不能创建 `tests/**`。 |
| `ST13_25` | `WT13-25` | global、M01、M10 | `contract_refined` | 治理收口 contract 可作为 W13-E10 / 后续写回窗口输入；当前不写 Basic Memory。 |

W13-E9 不改变 M01-M10 当前成熟度，不解除 M02 模块 blocker，不打开 formal window，不生成 implementation packet。

## 7. 使用说明

- 模块状态变化后，应同步更新本文档、`TASK_INDEX.md` 和 `DOCUMENT_MATURITY.md`。
- 模块边界变化后，应先更新对应模块目录下的 `MODULE_REQUIREMENTS.md` 与 `MODULE_DESIGN.md`。
- 模块从“不可以进入子任务设计”切换到“可进入子任务设计”前，必须同步更新：
  - `DOCUMENT_MATURITY.md`
  - `DOCUMENT_PROGRESS.md`
  - `MODULE_INDEX.md`
- 总控 Codex 每轮至少要检查：
  - 当前最低成熟度模块是否变化
  - 当前优先推进建议是否变化
  - 是否已有模块可进入子任务设计阶段
