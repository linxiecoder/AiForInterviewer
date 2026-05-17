---
title: F4_TO_F8_READINESS_ACCEPTANCE
type: acceptance-record
status: active-f4
source_task: AIFI-ARCH-005
permalink: ai-for-interviewer/design/reviews/f4-to-f8-readiness-acceptance
---

# F4→F8 交接就绪性验收记录

状态：Pending

本验收记录不得写 Accepted。本轮只记录严格审计结果和已授权单 finding 整改状态；active 设计文档的修复完成不等于最终验收。

整改更新：`AR-F4-F8-001` 已通过定向复核并标记为 Verified；`AR-F4-F8-002` 已通过定向复核并标记为 Verified；`AR-F4-F8-004`、`AR-F4-F8-005`、`AR-F4-F8-006` 已通过本轮定向复核并标记为 Verified；`AR-F4-F8-007` 已通过中文优先文档治理定向复核并标记为 Verified；`AR-F4-F8-008` 已通过 API path / 技术标识符原样性定向复核并标记为 Verified；`AR-F4-F8-003` 保持 Open。本文件整体 `状态` 仍为 `Pending`，不得作为 Accepted 结论。

## 1. 审计范围

- F4 active design docs：`TECH_DESIGN.md`、`DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`
- Prompt contract 子文档：`docs/02-design/prompt-contracts/*.md` 下 9 个 `.md` 文件
- 后续阶段依据：`DELIVERY_PLAN.md`、`BACKLOG.md`
- 上游辅助输入：`PRD.md`、`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`
- 前序审计 evidence：`F4_PROMPT_SECURITY_TECH_*`、`F4_FULL_DESIGN_*`

## 2. 就绪性结论

| 阶段 | 结论 | 是否允许启动 |
|---|---|---|
| F5 就绪性结论 | AR-F4-F8-001_VERIFIED；AR-F4-F8-004_VERIFIED；AR-F4-F8-005_VERIFIED；AR-F4-F8-006_VERIFIED；AR-F4-F8-007_VERIFIED；AR-F4-F8-008_VERIFIED。上述 finding 不再阻断 F5 API / DATA / Prompt handoff；但整体 `状态` 仍为 `Pending`，不得作为 F4 Accepted 或 F5 正式启动审批。 | 否 |
| F6 就绪性结论 | AR-F4-F8-002_VERIFIED；AR-F4-F8-004_VERIFIED；AR-F4-F8-005_VERIFIED；AR-F4-F8-006_VERIFIED；AR-F4-F8-007_VERIFIED；AR-F4-F8-008_VERIFIED。Job summary、Resume Markdown-only、Polish topic/subtopic 和中文优先文档治理已可作为 F6 接入输入；但整体 `状态` 仍为 `Pending`，不得作为 F4 Accepted 或 F6 正式启动审批。 | 否 |
| F7 就绪性结论 | API 契约测试和页面 assertions 有 Verified 基线；AR-F4-F8-004 / 005 / 006 的新增 F7 assertions 已定向复核，AR-F4-F8-007 中文优先治理已复核；但本文件整体 `状态` 仍为 `Pending`，不得作为 F7 正式启动审批。 | 否 |
| F8 就绪性结论 | BLOCKED。缺 release checklist 来源矩阵、runbook、known limitations、rollback / migration、observability 和 Deferred→Backlog 映射。 | 否 |

## 3. Finding 统计

| 严重度 | 未关闭数量 |
|---|---:|
| Critical | 0 |
| High | 1 |
| Medium | 0 |
| Low | 0 |

已验证 finding：

