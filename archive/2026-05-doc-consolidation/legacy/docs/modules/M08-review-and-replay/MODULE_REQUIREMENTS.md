---
title: MODULE_REQUIREMENTS
type: note
permalink: ai-for-interviewer/docs/modules/m08-review-and-replay/module-requirements
---

# M08 复盘与回放 - 模块需求

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：模拟复盘、真实面试复盘、逐题拆解、导出和归档入口。
- 后续补齐项：按真实 / 模拟复盘、低置信度校对、Markdown 导出和证据展示补齐模块设计。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“复盘与回放”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> historical context：历史 P1 设计稿和历史实现计划只用于追溯，不作为当前依据。当前需求事实源为 `docs/requirements/workbench-mvp/**`，当前设计事实源为 `docs/design/workbench-mvp/**`；规划入口为 `PLAN_LATEST.md`，任务入口为 `TASK_INDEX.md`、`docs/governance/DOC_STATE.yaml` 和当前任务文档。

### 2.1 原始需求引用
- 历史 P1 设计材料：7.7 复盘
- 历史 P1 设计材料：9.6 复盘
- 历史 P1 设计材料：15.5 复盘模块

### 2.2 原始实施计划引用
- 历史 P1 实现计划材料：359-364 复盘与薄弱项域
- 历史 P1 实现计划材料：442-453 复盘 API
- 历史 P1 实现计划材料：945-964 里程碑 9
- 历史 P1 实现计划材料：3544-3797 任务 9

## 3. 模块目标

- 定义复盘总对象、真实面试导入、逐题分析、从模拟面试生成复盘以及导出。

## 4. 模块范围内
- review aggregate
- 真实面试导入
- 逐题分析
- 从模拟面试生成复盘
- 复盘导出

## 5. 不在本模块范围内
- 外部 ATS 集成
- 语音转录服务

## 6. 关键角色与对象
- reviews
- review_question_analyses
- review_exports / replay artifacts

## 7. 关键流程
- 真实面试导入
- 逐题分析与结论生成
- 模拟面试到复盘的映射与导出

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
- OQ-010 已由当前需求 / 设计输入中的 `FC-14` confirmed 覆盖：支持整份和单题归档到资产库。
- OQ-014 已由当前需求 / 设计输入中的 `FC-17` confirmed 覆盖：模拟面试、打磨模式和复盘共享核心评估框架，具体模式差异按评分 / 复盘 / 导出 / DoD 输入承接。
- OQ-015 已由当前需求 / 设计输入中的 `FC-11` confirmed 覆盖：真实面试输入支持上传逐字稿原文，不要求用户先按题目拆分；系统由大模型自动识别问答边界，低置信度时提示用户校对。
- 以上输入以 `OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` 和 Workbench MVP 当前设计输入文档为准，不再作为当前阻塞。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。