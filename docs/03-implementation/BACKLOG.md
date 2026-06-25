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
| AIFI-PROD-011 | F1 | M1 | MUST | BMAD feedback PRD active docs intake | 已将 BMAD feedback-loop PRD 作为需求来源登记到 active PRD、需求追踪和相关设计文档；不改产品代码 | active docs 来源回写、Non-goals、Open Questions、追踪入口 | BMAD PRD；Lazycodex plan | DONE |
| AIFI-TRACE-001 | F1 | M1 | MUST | BMAD C-ID traceability registration | 已完成 BMAD C-ID 单项追踪登记，包含来源状态、active doc 去向、BACKLOG 承接和关闭条件；Rejected / Deferred 边界保持，不把 Deferred 项改成已实现 | `REQUIREMENT_TRACEABILITY.md` C-ID 追踪矩阵 | BMAD PRD；Lazycodex plan；AIFI-PROD-011 | DONE |
| AIFI-ARCH-009 | F4 | M4 | MUST | Feedback stability architecture gap analysis | 规划级分析 feedback 稳定性、API、data、prompt、scoring、state 和 release 差距；不形成代码级实现方案 | active design docs 差距清单、ADR 是否需要的判断 | AIFI-PROD-011；AIFI-TRACE-001 | NOT_STARTED |
| AIFI-QA-003 | F7 | M7 | MUST | Feedback acceptance semantics matrix | 硬化“基本一致、评分趋势应上升、大量失分点、用户补足失分点、自动验收 vs 人工验收”的验收语义；不定义未确认阈值 | QA 语义矩阵、人工抽样边界、待确认阈值清单 | AIFI-PROD-011；AIFI-ARCH-009 | NOT_STARTED |
| AIFI-BE-009 | F5 | M5 | MUST | Feedback state and compatibility survey | 只做后端状态、旧反馈、旧题目状态、task 状态、payload projection、数据读写和迁移风险探查；不修改后端代码 | 兼容性矩阵、数据风险清单、迁移/回滚待确认项 | AIFI-PROD-011；AIFI-ARCH-009；AIFI-QA-003 | NOT_STARTED |
| AIFI-FE-002 | F6 | M6 | SHOULD | Feedback display and refresh recovery survey | 只做前端反馈展示、失败折叠、刷新恢复、状态提示去重和验收证据展示缺口探查；不修改页面代码 | UX/FE 展示差距清单、刷新恢复验收建议 | AIFI-PROD-011；AIFI-QA-003 | NOT_STARTED |
| AIFI-REL-008 | F8 | M8 | MUST | Feedback rollback and degradation gate plan | 规划 feedback-loop 重构的开关、降级、数据兼容、迁移、恢复和发布门槛；不声明 release-ready | rollback/degradation gate TODO、发布门槛清单 | AIFI-PROD-011；AIFI-ARCH-009；AIFI-QA-003；AIFI-BE-009；AIFI-FE-002 | NOT_STARTED |
| AIFI-QA-004 | F7 | M7 | MUST | Feedback acceptance semantics tests | 基于 `.omo/plans/plan.md` Step 1 建立 AC-001、AC-002、AC-003、AC-012 首批 feedback 验收语义测试护栏；当前收口为 `ACCEPTED_RED`，RED 作为后续实现缺口证据 | `tests/api/test_polish_feedback_acceptance_semantics.py` 等 pytest 覆盖和语义矩阵证据 | AIFI-PROD-011；AIFI-TRACE-001；当轮 scope lock | ACCEPTED_RED |
| AIFI-BE-010 | F5 | M5 | MUST | Effective feedback state and compatibility | 实现有效 feedback 状态、旧 payload 兼容投影和 API/schema 兼容读取；AIFI-BE-009 仅作为参考上下文，不再作为硬依赖，AIFI-BE-009=NOT_STARTED 不阻塞本任务启动；Step2 effective feedback selector 已完成并提交 | 后端状态契约、兼容投影、相关 tests/api；Step2 commit `763ad98668535998bb7c16ad32e08d7bae1bc94a` | AIFI-QA-004；AIFI-BE-009（参考上下文，非硬依赖） | DONE |
| AIFI-BE-011 | F5 | M5 | MUST | Fail-closed feedback validation | 实现 feedback 生成失败时的 fail-closed 校验、投影和错误折叠 | validation/projection/service 行为和失败路径 tests/api | AIFI-BE-010 | DONE |
| AIFI-BE-012 | F5 | M5 | MUST | Same-answer stability and reference-answer replay | 实现同答案稳定评分、参考答案 replay 和评分归一化；Step4 closeout 已通过 | scoring/runtime 稳定性行为和回归 tests/api；Step4 commit `2e82dbfbc8f23d0c09cd784a94190dceecc36732` | AIFI-BE-010；AIFI-BE-011 | DONE |
| AIFI-BE-015 | F5 | M5 | MUST | Improved-answer trend calibration and effective-result consistency | 实现改进回答后的评分趋势校准、current effective feedback result 一致性，以及 Step2/Step3/Step4 兼容；Step5 closeout 已通过并提交 | improvement trend / effective-result 行为和相关 tests/api；Step5 commit `ef95d4a9139d4c0f41593a6c9c57897d533aca0b` | AIFI-BE-010；AIFI-BE-011；AIFI-BE-012；AIFI-QA-004 | DONE |
| AIFI-BE-013 | F5 | M5 | MUST | Progress mastery and manual completion consistency | 实现 progress mastery、手动完成和有效反馈状态一致性；仅允许重新执行 Step6 scope lock，scope lock 返回授权前不得实现 | progress/use cases 一致性行为和 tests/api | AIFI-BE-010；AIFI-BE-012；AIFI-BE-015 | READY_TO_START |
| AIFI-BE-014 | F5 | M5 | MUST | Follow-up and next-question behavior | 实现追问、下一题、progress 绑定和相似度拦截语义 | question generation/progress binding 行为和 tests/api | AIFI-BE-013 | NOT_STARTED |
| AIFI-FE-003 | F6 | M6 | MUST | Feedback view model and failure folding | 实现前端 feedback view model、失败折叠和旧 payload 容错 | `entities/polish` view model/types/API 适配和 FE tests | AIFI-BE-010；AIFI-BE-011；AIFI-BE-014；AIFI-FE-002 | NOT_STARTED |
| AIFI-FE-004 | F6 | M6 | MUST | Interview workbench interaction and refresh recovery | 实现面试工作台反馈交互、刷新恢复和重试/降级呈现 | `InterviewPage.tsx` 行为和相关 FE tests | AIFI-FE-003；AIFI-BE-010；AIFI-BE-011；AIFI-BE-012；AIFI-BE-015；AIFI-BE-013；AIFI-BE-014 | NOT_STARTED |
| AIFI-REL-009 | F8 | M8 | MUST | Feedback-loop release gate and rollback checklist | 建立 feedback-loop 发布门禁、回滚 checklist 和 QA evidence 归档要求 | release/runbook/QA evidence 文档更新 | AIFI-QA-004；AIFI-BE-010；AIFI-BE-011；AIFI-BE-012；AIFI-BE-015；AIFI-BE-013；AIFI-BE-014；AIFI-FE-003；AIFI-FE-004；AIFI-REL-008 | NOT_STARTED |

