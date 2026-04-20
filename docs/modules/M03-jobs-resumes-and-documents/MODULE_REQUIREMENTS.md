# M03 岗位、简历与文档处理 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“岗位、简历与文档处理”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：3.3 简历处理边界
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：7.2 岗位与简历
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：9.1 简历导入与编辑
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：9.2 岗位创建与简历绑定
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：15.2 岗位模块
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：15.3 简历模块

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：326-334 岗位与简历域
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：389-411 岗位与简历 API
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：479-505 页面与路由总表
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：722-778 对象存储、Markdown 预览与导出约束
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：1937-2334 任务 4

## 3. 模块目标

- 定义岗位、简历、文档版本、上传、转换、预览与导出的模块边界。

## 4. 模块范围内
- 岗位对象与页面
- 简历对象、文档版本、Markdown 编辑
- 文件上传、PDF 转 Markdown、导出记录

## 5. 不在本模块范围内
- 多格式文档解析矩阵
- 复杂协同编辑
- 音视频简历

## 6. 关键角色与对象
- jobs
- resumes
- resume_documents
- storage_objects
- resume_export_records

## 7. 关键流程
- 岗位创建与编辑
- 简历版本快照与编辑
- 上传 -> 转换 -> 预览 -> 导出链路

## 8. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确接口、鉴权与错误语义。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 9. 当前缺口

- 仍需把原始文档中的细节进一步提纯到稳定边界。
- 仍需把跨模块耦合点从“描述性要求”转为“可引用的文档输入”。

## 10. 待确认问题
- OQ-006 Markdown 预览与导出是否必须共用同一渲染链
- OQ-007 上传、转换、导出在 P1 中哪些必须异步

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
