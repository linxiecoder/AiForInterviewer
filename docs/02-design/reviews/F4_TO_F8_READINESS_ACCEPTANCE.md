---
title: F4_TO_F8_READINESS_ACCEPTANCE
type: acceptance-record
status: active-f4
source_task: AIFI-ARCH-005
permalink: ai-for-interviewer/design/reviews/f4-to-f8-readiness-acceptance
---

# F4→F8 交接就绪性验收记录

状态：Accepted

本验收记录此前为 `Pending`；本轮依据人工决策批准 `F4/M4 Accepted`，批准结果为允许进入 F5 后端开发阶段。批准范围限于 F4 设计就绪性与 F4→F8 handoff baseline，不自动批准 F6 / F7 / F8 独立启动，不代表 F8 正式发布审批；F8 正式发布仍必须等待 F7 全链路通过和 F8 阶段产物完成。

整改更新：`AR-F4-F8-001` 已通过定向复核并标记为 Verified；`AR-F4-F8-002` 已通过定向复核并标记为 Verified；`AR-F4-F8-003` 已通过 F8 release handoff 定向复核并标记为 Verified；`AR-F4-F8-004`、`AR-F4-F8-005`、`AR-F4-F8-006` 已通过定向复核并标记为 Verified；`AR-F4-F8-007` 已通过中文优先文档治理定向复核并标记为 Verified；`AR-F4-F8-008` 已通过 API path / 技术标识符原样性定向复核并标记为 Verified。所有 known findings 均为 Verified；本轮人工批准后，本文件整体 `状态` 转为 `Accepted`，允许 F5 正式启动。F6 / F7 / F8 不因 F4 handoff 阻断，但仍分别依赖 F5 主接口、F5/F6 联调输入、F7 全链路通过和 F8 阶段产物。

## 1. 审计范围

- F4 active design docs：`TECH_DESIGN.md`、`DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`
- Prompt contract 子文档：`docs/02-design/prompt-contracts/*.md` 下 9 个 `.md` 文件
- 后续阶段依据：`DELIVERY_PLAN.md`、`BACKLOG.md`
- 上游辅助输入：`PRD.md`、`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`
- 前序审计 evidence：`F4_PROMPT_SECURITY_TECH_*`、`F4_FULL_DESIGN_*`

## 2. 就绪性结论

| 阶段 | 结论 | 是否允许启动 |
|---|---|---|
| F5 就绪性结论 | Accepted baseline。AR-F4-F8-001/004/005/006/007/008 不再阻断 F5 API / DATA / Prompt handoff；AR-F4-F8-003 的 F8 release handoff 已补齐；本轮人工批准 `F4/M4 Accepted`，允许进入 F5 后端开发。 | 是 |
| F6 就绪性结论 | Verified baseline。AR-F4-F8-002/004/005/006/007/008 已可作为 F6 接入输入；Job summary、Resume Markdown-only、Polish topic/subtopic 和中文优先文档治理已完成定向复核；F6 不因 F4 阻断，但仍依赖 F5 主接口可用和后续阶段授权。 | 不因 F4 阻断；未自动启动 |
| F7 就绪性结论 | Verified baseline。API 契约测试和页面 assertions 有 Verified 基线；AR-F4-F8-004 / 005 / 006 的新增 F7 assertions、AR-F4-F8-007 中文优先治理、AR-F4-F8-008 技术标识符原样性已定向复核；F7 不因 F4 阻断，但仍依赖 F5/F6。 | 不因 F4 阻断；未自动启动 |
| F8 就绪性结论 | Verified handoff baseline。`RELEASE_HANDOFF_SPEC.md`、TECH / API / SECURITY / PERSISTENCE / BACKLOG 已补齐 release checklist 来源矩阵、known limitations、runbook source、rollback / migration / restore handoff、observability / audit / trace inventory、provider failure / rate limit / retry policy、retention / deletion / privacy handoff 和 Deferred→Backlog 映射；F8 不因 F4 handoff 阻断，但正式发布仍依赖 F7 全链路通过和 F8 release checklist / changelog / runbook 等阶段产物。 | 不因 F4 handoff 阻断；未批准发布 |

## 3. Finding 统计

| 严重度 | 未关闭数量 |
|---|---:|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |

已验证 finding：

