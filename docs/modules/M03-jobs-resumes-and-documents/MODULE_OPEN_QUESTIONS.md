# M03 岗位、简历与文档处理 - 模块待确认问题

## 1. 当前模块问题
- OQ-006 Markdown 预览与导出是否必须共用同一渲染链
- OQ-007 上传、转换、导出在 P1 中哪些必须异步

## 2. 问题详情
### OQ-006 Markdown 预览与导出是否必须共用同一渲染链

- 为什么影响本模块：会影响简历编辑、导出一致性和文档处理模块的技术选型。
- 当前建议：默认要求预览与导出共用同一语义渲染链。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`

### OQ-007 上传、转换、导出在 P1 中哪些必须异步

- 为什么影响本模块：会影响对象存储、任务队列、导出日志和实施顺序。
- 当前建议：默认转换和正式导出异步，上传元数据登记同步。
- 需要回写的文档：`MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`