## 2. BMAD feedback-loop planning intake task details

以下入口来自 2026-06-23 BMAD feedback-loop PRD 与 Lazycodex 重构规划。PRD 是需求来源；Lazycodex plan 是工程规划来源。以下任务只建立 active docs / BACKLOG 治理入口，不是可直接进入产品代码实现的开发任务。

### AIFI-PROD-011 BMAD feedback PRD active docs intake

- 背景：BMAD feedback-loop PRD 已通过 Plan Readiness Gate 允许进入 active docs / BACKLOG 回写，但当前仍不是可直接开工的实现方案。
- 范围：回写 active PRD、需求追踪和相关设计文档的来源边界、Non-goals、Open Questions、验收术语和后续承接关系。
- 非目标：不修改产品代码、不生成接口/数据/Prompt/页面实现方案、不关闭 C-049 到 C-054。
- PRD 来源：`_bmad-output/planning-artifacts/PRD.md`、`_bmad-output/planning-artifacts/briefs/brief-AiForInterviewer-2026-06-23/brief-traceability.md`；工程规划来源：`.omo/plans/bmad-feedback-loop-refactor-planning.md`。
- 验收标准：active docs 明确 BMAD PRD 是需求来源、Lazycodex plan 是工程规划来源；C-049 到 C-054 保持 Deferred / Open Question；BR-024 仅登记为产品排序规则，不登记为算法实现；没有产品代码 diff。
- 完成证据：Todo 1-3 证据确认 PRD、需求追踪和计划列出的相关设计文档已完成 active-docs intake；本任务关闭不关闭 AIFI-TRACE-001。
- 依赖：BMAD PRD、Lazycodex plan。
- 是否阻塞后续实现：否。active-docs intake 已完成；后续实现仍受 AIFI-TRACE-001、AIFI-ARCH-009、AIFI-QA-003 等独立任务和当轮 scope lock 约束。

### AIFI-TRACE-001 BMAD C-ID traceability registration

