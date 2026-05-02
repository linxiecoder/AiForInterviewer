---
title: DOCUMENT_MATURITY
type: note
permalink: ai-for-interviewer/document-maturity
---

# AI 模拟面试项目文档成熟度

## 1. 文档定位

本文档只记录文档成熟度、下游可用性和风险摘要，不承载需求正文、设计正文、任务正文或过程日志。

## 2. 成熟度摘要

| area | current level | downstream usability | notes |
| --- | --- | --- | --- |
| Workbench MVP requirements | L5 | usable as requirement input | 需求范围与验收口径已独立成层 |
| Workbench MVP design | L5 | usable as design input | 五份设计文档继续承载设计事实 |
| current planning | L4 | usable for governance planning | 当前 planning 文档已迁入 `docs/planning/**` |
| current task docs | L3-L4 | not implementation-ready | formal window 未打开 |
| module docs | L3-L5 | module-dependent | 模块文档保持原路径，不自动放行 |
| governance docs | L5 | usable as collaboration rules | 状态自动化以 `docs/governance/**` 与工具实现为准 |
| process docs | L2-L4 | historical/process only | 过程记录不作为当前需求或设计依据 |

## 3. 当前风险

| risk | severity | mitigation |
| --- | --- | --- |
| implementation readiness may be misread from task docs | medium | 继续以 `DOC_STATE.yaml` 和 gate 为准 |

## 4. 使用规则

- 成熟度等级不等于状态层可实施。
- L5 文档可作为下游输入，但不能替代 formal window 和 implementation packet。
- 本文档不直接修改 `DOC_STATE.yaml`。