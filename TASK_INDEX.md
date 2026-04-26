# AI 模拟面试 P1 任务索引

> 本索引用于全局任务导航，不替代模块目录下的 `MODULE_TASK_INDEX.md`。  
> 状态使用：`todo` / `doing` / `done` / `blocked` / `need-clarification`。  
> 当前状态主要表示文档建设状态，不表示代码开发状态。
> `FC-01~FC-19` 已完成用户确认；当前一期 MVP 任务拆分必须以 W13 四份唯一事实源为准。
> W10 `RQ01` 首切片关系层只保留为历史参考，不再作为当前一期工作台 MVP 的正式任务映射。
> 用户已确认 `WT13-xx` 作为 W13 候选任务域命名；阶段 1 已用兼容的 `ST13_01~ST13_25` 写入正式 `DOC_STATE.yaml.subtasks`，阶段 2 已在旧 `STxx_*` facts 中表达 `historical-reference / superseded`，阶段 3 已正式将旧 `STxx_*` 从 current `subtasks` 容器移出，并将 `RQ01.facts.task_ids` 收敛为 `ST13_01~ST13_25`。
> 当前正式开窗层仍为空；W13-E8 已创建第一批 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的集中任务包双文档，W13-E8.5 已登记 required doc slot，W13-E9 已完成第一批 contract 细化，W13-E10 已完成第一批 readiness review，W13-E11 已完成第一批文档层 formal window candidate 评估，W13-E12 已完成 State Update 准备和确认卡输出，W13-E13 已创建 candidate state preview 但验证失败，W13-E13.5 已完成 candidate 状态表达策略修正，W13-E13.6 已完成 facts-only Preview，W13-E13.8 已在 docs/governance/previews 路径 Preview 严格全绿后完成 `ST13_24 / ST13_25` facts-only 正式 State Update，W13-E14-Merge 已完成四个并行 formal window 前置补齐窗口的合并核验。状态只能记为 `formal_window_preconditions_refined` / `near-ready blocker refined` / `not implementation-ready`，formal window、implementation packet 和真实服务接入仍需后续单独窗口。

## 1. 模块任务索引

| Task ID | 名称 | 父任务 | 前置依赖 | 状态 | 文档成熟度 | 是否具备实施条件 | 对应文档路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | 基础平台与工作台壳层 | - | - | doing | L4 可评审 | 否 | `docs/modules/M01-foundation-and-platform/` |
| M02 | 鉴权、团队与成员 | - | M01 | doing | L4 可评审 | 否 | `docs/modules/M02-identity-and-team/` |
| M03 | 岗位、简历与文档处理 | - | M01、M02 | doing | L4 可评审 | 否 | `docs/modules/M03-jobs-resumes-and-documents/` |
| M04 | 匹配分析与训练证据 | - | M03 | blocked | L1 骨架 | 否 | `docs/modules/M04-match-analysis-and-evidence/` |
| M05 | 资产库、归档与检索 | - | M03、M04 | blocked | L1 骨架 | 否 | `docs/modules/M05-assets-and-retrieval/` |
| M06 | 模拟面试、上下文与导出 | - | M03、M04、M05 | blocked | L1 骨架 | 否 | `docs/modules/M06-simulated-interview-and-context/` |
| M07 | 打磨模式、评估与进度 | - | M06 | blocked | L1 骨架 | 否 | `docs/modules/M07-polish-assessment-and-progress/` |
| M08 | 复盘与回放 | - | M06、M07 | blocked | L1 骨架 | 否 | `docs/modules/M08-review-and-replay/` |
| M09 | 训练中心与薄弱项生命周期 | - | M04、M07、M08 | blocked | L1 骨架 | 否 | `docs/modules/M09-training-and-weakness-lifecycle/` |
| M10 | 管理台、治理与可观测性 | - | M02、M03、M06、M09 | blocked | L1 骨架 | 否 | `docs/modules/M10-admin-governance-and-observability/` |

## 1.1 `RQ01` 首切片关系映射（W10-C，历史参考）

> 本节仅解释 W10 原型探索期间的 `RQ01` 关系层来源。该关系已被 `DD-018`、`DD-019` 和 W13 唯一事实源取代，不再作为当前一期工作台 MVP 范围、模块优先级或正式开窗依据。

| 层级 | 对象 | 当前角色 | 当前结论 |
| --- | --- | --- | --- |
| requirement | `RQ01` | W10 首切片历史 requirement 入口 | 承载“岗位 JD 手工输入 + 简历 Markdown 粘贴/编辑 -> 首轮问题 -> 1 轮问答 -> 简版反馈摘要”的最小闭环；仅作历史来源追踪 |
| direct module | `M03` | 输入侧能力 | 承接岗位 JD 文本、简历 Markdown、最小对齐，以及面向 `M04 / M06` 的最小共享输入；`MT03_01 / MT03_03` 仅为观察蓝本 |
| direct module | `M04` | 问题生成与最小证据 | 承接岗位-简历绑定、首轮问题生成与最小证据组织；后续承接对象为 `ST04_01 / ST04_02` |
| direct module | `M06` | 单轮会话与上下文 | 承接单轮会话创建、最小上下文包与 `1` 轮问答记录；后续承接对象为 `ST06_01 / ST06_02` |
| direct module | `M07` | 简版反馈与最小改进建议 | 承接简版反馈摘要与最小改进建议；后续承接对象为 `ST07_03` |
| conditional support | `M01` | 条件性支撑模块 | 仅在总控后续批准最小壳层 / 运行时 / 共享原语骨架时介入；当前不进入首切片主链 |
| excluded | `M02 / M05 / M08 / M09 / M10` | W10 历史排除 | 登录与成员治理、资产 / RAG、复盘、训练中心、管理台 / 运维不进入 W10 首切片关系主链；不得外推为 W13 一期工作台 MVP 排除项 |

## 2. 子任务索引

