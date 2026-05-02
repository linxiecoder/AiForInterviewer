---
title: SUBTASK_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m03-jobs-resumes-and-documents/sub-modules/st03-03-upload-transform-export/subtask-design
---

# ST03_03 上传、转换与导出链路 - 子任务设计

## 1. 文档定位

- 本文档承接模块设计，并把“上传、转换与导出链路”拆成可持续细化的子任务设计单元。
- 当前成熟度：仅有骨架。

## 2. 父模块

- $(System.Collections.Specialized.OrderedDictionary.Id) 岗位、简历与文档处理。

## 3. 子任务目标

- 沉淀对象存储、PDF 转 Markdown、导出记录和异步链路。

## 4. 输入文档

- ../../MODULE_REQUIREMENTS.md。
- ../../MODULE_DESIGN.md。
- ../../MODULE_API_DESIGN.md。
- ../../MODULE_SCHEMA_DESIGN.md。
- ../../MODULE_LOGIC_DESIGN.md。

## 5. 范围内
- 上传与转换流程设计
- 导出策略
- 对象存储约束

## 6. 不在范围内

- 不直接进入代码实现。
- 不替代父模块的全局边界定义。
- 不解决未进入本子任务范围的跨模块问题。

## 7. 当前已知目标区域
- apps/api/app/services/storage_service.py
- apps/api/app/services/pdf_to_markdown_service.py
- apps/api/app/tasks/**

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
- OQ-006 Markdown 预览与导出是否必须共用同一渲染链
- OQ-007 上传、转换、导出在 P1 中哪些必须异步

## 11. 下一轮建议补充

- 补充精确输入输出。
- 补充接口/字段/状态相关设计。
- 补充验证目标与下游引用方式。