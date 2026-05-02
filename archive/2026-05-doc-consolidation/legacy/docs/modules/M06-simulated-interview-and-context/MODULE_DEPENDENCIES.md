---
title: MODULE_DEPENDENCIES
type: note
permalink: ai-for-interviewer/docs/modules/m06-simulated-interview-and-context/module-dependencies
---

# M06 模拟面试、上下文与导出 - 模块依赖

## 1. 上游模块
- M03
- M04
- M05

## 2. 下游承接子任务
- ST06_01 面试会话创建与列表
- ST06_02 上下文包与问题来源规则
- ST06_03 消息流、trace、报告与导出

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