> 当前轮次口径：
> - `RQ01` 已承载 W13 工作台级当前任务入口 `ST13_01~ST13_25`；W10 首切片只保留为历史来源追踪。
> - `ST02_*`、`ST03_*` 只保留为历史容器，禁止作为当前及后续直开窗口。
> - `OQ-024 / FC-16` 的总控正式映射已写死；`M02`、`M03` 的观察蓝本当前仍不是正式子任务 ID。
> - 白名单观察面 != 正式子任务 ID != 可开窗任务；本轮仍不允许开启任何子任务窗口。
> - `M03` 仍只观察 `MT03_01 / MT03_03`；`ST04_01 / ST04_02 / ST06_01 / ST06_02 / ST07_03` 仅为历史后续承接对象，不等于当前 W13 正式开窗任务。
> - 本轮收口后正式开窗层仍为空；阶段 3 已将正式状态层 current 任务入口收敛为 `ST13_01~ST13_25`，但仍不等于可开实施窗口。
> - 下表中的旧 `STxx_*` 行只保留为历史索引 / reusable evidence / archive candidate，不再对应正式 `DOC_STATE.yaml.subtasks` current entity，也不再是 current implementation entry。

| Task ID | 名称 | 父任务 | 前置依赖 | 状态 | 文档成熟度 | 是否具备实施条件 | 对应文档路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ST01_01 | 运行环境与仓库基线 | M01 | M01 | todo | 仅有骨架 | 否 | `docs/modules/M01-foundation-and-platform/sub_modules/ST01_01-runtime-and-repo-baseline/` |
| ST01_02 | 工作台壳层与 i18n 基线 | M01 | M01 | todo | 仅有骨架 | 否 | `docs/modules/M01-foundation-and-platform/sub_modules/ST01_02-workspace-shell-and-i18n/` |
| ST01_03 | 测试、日志与文档治理基线 | M01 | M01 | todo | 仅有骨架 | 否 | `docs/modules/M01-foundation-and-platform/sub_modules/ST01_03-testing-logging-and-doc-governance/` |
| ST02_01 | 鉴权机制与会话边界（旧入口） | M02 | M01、M02 | blocked | 历史容器，禁止直开 | 否 | `docs/modules/M02-identity-and-team/sub_modules/ST02_01-auth-mechanism-boundary/` |
| ST02_02 | 团队、用户与成员目录（旧入口） | M02 | M01、M02 | blocked | 历史容器，禁止直开 | 否 | `docs/modules/M02-identity-and-team/sub_modules/ST02_02-team-user-member-domain/` |
| ST02_03 | 授权矩阵与管理员/成员边界（旧入口） | M02 | M01、M02 | blocked | 历史容器，禁止直开 | 否 | `docs/modules/M02-identity-and-team/sub_modules/ST02_03-authorization-matrix/` |
| ST03_01 | 岗位域与页面（旧入口） | M03 | M01、M02、M03 | blocked | 历史容器，禁止直开 | 否 | `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_01-job-domain-and-pages/` |
| ST03_02 | 简历域、版本与编辑器（旧入口） | M03 | M01、M02、M03 | blocked | 历史容器，禁止直开 | 否 | `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_02-resume-domain-versioning-and-editor/` |
| ST03_03 | 上传、转换与导出链路（旧入口） | M03 | M01、M02、M03 | blocked | 历史容器，禁止直开 | 否 | `docs/modules/M03-jobs-resumes-and-documents/sub_modules/ST03_03-upload-transform-export/` |
| ST04_01 | 岗位-简历绑定与输入契约 | M04 | M03、M04 | todo | 仅有骨架 | 否 | `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_01-bindings-and-input-contract/` |
| ST04_02 | 匹配分析、评分与证据 | M04 | M03、M04 | todo | 仅有骨架 | 否 | `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_02-analysis-scoring-and-evidence/` |
| ST04_03 | 分析展示与训练入口 | M04 | M03、M04 | todo | 仅有骨架 | 否 | `docs/modules/M04-match-analysis-and-evidence/sub_modules/ST04_03-analysis-ui-and-training-entry/` |
| ST05_01 | 资产类型与资产域 | M05 | M03、M04、M05 | todo | 仅有骨架 | 否 | `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_01-asset-type-and-asset-domain/` |
| ST05_02 | 归档记录与来源追踪 | M05 | M03、M04、M05 | todo | 仅有骨架 | 否 | `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_02-archive-records-and-source-linkage/` |
| ST05_03 | 检索分块与索引入库 | M05 | M03、M04、M05 | todo | 仅有骨架 | 否 | `docs/modules/M05-assets-and-retrieval/sub_modules/ST05_03-retrieval-chunking-and-index-ingestion/` |
| ST06_01 | 面试会话创建与列表 | M06 | M03、M04、M05、M06 | todo | 仅有骨架 | 否 | `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_01-interview-session-bootstrap/` |
| ST06_02 | 上下文包与问题来源规则 | M06 | M03、M04、M05、M06 | todo | 仅有骨架 | 否 | `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_02-context-pack-and-question-source/` |
| ST06_03 | 消息 Trace、报告与导出 | M06 | M03、M04、M05、M06 | todo | 仅有骨架 | 否 | `docs/modules/M06-simulated-interview-and-context/sub_modules/ST06_03-message-trace-report-and-export/` |
| ST07_01 | 打磨主题推荐与启动 | M07 | M06、M07 | todo | 仅有骨架 | 否 | `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_01-practice-topic-recommendation/` |
| ST07_02 | 能力树蓝图与节点状态 | M07 | M06、M07 | todo | 仅有骨架 | 否 | `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_02-capability-tree-and-node-state/` |
| ST07_03 | 逐题评估与进度快照 | M07 | M06、M07 | todo | 仅有骨架 | 否 | `docs/modules/M07-polish-assessment-and-progress/sub_modules/ST07_03-assessment-and-progress/` |
| ST08_01 | 复盘总对象与列表/详情 | M08 | M06、M07、M08 | todo | 仅有骨架 | 否 | `docs/modules/M08-review-and-replay/sub_modules/ST08_01-review-aggregate/` |
| ST08_02 | 真实面试导入与逐题分析 | M08 | M06、M07、M08 | todo | 仅有骨架 | 否 | `docs/modules/M08-review-and-replay/sub_modules/ST08_02-real-interview-intake/` |
| ST08_03 | 模拟面试复盘回放与导出 | M08 | M06、M07、M08 | todo | 仅有骨架 | 否 | `docs/modules/M08-review-and-replay/sub_modules/ST08_03-simulated-review-replay/` |
| ST09_01 | 薄弱项聚合与训练中心 | M09 | M04、M07、M08、M09 | todo | 仅有骨架 | 否 | `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_01-weakness-aggregation/` |
| ST09_02 | 训练抽屉与待打磨入列 | M09 | M04、M07、M08、M09 | todo | 仅有骨架 | 否 | `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_02-training-drawer-and-intake/` |
| ST09_03 | 生命周期、消减与停练规则 | M09 | M04、M07、M08、M09 | todo | 仅有骨架 | 否 | `docs/modules/M09-training-and-weakness-lifecycle/sub_modules/ST09_03-lifecycle-rules/` |
| ST10_01 | 成员治理与角色操作 | M10 | M02、M03、M06、M09、M10 | todo | 仅有骨架 | 否 | `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_01-admin-member-and-role-ops/` |
| ST10_02 | 模型目录、评分规则与系统设置 | M10 | M02、M03、M06、M09、M10 | todo | 仅有骨架 | 否 | `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_02-models-rules-and-settings/` |
| ST10_03 | 可观测性、CI/E2E 与 snapshot 运维 | M10 | M02、M03、M06、M09、M10 | todo | 仅有骨架 | 否 | `docs/modules/M10-admin-governance-and-observability/sub_modules/ST10_03-observability-ci-and-snapshot-ops/` |

