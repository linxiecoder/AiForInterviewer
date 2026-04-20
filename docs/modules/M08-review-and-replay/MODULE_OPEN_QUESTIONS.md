# M08 复盘与回放 - 模块待确认问题

## 1. 当前模块问题
- OQ-010 归档粒度是整份资产、片段还是题目级
- OQ-014 模拟面试、打磨模式和复盘是否共用同一评估口径
- OQ-015 真实面试输入是结构化问答、自由 transcript 还是混合

## 2. 问题详情
### OQ-010 归档粒度是整份资产、片段还是题目级

- 为什么影响本模块：会影响 archive records、来源追踪和资产复用边界。
- 当前建议：默认支持整份与片段两级，题目级通过来源字段追踪而非额外域对象。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-014 模拟面试、打磨模式和复盘是否共用同一评估口径

- 为什么影响本模块：会影响能力树、评估对象和结果可对比性。
- 当前建议：默认共用核心评分框架，但允许不同场景补充上下文字段。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-015 真实面试输入是结构化问答、自由 transcript 还是混合

- 为什么影响本模块：会影响复盘导入 UI、分析拆题质量和下游训练入口。
- 当前建议：默认先用结构化问答数组。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`