- 背景：BMAD PRD 包含 C-001 到 C-054 的确认、拒绝和后置项，需要进入唯一需求追踪入口，避免 planning artifact 直接变成执行依据。
- 范围：登记 C-ID 状态、目标 active docs、BACKLOG 承接和关闭条件；显式标注 C-049 到 C-054 Deferred。
- 非目标：不把 BMAD C-ID 标为已实现，不把 Deferred 项改写成 MERGED / ACCEPTED，不从 brief 或 addendum 替代 PRD §13.2 / traceability 主证据。
- PRD 来源：`_bmad-output/planning-artifacts/PRD.md` §13.2、`brief-traceability.md`；工程规划来源：`.omo/plans/bmad-feedback-loop-refactor-planning.md`。
- 验收标准：`REQUIREMENT_TRACEABILITY.md` 可追踪 C-001 到 C-054；Rejected / Deferred 项不会出现在可开工实现范围；C-048 / BR-024 不关闭 C-054。
- 完成证据：Todo 2 证据确认 `REQUIREMENT_TRACEABILITY.md` 已建立 `### 5.1 C-001 到 C-054 单项追踪矩阵`，`matrix_block=present`、`rows=54`、`missing=`、`duplicate=`、`unexpected=` 且 `forbidden_matches=0`。
- 边界：Rejected / Deferred 边界保持；C-049 到 C-054 仍为 Deferred / Open Question，不进入 implementation start scope；C-048 / BR-024 只关闭产品排序规则，不关闭 C-054 的具体算法。
- 依赖：AIFI-PROD-011。
- 是否阻塞后续实现：否。C-ID 追踪登记已完成；后续实现仍受 AIFI-ARCH-009、AIFI-QA-003、AIFI-BE-009、AIFI-FE-002、AIFI-REL-008 等独立任务和当轮 scope lock 约束。

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

### AIFI-QA-004 Feedback acceptance semantics tests

- 背景：`.omo/plans/plan.md` Step 1 要求先把 feedback 验收语义落成可运行测试，避免后续后端/前端实现各自解释“有效反馈”“失败折叠”“追问/下一题”语义。
- 范围：新增或更新 feedback acceptance semantics pytest，只负责 feedback acceptance semantics tests 的首批护栏，覆盖 AC-001、AC-002、AC-003、AC-012。
- 非目标：不实现后端业务逻辑、不修改前端、不创建迁移、不改变 API schema、不关闭 C-049 到 C-054。AC-004 到 AC-011、AC-013 到 AC-015 由后续 BE / FE / QA / REL steps 承接。
- 允许修改路径：`tests/api/test_polish_feedback_acceptance_semantics.py`；必要时可补充同目录下命名清晰的 `tests/api/test_polish_feedback_*acceptance*.py` 测试文件。
- 禁止修改路径：`apps/**`；`apps/api/migrations/**`；`apps/web/**`；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-PROD-011；AIFI-TRACE-001；当前 BACKLOG 授权入口；当轮 scope lock 明确允许写 `tests/api/**`。`AIFI-QA-003` 可作为 QA 语义参考上下文，但不是 AIFI-QA-004 的硬阻塞依赖。
- 验收标准：
  - `tests/api/test_polish_feedback_acceptance_semantics.py` 能被单独运行。
  - 测试名称、断言注释或 evidence 必须可追踪到 AC-001、AC-002、AC-003、AC-012。
  - AC-004 到 AC-011、AC-013 到 AC-015 不属于 AIFI-QA-004 的完成范围，必须由后续对应 implementation / QA / release steps 承接。
  - 测试必须显式断言 C-049 到 C-054 仍为 Deferred / Open Question。
  - 失败断言允许先红后绿，不得通过 mock 直接绕过业务契约。
- 对应 plan.md Step：Step 1。
- 主要对应 PRD AC：AC-001、AC-002、AC-003、AC-012。
- 参考 PRD 范围：FR-001 到 FR-064、BR-001 到 BR-024 仅作为语义上下文，不构成 AIFI-QA-004 的全量覆盖承诺。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务只把 Deferred guard 写入测试，不把相似度阈值、持久化表、UI 形态、错误枚举、刷新恢复状态机或下一题算法升级为已决策。

#### Step 1 Execution Result

* Result：`ACCEPTED_RED`
* Execution date：2026-06-24
* Plan step：`.omo/plans/plan.md` Step 1 - 验收语义硬化与测试矩阵冻结
* AIFI：`AIFI-QA-004`
* Test command：`PYTHONPATH=.:apps/api python -m pytest -p no:cacheprovider tests/api/test_polish_feedback_acceptance_semantics.py -q`
* Current result：`2 failed, 3 passed`

Accepted RED failures：

* AC-001：同题同答稳定性 RED。当前实现的 score band 超过允许范围，属于实现缺口，不是测试装配错误。
* AC-003：参考答案回灌 RED。当前实现的 replay score 低于高分预期，属于实现缺口，不是测试装配错误。

Current interpretation：

* Step 1 已产出首批 feedback acceptance semantics tests。
* 当前 RED 结果作为后续实现的验收护栏被接受。
* Step 1 没有修改后端业务实现、前端、migration、配置、依赖或 API schema。
* Step 1 只覆盖 AC-001、AC-002、AC-003、AC-012 的首批测试护栏。
* AC-004 到 AC-011、AC-013 到 AC-015 由后续 BE / FE / QA / REL steps 承接。
* C-049 到 C-054 仍保持 `Deferred / Open Question`。
* Step 1 不授权 Step 2；Step 2 必须重新执行 scope lock。