## 2.1 计划重构观察入口（非正式子任务 ID）

- `M01`：当前无白名单观察面；本轮目标项已清理完成，当前无需继续开模块清理窗；`ST01_*` 仍只作为规划入口，不得在当前阶段直开。
- `M02`：当前观察入口以 `MT02_01 ~ MT02_08` 为蓝本，但只允许把 `MT02_01 / MT02_02` 记为条件性白名单观察面；`FC-15A / FC-16A` 已确认共享最小层与正式开窗边界，但在 W13-F 回写并由总控写入正式任务 ID 前，不得把模块内闭合外推为 `MT02_04 / MT02_06` ready，`MT02_02` 权限消费边界仍须留在模块层复核。
- `M03`：当前观察入口以 `MT03_01`、`MT03_02A`、`MT03_02B`、`MT03_03` 等蓝本为准；只允许把 `MT03_01 / MT03_03` 记为条件性白名单观察面，且应理解为“已吸收但未放行”；若后续继续推进，只允许围绕“正式开窗层为空 + 当前阶段关窗 + 上传 / 导出链依赖未变”的直接结构性主阻塞复核展开，上传 / 导出链继续不得视为可直开子任务。

## 2.2 `OQ-024` 正式映射（已写死）

- 历史容器层：`ST02_01`、`ST02_02`、`ST02_03`、`ST03_01`、`ST03_02`、`ST03_03` 全部固定为历史容器，禁止作为当前及后续直开窗口。
- 观察蓝本层：
  - `M01`：当前无白名单观察面。
  - `M02`：当前只允许 `MT02_01 / MT02_02` 作为条件性白名单观察蓝本；`MT02_03 / MT02_07` 只保留为后续顺位；`MT02_04 / MT02_05 / MT02_06 / MT02_08` 当前不得进入观察面。
  - `M03`：当前只允许 `MT03_01 / MT03_03` 作为条件性白名单观察蓝本；`MT03_02A / MT03_02B` 当前不得进入观察面。
- 正式开窗层：当前轮次正式子任务 ID 名单固定为空；只有总控在后续正式候选复评完成后，才能在本文件中新增正式子任务 ID 与开窗资格。

## 2.3 W10 首切片后续承接对象（历史 / 非正式开窗）

- `ST04_01 / ST04_02`：后续承接 `M04` 的岗位-简历绑定、首轮问题生成与最小证据组织，不等于本轮正式开窗任务。
- `ST06_01 / ST06_02`：后续承接 `M06` 的单轮会话创建、问题来源约束与 `1` 轮问答记录，不扩展到 `ST06_03` 的报告 / 导出链。
- `ST07_03`：后续承接 `M07` 的简版反馈摘要、逐题评估投影与最小改进建议，不等于训练中心或长期进度开窗。
- 当前正式开窗层固定为空；W10 后续承接对象不得直接升级为 W13 一期工作台 MVP 正式子任务 ID。

## 2.4 W13-E 工作台级任务重映射草案（阶段 3 已收敛状态层）

> 本节登记 W13-E / W13-E2 候选任务树摘要，以及 W13-E4-B 阶段 1 已写入的正式状态层入口。
> `WT13-xx` 已由用户确认为候选任务域命名；正式 `DOC_STATE.yaml.subtasks` key 使用兼容的 `ST13_01~ST13_25`。
> W13-E4-C 阶段 2 曾用旧 `STxx_*` facts 表达 historical / superseded；W13-E4-F 阶段 3 已将旧任务从正式 current `subtasks` 容器移出，旧任务不作为当前 W13 实施入口。
> W13-E4-D 阶段 3 dry-run 已确认：旧 `STxx_*` 仍被全局索引和模块任务索引作为历史追溯引用；用户已确认下一步先做 Stage3 Preview，并在 Preview 中同步验证 `RQ01.facts.task_ids` 移除旧 `ST01_01`、`ST09_03` 的方案。
> W13-E4-E Stage3 Preview 已通过；W13-E4-F 已基于用户确认方案 B 正式写入：formal `subtasks` 只保留 `ST13_01~ST13_25`，旧 `STxx_*` formal current 数量为 0，formal `RQ01.facts.task_ids` 只保留 `ST13_01~ST13_25`。
> 下表 `当前状态=blocked` 表示已写入正式状态层但仍不具备实施条件，不表示 `WT13-xx` 命名待确认。

