# M07 打磨模式、评估与进度 - 模块待确认问题

## 1. 当前模块问题
- OQ-008 匹配分析与评估规则是否需要版本化
- OQ-013 打磨主题推荐是规则、LLM 还是混合
- OQ-014 模拟面试、打磨模式和复盘是否共用同一评估口径

## 2. 问题详情
### OQ-008 匹配分析与评估规则是否需要版本化

- 为什么影响本模块：会影响评分可追溯性、弱项证据归因和复盘结果复现。
- 当前建议：默认保留规则版本字段和来源记录，但首轮不做复杂配置中心。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-013 打磨主题推荐是规则、LLM 还是混合

- 为什么影响本模块：会影响打磨模式可验证性和实施复杂度。
- 当前建议：默认先做规则推荐，后续再考虑 LLM 增强。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-014 模拟面试、打磨模式和复盘是否共用同一评估口径

- 为什么影响本模块：会影响能力树、评估对象和结果可对比性。
- 当前建议：默认共用核心评分框架，但允许不同场景补充上下文字段。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`
