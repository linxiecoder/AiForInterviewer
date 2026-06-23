---
title: BACKLOG
type: delivery-backlog
status: active-f1
owner: 项目交付
source_report: archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md
permalink: ai-for-interviewer/docs/03-implementation/backlog-1
---

# BACKLOG

本文件是唯一任务入口。所有任务必须使用 `AIFI-*` 编号；优先级只使用 `MUST`、`SHOULD`、`COULD`、`LATER`；阶段只引用 `F0` 至 `F8`。本文件不设置批次、波次或发布批次字段，任务承接只通过阶段、里程碑、优先级、依赖、验收和状态表达。

## 1. Backlog

PR1.6 blocker note：`AIFI-BE-004` 已由 `docs/02-design/PRESSURE_MODE_SPEC.md` 接受并关闭 Pressure Mode blocker，`AIFI-ARCH-007` 已由 `docs/02-design/SKILL_MODEL_SPEC.md` 接受并关闭 Skill Model blocker，`AIFI-PROMPT-002` 已由 `docs/02-design/PROMPT_ASSET_SPEC.md` / `docs/02-design/PROMPT_EVALUATION_SPEC.md` 接受并关闭 Prompt Asset / Evaluation blocker，`AIFI-ARCH-008` 已同步为 `ACCEPTED` 并关闭 AI/Core directory blocker；`AIFI-BE-005` / `AIFI-BE-006` 将 PR2 readiness 更新为 `CONDITIONAL GO`。原 PR2 implementation planning 目录已去层并删除；后续 PR2 code implementation 必须重新以 active design docs、ADR-0005、`docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md` 中已迁移的实现证据和当轮 scope lock 为准，不得复用旧 refactor 目录作为 executable source of truth。