- `AR-F4-F8-001` High: API_SPEC / DATA_MODEL 字段级 contract 和幂等 / task / trace / persistence 承接已通过定向复核，标记为 Verified；整体验收仍为 Pending。
- `AR-F4-F8-002` High: F6 页面到 API / 状态 / 错误态接入矩阵已通过定向复核，标记为 Verified；整体验收仍为 Pending。
- `AR-F4-F8-004` High: Resume API Markdown-only、无 project-experience module CRUD、无 `modules[]`、普通 Resume CRUD 不使用 `source_availability` 已通过定向复核，标记为 Verified；整体验收仍为 Pending。
- `AR-F4-F8-005` High: Job list/detail 的 `binding_summary` / `latest_match_summary`、summary 状态域、评分版本字段和 no exact probability 边界已通过定向复核，标记为 Verified；整体验收仍为 Pending。
- `AR-F4-F8-006` High: Polish topic/subtopic、`resume_job_binding_id`、`GET /api/v1/polish-topics`、F6 surface、F7 tests 和 `custom_topic_text` prompt injection 防护已通过定向复核，标记为 Verified；整体验收仍为 Pending。
- `AR-F4-F8-007` Medium: `docs/02-design` 中文优先治理和技术标识符保留已通过定向复核，标记为 Verified；整体验收仍为 Pending。
- `AR-F4-F8-008` High: API path / 技术标识符原样性已通过定向复核，API 清单总表与逐接口详情 Method + Path 一致，标记为 Verified；整体验收仍为 Pending。

已修复但待复核 finding：无。

未关闭 finding（Open findings）：

- `AR-F4-F8-003` High: 缺少 F8 发布 / 运维 / 复盘交接依据。

## 4. 启动判定

| 判定项 | 结论 |
|---|---|
| 是否允许 F5 启动 | 否。AR-F4-F8-001/004/005/006/007/008 不再阻断 API / DATA / Prompt 实现交接；但整体验收仍为 Pending，本记录不作为 F4 Accepted 或 F5 正式启动审批。 |
| 是否允许 F6 启动 | 否。本记录整体仍为 Pending，且未创建 F4 accepted / F6 阶段启动审批；AR-F4-F8-002/004/005/006/007/008 已可作为 F6 页面接入准备输入。 |
| 是否允许 F7 规划测试 | 否。本记录整体仍为 Pending，不能作为正式 F7 启动审批；AR-F4-F8-004/005/006 的新增 F7 assertions 与 AR-F4-F8-007 中文优先治理已定向复核通过。 |
| 是否允许 F8 发布准备 | 否 |

## 5. 需要人工决策项

1. 是否在整体 `状态：Pending` 且 `AR-F4-F8-003` 仍 Open 的情况下，允许 F5 仅基于已 Verified 的 API / DATA / Prompt contract 做后续准备；本记录不作为 F5 正式启动审批。
2. 是否授权后续 remediation 修改 `API_SPEC.md`、`DATA_MODEL.md`、`TECH_DESIGN.md`、`SECURITY_PRIVACY.md` 和必要的 `BACKLOG.md`。
3. 是否在整体 `状态：Pending` 且 `AR-F4-F8-003` 仍 Open 的情况下，允许 F6 仅基于已 Verified 的页面接入矩阵、Job summary、Resume Markdown-only 和 Polish topic/subtopic contract 做 mock adapter、状态处理和 E2E fixture 准备；本记录不作为 F6 正式启动审批。
4. 是否将 `AR-F4-F8-003` 的 Deferred / release ops 项拆入后续 AIFI-* Backlog，或逐项标记 Accepted_Risk。
5. 是否保留前序 `AIFI-ARCH-004` 的 Verified finding 状态，同时明确其不等于本轮 F4→F8 readiness Accepted。
6. PRD / UX 中“展示主要简历模块”“维护项目经历”等上游产品口径是否需要改写为 Markdown-only + derived outline 表述；本轮不修改 PRD / UX，仅按人工审计决策执行 F4 API / DATA / Prompt 修复。

## 6. 定向复核：AR-F4-F8-001

状态：Verified

