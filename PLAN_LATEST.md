# AI 模拟面试 P1 最新文档总控

## 1. 文档定位

- 本文档是当前项目全局文档体系的总控入口，用于说明目标、范围、模块顺序和维护规则。
- 上游源文档为：
  - [AI 模拟面试 P1 文本版闭环设计稿](docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md)
  - [AI 模拟面试 P1 MVP 实现计划](docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md)
- `docs/modules/` 下的模块文档和子任务文档，是后续设计细化、实施准备与执行回写的主承接区。

## 2. 当前阶段

- 当前状态：已完成全局文档骨架修复与模块目录初始化，正在从源设计稿向模块级设计与子任务级设计沉淀。
- 当前目标：把 `global -> module -> subtask` 文档链路稳定下来，使后续任一实施都能以模块文档和子任务文档为直接输入。
- 当前限制：仓库尚未进入稳定代码实施阶段，绝大多数 `SUBTASK_IMPLEMENTATION.md` 仍处于“不可直接实施”状态。

## 3. 执行原则

- 文档体系采用 `global -> module -> subtask` 分层。
- 源设计稿与源实现计划保留为历史上游，不直接承担逐轮回写。
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

1. M01 基线模块
2. M02 鉴权与成员
3. M03 岗位、简历与文档
4. M04 匹配分析
5. M05 资产与检索
6. M06 模拟面试
7. M07 打磨与进度
8. M08 复盘与回放
9. M09 训练中心与生命周期
10. M10 管理台与治理

## 6. 维护规则

- 全局规则变化时，先更新 `TECHNICAL_STANDARDS.md`、`DESIGN_DECISIONS.md` 和 `OPEN_QUESTIONS.md`。
- 模块边界变化时，先更新对应模块目录下的模块文档，再回写 `MODULE_INDEX.md` 与 `TASK_INDEX.md`。
- 子任务成熟度变化时，回写 `DOCUMENT_MATURITY.md` 与 `DOCUMENT_PROGRESS.md`。