Downstream handling：

* AC-001 RED 由后续 feedback stability / scoring consistency implementation 承接。
* AC-003 RED 由后续 reference-answer replay / scoring consistency implementation 承接。
* AC-002 和 AC-012 的当前测试结果按 pytest 输出记录，不扩大为全量 PRD 通过声明。

### AIFI-BE-010 Effective feedback state and compatibility

- 背景：`.omo/plans/plan.md` Step 2 要求后端有单一 effective feedback state，并能兼容旧 feedback payload、pending/failed 状态和只读投影，防止旧数据在 API 与 progress 之间表现不一致。Step 5 中 current effective feedback selector 与本任务兼容，但完整 Step5 implementation 由 AIFI-BE-015 承接。
- 范围：本任务只授权 Step2 的 effective feedback state、feedback history、failure record exclusion、old payload compatibility、read-time projection，以及与该范围直接相关的 tests/api；允许为 scope lock 做 Step2-A 材料补齐和代码事实探查。
- 非目标：不授权 Step3 fail-closed validation；不授权 Step4 same-answer stability implementation；不授权 Step5 improvement trend implementation；不授权 Step6 progress mastery；不授权 Step7 question generation；不授权 FE、migration 或 release。
- 允许修改路径：`apps/api/app/application/polish/**`；`apps/api/app/schemas/polish.py`；`apps/api/app/infrastructure/db/repositories/polish.py`；相关 `tests/api/test_polish_feedback*_compatibility*.py`、`tests/api/test_polish_effective_feedback_state.py`、`tests/api/test_polish_api.py` 中限定 feedback state/compatibility 的测试。
- 禁止修改路径：`apps/api/migrations/**`；`apps/web/**`；非 polish 后端模块；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-QA-004。AIFI-BE-009 仅作为参考上下文，AIFI-BE-009=NOT_STARTED 不再硬阻塞 AIFI-BE-010；Step2-A 必须在 AIFI-BE-010 内完成材料补齐、代码事实探查和 scope lock，并在 scope lock 中重新列出 allowed paths / forbidden paths。
- 验收标准：旧 payload、无 feedback payload、pending/failed/succeeded 状态都有稳定投影；API 返回不破坏既有字段；effective feedback selector 只选当前有效反馈；相关兼容测试通过；未引入迁移。
- 对应 plan.md Step：Step 2；Step 5 中 current effective feedback selector 的兼容依赖；Step 8 中与 feedback state/schema 兼容有关的 API envelope。本任务不授权 Step5 improvement trend implementation。
- 对应 PRD AC / FR / BR：AC-004、AC-005、AC-006、AC-012、AC-013；FR-006 到 FR-011、FR-024、FR-026、FR-027、FR-039 到 FR-047、FR-058 到 FR-061；BR-009、BR-010、BR-016 到 BR-023。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务可实现兼容状态字段和投影，但不关闭 C-050、C-052、C-053，也不决定 C-049、C-051、C-054。

#### Step 2 closeout

- 最终状态：DONE / CLOSED。Step 2 / AIFI-BE-010 effective feedback selector 已通过 closeout 并提交。
- commit：`763ad98668535998bb7c16ad32e08d7bae1bc94a`（`fix(polish-api): project effective feedback state`）。
- evidence：`.omo/evidence/plan/step2-closeout.md` 记录 `result=PASS`。
- 已完成范围：latest valid generated feedback 作为 current effective feedback；failed feedback 不覆盖 valid feedback；legacy JSON / plain-text payload 可兼容读取；failure record 不参与 effective feedback / score / recommendation。
- 明确不覆盖：Step5 improvement trend、Step6 progress mastery、Step7 question generation / similarity interception、FE、migration、release、C-049 到 C-054 关闭。

### AIFI-BE-011 Fail-closed feedback validation

