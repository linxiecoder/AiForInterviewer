---
title: TECH_DESIGN
type: design
status: draft-f4-entry
owner: 技术架构
source_task: AIFI-ARCH-001
permalink: ai-for-interviewer/docs/02-design/tech-design
---

# TECH_DESIGN

## 1. 文档状态

- 本文件是 F4 技术设计入口骨架，用于承接 `AIFI-ARCH-001` 的后续分段设计。
- 本文件不是完整 M4 交付，不替代 `DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。
- 本轮仅建立入口与边界，不关闭 `F4_TECH_DESIGN` UNKNOWN。

## 2. F4 目标

- 基于 PRD、UX_SPEC、UI_DESIGN_SYSTEM 和交付计划，拆分 MVP 技术设计产物。
- 在后续分段中明确数据模型、API、Prompt、LLM 边界、安全隐私、评分与状态策略。
- 为 F5 实现、F7 验收和发布前风险复核提供可追踪技术依据。

## 3. 输入来源

- `docs/01-product/PRD.md`：MVP 业务对象、核心数据流、非目标、评分/复制/通过倾向口径和 UNKNOWN 台账。
- `docs/02-design/UX_SPEC.md`：F2 低保真信息架构、核心页面场景、状态与异常路径。
- `docs/02-design/UI_DESIGN_SYSTEM.md`：F3 设计系统草案、交互状态约束和前端实现交接边界。
- `docs/03-delivery/DELIVERY_PLAN.md`：F4 / M4 目标、产物和阶段边界。
- `docs/03-delivery/BACKLOG.md`：AIFI-ARCH、AIFI-DATA、AIFI-API、AIFI-PROMPT、AIFI-SEC 后续任务入口。

## 4. 非目标

- 不在本文件中完成完整架构设计、数据模型、API 契约、Prompt 规范或安全隐私设计。
- 不创建或关闭 ADR。
- 不更新 BACKLOG、DELIVERY_PLAN、DOCS_INDEX 或任何任务状态。
- 不关闭 PRD §10 中归类为 `F4_TECH_DESIGN` 的 UNKNOWN。
- MVP 不支持 PDF、Markdown、Word 或批量文件导出；报告复制是页面交互，不是文件导出。
- MVP 不支持解析外部材料并自动生成岗位 / JD。
- MVP 不承诺精确通过概率或准确预测面试结果。

## 5. F4 产物拆分

| 产物 | 后续职责 |
| --- | --- |
| `TECH_DESIGN.md` | F4 技术设计入口、范围拆分、后续分段顺序和跨文档边界 |
| `DATA_MODEL.md` | MVP 数据对象、状态、版本、持久化和数据流边界 |
| `API_SPEC.md` | 前后端 API 契约、错误语义、任务追踪和状态流转 |
| `PROMPT_SPEC.md` | Prompt 输入输出、LLM 边界、低信心处理和可追踪约束 |
| `SECURITY_PRIVACY.md` | 隐私字段、数据保留、密钥、权限、安全边界和发布风险 |

## 6. 核心技术设计范围清单

- 简历、岗位 / JD、岗位匹配分析、打磨模式会话、压力面模式会话、进展树、面试报告、面试复盘、薄弱项、资产库、训练建议。
- 项目经历属于简历模块，不是独立顶层业务对象，也不是独立顶层数据对象。
- 覆盖简历与岗位匹配、打磨模式、压力面模式、模拟面试复盘、真实面试复盘和反馈回流数据流。
- 后续需明确 0-100 分数展示的公式、权重、阈值、校准、低信心处理和风险提示边界。
- 后续需明确复制、报告、资产沉淀、薄弱项生命周期、进展树更新和训练建议的技术约束。

## 7. 明确不在本文件展开的内容

- 数据表、字段、枚举、状态机、版本策略和迁移细节。
- API path、request / response schema、错误码、鉴权和异步任务语义。
- Prompt 模板、模型选择、输入裁剪、输出校验、重试和降级策略。
- 安全隐私分级、敏感字段、日志脱敏、密钥管理、数据保留和删除策略。
- 评分算法、推荐算法、弱项合并算法、通过倾向表达和校准细节。

## 8. 后续分段执行顺序

1. 创建 `DATA_MODEL.md`，先收敛业务对象、数据对象、状态与版本边界。
2. 创建 `API_SPEC.md`，对齐页面流、任务流、错误语义和前后端契约。
3. 创建 `PROMPT_SPEC.md`，明确 LLM 输入输出、可追踪性和安全约束。
4. 创建 `SECURITY_PRIVACY.md`，补齐隐私、安全、密钥、日志和发布风险。
5. 回到 `TECH_DESIGN.md` 汇总跨文档决策，并在证据充分时关闭对应 `F4_TECH_DESIGN` UNKNOWN。

## 9. 本轮状态

- 已建立 F4 技术设计入口骨架。
- 未创建 `DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。
- 未修改 BACKLOG、DELIVERY_PLAN、DOCS_INDEX、PRD、UX_SPEC、UI_DESIGN_SYSTEM、ADR、apps、packages 或 archive。
- 未关闭任何 `F4_TECH_DESIGN` UNKNOWN。