| 任务 ID | 阶段 | 里程碑 | 优先级 | 标题 | 范围 | 产物 | 依赖 | 状态 |
|---|---|---|---|---|---|---|---|---|
| AIFI-DOC-001 | F0 | M0 | MUST | 建立目标文档索引 | 新建/改写 `DOCS_INDEX.md`，登记唯一有效文档体系 | `docs/00-governance/DOCS_INDEX.md` | F0 审计 | DONE |
| AIFI-DOC-002 | F0 | M0 | MUST | 合并归档台账 | 新建 `archive/MANIFEST.md`，合并旧归档索引与台账 | `archive/MANIFEST.md` | `DOCS_INDEX.md` | DONE |
| AIFI-DOC-003 | F0 | M0 | MUST | 废弃旧 active 入口 | 将旧 planning/task/module/state 文档迁入 archive 并登记替代路径 | README、AGENTS、`archive/MANIFEST.md` | F0.1 归档 | DONE |
| AIFI-DOC-004 | F0 | M0 | MUST | 清理重复模板文档 | 旧模板和旧治理文档转为历史来源 | `archive/2026-05-doc-consolidation/legacy/` | F0.1 归档 | DONE |
| AIFI-DOC-005 | F0 | M0 | SHOULD | 固化 AI 协作治理规则 | 在 Claude Code / Codex / ChatGPT 协作入口中固化 Prompt Markdown 可复制、中文、转义、安全读取、最小审计、三轮推进、第三轮后不重复全面审计、ChatGPT 优先自行最小审查、Scope 外本地改动只报告不阻塞等规则 | `docs/00-governance/AI_WORKFLOW.md`、`docs/00-governance/DOCS_GOVERNANCE.md`、`docs/04-decisions/ADR-0004-ai-collaboration-governance.md`、`docs/00-governance/DOCS_INDEX.md` | AIFI-DOC-001、ADR-0001、ADR-0002 | DONE |
| AIFI-PROD-001 | F1 | M1 | MUST | 编写并冻结 MVP PRD | 建立唯一产品需求事实源，覆盖产品定位、目标、角色、业务对象、核心需求、核心业务数据流、状态异常、验收标准和非目标 | `docs/01-product/PRD.md` | AIFI-DOC-001 | DONE |
| AIFI-PROD-002 | F1 | M1 | MUST | 完成历史需求继承处理 | 将历史有效需求标记为 MERGED_TO_PRD / PARTIAL / DEFERRED / REJECTED / UNKNOWN，并登记 F1 覆盖矩阵 | `docs/01-product/REQUIREMENT_TRACEABILITY.md` | AIFI-PROD-001 | DONE |
| AIFI-PROD-003 | F1 | M1 | MUST | 定义 MVP 用户角色与权限边界 | 冻结求职者 / 面试准备用户、管理员/内容维护者、项目维护者和最小管理边界 | `docs/01-product/PRD.md` §3 | AIFI-PROD-001 | DONE |
| AIFI-PROD-004 | F1 | M1 | MUST | 定义核心面试双模式 | 冻结模拟面试必须拆分为打磨模式和压力面模式；定义进展树状态、同一道题多轮打磨、详细点评、打分、失分原因、参考回答、参考回答与失分点对应、考点解析、技术原理扩展、打磨模式暂停与恢复，以及压力面连续追问和真实节奏边界 | `docs/01-product/PRD.md` §6.8-§6.11、§7-§8 | AIFI-PROD-001 | DONE |
| AIFI-PROD-005 | F1 | M1 | MUST | 定义评分、面试报告、复盘和薄弱项需求 | 冻结 0-100 产品展示刻度、可解释评分、面试报告、报告内容复制、面试复盘、薄弱项提炼、薄弱项回流、未生成状态提示、通过倾向 / 风险提示目标效果，以及报告和复盘进入打磨模式、压力面模式、资产库和模拟面试输入的边界；不冻结具体评分公式或精确通过概率 | `docs/01-product/PRD.md` §5.5、§6.12-§6.14、§7-§8 | AIFI-PROD-001 | DONE |
| AIFI-PROD-006 | F1 | M1 | MUST | 定义 MVP 非目标范围 | 冻结多团队、多租户、语音、视频、ATS、商业化、高级治理、文件导出、精确通过概率等非目标范围，并明确 PRD 核心需求不得降级为非目标 | `docs/01-product/PRD.md` §9 | AIFI-PROD-001 | DONE |
| AIFI-PROD-007 | F1 | M1 | MUST | 冻结打磨模式与面试复盘关键业务数据流 | 定义简历中的项目经历模块、打磨模式多主题、面试复盘、资产库沉淀、资产驱动模拟面试输入、反馈反哺打磨模式，以及这些数据流不构成交付批次、阶段体系或唯一产品闭环 | `docs/01-product/PRD.md` §5.2-§5.6、§6.5-§6.8、§8；`docs/01-product/REQUIREMENT_TRACEABILITY.md` §2-§5 | AIFI-PROD-001 | DONE |
| AIFI-PROD-008 | F1 | M1 | MUST | 定义简历边界与岗位匹配度分析 | 定义简历边界、简历中的项目经历模块、岗位 / JD 手动录入、岗位 / JD 与简历绑定、岗位匹配度分析、匹配度打分、匹配点、不匹配点、加强点，以及岗位匹配分析如何提炼薄弱项并进入打磨模式、压力面模式、面试复盘、资产库和训练建议 | `docs/01-product/PRD.md` §6.1-§6.5；`docs/01-product/REQUIREMENT_TRACEABILITY.md` §2-§5 | AIFI-PROD-001 | DONE |
| AIFI-PROD-009 | F1 | M1 | MUST | 完成 PRD 规格化补全 | 将 PRD 从能力清单补全为产品需求规格说明书，覆盖用户故事、用户任务、业务对象、业务数据流、功能逻辑、输入 / 输出、场景级规格、状态流转、异常状态、规则约束、验收标准、UNKNOWN 和非目标范围 | `docs/01-product/PRD.md`、`docs/01-product/REQUIREMENT_TRACEABILITY.md` | AIFI-PROD-001、AIFI-PROD-002 | DONE |
| AIFI-PROD-010 | F1 | M1 | MUST | 补强 UNKNOWN 收敛机制 | 将 PRD 中全部 UNKNOWN 绑定分类、影响范围、处理策略、关闭阶段、承接任务、目标文档和关闭标准，并同步追踪、任务和阶段退出标准；OQ-F1-006 已在 F1 关闭，岗位 / JD 仅支持手动录入；不创建新 UNKNOWN 文档 | `docs/01-product/PRD.md` §10、`docs/01-product/REQUIREMENT_TRACEABILITY.md` §4 | AIFI-PROD-009 | DONE |
| AIFI-UX-001 | F2 | M2 | MUST | 准备 F2 低保真设计输入 | 已创建 `docs/02-design/UX_SPEC.md`；基于 PRD 的用户故事、核心业务数据流、功能逻辑、输入 / 输出、状态异常和验收标准完成低保真 UX 规范；已按最新产品交互口径修正简历、岗位、模拟面试、面试复盘、薄弱项场景，覆盖简历 Markdown 编辑、岗位手动录入表单、岗位详情模块化展示、模拟面试列表与详情、面试报告无一级入口、面试复盘列表与新增复盘、薄弱项多选发起打磨模式、资产库、内容沉淀确认和低置信度校对；本轮结构性返修已补充列表主态 / 抽屉态拆分、状态 Frame 不遮挡主体、表格最大承载、分页条数选择、操作列图标、表头筛选下拉扩展区、打磨 / 压力面工作台四区布局、用户设置入口、发起模拟面试抽屉或弹窗、新增面试复盘抽屉或弹窗、薄弱项多选自动带出和内容沉淀确认；本轮细节返修已补充操作列图标基础态清晰、无双层文字 / 字母、分页每页条数以下拉方式表达、表头筛选 / 排序图标化、用户区包含头像、角色和设置入口；本轮组件基线返修已建立 F2 低保真组件基线，并要求 Figma 页面按组件基线统一；本轮质量返修已要求 F2 低保真组件基线不得出现重叠、溢出和越界，进展树已按多维进展模型修正，分页、操作列、抽屉和表格尺寸比例已统一；本轮人工可读性返修已补充无文字溢出、无图标越界、无说明遮挡主体、无组件互相重叠、应用壳用户区布局稳定、进展树节点与说明不重叠、打磨模式回答后决策闭环和进展树任意节点生成题目流程；本轮清理重建已补充不允许 overlay 修正、旧问题节点必须删除、组件区和页面引用必须一致、Figma 必须通过人工可读性检查；本轮组件基线精修已补充 F2 低保真组件基线达到可评审线框稿质量、组件区和页面引用一致、打磨模式反馈卡片和下一步建议固定区完成、聊天窗口滚动与反馈卡片折叠规则完成；本轮质量闸门修复及继续返修复核已补充用户设置抽屉内容完整、抽屉态底层列表可读、组件区与页面引用关键尺寸一致、列表承载密度与分页语义一致、工作台反馈卡片无重叠、备份 Page 有效或明确风险；人工调整后的 Figma active Page 已确认组件基线、表格、分页、抽屉、进展树、模拟面试聊天工作台、反馈卡片、下一步建议固定区、用户区和状态 Frame 的越线、重叠、嵌套、组件引用不一致问题关闭；本轮同步已补充文本 / 视频 / 音频切换图标化、视频 / 音频置灰、置灰入口“暂未开放”提示、多维进展树状态图例、节点选中、右键菜单和节点生成题目流程；组件区和页面引用需保持一致；表格、分页、操作列、筛选、排序、抽屉、状态、用户区、聊天工作台均复用低保真组件基线；每个核心功能都具备布局、流程、交互、状态和 Figma 交付要求，可直接指导 Figma 低保真；已在 Figma Page `AiForInterviewer - F2 Low Fidelity` 重新落图并由人工接受；未新增页面代号体系，未设计精确通过概率展示 | `docs/02-design/UX_SPEC.md` | F1 完成 | DONE |
| AIFI-UX-002 | F2 | M2 | MUST | 关闭 F2 UX-blocking UNKNOWN | 已在 `docs/02-design/UX_SPEC.md` 中关闭所有 `F2_UX_BLOCKING` 和必须在 F2 确认的 `HUMAN_CONFIRMATION`；低保真交互不再依赖分散表格，功能场景能直接指导 Figma；本轮结构性返修已重新审视 OQ-F1-035，将低保真 Frame 建议命名为内容沉淀确认抽屉态，并明确产品目的、目标集合、目标级状态、用户确认、编辑、跳过和失败重试；已要求列表 / 抽屉拆分为主态与抽屉态，状态页不遮挡主体，工作台按四区聊天窗口结构重画；覆盖多简历多岗位绑定、岗位状态、岗位手动录入表单、打磨主题完成、内容沉淀确认、低置信度校对、资产更新确认、缺失增强输入提示、压力面节奏、进展树展示层级、报告复盘展示和报告复制反馈；OQ-F1-006 已在 F1 关闭，F2 只设计岗位手动录入表单；OQ-F1-035 已在内容沉淀确认功能场景中完整关闭，目标覆盖资产库、薄弱项、训练建议、打磨模式输入、压力面模式输入和下一次模拟面试输入，目标级状态可测试，且明确不得自动静默写入；OQ-F1-040 保留给 F4/F7；未新增页面代号体系 | `docs/02-design/UX_SPEC.md` | AIFI-UX-001、AIFI-PROD-010 | DONE |
| AIFI-UI-001 | F3 | M3 | MUST | 编写 UI 设计系统 | 迁移有效视觉原则，补组件、页面规范和设计 token，服务 F2 已冻结的 PRD 核心需求 | `docs/02-design/UI_DESIGN_SYSTEM.md` | F2 评审 | DONE |
| AIFI-ARCH-001 | F4 | M4 | MUST | 准备 F4 技术设计输入 | 基于 PRD 的业务对象、核心业务数据流、规则约束、状态异常、验收标准和 UNKNOWN，结合当前仓库事实冻结技术架构、服务边界、进展树、薄弱项、岗位匹配、评分、面试复盘、题目推荐和资产边界；除非后续 PRD 变更，项目经历随简历处理 | `docs/02-design/TECH_DESIGN.md`、ADR | F1/F2 | ACCEPTED |
| AIFI-ARCH-002 | F4 | M4 | MUST | 关闭 F4 技术设计 UNKNOWN | 基于 PRD §10 关闭所有 `F4_TECH_DESIGN`，覆盖评分公式、权重、阈值、评分校准方法、低置信度、通过倾向 / 风险提示展示边界、可信度说明、免责声明、版本策略、资产合并、输入优先级、题目推荐、暂停恢复、进展树数据结构、Prompt、模型选择、模型调用参数、复盘切分、薄弱项算法和安全边界 | `TECH_DESIGN.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`API_SPEC.md`、`SECURITY_PRIVACY.md` | AIFI-ARCH-001、AIFI-DATA-001、AIFI-PROMPT-001、AIFI-SEC-001 | ACCEPTED |
| AIFI-ARCH-003 | F4 | M4 | MUST | 完成 F4 Prompt / 安全隐私 / 技术设计对抗性审查 | 审查 `PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`TECH_DESIGN.md` 和 `prompt-contracts/*.md`；F4/M4 人工批准后，该审查证据不再阻断 F5 后端启动 | `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_ADVERSARIAL_REVIEW.md`、`docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_RISK_REGISTER.md`、`docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_REMEDIATION_MATRIX.md`、`docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_ACCEPTANCE.md` | AIFI-ARCH-001、AIFI-PROMPT-001、AIFI-SEC-001、AIFI-DATA-001 | ACCEPTED |
| AIFI-ARCH-004 | F4 | M4 | MUST | 完成 F4 全量技术设计对抗性审计 | 审计 `TECH_DESIGN.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`PROMPT_SPEC.md`、`prompt-contracts/*.md`；F4/M4 人工批准后，当前 Verified / Deferred finding 不再阻断 M4 或 F5 | `docs/02-design/reviews/F4_FULL_DESIGN_ADVERSARIAL_REVIEW.md`、`docs/02-design/reviews/F4_FULL_DESIGN_RISK_REGISTER.md`、`docs/02-design/reviews/F4_FULL_DESIGN_REMEDIATION_MATRIX.md`、`docs/02-design/reviews/F4_FULL_DESIGN_ACCEPTANCE.md` | AIFI-ARCH-001、AIFI-ARCH-002、AIFI-API-001、AIFI-DATA-001、AIFI-PROMPT-001、AIFI-SEC-001 | ACCEPTED |
| AIFI-ARCH-005 | F4 | M4 | MUST | 完成 F4→F8 交接就绪性严格审计 | 基于更高标准重新审计 F4 active design docs 是否足以直接支撑 F5 后端实现、F6 前端接入、F7 联调测试和 F8 发布复盘；所有 known findings Verified，`F4_TO_F8_READINESS_ACCEPTANCE.md` 已记录 F4/M4 人工批准 | `docs/02-design/reviews/F4_TO_F8_READINESS_AUDIT_REPORT.md`、`docs/02-design/reviews/F4_TO_F8_READINESS_RISK_REGISTER.md`、`docs/02-design/reviews/F4_TO_F8_READINESS_REMEDIATION_MATRIX.md`、`docs/02-design/reviews/F4_TO_F8_READINESS_ACCEPTANCE.md` | AIFI-ARCH-001、AIFI-ARCH-002、AIFI-ARCH-004、AIFI-API-001、AIFI-DATA-001、AIFI-PROMPT-001、AIFI-SEC-001 | ACCEPTED |
| AIFI-ARCH-006 | F4 | M4 | MUST | 完成 docs/02 设计体系深度语义关联审计 | 审计 `docs/02-design` active 设计文档之间的 PRD -> UX -> UI -> TECH -> DATA -> API -> PROMPT -> SECURITY -> F5 -> F8 语义链路、上下游闭环、历史审计问题复发和 F5/F6/F7/F8 交接能力；F4/M4 人工批准后，该审计作为后续 F6/F8 refinement evidence 保留，不阻断 F5 后端启动 | `docs/02-design/reviews/DOCS02_DEEP_SEMANTIC_AUDIT_REPORT.md`、`docs/02-design/reviews/DOCS02_DEEP_SEMANTIC_RISK_REGISTER.md`、`docs/02-design/reviews/DOCS02_DEEP_SEMANTIC_REMEDIATION_MATRIX.md`、`docs/02-design/reviews/DOCS02_DEEP_SEMANTIC_ACCEPTANCE.md` | AIFI-ARCH-004、AIFI-ARCH-005、AIFI-API-001、AIFI-DATA-001、AIFI-PROMPT-001、AIFI-SEC-001 | ACCEPTED |
| AIFI-API-001 | F4 | M4 | MUST | 编写 API 契约 | 汇总岗位、简历、岗位绑定、岗位匹配分析、打磨模式、资产、双模式模拟面试、面试报告、面试复盘、报告内容复制边界、训练、权限 API | `docs/02-design/API_SPEC.md` | AIFI-ARCH-001 | ACCEPTED |
| AIFI-DATA-001 | F4 | M4 | MUST | 编写数据模型 | 汇总简历、简历中的项目经历模块、岗位 / JD、岗位与简历绑定关系、岗位匹配分析结果、匹配度评分、匹配点、不匹配点、加强点、打磨模式记录、面试复盘记录、资产库、模拟面试会话、题目、回答、点评、评分、失分点、参考回答、考点解析、进展树、暂停恢复状态、薄弱项、训练建议和资产库回流关系；除非后续 PRD 变更，不把项目建成独立一级数据对象 | `docs/02-design/DATA_MODEL.md` | AIFI-PROD-003、AIFI-PROD-004、AIFI-PROD-007、AIFI-PROD-008、AIFI-PROD-009 | ACCEPTED |
| AIFI-PROMPT-001 | F4 | M4 | MUST | 编写 Prompt 规范 | 写入参考材料包、资产库消费、打磨模式出题、压力面模式出题和追问、考点规划、问题生成、点评、打分、失分原因、参考回答、考点解析、技术原理扩展、面试报告、模拟面试复盘、薄弱项提炼、岗位匹配分析、匹配度打分、匹配点、不匹配点、加强点分析、岗位匹配分析提炼薄弱项、低置信度规则和通过倾向 / 风险提示表达边界 | `docs/02-design/PROMPT_SPEC.md` | AIFI-PROD-004、AIFI-PROD-005、AIFI-PROD-007、AIFI-PROD-008 | ACCEPTED |
| AIFI-SEC-001 | F4 | M4 | MUST | 编写安全隐私规范 | 权限、数据可见性、审计、脱敏、保留周期、Markdown 简历输入安全、报告复制内容边界、可信度说明和资产访问边界 | `docs/02-design/SECURITY_PRIVACY.md` | AIFI-PROD-003 | ACCEPTED |
| AIFI-BE-001 | F5 | M5 | MUST | 完成后端核心链路 | 实现服务端保存、Markdown 简历粘贴 / 编辑保存、简历中的项目经历模块、打磨模式记录、面试复盘、资产沉淀和读取、资产驱动模拟面试输入、打磨模式会话、压力面模式会话、面试报告生成、模拟面试复盘、真实面试复盘、薄弱项提炼、打磨模式暂停与恢复状态、岗位绑定简历、岗位匹配度分析、0-100 评分展示所需结果、匹配点、不匹配点、加强点生成、从岗位匹配分析中提炼薄弱项、RAG/LLM、评分复盘、报告内容复制所需内容读取能力；不得拆出 PDF 导入、文件解析、MIME 校验或对象存储作为 MVP 必需任务 | 后端实现、API 测试 | F4/M4 Accepted；`F4_TO_F8_READINESS_ACCEPTANCE.md` | READY_TO_START |
| AIFI-BE-002 | F5 | M5 | SHOULD | 创建 LangGraph MultiAgent 重构专题设计包骨架 | 在不修改业务代码、测试、依赖或 migration 的前提下登记 LangGraph MultiAgent 重构专题，创建 PR1 planning package，冻结单微服务双域、Option C、AI Runtime、checkpoint 非事实源、raw payload 禁止、candidate/formal 边界和 PR1-PR8 拆分；`DONE` 只表示 PR1 skeleton / planning package 完成，不表示 runtime data model、repository、API、graph、frontend、test 或 security/privacy implementation-ready；历史 planning package 已去层删除，已确认实现证据迁入 active docs 和实现说明 | `docs/00-governance/DOCS_INDEX.md`、`docs/03-implementation/BACKLOG.md`、`docs/02-design/APPLICATION_FLOW_SPEC.md`、`docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md` | F4/M4 Accepted；`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`；`docs/tmp/*` 仅作 PR1 输入 | DONE |
| AIFI-BE-003 | F5 | M5 | MUST | 修复 LangGraph MultiAgent PR1.5 implementation-ready spec | 在不修改业务代码、测试、依赖或 migration 的前提下，将历史 skeleton planning package 修成 implementation-ready spec package；补齐 Option C 决策状态、目录 / import / dependency 边界、AI Runtime 方法级 contract、runtime data model、LLM trace、replay / resume / idempotency、graph node contract、API/schema、frontend state machine、测试方法级计划、validation gate 和 PR sequence；历史 planning package 已去层删除，后续不得作为 source of truth | `docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md`、`docs/02-design/APPLICATION_FLOW_SPEC.md`、`docs/02-design/PERSISTENCE_MODEL.md`、`docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md`、`docs/00-governance/DOCS_INDEX.md`、`docs/03-implementation/BACKLOG.md` | AIFI-BE-002；F4/M4 Accepted；active design docs；`docs/tmp/*` 仅作 PR1 输入，不作为事实源 | DONE |
| AIFI-BE-004 | F5 | M5 | MUST | 补齐 Pressure Mode mode-level spec | 基于 PR1.6 `PR16-BLOCKER-003`，已冻结压力面独立 session、turn、pace、end condition、report input package、API/data/UI/runtime prompt bundle、graph boundary 和测试契约；Pressure graph 不进入 PR2，PR8 或独立受权 Pressure PR 才能实现业务 graph | `docs/02-design/PRESSURE_MODE_SPEC.md`、`APPLICATION_FLOW_SPEC.md`、`DATA_MODEL.md`、`API_SPEC.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`prompt-contracts/PRESSURE_CONTRACTS.md`、PR1.6 验证证据 | AIFI-BE-003；AIFI-PROMPT-002 | ACCEPTED |
| AIFI-PROMPT-002 | F5 | M5 | MUST | 补齐 Prompt Asset / Prompt Evaluation 设计 | 已定义 Prompt Contract、Runtime Prompt Bundle、Production Prompt Asset、Prompt Skill / capability prompt、Prompt Evaluation Fixture、Golden Fixture、Counterexample、Prompt Regression Suite 和 Model Comparison Policy 的职责分工；已冻结 Prompt Asset registry owner/path/fields、contract/runtime/builder/validator/test 映射、golden / regression / negative fixtures、quality metrics、fake / real provider gate、human review、CI gate、release / rollback 和 redaction policy；防止 runtime prompt 只隐藏在 Python builder 或 fake transport 中 | `docs/02-design/PROMPT_ASSET_SPEC.md`、`docs/02-design/PROMPT_EVALUATION_SPEC.md`、`PROMPT_SPEC.md`、`prompt-contracts/*.md`、PR1.6 验证证据；两个新增 registry / evaluation 文档已登记 `DOCS_INDEX.md` | AIFI-PROMPT-001；AIFI-BE-003；PR1.6 `PR16-MAJOR-002`、`PR16-MINOR-001` | ACCEPTED |
| AIFI-ARCH-007 | F5 | M5 | MUST | 补齐 Skill / Capability Model 设计 | 已冻结 Skill taxonomy 与 `ScoreDimension`、`ProgressTree`、`Weakness`、`Asset`、`TrainingRecommendation` / `TrainingTask` 的映射和非替代关系，定义 `SkillTaxonomyVersion`、`SkillArea`、`Skill`、`SkillLevel`、`SkillEvidence`、`SkillAssessment`、`SkillGap`、`SkillProgress` 及 confirmation boundary；后续实现不得把任一现有对象临时升级为 Skill，也不得绕过 `SKILL_MODEL_SPEC.md` 发明临时 skill key | `docs/02-design/SKILL_MODEL_SPEC.md`、`BACKLOG.md`、`DOCS_INDEX.md`、`DATA_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md`、`APPLICATION_FLOW_SPEC.md` | AIFI-DATA-001；AIFI-PROMPT-001；AIFI-ARCH-006；PR1.6 `PR16-MAJOR-003`、`PR16-MAJOR-004` | ACCEPTED |
| AIFI-ARCH-008 | F5 | M5 | MUST | 收敛 AI/Core 目录边界与 ADR 更新 | 基于 Option C 收敛最终目录命名，解决 `application/ai`、`application/agents`、`application/ai_runtime` 与 `infrastructure/agent_runtime` / `infrastructure/ai_runtime` 的分裂风险；已冻结 import scan 规则、PR2 不创建业务 graph 目录、PR3/PR4 目录职责和 ADR caveat；`ACCEPTED` 只关闭目录边界 blocker，不实现 runtime symbol，不授权业务 graph | ADR-0005、`docs/02-design/APPLICATION_FLOW_SPEC.md`、`docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md`、验证 / 导入边界规则 | AIFI-BE-003；ADR-0005；PR1.6 `PR16-MAJOR-001` | ACCEPTED |
| AIFI-BE-005 | F5 | M5 | MUST | PR2 Runtime Data Model preflight readiness gate | 已在代码实现前逐项复核 PR1.6 P0 gates：source-of-truth backfill、runtime flags、directory boundary、repository contract、bootstrap/rollback、test list、Prompt Asset boundary、Pressure hold、Skill model accepted、security/privacy raw-off；结论为 `CONDITIONAL GO`，PR2 只允许创建 AI Runtime 数据模型、repository 和后端测试，且 runtime default-off、不启用 LangGraph / graph / real provider / business migration；原 exact scope 文档已去层删除，后续 PR2 需要 fresh scope lock | `docs/02-design/PERSISTENCE_MODEL.md`、`docs/02-design/APPLICATION_FLOW_SPEC.md`、`docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md`、`docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md`、readiness verdict、允许 / 禁止文件清单、验证命令清单、accepted-risk 记录 | AIFI-BE-004、AIFI-ARCH-007、AIFI-PROMPT-002、AIFI-ARCH-008 已 ACCEPTED；ADR-0005 保持 Proposed 但 PR2-only accepted risk 已登记；AIFI-BE-006 governance closure 已完成 | ACCEPTED |
| AIFI-BE-006 | F5 | M5 | MUST | PR2 governance closure | 在 docs-only 范围内关闭或保留 PR2 governance blockers，决定 AIFI-ARCH-008、ADR-0005、runtime default-off 和 source-of-truth backfill 处理方式；原 exact PR2 scope lock 已随旧规划层删除，后续 implementation 不得复用旧目录；本任务不修改 `apps/**`、`tests/**`、依赖、migration、CI、业务代码，不调用真实 LLM | `docs/03-implementation/BACKLOG.md`、ADR-0005、`docs/02-design/APPLICATION_FLOW_SPEC.md`、`docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md` | AIFI-BE-005；AIFI-ARCH-008 | ACCEPTED |
| AIFI-BE-007 | F5 | M5 | MUST | 收敛 runtime-state 契约与并发安全实现入口 | 在 active design docs、ADR-0005 default-off 边界和当轮 scope lock 下，分切片实现 answer durable idempotency、feedback task/result idempotency 与原子性、feedback running/resume/cancel/deadline、question final write once、progress stale guard、RAG empty non-claim、token budget request-scoped、raw dump / real-provider / sensitive marker fail-closed；不得把临时方案包、fixed sample、frontend loading、进程内 lock/cache 或顺序 commit 当作 durable runtime contract；新增 queue/outbox、streaming、provider lane、raw-debug 策略或 migration 前必须重新做 ADR / rollback / 安全授权判断 | 后端/API/Web/eval focused tests、scope lock、review evidence；必要时回写 active docs 或 ADR | AIFI-BE-005、AIFI-BE-006、ADR-0005；F4/M4 Accepted | READY_TO_START |
| AIFI-BE-008 | F5 | M5 | MUST | 关闭 Polish execution temporary exceptions | 在 `refactor-for-arch-01` 已回写的 Execution Minimal Model 下，清理 remaining skeleton / placeholder / graph descriptor temporary exceptions；每个例外必须具备 blocking condition、delete condition、cleanup task、owner check 和 unavailable safe response，且不得恢复旧 direct path、旧 API compat mirror payload、legacy fallback-as-authority、provider direct formal write 或 frontend execution target override；进入 formal business graph enablement 前必须完成 focused grep gate、contract tests 和 final cleanup evidence | `apps/api/app/application/polish/**`、`apps/api/app/application/ai_runtime/**`、`tests/api/test_polish_*`、active design docs / ADR evidence | AIFI-BE-007；ADR-0005；APPLICATION_FLOW_SPEC §2.3；API_SPEC §5.5 | NOT_STARTED |
| AIFI-FE-001 | F6 | M6 | MUST | 完成前端核心链路 | 实现工作台、简历、简历中的项目经历模块、岗位 / JD、岗位绑定简历、岗位匹配分析、资产库、打磨模式、压力面模式、进展树、面试报告、报告内容复制、模拟面试复盘、真实面试复盘、薄弱项、训练建议、暂停恢复、反馈回流和异常状态页面 | 前端实现、页面测试 | F5 主接口可用 | NOT_STARTED |
| AIFI-QA-001 | F7 | M7 | MUST | 完成全链路测试 | 验证 PRD 中的用户故事、核心业务数据流、功能逻辑、输入 / 输出、状态异常和验收标准，包括 Markdown 简历粘贴 / 保存、简历中的项目经历模块、岗位 / JD、岗位绑定简历、岗位匹配分析、0-100 评分展示、资产库、打磨模式、压力面模式、进展树、面试报告、报告内容复制、无文件导出入口、模拟面试复盘、真实面试复盘、薄弱项、训练建议和反馈回流；F7 不按 PDF 导入、文件解析或 MIME 校验设计 MVP 验收 | `docs/03-implementation/TEST_PLAN.md`、测试报告 | F5/F6 | NOT_STARTED |
| AIFI-QA-002 | F7 | M7 | MUST | 验证 UNKNOWN 关闭状态 | 在测试计划和测试报告中确认 PRD §10 中所有影响验收的 UNKNOWN 已关闭、已转为明确测试断言或已按产品原因排除出 MVP 阻塞范围；重点验证 0-100 展示、无精确通过概率承诺、风险提示不误导用户 | `docs/03-implementation/TEST_PLAN.md`、测试报告 | AIFI-QA-001、AIFI-UX-002、AIFI-ARCH-002 | NOT_STARTED |
| AIFI-REL-001 | F8 | M8 | MUST | 完成发布检查 | 基于 `docs/02-design/RELEASE_HANDOFF_SPEC.md` 生成正式发布清单、变更记录输入、known limitations 和发布复盘输入；检查 PRD 核心需求无遗漏，并验证 no export、no file download、no exact probability、candidate not formal、copy boundary、owner boundary、source unavailable、low confidence、validation failed 等发布阻断项 | `docs/03-implementation/RELEASE_CHECKLIST.md`、`CHANGELOG.md`、known limitations、release retrospective input | F7 全链路通过；`RELEASE_HANDOFF_SPEC.md` | NOT_STARTED |
| AIFI-REL-002 | F8 | M8 | MUST | 编写 F8 runbook | 基于 `RELEASE_HANDOFF_SPEC.md` 的 runbook source 表生成运行手册，覆盖 provider unavailable / timeout / rate limit、AI task timeout、generation failed、validation failed、low confidence spike、source unavailable、RAG retrieval empty、owner mismatch spike、idempotency conflict、stale version conflict、copy boundary violation、export not supported attempt、audit / trace write failure、database migration failure 和 backup restore required | runbook | AIFI-REL-001；F7 全链路通过 | NOT_STARTED |
| AIFI-REL-003 | F8 | M8 | MUST | 完成 rollback / migration / backup restore 发布方案 | 基于 `PERSISTENCE_MODEL.md` 和 `RELEASE_HANDOFF_SPEC.md` 生成 migration 前后检查、rollback trigger、rollback decision owner、schema rollback 风险、data compatibility、versioned object rollback、`ScoreRuleVersion` rollback、in-flight `AiTask` rollback、backup restore validation 和 source availability after restore 检查 | rollback strategy、migration checklist、restore validation checklist | AIFI-BE-001；AIFI-QA-001；AIFI-REL-001 | NOT_STARTED |
| AIFI-REL-004 | F8 | M8 | MUST | 完成 observability / audit / trace 发布检查 | 基于 `SECURITY_PRIVACY.md`、`API_SPEC.md`、`DATA_MODEL.md` 和 `RELEASE_HANDOFF_SPEC.md` 校验 monitoring / observability signals、logs redaction、audit events、trace refs、rate limit headers、provider failure category、copy event summary、confirmation action、retention / deletion action；不要求 F4 已实现完整观测平台或 SIEM | observability checklist、audit / trace release check | AIFI-REL-001；F7 全链路通过 | NOT_STARTED |
| AIFI-REL-005 | F8 | M8 | MUST | 完成 security / privacy 发布验证 | 验证 owner boundary、session / cookie / token、secret handling、log redaction、provider payload、system prompt、completion 原文、copy boundary、third-party privacy、retention / deletion、backup restore、rate limit、provider failure、audit event、trace 和 source availability；不保存 provider payload / completion 原文，不暴露 hidden scoring rules | security / privacy release verification | AIFI-SEC-001；AIFI-REL-001；F7 全链路通过 | NOT_STARTED |
| AIFI-REL-006 | F8 | M8 | LATER | 梳理下一轮 advanced features | 承接不阻断 MVP 的 advanced / deferred 项：真实招聘结果校准、复杂动态权重学习、provider-specific tuning、可选 queue / worker 独立化、vector database / embedding model selection、full observability platform、full SIEM / log platform、enterprise SSO / OAuth、organization / team ACL、internet search governance、advanced backup restore automation、advanced semantic dedup / merge algorithm | next iteration backlog candidates 或 accepted risk 清单 | AIFI-REL-001 | NOT_STARTED |
| AIFI-REL-007 | F8 | M8 | LATER | 评估 advanced release automation | 在人工 release checklist、changelog、runbook、rollback strategy 和 retrospective 流程稳定后，再评估自动生成、自动核对或自动归档能力；不阻断 MVP 发布 | release automation proposal 或 accepted risk 说明 | AIFI-REL-001 | NOT_STARTED |
| AIFI-PROD-011 | F1 | M1 | MUST | BMAD feedback PRD active docs intake | 将 BMAD feedback-loop PRD 作为需求来源登记到 active PRD、需求追踪和相关设计文档；不改产品代码 | active docs 来源回写、Non-goals、Open Questions、追踪入口 | BMAD PRD；Lazycodex plan；AIFI-TRACE-001 | NOT_STARTED |
| AIFI-TRACE-001 | F1 | M1 | MUST | BMAD C-ID traceability registration | 登记 C-001 到 C-054 的来源状态、active doc 去向、BACKLOG 承接和关闭条件；不把 Deferred 项改成已实现 | `REQUIREMENT_TRACEABILITY.md` C-ID 追踪矩阵 | BMAD PRD；Lazycodex plan；AIFI-PROD-011 | NOT_STARTED |
| AIFI-ARCH-009 | F4 | M4 | MUST | Feedback stability architecture gap analysis | 规划级分析 feedback 稳定性、API、data、prompt、scoring、state 和 release 差距；不形成代码级实现方案 | active design docs 差距清单、ADR 是否需要的判断 | AIFI-PROD-011；AIFI-TRACE-001 | NOT_STARTED |
| AIFI-QA-003 | F7 | M7 | MUST | Feedback acceptance semantics matrix | 硬化“基本一致、评分趋势应上升、大量失分点、用户补足失分点、自动验收 vs 人工验收”的验收语义；不定义未确认阈值 | QA 语义矩阵、人工抽样边界、待确认阈值清单 | AIFI-PROD-011；AIFI-ARCH-009 | NOT_STARTED |
| AIFI-BE-009 | F5 | M5 | MUST | Feedback state and compatibility survey | 只做后端状态、旧反馈、旧题目状态、task 状态、payload projection、数据读写和迁移风险探查；不修改后端代码 | 兼容性矩阵、数据风险清单、迁移/回滚待确认项 | AIFI-PROD-011；AIFI-ARCH-009；AIFI-QA-003 | NOT_STARTED |
| AIFI-FE-002 | F6 | M6 | SHOULD | Feedback display and refresh recovery survey | 只做前端反馈展示、失败折叠、刷新恢复、状态提示去重和验收证据展示缺口探查；不修改页面代码 | UX/FE 展示差距清单、刷新恢复验收建议 | AIFI-PROD-011；AIFI-QA-003 | NOT_STARTED |
| AIFI-REL-008 | F8 | M8 | MUST | Feedback rollback and degradation gate plan | 规划 feedback-loop 重构的开关、降级、数据兼容、迁移、恢复和发布门槛；不声明 release-ready | rollback/degradation gate TODO、发布门槛清单 | AIFI-PROD-011；AIFI-ARCH-009；AIFI-QA-003；AIFI-BE-009；AIFI-FE-002 | NOT_STARTED |

## 2. BMAD feedback-loop planning intake task details

以下入口来自 2026-06-23 BMAD feedback-loop PRD 与 Lazycodex 重构规划。PRD 是需求来源；Lazycodex plan 是工程规划来源。以下任务只建立 active docs / BACKLOG 治理入口，不是可直接进入产品代码实现的开发任务。

### AIFI-PROD-011 BMAD feedback PRD active docs intake

- 背景：BMAD feedback-loop PRD 已通过 Plan Readiness Gate 允许进入 active docs / BACKLOG 回写，但当前仍不是可直接开工的实现方案。
- 范围：回写 active PRD、需求追踪和相关设计文档的来源边界、Non-goals、Open Questions、验收术语和后续承接关系。
- 非目标：不修改产品代码、不生成接口/数据/Prompt/页面实现方案、不关闭 C-049 到 C-054。
- PRD 来源：`_bmad-output/planning-artifacts/PRD.md`、`_bmad-output/planning-artifacts/briefs/brief-AiForInterviewer-2026-06-23/brief-traceability.md`；工程规划来源：`.omo/plans/bmad-feedback-loop-refactor-planning.md`。
- 验收标准：active docs 明确 BMAD PRD 是需求来源、Lazycodex plan 是工程规划来源；C-049 到 C-054 保持 Deferred / Open Question；BR-024 仅登记为产品排序规则，不登记为算法实现；没有产品代码 diff。
- 依赖：BMAD PRD、Lazycodex plan、AIFI-TRACE-001。
- 是否阻塞后续实现：是。未完成前不得进入 `$start-work` 或代码实现。

### AIFI-TRACE-001 BMAD C-ID traceability registration

- 背景：BMAD PRD 包含 C-001 到 C-054 的确认、拒绝和后置项，需要进入唯一需求追踪入口，避免 planning artifact 直接变成执行依据。
- 范围：登记 C-ID 状态、目标 active docs、BACKLOG 承接和关闭条件；显式标注 C-049 到 C-054 Deferred。
- 非目标：不把 BMAD C-ID 标为已实现，不把 Deferred 项改写成 MERGED / ACCEPTED，不从 brief 或 addendum 替代 PRD §13.2 / traceability 主证据。
- PRD 来源：`_bmad-output/planning-artifacts/PRD.md` §13.2、`brief-traceability.md`；工程规划来源：`.omo/plans/bmad-feedback-loop-refactor-planning.md`。
- 验收标准：`REQUIREMENT_TRACEABILITY.md` 可追踪 C-001 到 C-054；Rejected / Deferred 项不会出现在可开工实现范围；C-048 / BR-024 不关闭 C-054。
- 依赖：AIFI-PROD-011。
- 是否阻塞后续实现：是。未登记前不得按 BMAD PRD 启动实现。

### AIFI-ARCH-009 Feedback stability architecture gap analysis

- 背景：当前代码事实只证明已有 feedback task、payload、展示和部分兼容机制，不能证明 BMAD 的同答一致性、评分趋势和参考答案回灌验收已实现。
- 范围：在 active API、data、persistence、prompt、scoring、UX、security 和 release docs 中登记差距分析入口和后续设计问题。
- 非目标：不选择相似度算法、不定义数据迁移、不命名开关、不写接口字段、不写 Prompt 正文、不形成实现任务拆分。
- PRD 来源：BMAD PRD 的 Goals、FR、Business Rules、Acceptance Criteria、Compatibility Constraints；工程规划来源：Lazycodex plan 的代码事实和风险矩阵。
- 验收标准：相关 active design docs 均能说明 PRD 需求来源、工程规划来源、当前只登记差距和待确认项；必要 ADR 仅作为待判断项，不自动创建。
- 依赖：AIFI-PROD-011、AIFI-TRACE-001。
- 是否阻塞后续实现：是。未完成前不得将 feedback-loop 重构列为 implementation-ready。

### AIFI-QA-003 Feedback acceptance semantics matrix

- 背景：PRD Readiness P1 指出验收语义仍需硬化，尤其是“基本一致”“评分趋势应上升”“大量失分点”和“用户补足失分点”。
- 范围：定义验收语义的规划口径、自动验收候选、人工验收边界、未决阈值和样本需求。
- 非目标：不直接设定最终阈值、不写测试代码、不生成 fixtures、不把 LLM 语义判断完全自动化。
- PRD 来源：BMAD PRD Acceptance Criteria 与 validation report；工程规划来源：Lazycodex plan 的验收语义硬化建议。
- 验收标准：QA 语义矩阵覆盖基本一致、评分趋势应上升、大量失分点、用户补足失分点、自动验收 vs 人工验收边界；待确认阈值不得伪装成已确认。
- 依赖：AIFI-PROD-011、AIFI-ARCH-009。
- 是否阻塞后续实现：是。未完成前不得把 BMAD 验收写成代码验收标准。

### AIFI-BE-009 Feedback state and compatibility survey

- 背景：PRD Readiness P1 指出兼容性矩阵不足，Lazycodex plan 也标出旧反馈、旧题目状态、API 行为、数据读写和迁移风险。
- 范围：只探查旧 feedback payload、旧 `feedback_summary`、question / progress / task 状态、API envelope、数据读写、迁移和 read-time projection 风险。
- 非目标：不修改后端代码、不写 migration、不改 schema、不删除兼容字段、不恢复旧顶层 mirror。
- PRD 来源：BMAD PRD Compatibility Constraints；工程规划来源：Lazycodex plan 的兼容性矩阵。
- 验收标准：兼容性矩阵覆盖旧反馈、旧题目状态、API 行为、数据读写 / 迁移和 rollback 风险；明确哪些需要后续 active docs 或 ADR 判断。
- 依赖：AIFI-PROD-011、AIFI-ARCH-009、AIFI-QA-003。
- 是否阻塞后续实现：是。未完成前不得做 feedback state / persistence 类代码改动。

### AIFI-FE-002 Feedback display and refresh recovery survey

- 背景：Lazycodex plan 标出前端可展示 feedback card、score、loss_points、reference answer，但缺少同答一致性、趋势验收证据和完整刷新恢复验收闭环。
- 范围：只探查 feedback card、失败折叠、task timeout、session refresh、状态提示去重、验收证据展示和暂停/恢复可见边界。
- 非目标：不修改前端代码、不设计最终 UI、不关闭 C-051 / C-053、不写 Playwright 或截图验收。
- PRD 来源：BMAD PRD UX/Compatibility 相关条目；工程规划来源：Lazycodex plan 的 frontend facts 与兼容性矩阵。
- 验收标准：UX/FE 差距清单覆盖旧反馈展示、失败状态、刷新恢复、状态提示去重和验收证据展示；未确认 UI 样式不进入 active 事实。
- 依赖：AIFI-PROD-011、AIFI-QA-003。
- 是否阻塞后续实现：否。它依赖产品/QA语义，但不单独阻塞 active docs 回写；会阻塞具体前端改造开工。

### AIFI-REL-008 Feedback rollback and degradation gate plan

- 背景：PRD Readiness P1 指出回滚 / 降级需要后续规划补出 TODO，Lazycodex plan 要求开关设计、数据兼容、迁移策略、恢复策略和发布门槛。
- 范围：在 release handoff 中登记 default-off / gray / rollback / restore / release gate 的规划入口和待确认问题。
- 非目标：不命名真实 env var、不写部署脚本、不声明 release-ready、不修改 runtime、不写迁移或回滚命令。
- PRD 来源：BMAD PRD Risk、Compatibility、Acceptance Criteria；工程规划来源：Lazycodex plan 的回滚 / 降级 / 发布门槛 TODO。
- 验收标准：发布门槛 TODO 覆盖开关设计、数据兼容、迁移策略、恢复策略和发布门槛；明确未通过前禁止进入 `$start-work`。
- 依赖：AIFI-PROD-011、AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002。
- 是否阻塞后续实现：是。未完成前不得进入可发布或灰度执行判断。

## 3. 优先级定义

| 优先级 | 定义 |
|---|---|
| MUST | 没有它不能发布 |
| SHOULD | MVP 强相关，但不阻塞发布 |
| COULD | 可选优化 |
| LATER | 下一轮迭代 |

## 4. 旧任务迁移规则

1. 旧任务包只作为历史来源或归档证据，不得直接作为当前任务入口。
2. 每个仍有效的旧任务必须映射到一个 `AIFI-*` 任务。
3. 无法证明仍有效的旧任务标记为 `UNKNOWN`，待核查后再进入 Backlog。
4. 模块级待办不得绕过本文件直接执行。