- 背景：`.omo/plans/plan.md` Step 3 要求 feedback 生成失败、校验失败或 payload 不完整时必须 fail-closed，避免把无效反馈当作可完成、可掌握或可追问依据。
- 范围：仅授权 `.omo/plans/plan.md` Step 3：BE 反馈生成 fail-closed 与 payload validator。实现 feedback generation service、feedback validation、feedback projection、feedback models 和 application service 中的 payload validation、invalid / malformed / inconsistent feedback fail-closed、safe failure payload、retryable terminal failure，以及 session detail 不把失败 payload 当作 generated feedback 的行为；把 invalid / failed / pending 的投影和错误语义写入 tests/api。
- 非目标：不授权 Step 4 same-answer stability、Step 5 improvement trend、Step 6 progress mastery、Step 7 question generation、FE、migration、release；不改 UI 呈现；不新增错误枚举的最终产品决策；不改变 LLM provider；不吞掉已有异常可观测性。
- 允许修改路径：`apps/api/app/application/polish/feedback_application_service.py`；`apps/api/app/application/polish/feedback_generation_service.py`；`apps/api/app/application/polish/feedback_validation.py`；`apps/api/app/application/polish/feedback_projection.py`；`apps/api/app/application/polish/feedback_models.py`；`tests/api/test_polish_feedback_failure_contract.py`；`tests/api/test_polish_feedback_runtime.py`；必要的 `tests/api/test_polish_*feedback*.py` 中限定 Step 3 fail-closed / payload validator 的测试。
- 禁止修改路径：`apps/api/migrations/**`；`apps/web/**`；非 polish 后端模块；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-BE-010；AIFI-QA-004。
- 验收标准：无效 feedback payload 不会产生 mastered/progress completion；失败状态有稳定投影；safe failure payload 不暴露 raw prompt / raw completion / provider payload；retryable terminal failure 可被 API/session detail 安全读取；session detail 不把失败 payload 当作 generated feedback；旧兼容字段不被破坏；失败路径测试覆盖 validation、generation runtime 和 API 输出；日志或错误对象不暴露敏感 prompt。
- 对应 plan.md Step：Step 3：BE 反馈生成 fail-closed 与 payload validator；Step 8 中失败 envelope 和 schema 兼容。
- 对应 PRD AC / FR / BR：AC-012、AC-013、AC-015；FR-005、FR-058 到 FR-064；BR-009、BR-010、BR-021、BR-023。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务只固化 fail-closed 行为，不把 C-052 的最终错误枚举或 C-053 的刷新恢复状态机改为已决策。

#### Step 3 final closeout

- 最终状态：DONE。Step 3 / AIFI-BE-011 closeout 已由 `FAIL_CHECK_ENV` 修正为 `PASS`；环境阻断已解除。
- 证据：`ef1391c` 已提交 Step 3 fail-closed feedback validation 实现；`.omo/evidence/plan/step3-final-closeout.md` 记录 Step3 review-work 结论为 PASS；`.omo/evidence/plan/step3-env-closeout.md` 记录 exact pytest 在未设置 `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS` 时通过，关键输出为 `31 passed in 9.33s`。
- supersede：旧 `.omo/evidence/plan/step3-closeout.md` 保留为历史 evidence，其中 `FAIL_CHECK_ENV` 结论已被 `.omo/evidence/plan/step3-final-closeout.md` supersede。
- 边界：本 closeout 不授权 Step 4 same-answer stability、Step 5 improvement trend、Step 6 progress mastery、Step 7 question generation、FE、migration 或 release；C-049 到 C-054 仍保持 Deferred / Open Question。

### AIFI-BE-012 Same-answer stability and reference-answer replay

- 背景：`.omo/plans/plan.md` Step 4 要求同一答案重复生成 feedback 时评分、参考答案 replay 和 scoring normalization 不漂移，避免用户看到同题同答结果不一致。
- 范围：只授权 Step 4：same-answer stability、reference-answer replay、scoring normalization 和相关 tests/api。
- 非目标：不授权 Step5 improvement trend；不授权 Step6 progress mastery；不授权 Step7 question generation；不改 FE；不新增 migration；不做 release；不更换 LLM provider；不把评分算法扩展到未登记业务域。
- 允许修改路径：`apps/api/app/application/polish/**` 中 feedback runtime、scoring normalization、reference answer replay 相关文件；允许创建 `tests/api/test_polish_feedback_stability.py`；允许修改与 Step 4 直接相关的 `tests/api/test_polish_feedback_generation_service.py`、`tests/api/test_polish_feedback_runtime.py`。
- 禁止修改路径：`apps/api/migrations/**`；`apps/web/**`；非 polish 后端模块；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-BE-010；AIFI-BE-011；AIFI-QA-004。
- 验收标准：同答案重复执行时评分归一化稳定；reference answer replay 不丢失；相关 tests/api 覆盖 repeat answer、old payload、invalid payload 和 fake LLM fixture；本任务不验收 Step5 improvement trend。
- 对应 plan.md Step：Step 4。不包括 Step 5 improvement trend。
- 对应 PRD AC / FR / BR：AC-001、AC-002、AC-003、AC-004、AC-005；FR-012 到 FR-018、FR-024、FR-039 到 FR-047；BR-007、BR-008、BR-016 到 BR-020。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务不决定相似度阈值、考察点与题目绑定模型、失败记录折叠最终样式、错误枚举最终映射、刷新恢复状态机或下一题算法；仅确保 Step 4 已授权 feedback runtime 的稳定性。

#### Step 4 closeout

