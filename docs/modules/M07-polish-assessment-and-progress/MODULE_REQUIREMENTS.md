# M07 打磨模式、评估与进度 - 模块需求

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：打磨模式、ProgressTree、题级反馈、能力树、训练入口和部分导出。
- 后续补齐项：明确打磨模式不固定轮次，并与压力面评分和训练闭环分离。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“打磨模式、评估与进度”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> historical context：历史 P1 设计稿和历史实现计划只用于追溯，不作为当前依据。当前需求事实源为 `docs/requirements/workbench-mvp/**`，当前设计事实源为 `docs/design/workbench-mvp/**`；规划入口为 `PLAN_LATEST.md`，任务入口为 `TASK_INDEX.md`、`docs/governance/DOC_STATE.yaml` 和当前任务文档。

### 2.1 原始需求引用
- 历史 P1 设计材料：7.6 评估与进展
- 历史 P1 设计材料：7.8 薄弱项与打磨主题
- 历史 P1 设计材料：8 评分与评估体系
- 历史 P1 设计材料：9.4 打磨模式
- 历史 P1 设计材料：15.4 打磨模式面试页/启动页

### 2.2 原始实施计划引用
- 历史 P1 实现计划材料：346-358 模拟面试与打磨域
- 历史 P1 实现计划材料：397-433 评分与评估体系
- 历史 P1 实现计划材料：923-944 里程碑 8
- 历史 P1 实现计划材料：3246-3543 任务 8

## 3. 模块目标

- 定义打磨主题推荐、能力树、逐题评估和进度快照。

## 4. 模块范围内
- practice topic 推荐
- 能力树蓝图与节点
- 题目级评估
- 会话进度快照

## 5. 不在本模块范围内
- 多轮个性化推荐系统
- 复杂模型排序服务

## 6. 关键角色与对象
- practice_topics
- polish_session_topic_links
- capability_blueprints
- capability_nodes
- answer_assessments
- interview_progress_snapshots

## 7. 关键流程
- 主题推荐与会话启动
- 能力节点推进
- 评估结果写入与进度快照计算

## 8. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确接口、鉴权与错误语义。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 9. 当前缺口

- 仍需把原始文档中的细节进一步提纯到稳定边界。
- 仍需把跨模块耦合点从“描述性要求”转为“可引用的文档输入”。

## 10. 旧待确认问题处理

- 当前无模块内 open 问题。
- OQ-008 已由当前需求 / 设计输入中的 `FC-17` confirmed 覆盖：匹配分析与评估采用规则版本化、共享核心评估框架与规则推荐优先。
- OQ-013 已由当前需求 / 设计输入中的 `FC-13`、`FC-17` confirmed 覆盖：打磨主题可由用户自定义，也可结合岗位与薄弱项自动推荐，规则推荐优先。
- OQ-014 已由当前需求 / 设计输入中的 `FC-17` confirmed 覆盖：模拟面试、打磨模式和复盘共享核心评估框架，具体模式差异按评分 / 复盘 / 导出 / DoD 输入承接。
- 以上输入以 `OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` 和 Workbench MVP 当前设计输入文档为准，不再作为当前阻塞。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