- `AR-F4-F8-001` High: API_SPEC / DATA_MODEL 字段级 contract 和幂等 / task / trace / persistence 承接已通过定向复核，标记为 Verified；整体验收已人工批准为 Accepted。
- `AR-F4-F8-002` High: F6 页面到 API / 状态 / 错误态接入矩阵已通过定向复核，标记为 Verified；整体验收已人工批准为 Accepted。
- `AR-F4-F8-003` High: F8 release / ops / retrospective handoff 已通过定向复核，`RELEASE_HANDOFF_SPEC.md` 与 TECH / API / SECURITY / PERSISTENCE / BACKLOG 已可生成 release checklist、known limitations、runbook、rollback strategy、changelog 输入、发布复盘输入和 next iteration backlog，标记为 Verified；整体验收已人工批准为 Accepted，但 F8 正式产物尚未创建。
- `AR-F4-F8-004` High: Resume API Markdown-only、无 project-experience module CRUD、无 `modules[]`、普通 Resume CRUD 不使用 `source_availability` 已通过定向复核，标记为 Verified；整体验收已人工批准为 Accepted。
- `AR-F4-F8-005` High: Job list/detail 的 `binding_summary` / `latest_match_summary`、summary 状态域、评分版本字段和 no exact probability 边界已通过定向复核，标记为 Verified；整体验收已人工批准为 Accepted。
- `AR-F4-F8-006` High: Polish topic/subtopic、`resume_job_binding_id`、`GET /api/v1/polish-topics`、F6 surface、F7 tests 和 `custom_topic_text` prompt injection 防护已通过定向复核，标记为 Verified；整体验收已人工批准为 Accepted。
- `AR-F4-F8-007` Medium: `docs/02-design` 中文优先治理和技术标识符保留已通过定向复核，标记为 Verified；整体验收已人工批准为 Accepted。
- `AR-F4-F8-008` High: API path / 技术标识符原样性已通过定向复核，API 清单总表与逐接口详情 Method + Path 一致，标记为 Verified；整体验收已人工批准为 Accepted。

已修复但待复核 finding：无。

未关闭 finding（Open findings）：

- 无。所有 known findings 已 Verified；人工批准已完成。

## 4. 启动判定

| 判定项 | 结论 |
|---|---|
| 是否允许 F5 启动 | 是。`F4/M4 Accepted` 已由人工批准，AR-F4-F8-001/004/005/006/007/008 不再阻断 API / DATA / Prompt 实现交接，AR-F4-F8-003 已补齐 F8 handoff；允许进入 F5 后端开发。 |
| 是否允许 F6 启动 | 不因 F4 阻断，但不在本次批准中自动启动。F6 仍依赖 F5 主接口可用和后续阶段授权；AR-F4-F8-002/004/005/006/007/008 已可作为 F6 页面接入准备输入。 |
| 是否允许 F7 规划测试 | 不因 F4 阻断，但不在本次批准中自动启动。F7 仍依赖 F5/F6；API / DATA / Prompt / F6 assertions / 中文治理 / 技术标识符原样性均已有 Verified baseline。 |
| 是否允许 F8 发布准备 | 不因 F4 handoff 阻断，但不代表 F8 正式发布审批。F8 正式发布仍需 F7 全链路通过、F8 阶段任务授权，并创建 release checklist / changelog / runbook 等阶段产物。 |

## 5. 批准记录 / Approval Record

- decision: F4/M4 Accepted
- scope: F4 design readiness and F4→F8 handoff baseline
- allowed next phase: F5
- not included: F8 release approval, production release, F6/F7/F8 independent approval
- approved_by: human decision in current workflow
- date: 2026-05-17

保留边界：

1. F6 / F7 / F8 不因 F4 阻断，但仍需满足各自依赖和后续阶段授权。
2. F8 阶段仍需基于 `RELEASE_HANDOFF_SPEC.md` 创建正式 `docs/03-implementation/RELEASE_CHECKLIST.md`、`CHANGELOG.md`、runbook、rollback strategy、known limitations 和 release retrospective；本轮不创建这些 F8 产物。
3. PRD / UX 中“展示主要简历模块”“维护项目经历”等上游产品口径如需改写为 Markdown-only + derived outline 表述，后续按产品变更流程处理；本轮不修改 PRD / UX。

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

本节只记录 `AR-F4-F8-002` 定向复核结果；整体验收已在本轮人工批准后转为 `Accepted`，但不代表 F6 / F7 / F8 独立启动或 F8 发布审批。

