---
title: DOCS02_DEEP_SEMANTIC_AUDIT_REPORT
type: review
status: pending
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/reviews/docs02-deep-semantic-audit-report
---

# docs/02 设计体系深度语义关联审计报告

## 审计边界

- task_id: `AIFI-ARCH-006`
- 阶段: `F4`
- 里程碑: `M4`
- 审计目标: 审计 `docs/02-design` active 设计文档之间的 PRD -> UX -> UI -> TECH -> DATA -> API -> PROMPT -> SECURITY -> F5 -> F8 语义链路是否闭合，并检查历史审计问题是否系统性复发。
- 审计对象: `UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`TECH_DESIGN.md`、`DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`prompt-contracts/*.md`、上游 `PRD.md` / `REQUIREMENT_TRACEABILITY.md`、下游 `DELIVERY_PLAN.md` / `BACKLOG.md`、前序 F4 review 产物。
- 允许写入: `BACKLOG.md`、`DOCS_INDEX.md`、本轮 `DOCS02_DEEP_SEMANTIC_*` 审计产物。
- 禁止写入: active design docs、product docs、`DELIVERY_PLAN.md`、`archive/**`、`.spec-workflow/specs/**`、业务代码、package / lock / config 文件、roadmap / plan-v2 / latest-plan / codex-plan。
- MCP: 仅允许 Spec Workflow MCP `approvals`。
- 多 Agent: 已使用 11 个审计角色输出独立结论。
- 完成条件: 形成 30 条业务能力语义链路矩阵、AR-DOCS02-SEM finding、风险登记表、整改矩阵和 Pending 验收记录；不修复 active design docs。

## 实际读取范围

