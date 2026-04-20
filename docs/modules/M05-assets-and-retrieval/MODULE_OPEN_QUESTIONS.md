# M05 资产库、归档与检索 - 模块待确认问题

## 1. 当前模块问题
- OQ-009 Embedding 与向量化来源如何确定
- OQ-010 归档粒度是整份资产、片段还是题目级

## 2. 问题详情
### OQ-009 Embedding 与向量化来源如何确定

- 为什么影响本模块：会影响检索分块、测试可重复性和后续真实检索质量。
- 当前建议：默认先定义 provider 抽象并使用可重复占位 embedding。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-010 归档粒度是整份资产、片段还是题目级

- 为什么影响本模块：会影响 archive records、来源追踪和资产复用边界。
- 当前建议：默认支持整份与片段两级，题目级通过来源字段追踪而非额外域对象。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`
