---
title: SUBTASK_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m09-training-and-weakness-lifecycle/sub-modules/st09-03-lifecycle-rules/subtask-design
---

# ST09_03 生命周期、消减与停练规则 - 子任务设计

## 1. 文档定位

- 本文档承接模块设计，并把“生命周期、消减与停练规则”拆成可持续细化的子任务设计单元。
- 当前成熟度：仅有骨架。

## 2. 父模块

- M09 训练中心与薄弱项生命周期；父级索引：[MODULE_TASK_INDEX.md](../../MODULE_TASK_INDEX.md)。

## 3. 子任务目标

- 定义薄弱项的状态机、消减规则、停练规则和跨模块联动边界。

## 4. 输入文档

- ../../MODULE_REQUIREMENTS.md
- ../../MODULE_DESIGN.md
- ../../MODULE_API_DESIGN.md
- ../../MODULE_SCHEMA_DESIGN.md
- ../../MODULE_LOGIC_DESIGN.md

## 5. 范围内

- 生命周期状态机设计
- 消减规则
- 停练规则
- 跨模块状态联动说明

## 6. 不在范围内

- 不直接进入代码实现。
- 不替代训练抽屉和聚合视图本身的页面设计。
- 不覆盖模块外的全局评估框架定义。

## 7. 当前已知目标区域

- `apps/api/app/domain/weakness/**`
- `apps/api/app/services/training/**`
- `apps/api/app/api/routes/training.py`
- `apps/web/src/components/training/**`

## 8. 当前设计缺口

- 仍需明确输入输出契约。
- 仍需明确状态迁移条件和例外路径。
- 仍需明确验证方式和 DoD。
- 仍需把目标区域收敛到可实施的文件级边界。

## 9. 设计完成判定

- 输入、输出、范围和依赖稳定。
- 状态机、消减和停练规则可描述、可验证。
- 与评估口径、训练抽屉和复盘结果的联动边界明确。
- 没有阻塞级待确认问题。

## 10. 旧待确认内容处理

- 当前无子任务内 open 问题。
- OQ-014 已由当前需求 / 设计输入中的 `FC-17` confirmed 覆盖：共享核心评估框架，具体模式差异按评分 / 复盘 / 导出 / DoD 输入承接。
- OQ-016 已由当前需求 / 设计输入中的 `FC-13` confirmed 覆盖：`WeaknessItem` 是可训练、可累计、可消减、可停练的中粒度训练主题；消减建议由用户确认后生效。
- 该确认不激活本 ST，也不改变“当前成熟度：仅有骨架”的状态。

## 11. 下一轮建议补充

- 补充精确输入输出。
- 补充状态迁移、衰减和停练的规则表。
- 补充验证目标与下游引用方式。