| 候选 ID | 任务域 | 关联模块 | 当前状态 | 是否具备实施条件 | 说明 |
| --- | --- | --- | --- | --- | --- |
| WT13-01 | 账号 / 登录 / 权限 | M02、M10、M01 | blocked | 否 | 承接 session cookie、普通用户 / 管理员、记录可见范围。 |
| WT13-02 | 工作台首页 / 导航 / 权限入口 | M01、M02、M10 | blocked | 否 | 承接左侧导航、顶部账号区、行动型摘要和后续能力低干扰入口。 |
| WT13-03 | 岗位管理 | M03、M04 | blocked | 否 | 承接 `Job` 列表、详情、创建编辑和发起必选输入。 |
| WT13-04 | 简历管理 | M03、M10 | blocked | 否 | 承接 `Resume` 服务端保存、版本、上传 / 粘贴 / 编辑。 |
| WT13-05 | 模拟记录列表 | M06、M08、M02 | blocked | 否 | 模拟面试模块默认入口，承接权限可见范围、继续、复盘、导出入口。 |
| WT13-06 | 发起模拟面试 | M03、M04、M05、M06、M07 | blocked | 否 | 承接岗位、简历、知识库、模式选择和参考材料包。 |
| WT13-07 | 面试台 | M06、M05、M07、M08 | blocked | 否 | 承接真实 LLM、多轮、RAG 引用、暂停 / 继续和完成触发。 |
| WT13-08 | 打磨模式 | M07、M06、M09 | blocked | 否 | 承接 `ProgressTree`、题级反馈、下一题建议和用户结束决策。 |
| WT13-09 | 压力面模式 | M06、M08、M07 | blocked | 否 | 承接 `InterviewQuestionSet`、题组完成和最终评估。 |
| WT13-10 | RAG / 知识库 | M05、M06、M08、M10 | blocked | 否 | 承接知识库、检索、引用、无命中 / 失败降级。 |
| WT13-11 | 真实 LLM provider / adapter | M10、M06、M04、M08 | blocked | 否 | 承接可插拔 provider、默认真实 provider、脱敏记录和失败重试。 |
| WT13-12 | 多轮上下文 / 状态机 | M06、M07、M08 | blocked | 否 | 承接 `InterviewContext`、轮次、turn、暂停 / 继续和模式结束条件。 |
| WT13-13 | 评分体系 | M04、M07、M08、M10 | blocked | 否 | 承接 `0-100` 多维评分、证据绑定、规则版本和重算 / 修订。 |
| WT13-14 | 真实面试复盘 | M08、M09、M10 | blocked | 否 | 承接逐字稿输入、LLM 自动识别问答边界和逐题拆解。 |
| WT13-15 | 模拟面试复盘 | M08、M06、M07、M09 | blocked | 否 | 承接整场判断、多维评分、岗位匹配、通过概率、逐题点评。 |
| WT13-16 | 薄弱项 `WeaknessItem` | M09、M04、M07、M08 | blocked | 否 | 承接中粒度训练主题、证据、聚合、消减和停练。 |
| WT13-17 | 训练抽屉 / 待打磨清单 | M09、M07、M08、M03 | blocked | 否 | 承接归并、加入待打磨、立即打磨、暂不处理和影响预览。 |
| WT13-18 | 资产归档 | M05、M08、M10 | blocked | 否 | 承接整份 / 单题归档、资产类型和动态字段子集。 |
| WT13-19 | Markdown 导出 / 复制 | M07、M08、M03、M10 | blocked | 否 | 承接 `ExportSnapshot`、复制内容和 Markdown 下载。 |
| WT13-20 | 服务端保存 / 数据库 | M01、M02-M10 | blocked | 否 | 承接 PostgreSQL 和核心对象持久化。 |
| WT13-21 | API / 后端服务边界 | M01、M10、M02-M09 | blocked | 否 | 承接 Auth、Job、Resume、Knowledge、Interview、Review、Score、Export 等 API contract。 |
| WT13-22 | 日志 / 观测 / 运维 | M10、M01 | blocked | 否 | 承接应用日志、LLM 日志、RAG 日志、权限审计和配置边界。 |
| WT13-23 | 前端工作台 UI / 页面集合 | M01-M10 | blocked | 否 | 承接登录、工作台、岗位、简历、知识库、记录、发起、面试台、复盘和导出页面。 |
| WT13-24 | 测试 / 验收 / DoD | M01、M10、全模块 | blocked | 否 | 承接产品、数据、UI、工程、收口五层 DoD 测试矩阵。 |
| WT13-25 | 文档治理 / 收口 / Basic Memory | global、M01、M10 | blocked | 否 | 承接任务索引、模块映射、状态层迁移方案、收口记录和后续写回。 |

### 2.4.1 W13-E4-B 正式状态层入口

| 正式状态层 ID | WT13 alias | 主模块 | 当前状态 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| ST13_01 | WT13-01 | M01 | blocked | 否 |
| ST13_02 | WT13-02 | M01 | blocked | 否 |
| ST13_03 | WT13-03 | M03 | blocked | 否 |
| ST13_04 | WT13-04 | M03 | blocked | 否 |
| ST13_05 | WT13-05 | M02 | blocked | 否 |
| ST13_06 | WT13-06 | M03 | blocked | 否 |
| ST13_07 | WT13-07 | M05 | blocked | 否 |
| ST13_08 | WT13-08 | M06 | blocked | 否 |
| ST13_09 | WT13-09 | M06 | blocked | 否 |
| ST13_10 | WT13-10 | M05 | blocked | 否 |
| ST13_11 | WT13-11 | M04 | blocked | 否 |
| ST13_12 | WT13-12 | M06 | blocked | 否 |
| ST13_13 | WT13-13 | M04 | blocked | 否 |
| ST13_14 | WT13-14 | M08 | blocked | 否 |
| ST13_15 | WT13-15 | M06 | blocked | 否 |
| ST13_16 | WT13-16 | M04 | blocked | 否 |
| ST13_17 | WT13-17 | M03 | blocked | 否 |
| ST13_18 | WT13-18 | M05 | blocked | 否 |
| ST13_19 | WT13-19 | M03 | blocked | 否 |
| ST13_20 | WT13-20 | M01 | blocked | 否 |
| ST13_21 | WT13-21 | M01 | blocked | 否 |
| ST13_22 | WT13-22 | M01 | blocked | 否 |
| ST13_23 | WT13-23 | M01 | blocked | 否 |
| ST13_24 | WT13-24 | M01 | blocked | 否 |
| ST13_25 | WT13-25 | M01 | blocked | 否 |

### 2.4.2 W13-E5 readiness audit 摘要

