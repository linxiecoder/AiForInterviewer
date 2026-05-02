---
title: REQUIREMENT_TRACEABILITY
type: product-traceability
status: active-f1
owner: 产品/文档治理
source_report: archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md
permalink: ai-for-interviewer/docs/01-product/requirement-traceability
---

# REQUIREMENT_TRACEABILITY

本文档只登记历史需求如何被当前 active 产品需求处理。历史设计稿、迁移前需求与迁移前设计只能作为来源证据，不是当前阶段、路线图或任务体系。当前产品需求唯一事实源是 `docs/01-product/PRD.md`。

## 1. 状态定义

| 状态 | 含义 |
|---|---|
| MERGED_TO_PRD | 已迁入 `docs/01-product/PRD.md` |
| PARTIAL | 已有部分迁入，但仍需补齐 PRD、Backlog、Delivery 或 F4 子项 |
| DEFERRED | 有价值但不属于 MVP 发布阻塞范围，并已说明产品原因 |
| REJECTED | 明确不采纳，或已被当前仓库事实替代 |
| UNKNOWN | 证据不足，待人工确认 |

## 2. F1.2 规格化覆盖矩阵

| 需求主题 | 历史来源证据 | PRD 覆盖 | Traceability 处理 | Backlog / Delivery 承接 | 说明 |
|---|---|---|---|---|---|
| 文档状态、PRD 边界和 F1 范围 | `archive/MANIFEST.md` §1-§6；`archive/2026-05-doc-consolidation/legacy/docs/requirements/workbench-mvp/scope-and-acceptance.md` §1 | `PRD.md` §1 | MERGED_TO_PRD | AIFI-PROD-009；F1 退出标准 | 明确 PRD 是产品需求事实源，不包含技术设计、接口设计、数据模型和 Prompt 设计 |
| 产品定位、核心价值和 MVP 成功标准 | 2026-04-20 历史设计稿 §1-§3、§18；legacy requirements §2、§6 | `PRD.md` §2 | MERGED_TO_PRD | AIFI-PROD-001；AIFI-PROD-009 | 从能力清单扩展为可验收的产品目标和成功标准 |
| 用户角色边界 | 2026-04-20 历史设计稿 §3.1、§12；legacy requirements §3 | `PRD.md` §3 | MERGED_TO_PRD | AIFI-PROD-003 | 当前业务终端用户统一为求职者 / 面试准备用户；复杂组织治理不进入本 MVP |
| 核心业务对象 | 2026-04-20 历史设计稿 §7；legacy object model §2-§3；legacy scoring §2-§5 | `PRD.md` §4 | MERGED_TO_PRD；若涉及具体结构则 UNKNOWN | AIFI-PROD-009；AIFI-DATA-001 | 已补齐对象含义、来源、主要信息范围、关系和 MVP 核心属性 |
| 简历与岗位匹配数据流 | 2026-04-20 历史设计稿 §7.2-§7.3、§9.2；legacy lowfi §5.6；legacy IA §4-§5 | `PRD.md` §5.1、§6.1-§6.4 | MERGED_TO_PRD；评分公式、权重和阈值 UNKNOWN | AIFI-PROD-008；AIFI-UX-001；AIFI-DATA-001；AIFI-QA-001 | 数据流已明确不是阶段体系、不是批次体系、不是唯一闭环 |
| 项目打磨与复盘数据流 | 2026-04-20 历史设计稿 §9.4、§9.6、§9.7、§17-§18；legacy scoring §3、§5 | `PRD.md` §5.2、§6.5-§6.7 | MERGED_TO_PRD；资产版本和复盘切分规则 UNKNOWN | AIFI-PROD-007；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 项目打磨、真实项目复盘和资产库均进入 MVP 核心需求 |
| 模拟面试数据流 | 2026-04-20 历史设计稿 §3.4、§9.3-§9.5、§15.4；legacy IA §3-§5；legacy object model §5 | `PRD.md` §5.3、§6.8-§6.13 | MERGED_TO_PRD；题量、节奏和状态细节 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 打磨模式和压力面模式均为 MVP 核心需求 |
| 反馈回流数据流 | 2026-04-20 历史设计稿 §10-§11、§17-§18；legacy scoring §5 | `PRD.md` §5.4、§6.12-§6.14 | MERGED_TO_PRD；自动回流确认规则 UNKNOWN | AIFI-PROD-005；AIFI-PROD-007；AIFI-QA-001 | 模拟反馈可回流到薄弱项、项目打磨、真实项目复盘、资产库和下一次模拟面试输入 |
| 简历规格 | 2026-04-20 历史设计稿 §3.3、§7.2、§9.1；legacy lowfi §5.6 | `PRD.md` §6.1 | MERGED_TO_PRD；扫描件 OCR UNKNOWN | AIFI-PROD-008；AIFI-UX-001；AIFI-DATA-001 | 明确简历按通用简历模块处理，且不等同于资产库 |
| 岗位 / JD 规格 | 2026-04-20 历史设计稿 §7.2、§9.2；legacy requirements §4 | `PRD.md` §6.2 | MERGED_TO_PRD；岗位版本和导入格式 UNKNOWN | AIFI-PROD-008；AIFI-UX-001；AIFI-DATA-001 | 岗位 / JD 是匹配分析和模拟面试的重要输入 |
| 岗位绑定简历 | 2026-04-20 历史设计稿 §9.2；legacy lowfi §5.5-§5.6 | `PRD.md` §6.3 | MERGED_TO_PRD；多简历多岗位规则 UNKNOWN | AIFI-PROD-008；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 已补齐绑定规则、解除绑定规则和验收标准 |
| 岗位匹配度分析 | 2026-04-20 历史设计稿 §7.3、§8、§9.2；legacy lowfi §5.6 | `PRD.md` §6.4 | MERGED_TO_PRD；算法、权重、阈值 UNKNOWN | AIFI-PROD-008；AIFI-DATA-001；AIFI-PROMPT-001；AIFI-QA-001 | 匹配度分数、匹配点、不匹配点、加强点和薄弱项均进入 PRD |
| 项目打磨 | 2026-04-20 历史设计稿 §9.4、§15.4、§17-§18 | `PRD.md` §6.5 | MERGED_TO_PRD；结束标准和版本策略 UNKNOWN | AIFI-PROD-007；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 已补齐用户如何选择或录入项目、系统如何拆解和沉淀 |
| 真实项目复盘 | 2026-04-20 历史设计稿 §9.6、§15.5；legacy scoring §3 | `PRD.md` §6.6 | MERGED_TO_PRD；切分阈值和校对规则 UNKNOWN | AIFI-PROD-007；AIFI-UX-001；AIFI-DATA-001；AIFI-QA-001 | 已补齐复盘对象、复盘维度、输出和薄弱项提炼 |
| 资产库 | 2026-04-20 历史设计稿 §7.4、§9.7、§15.6；legacy object model §2-§3 | `PRD.md` §4、§6.7、§9 | MERGED_TO_PRD；资产版本和合并规则 UNKNOWN | AIFI-PROD-007；AIFI-DATA-001；AIFI-BE-001；AIFI-FE-001 | 明确资产库是独立业务对象，不等同于简历 |
| 模拟面试总览 | 2026-04-20 历史设计稿 §3.4、§9.3；legacy IA §3-§5 | `PRD.md` §6.8 | MERGED_TO_PRD；输入优先级 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-QA-001 | 已补齐两种模式的共同输入、共同进展树和报告 / 复盘差异 |
| 打磨模式 | 2026-04-20 历史设计稿 §9.4、§15.4；legacy scoring §3 | `PRD.md` §6.9 | MERGED_TO_PRD；题目推荐和结束阈值 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-DATA-001；AIFI-PROMPT-001；AIFI-QA-001 | 已补齐同题多轮、详细反馈和暂停恢复上下文 |
| 压力面模式 | 2026-04-20 历史设计稿 §3.4、§9.5；legacy object model §5 | `PRD.md` §6.10 | MERGED_TO_PRD；题量、节奏和追问深度 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 明确压力面不默认允许无限修改同一道题 |
| 进展树 | 2026-04-20 历史设计稿 §7.6、§15.4、§17；legacy IA §5 | `PRD.md` §6.11 | MERGED_TO_PRD；数据结构和更新规则 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-DATA-001；AIFI-FE-001；AIFI-QA-001 | 已补齐专题、主题、技术点、项目、题目、薄弱项和状态规则 |
| 面试报告 | 2026-04-20 历史设计稿 §8、§9.5、§9.6；legacy scoring §1-§4 | `PRD.md` §6.12 | MERGED_TO_PRD；评分公式和分项权重 UNKNOWN | AIFI-PROD-005；AIFI-PROMPT-001；AIFI-QA-001 | 已补齐完整评分、分项评分、建议、失分点、薄弱项和回流 |
| 模拟面试复盘 | 2026-04-20 历史设计稿 §9.6、§15.5；legacy scoring §3 | `PRD.md` §6.13 | MERGED_TO_PRD；回流确认规则 UNKNOWN | AIFI-PROD-005；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 已补齐题目、回答、点评、评分、失分原因和训练建议 |
| 薄弱项与训练建议 | 2026-04-20 历史设计稿 §10-§11；legacy scoring §5 | `PRD.md` §6.14、§8 | MERGED_TO_PRD；算法、合并和生命周期 UNKNOWN | AIFI-PROD-005；AIFI-DATA-001；AIFI-PROMPT-001；AIFI-QA-001 | 已补齐来源、用途、状态、生命周期待确认项和验收标准 |
| 状态与异常 | 2026-04-20 历史设计稿 §16；legacy scoring §6；legacy lowfi §3.7、§7.12 | `PRD.md` §7 | MERGED_TO_PRD | AIFI-UX-001；AIFI-QA-001 | 已补齐缺失、生成中、失败、暂停、恢复失败、报告失败、资产失败和 LLM 输出不可用 |
| 非目标范围 | 2026-04-20 历史设计稿 §2-§3；legacy requirements §5；legacy scope §3 | `PRD.md` §9 | MERGED_TO_PRD；实时语音、视频、ATS、商业化等 DEFERRED | AIFI-PROD-006 | 非目标只列本 MVP 不包含的内容，不降低已进入 PRD 的核心需求 |

