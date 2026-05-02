---
title: MODULE_DEPENDENCIES
type: note
permalink: ai-for-interviewer/docs/modules/m08-review-and-replay/module-dependencies
---

# M08 复盘与回放 - 模块依赖

## 1. 上游模块
- M06
- M07

## 2. 下游承接子任务
- ST08_01 复盘总对象与列表/详情
- ST08_02 真实面试导入与逐题分析
- ST08_03 模拟面试复盘回放与导出

## 3. 依赖门槛

- 进入本模块详细设计前，至少需要：
  - 上游模块的 MODULE_REQUIREMENTS.md 达到初稿。
  - 本模块的关键开放问题已登记。
- 进入本模块子任务设计前，至少需要：
  - 本模块的 MODULE_REQUIREMENTS.md 与 MODULE_DESIGN.md 达到可评审。
- 进入本模块子任务实施前，至少需要：
  - 相关 SUBTASK_DESIGN.md 达到可作为下游输入。
  - 对应 SUBTASK_IMPLEMENTATION.md 达到可直接用于实施。

## 4. 当前依赖风险

- 上游原始文档内容仍需进一步抽取。
- 多个跨模块开放问题尚未确认，可能影响边界。