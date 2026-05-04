---
title: BACKLOG
type: delivery-backlog
status: active-f1
owner: 项目交付
source_report: archive/2026-05-doc-consolidation/audit/F0_AUDIT_REPORT.md
permalink: ai-for-interviewer/docs/03-delivery/backlog
---

# BACKLOG

本文件是唯一任务入口。所有任务必须使用 `AIFI-*` 编号；优先级只使用 `MUST`、`SHOULD`、`COULD`、`LATER`；阶段只引用 `F0` 至 `F8`。本文件不设置批次、波次或发布批次字段，任务承接只通过阶段、里程碑、优先级、依赖、验收和状态表达。

## 1. Backlog

| 任务 ID | 阶段 | 里程碑 | 优先级 | 标题 | 范围 | 产物 | 依赖 | 状态 |
|---|---|---|---|---|---|---|---|---|
| AIFI-DOC-001 | F0 | M0 | MUST | 建立目标文档索引 | 新建/改写 `DOCS_INDEX.md`，登记唯一有效文档体系 | `docs/00-governance/DOCS_INDEX.md` | F0 审计 | DONE |
| AIFI-DOC-002 | F0 | M0 | MUST | 合并归档台账 | 新建 `archive/MANIFEST.md`，合并旧归档索引与台账 | `archive/MANIFEST.md` | `DOCS_INDEX.md` | DONE |
| AIFI-DOC-003 | F0 | M0 | MUST | 废弃旧 active 入口 | 将旧 planning/task/module/state 文档迁入 archive 并登记替代路径 | README、AGENTS、`archive/MANIFEST.md` | F0.1 归档 | DONE |
| AIFI-DOC-004 | F0 | M0 | MUST | 清理重复模板文档 | 旧模板和旧治理文档转为历史来源 | `archive/2026-05-doc-consolidation/legacy/` | F0.1 归档 | DONE |
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
| AIFI-UX-001 | F2 | M2 | MUST | 准备 F2 低保真设计输入 | 已创建 `docs/02-design/UX_SPEC.md`；基于 PRD 的用户故事、核心业务数据流、功能逻辑、输入 / 输出、状态异常和验收标准完成低保真 UX 规范；已按最新产品交互口径修正简历、岗位、模拟面试、面试复盘、薄弱项场景，覆盖简历 Markdown 编辑、岗位手动录入表单、岗位详情模块化展示、模拟面试列表与详情、面试报告无一级入口、面试复盘列表与新增复盘、薄弱项多选发起打磨模式、资产库、内容沉淀确认和低置信度校对；本轮结构性返修已补充列表主态 / 抽屉态拆分、状态 Frame 不遮挡主体、表格最大承载、分页条数选择、操作列图标、表头筛选下拉扩展区、打磨 / 压力面工作台四区布局、用户设置入口、发起模拟面试抽屉或弹窗、新增面试复盘抽屉或弹窗、薄弱项多选自动带出和内容沉淀确认；本轮细节返修已补充操作列图标基础态清晰、无双层文字 / 字母、分页每页条数以下拉方式表达、表头筛选 / 排序图标化、用户区包含头像、角色和设置入口；本轮组件基线返修已建立 F2 低保真组件基线，并要求 Figma 页面按组件基线统一；本轮质量返修已要求 F2 低保真组件基线不得出现重叠、溢出和越界，进展树已按多维进展模型修正，分页、操作列、抽屉和表格尺寸比例已统一；本轮人工可读性返修已补充无文字溢出、无图标越界、无说明遮挡主体、无组件互相重叠、应用壳用户区布局稳定、进展树节点与说明不重叠、打磨模式回答后决策闭环和进展树任意节点生成题目流程；本轮清理重建已补充不允许 overlay 修正、旧问题节点必须删除、组件区和页面引用必须一致、Figma 必须通过人工可读性检查；本轮组件基线精修已补充 F2 低保真组件基线达到可评审线框稿质量、组件区和页面引用一致、打磨模式反馈卡片和下一步建议固定区完成、聊天窗口滚动与反馈卡片折叠规则完成；本轮质量闸门修复及继续返修复核已补充用户设置抽屉内容完整、抽屉态底层列表可读、组件区与页面引用关键尺寸一致、列表承载密度与分页语义一致、工作台反馈卡片无重叠、备份 Page 有效或明确风险；表格、分页、操作列、筛选、排序、抽屉、状态、用户区、聊天工作台均复用低保真组件基线；每个核心功能都具备布局、流程、交互、状态和 Figma 交付要求，可直接指导 Figma 低保真；已在 Figma Page `AiForInterviewer - F2 Low Fidelity` 重新落图；未新增页面代号体系，未设计精确通过概率展示 | `docs/02-design/UX_SPEC.md` | F1 完成 | DONE |
| AIFI-UX-002 | F2 | M2 | MUST | 关闭 F2 UX-blocking UNKNOWN | 已在 `docs/02-design/UX_SPEC.md` 中关闭所有 `F2_UX_BLOCKING` 和必须在 F2 确认的 `HUMAN_CONFIRMATION`；低保真交互不再依赖分散表格，功能场景能直接指导 Figma；本轮结构性返修已重新审视 OQ-F1-035，将低保真 Frame 建议命名为内容沉淀确认抽屉态，并明确产品目的、目标集合、目标级状态、用户确认、编辑、跳过和失败重试；已要求列表 / 抽屉拆分为主态与抽屉态，状态页不遮挡主体，工作台按四区聊天窗口结构重画；覆盖多简历多岗位绑定、岗位状态、岗位手动录入表单、打磨主题完成、内容沉淀确认、低置信度校对、资产更新确认、缺失增强输入提示、压力面节奏、进展树展示层级、报告复盘展示和报告复制反馈；OQ-F1-006 已在 F1 关闭，F2 只设计岗位手动录入表单；OQ-F1-035 已在内容沉淀确认功能场景中完整关闭，目标覆盖资产库、薄弱项、训练建议、打磨模式输入、压力面模式输入和下一次模拟面试输入，目标级状态可测试，且明确不得自动静默写入；OQ-F1-040 保留给 F4/F7；未新增页面代号体系 | `docs/02-design/UX_SPEC.md` | AIFI-UX-001、AIFI-PROD-010 | DONE |
| AIFI-UI-001 | F3 | M3 | MUST | 编写 UI 设计系统 | 迁移有效视觉原则，补组件、页面规范和设计 token，服务 F2 已冻结的 PRD 核心需求 | `docs/02-design/UI_DESIGN_SYSTEM.md` | F2 评审 | NOT_STARTED |
| AIFI-ARCH-001 | F4 | M4 | MUST | 准备 F4 技术设计输入 | 基于 PRD 的业务对象、核心业务数据流、规则约束、状态异常、验收标准和 UNKNOWN，结合当前仓库事实冻结技术架构、服务边界、进展树、薄弱项、岗位匹配、评分、面试复盘、题目推荐和资产边界；除非后续 PRD 变更，项目经历随简历处理 | `docs/02-design/TECH_DESIGN.md`、ADR | F1/F2 | NOT_STARTED |
| AIFI-ARCH-002 | F4 | M4 | MUST | 关闭 F4 技术设计 UNKNOWN | 基于 PRD §10 关闭所有 `F4_TECH_DESIGN`，覆盖评分公式、权重、阈值、评分校准方法、低置信度、通过倾向 / 风险提示展示边界、可信度说明、免责声明、版本策略、资产合并、输入优先级、题目推荐、暂停恢复、进展树数据结构、Prompt、模型选择、模型调用参数、复盘切分、薄弱项算法和安全边界 | `TECH_DESIGN.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`API_SPEC.md`、`SECURITY_PRIVACY.md` | AIFI-ARCH-001、AIFI-DATA-001、AIFI-PROMPT-001、AIFI-SEC-001 | NOT_STARTED |
| AIFI-API-001 | F4 | M4 | MUST | 编写 API 契约 | 汇总岗位、简历、岗位绑定、岗位匹配分析、打磨模式、资产、双模式模拟面试、面试报告、面试复盘、报告内容复制边界、训练、权限 API | `docs/02-design/API_SPEC.md` | AIFI-ARCH-001 | NOT_STARTED |
| AIFI-DATA-001 | F4 | M4 | MUST | 编写数据模型 | 汇总简历、简历中的项目经历模块、岗位 / JD、岗位与简历绑定关系、岗位匹配分析结果、匹配度评分、匹配点、不匹配点、加强点、打磨模式记录、面试复盘记录、资产库、模拟面试会话、题目、回答、点评、评分、失分点、参考回答、考点解析、进展树、暂停恢复状态、薄弱项、训练建议和资产库回流关系；除非后续 PRD 变更，不把项目建成独立一级数据对象 | `docs/02-design/DATA_MODEL.md` | AIFI-PROD-003、AIFI-PROD-004、AIFI-PROD-007、AIFI-PROD-008、AIFI-PROD-009 | NOT_STARTED |
| AIFI-PROMPT-001 | F4 | M4 | MUST | 编写 Prompt 规范 | 写入参考材料包、资产库消费、打磨模式出题、压力面模式出题和追问、考点规划、问题生成、点评、打分、失分原因、参考回答、考点解析、技术原理扩展、面试报告、模拟面试复盘、薄弱项提炼、岗位匹配分析、匹配度打分、匹配点、不匹配点、加强点分析、岗位匹配分析提炼薄弱项、低置信度规则和通过倾向 / 风险提示表达边界 | `docs/02-design/PROMPT_SPEC.md` | AIFI-PROD-004、AIFI-PROD-005、AIFI-PROD-007、AIFI-PROD-008 | NOT_STARTED |
| AIFI-SEC-001 | F4 | M4 | MUST | 编写安全隐私规范 | 权限、数据可见性、审计、脱敏、保留周期、报告复制内容边界、可信度说明和资产访问边界 | `docs/02-design/SECURITY_PRIVACY.md` | AIFI-PROD-003 | NOT_STARTED |
| AIFI-BE-001 | F5 | M5 | MUST | 完成后端核心链路 | 实现服务端保存、简历中的项目经历模块、打磨模式记录、面试复盘、资产沉淀和读取、资产驱动模拟面试输入、打磨模式会话、压力面模式会话、面试报告生成、模拟面试复盘、真实面试复盘、薄弱项提炼、打磨模式暂停与恢复状态、岗位绑定简历、岗位匹配度分析、0-100 评分展示所需结果、匹配点、不匹配点、加强点生成、从岗位匹配分析中提炼薄弱项、RAG/LLM、评分复盘、报告内容复制所需内容读取能力 | 后端实现、API 测试 | F4 评审通过 | NOT_STARTED |
| AIFI-FE-001 | F6 | M6 | MUST | 完成前端核心链路 | 实现工作台、简历、简历中的项目经历模块、岗位 / JD、岗位绑定简历、岗位匹配分析、资产库、打磨模式、压力面模式、进展树、面试报告、报告内容复制、模拟面试复盘、真实面试复盘、薄弱项、训练建议、暂停恢复、反馈回流和异常状态页面 | 前端实现、页面测试 | F5 主接口可用 | NOT_STARTED |
| AIFI-QA-001 | F7 | M7 | MUST | 完成全链路测试 | 验证 PRD 中的用户故事、核心业务数据流、功能逻辑、输入 / 输出、状态异常和验收标准，包括简历、简历中的项目经历模块、岗位 / JD、岗位绑定简历、岗位匹配分析、0-100 评分展示、资产库、打磨模式、压力面模式、进展树、面试报告、报告内容复制、无文件导出入口、模拟面试复盘、真实面试复盘、薄弱项、训练建议和反馈回流 | `docs/03-delivery/TEST_PLAN.md`、测试报告 | F5/F6 | NOT_STARTED |
| AIFI-QA-002 | F7 | M7 | MUST | 验证 UNKNOWN 关闭状态 | 在测试计划和测试报告中确认 PRD §10 中所有影响验收的 UNKNOWN 已关闭、已转为明确测试断言或已按产品原因排除出 MVP 阻塞范围；重点验证 0-100 展示、无精确通过概率承诺、风险提示不误导用户 | `docs/03-delivery/TEST_PLAN.md`、测试报告 | AIFI-QA-001、AIFI-UX-002、AIFI-ARCH-002 | NOT_STARTED |
| AIFI-REL-001 | F8 | M8 | MUST | 完成发布检查 | 发布清单、变更记录、已知问题、回滚策略，并确认 PRD 核心需求无遗漏 | `docs/03-delivery/RELEASE_CHECKLIST.md`、`CHANGELOG.md` | F7 全链路通过 | NOT_STARTED |

## 2. 优先级定义

| 优先级 | 定义 |
|---|---|
| MUST | 没有它不能发布 |
| SHOULD | MVP 强相关，但不阻塞发布 |
| COULD | 可选优化 |
| LATER | 下一轮迭代 |

## 3. 旧任务迁移规则

1. 旧任务包只作为历史来源或归档证据，不得直接作为当前任务入口。
2. 每个仍有效的旧任务必须映射到一个 `AIFI-*` 任务。
3. 无法证明仍有效的旧任务标记为 `UNKNOWN`，待核查后再进入 Backlog。
4. 模块级待办不得绕过本文件直接执行。