- 最终状态：DONE / CLOSED。Step 4 / AIFI-BE-012 已通过 review-work PASS 并提交。
- commit：`2e82dbfbc8f23d0c09cd784a94190dceecc36732`（`feat(aifi): close step4 feedback stability`）。
- evidence：`.omo/evidence/step4-aifi-be-012-review-work-pass.md` 记录 Step4 review-work PASS；`.omo/evidence/plan/step4-ulw-loop-closeout.md` 状态为 PASS。
- 已完成范围：AC-001 同题同答稳定性；AC-003 参考答案回灌高分自洽；Step2 effective feedback selector / 兼容投影回归不回退；Step3 fail-closed validation 回归不回退。
- 未完成且不得被误认为完成的范围：Step5 improvement trend；Step6 progress mastery；Step7 question generation / similarity interception；FE 改造；migration；release；C-049 到 C-054 仍保持 Deferred / Open Question。

### AIFI-BE-015 Improved-answer trend calibration and effective-result consistency

- 背景：`.omo/plans/plan.md` Step 5 要求改进回答后的评分趋势应上升，并要求 current effective feedback result 不因历史失败态或旧结果回退。现有 AIFI-BE-010 只覆盖 effective feedback state / compatibility / selector 局部，且明确不授权 Step5 improvement trend implementation，因此不得强行复用 AIFI-BE-010 承接完整 Step5。
- 范围：只授权 Step 5：improved-answer trend calibration、score_delta / dimension_delta 投影、derived_improvement_summary / derived_remaining_gap_summary / derived_regression_summary 的安全派生、current effective feedback result 一致性、failure record 不回退 current effective feedback、与 Step2 effective feedback selector、Step3 fail-closed validation、Step4 same-answer stability / reference replay 的兼容。
- 非目标：不授权 Step6 progress mastery；不授权 Step7 next-question generation / similarity interception；不改 FE；不新增 migration；不做 release；不关闭 C-049 到 C-054；不更换 LLM provider；不把 Step5 的趋势策略扩展成长期能力画像或训练建议算法。
- 允许修改路径：`apps/api/app/application/polish/**` 中 feedback trend、effective feedback result、score delta、payload projection 相关文件；`apps/api/app/schemas/polish.py` 中与 Step5 结果兼容的 additive 字段；`apps/api/app/infrastructure/db/repositories/polish.py` 中 current effective result 读取/投影相关最小调整；`tests/api/test_polish_feedback_improvement_trend.py`；`tests/api/test_polish_effective_feedback_state.py`；`tests/api/test_polish_feedback_stability.py`；`tests/api/test_polish_feedback_failure_contract.py`；必要的 `tests/api/test_polish_api.py` 中限定 Step5 effective result / trend consistency 的测试。
- 禁止修改路径：`apps/api/migrations/**`；`apps/web/**`；非 polish 后端模块；配置文件；依赖文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-BE-010；AIFI-BE-011；AIFI-BE-012；AIFI-QA-004；Step4 commit `2e82dbfbc8f23d0c09cd784a94190dceecc36732`；Step4 review-work PASS。
- 验收标准：改进回答后评分趋势在 Step1 AC-002 语义矩阵允许窗口内上升；current effective feedback result 始终指向 latest valid feedback；失败、pending、invalid 或旧 payload 不会回退 current effective result；不破坏 AC-001 同题同答稳定性；不破坏 AC-003 参考答案回灌；不破坏 Step3 fail-closed；相关 tests/api 通过。
- 对应 plan.md Step：Step 5。
- 对应 PRD AC / FR / BR：主要对应 AC-002；兼容 AC-001、AC-003、AC-004、AC-012、AC-013；FR-012 到 FR-018、FR-024、FR-039 到 FR-047、FR-058 到 FR-061；BR-007 到 BR-010、BR-016 到 BR-023。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务只建立 Step5 改进趋势和 current effective result 一致性，不决定相似度阈值、考察点与题目绑定模型、失败记录折叠最终样式、错误枚举最终映射、刷新恢复状态机或下一题算法。

#### Step 5 closeout

- 最终状态：DONE / CLOSED。Step 5 / AIFI-BE-015 已通过 closeout 并提交。
- commit：`ef95d4a9139d4c0f41593a6c9c57897d533aca0b`（`feat(aifi): close step5 feedback trend`）。
- evidence：`.omo/evidence/plan/step5-implementation-closeout.md` 记录 Step5 implementation closeout，`.omo/` 路径为 ignored evidence，不替代 active docs；本节只登记 active docs closeout 状态。
- 已完成范围：improved-answer trend calibration、score_delta / dimension_delta 投影、derived improvement / remaining gap / regression summary、安全 current effective feedback result consistency、failure record 不回退 current effective feedback、Step2 / Step3 / Step4 兼容回归。
- 未完成且不得被误认为完成的范围：Step6 progress mastery、Step7 next-question generation / similarity interception、FE 改造、migration、release、C-049 到 C-054 关闭。

