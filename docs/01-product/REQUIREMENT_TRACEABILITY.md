---
title: REQUIREMENT_TRACEABILITY
type: product-traceability
status: active-f1
owner: 产品/文档治理
source_report: archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md
permalink: ai-for-interviewer/docs/01-product/requirement-traceability
---

# REQUIREMENT_TRACEABILITY

本文档只登记历史需求如何被当前 active 产品需求处理。历史 P1 是历史来源追踪术语，不是当前阶段、路线图或任务体系。当前产品需求唯一事实源是 `docs/01-product/PRD.md`。

## 1. 状态定义

| 状态 | 含义 |
|---|---|
| MERGED_TO_PRD | 已迁入 `docs/01-product/PRD.md` |
| DEFERRED | 有价值但明确后置，不阻塞 MVP |
| REJECTED | 明确不采纳，或已被当前仓库事实替代 |
| UNKNOWN | 证据不足，待人工确认 |

## 2. 历史 P1 需求处理矩阵

| 历史来源文件路径 | 历史需求摘要 | 当前处理状态 | 迁入目标位置 / 未迁入原因 | 对应 BACKLOG |
|---|---|---|---|---|
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §2-§3 | 文本面试 MVP 覆盖岗位、简历、匹配、模拟、复盘、训练和管理边界 | MERGED_TO_PRD | `PRD.md` §1、§2、§4、§14 | AIFI-PROD-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.1、§12 | 团队管理员/成员、单团队产品形态、成员权限边界 | MERGED_TO_PRD | `PRD.md` §3、§12；数据库扩展字段进入 F4 | AIFI-PROD-003 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.1 | 多团队 / 多租户扩展 | DEFERRED | `PRD.md` §13、§14，后置为 LATER | AIFI-PROD-006 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.2、§6 | 参考材料包不是题库；考点规划后再生成问题；不得直接复用原题 | MERGED_TO_PRD | `PRD.md` §7 | AIFI-PROD-004 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §6、§7.9 | 实时互联网搜索结果作为参考材料 | DEFERRED | `PRD.md` §7、§13、§14，后置为 LATER | AIFI-PROD-006 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.3、§7.2、§9.1 | PDF/Markdown 简历导入、保留原件、转可编辑文本、版本与导出 | MERGED_TO_PRD | `PRD.md` §5 | AIFI-PROD-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §7.2、§15.3 | 基于当前 MD 导出简历 PDF | DEFERRED | `PRD.md` §5、§14，标为 COULD | AIFI-PROD-006 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.4、§9.4-§9.5 | 打磨模式与模拟模式 | MERGED_TO_PRD | `PRD.md` §8、§11、§14 | AIFI-PROD-004 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §8 | 规则化评分框架 + AI 解释；通过概率不得黑盒 | MERGED_TO_PRD | `PRD.md` §9、§10、§14 | AIFI-PROD-005 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §9.6、§15.5 | 真实面试复盘和模拟面试复盘 | MERGED_TO_PRD | `PRD.md` §10、§14；真实面试复盘为 SHOULD | AIFI-PROD-005 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §10-§11 | WeaknessItem、训练抽屉、弱项状态、消减和停练 | MERGED_TO_PRD | `PRD.md` §11、§14；自动消减后置 | AIFI-PROD-005 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §12-§13 | 管理台：成员、资产类型、评分规则、模型配置、搜索策略 | MERGED_TO_PRD | `PRD.md` §12、§13、§14；完整治理后台后置 | AIFI-PROD-003 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §7.4、§9.7、§15.6 | 资产库、资产类型 schema、归档到资产库 | DEFERRED | `PRD.md` §12-§14，复杂资产治理不阻塞 MVP | AIFI-PROD-006 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §4 | Next.js + FastAPI + PostgreSQL + pgvector + Redis + 对象存储推荐技术栈 | REJECTED | F1 不冻结技术栈；技术方案进入 F4，且必须以当前仓库事实为准 | AIFI-ARCH-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §13.2 | 系统推荐最新模型并维护模型发布信息 | DEFERRED | `PRD.md` §12-§14；模型选择和验证进入 F4 | AIFI-ARCH-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §14-§18 | 页面 IA、工作台、岗位、简历、模拟、复盘、训练和资产入口 | MERGED_TO_PRD | `PRD.md` §4、§8、§10、§11；页面细化进入 F2 | AIFI-UX-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §19 | 视觉风格和 UI 执行方向 | DEFERRED | 不进入 PRD 正文；作为 F2/F3 设计输入 | AIFI-UX-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/requirements/workbench-mvp/scope-and-acceptance.md` §2-§6 | 文本优先工作台、主链路、in-scope/out-of-scope 和验收口径 | MERGED_TO_PRD | `PRD.md` §1-§4、§13、§15 | AIFI-PROD-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/information-architecture.md` §1-§5 | 记录列表、发起、面试台、复盘详情、训练抽屉和状态流转 | MERGED_TO_PRD | `PRD.md` §4、§8、§10、§11；低保真进入 F2 | AIFI-UX-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/object-model-rag-multiround-backend.md` §2-§8 | 对象族、RAG、状态字段、可追溯保存和后端边界 | MERGED_TO_PRD | `PRD.md` §4、§6-§11；对象细化进入 F4 | AIFI-ARCH-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/scoring-review-export-dod.md` §1-§7 | 0-100 评分、低置信度、复盘、Markdown 导出、弱项和 DoD | MERGED_TO_PRD | `PRD.md` §9-§11、§15 | AIFI-PROD-005 |

## 3. 待人工确认项

| 编号 | 问题 | 当前状态 | 建议处理 |
|---|---|---|---|
| OQ-F1-001 | 是否需要在 MVP 数据模型中强制预留 `team_id` | UNKNOWN | 进入 F4 `DATA_MODEL.md` 或 ADR，不阻塞 F1 产品范围 |
| OQ-F1-002 | PDF 解析是否必须覆盖扫描件 OCR | UNKNOWN | 进入 F4 技术设计；PRD 只冻结“解析失败可手动编辑” |
| OQ-F1-003 | 通过概率的具体公式和阈值 | UNKNOWN | 进入 F4 `PROMPT_SPEC.md` / `DATA_MODEL.md`，F1 只冻结“不得黑盒” |
| OQ-F1-004 | 管理台首版是否提供完整可视化模型配置 | DEFERRED | 当前标为 COULD / LATER，由 F4 决定实现边界 |

## 4. F1 结论

历史 P1 的有效产品需求已迁入 `docs/01-product/PRD.md` 或明确后置。未迁入项仅保留为技术设计、低保真设计或后续范围输入，不能直接作为当前执行依据。
