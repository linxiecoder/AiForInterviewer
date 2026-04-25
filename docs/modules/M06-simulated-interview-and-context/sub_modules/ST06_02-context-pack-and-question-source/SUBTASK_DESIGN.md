# ST06_02 上下文包与问题来源规则 - 子任务设计

## 1. 文档定位

- 本文档承接模块设计，并把“上下文包与问题来源规则”拆成可持续细化的子任务设计单元。
- 当前成熟度：仅有骨架。

## 2. 父模块

- M06 模拟面试、上下文与导出；父级索引见 ../../MODULE_TASK_INDEX.md。

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
- 无阻塞级待确认问题。
- historical：旧 `OQ-009` 已由 W13 唯一事实源和 `FC-05` / `DD-021` 覆盖；当前口径为 RAG / 知识库进入一期，支持混合检索，失败时降级继续并标注证据缺口。
- historical：旧 `OQ-011` 已由 W13 唯一事实源和 `FC-18` / `DD-008` 覆盖；当前口径为 Search snapshot 只导入不抓取。
- historical：旧 `OQ-012` 已由 W13 唯一事实源和 `FC-05` / `DD-021` 覆盖；当前口径为 RAG 引用、检索结果与证据缺口进入面试、评分和复盘证据链。
- historical：旧 `OQ-018` 已由 W13 唯一事实源和 `FC-18` 覆盖；当前口径为管理台负责导入与运维入口，完整运维能力低干扰占位。

## 11. 下一轮建议补充

- 补充精确输入输出。
- 补充接口/字段/状态相关设计。
- 补充验证目标与下游引用方式。
