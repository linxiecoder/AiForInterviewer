# M06 模拟面试、上下文与导出 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“模拟面试、上下文与导出”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> W13-StateArchive 说明：本节中的旧 P1 设计稿和旧实现计划引用仅用于历史追溯；当前一期工作台 MVP 事实以 `PLAN_LATEST.md`、四份 W13 唯一事实源、`DESIGN_DECISIONS.md` 与 `OPEN_QUESTIONS.md` 为准。

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：3.4 面试模式边界
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：6 问题生成与参考材料原则
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：7.5 模拟面试与消息
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：9.3 模拟面试启动
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：9.5 模拟模式
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：15.4 模拟面试模块

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：346-358 模拟面试与打磨域
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：425-441 模拟面试与打磨 API
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：693-710 模拟面试/打磨上下文包
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：903-922 里程碑 7
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：2885-3245 任务 7

## 3. 模块目标

- 定义模拟面试会话、上下文包、问题来源、消息流、报告与导出。

## 4. 模块范围内
- 面试会话对象
- context pack 装配
- 消息流与 trace
- 报告与导出产物

## 5. 不在本模块范围内
- 语音/视频面试
- 在线搜索抓取

## 6. 关键角色与对象
- interview_sessions
- interview_messages
- interview_question_traces
- search_snapshots
- interview_reports / exports

## 7. 关键流程
- 会话创建与模式选择
- 上下文包装配与 source summary
- 答题 -> 追问/推进 -> 完成 -> 导出

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
- historical：旧 `OQ-009` 已由 W13 唯一事实源和 `FC-05` / `DD-021` 覆盖；当前口径为 RAG / 知识库进入一期，支持混合检索，失败时降级继续并标注证据缺口。
- historical：旧 `OQ-011` 已由 W13 唯一事实源和 `FC-18` / `DD-008` 覆盖；当前口径为 Search snapshot 只导入不抓取。
- historical：旧 `OQ-012` 已由 W13 唯一事实源和 `FC-05` / `DD-021` 覆盖；当前口径为 RAG 引用、检索结果与证据缺口进入面试、评分和复盘证据链。
- historical：旧 `OQ-018` 已由 W13 唯一事实源和 `FC-18` 覆盖；当前口径为管理台负责导入与运维入口，完整运维能力低干扰占位。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
