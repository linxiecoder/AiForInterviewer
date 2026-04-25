# M08 复盘与回放 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“复盘与回放”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> W13-StateArchive 说明：本节中的旧 P1 设计稿和旧实现计划引用仅用于历史追溯；当前一期工作台 MVP 事实以 `PLAN_LATEST.md`、四份 W13 唯一事实源、`DESIGN_DECISIONS.md` 与 `OPEN_QUESTIONS.md` 为准。

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：7.7 复盘
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：9.6 复盘
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：15.5 复盘模块

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：359-364 复盘与薄弱项域
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：442-453 复盘 API
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：945-964 里程碑 9
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：3544-3797 任务 9

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
- OQ-010 已由 W13 `FC-14` confirmed 覆盖：支持整份和单题归档到资产库。
- OQ-014 已由 W13 `FC-17` confirmed 覆盖：模拟面试、打磨模式和复盘共享核心评估框架，具体模式差异按评分 / 复盘 / 导出 / DoD 事实源承接。
- OQ-015 已由 W13 `FC-11` confirmed 覆盖：真实面试输入支持上传逐字稿原文，不要求用户先按题目拆分；系统由大模型自动识别问答边界，低置信度时提示用户校对。
- 以上事实源以 `OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` 和 W13 唯一事实源文档为准，不再作为当前阻塞。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
