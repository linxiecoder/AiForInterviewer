# M09 训练中心与薄弱项生命周期 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“训练中心与薄弱项生命周期”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> W13-StateArchive 说明：本节中的旧 P1 设计稿和旧实现计划引用仅用于历史追溯；当前一期工作台 MVP 事实以 `PLAN_LATEST.md`、四份 W13 唯一事实源、`DESIGN_DECISIONS.md` 与 `OPEN_QUESTIONS.md` 为准。

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：10 薄弱项体系
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：11 训练机制
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：15.7 训练中心 / 薄弱项页

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：359-364 复盘与薄弱项域
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：454-463 训练与薄弱项 API
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：711-721 薄弱项聚合
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：965-980 里程碑 10
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：3798-4046 任务 10

## 3. 模块目标

- 定义薄弱项聚合、训练抽屉、待打磨入列和生命周期状态流转。

## 4. 模块范围内
- weakness item 聚合
- 训练中心页面
- 训练抽屉动作
- 生命周期状态流转

## 5. 不在本模块范围内
- 长期智能学习画像
- 跨租户推荐共享

## 6. 关键角色与对象
- weakness_items
- training_actions / intake records
- lifecycle status transitions

## 7. 关键流程
- 弱项聚合与排序
- 训练抽屉动作与待打磨入列
- 状态流转、停练与消减规则

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
- OQ-014 已由 W13 `FC-17` confirmed 覆盖：模拟面试、打磨模式和复盘共享核心评估框架，具体模式差异按评分 / 复盘 / 导出 / DoD 事实源承接。
- OQ-016 已由 W13 `FC-13` confirmed 覆盖：`WeaknessItem` 是可训练、可累计、可消减、可停练的中粒度训练主题；状态包括 `active / low_priority / dismissed / resolved`，消减建议由用户确认后生效。
- 以上事实源以 `OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` 和 W13 唯一事实源文档为准，不再作为当前阻塞。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
