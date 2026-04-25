# AI 模拟面试 P1 任务索引

> 本索引用于全局任务导航，不替代模块目录下的 `MODULE_TASK_INDEX.md`。  
> 状态使用：`todo` / `doing` / `done` / `blocked` / `need-clarification`。  
> 当前状态主要表示文档建设状态，不表示代码开发状态。
> 当前以 `W10-A / W10-B / W10-C` 已冻结的首切片关系层口径为准；当前主任务是补齐 `RQ01 -> module -> subtask / 观察蓝本` 关系，而不是重开历史阶段 3 白名单叙事。

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

## 1.1 `RQ01` 首切片关系映射（W10-C）

| 层级 | 对象 | 当前角色 | 当前结论 |
| --- | --- | --- | --- |
| requirement | `RQ01` | 首切片正式 requirement 入口 | 承载“岗位 JD 手工输入 + 简历 Markdown 粘贴/编辑 -> 首轮问题 -> 1 轮问答 -> 简版反馈摘要”的最小闭环；本轮不新增 requirement ID |
| direct module | `M03` | 输入侧能力 | 承接岗位 JD 文本、简历 Markdown、最小对齐，以及面向 `M04 / M06` 的最小共享输入；`MT03_01 / MT03_03` 仅为观察蓝本 |
| direct module | `M04` | 问题生成与最小证据 | 承接岗位-简历绑定、首轮问题生成与最小证据组织；后续承接对象为 `ST04_01 / ST04_02` |
| direct module | `M06` | 单轮会话与上下文 | 承接单轮会话创建、最小上下文包与 `1` 轮问答记录；后续承接对象为 `ST06_01 / ST06_02` |
| direct module | `M07` | 简版反馈与最小改进建议 | 承接简版反馈摘要与最小改进建议；后续承接对象为 `ST07_03` |
| conditional support | `M01` | 条件性支撑模块 | 仅在总控后续批准最小壳层 / 运行时 / 共享原语骨架时介入；当前不进入首切片主链 |
| excluded | `M02 / M05 / M08 / M09 / M10` | 本轮明确排除 | 登录与成员治理、资产 / RAG、复盘、训练中心、管理台 / 运维不进入首切片关系主链；即使相关问题已有默认口径，也不转成本轮实施入口 |

## 2. 子任务索引

> 当前轮次口径：
> - `RQ01` 当前只承载首切片：“岗位 JD 手工输入 + 简历 Markdown 粘贴/编辑 -> 首轮问题 -> 1 轮问答 -> 简版反馈摘要”。
> - `ST02_*`、`ST03_*` 只保留为历史容器，禁止作为当前及后续直开窗口。
> - `OQ-024` 的总控正式映射已写死；`M02`、`M03` 的新微任务蓝本当前仍不是正式子任务 ID。
> - 白名单观察面 != 正式子任务 ID != 可开窗任务；本轮仍不允许开启任何子任务窗口。
> - `M03` 仍只观察 `MT03_01 / MT03_03`；`ST04_01 / ST04_02 / ST06_01 / ST06_02 / ST07_03` 仅为后续承接对象，不等于当前正式开窗任务。
> - 本轮收口后正式开窗层仍为空，不新增正式子任务 ID；`W10-D` 仍需总控二次判定。

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
- `M02`：当前观察入口以 `MT02_01 ~ MT02_08` 为蓝本，但只允许把 `MT02_01 / MT02_02` 记为条件性白名单观察面；若后续继续推进，只允许围绕 `GET /api/v1/members` 的共享最小层何时可从 `OQ-021 proposed-default` 升格为正式候选输入，以及 `MT02_02` 权限消费边界稳定性复核展开，不得把模块内闭合外推为 `MT02_04 / MT02_06` ready。
- `M03`：当前观察入口以 `MT03_01`、`MT03_02A`、`MT03_02B`、`MT03_03` 等蓝本为准；只允许把 `MT03_01 / MT03_03` 记为条件性白名单观察面，且应理解为“已吸收但未放行”；若后续继续推进，只允许围绕“正式开窗层为空 + 当前阶段关窗 + 上传 / 导出链依赖未变”的直接结构性主阻塞复核展开，上传 / 导出链继续不得视为可直开子任务。

## 2.2 `OQ-024` 正式映射（已写死）

- 历史容器层：`ST02_01`、`ST02_02`、`ST02_03`、`ST03_01`、`ST03_02`、`ST03_03` 全部固定为历史容器，禁止作为当前及后续直开窗口。
- 观察蓝本层：
  - `M01`：当前无白名单观察面。
  - `M02`：当前只允许 `MT02_01 / MT02_02` 作为条件性白名单观察蓝本；`MT02_03 / MT02_07` 只保留为后续顺位；`MT02_04 / MT02_05 / MT02_06 / MT02_08` 当前不得进入观察面。
  - `M03`：当前只允许 `MT03_01 / MT03_03` 作为条件性白名单观察蓝本；`MT03_02A / MT03_02B` 当前不得进入观察面。
- 正式开窗层：当前轮次正式子任务 ID 名单固定为空；只有总控在后续正式候选复评完成后，才能在本文件中新增正式子任务 ID 与开窗资格。

## 2.3 首切片后续承接对象（非正式开窗）

- `ST04_01 / ST04_02`：后续承接 `M04` 的岗位-简历绑定、首轮问题生成与最小证据组织，不等于本轮正式开窗任务。
- `ST06_01 / ST06_02`：后续承接 `M06` 的单轮会话创建、问题来源约束与 `1` 轮问答记录，不扩展到 `ST06_03` 的报告 / 导出链。
- `ST07_03`：后续承接 `M07` 的简版反馈摘要、逐题评估投影与最小改进建议，不等于训练中心或长期进度开窗。
- 当前正式开窗层固定为空；本轮不新增正式子任务 ID。

## 3. 使用规则

- 子任务只有在 `SUBTASK_DESIGN.md` 达到“可作为下游输入”且 `SUBTASK_IMPLEMENTATION.md` 达到“可直接用于实施”后，才进入代码执行。
- 每轮工作结束后，应同步回写本文件中的状态、成熟度和实施条件。
