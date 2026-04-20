# ST06_02 上下文包与问题来源规则 - 子任务设计

## 1. 文档定位

- 本文档承接模块设计，并把“上下文包与问题来源规则”拆成可持续细化的子任务设计单元。
- 当前成熟度：仅有骨架。

## 2. 父模块

- $(System.Collections.Specialized.OrderedDictionary.Id) 模拟面试、上下文与导出。

## 3. 子任务目标

- 明确 source priority、search snapshot 消费边界和问题生成引用规则。

## 4. 输入文档

- ../../MODULE_REQUIREMENTS.md。
- ../../MODULE_DESIGN.md。
- ../../MODULE_API_DESIGN.md。
- ../../MODULE_SCHEMA_DESIGN.md。
- ../../MODULE_LOGIC_DESIGN.md。

## 5. 范围内
- context pack 设计
- source summary 契约
- 问题来源约束

## 6. 不在范围内

- 不直接进入代码实现。
- 不替代父模块的全局边界定义。
- 不解决未进入本子任务范围的跨模块问题。

## 7. 当前已知目标区域
- apps/api/app/services/interview_context_service.py
- apps/api/app/models/search_snapshot.py

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
- OQ-009 Embedding 与向量化来源如何确定
- OQ-011 Search snapshot 的来源只做导入还是需要抓取
- OQ-012 上下文包中的 source priority 与引用摘要规则如何固定
- OQ-018 管理台是否负责 search snapshot 导入与运维

## 11. 下一轮建议补充

- 补充精确输入输出。
- 补充接口/字段/状态相关设计。
- 补充验证目标与下游引用方式。