> W13-E5 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`。该审计只判断任务包准备前置条件，不生成 implementation packet，不打开 formal window，不标记 implementation-ready。

| 分类 | ST13 | 结论 |
| --- | --- | --- |
| `ready_for_task_packet_candidate` | `ST13_20`、`ST13_21`、`ST13_24`、`ST13_25` | 仅表示可作为下一窗口任务包草案候选；仍需用户确认、双文档、验收标准和 required tests。 |
| `blocked_by` 上游 | `ST13_01`、`ST13_02`、`ST13_05`、`ST13_20`、`ST13_21`、`ST13_23` | 额外带 `module:M02` blocker；不得据此进入实现。 |
| `not_ready` | 其余 `ST13_*` | 依赖 API contract、数据 / 权限、LLM / RAG、状态机、评分、复盘、UI 或测试任务包。 |

当前统一缺口：25 个 ST13 均缺 ST13 专属任务设计文档、实施说明文档、验收标准、测试要求和 formal window。任何 `ready_for_task_packet_candidate` 都不是 `ready_for_implementation`。

### 2.4.3 W13-E6 第一批 contract 任务包草案摘要

> W13-E6 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`。该文档只生成第一批任务包草案，不创建正式子任务目录，不生成 implementation packet，不打开 formal window，不标记 implementation-ready。

- 用户确认：`OQ-101=A`、`OQ-102=A`、`OQ-103=A`、`OQ-104=B`、`OQ-105=A`、`OQ-106=A`、`OQ-107=A`、`OQ-108=A`、`OQ-109=A`、`OQ-110=C`。
- 第一批顺序：`ST13_21 -> ST13_20 -> ST13_24 -> ST13_25`。
- 当前状态：四个任务均为 `task_packet_draft_created` / `not_ready_for_implementation`；正式状态层中的 25 个 ST13 仍 blocked。
- W13-E7 结果：已形成第一批双文档路径和模板准备方案；当时状态为 `double_doc_path_planned` / `not_ready_for_implementation`。
- W13-E8 结果：用户已确认 `OQ-111=A`、`OQ-112=A`、`OQ-113=B`，并已创建第一批正式双文档；仍不得实现。
- W13-E8.5 结果：已把第一批 8 个双文档登记到 required doc slot；仍不得实现。
- W13-E9 结果：已细化第一批四个 ST13 的 API、数据、测试和治理 contract；仍不得实现、不得生成 implementation packet、不得打开 formal window。

### 2.4.4 W13-E7 第一批 contract 双文档准备摘要

> W13-E7 已新增 `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`。该文档只冻结路径方案、模板结构、任务包前置清单、contract 摘要、父索引同步方案和确认卡，不创建正式双文档，不更新 `DOC_STATE.yaml` required doc slot，不生成 implementation packet，不打开 formal window。

| ST13 | WT13 alias | 当前 W13-E7 状态 | 推荐路径方案 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | `task_packet_draft_created` / `double_doc_path_planned` | 方案 C：先只在 W13-E7 plan 冻结路径和模板 | 否 |
| `ST13_20` | `WT13-20` | `task_packet_draft_created` / `double_doc_path_planned` | 方案 C：先只在 W13-E7 plan 冻结路径和模板 | 否 |
| `ST13_24` | `WT13-24` | `task_packet_draft_created` / `double_doc_path_planned` | 方案 C：先只在 W13-E7 plan 冻结路径和模板 | 否 |
| `ST13_25` | `WT13-25` | `task_packet_draft_created` / `double_doc_path_planned` | 方案 C：先只在 W13-E7 plan 冻结路径和模板 | 否 |

截至 W13-E7 仍缺正式 `DESIGN` / `IMPLEMENTATION` 双文档实体、required doc slot 写回、验收标准落盘、required tests 落盘和用户确认；W13-E8 已补齐第一批四个 ST13 的双文档实体，W13-E8.5 已补齐 required doc slot，但 formal window 和 implementation-ready 仍未形成。

### 2.4.5 W13-E8 第一批 ST13 正式双文档创建摘要

> W13-E8 已按用户确认的 `OQ-111=A`、`OQ-112=A`、`OQ-113=B` 创建集中任务包目录和正式双文档。W13-E8.5 已登记 required doc slot。W13-E9 已完成第一批 contract 细化。当前状态只表示 `contract_refined`，不表示 formal window open，不表示 implementation-ready。

| ST13 | WT13 alias | DESIGN 文档 | IMPLEMENTATION 文档 | 当前状态 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md` | `contract_refined` / `not implementation-ready` / `formal window closed` / `implementation packet forbidden` | 否 |
| `ST13_20` | `WT13-20` | `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md` | `contract_refined` / `not implementation-ready` / `formal window closed` / `implementation packet forbidden` | 否 |
| `ST13_24` | `WT13-24` | `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_IMPLEMENTATION.md` | `contract_refined` / `not implementation-ready` / `formal window closed` / `implementation packet forbidden` | 否 |
| `ST13_25` | `WT13-25` | `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md` | `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md` | `contract_refined` / `not implementation-ready` / `formal window closed` / `implementation packet forbidden` | 否 |

W13-E8.5 已另窗把上述 8 个文档路径登记到 `DOC_STATE.yaml` 既有 `facts.design_doc` / `facts.implementation_doc` slot；这只解除第一批四个 ST13 的 required doc slot 缺口，不解除 formal window、implementation doc activation、acceptance criteria、required tests 或 implementation scope blocker。

### 2.4.6 W13-E9 第一批 ST13 contract 细化摘要

> W13-E9 只做文档清理和 contract 细化，不写代码，不创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`，不修改 `DOC_STATE.yaml`，不生成 implementation packet，不打开 formal window。

| ST13 | WT13 alias | contract_refined 摘要 | 仍未闭合事项 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | API / 后端服务边界已细化 Auth、Account / Role / Permission、Job、Resume、Knowledge、Retrieval、Interview、Question / Follow-up、Answer、Feedback / Score、SessionRecord、Markdown Export、Admin / Ops、错误和 LLM / RAG 失败 contract。 | formal window、implementation doc activation、acceptance criteria、required tests、implementation scope、M02 权限 blocker。 | 否 |
| `ST13_20` | `WT13-20` | 服务端保存 / 数据库 contract 已细化账号权限、岗位、简历、知识库、检索、面试、回答、反馈评分、弱项训练、资产导出、LLM 生成、脱敏、归档、审计和 schema version。 | formal window、schema / migration / ORM 授权、required tests、implementation scope、M02 权限 blocker。 | 否 |
| `ST13_24` | `WT13-24` | 测试 / 验收 / DoD contract 已细化产品、数据、UI、工程、收口、API、数据库、RAG、LLM、多轮、打磨、压力面、评分复盘、Markdown 导出、错误态、权限、安全、临时产物、浏览器验证和分层测试。 | formal window、测试代码授权、required tests 落到每个实施窗口、implementation scope。 | 否 |
| `ST13_25` | `WT13-25` | 文档治理 / 收口 / Basic Memory contract 已细化唯一事实源、OQ/DD/backlog、State Write 记录、archive、Basic Memory 检索与回读、fallback 包、Superpowers、确认项闭环、收口报告、过时检查、引用检查和未来写回窗口。 | formal window、Basic Memory 写回授权、后续收口窗口、implementation scope。 | 否 |

