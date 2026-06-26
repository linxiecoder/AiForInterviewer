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
| 核心业务对象 | 2026-04-20 历史设计稿 §7；legacy object model §2-§3；legacy scoring §2-§5 | `PRD.md` §4 | MERGED_TO_PRD；若涉及具体结构则 UNKNOWN | AIFI-PROD-009；AIFI-DATA-001 | 已补齐对象含义、来源、主要信息范围、关系和 MVP 核心属性；历史“项目”不再作为当前一级对象，项目经历归入简历模块 |
| 简历与岗位匹配数据流 | 2026-04-20 历史设计稿 §7.2-§7.3、§9.2；legacy lowfi §5.6；legacy IA §4-§5 | `PRD.md` §5.1、§6.1-§6.4 | MERGED_TO_PRD；评分公式、权重和阈值 UNKNOWN | AIFI-PROD-008；AIFI-UX-001；AIFI-DATA-001；AIFI-QA-001 | 数据流已明确不是阶段体系、不是批次体系、不是唯一闭环 |
| 打磨模式与面试复盘数据流 | 2026-04-20 历史设计稿 §9.4、§9.6、§9.7、§17-§18；legacy scoring §3、§5 | `PRD.md` §5.2-§5.5、§6.5-§6.7 | MERGED_TO_PRD；资产版本和复盘切分规则 UNKNOWN | AIFI-PROD-007；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 历史“项目打磨”修正为打磨模式中的项目经历表达主题；历史“真实项目复盘”修正为面试复盘，含真实面试复盘 |
| 模拟面试数据流 | 2026-04-20 历史设计稿 §3.4、§9.3-§9.5、§15.4；legacy IA §3-§5；legacy object model §5 | `PRD.md` §5.3、§6.8-§6.13 | MERGED_TO_PRD；题量、节奏和状态细节 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 打磨模式和压力面模式均为 MVP 核心需求 |
| 反馈回流数据流 | 2026-04-20 历史设计稿 §10-§11、§17-§18；legacy scoring §5 | `PRD.md` §5.4-§5.6、§6.12-§6.14 | MERGED_TO_PRD；自动回流确认规则 UNKNOWN | AIFI-PROD-005；AIFI-PROD-007；AIFI-QA-001 | 模拟反馈和面试复盘可回流到薄弱项、打磨模式、压力面模式、资产库和下一次模拟面试输入 |
| 简历规格 | 2026-04-20 历史设计稿 §3.3、§7.2、§9.1；legacy lowfi §5.6 | `PRD.md` §6.1 | MERGED_TO_PRD；扫描件 OCR UNKNOWN | AIFI-PROD-008；AIFI-UX-001；AIFI-DATA-001 | 明确简历按通用简历模块处理，且不等同于资产库 |
| 岗位 / JD 手动录入规格 | 2026-04-20 历史设计稿 §7.2、§9.2；legacy requirements §4 | `PRD.md` §6.2 | MERGED_TO_PRD；岗位版本和状态枚举 UNKNOWN | AIFI-PROD-008；AIFI-UX-001；AIFI-DATA-001 | 岗位 / JD 是匹配分析和模拟面试的重要输入；MVP 创建岗位等同于用户手动填写岗位表单 |
| 历史岗位外部材料解析诉求 | 2026-04-20 历史设计稿 §7.2、§9.2；legacy requirements §4 | `PRD.md` §6.2、§10 OQ-F1-006 | DEFERRED | AIFI-PROD-010；AIFI-UX-002 | MVP 岗位只支持手动录入；历史外部文件解析或剪贴板批量生成岗位信息的诉求不标记为 `MERGED_TO_PRD` |
| 岗位绑定简历 | 2026-04-20 历史设计稿 §9.2；legacy lowfi §5.5-§5.6 | `PRD.md` §6.3 | MERGED_TO_PRD；多简历多岗位规则 UNKNOWN | AIFI-PROD-008；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 已补齐绑定规则、解除绑定规则和验收标准 |
| 岗位匹配度分析 | 2026-04-20 历史设计稿 §7.3、§8、§9.2；legacy lowfi §5.6 | `PRD.md` §6.4 | MERGED_TO_PRD；算法、权重、阈值 UNKNOWN | AIFI-PROD-008；AIFI-DATA-001；AIFI-PROMPT-001；AIFI-QA-001 | 匹配度分数、匹配点、不匹配点、加强点和薄弱项均进入 PRD |
| 项目经历 | 2026-04-20 历史设计稿 §7.2、§9.4、§15.4、§17-§18 | `PRD.md` §4、§6.1、§6.5 | MERGED_TO_PRD；版本策略 UNKNOWN | AIFI-PROD-007；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 项目经历归入简历模块，可作为打磨模式、压力面模式、面试复盘和资产库沉淀的输入 |
| 历史“项目打磨”术语 | 2026-04-20 历史设计稿 §9.4、§15.4、§17-§18 | `PRD.md` §5.2、§6.5、§6.9 | MERGED_TO_PRD；结束状态和版本策略 UNKNOWN | AIFI-PROD-007；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 当前口径为打磨模式中的项目经历表达主题，不再作为独立一级能力或主流程 |
| 历史“真实项目复盘”术语 | 2026-04-20 历史设计稿 §9.6、§15.5；legacy scoring §3 | `PRD.md` §5.4-§5.5、§6.6、§6.13 | MERGED_TO_PRD；切分阈值和校对规则 UNKNOWN | AIFI-PROD-007；AIFI-UX-001；AIFI-DATA-001；AIFI-QA-001 | 当前口径为面试复盘；如历史需求实际指向外部真实面试材料，按真实面试复盘处理 |
| 资产库 | 2026-04-20 历史设计稿 §7.4、§9.7、§15.6；legacy object model §2-§3 | `PRD.md` §4、§6.7、§9 | MERGED_TO_PRD；资产版本和合并规则 UNKNOWN | AIFI-PROD-007；AIFI-DATA-001；AIFI-BE-001；AIFI-FE-001 | 明确资产库是独立业务对象，不等同于简历；项目经历相关资产可沉淀，但不改变对象边界 |
| 模拟面试总览 | 2026-04-20 历史设计稿 §3.4、§9.3；legacy IA §3-§5 | `PRD.md` §6.8 | MERGED_TO_PRD；输入优先级 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-QA-001 | 已补齐两种模式的共同输入、共同进展树和报告 / 复盘差异 |
| 打磨模式 | 2026-04-20 历史设计稿 §9.4、§15.4；legacy scoring §3 | `PRD.md` §6.9 | MERGED_TO_PRD；题目推荐和结束阈值 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-DATA-001；AIFI-PROMPT-001；AIFI-QA-001 | 已补齐同题多轮、详细反馈和暂停恢复上下文 |
| 压力面模式 | 2026-04-20 历史设计稿 §3.4、§9.5；legacy object model §5 | `PRD.md` §6.10 | MERGED_TO_PRD；题量、节奏和追问深度 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 明确压力面不默认允许无限修改同一道题 |
| 进展树 | 2026-04-20 历史设计稿 §7.6、§15.4、§17；legacy IA §5 | `PRD.md` §6.11 | MERGED_TO_PRD；数据结构和更新规则 UNKNOWN | AIFI-PROD-004；AIFI-UX-001；AIFI-DATA-001；AIFI-FE-001；AIFI-QA-001 | 已补齐专题、主题、技术点、项目经历主题、题目、薄弱项和状态规则 |
| 面试报告 | 2026-04-20 历史设计稿 §8、§9.5、§9.6；legacy scoring §1-§4 | `PRD.md` §5.5、§6.12 | MERGED_TO_PRD；评分公式、分项权重和通过倾向展示边界 UNKNOWN | AIFI-PROD-005；AIFI-PROMPT-001；AIFI-QA-001 | 已补齐 0-100 产品展示刻度、分项评分、建议、失分点、薄弱项、复制能力和回流；未合并精确通过概率 |
| 面试复盘 | 2026-04-20 历史设计稿 §9.6、§15.5；legacy scoring §3 | `PRD.md` §6.6、§6.13 | MERGED_TO_PRD；回流确认规则 UNKNOWN | AIFI-PROD-005；AIFI-UX-001；AIFI-BE-001；AIFI-FE-001；AIFI-QA-001 | 已补齐模拟面试复盘、真实面试复盘、题目、回答、点评、评分或表现判断、失分原因和训练建议 |
| 薄弱项与训练建议 | 2026-04-20 历史设计稿 §10-§11；legacy scoring §5 | `PRD.md` §6.14、§8 | MERGED_TO_PRD；算法、合并和生命周期 UNKNOWN | AIFI-PROD-005；AIFI-DATA-001；AIFI-PROMPT-001；AIFI-QA-001 | 已补齐来源、用途、状态、生命周期待确认项和验收标准 |
| 状态与异常 | 2026-04-20 历史设计稿 §16；legacy scoring §6；legacy lowfi §3.7、§7.12 | `PRD.md` §7 | MERGED_TO_PRD | AIFI-UX-001；AIFI-QA-001 | 已补齐缺失、生成中、失败、暂停、恢复失败、报告失败、资产失败和 LLM 输出不可用 |
| 非目标范围 | 2026-04-20 历史设计稿 §2-§3；legacy requirements §5；legacy scope §3 | `PRD.md` §9 | MERGED_TO_PRD；实时语音、视频、ATS、商业化等 DEFERRED | AIFI-PROD-006 | 非目标只列本 MVP 不包含的内容，不降低已进入 PRD 的核心需求 |

## 3. 历史来源处理明细

本节出现的 `archive/2026-05-doc-consolidation/legacy/docs/requirements/workbench-mvp/**` 与 `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/**` 只表示历史来源证据；不得恢复为 `docs/requirements/workbench-mvp/**` 或 `docs/design/workbench-mvp/**` active 路径，也不得作为当前开发、验收或测试依据。