| 检查项 | 结果 | 证据 |
|---|---|---|
| API 清单总表 | Verified | 本轮复核确认 `API_SPEC.md` §6 当前包含 48 个稳定唯一 API ID，Method + Path 与逐接口详情一致；语义修复后的 route inventory 已由 `AR-F4-F8-004` / `005` / `006` / `008` 定向复核通过 |
| 逐接口字段级详情 | Verified | 本轮复核确认 `API_SPEC.md` §7 当前包含 48 个接口详情，均有路径参数、查询参数、请求头、请求体、成功响应、错误响应和 F7 契约测试；新增语义修复已复核 |
| Schema 索引 | Verified | `API_SPEC.md` §8 覆盖所有必需的通用 / 请求 / 响应数据 schema，并额外登记 `RecordCopyEventRequest` |
| DATA_MODEL 承接 | Verified | `DATA_MODEL.md` §4.4、§11.2、§14 承接 `IdempotencyRecord`、`AiTask` / `AiTaskResult`、`ApiRequestTrace` / `TraceRef`、`AuditEvent` 和 persistence handoff |
| 禁止项 | Verified | route inventory 未新增 export / download / upload / file / pdf / docx / word endpoint，未新增文件上传解析、外部材料解析岗位或精确通过概率 endpoint |

## 7. 定向复核：AR-F4-F8-002

状态：Verified

| 检查项 | 结果 | 证据 |
|---|---|---|
| F6 页面接入矩阵 | Verified | `API_SPEC.md` §6.1 覆盖 32 个 F6 page / surface；机械校验确认 32 行均有所需 API、读取模型 / 响应 Schema、加载 / 异步状态、空态、错误态、权限态、候选 / 确认态、复制边界和 F7 断言，且无空列 |
| 状态映射 | Verified | `API_SPEC.md` §6.2 覆盖 19 个状态：loading、empty、success、queued、running、partial、low_confidence、validation_failed、source_unavailable、generation_failed、provider_unavailable、task_timeout、rate_limited、stale_version_conflict、permission_denied、owner_mismatch、not_found_or_inaccessible、idempotency_conflict、export_not_supported；每项均有 handling、applies-to 和 N/A rule / reason |
| 前端字段需求 | Verified | `API_SPEC.md` §6.3 登记 display title / summary、status、timestamps、version、confidence、source availability、low confidence、validation、evidence、trace、next_actions、confirmation、candidate / suggestion、copyable content 和 user_visible_status，且要求 F6 不得伪造缺失字段 |
| 用户确认流 | Verified | `API_SPEC.md` §6.4 覆盖 `AssetCandidate`、`AssetVersionSuggestion`、`WeaknessCandidate`、`WeaknessMergeSuggestion`、`TrainingSuggestion`、Report / Review 沉淀项和 Candidate / draft / suggestion 到 formal object 的转换；确认前不得写正式对象 |
| F6 禁止能力 | Verified | `API_SPEC.md` §6.5 明确无文件导出、无 PDF / Markdown / Word / docx 下载、无文件上传解析、无外部材料解析岗位、无精确通过概率、无 system prompt / provider payload / 隐藏评分规则展示；API route inventory 未发现 export / download / upload / file parse 类 endpoint |
| F2/F3 一致性 | Verified | `API_SPEC.md` §6.6 明确不新增未登记页面体系；dashboard aggregate、report history list、candidate inbox、account preferences 均列为待补缺口或后续 refinement，不作为 AR-F4-F8-002 阻断项，也不得由 F6 自行发明 |
| F4→F6 handoff 规则 | Verified | `TECH_DESIGN.md` §15.1 指向 `API_SPEC.md` §6.1-§6.6，并禁止 F6 从 UX/UI 反向发明 API 字段、状态或错误码 |

本节只记录 `AR-F4-F8-002` 定向复核结果；整体 `状态` 仍为 `Pending`，`AR-F4-F8-003` 仍为 Open，不创建最终验收审批。

## 8. 定向复核：AR-F4-F8-008

状态：Verified

