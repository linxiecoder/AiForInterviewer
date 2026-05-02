---
title: SUBTASK_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m01-foundation-and-platform/sub-modules/st01-02-workspace-shell-and-i18n/subtask-design
---

# ST01_02 工作台壳层与 i18n 基线 - 子任务设计

## 1. 文档定位

- 本文档承接模块设计，并把“工作台壳层与 i18n 基线”拆成可持续细化的子任务设计单元。
- 当前成熟度：仅有骨架。

## 2. 父模块

- $(System.Collections.Specialized.OrderedDictionary.Id) 基础平台与工作台壳层。

## 3. 子任务目标

- 建立首页、Dashboard 壳层、通用页面头部、i18n 入口和列表原语的设计与实施承接关系。

## 4. 输入文档

- ../../MODULE_REQUIREMENTS.md。
- ../../MODULE_DESIGN.md。
- ../../MODULE_API_DESIGN.md。
- ../../MODULE_SCHEMA_DESIGN.md。
- ../../MODULE_LOGIC_DESIGN.md。

## 5. 范围内
- 工作台壳层设计
- 页面模板与列表原语
- 文案读取规范

## 6. 不在范围内

- 不直接进入代码实现。
- 不替代父模块的全局边界定义。
- 不解决未进入本子任务范围的跨模块问题。

## 7. 当前已知目标区域
- apps/web/src/app/**
- apps/web/src/components/**
- apps/web/src/i18n/**

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
- OQ-003 视觉规范首轮需要沉淀到什么粒度

## 11. 下一轮建议补充

- 补充精确输入输出。
- 补充接口/字段/状态相关设计。
- 补充验证目标与下游引用方式。