当前结论：第一批 contract 已完成 W13-E11 formal window candidate 评估，可作为后续 State Update 输入，但不能生成 implementation packet，不能打开 formal window，不能进入实现。

### 2.4.7 W13-E10 第一批 ST13 readiness 复核摘要

> W13-E10 只做 readiness review、缺口审计、formal window candidate 判断和确认卡输出；不修改 `DOC_STATE.yaml`，不生成 implementation packet，不打开 formal window，不进入实现。

| ST13 | WT13 alias | W13-E10 状态建议 | 仍未闭合事项 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | `near_ready_for_formal_window_candidate` | M02 权限 blocker、State Update、formal window 用户确认、OpenAPI / `apps/api/**` 授权 | 否 |
| `ST13_20` | `WT13-20` | `near_ready_for_formal_window_candidate` | M02 权限 blocker、State Update、schema / migration / ORM 授权、formal window 用户确认 | 否 |
| `ST13_24` | `WT13-24` | `ready_for_formal_window_candidate` | State Update、测试文件授权、formal window 用户确认 | 否 |
| `ST13_25` | `WT13-25` | `ready_for_formal_window_candidate` | State Update、Basic Memory / Superpowers 写回授权、formal window 用户确认 | 否 |

当前结论：四个 ST13 可以进入 W13-E11 formal window candidate 评估；但该结论不等于 `candidate_status=candidate`，不等于 formal window open，不等于 implementation-ready。

### 2.4.8 W13-E11 第一批 ST13 formal window candidate 评估摘要

> 用户已确认 `OQ-114=A`、`OQ-115=B`、`OQ-116=A`、`OQ-117=A`。W13-E11 只形成文档层 candidate 评估，不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet，不进入实现。

| ST13 | WT13 alias | W13-E11 文档层结论 | 后续 State Update 建议 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | `near_ready_for_formal_window_candidate_confirmed` | 不建议直接写为 `candidate_status=candidate`；先保留 near-ready 解释，等待 M02 blocker 或用户另行确认 | 否 |
| `ST13_20` | `WT13-20` | `near_ready_for_formal_window_candidate_confirmed` | 不建议直接写为 `candidate_status=candidate`；先保留 near-ready 解释，等待 M02 blocker 或 schema 授权 | 否 |
| `ST13_24` | `WT13-24` | `formal_window_candidate_recommended` | 建议后续 State Update 评估是否写入 candidate 相关状态 | 否 |
| `ST13_25` | `WT13-25` | `formal_window_candidate_recommended` | 建议后续 State Update 评估是否写入 candidate 相关状态 | 否 |

当前结论：W13-E11 不等于正式状态层 candidate 写入，不等于 formal window open，不等于 implementation-ready。

### 2.4.9 W13-E12 第一批 ST13 State Update 准备摘要

> W13-E12 只做 State Update 准备、字段影响分析、preview 方案和确认卡输出；不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet，不进入实现。

| ST13 | WT13 alias | W13-E12 状态准备结论 | 后续状态层建议 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | 文档层 near-ready 保持；不建议写入 `candidate_status=candidate` | 默认不写状态层 near-ready；如用户确认，可在 preview 中仅以 `facts` 中间态表达 | 否 |
| `ST13_20` | `WT13-20` | 文档层 near-ready 保持；不建议写入 `candidate_status=candidate` | 默认不写状态层 near-ready；如用户确认，可在 preview 中仅以 `facts` 中间态表达 | 否 |
| `ST13_24` | `WT13-24` | 可进入 candidate State Update preview | 建议 W13-E13 preview `candidate_status=candidate`、`review_status=pending_confirmation`、`readiness=downstream_ready`，保持 `formal_window_open=false` | 否 |
| `ST13_25` | `WT13-25` | 可进入 candidate State Update preview | 建议 W13-E13 preview `candidate_status=candidate`、`review_status=pending_confirmation`、`readiness=downstream_ready`，保持 `formal_window_open=false` | 否 |

当前结论：W13-E12 不等于正式状态层 candidate 写入，不等于 formal window open，不等于 implementation-ready。是否进入 W13-E13 Preview 需等待用户确认 `OQ-118~OQ-120`。

### 2.4.10 W13-E13 第一批 ST13 candidate State Preview 摘要

> 用户已确认 `OQ-118=B`、`OQ-119=A`、`OQ-120=B`。W13-E13 只创建 preview YAML，不修改正式 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet，不进入实现。

| ST13 | WT13 alias | Preview 尝试 | Preview 验证结果 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | 保持正式状态原样；near-ready 只保留文档层 | 未写入 `candidate_status=candidate`，未写入 `readiness=downstream_ready` | 否 |
| `ST13_20` | `WT13-20` | 保持正式状态原样；near-ready 只保留文档层 | 未写入 `candidate_status=candidate`，未写入 `readiness=downstream_ready` | 否 |
| `ST13_24` | `WT13-24` | 尝试 `candidate_status=candidate`、`review_status=pending_confirmation`、`readiness=downstream_ready` | 失败：`formal_window_open=false` 时禁止 candidate，且 `downstream_ready` 要求 `maturity` 非空 | 否 |
| `ST13_25` | `WT13-25` | 尝试 `candidate_status=candidate`、`review_status=pending_confirmation`、`readiness=downstream_ready` | 失败：`formal_window_open=false` 时禁止 candidate，且 `downstream_ready` 要求 `maturity` 非空 | 否 |