## 3. 历史来源处理明细

| 历史来源文件路径 | 历史需求摘要 | 当前处理状态 | 迁入目标位置 / 未迁入原因 | 对应 BACKLOG |
|---|---|---|---|---|
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §2-§3、§18 | 文本面试工作台覆盖岗位、简历、匹配、模拟、打磨、复盘、训练、资产库和管理边界 | MERGED_TO_PRD | `PRD.md` §2-§6、§9 | AIFI-PROD-001、AIFI-PROD-009 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.1、§12 | 团队管理员/成员、单工作区产品形态、成员权限边界 | MERGED_TO_PRD | `PRD.md` §3、§9；复杂组织治理不进入本 MVP | AIFI-PROD-003 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.2、§6 | 参考材料包不是题库；先规划考点再生成自然问题；不得直接复用原题 | MERGED_TO_PRD | `PRD.md` §6.8-§6.10、§10；具体模板进入 F4 UNKNOWN | AIFI-PROD-004、AIFI-PROMPT-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.3、§7.2、§9.1 | PDF/Markdown 简历导入、保留原件、转可编辑文本、版本与导出 | MERGED_TO_PRD | `PRD.md` §6.1；扫描件 OCR 为 UNKNOWN | AIFI-PROD-008、AIFI-DATA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §7.3、§8、§9.2 | 岗位绑定简历、岗位匹配分析、匹配度、缺口、高风险和建议打磨主题 | MERGED_TO_PRD | `PRD.md` §5.1、§6.3-§6.4；评分公式、权重和阈值 UNKNOWN | AIFI-PROD-008、AIFI-UX-001、AIFI-DATA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §9.4、§15.4 | 打磨模式、多轮同题、反馈、进展树、参考回答和技术原理扩展 | MERGED_TO_PRD | `PRD.md` §6.9、§6.11；题目推荐和结束阈值 UNKNOWN | AIFI-PROD-004、AIFI-UX-001、AIFI-QA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §9.5 | 更接近真实面试节奏的连续问答和整场评估 | MERGED_TO_PRD | `PRD.md` §6.10、§6.12；题量和追问深度 UNKNOWN | AIFI-PROD-004、AIFI-QA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §9.6、§15.5 | 真实面试复盘和模拟面试复盘 | MERGED_TO_PRD | `PRD.md` §6.6、§6.13；切分阈值和回流确认规则 UNKNOWN | AIFI-PROD-005、AIFI-PROD-007 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §10-§11 | 薄弱项、训练建议、状态、消减和停练 | MERGED_TO_PRD | `PRD.md` §6.14、§8、§10；算法和生命周期 UNKNOWN | AIFI-PROD-005 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §7.4、§9.7、§15.6 | 资产库、复盘归档、问答归档、长期能力增长 | MERGED_TO_PRD | `PRD.md` §4、§5.2-§5.4、§6.7；复杂资产治理不进入本 MVP | AIFI-PROD-007、AIFI-DATA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §4-§5、§13 | 历史推荐技术方案、内部模块和模型配置细节 | REJECTED / DEFERRED | 不进入 F1 PRD；技术、模型和参数由 F4 处理 | AIFI-ARCH-001、AIFI-PROMPT-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/requirements/workbench-mvp/scope-and-acceptance.md` §2-§6 | 文本优先工作台、关键流程、in-scope / out-of-scope 和验收口径 | MERGED_TO_PRD | `PRD.md` §2、§8-§9 | AIFI-PROD-001、AIFI-PROD-009 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/information-architecture.md` §1-§5 | 记录列表、发起、面试台、复盘详情、训练入口和状态流转 | MERGED_TO_PRD | `PRD.md` §5-§7；页面低保真进入 F2 | AIFI-UX-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/object-model-rag-multiround-backend.md` §1-§8 | 对象族、关系、状态、打磨模式、压力面模式、资产和后端边界 | MERGED_TO_PRD / PARTIAL | 产品对象和状态进入 `PRD.md` §4、§6-§7；具体实现边界进入 F4 | AIFI-ARCH-001、AIFI-DATA-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/scoring-review-export-dod.md` §1-§7 | 0-100 评分、低置信度、复盘、Markdown 导出、薄弱项和质量门禁 | MERGED_TO_PRD | `PRD.md` §6.12-§6.14、§7-§8；评分公式 UNKNOWN | AIFI-PROD-005、AIFI-QA-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/r1-penpot-lowfi-spec.md` §3、§5-§8、§11 | 迁移前低保真规格包含简历匹配评估、双模式启动、面试进展树、复盘详情、空态与异常状态 | MERGED_TO_PRD | `PRD.md` §6-§8；低保真需在 F2 重新基于 active PRD 设计 | AIFI-UX-001、AIFI-QA-001 |

## 4. 待人工确认项

| 编号 | 问题 | 当前状态 | 建议处理 |
|---|---|---|---|
| OQ-F1-001 | 匹配度评分公式、权重和阈值 | UNKNOWN | 进入 F4 技术设计，不阻塞 F2 低保真设计 |
| OQ-F1-002 | 多简历多岗位绑定规则 | UNKNOWN | 人工确认或进入 F4；F2 可先设计 UNKNOWN 提示和默认绑定路径 |
| OQ-F1-003 | 薄弱项算法、合并规则、状态和生命周期 | UNKNOWN | 进入 F4；F2 只需展示来源、状态和操作入口 |
| OQ-F1-004 | 进展树数据结构、节点类型和更新规则 | UNKNOWN | 进入 F4；F2 只需设计用户可见状态与路径 |
| OQ-F1-005 | 资产版本策略、合并规则和质量判断 | UNKNOWN | 进入 F4；F2 只需设计资产沉淀确认和失败态 |
| OQ-F1-006 | Prompt 具体模板、模型选择和模型调用参数 | UNKNOWN | 进入 F4；F1 不冻结 |
| OQ-F1-007 | 打磨模式题目推荐算法和同题结束建议阈值 | UNKNOWN | 进入 F4；F2 可设计多轮同题流程 |
| OQ-F1-008 | 压力面题量、节奏和连续追问深度规则 | UNKNOWN | 进入 F4；F2 可设计连续问答和结束报告流程 |
| OQ-F1-009 | 真实面试材料切分阈值和人工校对规则 | UNKNOWN | 进入 F4；F2 可设计低置信度校对状态 |
| OQ-F1-010 | 复盘、报告、薄弱项、资产库之间的自动回流是否需要用户确认 | UNKNOWN | 人工确认或 F4 冻结；F2 需设计确认态和失败态 |

## 5. F1.2 结论

F1.2 已将 PRD 从“大能力清单”补全为产品需求规格说明书：补齐文档状态、产品目标、用户角色、核心业务对象、核心业务数据流、功能规格、状态与异常、验收标准、非目标范围和集中 UNKNOWN。历史有效需求已同步标记为 `MERGED_TO_PRD`、`PARTIAL`、`DEFERRED`、`REJECTED` 或 `UNKNOWN`；其中产品规格层需求已进入 PRD，算法、结构、模板、模型、权重和技术实现细节保留为 F4 `UNKNOWN`。
