# AI 模拟面试 P1 最新文档总控

## 1. 文档定位

- 本文档是当前项目全局文档体系的总控入口，用于说明目标、范围、模块顺序和维护规则。
- 上游源文档为：
  - [AI 模拟面试 P1 文本版闭环设计稿](docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md)
  - [AI 模拟面试 P1 MVP 实现计划](docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md)
- `docs/modules/` 下的模块文档和子任务文档，是后续设计细化、实施准备与执行回写的主承接区。

## 2. 当前阶段

- 当前状态：当前仍处于阶段 3 的“总控澄清 + 模块候选白名单准备轮（收口阶段）”。
- 当前目标：统一 `OQ-021 / OQ-024 / OQ-025` 的吸收结果与状态分层，并把 `M01 / M02 / M03` 的最低位压缩结果收敛为一致的总控判断。
- 当前限制：仓库尚未进入稳定代码实施阶段；本轮仍不开放任何子任务实施窗口，也不允许把白名单观察面误写成正式子任务候选。
- 当前说明：`最低位压缩` 只是本轮模块窗口采用的执行方法，不是新的全局阶段名；本轮只证明最低位压缩与问题吸收更清楚，不证明正式候选条件已闭合。

## 3. 执行原则

- 文档体系采用 `global -> module -> subtask` 分层。
- 源设计稿与源实现计划保留为历史上游，不直接承担逐轮回写。
- 当前轮次优先处理总控状态分层与全局叙事收口，而不是继续按源任务顺序平推。
- 单次实施单位应收敛到一个子任务。
- 只有当 `SUBTASK_DESIGN.md` 可作为下游输入，且 `SUBTASK_IMPLEMENTATION.md` 可直接用于实施后，才进入代码执行。
- 每轮执行后需要同步回写 `TASK_INDEX.md`、`EXECUTION_LOG.md`、`DOCUMENT_MATURITY.md`、`DOCUMENT_PROGRESS.md`。

## 4. 模块地图

| Module ID | 模块名称 | 目标摘要 | 模块目录 |
| --- | --- | --- | --- |
| M01 | 基础平台与工作台壳层 | 建立仓库结构、运行时、i18n、测试与文档治理基线 | `docs/modules/M01-foundation-and-platform/` |
| M02 | 鉴权、团队与成员 | 明确身份模型、团队隔离、成员目录与权限矩阵 | `docs/modules/M02-identity-and-team/` |
| M03 | 岗位、简历与文档处理 | 建立岗位、简历、版本、上传、转换与导出链路 | `docs/modules/M03-jobs-resumes-and-documents/` |
| M04 | 匹配分析与训练证据 | 建立岗位-简历绑定、分析评分和训练证据输出 | `docs/modules/M04-match-analysis-and-evidence/` |
| M05 | 资产库、归档与检索 | 建立资产类型、资产对象、归档和检索入库机制 | `docs/modules/M05-assets-and-retrieval/` |
| M06 | 模拟面试、上下文与导出 | 建立会话、上下文包、题目来源、消息流与导出 | `docs/modules/M06-simulated-interview-and-context/` |
| M07 | 打磨模式、评估与进度 | 建立主题推荐、能力树、逐题评估与进度快照 | `docs/modules/M07-polish-assessment-and-progress/` |
| M08 | 复盘与回放 | 建立复盘对象、真实面试导入、模拟面试回放与导出 | `docs/modules/M08-review-and-replay/` |
| M09 | 训练中心与薄弱项生命周期 | 建立薄弱项聚合、训练抽屉与生命周期流转 | `docs/modules/M09-training-and-weakness-lifecycle/` |
| M10 | 管理台、治理与可观测性 | 建立成员治理、模型/规则配置、可观测性与运维入口 | `docs/modules/M10-admin-governance-and-observability/` |

## 5. 推荐执行顺序

1. 先由总控执行 `GC-04：阶段名统一回写 + OQ-024 正式映射写死`
2. 并行开启 `MR-11：M02 /members 列表共享契约继续收敛`
3. 并行开启 `MR-12：M03 最低位 API 与依赖口径精确化`
4. 视资源再开 `MR-13：M01 候选前保守复核与乐观措辞回收`
5. 继续保留 `RV-05：正式候选前第二次交叉复核`
6. 在 `GC-04` 完成正式映射、`MR-11` 继续收敛 `/members` 契约、且 `M01/M02/M03` 最低位文档不再以高 `L4` 承载主阻塞前，仍不开放任何子任务窗口

## 6. 维护规则

- 全局规则变化时，先更新 `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` 和 `OPEN_QUESTIONS.md`。
- 模块边界变化时，先更新对应模块目录下的模块文档，再回写 `MODULE_INDEX.md` 与 `TASK_INDEX.md`。
- 子任务成熟度变化时，回写 `DOCUMENT_MATURITY.md` 与 `DOCUMENT_PROGRESS.md`。