| 历史来源文件路径 | 历史需求摘要 | 当前处理状态 | 迁入目标位置 / 未迁入原因 | 对应 BACKLOG |
|---|---|---|---|---|
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §2-§3、§18 | 文本面试工作台覆盖岗位、简历、匹配、模拟、打磨、复盘、训练、资产库和管理边界 | MERGED_TO_PRD | `PRD.md` §2-§6、§9 | AIFI-PROD-001、AIFI-PROD-009 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.1、§12 | 团队管理员/成员、单工作区产品形态、成员权限边界 | MERGED_TO_PRD | `PRD.md` §3、§9；复杂组织治理不进入本 MVP | AIFI-PROD-003 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.2、§6 | 参考材料包不是题库；先规划考点再生成自然问题；不得直接复用原题 | MERGED_TO_PRD | `PRD.md` §6.8-§6.10、§10；具体模板进入 F4 UNKNOWN | AIFI-PROD-004、AIFI-PROMPT-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §3.3、§7.2、§9.1 | PDF/Markdown 简历导入、保留原件、转可编辑文本、版本；历史文件导出诉求 | MERGED_TO_PRD / DEFERRED | 简历导入和编辑进入 `PRD.md` §6.1；扫描件 OCR 为 UNKNOWN；文件导出不进入 MVP，仅支持报告内容复制 | AIFI-PROD-008、AIFI-DATA-001、AIFI-PROD-006 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §7.3、§8、§9.2 | 岗位绑定简历、岗位匹配分析、匹配度、缺口、高风险和建议打磨主题 | MERGED_TO_PRD | `PRD.md` §5.1、§6.3-§6.4；评分公式、权重和阈值 UNKNOWN | AIFI-PROD-008、AIFI-UX-001、AIFI-DATA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §9.4、§15.4 | 打磨模式、多轮同题、反馈、进展树、参考回答、技术原理扩展和项目经历表达打磨 | MERGED_TO_PRD | `PRD.md` §6.5、§6.9、§6.11；题目推荐和结束阈值 UNKNOWN | AIFI-PROD-004、AIFI-UX-001、AIFI-QA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §9.5 | 更接近真实面试节奏的连续问答和整场评估 | MERGED_TO_PRD | `PRD.md` §6.10、§6.12；题量和追问深度 UNKNOWN | AIFI-PROD-004、AIFI-QA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §9.6、§15.5 | 真实面试复盘和模拟面试复盘；历史材料中的“真实项目复盘”按面试复盘处理 | MERGED_TO_PRD | `PRD.md` §6.6、§6.13；切分阈值和回流确认规则 UNKNOWN | AIFI-PROD-005、AIFI-PROD-007 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §10-§11 | 薄弱项、训练建议、状态、消减和停练 | MERGED_TO_PRD | `PRD.md` §6.14、§8、§10；算法和生命周期 UNKNOWN | AIFI-PROD-005 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §7.4、§9.7、§15.6 | 资产库、复盘归档、问答归档、长期能力增长 | MERGED_TO_PRD | `PRD.md` §4、§5.2-§5.4、§6.7；复杂资产治理不进入本 MVP | AIFI-PROD-007、AIFI-DATA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §4-§5、§13 | 历史推荐技术方案、内部模块和模型配置细节 | REJECTED / DEFERRED | 不进入 F1 PRD；技术、模型和参数由 F4 处理 | AIFI-ARCH-001、AIFI-PROMPT-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/requirements/workbench-mvp/scope-and-acceptance.md` §2-§6 | 文本优先工作台、关键流程、in-scope / out-of-scope 和验收口径 | MERGED_TO_PRD | `PRD.md` §2、§8-§9 | AIFI-PROD-001、AIFI-PROD-009 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/information-architecture.md` §1-§5 | 记录列表、发起、面试台、复盘详情、训练入口和状态流转 | MERGED_TO_PRD | `PRD.md` §5-§7；页面低保真进入 F2 | AIFI-UX-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/object-model-rag-multiround-backend.md` §1-§8 | 对象族、关系、状态、打磨模式、压力面模式、资产和后端边界 | MERGED_TO_PRD / PARTIAL | 产品对象和状态进入 `PRD.md` §4、§6-§7；具体实现边界进入 F4 | AIFI-ARCH-001、AIFI-DATA-001 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/scoring-review-export-dod.md` §1-§7 | 0-100 评分、低置信度、复盘、薄弱项和质量门禁 | MERGED_TO_PRD | `PRD.md` §5.5、§6.12-§6.14、§7-§8；合并的是产品展示刻度采用 0-100，不是具体评分公式 | AIFI-PROD-005、AIFI-QA-001、AIFI-ARCH-002 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/scoring-review-export-dod.md` §4 | Markdown 文件导出 | DEFERRED | MVP 不做任何文件导出，仅支持复制报告内容；见 `PRD.md` §5.5、§9、§10 OQ-F1-003 | AIFI-PROD-006、AIFI-FE-001、AIFI-QA-001 |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` §8.4、§9.5、§9.6、§15.4、§19；`archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/scoring-review-export-dod.md` §3 | 通过概率、低置信度和表现风险判断 | UNKNOWN / DEFERRED | 当前不合并为精确概率功能；目标效果已吸收到 `PRD.md` §5.5、§6.10、§6.12：帮助用户理解表现差距、风险和改进方向；具体概率展示方式、算法、阈值、可信度说明后续由 OQ-F1-040 关闭 | AIFI-ARCH-002、AIFI-PROMPT-001、AIFI-QA-002 |
| `archive/2026-05-doc-consolidation/legacy/docs/design/workbench-mvp/r1-penpot-lowfi-spec.md` §3、§5-§8、§11 | 迁移前低保真规格包含简历匹配评估、双模式启动、面试进展树、复盘详情、空态与异常状态 | MERGED_TO_PRD | `PRD.md` §6-§8；低保真需在 F2 重新基于 active PRD 设计 | AIFI-UX-001、AIFI-QA-001 |

## 4. F1.3 UNKNOWN 收敛同步

`PRD.md` §10 是完整 UNKNOWN 收敛台账；本节只同步历史需求未完全确认部分的处理状态和任务承接，避免历史来源中的缺口在 F2/F4/F7 被遗忘。