当前结论：W13-E13 Preview 失败，不得进入 W13-E14 正式 State Update；正式 `DOC_STATE.yaml` 未修改，formal window 仍关闭，implementation-ready 未形成。W13-E13.5 已将后续策略修正为优先验证 facts-only 表达，备选验证 `candidate_status=observe`。

### 2.4.11 W13-E13.5 Candidate State 表达策略修正摘要

> W13-E13.5 已吸收用户确认 `OQ-121=A`：暂不执行正式 State Update，只保留失败 Preview，并先修正后续状态表达策略。该窗口不修改正式 `DOC_STATE.yaml`，不创建新的正式 Preview 并自动 apply，不进入 W13-E14，不打开 formal window，不生成 implementation packet，不进入实现。

| ST13 | WT13 alias | 文档层状态 | 正式状态层策略 | 后续 Preview 建议 | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | `near_ready_for_formal_window_candidate_confirmed` | 不写 `candidate_status`，不写 `readiness=downstream_ready`，不写 formal window candidate | 等 M02 blocker、OpenAPI / `apps/api/**` 授权闭合后再重新评估 | 否 |
| `ST13_20` | `WT13-20` | `near_ready_for_formal_window_candidate_confirmed` | 不写 `candidate_status`，不写 `readiness=downstream_ready`，不写 formal window candidate | 等 M02 blocker、schema / migration / ORM 授权闭合后再重新评估 | 否 |
| `ST13_24` | `WT13-24` | `formal_window_candidate_recommended` | 暂不写 `candidate_status=candidate`；不直接写 `readiness=downstream_ready` | 优先验证 facts-only：`facts.formal_window_candidate_recommended=true`；备选验证 `candidate_status=observe` | 否 |
| `ST13_25` | `WT13-25` | `formal_window_candidate_recommended` | 暂不写 `candidate_status=candidate`；不直接写 `readiness=downstream_ready` | 优先验证 facts-only：`facts.formal_window_candidate_recommended=true`；备选验证 `candidate_status=observe` | 否 |

当前结论：`ST13_24 / ST13_25` 的 candidate 推荐仍停留在文档层，正式状态层 candidate 尚未写入；`ST13_21 / ST13_20` 继续保持 near-ready 文档层状态。下一轮如继续，必须先创建修正后的 Candidate Preview 并通过 `validate-state / evaluate-state`。

### 2.4.12 W13-E13.6 facts-only Candidate Preview 摘要

> 用户已确认 `OQ-122=A`、`OQ-123=A`。W13-E13.6 只创建 facts-only Candidate Preview，不修改正式 `DOC_STATE.yaml`，不进入 W13-E14，不打开 formal window，不生成 implementation packet，不进入实现。

| ST13 | WT13 alias | Preview 写入 | Preview 验证结果 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| `ST13_21` | `WT13-21` | 保持正式状态原样；near-ready 只保留文档层 | 未写 `candidate_status=candidate`、未写 `readiness=downstream_ready`、未写 candidate facts | 否 |
| `ST13_20` | `WT13-20` | 保持正式状态原样；near-ready 只保留文档层 | 未写 `candidate_status=candidate`、未写 `readiness=downstream_ready`、未写 candidate facts | 否 |
| `ST13_24` | `WT13-24` | 仅在 `facts` 下写入 `formal_window_candidate_recommended=true`、来源、review status、document layer state 和禁止 packet/实现说明 | `validate-state / evaluate-state` 为 `ok=true,error=0,warning=0`；未复现 W13-E13 的 state rule error | 否 |
| `ST13_25` | `WT13-25` | 仅在 `facts` 下写入 `formal_window_candidate_recommended=true`、来源、review status、document layer state 和禁止 packet/实现说明 | `validate-state / evaluate-state` 为 `ok=true,error=0,warning=0`；未复现 W13-E13 的 state rule error | 否 |

完整 Preview 仍有 `documents_blocked_count=1`，原因是 plan-path Preview 的 document 扫描根目录与正式 `docs/governance/DOC_STATE.yaml` 不同。该 blocker 不来自 ST13 facts-only 字段，但按 `OQ-123=A` 的严格口径，当前仍不直接进入 W13-E14。

当前结论：facts-only candidate 推荐已在 Preview 中验证为 schema 可接受；正式 `DOC_STATE.yaml` 仍未写入 candidate，formal window 仍关闭，implementation-ready 未形成，implementation packet 仍禁止生成。

### 2.4.13 W13-E13.8 docs/governance/previews 路径 facts-only State Update 摘要

> 用户已确认 `OQ-124` 方案 A。W13-E13.8 已将 Preview 放到 `docs/governance/previews/` 下重新验证；Preview 严格全绿后，正式 `DOC_STATE.yaml` 仅对 `ST13_24 / ST13_25` 写入 facts-only candidate 推荐字段。该写入不等于 formal window open，不等于 implementation-ready，不生成 implementation packet。

| ST13 | WT13 alias | 正式状态层写入 | 验证结果 | 是否 implementation-ready |
| --- | --- | --- | --- | --- |
| `ST13_20` | `WT13-20` | 保持原样；不写 candidate facts，不写 near-ready 状态 | 未被误识别为 candidate | 否 |
| `ST13_21` | `WT13-21` | 保持原样；不写 candidate facts，不写 near-ready 状态 | 未被误识别为 candidate | 否 |
| `ST13_24` | `WT13-24` | 在 `facts` 下写入 `formal_window_candidate_recommended=true`、来源、review status、document layer state 和禁止 packet/实现说明 | Preview 与正式状态均 `ok=true,error=0,warning=0,documents_blocked_count=0` | 否 |
| `ST13_25` | `WT13-25` | 在 `facts` 下写入 `formal_window_candidate_recommended=true`、来源、review status、document layer state 和禁止 packet/实现说明 | Preview 与正式状态均 `ok=true,error=0,warning=0,documents_blocked_count=0` | 否 |

当前仍不得写 `candidate_status=candidate`、`readiness=downstream_ready`、`formal_window_open=true` 或 `implementation_ready=true`；仍不得创建 `apps/**`、`infra/**`、`tests/**`，不得进入实现。

### 2.4.14 W13-E14-Merge formal window 前置补齐合并摘要

> W13-E14-Merge 已接收 W13-E14-A/B/C/D 四个并行窗口结果，并以最终 diff 为准复核 8 个双文档。并行窗口报告的其他文件修改属于并行结果集中到同一工作区；最终禁止范围 diff 为空，未发现越权实现修改。

