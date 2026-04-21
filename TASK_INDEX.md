# AI 模拟面试 P1 任务索引

> 本索引用于全局任务导航，不替代模块目录下的 `MODULE_TASK_INDEX.md`。  
> 状态使用：`todo` / `doing` / `done` / `blocked` / `need-clarification`。  
> 当前状态主要表示文档建设状态，不表示代码开发状态。
> 当前已进入“计划重构执行轮”，不再按 11 个源任务直接执行；具体窗口编排以 `DOCUMENT_PROGRESS.md` 为准。

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

## 2. 子任务索引

> `R-Refactor-01` 收口口径：
> - `ST02_*`、`ST03_*` 只保留为历史容器，禁止作为下一轮直开窗口。
> - `M02`、`M03` 的新微任务蓝本见各自模块目录下的 `MODULE_TASK_INDEX.md`；在 `OQ-024` 完成总控映射前，这些蓝本还不是正式子任务 ID。

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

- `M02`：下一轮观察入口以 `MT02_01 ~ MT02_08` 为蓝本，优先顺序与并行组定义以 `docs/modules/M02-identity-and-team/MODULE_TASK_INDEX.md` 为准。
- `M03`：下一轮观察入口以 `MT03_01 ~ MT03_08` 为蓝本；当前只有简历聚合根链局部接近候选，岗位链与上传 / 导出链仍不得视为可直开子任务。

## 3. 使用规则

- 子任务只有在 `SUBTASK_DESIGN.md` 达到“可作为下游输入”且 `SUBTASK_IMPLEMENTATION.md` 达到“可直接用于实施”后，才进入代码执行。
- 每轮工作结束后，应同步回写本文件中的状态、成熟度和实施条件。
