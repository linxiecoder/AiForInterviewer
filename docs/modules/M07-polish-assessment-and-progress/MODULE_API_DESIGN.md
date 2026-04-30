---
title: MODULE_API_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m07-polish-assessment-and-progress/module-api-design
---

# M07 打磨模式、评估与进度 - API 设计

## 1. 文档定位

- 本文档用于沉淀本模块的接口清单与契约方向。
- 当前状态：仅有骨架。

## 2. 计划接口清单
- GET /api/v1/practice-topics/recommendations
- POST /api/v1/polish/sessions
- POST /api/v1/polish/sessions/{sessionId}/assess
- GET /api/v1/polish/sessions/{sessionId}/progress

## 3. 需要补充的接口维度

- 请求输入结构
- 响应结构
- 认证与授权要求
- 错误语义
- 分页、过滤、排序、导出等跨接口规则

## 4. 当前缺口

- 尚未把接口契约细化到字段级。
- 尚未把接口与页面、对象、任务流一一对应。

## 5. 进入可作为下游输入前需要补充

- 接口输入输出示例
- 成功/失败响应模型
- 幂等性与异步约束
- 与 MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md 的映射关系