### AIFI-BE-013 Progress mastery and manual completion consistency

- 背景：`.omo/plans/plan.md` Step 6 要求 progress mastery、manual completion 和有效 feedback 状态一致，避免无效 feedback 推动进度或手动完成覆盖真实状态。
- 范围：实现或调整 progress 更新、polish use cases、manual completion 行为和有效 feedback selector 之间的一致性；补充相关 tests/api。
- 非目标：不实现下一题算法；不改前端交互；不新增迁移；不关闭 C-053。
- 允许修改路径：`apps/api/app/application/polish/**`；`apps/api/app/schemas/polish.py` 中 progress/manual completion 相关字段；相关 `tests/api/test_polish_progress*.py`、`tests/api/test_polish_api.py`。
- 禁止修改路径：`apps/api/migrations/**`；`apps/web/**`；非 polish 后端模块；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-BE-010；AIFI-BE-012；AIFI-BE-015；AIFI-QA-004。
- 验收标准：只有有效 feedback 能推动 mastery/progress；manual completion 与 feedback invalid/failed/pending 状态不冲突；repeat answer 和旧 payload 场景保持兼容；相关 tests/api 通过。
- 对应 plan.md Step：Step 6。
- 对应 PRD AC / FR / BR：AC-004 到 AC-008、AC-013；FR-024、FR-026 到 FR-031、FR-039 到 FR-047；BR-007、BR-016 到 BR-023。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务实现 progress 一致性，但不关闭 C-050、C-052、C-053，也不决定 C-049、C-051、C-054。

#### Step 6 canonicalization and scope-lock readiness

- canonical Step6 BE：AIFI-BE-013。
- rejected drift ID：AIFI-BE-016。当前 BACKLOG 不新增 AIFI-BE-016，AIFI-BE-016 不得作为 Step6 scope lock、实现或测试入口。
- Step5 依赖状态：AIFI-BE-015 已 DONE / CLOSED；Step6 不再因 Step5 active-doc closeout 缺失而阻断。
- authorization_status：READY_TO_START。
- 允许重新执行 Step6 scope lock：YES。
- 当前授权边界：本状态只允许重新执行 Step6 scope lock；scope lock 返回 `execution_mode=AUTHORIZED` 前，不授权代码、测试、FE、migration、release 或 Step7 行为。

### AIFI-BE-014 Follow-up and next-question behavior

- 背景：`.omo/plans/plan.md` Step 7 要求追问、下一题、progress 绑定和相似度拦截按同一 feedback/progress 状态运行，避免相同错误被重复追问或下一题绕过 mastery。
- 范围：实现或调整 question generation、follow-up、next-question、progress binding 和 similarity interception 相关后端行为；补充 tests/api。
- 非目标：不最终确定 C-049 相似度阈值；不最终确定 C-054 下一题算法；不改前端 UI；不新增迁移。
- 允许修改路径：`apps/api/app/application/polish/**` 中 question generation、progress binding、similarity interception 相关文件；`apps/api/app/api/v1/polish.py` 中与现有 polish API envelope 兼容的最小调整；相关 `tests/api/test_polish_question*.py`、`tests/api/test_polish_followup*.py`、`tests/api/test_polish_api.py`。
- 禁止修改路径：`apps/api/migrations/**`；`apps/web/**`；非 polish 后端模块；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-BE-013；AIFI-BE-010；AIFI-QA-004。
- 验收标准：follow-up 和 next-question 使用有效 feedback/progress；相似度拦截有保守默认和测试护栏；manual completion 后不会生成冲突追问；API envelope 与旧调用兼容；相关 tests/api 通过。
- 对应 plan.md Step：Step 7；Step 8 中 follow-up / next-question envelope。
- 对应 PRD AC / FR / BR：AC-009、AC-010、AC-011、AC-014；FR-019 到 FR-023、FR-032 到 FR-038、FR-048 到 FR-057；BR-011 到 BR-014、BR-024。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务只建立保守行为和测试护栏，不把 C-049 阈值或 C-054 算法标记为最终决策。

### AIFI-FE-003 Feedback view model and failure folding