## 8. 定向复核：AR-F4-F8-008

状态：Verified

| 检查项 | 结果 | 证据 |
|---|---|---|
| API path 不可变性 | Verified | `API_SPEC.md` 中 API 清单总表、逐接口详情和 Method + Path 引用的 path 字段内中文字符、pipe、空格和中文说明污染均为 0；path params 均为英文 snake_case |
| Method + Path 对账 | Verified | API 清单总表 Method + Path 数量为 48；逐接口详情 Method + Path 数量为 48；二者集合差异为 0；API ID 为 48 个且唯一 |
| 禁止 endpoint | Verified | 未发现独立 `GET /api/v1/reports/{report_id}/sections`；未发现 project-experience module CRUD；report sections 由 `GET /api/v1/reports/{report_id}` 的 `data.sections[]` 承接 |
| 技术标识符 | Verified | JSON 字段名、Header、enum / error code、Schema 名、API ID、`AR-F4-F8-*`、`AIFI-*`、`P-*` 和 F7 assertion id 均保持技术标识符原样；未发现 `简历_id`、`岗位_id`、`请求_id`、`追踪_id`、`来源_availability`、`低_confidence`、`验证_status`、`确认_required` |
| DATA_MODEL 交叉检查 | Verified | `DATA_MODEL.md` 保留 `IdempotencyRecord`、`AiTask`、`ApiRequestTrace`、`TraceRef`、`AuditEvent` 等 schema / 逻辑对象名；字段名和 enum 值未被误翻译；provider payload、system prompt、hidden scoring rules 均处于不得保存 / 不得暴露边界 |

本节只记录 `AR-F4-F8-008` 定向复核结果；整体验收已在本轮人工批准后转为 `Accepted`，但不代表 F6 / F7 / F8 独立启动或 F8 发布审批。

## 9. 定向复核：AR-F4-F8-004 / 005 / 006 / 007

状态：Verified

| Finding ID | 修复记录 | 复核状态 |
|---|---|---|
| AR-F4-F8-004 | Resume API 收敛为 Markdown-only：移除 project-experience module CRUD 和 `modules[]`；`UpdateResumeRequest` 只保留 `markdown_text`、`base_version_ref`、可选 `edit_reason`；普通 Resume CRUD 不使用 `source_availability`；`DATA_MODEL.md` / `SECURITY_PRIVACY.md` / Prompt contracts 均收敛为 Markdown 片段或 derived outline。 | Verified；定向复核通过，整体验收已人工批准为 Accepted |
| AR-F4-F8-005 | Job list/detail 增加 `binding_summary` 和 `latest_match_summary`；补 `JobBindingSummary` / `JobMatchSummary`、summary 状态域、`score_scale`、`score_version`、`rubric_version`、stale 原因和 no exact probability 约束；`DATA_MODEL.md` 说明 summary 由 `JobResumeBinding` / `JobMatchAnalysis` 派生。 | Verified；定向复核通过，整体验收已人工批准为 Accepted |
| AR-F4-F8-006 | Polish session request 使用 `resume_job_binding_id` 并增加 `topic_id`、`subtopic_id`、`custom_topic_text`；新增 `GET /api/v1/polish-topics`、`PolishTopic` / `PolishSubtopic`；DATA / PROMPT / POLISH / SECURITY 增加 topic refs、上下文装配和 custom topic prompt injection 防护。 | Verified；定向复核通过，整体验收已人工批准为 Accepted |
| AR-F4-F8-007 | `docs/02-design` 正式设计文档改为中文优先：正文、章节标题、表头、说明、风险、验收和测试描述已中文化；API path、JSON 字段、enum、schema、ID、命令和文件路径等技术标识符保留原样。 | Verified；定向复核通过，整体验收已人工批准为 Accepted |

## 10. 定向复核：AR-F4-F8-003

状态：Verified

