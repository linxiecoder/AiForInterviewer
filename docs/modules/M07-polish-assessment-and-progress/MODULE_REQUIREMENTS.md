# M07 打磨模式、评估与进度 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“打磨模式、评估与进度”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：7.6 评估与进展
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：7.8 薄弱项与打磨主题
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：8 评分与评估体系
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：9.4 打磨模式
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：15.4 打磨模式面试页/启动页

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：346-358 模拟面试与打磨域
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：397-433 评分与评估体系
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：923-944 里程碑 8
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：3246-3543 任务 8

## 3. 模块目标

- 定义打磨主题推荐、能力树、逐题评估和进度快照。

## 4. 模块范围内
- practice topic 推荐
- 能力树蓝图与节点
- 题目级评估
- 会话进度快照

## 5. 不在本模块范围内
- 多轮个性化推荐系统
- 复杂模型排序服务

## 6. 关键角色与对象
- practice_topics
- polish_session_topic_links
- capability_blueprints
- capability_nodes
- answer_assessments
- interview_progress_snapshots

## 7. 关键流程
- 主题推荐与会话启动
- 能力节点推进
- 评估结果写入与进度快照计算

## 8. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确接口、鉴权与错误语义。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 9. 当前缺口

- 仍需把原始文档中的细节进一步提纯到稳定边界。
- 仍需把跨模块耦合点从“描述性要求”转为“可引用的文档输入”。

## 10. 待确认问题
- OQ-008 匹配分析与评估规则是否需要版本化
- OQ-013 打磨主题推荐是规则、LLM 还是混合
- OQ-014 模拟面试、打磨模式和复盘是否共用同一评估口径

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