### 治理入口

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/AI_WORKFLOW.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`

### 上游和下游依据

- `docs/01-product/PRD.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`

### docs/02 active 设计文档

- `docs/02-design/UX_SPEC.md`
- `docs/02-design/UI_DESIGN_SYSTEM.md`
- `docs/02-design/TECH_DESIGN.md`
- `docs/02-design/DATA_MODEL.md`
- `docs/02-design/API_SPEC.md`
- `docs/02-design/PROMPT_SPEC.md`
- `docs/02-design/SECURITY_PRIVACY.md`

### Prompt contract 子文档

- `docs/02-design/prompt-contracts/ASSET_CONTRACTS.md`
- `docs/02-design/prompt-contracts/JOB_MATCH_CONTRACTS.md`
- `docs/02-design/prompt-contracts/POLISH_CONTRACTS.md`
- `docs/02-design/prompt-contracts/PRESSURE_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REVIEW_CONTRACTS.md`
- `docs/02-design/prompt-contracts/SHARED_CONTRACTS.md`
- `docs/02-design/prompt-contracts/TRAINING_CONTRACTS.md`
- `docs/02-design/prompt-contracts/WEAKNESS_CONTRACTS.md`

### 前序审计产物

- `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_ADVERSARIAL_REVIEW.md`
- `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_RISK_REGISTER.md`
- `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_REMEDIATION_MATRIX.md`
- `docs/02-design/reviews/F4_PROMPT_SECURITY_TECH_ACCEPTANCE.md`
- `docs/02-design/reviews/F4_FULL_DESIGN_ADVERSARIAL_REVIEW.md`
- `docs/02-design/reviews/F4_FULL_DESIGN_RISK_REGISTER.md`
- `docs/02-design/reviews/F4_FULL_DESIGN_REMEDIATION_MATRIX.md`
- `docs/02-design/reviews/F4_FULL_DESIGN_ACCEPTANCE.md`
- `docs/02-design/reviews/F4_TO_F8_READINESS_AUDIT_REPORT.md`
- `docs/02-design/reviews/F4_TO_F8_READINESS_RISK_REGISTER.md`
- `docs/02-design/reviews/F4_TO_F8_READINESS_REMEDIATION_MATRIX.md`
- `docs/02-design/reviews/F4_TO_F8_READINESS_ACCEPTANCE.md`

## 前序审计问题复盘

### AIFI-ARCH-004 暴露的问题

- `F4_TECH_DESIGN` UNKNOWN 未真正关闭，review 证据无法替代 active design docs 的事实回写。
- `API_SPEC.md` 曾经骨架化，无法支撑 F5/F6/F7 直接进入实现、接入和测试。
- 评分、通过倾向、风险提示和校准口径未冻结，容易被实现阶段自行发明。
- Report contract 重新引入 Markdown 下载 / 文件导出语义，冲突于 PRD 非目标和 copy-only 边界。
- Prompt / Security / Tech 横向一致性不足，尤其是 LLM 输入、输出、审计、复制和正式事实写入边界。

### AIFI-ARCH-005 暴露的问题

- `API_SPEC.md` 缺逐接口字段级 contract。
- `DATA_MODEL.md` 缺 idempotency / task / trace / persistence 承接。
- 缺 F6 页面到 API / 状态 / 错误态接入矩阵。
- 缺 F8 发布 / 运维 / 复盘交接依据。
- Resume API 错误引入 `modules[]` / project-experience module CRUD。
- Job list/detail 缺 `binding_summary` / `latest_match_summary`。
- Polish mode 缺 topic / subtopic 选择 contract，`binding_id` 语义不清。
- docs/02 英文过多，中文化时误改 API path / 技术标识符。

### 根因总结

1. 审计过度依赖机械结构检查。
2. 缺少 PRD -> UX -> API -> DATA -> PROMPT -> SECURITY 的语义链路检查。
3. 缺少“页面任务需要什么，API 是否直接提供”的检查。
4. 缺少“API 字段是否能被 DATA 持久化”的检查。
5. 缺少“Prompt 输出是否能被 API / DATA 承接”的检查。
6. 缺少“中文正文优先但技术标识符不可翻译”的防护检查。

## 多角色独立结论

| 角色 | 结论 | 关键证据 / 判断 |
|---|---|---|
| Product Semantics Auditor | BLOCKED | 产品语义大体承接，但压力面动作边界、Job/JD 字段展示、复盘列表等仍存在 UX/API/DATA 断点。 |
| UX / UI Handoff Auditor | BLOCKED | 绑定解绑、复盘列表、复盘复制、低置信校对保存、内容沉淀目标会迫使 F6 猜 endpoint 或状态。 |
| API Semantics Auditor | BLOCKED | 未发现 Resume module CRUD、project-experience API 资源和 path 中文化复发；但解绑 API、`source_unavailable` 读写语义、`binding_id` alias 仍不稳。 |
| Data Semantics Auditor | BLOCKED | 数据层没有过度把项目经历建模成独立资源；但 typed ref、`UserConfirmationRef`、Prompt/API 状态映射和 F8 release data 仍未完全闭合。 |
| Prompt Semantics Auditor | BLOCKED | 48 个 `P-*` contract 已登记且未发现新 ID；但 Prompt status、`source_availability`、输出对象名和 API/DATA 承接仍漂移。 |
| Security Semantics Auditor | BLOCKED | owner、no export、LLM 后端隔离大体成立；但 copy event 返回复制内容、真实复盘敏感输入和 raw LLM trace 仍有语义风险。 |
| F5 Backend Readiness Auditor | BLOCKED | F5 contract 面基本可实现，但 F4->F8 readiness 仍 Pending，`AR-F4-F8-003` Open，不能正式启动。 |
| F6 Frontend Readiness Auditor | BLOCKED | Job summary 和 topic/subtopic 可消费；解绑、复盘列表、复盘复制、低置信校对、内容沉淀 target schema 阻断 F6。 |
| F7 QA Readiness Auditor | BLOCKED | 多数断言可测；复盘列表和岗位解绑缺可调用 API / 字段级状态，且 acceptance 仍 Pending。 |
| F8 Release Readiness Auditor | BLOCKED | `AR-F4-F8-003` 仍 Open；release checklist、runbook、rollback、observability、Deferred->Backlog 映射不足。 |
| Documentation Governance Auditor | BLOCKED | `DOCS_INDEX.md` 和 `BACKLOG.md` 与当前 F4 文档 / review 状态漂移；本轮已登记 AIFI-ARCH-006 和四份 review 产物。 |

## 语义链路矩阵

| 业务能力 | PRD 需求 | UX 页面 / 交互 | UI / 状态要求 | TECH 模块 | DATA 对象 / 状态 | API 接口 / Schema | PROMPT Contract | SECURITY 边界 | F5 实现依据 | F6 接入依据 | F7 测试断言 | F8 发布 / 复盘依据 | 缺口 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Markdown 简历创建 / 编辑 | 有，Markdown paste/edit | 简历编辑 | 表单、保存、错误态 | Resume service | `Resume` / version | Resume CRUD | 不直接生成 | owner、no upload | 可实现 | 可接入 | 可测保存/owner | 需发布输入 | OK |
| 简历版本和历史引用 | 有，历史引用不破坏 | 版本/历史引用 | 历史提示 | Version/trace | `VersionRef` / `SnapshotRef` | refs in response | source refs | audit trace | 可实现 | 可展示 | 可测引用稳定 | 需 release trace | OK |
| 简历中的项目经历作为 Markdown 内容片段 | 有，随简历处理 | 简历内编辑 | Markdown 区块 | Resume derived outline | derived outline | 无独立 project CRUD | 可作为 source | no separate upload | 可实现 | 可展示 | 可测无独立 CRUD | 需守护 | OK |
| 岗位 / JD 手动创建 / 编辑 | 有，手动录入 | Job form/detail | 表单状态 | Job service | `Job` | Job create/update/detail | 可供 job match | owner | 可实现 | 字段需对齐 | 可测 CRUD | 需发布输入 | Medium: Job/JD 字段如 department/other 在 API read model 中仍需复核 |
| 岗位绑定简历 | 有，绑定/解绑 | 绑定/解绑 | loading/error/success | Binding service | `JobResumeBinding` active/unbinding/unbound | 仅 create 清楚 | 不直接生成 | owner/cross-user | 缺解绑实现 contract | 解绑需猜 | 解绑不可测 | 影响 release checklist | High: AR-DOCS02-SEM-001 |
| 岗位匹配分析 | 有 | 详情进入分析 | 分析状态 | Job match service | `JobMatchAnalysis` | match task/result | `P-JOBMATCH-*` | source minimization | 可实现 | 可接入 | 可测 score/explain | 需 metrics | OK |
| 岗位列表 / 详情展示绑定摘要和最新匹配摘要 | 有 | Job list/detail | summary cards | Job read model | `JobBindingSummary` / `JobMatchSummary` | list/detail summary | 不直接生成 | owner | 可实现 | 大体可接入 | 可测 summary | 需 release smoke | Medium: 绑定数量、字段完整度需统一 |
| 打磨模式主题 / 次主题选择 | 有，多主题 | topic/subtopic selector | 选择/空态 | Polish service | `PolishTopicRef` | `GET /api/v1/polish-topics` | `P-POLISH-*` | owner | 可实现 | 可接入 | 可测 topic | 需 release fixture | OK |
| 打磨模式题目生成 | 有 | 工作台生成 | task 状态 | AI orchestration | Question/task | AI task result | Polish question contracts | LLM minimization | 可实现 | 可接入 | 可测 async | provider runbook 缺 | Medium: F8 运维依赖 AR-DOCS02-SEM-003 |
| 打磨模式回答保存 | 有 | 回答输入保存 | draft/saved/error | Answer service | Answer/session | Answer APIs | 反馈输入 | sensitive logs | 可实现 | 可接入 | 可测 save | 需 release smoke | OK |
| 打磨模式反馈 / 评分 / 参考回答 / 考点解析 | 有 | feedback card | score/reference/explanation | Feedback service | Feedback + reference answer | feedback result | Polish feedback contracts | no exact probability | 可实现 | 可接入 | 可测 scoring boundary | 需 metrics | Medium: API/DATA/PROMPT 输出对象需统一 |
| 压力面模式会话 | 有，真实节奏 | Pressure workbench | session state | Pressure service | Session | Pressure APIs | `P-PRESSURE-*` | LLM minimization | 可实现 | 可接入 | 可测 session | provider runbook 缺 | OK |
| 压力面题目生成和追问 | 有，连续追问 | 追问交互 | question/follow-up | AI orchestration | Question/follow-up | task/result | Pressure contracts | source minimization | 可实现 | 可接入 | 可测 follow-up | 需 metrics | OK |
| 压力面整场评分 | 有 | session score | score summary | Scoring service | score result | pressure score | Pressure scoring | no exact probability | 可实现 | 可接入 | 可测 score | 需 metrics | OK |
| 进展树 | 有 | progress tree | node state | Progress service | progress nodes | progress read APIs | 不直接生成或作为输入 | owner | 可实现 | 可接入 | 可测 state | 需 release smoke | OK |
| 面试报告 | 有 | report detail | report cards | Report service | Report | report APIs | `P-REPORT-*` | copy-only/no export | 可实现 | 可接入 | 可测 no export | 需 release known limitations | OK |
| 报告 copy content | 有，只复制内容 | copy action | copy feedback | Report copy service | Copy event | report copy content / copy event | 不生成导出物 | audit no正文 | 可实现但需收敛 | 可接入报告 | 可测 copy boundary | 需 audit metrics | High: AR-DOCS02-SEM-002 |
| 模拟面试复盘 | 有 | review create/detail | review state | Review service | Review | review create/detail | `P-REVIEW-*` | sensitive logs | 可实现 | 缺 list 支撑 | list 不可测 | release smoke 不足 | High: AR-DOCS02-SEM-001 |
| 真实面试复盘输入 | 有，用户确认输入 | review input | sensitive input | Review service | Review input | review create | Review contracts | third-party PII/prompt injection | 可实现但需补安全字段 | 可接入需提示 | 可测部分安全 | 需 known limitations | High: AR-DOCS02-SEM-002 |
| 真实面试复盘结果 | 有 | review result | result cards | Review service | Review result | review detail/result | Review output | no silent formal write | 可实现 | 可接入 | 可测 result | 需 metrics | Medium: review list/copy 仍缺 |
| 资产库 | 有 | asset library | list/detail | Asset service | Asset | asset APIs | asset suggestion/input | owner | 可实现 | 可接入 | 可测 owner | 需 release smoke | OK |
| 资产候选确认 | 有，不静默写正式事实 | confirm drawer | pending/confirmed | Confirmation service | Candidate/Suggestion/Confirmation/Asset | confirm candidate | `P-ASSET-*` | audit/actor | 可实现 | 可接入 | 可测 no silent write | 需 audit metrics | High: AR-DOCS02-SEM-002 |
| 薄弱项 | 有 | weakness list/detail | status/merge | Weakness service | Weakness | weakness APIs | `P-WEAKNESS-*` | owner | 可实现 | 可接入 | 可测 lifecycle | 需 release smoke | OK |
| 薄弱项候选确认 / 合并 | 有 | confirm/merge | confirm state | Confirmation service | Candidate/Weakness | confirm/merge | Weakness contracts | audit/actor | 可实现 | 可接入 | 可测 confirm/merge | 需 audit metrics | High: AR-DOCS02-SEM-002 |
| 训练建议 | 有 | training recommendation | suggestion state | Training service | TrainingRecommendation | training APIs | `P-TRAINING-*` | no silent formal write | 可实现 | 可接入 | 可测 candidate->formal | 需 release smoke | OK |
| AI task status / result / retry / cancel | 有异常状态 | task indicator | running/retry/cancel | AI task service | AiTask/AiTaskResult | task endpoints | shared contracts | provider isolation | 可实现 | 可接入 | 可测 async | provider runbook 缺 | High: AR-DOCS02-SEM-003 |
| 评分、风险提示、通过倾向 | 有，非精确概率 | score/risk display | disclaimer | Scoring service | ScoreResult | score schema | scoring contracts | no exact probability | 可实现 | 可接入 | 可测 no exact prob | 需 known limitations | OK |
| low confidence / source unavailable / validation failed / generation failed | 有异常态 | correction/retry flows | banner/drawer | AI/status service | source/status refs | status/error schemas | shared failure signals | logs minimized | 部分可实现 | correction save 需补 | 部分不可测 | ops input 不足 | High: AR-DOCS02-SEM-002 |
| owner boundary / cross-user protection | 有权限边界 | 所有页面 | forbidden/error | auth boundary | owner refs | owner scoped APIs | source minimization | cross-user denial | 可实现 | 可接入 | 可测 403/404 | audit metrics 需补 | OK |
| no export / no upload / no exact probability | 有非目标 | 无导出/上传入口 | copy-only display | design guardrail | 无 export artifact | no export/upload endpoints | no exact prob contracts | copy boundary | 可实现 | 可接入 | 可测 negative | known limitations 需补 | OK |

## 历史高风险项复发检查

| 高风险项 | 本轮判断 |
|---|---|
| Resume module CRUD 复发 | 未复发，当前仍以 Markdown 简历和 derived outline 表达。 |
| project-experience 被误建成 API 资源 | 未复发，未发现独立 project-experience CRUD。 |
| `source_availability` 被滥用到普通 CRUD | 部分风险，主要集中在 read-vs-generate 语义和 Prompt/API 枚举映射。 |
| `binding_id` 语义不清 | 仍有风险，`binding_id` / `resume_job_binding_id` / `binding_ref` alias 需要统一。 |
| Job list/detail 缺绑定和匹配摘要 | 已部分修复，但绑定数量和字段完整度仍需收敛。 |
| Polish topic / subtopic 缺接口或 schema | 未复发，已有 `GET /api/v1/polish-topics`。 |
| API path 被中文化破坏 | 未发现。 |
| API 清单与逐接口详情不一致 | 局部存在，尤其 review list、unbind 和 copy route。 |
| API 字段未被 DATA 承接 | 仍有风险，typed ref、confirmation、status/source availability 映射需统一。 |
| Prompt 输出未被 API/DATA 承接 | 仍有风险，Prompt 输出对象、状态、action taxonomy 需要映射到 API/DATA。 |
| API 引入 non-goal | 未发现 export/upload/exact probability 主路径复发，但 copy event 返回内容需收敛。 |
| F6 页面需二次拼接核心信息 | 仍有风险，review list、correction save、content deposition targets。 |
| F7 assertion 只有名字 | 局部存在，解绑和复盘列表不可测。 |
| F8 release / ops / retrospective 口号化 | 仍存在，`AR-F4-F8-003` Open。 |
| 中文化后技术标识符被误改 | 未发现 API path 被误改，但 review 英文结构标题仍多。 |
| docs/02 review 文件被误当作 active source | 仍需治理提醒，review 只能作为证据，不替代 active docs。 |

## Findings

## AR-DOCS02-SEM-001: UX 可见任务到 API / DATA 交接仍有断链

Severity: High  
Category: Product Semantics / UX Handoff / API / Data / F6 / F7  
Source Documents:
- `docs/01-product/PRD.md` §岗位绑定、复盘、报告复制、低置信度校对、内容沉淀
- `docs/02-design/UX_SPEC.md` §岗位绑定、复盘列表、低置信度校对、内容沉淀确认
- `docs/02-design/UI_DESIGN_SYSTEM.md` §复盘入口、复制反馈、低置信度校对状态
- `docs/02-design/API_SPEC.md` §API inventory、resume-job-bindings、reviews、copy content、confirmation flow
- `docs/02-design/DATA_MODEL.md` §JobResumeBinding、UserConfirmation、content deposition targets
Affected Chain:
- PRD -> UX -> UI -> TECH -> DATA -> API -> PROMPT -> SECURITY -> F5 -> F6 -> F7 -> F8
Affected Phase:
- F4 / F5 / F6 / F7 / F8
Status: Open

### Claim Under Review

当前 docs/02 active design docs 已足以让 F6 直接按页面任务接入 API，并让 F7 为所有核心页面任务生成可调用、可断言的测试。

### Semantic Gap

多个用户可见任务在 UX/UI 中已经成立，但 API/DATA 尚未提供直接、字段级、状态级承接。最明显的是岗位解绑、面试复盘列表、复盘复制、低置信度校对保存、内容沉淀到 polish input / pressure input / next simulation input 等目标级写入。

### Cross-document Evidence

- PRD / UX 要求岗位绑定和解绑；DATA 有 `active` / `unbinding` / `unbound` / `failed` 状态；API 只清楚定义 `POST /api/v1/resume-job-bindings` 创建绑定，缺解绑 endpoint、幂等、错误态和 F7 assertion。
- PRD / UX / UI 要求复盘列表、筛选、排序、分页和列表入口；API 只有 create 与 `GET /api/v1/reviews/{review_id}`，缺 `GET /api/v1/reviews` 与 `ReviewSummary[]`。
- PRD / UI / Security 允许复制复盘授权内容并审计；API copy route 主要绑定 report，review copy 边界未单独表达。
- UX / UI 要求低置信度校对抽屉和保存；DATA 要求用户校正产生 confirmation/correction record；API 主要提供展示 flags 和 next actions，缺通用 correction save contract。
- UX / DATA 要求内容沉淀到资产、弱点、训练建议、打磨输入、压力输入、下次模拟输入；API 仅清楚覆盖 Asset/Weakness/Training 候选确认，缺其他 target schema。

### Why It Matters

F6 会被迫从多个接口拼接核心页面信息或自行猜测 route、状态、错误态和确认流；F7 无法为解绑、复盘列表、复盘复制和低置信校对保存形成可执行断言；F5 也会在实现时补发明接口语义。

### Required Fix

必须回写到 `API_SPEC.md`、`DATA_MODEL.md`、必要的 `UX_SPEC.md` / `UI_DESIGN_SYSTEM.md` 页面状态矩阵，并补齐与 `SECURITY_PRIVACY.md` 的 copy / audit 边界。若涉及 Prompt 输出或候选确认动作，还需同步 `PROMPT_SPEC.md` 与对应 `prompt-contracts/*.md`。

### Acceptance Condition

每个 UX 页面核心动作都能映射到一个明确 API route、request / response schema、状态枚举、错误态、owner 断言、幂等或版本处理规则；F6 不需要自行拼接核心信息；F7 能为解绑、复盘列表、复盘复制、低置信校对保存和内容沉淀目标写出可执行测试。

## AR-DOCS02-SEM-002: API / DATA / PROMPT / SECURITY 的字段级语义仍未完全归一

Severity: High  
Category: API / Data / Prompt / Security / F5 / F6 / F7  
Source Documents:
- `docs/02-design/API_SPEC.md` §Shared schemas、copy content、confirmation flow、source availability、review APIs
- `docs/02-design/DATA_MODEL.md` §Reference model、UserConfirmationRef、AiTaskResultRef、LlmResponseTrace
- `docs/02-design/PROMPT_SPEC.md` §Output status、SourceAvailability、AI task contract registry
- `docs/02-design/SECURITY_PRIVACY.md` §copy boundary、LLM input minimization、real interview review、audit logging
- `docs/02-design/prompt-contracts/*.md` §Report / Review / Asset / Weakness / Training contract outputs
Affected Chain:
- PRD -> UX -> UI -> TECH -> DATA -> API -> PROMPT -> SECURITY -> F5 -> F6 -> F7 -> F8
Affected Phase:
- F4 / F5 / F6 / F7 / F8
Status: Open

### Claim Under Review

当前 API、DATA、PROMPT 和 SECURITY 已用同一套字段、状态、引用、审计和正式事实写入语义表达 AI 输出和用户确认流。

### Semantic Gap

Prompt contract、API schema、DATA reference model 和 SECURITY logging/copy boundary 之间仍有字段级语义漂移。典型问题包括 `success` / `succeeded`、`source_availability` enum 取值不一致，`UserConfirmationRef` 在 DATA 与 API 中字段不一致，typed ref 与 `TraceRef` 使用边界不清，copy event 返回复制内容与“审计不记录正文”边界冲突，真实复盘输入的第三方敏感信息、prompt injection、trust/completeness flags 未被 API/Prompt 全量承接。

### Cross-document Evidence

- `PROMPT_SPEC.md` 定义 canonical failure signals 和 `source_unavailable`，但部分 prompt-contract 输出仍使用 `success` / `partial` / `low_confidence` 与 `available` / `partial` / `unavailable` / `mixed`，API task status 又使用另一组状态。
- `DATA_MODEL.md` 要求 `UserConfirmationRef` 包含 owner、actor、target_type、before/after summary、confirmed_at、trace_ref；`API_SPEC.md` 的 shared schema 中字段更少且更偏 generic `target_ref`。
- `DATA_MODEL.md` 定义 candidate / suggestion / confirmation / formal object 隔离；API 和 Prompt 对 next actions、confirmation target、formal write 的名称和字段仍需统一。
- `SECURITY_PRIVACY.md` 要求 copy audit 不记录正文；API copy event response 又返回 `clipboard_blocks[]`，容易把 copy content 与 audit event 混在同一个安全边界里。
- `SECURITY_PRIVACY.md` 对真实面试复盘输入提出第三方敏感信息、prompt injection 和 trust/completeness 风险；API / Prompt 侧没有稳定字段矩阵证明这些风险被输入校验、日志脱敏和输出提示承接。

### Why It Matters

F5 会在实现 shared schema、AI task、confirmation flow 和 audit log 时自行选择哪个文档为准；F6 会拿到不稳定状态和 action 名称；F7 的测试 fixture 不能证明 Prompt 输出能被 API/DATA 安全落地；Security 不能证明复制、真实复盘和 LLM trace 不泄漏敏感正文或 provider payload。

### Required Fix

必须回写到 `API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md` 和相关 `prompt-contracts/*.md`，建立统一 status enum、source availability enum、typed ref schema、confirmation ref schema、copy content vs copy event 分层、real interview review sensitive input flags 与 LLM trace 最小化规则。

### Acceptance Condition

任意 Prompt contract 输出字段都能映射到 API response / task result / DATA object；任意 API shared schema 都能映射到 DATA model；copy event 不返回或记录正文；真实面试复盘输入有明确 trust/completeness/sensitive/injection flags；F7 能用同一组 enum 和 typed refs 编写 contract tests。

## AR-DOCS02-SEM-003: F8 发布 / 运维 / 复盘交接和治理事实源仍未闭合

Severity: High  
Category: F8 / Governance / Security / API / Data  
Source Documents:
- `docs/03-delivery/DELIVERY_PLAN.md` §F8
- `docs/03-delivery/BACKLOG.md` §AIFI-REL-001、AIFI-ARCH-002 至 AIFI-ARCH-006
- `docs/00-governance/DOCS_INDEX.md` §当前有效入口
- `docs/02-design/reviews/F4_TO_F8_READINESS_RISK_REGISTER.md` §AR-F4-F8-003
- `docs/02-design/API_SPEC.md` §Non-goals / Observability boundary
- `docs/02-design/SECURITY_PRIVACY.md` §Deferred security / privacy items
Affected Chain:
- PRD -> UX -> UI -> TECH -> DATA -> API -> PROMPT -> SECURITY -> F5 -> F6 -> F7 -> F8
Affected Phase:
- F4 / F5 / F6 / F7 / F8
Status: Open

### Claim Under Review

当前 docs/02 active design docs 和 review 产物已足以支撑 F8 发布准备、运维手册、known limitations、rollback/migration、observability 和 retrospective 输入。

### Semantic Gap

`AR-F4-F8-003` 仍保持 Open，且本轮未发现 active docs 已补齐 F8 release checklist matrix、runbook、rollback/migration、observability、provider failure runbook、Deferred->Backlog 映射和 release retrospective metrics。治理层面还存在 `DOCS_INDEX.md` / `BACKLOG.md` 与当前 active docs、review Verified/Pending 状态漂移的问题，可能让 F5/F6/F7/F8 误判启动条件。

### Cross-document Evidence

- `DELIVERY_PLAN.md` 要求 F8 产出 release checklist、changelog、发布复盘 ADR / Issue，并清零发布阻塞项。
- `BACKLOG.md` 中 `AIFI-REL-001` 仍是粗粒度发布检查任务，尚未承接 hard delete、backup restore、KMS/DPA、WAF、audit console、provider protocol、observability、rollback/migration 等 deferred 项。
- `F4_TO_F8_READINESS_RISK_REGISTER.md` 中 `AR-F4-F8-003` 仍为 Open，直接指向 release checklist、runbook、known limitations、rollback/migration、observability 和 Deferred->Backlog 映射缺失。
- `API_SPEC.md` 定义 request_id / trace_id / rate limit meta，但也明确日志平台、监控告警和部署拓扑不属于 API contract。
- `SECURITY_PRIVACY.md` 定义 soft delete、retention、copy boundary 和 audit，但 hard delete、备份即时删除、KMS/DPA、WAF、审计检索台、provider 协议和告警策略仍为 Deferred。
- `DOCS_INDEX.md` 和 `BACKLOG.md` 中部分 F4 active docs / review 状态表述仍与当前工作树中的已扩展 API/DATA/PROMPT/SECURITY 内容和 Pending readiness 结论不同步。

### Why It Matters

即使 F5/F6/F7 局部可以实现和测试，F8 仍无法形成发布清单、运维手册、可观测性指标、回滚策略、known limitations 和复盘输入。治理事实源漂移还会让 review 文件被误当作 active design source，或让 Pending readiness 被误解成 Accepted。

### Required Fix

必须回写到 `TECH_DESIGN.md`、`API_SPEC.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`BACKLOG.md` 和 `DOCS_INDEX.md`。如需调整前序 review 的 current-state banner，必须单独授权，不得在本轮修改前序审计产物。

### Acceptance Condition

`AR-F4-F8-003` 或其后续 remediation 在 active docs 中有可验证闭环；F8 release checklist 可从 API/DATA/SECURITY/Prompt/Backlog 生成；Deferred 安全/隐私/运维项映射到 Backlog、Accepted_Risk 或明确非目标；`DOCS_INDEX.md` 和 `BACKLOG.md` 不再给出相互冲突的启动状态。

## Readiness 判定

| 阶段 | 判定 | 原因 |
|---|---|---|
| F5 | BLOCKED | F5 contract 面多数可实现，但 `AR-DOCS02-SEM-001` / `002` 仍会迫使后端发明局部 API/schema，且 F4->F8 readiness 尚 Pending。 |
| F6 | BLOCKED | 解绑、复盘列表、复盘复制、低置信校对保存、内容沉淀目标仍缺直接接入依据。 |
| F7 | BLOCKED | 解绑和复盘列表缺可执行断言；status / source availability / confirmation schema 仍需统一。 |
| F8 | BLOCKED | `AR-F4-F8-003` 与本轮 `AR-DOCS02-SEM-003` 均指向 release / ops / retrospective 输入不足。 |