| 检查项 | 结果 | 证据 |
|---|---|---|
| API path 不可变性 | Verified | `API_SPEC.md` 中 API 清单总表、逐接口详情和 Method + Path 引用的 path 字段内中文字符、pipe、空格和中文说明污染均为 0；path params 均为英文 snake_case |
| Method + Path 对账 | Verified | API 清单总表 Method + Path 数量为 48；逐接口详情 Method + Path 数量为 48；二者集合差异为 0；API ID 为 48 个且唯一 |
| 禁止 endpoint | Verified | 未发现独立 `GET /api/v1/reports/{report_id}/sections`；未发现 project-experience module CRUD；report sections 由 `GET /api/v1/reports/{report_id}` 的 `data.sections[]` 承接 |
| 技术标识符 | Verified | JSON 字段名、Header、enum / error code、Schema 名、API ID、`AR-F4-F8-*`、`AIFI-*`、`P-*` 和 F7 assertion id 均保持技术标识符原样；未发现 `简历_id`、`岗位_id`、`请求_id`、`追踪_id`、`来源_availability`、`低_confidence`、`验证_status`、`确认_required` |
| DATA_MODEL 交叉检查 | Verified | `DATA_MODEL.md` 保留 `IdempotencyRecord`、`AiTask`、`ApiRequestTrace`、`TraceRef`、`AuditEvent` 等 schema / 逻辑对象名；字段名和 enum 值未被误翻译；provider payload、system prompt、hidden scoring rules 均处于不得保存 / 不得暴露边界 |

本节只记录 `AR-F4-F8-008` 定向复核结果；整体 `状态` 仍为 `Pending`，`AR-F4-F8-003` 仍为 Open，不创建最终验收审批。

## 9. 定向复核：AR-F4-F8-004 / 005 / 006 / 007

状态：Verified

| Finding ID | 修复记录 | 复核状态 |
|---|---|---|
| AR-F4-F8-004 | Resume API 收敛为 Markdown-only：移除 project-experience module CRUD 和 `modules[]`；`UpdateResumeRequest` 只保留 `markdown_text`、`base_version_ref`、可选 `edit_reason`；普通 Resume CRUD 不使用 `source_availability`；`DATA_MODEL.md` / `SECURITY_PRIVACY.md` / Prompt contracts 均收敛为 Markdown 片段或 derived outline。 | Verified；定向复核通过，整体验收仍为 Pending |
| AR-F4-F8-005 | Job list/detail 增加 `binding_summary` 和 `latest_match_summary`；补 `JobBindingSummary` / `JobMatchSummary`、summary 状态域、`score_scale`、`score_version`、`rubric_version`、stale 原因和 no exact probability 约束；`DATA_MODEL.md` 说明 summary 由 `JobResumeBinding` / `JobMatchAnalysis` 派生。 | Verified；定向复核通过，整体验收仍为 Pending |
| AR-F4-F8-006 | Polish session request 使用 `resume_job_binding_id` 并增加 `topic_id`、`subtopic_id`、`custom_topic_text`；新增 `GET /api/v1/polish-topics`、`PolishTopic` / `PolishSubtopic`；DATA / PROMPT / POLISH / SECURITY 增加 topic refs、上下文装配和 custom topic prompt injection 防护。 | Verified；定向复核通过，整体验收仍为 Pending |
| AR-F4-F8-007 | `docs/02-design` 正式设计文档改为中文优先：正文、章节标题、表头、说明、风险、验收和测试描述已中文化；API path、JSON 字段、enum、schema、ID、命令和文件路径等技术标识符保留原样。 | Verified；定向复核通过，整体验收仍为 Pending |

## 10. 需要 MCP Approval 的审计产物清单

本轮可以为以下三个文档创建 approval request：

- `docs/02-design/reviews/F4_TO_F8_READINESS_AUDIT_REPORT.md`
- `docs/02-design/reviews/F4_TO_F8_READINESS_RISK_REGISTER.md`
- `docs/02-design/reviews/F4_TO_F8_READINESS_REMEDIATION_MATRIX.md`

不得为本验收记录创建最终审批。本文件保持 `状态：Pending`。
