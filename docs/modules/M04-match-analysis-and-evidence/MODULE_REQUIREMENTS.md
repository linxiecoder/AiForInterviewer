# M04 匹配分析与训练证据 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“匹配分析与训练证据”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> W13-StateArchive 说明：本节中的旧 P1 设计稿和旧实现计划引用仅用于历史追溯；当前一期工作台 MVP 事实以 `PLAN_LATEST.md`、四份 W13 唯一事实源、`DESIGN_DECISIONS.md` 与 `OPEN_QUESTIONS.md` 为准。

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：7.3 岗位-简历分析
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：8 评分与评估体系
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：10.2 来源
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：15.2 岗位详情页

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：335-339 匹配分析与训练证据域
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：669-681 岗位-简历匹配分析技术路线
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：2335-2581 任务 5

## 3. 模块目标

- 定义岗位-简历绑定、匹配分析、评分依据和训练证据输出。

## 4. 模块范围内
- 岗位与简历绑定
- 匹配分析对象与评分结果
- 弱项证据与训练入口

## 5. 不在本模块范围内
- 复杂多模型融合评分
- 在线自学习策略

## 6. 关键角色与对象
- job_resume_bindings
- job_resume_match_analyses
- weakness_evidences

## 7. 关键流程
- 岗位与简历绑定
- 匹配评分与依据生成
- 训练证据输出和前端展示

## 8. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确接口、鉴权与错误语义。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 9. 当前缺口

- 仍需把原始文档中的细节进一步提纯到稳定边界。
- 仍需把跨模块耦合点从“描述性要求”转为“可引用的文档输入”。

## 10. 待确认问题
- 当前无模块级 open 问题。
- historical：旧 `OQ-008` 已由 W13 唯一事实源和 `FC-17` / `DD-009` 覆盖；当前口径为匹配分析与评估采用规则版本化 + 共享核心评估框架 + 规则推荐优先。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