| 历史未完全确认主题 | 对应 PRD UNKNOWN | 分类 | 当前状态 | 承接 AIFI-* 任务 | 关闭后写入目标文档 | 关闭标准 |
|---|---|---|---|---|---|---|
| 扫描件 OCR 与文件导出 | OQ-F1-001、OQ-F1-003 | DEFERRED_WITH_REASON | UNKNOWN 已绑定处理策略；MVP 不做 PDF、Markdown 文件、Word / docx 或批量导出，仅支持复制报告内容 | AIFI-PROD-006、AIFI-PROD-010、AIFI-FE-001、AIFI-QA-001 | `PRD.md`、`REQUIREMENT_TRACEABILITY.md`、`BACKLOG.md` | 明确不作为 MVP 发布阻塞，F2 只设计复制入口和反馈，F7 不按文件导出设置阻塞验收 |
| 简历、岗位、项目经历和资产版本策略 | OQ-F1-002、OQ-F1-004、OQ-F1-013、OQ-F1-018 | F4_TECH_DESIGN | UNKNOWN 已绑定 F4 承接 | AIFI-DATA-001、AIFI-ARCH-002 | `DATA_MODEL.md`、`TECH_DESIGN.md` | F4 文档明确版本、引用、历史回看和更新规则 |
| 岗位状态、多简历多岗位绑定和解除绑定 | OQ-F1-005、OQ-F1-007、OQ-F1-008 | F2_UX_BLOCKING | UNKNOWN 已绑定 F2 承接 | AIFI-UX-002 | `UX_SPEC.md` | F2 低保真关闭岗位状态、绑定关系和解除绑定后默认行为 |
| 岗位输入方式与外部材料解析范围 | OQ-F1-006 | DEFERRED_WITH_REASON | F1 已关闭，结论为岗位 / JD 仅支持手动录入 | AIFI-PROD-010、AIFI-UX-002 | `PRD.md`、`UX_SPEC.md` | PRD 已冻结岗位手动录入字段；F2 只承接岗位手动录入表单低保真设计，不承接外部材料解析路径 |
| 岗位匹配评分公式、权重、阈值、校准方法和低置信度 | OQ-F1-009、OQ-F1-010、OQ-F1-011 | F4_TECH_DESIGN | PRD 已合并 0-100 产品展示刻度；公式、权重、阈值和校准方法仍由 F4 承接 | AIFI-DATA-001、AIFI-PROMPT-001、AIFI-ARCH-002、AIFI-QA-002 | `DATA_MODEL.md`、`PROMPT_SPEC.md`、`TECH_DESIGN.md`、`TEST_PLAN.md` | F4 关闭评分生成口径，F7 转为可测断言 |
| 打磨模式、面试复盘和资产确认态 | OQ-F1-012、OQ-F1-014、OQ-F1-016、OQ-F1-017、OQ-F1-020 | F2_UX_BLOCKING | UNKNOWN 已绑定 F2 承接 | AIFI-UX-002、AIFI-QA-002 | `UX_SPEC.md`、`TEST_PLAN.md` | F2 低保真覆盖完成态、确认态、低置信度校对、合并展示和失败态 |
| 真实面试材料切分、资产合并和质量判断 | OQ-F1-015、OQ-F1-019 | F4_TECH_DESIGN | UNKNOWN 已绑定 F4 承接 | AIFI-PROMPT-001、AIFI-DATA-001、AIFI-ARCH-002 | `PROMPT_SPEC.md`、`DATA_MODEL.md`、`TECH_DESIGN.md` | F4 明确切分、合并、质量判断和降级规则 |
| 模拟面试输入优先级和增强输入缺失提示 | OQ-F1-021、OQ-F1-022 | F4_TECH_DESIGN / F2_UX_BLOCKING | UNKNOWN 已拆分到 F2 和 F4 | AIFI-UX-002、AIFI-PROMPT-001、AIFI-ARCH-002 | `UX_SPEC.md`、`PROMPT_SPEC.md`、`TECH_DESIGN.md` | F2 关闭用户提示，F4 关闭输入优先级和编排规则 |
| 打磨模式题目推荐、结束阈值和暂停恢复 | OQ-F1-023、OQ-F1-024、OQ-F1-025 | F4_TECH_DESIGN | UNKNOWN 已绑定 F4 承接 | AIFI-DATA-001、AIFI-PROMPT-001、AIFI-ARCH-002 | `DATA_MODEL.md`、`PROMPT_SPEC.md`、`TECH_DESIGN.md` | F4 明确推荐依据、结束建议和恢复上下文保存策略 |
| 压力面题量、节奏、暂停和追问深度 | OQ-F1-026、OQ-F1-027、OQ-F1-028 | F2_UX_BLOCKING / F4_TECH_DESIGN | UNKNOWN 已拆分到 F2 和 F4 | AIFI-UX-002、AIFI-PROMPT-001、AIFI-ARCH-002 | `UX_SPEC.md`、`PROMPT_SPEC.md`、`TECH_DESIGN.md` | F2 关闭用户流程和暂停规则，F4 关闭追问深度和停止条件 |
| 进展树展示层级、数据结构和推荐算法 | OQ-F1-029、OQ-F1-030、OQ-F1-031 | F2_UX_BLOCKING / F4_TECH_DESIGN | UNKNOWN 已按展示层和结构层拆分 | AIFI-UX-002、AIFI-DATA-001、AIFI-ARCH-002、AIFI-PROMPT-001 | `UX_SPEC.md`、`DATA_MODEL.md`、`TECH_DESIGN.md`、`PROMPT_SPEC.md` | F2 关闭展示层级，F4 关闭数据结构、状态更新和推荐算法 |
| 面试报告评分、重试、复盘切分、展示和复制 | OQ-F1-032、OQ-F1-033、OQ-F1-034、OQ-F1-036 | F4_TECH_DESIGN / F2_UX_BLOCKING | PRD 已合并 0-100 产品展示刻度和复制能力；评分公式、重试和切分规则拆分到 F2 和 F4 | AIFI-UX-002、AIFI-PROMPT-001、AIFI-ARCH-002、AIFI-QA-002 | `UX_SPEC.md`、`PROMPT_SPEC.md`、`TECH_DESIGN.md`、`TEST_PLAN.md` | F2 关闭展示关系和复制反馈，F4 关闭评分、重试和切分规则，F7 转为测试断言 |
| 通过概率、通过倾向和风险提示展示边界 | OQ-F1-040 | F4_TECH_DESIGN | 当前不合并为精确概率功能；PRD 只保留表现差距、风险提示和改进方向的目标效果 | AIFI-ARCH-002、AIFI-PROMPT-001、AIFI-QA-002 | `TECH_DESIGN.md`、`PROMPT_SPEC.md`、`TEST_PLAN.md` | F4 明确可信度说明、免责声明和展示边界；F7 验证不得误导用户或承诺精确通过概率 |
| 自动回流是否需要用户确认 | OQ-F1-035 | HUMAN_CONFIRMATION | UNKNOWN 已绑定人工确认和 F2 承接 | AIFI-PROD-010、AIFI-UX-002 | `REQUIREMENT_TRACEABILITY.md`、`UX_SPEC.md` | 人工确认默认策略，F2 低保真体现确认入口、取消态和失败态 |
| 薄弱项算法、合并、生命周期和自动消减 | OQ-F1-037、OQ-F1-038、OQ-F1-039 | F4_TECH_DESIGN | UNKNOWN 已绑定 F4 承接 | AIFI-DATA-001、AIFI-PROMPT-001、AIFI-ARCH-002 | `DATA_MODEL.md`、`PROMPT_SPEC.md`、`TECH_DESIGN.md` | F4 明确薄弱项提炼、合并、状态流转、来源证据和自动消减规则 |

## 5. BMAD feedback-loop C-ID 追踪登记

本节只登记 2026-06-23 BMAD feedback-loop 需求进入 active docs 的追踪入口。`_bmad-output/planning-artifacts/PRD.md` 是需求来源；`.omo/plans/bmad-feedback-loop-refactor-planning.md` 是工程规划来源。BMAD PRD、brief、addendum 和 Lazycodex plan 不替代本文件、`PRD.md` 或 `BACKLOG.md` 的 active 治理入口。

| 来源组 | 状态 | active doc 去向 | BACKLOG 承接 | 关闭条件 |
|---|---|---|---|---|
| C-001、C-003 到 C-014、C-016 到 C-019、C-021 到 C-029、C-031 到 C-032、C-034 到 C-047 | Confirmed，待 active docs 分流 | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-002、C-015、C-020、C-030、C-033 | Rejected / Non-goal | `PRD.md` §9、§12；本文件 | AIFI-PROD-011、AIFI-TRACE-001 | 不进入实现范围；如后续重新评估，必须走 PRD 变更流程 |
| C-048 / BR-024 | Confirmed product sorting rule | `PRD.md` §12、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`UX_SPEC.md` | AIFI-PROD-011、AIFI-ARCH-009、AIFI-QA-003 | 只关闭产品排序规则，不关闭 C-054 的具体算法 |
| C-049 到 C-054 | Deferred / Open Question | `PRD.md` §12、相关 active design docs 的待确认项 | AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-QA-004、AIFI-BE-010 到 AIFI-BE-015、AIFI-BE-017、AIFI-FE-003、AIFI-FE-004、AIFI-QA-005、AIFI-REL-009 | 仍保持 Deferred；后续只允许按 BACKLOG 对应 AIFI 执行测试护栏、兼容投影、fail-closed、Step5 趋势一致性、后端 API schema / response envelope 汇总、页面恢复、Step11 integration QA 和 release gate，不得关闭这些 C-ID |

### 5.1 C-001 到 C-054 单项追踪矩阵

| C-ID | 来源状态 | PRD 去向 | active doc 去向 | BACKLOG 承接 | 关闭条件 |
|---|---|---|---|---|---|
| C-001 | Confirmed | §2 Goals、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-002 | Rejected / Non-goal | §3 Non-goals | `PRD.md` §9、§12；`REQUIREMENT_TRACEABILITY.md` | AIFI-PROD-011、AIFI-TRACE-001 | 不进入实现范围；如后续重新评估，必须走 PRD 变更流程 |
| C-003 | Confirmed | §7 Business Rules、§8 Compatibility Constraints | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-004 | Confirmed | §7 Business Rules、§8 Compatibility Constraints | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-005 | Confirmed | §7 Business Rules、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-006 | Confirmed | §7 Business Rules、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-007 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-008 | Confirmed | §5 Functional Requirements | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-009 | Confirmed | §5 Functional Requirements | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-010 | Confirmed | §5 Functional Requirements、§8 Compatibility Constraints | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-011 | Confirmed | §5 Functional Requirements | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-012 | Confirmed | §5 Functional Requirements | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-013 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-014 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-015 | Rejected / Non-goal | §3 Non-goals、§5 Functional Requirements | `PRD.md` §9、§12；`REQUIREMENT_TRACEABILITY.md` | AIFI-PROD-011、AIFI-TRACE-001 | 不进入实现范围；如后续重新评估，必须走 PRD 变更流程 |
| C-016 | Confirmed | §5 Functional Requirements、§8 Compatibility Constraints | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-017 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-018 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-019 | Confirmed | §5 Functional Requirements、§8 Compatibility Constraints | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-020 | Rejected / Non-goal | §3 Non-goals、§5 Functional Requirements | `PRD.md` §9、§12；`REQUIREMENT_TRACEABILITY.md` | AIFI-PROD-011、AIFI-TRACE-001 | 不进入实现范围；如后续重新评估，必须走 PRD 变更流程 |
| C-021 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-022 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-023 | Confirmed | §5 Functional Requirements、§7 Business Rules、§9 Risk | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-024 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-025 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-026 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-027 | Confirmed | §5 Functional Requirements、§7 Business Rules、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-028 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-029 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-030 | Rejected / Non-goal | §3 Non-goals、§5 Functional Requirements | `PRD.md` §9、§12；`REQUIREMENT_TRACEABILITY.md` | AIFI-PROD-011、AIFI-TRACE-001 | 不进入实现范围；如后续重新评估，必须走 PRD 变更流程 |
| C-031 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-032 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-033 | Rejected / Non-goal | §3 Non-goals、§8 Compatibility Constraints | `PRD.md` §9、§12；`REQUIREMENT_TRACEABILITY.md` | AIFI-PROD-011、AIFI-TRACE-001 | 不进入实现范围；如后续重新评估，必须走 PRD 变更流程 |
| C-034 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-035 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-036 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-037 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-038 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-039 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-040 | Confirmed | §5 Functional Requirements、§7 Business Rules | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-041 | Confirmed | §5 Functional Requirements、§7 Business Rules、§8 Compatibility Constraints | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-042 | Confirmed | §5 Functional Requirements、§7 Business Rules、§9 Risk | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-043 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-044 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-045 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-046 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-047 | Confirmed | §5 Functional Requirements、§10 Acceptance Criteria | `PRD.md` §12、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`SECURITY_PRIVACY.md`、`RELEASE_HANDOFF_SPEC.md` | AIFI-PROD-011、AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 | 对应 active docs 明确需求语义、兼容边界、验收边界和 release gate；实现前仍需当轮 scope lock |
| C-048 | Confirmed product sorting rule（BR-024） | §5 Functional Requirements、§7 Business Rules、§10 Acceptance Criteria | `PRD.md` §12、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`UX_SPEC.md` | AIFI-PROD-011、AIFI-ARCH-009、AIFI-QA-003 | 只关闭产品排序规则，不关闭 C-054 的具体算法 |
| C-049 | Deferred / Open Question | §11 Open Questions、§12 Lazycodex Planning Inputs、§12.1 Architecture Inputs | `PRD.md` §12、相关 active design docs 的待确认项 | AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-QA-004、AIFI-BE-014、AIFI-REL-009 | 仍保持 Deferred；后续实现只允许在 AIFI-QA-004 / AIFI-BE-014 中建立测试护栏和保守拦截行为，不得定义最终阈值或关闭该 C-ID |
| C-050 | Deferred / Open Question | §11 Open Questions、§12 Lazycodex Planning Inputs、§12.1 Architecture Inputs | `PRD.md` §12、相关 active design docs 的待确认项 | AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-QA-004、AIFI-BE-010、AIFI-REL-009 | 仍保持 Deferred；后续实现只允许 read-time projection / compatibility guard，不得新增表结构、决定迁移或关闭该 C-ID |
| C-051 | Deferred / Open Question | §11 Open Questions、§12 Lazycodex Planning Inputs、§12.1 Architecture Inputs | `PRD.md` §12、相关 active design docs 的待确认项 | AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-QA-004、AIFI-FE-003、AIFI-FE-004、AIFI-QA-005、AIFI-REL-009 | 仍保持 Deferred；后续实现只允许 view model、失败折叠、页面恢复护栏和真实页面 QA，不得冻结最终 UI 形态或关闭该 C-ID |
| C-052 | Deferred / Open Question | §11 Open Questions、§12 Lazycodex Planning Inputs、§12.1 Architecture Inputs | `PRD.md` §12、相关 active design docs 的待确认项 | AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-QA-004、AIFI-BE-011、AIFI-FE-003、AIFI-QA-005、AIFI-REL-009 | 仍保持 Deferred；后续实现只允许 fail-closed validation、failure folding 和真实页面 failure display QA，不得新增最终错误码或关闭该 C-ID |
| C-053 | Deferred / Open Question | §11 Open Questions、§12 Lazycodex Planning Inputs、§12.1 Architecture Inputs | `PRD.md` §12、相关 active design docs 的待确认项 | AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-QA-004、AIFI-BE-013、AIFI-FE-004、AIFI-QA-005、AIFI-REL-009 | 仍保持 Deferred；后续实现只允许 progress/manual completion 一致性、刷新恢复护栏和真实页面 refresh recovery QA，不得决定最终前端状态机或关闭该 C-ID |
| C-054 | Deferred / Open Question | §11 Open Questions、§12 Lazycodex Planning Inputs、§12.1 Architecture Inputs | `PRD.md` §12、相关 active design docs 的待确认项 | AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003、AIFI-QA-004、AIFI-BE-014、AIFI-QA-005、AIFI-REL-009 | 仍保持 Deferred；后续实现只允许基于 BR-024 的产品排序护栏、signed next action 展示 QA 和 QA 断言，不得选择最终下一题算法或关闭该 C-ID |

