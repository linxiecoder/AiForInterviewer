# M06 模拟面试、上下文与导出 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“模拟面试、上下文与导出”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

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
- OQ-009 Embedding 与向量化来源如何确定
- OQ-011 Search snapshot 的来源只做导入还是需要抓取
- OQ-012 上下文包中的 source priority 与引用摘要规则如何固定
- OQ-018 管理台是否负责 search snapshot 导入与运维

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