| 检查项 | 结果 | 证据 |
|---|---|---|
| F8 handoff canonical 文档 | Verified | `DOCS_INDEX.md` 已登记 `RELEASE_HANDOFF_SPEC.md` 为 F4→F8 release / ops / retrospective handoff canonical 文档；该文档不替代 F8 最终 release checklist / changelog / runbook |
| release checklist source matrix | Verified | `RELEASE_HANDOFF_SPEC.md` §3 覆盖 no export、no file download、no file upload parsing、no external material parsing、no exact probability、score / rubric / evidence refs、low confidence、source unavailable、validation failed、candidate not formal、owner boundary、copy boundary、route inventory、async status、provider failure、rate limit、audit、trace、logs redaction、secret、retention / deletion、backup restore、migration / rollback 和 Deferred mapping |
| known limitations | Verified | `RELEASE_HANDOFF_SPEC.md` §4 区分 product non-goal、implementation limitation、operational limitation、accepted risk 和 next-iteration item，覆盖文件导出、PDF / Word / docx 下载、文件上传解析、外部材料自动生成岗位、精确通过概率、招聘结果校准、多租户、OAuth / SSO、复杂权限、互联网检索、provider payload / completion 原文和低置信降级 |
| runbook source | Verified | `RELEASE_HANDOFF_SPEC.md` §5 覆盖 LLM provider unavailable / timeout / rate limit、AI task timeout、generation failed、validation failed、low confidence spike、source unavailable、RAG retrieval empty、owner mismatch spike、idempotency conflict、stale version conflict、copy boundary violation、export not supported attempt、audit / trace write failure、migration failure 和 backup restore required |
| rollback / migration / restore | Verified | `RELEASE_HANDOFF_SPEC.md` §6 与 `PERSISTENCE_MODEL.md` §11 覆盖 migration 前后检查、rollback trigger、decision owner、schema rollback 风险、data compatibility、versioned object rollback、historical references、`ScoreRuleVersion` rollback、in-flight `AiTask` rollback、backup restore validation 和 source availability after restore |
| observability / audit / trace | Verified | `RELEASE_HANDOFF_SPEC.md` §7 与 `SECURITY_PRIVACY.md` §22 覆盖 request_id、trace_id、ai_task_id、audit_event_id、owner_id / actor_id、endpoint_ref、task_type、contract_ids、validation_status、confidence_level、source_availability、rate limit、provider failure、copy event、confirmation、retention / deletion；明确不得记录正文、Prompt、provider payload、completion 原文、hidden scoring rules、token、cookie、secret |
| provider failure / rate limit / retry | Verified | `RELEASE_HANDOFF_SPEC.md` §8 与 `API_SPEC.md` §14 明确可重试 / 不可重试 failure、retry 不扩大上下文、不启用互联网检索、不绕过 owner check、low confidence / partial 不伪装高置信，并要求 rate limit 响应进入 F8 release check |
| retention / deletion / privacy | Verified | `RELEASE_HANDOFF_SPEC.md` §9 与 `SECURITY_PRIVACY.md` §22 覆盖删除后历史引用展示、source deleted / disabled / archived / unavailable 行为、audit / trace 保留边界、provider payload 不保存或只保存安全摘要、copy event 不存正文、删除 / 禁用 / 归档对后续 AI 生成的影响和 restore 后校验 |
| Deferred→Backlog | Verified | `RELEASE_HANDOFF_SPEC.md` §10 将全部 Deferred 项映射到 owner、`AIFI-REL-001` 至 `AIFI-REL-007`、`AIFI-BE-001` 或 LATER / accepted risk / not blocking 理由；`BACKLOG.md` 已新增相应 AIFI-* 任务，不创建新阶段体系 |
| F8 output mapping | Verified | `RELEASE_HANDOFF_SPEC.md` §11 说明如何生成 `docs/03-implementation/RELEASE_CHECKLIST.md`、`CHANGELOG.md`、runbook、known limitations、rollback strategy、release retrospective 和 next iteration backlog；本轮不创建这些 F8 产物 |

本节只记录 `AR-F4-F8-003` 定向复核结果。所有 known findings 已 Verified；整体 `状态` 已在本轮人工批准后转为 `Accepted`，允许 F5 启动，但不自动批准 F6 / F7 / F8 独立启动或 F8 正式发布。

## 11. 需要 MCP Approval 的审计产物清单

前序审计产物可按治理流程保留 approval evidence：

- `docs/02-design/reviews/F4_TO_F8_READINESS_AUDIT_REPORT.md`
- `docs/02-design/reviews/F4_TO_F8_READINESS_RISK_REGISTER.md`
- `docs/02-design/reviews/F4_TO_F8_READINESS_REMEDIATION_MATRIX.md`

本验收记录已由人工决策批准为 `Accepted`。本轮不创建 F8 release approval，也不创建 F8 release checklist / changelog / runbook。