- 背景：`.omo/plans/plan.md` Step 9 要求前端先在 `entities/polish` 层把 feedback payload、有效状态、失败折叠和旧 payload 容错统一为 view model，再交给页面呈现。
- 范围：实现或调整 polish entity types/API/view model/parser，使前端能处理 succeeded、pending、failed、invalid、legacy payload 和缺失字段；补充 FE tests。
- 非目标：不改 `InterviewPage.tsx` 页面交互；不定义最终视觉样式；不改后端；不关闭 C-051 或 C-053。
- 允许修改路径：`apps/web/src/entities/polish/**`；同目录或现有 FE 测试目录下的相关 `*.test.ts`、`*.test.tsx`。
- 禁止修改路径：`apps/web/src/pages/interview/InterviewPage.tsx`；`apps/api/**`；`tests/api/**`；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-BE-010；AIFI-BE-011；AIFI-BE-014；AIFI-FE-002；AIFI-QA-004。
- 验收标准：view model 对旧 payload 和失败 payload 有稳定输出；缺失字段不导致渲染异常；错误折叠不会伪装为成功 feedback；相关 FE tests 或 typecheck 覆盖核心转换。
- 对应 plan.md Step：Step 8 中前端 schema/type 适配；Step 9。
- 对应 PRD AC / FR / BR：AC-012、AC-013、AC-015；FR-002 到 FR-005、FR-008 到 FR-010、FR-023 到 FR-031、FR-060 到 FR-064；BR-009、BR-010、BR-021、BR-023。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务不决定最终 UI 形态或刷新恢复状态机，只提供可兼容的数据视图模型。

### AIFI-FE-004 Interview workbench interaction and refresh recovery

- 背景：`.omo/plans/plan.md` Step 10 和 Step 11 要求面试页基于 view model 呈现 feedback、失败折叠、重试/刷新恢复和手动完成一致状态，并保留页面级 QA 证据。
- 范围：实现或调整 `InterviewPage.tsx` 的 feedback 展示、重试、刷新恢复、manual completion 和 next-question/follow-up 交互；补充相关 FE tests 或页面 smoke 证据。
- 非目标：不改 `entities/polish` contract 以外的后端；不创建新的设计系统；不最终关闭 C-051 或 C-053；不声明 release-ready。
- 允许修改路径：`apps/web/src/pages/interview/InterviewPage.tsx`；同目录或现有 FE 测试目录下与 InterviewPage 相关的 `*.test.ts`、`*.test.tsx`；必要时仅修改页面邻近的测试 fixture。
- 禁止修改路径：`apps/api/**`；`tests/api/**`；`apps/web/src/entities/polish/**` 中超出 AIFI-FE-003 contract 的改动；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-FE-003；AIFI-BE-010；AIFI-BE-011；AIFI-BE-012；AIFI-BE-015；AIFI-BE-013；AIFI-BE-014；AIFI-QA-004。
- 验收标准：成功、pending、failed、invalid、legacy feedback 均有一致页面状态；刷新后不丢失有效 feedback；失败折叠不遮蔽可恢复动作；页面 smoke 或 FE tests 记录 Step 11 的关键路径。
- 对应 plan.md Step：Step 10；Step 11 中页面集成与 smoke evidence。
- 对应 PRD AC / FR / BR：AC-012、AC-013、AC-014、AC-015；FR-001、FR-019 到 FR-025、FR-027 到 FR-031、FR-052、FR-060、FR-061；BR-021 到 BR-023。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务只实现页面行为和恢复护栏，不把 C-051 UI 形态或 C-053 刷新恢复状态机升格为最终产品决策。

### AIFI-REL-009 Feedback-loop release gate and rollback checklist

- 背景：`.omo/plans/plan.md` Step 12 要求在实现完成后有明确 release gate、rollback checklist、QA evidence 和未满足项，避免把部分通过的 feedback-loop 声明为可发布。
- 范围：更新 release docs、runbook、QA evidence docs，记录 Step 1 到 Step 11 的测试命令、结果、回滚策略、降级策略和 release blocker。
- 非目标：不改业务代码；不改测试代码；不创建新 roadmap 或并行计划入口；不把 `_bmad-output` 或 `.omo/plans` 变成 active docs。
- 允许修改路径：`docs/03-implementation/**` 中 release checklist、runbook、QA evidence、test plan 类 active docs；必要时同步 `docs/00-governance/DOCS_INDEX.md` 中新增 active doc 登记。
- 禁止修改路径：`apps/**`；`tests/**`；`apps/api/migrations/**`；配置文件；`archive/**`；`_bmad-output/**`；`.omo/plans/**`。
- 依赖：AIFI-QA-004；AIFI-BE-010；AIFI-BE-011；AIFI-BE-012；AIFI-BE-015；AIFI-BE-013；AIFI-BE-014；AIFI-FE-003；AIFI-FE-004；AIFI-REL-008。
- 验收标准：release gate 明确 PASS/FAIL 条件；rollback 和 degradation checklist 可执行；QA evidence 记录测试命令、结果和未覆盖风险；未完成项不会被写成 release-ready；如新增 active doc 已登记到 DOCS_INDEX。
- 对应 plan.md Step：Step 11 中集成 evidence 汇总；Step 12。
- 对应 PRD AC / FR / BR：AC-001 到 AC-015；NFR-001 到 NFR-008；BR-001 到 BR-024。
- C-049 到 C-054 是否仍保持 Deferred：是。该任务只登记 release gate 和回滚条件，不关闭任何 Deferred / Open Question；若后续要关闭，必须另走 active PRD / traceability / BACKLOG 决策入口。

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