### 5.2 C-049 到 C-054 保留探索项

| C-ID | 当前状态 | 探索方向 | 禁止事项 |
|---|---|---|---|
| C-049 | Deferred / Open Question | 相似题拦截的评测方法、人工标注样本、误杀 / 漏拦截容忍度 | 不定义阈值，不选择算法 |
| C-050 | Deferred / Open Question | 考察点与题目绑定关系属于数据、状态、反馈投影还是生成上下文 | 不新增表结构，不决定迁移 |
| C-051 | Deferred / Open Question | 失败反馈、低置信、超时和 validation failed 的折叠与展示优先级 | 不设计最终 UI |
| C-052 | Deferred / Open Question | provider / validator / request seam 到 API error、用户文案和 retryable 的映射 | 不新增错误码，不改 API 行为 |
| C-053 | Deferred / Open Question | answer saved、feedback pending、task timeout、session refresh、progress refresh failed 的状态提示去重与恢复 | 不决定最终前端状态机 |
| C-054 | Deferred / Open Question | 基于 C-048 产品排序规则拆解下一题算法输入 / 输出和 QA 断言 | 不选择算法，不写评分函数 |

### 5.3 Plan Readiness P1 处理登记

| P1 项 | active docs 承接 | 状态 |
|---|---|---|
| 验收语义仍需硬化 | `PRD.md` §12、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`UX_SPEC.md`、`RELEASE_HANDOFF_SPEC.md`；AIFI-QA-003；AIFI-QA-004 | 已拆分为 implementation-ready 测试入口；C-049 到 C-054 仍为 Deferred，Step 1 只能建立测试护栏和验收矩阵 |
| 兼容性矩阵不足 | `API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`UX_SPEC.md`、`RELEASE_HANDOFF_SPEC.md`；AIFI-BE-009、AIFI-FE-002、AIFI-BE-010、AIFI-BE-011、AIFI-BE-017、AIFI-FE-003、AIFI-FE-004、AIFI-QA-005 | 已拆分为后端兼容投影、fail-closed validation、后端 API schema / response envelope 汇总、前端 view model、刷新恢复入口和 Step11 integration / real page QA；不得新增迁移或关闭 Deferred C-ID |
| Lazycodex 输出边界要写硬 | `PRD.md` §12、本文件、`BACKLOG.md` §2、各 active design docs 回写段落；AIFI-QA-004、AIFI-BE-010 到 AIFI-BE-015、AIFI-BE-017、AIFI-FE-003、AIFI-FE-004、AIFI-QA-005、AIFI-REL-009 | 已登记，`.omo/plans/plan.md` 只作为工程规划来源；可执行范围以 BACKLOG 对应 AIFI 的允许/禁止路径为准 |
| 回滚 / 降级需要后续规划补出 TODO | `RELEASE_HANDOFF_SPEC.md`、`BACKLOG.md` AIFI-REL-008、AIFI-REL-009 | 已拆分为 release gate / rollback checklist 入口；未完成前不得进入 release-ready 判断 |

### 5.4 feedback-loop implementation-ready 授权入口同步

| plan.md Step | BACKLOG 授权入口 | 执行边界 |
|---|---|---|
| Step 1 | AIFI-QA-004 | 只允许写 feedback acceptance semantics tests；C-049 到 C-054 只写 Deferred guard |
| Step 2、Step 8 中 effective feedback state / schema compatibility | AIFI-BE-010 | 本入口只授权 effective feedback state、feedback history、failure record exclusion、old payload compatibility、read-time projection、current effective selector 兼容依赖和相关 tests/api；AIFI-BE-009 仅作参考上下文，AIFI-BE-009=NOT_STARTED 不再硬阻塞 AIFI-BE-010；不允许 migration、FE、release、Step3 fail-closed validation、Step4 same-answer stability、Step5 improvement trend、Step6 progress mastery 或 Step7 question generation |
| Step 3、Step 8 | AIFI-BE-011 | 只允许 Step 3：BE 反馈生成 fail-closed 与 payload validator，包括 payload validation、invalid / malformed / inconsistent feedback fail-closed、safe failure payload、retryable terminal failure、session detail 不把失败 payload 当作 generated feedback，以及 Step 8 中失败 envelope / schema 兼容的相关 tests/api；不授权 Step 4 same-answer stability、Step 5 improvement trend、Step 6 progress mastery、Step 7 question generation、FE、migration 或 release |
| Step 4 | AIFI-BE-012 | 只允许 same-answer stability、reference-answer replay、scoring normalization 和相关 tests/api；不授权 Step5 improvement trend、Step6 progress mastery、Step7 question generation、FE、migration 或 release |
| Step 5 | AIFI-BE-015 | 只允许 improved-answer trend calibration、score_delta / dimension_delta、current effective feedback result consistency、failure record 不回退 current effective result，以及与 AIFI-BE-010 / AIFI-BE-011 / AIFI-BE-012 的兼容 tests/api；不授权 Step6 progress mastery、Step7 next-question generation、FE、migration、release 或关闭 C-049 到 C-054 |
| Step 6 | AIFI-BE-013 | 已完成 progress mastery、score evolution、longitudinal feedback summary、stable user state projection 和相关 tests/api；输出为 derived-only，不授权 Step7 question generation、next_question_recommendation、adaptive_learning_path、auto_tutoring 或 trend_autopilot |
| Step 7 | AIFI-BE-014 | 已完成 follow_up_intent_classification、same_node_follow_up_contract、same_node_next_question_candidate_selection、next_question_response_contract、policy_signed_next_action、no_auto_generation_without_policy_signature；implementation commit 为 `bad29f58389ddd1a0bb440af31c03139eee633f7`；不关闭 C-049 / C-054，不授权 Step8、FE、migration、release 或泛化 question generation |
| Step 8 backend API schema and response envelope boundary | AIFI-BE-017 | 已完成后端 API response envelope / schema contract 汇总，包括 feedback / progress / follow-up / signed next action payload schema alignment、effective feedback / failure response contract、backwards-compatible API projection 和 backend contract tests；implementation commit 为 `23990da79118d200024735f193ba9b5d4499d4a2`；不授权 FE、migration、release、Step9-12 或关闭 C-049 到 C-054 |
| Step 9 | AIFI-FE-003 | 已完成 `apps/web/src/entities/polish/**` view model（视图模型）、failure folding（失败折叠）、response contract projection（响应契约投影）和相关 FE tests（前端测试）；implementation commit（实现提交）为 `7f5f889`；不授权 Step10 / Step11 / Step12 或关闭 C-049 到 C-054 |
| Step 10 | AIFI-FE-004 | 已完成 Step10 面试工作台页面层反馈交互和刷新恢复收口；implementation commit（实现提交）为 `8aa4d01bcf36b4929d477a76582848f7d6545d2d`；不授权 Step11 integration（集成）/ real page QA（真实页面验收）、Step12 release（发布）、backend（后端）语义变更或关闭 C-049 到 C-054 |
| Step 11 | AIFI-QA-005 | 已完成 integration QA（集成质量验证）和 real page QA（真实页面验收）所必需的最小修复；implementation commits 为 `9a97458`、`bd3c861`；已复现并修复 Step10 limited smoke residual risk，并补齐 partial、refresh recovery、trusted / untrusted signed action 证据；不授权 release、rollback、migration、config、dependency、新评分/策略逻辑、新题生成或关闭 C-049 到 C-054 |
| Step 12 | AIFI-REL-009 | 只允许 release docs / runbook / QA evidence docs；不得改业务代码或测试代码；必须等待 AIFI-QA-005 完成后才能进入 release gate 判断 |

### 5.5 Step 1 / AIFI-QA-004 Accepted-RED 状态登记

本节登记 `.omo/plans/plan.md` Step 1 的当前执行状态。该状态只用于追踪 Step 1 / AIFI-QA-004 的测试护栏结果，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不授权 Step 2 或后续实现步骤。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 1：验收语义硬化与测试矩阵冻结 |
| BACKLOG 授权入口 | AIFI-QA-004 |
| 当前状态 | ACCEPTED_RED |
| 测试命令 | `PYTHONPATH=.:apps/api python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_acceptance_semantics.py -q` |
| 当前结果 | `2 failed, 3 passed` |
| 允许修改范围 | `tests/api/test_polish_feedback_acceptance_semantics.py`；必要时包括命名清晰的 `tests/api/test_polish_feedback_*acceptance*.py` |
| 禁止修改范围 | `apps/**`；`apps/web/**`；`apps/api/migrations/**`；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**` |
| 下一步授权 | 本节不授权 Step 2；Step 2 必须重新执行 scope lock |

#### Step 1 覆盖范围

AIFI-QA-004 只覆盖首批 feedback acceptance semantics 测试护栏：

| AC | 当前状态 | 说明 |
|---|---|---|
| AC-001 | RED | 同题同答稳定性测试已建立；当前实现的 score band 超过允许范围，属于实现缺口，不是测试装配错误 |
| AC-002 | 已纳入 Step 1 测试护栏 | 改进趋势语义进入测试设计和断言范围；当前状态以 pytest 输出为准 |
| AC-003 | RED | 参考答案回灌测试已建立；当前 replay score 低于高分预期，属于实现缺口，不是测试装配错误 |
| AC-012 | 已纳入 Step 1 测试护栏 | 失败不伪成功语义进入测试设计和断言范围；当前状态以 pytest 输出为准 |

AIFI-QA-004 不覆盖以下验收项的完成：

- AC-004 到 AC-011。
- AC-013 到 AC-015。

这些验收项仍由后续 BE / FE / QA / REL steps 按 `BACKLOG.md` 和本文件 §5.4 的授权映射承接。

#### Accepted-RED 解释

`ACCEPTED_RED` 表示 Step 1 已产出首批可运行的 feedback acceptance semantics tests，且当前 RED 结果被接受为后续实现缺口证据。

当前 RED 不表示 Step 1 失败，也不表示测试装配错误。当前 RED 只说明：

- AC-001 的同题同答稳定性尚未由实现满足。
- AC-003 的参考答案回灌高分自洽尚未由实现满足。

Step 1 没有修改后端业务实现、前端实现、migration、配置、依赖或 API schema。

#### Deferred Guard

C-049 到 C-054 仍保持 `Deferred / Open Question`。

Step 1 / AIFI-QA-004 只允许建立 Deferred guard 测试护栏，不得关闭或实现以下事项：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。

#### 下一步约束

Step 1 的 `ACCEPTED_RED` 不直接授权实现 Step 2。

`BACKLOG.md` 已将 `AIFI-BE-010` 同步为 `DONE / CLOSED`；Step 2 effective feedback selector 已由 `.omo/evidence/plan/step2-closeout.md` 和 commit `763ad98668535998bb7c16ad32e08d7bae1bc94a` 证明完成。`AIFI-BE-009` 仅作为参考上下文，`AIFI-BE-009=NOT_STARTED` 不再硬阻塞 `AIFI-BE-010`。该 closeout 只覆盖 Step 2 effective feedback state / selector，不授权 Step 5 improvement trend implementation。

### 5.6 Step 3 / AIFI-BE-011 Final Closeout 状态登记

本节登记 `.omo/plans/plan.md` Step 3 / `AIFI-BE-011` 的最终 closeout 状态。该状态只说明 fail-closed feedback validation 已完成并通过 closeout，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不授权 Step 4 或后续实现步骤。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 3：BE 反馈生成 fail-closed 与 payload validator |
| BACKLOG 授权入口 | AIFI-BE-011 |
| previous_status | FAIL_CHECK_ENV |
| final_status | PASS |
| commit | ef1391c |
| closeout evidence | `.omo/evidence/plan/step3-final-closeout.md` |
| supersede | `.omo/evidence/plan/step3-closeout.md` 保留为历史 evidence，其 `FAIL_CHECK_ENV` 结论已被 final closeout supersede |
| 验证摘要 | Step3 review-work PASS；环境阻断已解除；exact pytest 未设置 `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS` 且通过 |
| 下一步授权 | 本节不授权 Step 4；Step 4 必须重新执行 scope lock，并以 `BACKLOG.md` 对应 AIFI 授权入口为准 |

#### Step 3 覆盖范围

AIFI-BE-011 只覆盖 Step 3 fail-closed feedback validation closeout：

- invalid / malformed / inconsistent feedback fail-closed。
- safe failure payload。
- retryable terminal failure。
- session detail 不把失败 payload 当作 generated feedback。
- Step 8 中与失败 envelope / schema 兼容直接相关的 tests/api。

AIFI-BE-011 不覆盖以下事项：

- Step 4 same-answer stability。
- Step 5 improvement trend。
- Step 6 progress mastery。
- Step 7 question generation。
- FE、migration 或 release。

#### Deferred Guard

C-049 到 C-054 仍保持 `Deferred / Open Question`。

Step 3 / AIFI-BE-011 只关闭 fail-closed feedback validation，不得关闭或实现以下事项：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。

### 5.7 Step 4 / AIFI-BE-012 Closeout 状态登记

本节登记 `.omo/plans/plan.md` Step 4 / `AIFI-BE-012` 的最终 closeout 状态。该状态只说明 same-answer stability、reference-answer replay 和 scoring normalization 已完成并通过 closeout，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不授权 Step 5、Step 6、Step 7、FE、migration 或 release。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 4：same-answer stability and reference-answer replay |
| BACKLOG 授权入口 | AIFI-BE-012 |
| final_status | DONE / CLOSED |
| commit | `2e82dbfbc8f23d0c09cd784a94190dceecc36732` |
| commit subject | `feat(aifi): close step4 feedback stability` |
| closeout evidence | `.omo/evidence/plan/step4-ulw-loop-closeout.md` |
| review-work evidence | `.omo/evidence/step4-aifi-be-012-review-work-pass.md` |
| review-work result | PASS |
| 完成范围 | AC-001 同题同答稳定性；AC-003 参考答案回灌高分自洽；Step2 / Step3 回归不回退 |
| 明确不授权 | Step5 improvement trend、Step6 progress mastery、Step7 question generation / similarity interception、FE、migration、release、C-049 到 C-054 关闭 |

#### Step 4 覆盖范围

AIFI-BE-012 只覆盖 Step 4 的完成范围：

- same-answer stability。
- reference-answer replay。
- scoring normalization。
- 与上述三项直接相关的 tests/api。

AIFI-BE-012 不覆盖以下事项：

- Step5 improvement trend。
- Step6 progress mastery。
- Step7 question generation。
- FE、migration 或 release。

#### Deferred Guard

C-049 到 C-054 仍保持 `Deferred / Open Question`。

Step 4 / AIFI-BE-012 不得关闭或实现以下事项：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。

### 5.8 Step 5 / AIFI-BE-015 Closeout 状态登记

本节登记 `.omo/plans/plan.md` Step 5 的最终 closeout 状态。该状态只说明 improved-answer trend calibration 和 current effective feedback result consistency 已完成并通过 closeout，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不直接授权 Step 6 实现；Step 6 仍必须重新执行 scope lock。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 5：改进回答趋势与当前有效结果 |
| BACKLOG 授权入口 | AIFI-BE-015 |
| final_status | DONE / CLOSED |
| 是否新增 AIFI | YES，新增 AIFI-BE-015 |
| 未复用 AIFI-BE-010 原因 | AIFI-BE-010 只覆盖 effective feedback state / compatibility / selector 局部，并明确不授权 Step5 improvement trend implementation |
| Step4 依赖 commit | `2e82dbfbc8f23d0c09cd784a94190dceecc36732` |
| Step4 review-work | PASS |
| Step5 closeout commit | `ef95d4a9139d4c0f41593a6c9c57897d533aca0b` |
| Step5 closeout evidence | `.omo/evidence/plan/step5-implementation-closeout.md` |
| Step2 依赖状态 | AIFI-BE-010 已 DONE / CLOSED；只作为 current effective selector 兼容依赖，不承接 Step5 trend implementation |
| Step3 依赖状态 | AIFI-BE-011 已 DONE；只作为 fail-closed 兼容依赖，不承接 Step5 trend implementation |
| Step4 依赖状态 | AIFI-BE-012 已 DONE / CLOSED；只作为 same-answer stability / reference replay 兼容依赖，不承接 Step5 trend implementation |

#### Step 5 目标

- 改进回答后评分趋势应上升。
- current effective feedback result 不因历史失败态、pending、invalid 或旧结果回退。
- 与 Step2 effective feedback selector 兼容。
- 与 Step3 fail-closed validation 兼容。
- 与 Step4 same-answer stability / reference replay 兼容。

#### Step 5 允许范围

- `apps/api/app/application/polish/**` 中 feedback trend、effective feedback result、score delta、payload projection 相关文件。
- `apps/api/app/schemas/polish.py` 中与 Step5 结果兼容的 additive 字段。
- `apps/api/app/infrastructure/db/repositories/polish.py` 中 current effective result 读取/投影相关最小调整。
- `tests/api/test_polish_feedback_improvement_trend.py`。
- `tests/api/test_polish_effective_feedback_state.py`。
- `tests/api/test_polish_feedback_stability.py`。
- `tests/api/test_polish_feedback_failure_contract.py`。
- 必要的 `tests/api/test_polish_api.py` 中限定 Step5 effective result / trend consistency 的测试。

#### Step 5 禁止范围

- Step6 progress mastery。
- Step7 next-question generation / similarity interception。
- FE 改造。
- migration。
- release。
- 配置文件或依赖文件。
- 非 polish 后端模块。
- 关闭 C-049 到 C-054。

#### Acceptance Focus

- AC-002 improved answer trend。
- current effective result 与 latest valid feedback 一致。
- 不破坏 AC-001 同题同答稳定性。
- 不破坏 AC-003 参考答案回灌。
- 不破坏 Step3 fail-closed。

#### Derived Summary 语义

- `derived_improvement_summary`、`derived_remaining_gap_summary`、`derived_regression_summary` 只是由 score_delta / dimension_delta / loss point delta 派生的摘要。
- 这些摘要只服务 AC-002 improved answer trend 和 current effective result consistency。
- 这些摘要不得成为 Step5 新业务范围，不授权 Step6 progress mastery，不授权 Step7 next-question generation。

#### Deferred Guard

C-049 到 C-054 仍保持 `Deferred / Open Question`。Step 5 / AIFI-BE-015 不得关闭或实现以下事项：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。

### 5.9 Step 6 / AIFI-BE-013 Closeout 状态登记

本节登记 `.omo/plans/plan.md` Step 6 的 canonical BE closeout。该状态只说明 Step6 progress mastery 已完成并关闭，不改变 PRD 需求事实源，不关闭 C-049 到 C-054。Step7 / AIFI-BE-014 已在后续 closeout 中完成，本节不直接授权 Step8、FE、migration、release 或 C-049 / C-054 关闭。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 6：考察点进度、节点掌握度与手动完成状态 |
| canonical BACKLOG 授权入口 | AIFI-BE-013 |
| rejected drift ID | AIFI-BE-016 |
| AIFI-BE-013 是否 legacy | NO，AIFI-BE-013 是 active docs 中 Step6 canonical BE |
| AIFI-BE-016 裁决 | REJECTED；未进入 BACKLOG，未进入本文件 §5.4 映射，不得作为 Step6 scope lock、实现或测试入口 |
| Step5 依赖状态 | AIFI-BE-015 已 DONE / CLOSED；Step6 不得绕过 Step5 |
| final_status | DONE / CLOSED |
| Step6 implementation commit | `1bfa1cea0d213e01c00f20fda33971b68fac7996` |
| Step6 commit subject | `feat(aifi): finalize step6 progress mastery system` |
| Step6 closeout evidence | `.omo/evidence/plan/step6-implementation-closeout.md` |
| 完成范围 | `progress_mastery_tracking`；`score_evolution_tracking`；`longitudinal_feedback_summary`；`stable_user_state_projection` |
| 输出边界 | derived-only；只投影已存在 feedback / progress / score evidence，不生成下一题、不生成学习路径、不驱动 tutoring |
| 明确未实现 | Step7 question generation；next_question_recommendation；adaptive_learning_path；auto_tutoring；trend_autopilot |
| 下一步授权 | Step7 / AIFI-BE-014 已完成 closeout；本节不授权 Step8、FE、migration、release 或 C-049 / C-054 关闭 |

#### canonical_be_mapping.json

```json
{
  "step5": "AIFI-BE-015",
  "step6": "AIFI-BE-013",
  "conflict_candidates": ["AIFI-BE-013", "AIFI-BE-016"],
  "resolution": {
    "AIFI-BE-013": "ACCEPTED_CANONICAL",
    "AIFI-BE-016": "REJECTED_NON_ACTIVE_DRIFT"
  },
  "conflicts_resolved": true
}
```

#### conflict_resolution_report.md

- AIFI-BE-013：ACCEPTED / DONE，作为 Step6 canonical BE，已由 commit `1bfa1cea0d213e01c00f20fda33971b68fac7996` 完成 progress mastery、score evolution、longitudinal feedback summary 和 stable user state projection。
- AIFI-BE-016：REJECTED，因不在 `REQUIREMENT_TRACEABILITY.md` §5.4 映射、不在 `BACKLOG.md` 任务表、不在当前 active docs 体系中登记。
- AIFI-BE-015：DONE / CLOSED，作为 Step5 canonical BE，Step6 依赖已满足。
- C-049 到 C-054：仍保持 Deferred / Open Question；本节不关闭这些 C-ID。

#### Step6 输出边界

- Step6 输出为 derived-only，只用于进展、掌握度、评分演进、长期反馈摘要和稳定用户状态投影。
- Step6 不实现 Step7 question generation。
- Step6 不实现 next_question_recommendation。
- Step6 不实现 adaptive_learning_path。
- Step6 不实现 auto_tutoring。
- Step6 不实现 trend_autopilot。

### 5.10 Step 7 / AIFI-BE-014 Closeout 状态登记

本节登记 `.omo/plans/plan.md` Step 7 / `AIFI-BE-014` 的最终 closeout 状态。该状态只说明受 policy signature（策略签名）约束的同节点追问、同节点下一题候选选择、next action / response contract（下一步动作 / 响应契约）和无签名 fail-closed（失败关闭）已完成，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不授权 Step 8、FE、migration、release 或泛化 question generation。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 7：受策略签名约束的同节点追问 / 同节点下一题候选契约 |
| BACKLOG 授权入口 | AIFI-BE-014 |
| final_status | DONE / CLOSED |
| docs authorization commit | `a5ae5cd42567b78362bacf04c43e4a0994fb2774` |
| implementation commit | `bad29f58389ddd1a0bb440af31c03139eee633f7` |
| implementation commit subject | `feat(aifi): close step7 follow-up policy` |
| active dependency | AIFI-BE-013 已 DONE / CLOSED，只作为 read-only dependency |
| closed dependency | AIFI-BE-015 已 DONE / CLOSED |
| rejected drift ID | AIFI-BE-016 仍为 REJECTED，不得复活 |
| prior boundary lock | `step7_scope_lock.json` 是 boundary lock，`mode=scope_lock_only`，不等于 implementation authorization |
| old blocked implementation lock | `.omo/evidence/plan/step7-implementation-scope-lock-blocked.json` 是旧 BLOCKED 结果，不得作为授权依据 |
| authorized implementation lock | Step7 implementation scope lock 曾生成 `execution_mode=AUTHORIZED`、`implementation_allowed=true`、`active_aifi=AIFI-BE-014`；根目录 JSON 已转存为 ignored evidence：`.omo/evidence/plan/step7-implementation-scope-lock-authorized.json` |
| 完成范围 | `follow_up_intent_classification`；`same_node_follow_up_contract`；`same_node_next_question_candidate_selection`；`next_question_response_contract`；`policy_signed_next_action`；`no_auto_generation_without_policy_signature` |
| 验证摘要 | focused Step7 API tests：`9 passed in 4.53s`；wide regression：`127 passed in 13.04s`；`py_compile` 通过；`git diff --check` 通过；forbidden path diff 为空 |
| 下一步授权 | 本节不授权 Step 8、FE、migration、release、泛化 question generation 或 C-049 / C-054 关闭 |

#### Step7 completed capabilities

- `follow_up_intent_classification`
- `same_node_follow_up_contract`
- `same_node_next_question_candidate_selection`
- `next_question_response_contract`
- `policy_signed_next_action`
- `no_auto_generation_without_policy_signature`

#### Step7 implementation result

- authorized feedback next-question metadata 会写入 `policy_signed_next_action`、`follow_up_intent_classification`、`same_node_follow_up_contract`、`same_node_next_question_contract`、`next_question_response_contract`。
- trusted metadata 校验会在缺失 policy signature、consumed grant 不满足、contract id 不匹配或 policy signature 不匹配时 fail-closed，并返回 `validation_failed`。
- API schema 未扩大；前端仍不能通过请求体覆盖 `selected_progress_node_ref`。
- Step6 只作为 read-only dependency；本 closeout 不重写 Step6 progress mastery、manual completion、score evolution、longitudinal feedback summary 或 stable user state projection。

#### Step7 forbidden capabilities

- `adaptive_learning_path`
- `auto_tutoring`
- `curriculum_generation`
- `open_ended_question_generation`
- `cross_node_uncontrolled_question_generation`
- `uncontrolled_question_generation`
- `step6_mastery_driven_autopilot`
- `rewriting_step6_progress_mastery`
- `rewriting_step5_improvement_trend`
- `rewriting_step4_replay_stability`
- `rewriting_step3_fail_closed`
- `rewriting_step2_effective_selector`

#### Deferred Guard

C-049 到 C-054 仍保持 `Deferred / Open Question`。AIFI-BE-014 已完成受控 contract / candidate selection / policy-signed next action，但不得定义 C-049 相似度阈值，不得选择或关闭 C-054 的最终下一题算法。

### 5.11 Step 8 / AIFI-BE-017 Closeout 状态登记

本节登记 `.omo/plans/plan.md` Step 8 的 active-docs unblock、implementation scope lock 和 backend implementation closeout 结果。该状态只说明 Step8 backend API schema and response envelope boundary 已按 AIFI-BE-017 完成，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不授权 Step9 implementation。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 8：API schema 与 response envelope 汇总 |
| BACKLOG 授权入口 | AIFI-BE-017 |
| current_status | DONE / CLOSED |
| initial scope lock evidence | `.omo/evidence/plan/step8-scope-lock.md` |
| active-docs unblock evidence | `.omo/evidence/plan/step8-active-docs-unblock.md` |
| implementation scope lock evidence | `.omo/evidence/plan/step8-implementation-scope-lock.md` |
| implementation closeout evidence | `.omo/evidence/plan/step8-implementation-closeout.md` |
| implementation commit | `23990da79118d200024735f193ba9b5d4499d4a2` |
| implementation_allowed | completed under Step8 implementation scope lock；本节关闭后不继续授权新的 implementation |
| completed response-only fields | `policy_signed_next_action`；`follow_up_intent_classification`；`same_node_follow_up_contract`；`same_node_next_question_contract`；`next_question_response_contract` |
| backend boundary | 上述字段仅进入 response projection / response schema；未进入 `FeedbackFinalPayload` required-final-field 契约源 |
| verification | focused Step8 tests：`3 passed in 1.63s`；Step8 / Step2-7 / API canary bundle：`279 passed in 26.48s`；full `tests/api` canary：`1052 passed, 1 skipped, 1 warning in 108.92s`；supplemental focused test commit：`d79a91555ca2ff578f77a84ac6e3740fa2209d8e`；测试通过时伴随 Windows pytest 临时目录清理 warnings；`py_compile` 通过；`git diff --check` 通过；forbidden path diff 为空 |
| Step2 dependency | AIFI-BE-010 已 DONE / CLOSED，只作为 effective feedback state / schema compatibility 依赖 |
| Step3 dependency | AIFI-BE-011 已 DONE，只作为 failure envelope / schema compatibility 依赖 |
| Step4 dependency | AIFI-BE-012 已 DONE / CLOSED，只作为 same-answer stability / reference-answer replay contract 依赖 |
| Step5 dependency | AIFI-BE-015 已 DONE / CLOSED，只作为 improved-answer trend / current effective result contract 依赖 |
| Step6 dependency | AIFI-BE-013 已 DONE / CLOSED，只作为 progress mastery / stable user state projection contract 依赖 |
| Step7 dependency | AIFI-BE-014 已 DONE / CLOSED，只作为 policy-signed next action / follow-up contract 依赖 |
| 下一步授权 | 本节不授权 Step9 implementation；Step9 必须重新走 BACKLOG / scope lock 授权 |

#### Step8 allowed capabilities

- `api_response_envelope_consolidation`
- `feedback_payload_schema_alignment`
- `progress_payload_schema_alignment`
- `follow_up_payload_schema_alignment`
- `signed_next_action_schema_alignment`
- `effective_feedback_response_contract`
- `failure_response_contract`
- `backwards_compatible_api_projection`
- `backend_contract_tests`

#### Step8 forbidden capabilities

- FE view model。
- FE rendering。
- FE workbench interaction。
- integration QA。
- release。
- migration。
- config changes。
- dependency changes。
- new scoring logic。
- new fail-closed logic。
- new replay logic。
- new trend logic。
- new progress mastery logic。
- new follow-up policy logic。
- new question generation。
- Step9 / Step10 / Step11 / Step12 behavior。

#### Deferred Guard

C-049 到 C-054 仍保持 `Deferred / Open Question`。AIFI-BE-017 不关闭或实现以下事项：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。

### 5.12 Step 9 / AIFI-FE-003 当前有效文档解锁状态登记

本节登记 `.omo/plans/plan.md` Step 9 的 active-docs unblock（当前有效文档解锁）、implementation scope lock（实现范围锁）、implementation（实现）和 closeout（收口）状态。该状态只说明 AIFI-FE-003 的前端 view model（视图模型）边界已完成，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不授权 Step10、Step11、Step12、backend（后端）、migration（迁移）、release（发布）或页面交互实现。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 9：FE types（前端类型）、view model（视图模型）与 failure folding（失败折叠） |
| BACKLOG 授权入口 | AIFI-FE-003 |
| 当前状态 | DONE / CLOSED |
| 初始范围锁证据 | `.omo/evidence/plan/step9-scope-lock.md` |
| 当前有效文档解锁证据 | `.omo/evidence/plan/step9-active-docs-unblock.md` |
| 实现范围锁证据 | `.omo/evidence/plan/step9-implementation-scope-lock.md` |
| 实现收口证据 | `.omo/evidence/plan/step9-implementation-closeout.md` |
| 实现审查证据 | `.omo/evidence/plan/step9-implementation-review-work.md` |
| 实现提交 | `7f5f889` |
| Step8 依赖 | AIFI-BE-017 已 DONE / CLOSED，只作为 backend response schema / envelope（后端响应结构 / 信封）来源，不授权 Step9 implementation（实现） |
| 硬依赖 | AIFI-BE-010、AIFI-BE-011、AIFI-BE-014、AIFI-QA-004 |
| 参考依赖 | AIFI-FE-002 保持 NOT_STARTED，但在本 Step9 view model contract（视图模型契约）范围内只作参考上下文，非硬依赖 |
| 完成验证 | `npm.cmd run web:test` 通过；runtime JS contract（运行时 JS 契约）断言通过；Step2-Step8 backend canary（后端金丝雀测试）为 `91 passed in 3.51s`；implementation review-work（实现审查）PASS；forbidden path diff（禁止路径差异）为空 |
| 下一步授权 | 本节不授权 Step10、Step11、Step12、backend（后端）、migration（迁移）、release（发布）或页面交互实现；如需继续，必须按 BACKLOG 重新走 AIFI-FE-004 / AIFI-QA-005 / AIFI-REL-009 范围锁 |

#### Step9 范围锁候选能力

- `frontend_type_alignment`
- `frontend_view_model_mapping`
- `feedback_view_model_projection`
- `progress_view_model_projection`
- `follow_up_view_model_projection`
- `signed_next_action_view_model_projection`
- `failure_state_view_model_projection`
- `pending_state_view_model_projection`
- `partial_state_view_model_projection`
- `backwards_compatible_frontend_contract_tests`

#### Step9 禁止能力

- `InterviewPage.tsx` 页面交互、刷新恢复或页面 smoke。
- backend（后端）业务逻辑、API 行为、schema source（结构来源）、migration（迁移）或数据模型变更。
- config / dependency / build pipeline（配置 / 依赖 / 构建流水线）改动。
- release docs / runbook / QA evidence closeout（发布文档 / 运行手册 / QA 证据收口）。
- Step10 / Step11 / Step12 behavior。
- C-049 到 C-054 关闭或最终决策。

#### Deferred Guard（后置护栏）

C-049 到 C-054 仍保持 `Deferred / Open Question`。AIFI-FE-003 只可承接前端 view model（视图模型）、失败折叠、response projection（响应投影）和兼容测试，不关闭或实现以下事项：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。

### 5.13 Step 10 / AIFI-FE-004 Final Closeout 状态登记

本节登记 `.omo/plans/plan.md` Step 10 / `AIFI-FE-004` 的最终 closeout（收口）状态。该状态只说明 Step10 面试工作台页面层反馈交互和刷新恢复已完成，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不授权 Step11 integration（集成）/ real page QA（真实页面验收）、Step12 release（发布）、backend（后端）语义、migration（迁移）、config（配置）或 dependency（依赖）改动。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 10：FE workbench interaction（前端工作台交互）与 state recovery（状态恢复） |
| BACKLOG 授权入口 | AIFI-FE-004 |
| final_status | DONE / CLOSED（仅 Step10 implementation closeout，不代表 Step11 integration / real page QA 已完成） |
| docs authorization commit | `612eef81e01cd1487c54cdc5655e9c64eb2c645e` |
| implementation commit | `8aa4d01bcf36b4929d477a76582848f7d6545d2d` |
| 初始范围锁证据 | `.omo/evidence/plan/step10-scope-lock.md` |
| 当前有效文档解锁证据 | `.omo/evidence/plan/step10-active-docs-unblock.md` |
| implementation scope lock 证据 | `.omo/evidence/plan/step10-implementation-scope-lock.md` |
| implementation review-work | PASS；证据为 `.omo/evidence/plan/step10-implementation-review-work.md` |
| Step9 依赖 | AIFI-FE-003 已 DONE / CLOSED，作为 Step9 view model（视图模型）来源，不授权改写 `apps/web/src/entities/polish/**` contract（契约） |
| 硬依赖 | AIFI-FE-003、AIFI-BE-010、AIFI-BE-011、AIFI-BE-012、AIFI-BE-015、AIFI-BE-013、AIFI-BE-014、AIFI-QA-004 |
| 下一步授权 | 本节不授权 Step11 implementation（实现）、Step11 real page QA（真实页面验收）、Step12 release（发布）或 rollback（回滚）；后续必须重新走 BACKLOG / scope lock |

#### Step10 已完成能力

- `workbench_feedback_state_binding`
- `workbench_feedback_refresh_recovery`
- `workbench_pending_partial_failure_display_flow`
- `workbench_signed_next_action_display`
- `workbench_follow_up_action_surface`
- `workbench_view_model_consumption`
- `frontend_state_restore_after_refresh`
- `frontend_interaction_contract_tests`

完成修改路径：

- `apps/web/src/pages/interview/InterviewPage.tsx`
- `apps/web/src/pages/interview/InterviewPage.test.ts`
- `tests/web/test_interview_actions.py`

验证结果：

- `npm.cmd run web:test`: PASS
- `python -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q`: PASS，`14 passed in 8.11s`
- backend focused regression（后端聚焦回归）：PASS，`77 passed in 4.68s`
- `npm.cmd run web:build`: PASS，保留既有 large chunk warning
- `git diff --check`: PASS，仅 LF -> CRLF warning

limited smoke（有限烟测）结果：

- `node scripts/qa/polish-feedback-frontend-smoke.mjs --scenario seeded-feedback-states --evidence-dir .omo/evidence/step10-polish-feedback-frontend-smoke` 失败于 `failed answer should expose generation_failed payload`。
- 该结果保留为 Step10 residual risk（残余风险），不得写成 Step11 integration（集成）/ real page QA（真实页面验收）PASS。

#### Step10 禁止能力

- backend（后端）scoring、fail-closed、replay / stability、trend、progress mastery、follow-up policy、response envelope 或 API contract semantic changes（语义变更）。
- new question generation（新题生成）、adaptive learning path（自适应学习路径）、auto tutoring（自动辅导）或 open-ended generation（开放式生成）。
- Step11 integration（集成）/ real page QA（真实页面验收）。
- Step12 release（发布）/ rollback（回滚）。
- migration（迁移）、config（配置）、dependency（依赖）或 build pipeline（构建流水线）改动。
- C-049 到 C-054 关闭或最终决策。

#### Deferred Guard（后置护栏）

C-049 到 C-054 仍保持 `Deferred / Open Question`。AIFI-FE-004 只可承接页面行为和恢复护栏，不关闭或实现以下事项：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。

### 5.14 Step 11 / AIFI-QA-005 当前有效文档解锁与收口状态登记

本节登记 `.omo/plans/plan.md` Step 11 的 active-docs unblock（当前有效文档解锁）、implementation scope lock（实现范围锁）和 final closeout（最终收口）状态。该状态只说明 Step11 integration（集成）/ real page QA（真实页面验收）已完成，不改变 PRD 需求事实源，不关闭 C-049 到 C-054，也不授权 Step12 release（发布）、rollback（回滚）、migration（迁移）、config（配置）或 dependency（依赖）改动。

| 项 | 内容 |
|---|---|
| plan.md Step | Step 11：integration（集成）与真实页面 QA |
| BACKLOG 授权入口 | AIFI-QA-005 |
| 当前状态 | DONE / CLOSED；implementation commits `9a97458`、`bd3c861` |
| 初始范围锁证据 | `.omo/evidence/plan/step11-scope-lock.md`，结果为 `execution_mode=BLOCKED` |
| implementation scope lock | `.omo/evidence/plan/step11-implementation-scope-lock.md`，结果为 `execution_mode=AUTHORIZED`、`implementation_allowed=true` |
| 当前有效文档解锁意图 | 补齐 Step11 的唯一 active BACKLOG 授权入口；不修改 `.omo/plans/plan.md` |
| 硬依赖 | AIFI-QA-004；AIFI-BE-010；AIFI-BE-011；AIFI-BE-012；AIFI-BE-015；AIFI-BE-013；AIFI-BE-014；AIFI-BE-017；AIFI-FE-003；AIFI-FE-004 |
| Step10 residual risk | 已复现并修复；red evidence 为 `.omo/evidence/step11-polish-feedback-frontend-smoke-red`，green evidence 为 `.omo/evidence/step11-polish-feedback-frontend-smoke-green` |
| 真实页面 QA | `.omo/evidence/step11-real-page-qa/action-log.json`；截图为 `.omo/evidence/step11-real-page-qa/mobile-375.png`、`tablet-768.png`、`desktop-1280.png` |
| enhanced 真实页面 QA | `.omo/evidence/step11-real-page-qa-enhanced/action-log.json`；三视口截图覆盖 partial、refresh recovery、trusted signed action 和 untrusted action |
| review-work | `.omo/evidence/plan/step11-implementation-review-work.md`，API contract、backend test、real page QA、governance scope、security / privacy 均为 PASS |
| 下一步授权 | 只允许进入 Step12 / AIFI-REL-009 的 release docs / runbook / QA evidence docs scope lock；不得直接执行 release、rollback、migration、config、dependency changes、业务代码或测试代码 |

#### Step11 候选能力

- `backend_frontend_contract_integration`
- `real_page_feedback_flow_QA`
- `real_page_refresh_recovery_QA`
- `signed_next_action_display_QA`
- `pending_partial_failure_display_QA`
- `follow_up_surface_QA`
- `integration_regression_matrix`
- `smoke_failure_reproduction_and_triage`
- `no_release_gate`

#### Step11 候选允许路径

最终允许路径以 Step11 implementation scope lock 的 `execution_mode=AUTHORIZED` 证据为准。候选路径仅包括：

- `apps/web/src/pages/interview/InterviewPage.tsx`
- `apps/web/src/pages/interview/InterviewPage.test.ts`
- `tests/web/test_interview_actions.py`
- `scripts/qa/polish-feedback-frontend-smoke.mjs`
- `tests/api/test_polish_api.py`
- `tests/api/test_polish_feedback_*.py`
- `apps/api/app/api/v1/polish.py`
- `apps/api/app/application/polish/**`
- `apps/api/app/schemas/polish.py`

后端候选路径只允许 response projection（响应投影）、failure envelope（失败响应信封）或 integration compatibility（集成兼容）最小修复；不得新增评分、策略、题目生成、迁移、配置或依赖。

#### Step11 禁止能力

- release（发布）、rollback（回滚）、production rollout（生产发布）。
- deployment config（部署配置）、migration（迁移）、dependency changes（依赖变更）。
- new backend scoring / policy logic（新的后端评分 / 策略逻辑）。
- new frontend feature beyond QA fix（超出 QA 修复的新前端功能）。
- new question generation（新题生成）、adaptive learning path（自适应学习路径）、auto tutoring（自动辅导）。
- Step12 release behavior（Step12 发布行为）。
- 关闭 C-049 到 C-054。
- 把 Step10 residual smoke failure 写成 Step11 PASS。

#### Step11 required verification

- 重新执行 Step11 implementation scope lock，并得到 `execution_mode=AUTHORIZED`、`implementation_allowed=true`。
- 运行或复现 Step10 limited smoke 命令，记录失败原因、修复结果或分流结论。
- 启动本地 app，通过真实浏览器驱动 interview/workbench 页面，保存 screenshot（截图）或 action log（操作日志）证据。
- 至少运行 `npm.cmd run web:test`、`python -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q`、focused backend regression（聚焦后端回归）、`npm.cmd run web:build` 和 `git diff --check`。
- implementation review-work 必须 PASS，且 safe_to_commit=yes 后才允许 implementation commit。

#### Deferred Guard（后置护栏）

C-049 到 C-054 仍保持 `Deferred / Open Question`。AIFI-QA-005 只可承接 Step11 integration QA（集成质量验证）、真实页面 QA 和必要最小修复，不关闭或实现以下事项：

- C-049：相似度阈值。
- C-050：考察点与题目绑定模型。
- C-051：失败记录折叠最终样式。
- C-052：错误枚举最终映射。
- C-053：状态提示去重与刷新恢复最终状态机。
- C-054：生成下一题具体算法。

#### Step11 final closeout

本节只关闭 Step11 / AIFI-QA-005 的 integration QA（集成质量验证）和 real page QA（真实页面验收）范围，不关闭 Step12 / AIFI-REL-009，不进入 release（发布）或 rollback（回滚）。

| 项 | 内容 |
|---|---|
| final_status | DONE / CLOSED |
| implementation commits | `9a97458`、`bd3c861` |
| red smoke | `node scripts/qa/polish-feedback-frontend-smoke.mjs --scenario seeded-feedback-states --evidence-dir .omo/evidence/step11-polish-feedback-frontend-smoke-red` 复现 `failed answer should expose generation_failed payload` |
| green smoke | `node scripts/qa/polish-feedback-frontend-smoke.mjs --scenario seeded-feedback-states --evidence-dir .omo/evidence/step11-polish-feedback-frontend-smoke-green` 通过，pending / generated / generation_failed 样本均返回 |
| real page QA | `.omo/evidence/step11-real-page-qa/action-log.json` 和三视口截图；generated / pending / failure / follow-up surface / next action 均为 true |
| enhanced real page QA | `.omo/evidence/step11-real-page-qa-enhanced/action-log.json` 和九张三视口截图；partial / refresh recovery / trusted signed action / untrusted action 均为 true |
| focused tests | `npm.cmd run web:test`；`python -m pytest -p no:cacheprovider tests/web/test_interview_actions.py -q`；focused backend regression `81 passed`；`npm.cmd run web:build`；`git diff --check` |
| non-blocking risks | mobile 375 截图主要依赖 DOM 文本检查；action log 有 404 console error 和 Ant Design deprecated warning；Vite build 保留 chunk size warning；LSP diagnostics MCP 返回 `Transport closed` |
| 不授权 | Step12 release / rollback；migration；config；dependency changes；新评分 / 策略逻辑；新题生成；关闭 C-049 到 C-054 |


## 6. F1.3 结论

F1.2 已将 PRD 从“大能力清单”补全为产品需求规格说明书。F1.3 已将 PRD 中所有 UNKNOWN 绑定到分类、影响范围、当前处理策略、必须关闭阶段、承接 AIFI-* 任务、关闭后写入的目标文档和关闭标准。F1.4 已将 0-100 产品展示刻度、MVP 不做文件导出仅支持复制、通过概率不承诺精确实现同步到 PRD 和追踪关系。F1.5 已修正业务对象模型：项目经历归入简历模块，历史“项目打磨”归入打磨模式中的项目经历表达主题，历史“真实项目复盘”归入面试复盘并区分模拟面试复盘和真实面试复盘。F1.6 已关闭 OQ-F1-006，冻结岗位 / JD 仅支持手动录入，历史外部文件解析或剪贴板批量生成岗位信息的诉求按产品原因后置，不作为 MVP active 能力。当前无 `F1_PRODUCT_BLOCKING`；`F2_UX_BLOCKING` 由 AIFI-UX-002 在 `UX_SPEC.md` 关闭；`F4_TECH_DESIGN` 由 AIFI-ARCH-002 及 F4 设计任务关闭；影响验收的剩余项由 AIFI-QA-002 在 F7 验证。
