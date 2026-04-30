---
title: MODULE_REQUIREMENTS
type: note
permalink: ai-for-interviewer/docs/modules/m09-training-and-weakness-lifecycle/module-requirements
---

# M09 训练中心与薄弱项生命周期 - 模块需求

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：WeaknessItem、训练抽屉、证据聚合、消减、停练和训练生命周期。
- 后续补齐项：区分薄弱项中心与待打磨执行层，补齐训练状态和回写边界。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“训练中心与薄弱项生命周期”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> historical context：历史 P1 设计稿和历史实现计划只用于追溯，不作为当前依据。当前需求事实源为 `docs/requirements/workbench-mvp/**`，当前设计事实源为 `docs/design/workbench-mvp/**`；规划入口为 `PLAN_LATEST.md`，任务入口为 `TASK_INDEX.md`、`docs/governance/DOC_STATE.yaml` 和当前任务文档。

### 2.1 原始需求引用
- 历史 P1 设计材料：10 薄弱项体系
- 历史 P1 设计材料：11 训练机制
- 历史 P1 设计材料：15.7 训练中心 / 薄弱项页

### 2.2 原始实施计划引用
- 历史 P1 实现计划材料：359-364 复盘与薄弱项域
- 历史 P1 实现计划材料：454-463 训练与薄弱项 API
- 历史 P1 实现计划材料：711-721 薄弱项聚合
- 历史 P1 实现计划材料：965-980 里程碑 10
- 历史 P1 实现计划材料：3798-4046 任务 10

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
- OQ-014 已由当前需求 / 设计输入中的 `FC-17` confirmed 覆盖：模拟面试、打磨模式和复盘共享核心评估框架，具体模式差异按评分 / 复盘 / 导出 / DoD 输入承接。
- OQ-016 已由当前需求 / 设计输入中的 `FC-13` confirmed 覆盖：`WeaknessItem` 是可训练、可累计、可消减、可停练的中粒度训练主题；状态包括 `active / low_priority / dismissed / resolved`，消减建议由用户确认后生效。
- 以上输入以 `OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` 和 Workbench MVP 当前设计输入文档为准，不再作为当前阻塞。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。