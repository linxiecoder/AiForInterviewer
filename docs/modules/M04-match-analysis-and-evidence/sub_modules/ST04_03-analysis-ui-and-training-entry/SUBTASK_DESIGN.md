---
title: SUBTASK_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m04-match-analysis-and-evidence/sub-modules/st04-03-analysis-ui-and-training-entry/subtask-design
---

# ST04_03 分析展示与训练入口 - 子任务设计

## 1. 文档定位

- 本文档承接模块设计，并把“分析展示与训练入口”拆成可持续细化的子任务设计单元。
- 当前成熟度：仅有骨架。

## 2. 父模块

- M04 匹配分析与训练证据；父级索引见 ../../MODULE_TASK_INDEX.md。

## 3. 子任务目标

- 连接岗位详情中的分析区块、弱项摘要和训练入口。

## 4. 输入文档

- ../../MODULE_REQUIREMENTS.md。
- ../../MODULE_DESIGN.md。
- ../../MODULE_API_DESIGN.md。
- ../../MODULE_SCHEMA_DESIGN.md。
- ../../MODULE_LOGIC_DESIGN.md。

## 5. 范围内
- 页面区块设计
- 前后端字段映射
- 训练入口约束

## 6. 不在范围内

- 不直接进入代码实现。
- 不替代父模块的全局边界定义。
- 不解决未进入本子任务范围的跨模块问题。

## 7. 当前已知目标区域
- apps/web/src/app/(dashboard)/jobs/[jobId]/**
- apps/web/src/components/jobs/**

## 8. 当前设计缺口

- 仍需明确输入输出契约。
- 仍需明确验证方式和 DoD。
- 仍需进一步缩小到可实施的文件/页面/接口边界。

## 9. 设计完成判定

- 输入、输出、范围、依赖稳定。
- 目标对象、页面或接口边界明确。
- 验证目标可描述。
- 没有阻塞级待确认问题。

## 10. 当前待确认内容
- 无阻塞级待确认问题。
- historical：旧 `OQ-008` 已由 Workbench MVP 当前设计输入和 `FC-17` / `DD-009` 覆盖；当前口径为匹配分析与评估采用规则版本化 + 共享核心评估框架 + 规则推荐优先。

## 11. 下一轮建议补充

- 补充精确输入输出。
- 补充接口/字段/状态相关设计。
- 补充验证目标与下游引用方式。