| ST13 | WT13 alias | W13-E14-Merge 状态 | 仍未闭合项 | 是否具备实施条件 |
| --- | --- | --- | --- | --- |
| `ST13_20` | `WT13-20` | `near-ready blocker refined` | M02 blocker、schema / migration / ORM / PostgreSQL 策略授权、`ST13_21` API contract 联动、formal window 用户确认 | 否 |
| `ST13_21` | `WT13-21` | `near-ready blocker refined` | M02 blocker、OpenAPI 授权、`apps/api/**` 授权、schema / DTO / shared contract 授权、`ST13_20` 数据 contract 联动、formal window 用户确认 | 否 |
| `ST13_24` | `WT13-24` | `formal_window_preconditions_refined` | formal window 用户确认、状态层 gate、implementation_doc activation、packet inputs 激活、测试目录授权 | 否 |
| `ST13_25` | `WT13-25` | `formal_window_preconditions_refined` | formal window 用户确认、Basic Memory / Superpowers 明确授权、状态层 gate、implementation_doc activation、packet inputs 激活 | 否 |

当前结论：四个 ST13 的双文档补齐可接受，适合进入 formal window open 确认窗口；但该结论不等于 `formal_window_open=true`，不等于可以生成 implementation packet，不等于 implementation-ready。`DOC_STATE.yaml` 未在本合并窗口修改。

### 2.4.15 W13-E4-F 旧 `STxx_*` historical / superseded 同步摘要

> 完整旧 ST 到 `ST13 / WT13` 映射见 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage2.md` 第 6 节和 `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage3.md`。
> 本节只做任务索引级同步：旧 `STxx_*` 已从正式状态层 current `subtasks` 容器移出，仍保留为历史可追溯对象、reusable evidence 和 archive candidate，不再作为 W13 当前实施入口。
> 下表中的“facts 表达”是阶段 2 历史写入和阶段文档追溯依据，不表示旧 `STxx_*` 仍存在于 formal current `subtasks` 容器。

| 旧 ST 范围 | 当前角色 | facts 表达 | 当前 W13 承接入口 | archive-candidate | 是否具备实施条件 |
| --- | --- | --- | --- | --- | --- |
| `ST01_01~ST01_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_02`、`ST13_20~ST13_25` / `WT13-02`、`WT13-20~WT13-25` | 是 | 否 |
| `ST02_01~ST02_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_01`、`ST13_21`、`ST13_22` / `WT13-01`、`WT13-21`、`WT13-22` | 是 | 否 |
| `ST03_01~ST03_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_03`、`ST13_04`、`ST13_06`、`ST13_19`、`ST13_20`、`ST13_23` | 是 | 否 |
| `ST04_01~ST04_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_06`、`ST13_13`、`ST13_16`、`ST13_17`、`ST13_21`、`ST13_23` | 是 | 否 |
| `ST05_01~ST05_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_10`、`ST13_18`、`ST13_20` / `WT13-10`、`WT13-18`、`WT13-20` | 是 | 否 |
| `ST06_01~ST06_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_05~ST13_07`、`ST13_10~ST13_12`、`ST13_15`、`ST13_19`、`ST13_22` | 是 | 否 |
| `ST07_01~ST07_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_08`、`ST13_13`、`ST13_16`、`ST13_17` / `WT13-08`、`WT13-13`、`WT13-16`、`WT13-17` | 是 | 否 |
| `ST08_01~ST08_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_14~ST13_16`、`ST13_18`、`ST13_19` / `WT13-14~WT13-16`、`WT13-18`、`WT13-19` | 是 | 否 |
| `ST09_01~ST09_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_16`、`ST13_17` / `WT13-16`、`WT13-17` | 是 | 否 |
| `ST10_01~ST10_03` | historical-reference / superseded | 已写入 `w13_status`、`w13_role`、`w13_superseded_by`、`w13_alias_target` | `ST13_01`、`ST13_11`、`ST13_13`、`ST13_22`、`ST13_24`、`ST13_25` | 是 | 否 |

W13-E 当前确认卡：

- `W13-E-Q1`：任务 ID 命名采用 `WT13-xx`，用户已确认。
- `W13-E-Q2`：旧 `STxx_*` 后续映射为 `superseded`，用户已确认；新 `ST13_*` 已写入正式状态层，旧任务 superseded / historical-reference 已在阶段 2 写入 facts。
- `W13-E-Q3`：暂不直接写 `DOC_STATE.yaml`，先做 W13-E2 dry-run，用户已确认。
- `W13-E2-Q1`：W13-E3 是否先创建 preview YAML，用户已确认方案 B；Preview YAML 已创建，正式 `DOC_STATE.yaml` 未修改。
- `W13-E4-B`：用户已确认 `OQ-094=B`、`OQ-095` 阶段 1 方案 C / 阶段 2 方案 B、`OQ-096=B`；阶段 1 已写入 `ST13_01~ST13_25`。
- `W13-E4-C`：阶段 2 已用旧任务 facts 写入 `historical-reference / superseded`，但未移出旧 `STxx_*`，未迁移 archive，未放行 implementation-ready。
- `W13-E4-D`：阶段 3 dry-run / 影响分析已完成；确认卡 `OQ-097~OQ-099` 已由用户确认进入 Stage3 Preview 路径。
- `W13-E4-E`：Stage3 Preview YAML 已创建并验证通过；正式 `DOC_STATE.yaml` 仍未移出旧 `STxx_*`，正式 `RQ01.facts.task_ids` 仍未改写，是否执行正式 Stage 3 等待 `OQ-100` 用户确认。
- `W13-E4-F`：用户已确认方案 B 并完成正式 Stage 3；正式 `DOC_STATE.yaml.subtasks` 只保留 `ST13_01~ST13_25`，正式 `RQ01.facts.task_ids` 只保留 `ST13_01~ST13_25`，旧 `STxx_*` 只作历史参考和 archive candidate。

## 3. 使用规则

- 子任务只有在 `SUBTASK_DESIGN.md` 达到“可作为下游输入”且 `SUBTASK_IMPLEMENTATION.md` 达到“可直接用于实施”后，才进入代码执行。
- 每轮工作结束后，应同步回写本文件中的状态、成熟度和实施条件。
