# M06 模拟面试、上下文与导出 - 模块待确认问题

## 1. 当前模块问题
- OQ-009 Embedding 与向量化来源如何确定
- OQ-011 Search snapshot 的来源只做导入还是需要抓取
- OQ-012 上下文包中的 source priority 与引用摘要规则如何固定
- OQ-018 管理台是否负责 search snapshot 导入与运维

## 2. 问题详情
### OQ-009 Embedding 与向量化来源如何确定

- 为什么影响本模块：会影响检索分块、测试可重复性和后续真实检索质量。
- 当前建议：默认先定义 provider 抽象并使用可重复占位 embedding。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-011 Search snapshot 的来源只做导入还是需要抓取

- 为什么影响本模块：会影响上下文包装配、管理台能力和后续搜索治理。
- 当前建议：默认只消费预导入快照，不做在线抓取。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-012 上下文包中的 source priority 与引用摘要规则如何固定

- 为什么影响本模块：会影响问题生成、可解释性和测试稳定性。
- 当前建议：默认按岗位 > 简历 > 弱项 > 资产 > search snapshot 的优先级装配。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-018 管理台是否负责 search snapshot 导入与运维

- 为什么影响本模块：会影响模块边界，以及上下文包对运营后台的依赖。
- 当前建议：默认由管理台承担导入配置和审计，不承担在线抓取。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`
