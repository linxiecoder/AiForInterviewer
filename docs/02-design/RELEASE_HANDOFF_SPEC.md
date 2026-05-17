---
title: RELEASE_HANDOFF_SPEC
type: design
status: draft-f4-release-handoff
owner: F4 / F8 发布治理
source_task: AIFI-ARCH-005
permalink: ai-for-interviewer/docs/02-design/release-handoff-spec
---

# RELEASE_HANDOFF_SPEC

## 1. 文档状态与治理边界

- 本文件是 F4 -> F8 release / ops / retrospective handoff spec，作为 F8 发布、运维和复盘交接的 canonical active design doc。
- 本文件不是实际发布清单，不是运行手册成品，不是监控平台实现，不是部署脚本，不是数据库 migration 文件，也不是最终 rollback runbook。
- 本文件为 F8 的 `docs/03-delivery/RELEASE_CHECKLIST.md`、`CHANGELOG.md`、runbook、known limitations、rollback strategy、release retrospective 和 next-iteration backlog 提供输入。
- 本文件不改变 MVP 非目标，不新增文件导出、PDF / docx / Word 下载、文件上传解析、外部材料解析岗位、精确通过概率、多租户、商业化或企业治理能力。
- 本文件不表示 F8 运维能力已经实现；F8 仍需基于本文件生成正式发布产物并经过人工 approval。
- 本文件不暴露 system prompt、provider payload、completion 原文、hidden scoring rules、secret、token、cookie、request / response body、简历正文、岗位全文、回答全文、报告正文或复盘正文。
- 本文件不允许 candidate / suggestion 静默成为 formal object；所有正式写入仍以 `API_SPEC.md`、`DATA_MODEL.md`、`SEMANTICS_GLOSSARY.md` 和用户确认边界为准。

## 2. 输入来源

| 来源文档 | 使用方式 |
|---|---|
| `TECH_DESIGN.md` | 模块边界、LLM 后端隔离、F4->F6 handoff、deferred_non_blocking 分类和 F8 handoff 上位规则 |
| `API_SPEC.md` | route inventory、response / error envelope、async task、retry、rate limit、copy boundary、no export、F7 assertions |
| `DATA_MODEL.md` | 逻辑对象、版本 / 快照、candidate / suggestion / formal object、trace / evidence、source availability、历史引用完整性 |
| `PERSISTENCE_MODEL.md` | F5 persistence handoff、建议物理模型、join / reference table、owner / trace / audit 和 migration / rollback 输入 |
| `SECURITY_PRIVACY.md` | owner boundary、session / token / cookie、secret、日志脱敏、provider payload、retention / deletion、backup 边界 |
| `PROMPT_SPEC.md` | P-* contract、Context Assembly、source availability、validation、low confidence、retry / fallback 和 no raw payload 边界 |
| `SCORING_SPEC.md` | 0-100 product score、`ScoreRuleVersion`、`score_version`、`rubric_version`、no exact probability 和 scoring rollback 边界 |
| `SEMANTICS_GLOSSARY.md` | `confidence_level`、`validation_status`、`source_availability`、candidate / suggestion / formal object 和失败状态语义 |
| `APPLICATION_FLOW_SPEC.md` | endpoint 到 application service、AiTask、P-* contract、LLM call plan、validation 和 persistence handoff |
| `DELIVERY_PLAN.md` | F8 目标、主要产物和 release blocker 清零要求 |
| `BACKLOG.md` | F8 / LATER 承接任务、MUST / SHOULD / COULD / LATER 优先级和任务依赖 |

## 3. Release checklist source matrix

F8 `RELEASE_CHECKLIST.md` 应直接从本矩阵抽取检查项。阻断级别使用 `release_blocker`、`must_verify`、`known_limitation`、`accepted_risk` 或 `next_iteration`。

| 检查项 | 来源文档 | F8 产物 | 阻断级别 | 验证方式 |
|---|---|---|---|---|
| no export | `TECH_DESIGN.md` §4 / §16；`API_SPEC.md` §10 / §11；`SECURITY_PRIVACY.md` §13-§14 | release checklist / known limitations | release_blocker | route inventory 不存在 export / download endpoint；UI 无文件导出入口；命中时返回 `export_not_supported` |
| no PDF / docx / Word / Markdown file download | `API_SPEC.md` §6.5 / §10；`SECURITY_PRIVACY.md` §8 / §14 | release checklist / known limitations | release_blocker | 扫描 route、UI、copy content schema 和文案；仅允许“不支持 / 禁止 / non-goal”语境 |
| no file upload parsing | `TECH_DESIGN.md` §4；`SECURITY_PRIVACY.md` §8；`DATA_MODEL.md` §5.2 | release checklist / known limitations | release_blocker | route / UI 不存在 upload parser；Resume 只保存 Markdown 文本 |
| no external material parsing for jobs | `TECH_DESIGN.md` §4；`API_SPEC.md` §2.2；`DATA_MODEL.md` §5.3 | release checklist / known limitations | release_blocker | Job create / update 只允许用户手动录入字段；无 URL 抓取、文件解析或自动生成岗位入口 |
| no exact pass probability | `SCORING_SPEC.md`；`API_SPEC.md` §4.4 / §11；`PROMPT_SPEC.md` §7.2 | release checklist / known limitations | release_blocker | API / copy content / UI 不返回 `pass_probability`、`offer_probability`、`admission_probability`、`pass_rate_percent` 或等价文案 |
| score version / rubric version / evidence refs | `SCORING_SPEC.md` §5 / §10；`API_SPEC.md` §4.4 / §8 / §11 | release checklist / changelog input | must_verify | 评分、报告、复盘和 job match 响应包含 `score_version`、`rubric_version`、`score_rule_version_ref`、`evidence_refs` 和 `trace_refs` |
| low confidence visible | `SEMANTICS_GLOSSARY.md` §2；`API_SPEC.md` §4.3 / §6.2；`SECURITY_PRIVACY.md` §17 | release checklist / runbook | must_verify | `low_confidence` 不被 success 吞掉；F6 / F7 fixture 展示风险、影响范围和 next actions |
| source unavailable handling | `SEMANTICS_GLOSSARY.md` §3.3；`PROMPT_SPEC.md` §6.1；`SECURITY_PRIVACY.md` §13 / §21.2 | release checklist / runbook | must_verify | `source_deleted` / `source_disabled` / `source_unavailable` 不读取正文；新生成阻断或降级 |
| validation failed not formal | `SEMANTICS_GLOSSARY.md` §3.2 / §5；`API_SPEC.md` §5 / §11；`SCORING_SPEC.md` §7 | release checklist / runbook | must_verify | `validation_failed` 不写正式评分、报告评分、Weakness、Asset、TrainingRecommendation 或 TrainingTask |
| candidate / suggestion not formal without confirmation | `DATA_MODEL.md` §4.3；`API_SPEC.md` §9；`SEMANTICS_GLOSSARY.md` §4 | release checklist | release_blocker | candidate / suggestion 到 formal object 必须经过 `UserConfirmationRef`、编辑、合并或显式业务动作 |
| owner boundary | `API_SPEC.md` §3.2-§3.3；`SECURITY_PRIVACY.md` §5；`PERSISTENCE_MODEL.md` §3 | release checklist / runbook | release_blocker | 列表、详情、生成、复制、确认、删除、RAG 检索和 trace 均 owner scoped；跨 owner fixture 全部拒绝 |
| copy boundary | `API_SPEC.md` §10 / §11；`SECURITY_PRIVACY.md` §13.3 / §14 / §21.2 | release checklist / known limitations | release_blocker | copy content 仅为剪贴板结构；copy event 不记录正文；无 filename、download URL 或 export artifact |
| report copy content | `API_SPEC.md` §10；`DATA_MODEL.md` §5.8；`PROMPT_SPEC.md` §9.5 | release checklist / smoke tests | must_verify | `GET /api/v1/reports/{report_id}/copy-content` 不含 Prompt、provider payload、隐藏评分规则或无权限正文 |
| review copy content | `API_SPEC.md` §6.1 / §7；`DATA_MODEL.md` §5.8；`SECURITY_PRIVACY.md` §15 | release checklist / smoke tests | must_verify | review copy content 脱敏真实复盘第三方 / 公司 / 面试官信息；copy event 不存正文 |
| API route inventory | `API_SPEC.md` §6 / §7 | release checklist / changelog input | must_verify | route inventory 与实现路由逐项对账；新增 / 删除 / 方法变化进入 changelog input |
| async task status | `API_SPEC.md` §5；`DATA_MODEL.md` §4.4.2；`APPLICATION_FLOW_SPEC.md` §4 | runbook / release checklist | must_verify | `queued`、`running`、`partial`、`low_confidence`、`validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled` 都可见 |
| provider failure | `API_SPEC.md` §4 / §5；`SECURITY_PRIVACY.md` §9.3；`PROMPT_SPEC.md` §7 | runbook / release checklist | must_verify | provider unavailable / timeout / generation failed 有错误码、retryable 标记、用户动作和不扩大上下文规则 |
| rate limit | `API_SPEC.md` §3.8 / §11；`SECURITY_PRIVACY.md` §19 / §20 | release checklist / runbook | must_verify | 429、`Retry-After` / rate limit meta、actor/IP/endpoint/task type 维度和不绕过 owner check |
| audit events | `DATA_MODEL.md` §4.4.4；`SECURITY_PRIVACY.md` §12；`PERSISTENCE_MODEL.md` §4 | release checklist / runbook | must_verify | 登录、权限失败、owner mismatch、copy、confirmation、source unavailable、validation failed、export_not_supported 有最小审计 |
| trace refs | `API_SPEC.md` §3.9；`DATA_MODEL.md` §4.1 / §4.4.3；`PERSISTENCE_MODEL.md` §8 | release checklist / runbook | must_verify | response 返回 `request_id` / `trace_id`；前端不可展开 Prompt、completion 或 provider payload |
| logs redaction | `SECURITY_PRIVACY.md` §12 / §21.3；`PERSISTENCE_MODEL.md` §3 | release checklist / runbook | release_blocker | 日志不含正文、request / response body、Prompt、completion、provider payload、token、cookie、secret |
| secret handling | `SECURITY_PRIVACY.md` §18 / §20 | release checklist | release_blocker | provider key、cookie secret、DSN、环境变量不进前端、日志、Prompt、trace 或仓库；泄露后有废弃 / 轮换输入 |
| retention / deletion | `SECURITY_PRIVACY.md` §13；`DATA_MODEL.md` §8；`SEMANTICS_GLOSSARY.md` §3.3 | release checklist / known limitations | must_verify | 删除、归档、禁用后 active 读取失效；历史结果只展示 source availability 状态 |
| backup restore | `SECURITY_PRIVACY.md` §13.1；`PERSISTENCE_MODEL.md` §11；本文件 §6 / §9 | runbook / rollback strategy | must_verify | restore 后校验 owner、trace、source availability、history refs；不得恢复无权限正文读取 |
| migration / rollback | `PERSISTENCE_MODEL.md` §11；`DATA_MODEL.md` §8；`SCORING_SPEC.md` §9 | rollback strategy / runbook | must_verify | migration 前后 owner / version / references / ScoreRuleVersion / in-flight AiTask 对账；rollback 不改写历史结果 |
| known limitations | 本文件 §4；`BACKLOG.md` | known limitations / changelog input | must_verify | MVP 限制逐条进入发布说明输入，并映射 Backlog 或 accepted risk |
| deferred items mapped to Backlog | 本文件 §10；`BACKLOG.md` | next iteration backlog | release_blocker | 每个 Deferred 项有承接阶段、owner、Backlog ID、处理方式或 accepted risk / 不阻断理由 |

## 4. Known limitations

F8 known limitations 应按下表生成，不能把限制写成已实现能力。

| 限制 | 分类 | 用户 / 运维影响 | 处理方式 |
|---|---|---|---|
| 不支持文件导出 | product non-goal | 用户只能页面复制授权内容，不能下载文件 | `AIFI-REL-001` 发布说明中列为限制；无阻断 |
| 不支持 PDF / Word / docx 下载 | product non-goal | 无报告 / 复盘文件下载 | `AIFI-REL-001` 发布说明中列为限制；无阻断 |
| 不支持文件上传解析 | product non-goal | 简历需粘贴 / 编辑 Markdown 文本 | `AIFI-REL-001` 发布说明中列为限制；无阻断 |
| 不支持外部材料自动生成岗位 | product non-goal | 岗位 / JD 需用户手动录入 | `AIFI-REL-001` 发布说明中列为限制；无阻断 |
| 不承诺精确通过概率 | product non-goal | 只展示 0-100 product score、分档倾向、风险和免责声明 | release_blocker 检查禁止概率字段；无阻断 |
| 不做真实招聘结果校准 | next-iteration item | 评分不代表真实招聘决定 | `AIFI-REL-006` 承接；MVP 不阻断 |
| 不做企业级多租户 | next-iteration item | MVP 仅个人工作台 owner 边界 | `AIFI-REL-006` 承接；MVP 不阻断 |
| 不做完整 OAuth / SSO | next-iteration item | MVP 使用最小登录态抽象，企业身份后置 | `AIFI-REL-006` 承接；MVP 不阻断 |
| 不做复杂权限继承 | next-iteration item | 组织 / 团队 ACL 后置 | `AIFI-REL-006` 承接；MVP 不阻断 |
| 不默认启用互联网检索 | accepted risk | RAG / public material 只能使用明确来源，联网检索后置 | `AIFI-REL-006` 承接治理；MVP 不阻断 |
| 不保存 provider payload / completion 原文 | operational limitation | 排障只能使用结构化结果、failure category、usage、trace / audit 摘要 | `AIFI-REL-005` 验证日志和 trace 边界 |
| 不把低置信结果当高置信结论 | release_blocker rule | low confidence 需展示原因、影响范围和 next actions | `AIFI-REL-001` / `AIFI-REL-005` 必测 |
| 完整监控 / SIEM 平台不在 F4 实现 | operational limitation | F8 只能基于最小 signals 生成 runbook 和检查项，平台选型后置 | `AIFI-REL-004` / `AIFI-REL-006` 承接 |
| backup 即时 hard delete 不在 MVP 默认能力 | accepted risk | 备份内删除延迟需发布说明和恢复审批控制 | `AIFI-REL-003` / `AIFI-REL-005` 承接 |

## 5. Runbook 输入

F8 runbook 应按以下场景生成。恢复动作是 F8 runbook 输入，不代表 F4 已实现自动恢复。

| 场景 | 触发信号 | 用户影响 | 排查入口 | 恢复动作 | 审计 / 日志要求 |
|---|---|---|---|---|---|
| LLM provider unavailable | `provider_unavailable`、502、provider failure category | AI 生成不可用或需稍后重试 | `ai_task_id`、`trace_id`、provider failure category、rate limit meta | 暂停重试、提示稍后重试、必要时切换手动校对；不得扩大上下文 | 记录 task、actor、failure category、retryable；不记录 payload |
| provider timeout | `task_timeout`、504、`timeout_at` | 生成超时，可能保留部分输入 | `AiTask.status`、timeout config、trace refs | 标记 timed_out，允许安全 retry 或 cancel；不得 late formal write | 审计 timeout 和用户动作；日志只记录阶段和 trace |
| provider rate limit | 429、`rate_limited`、`Retry-After` | 用户需等待或降低频率 | rate limit headers、actor/IP/endpoint/task type | 返回等待时间，阻止重复提交；不得绕过 owner check | 记录 rate limit summary，不记录正文 |
| AI task timeout | `AiTask.status=timed_out` | 任务结果不可用或 partial | ai task status / result、idempotency record | 保留输入引用，提示 retry / cancel / manual review | 审计 task timeout、retry_count、result 状态 |
| generation failed | `generation_failed` | 生成失败，不展示完成态 | `AiTaskResult.status`、failure signals、validation result | 可重试则 retry；不可重试则人工校对或补充输入 | 记录 failure signal 和 trace；不保存 completion 原文 |
| validation failed | `validation_failed`、422 | 结果不能成为正式对象或正式评分 | validation result ref、schema / semantic failure category | 返回修复 / retry / manual review；阻止 formal write | 审计 validation failure；不记录 request / response body |
| low confidence spike | low confidence 比例异常 | 用户看到更多风险提示，结果不应高置信展示 | `LowConfidenceFlag`、task_type、source availability、input length summary | 检查 source、RAG、prompt contract、scoring rule version；必要时降级或暂停生成 | 聚合统计只记录摘要和类型，不记录正文 |
| source unavailable | `source_deleted` / `source_disabled` / `source_unavailable` | 新生成被阻断或历史结果降级 | source refs、version refs、snapshot refs、owner check | 选择可用来源、恢复合法来源或展示历史状态；不得读取不可用正文 | 审计 source status、target ref、result |
| RAG retrieval empty | `retrieval_empty`、low confidence | 证据不足，结果可能 partial | retrieval query summary、source scope、KnowledgeDocument status | 提示补充来源或走无检索降级；不得默认启用互联网检索 | 记录 retrieval status、source count、scope |
| owner mismatch spike | `owner_mismatch` / 403 / 404 过多 | 跨用户访问被拒绝或页面不可访问 | `ApiRequestTrace`、endpoint_ref、target summary | 检查 owner filter、复合资源 owner 校验和前端参数 | 审计 actor、target ref、result；不暴露资源存在性 |
| idempotency conflict | `idempotency_conflict`、409 | 重复提交被拒绝，需要刷新或重新提交 | idempotency scope、request_body_hash summary | 返回冲突提示，要求新 key 或刷新；不得覆盖第一次结果 | 记录 idempotency record 和 conflict，不记录 body |
| stale version conflict | `stale_version_conflict`、409 | 用户需刷新 / 对比 / 重试 | base_version_ref、target_version_ref、record_version | 保留用户输入，提示刷新或重新提交 | 审计 stale conflict 和 actor |
| copy boundary violation | `copy_boundary_violation` | 复制被拒绝或内容被脱敏 | copy content ref、copy boundary flags | 阻止复制敏感内容，提示不可复制原因 | copy audit 只记范围摘要和结果，不记正文 |
| export not supported attempt | `export_not_supported` | 用户无法下载或导出文件 | endpoint_ref、attempted_semantic | 展示“仅支持页面复制，不支持文件导出”；无导出物 | 审计 attempted semantic，不创建文件、filename 或 URL |
| audit event write failure | audit write failure / persistence error | 高风险动作不得静默成功 | audit storage health、target action、trace_id | 对安全关键动作 fail closed；非关键动作进入告警和补偿队列输入 | 记录最小 failure category，不记录正文 |
| trace write failure | trace persistence failure | 排障信息不足；关键 AI task 应降级 | trace write status、AiTask、ApiRequestTrace | 对 AI / copy / confirmation 关键流程降级或阻断，避免无 trace formal write | 审计 trace failure summary |
| database migration failure | migration failed / schema mismatch | 发布或启动失败，可能需要 rollback | migration logs summary、schema version、backup checkpoint | 停止发布、执行 rollback decision、校验历史 refs | 日志脱敏；记录 migration version 和 decision |
| backup restore required | restore drill / data incident | 需要从备份恢复，可能影响 source availability | backup checkpoint、owner scope、trace refs、source status | 按 restore runbook 校验 owner、trace、history refs 和 source status；不得恢复无权限正文读取 | 审计 restore request、approval、result 和 post-restore validation |

## 6. Rollback / migration / restore handoff

| 主题 | F8 handoff 规则 |
|---|---|
| migration 前检查 | 对账 schema version、migration plan、backup checkpoint、owner filter、idempotency records、AiTask 状态、ScoreRuleVersion 当前版本和 route inventory |
| migration 后检查 | 抽样验证 owner-scoped list/detail、history refs、copy boundary、candidate / confirmation、source availability、trace / audit、score version / rubric version |
| rollback trigger | migration failure、critical owner leakage、copy boundary violation、trace/audit critical write failure、scoring rule version mismatch、无法恢复的 provider failure 配置错误 |
| rollback decision owner | F8 Release owner 协调 Backend owner、Data owner、Security owner；用户侧公告由 Product / Release owner 决定 |
| schema rollback 风险 | 回滚可能造成新字段不可读、新 enum 不兼容、new task status 不可识别；必须有 compatibility check |
| data compatibility | 新版本写入的数据不得被旧版本静默解释为 success；未知 enum 必须进入 manual review / unsupported state |
| versioned object rollback | `ResumeVersion`、`JobVersion`、`AssetVersion`、`ScoreRuleVersion` 和 `SnapshotRef` 不得被 rollback 静默改写 |
| report / review / score historical references | 历史报告、复盘、评分继续引用生成时版本或快照；rollback 不重算、不覆盖、不删除历史解释 |
| `ScoreRuleVersion` rollback | 规则版本回滚必须保留新旧版本；历史 `ScoreResult` 仍引用生成时 rule version；不得直接改写历史 `score_value` |
| `AiTask` in-flight rollback | `queued` / `running` task 在 rollback 时应 cancel、timeout 或标记 `generation_failed`；不得在旧版本恢复后 late formal write |
| backup restore validation | restore 后必须验证 owner、trace、audit、source availability、history refs、score refs、candidate / confirmation 和 copy boundary |
| source availability after restore | restore 不等于可读取所有历史正文；`source_deleted` / `source_disabled` / `source_unavailable` 必须按当前合法状态表达 |

强制规则：

- 历史报告、复盘、评分不能因 rollback 静默改写。
- `source_deleted`、`source_disabled`、`source_unavailable` 不能恢复读取正文，除非有合法 snapshot / backup restore 机制、owner 权限和审计记录。
- candidate / suggestion rollback 不能自动创建 formal object。
- rollback 后的发布复盘必须记录触发信号、影响对象、恢复动作、仍不可用来源和后续 Backlog。

## 7. Observability / audit / trace inventory

| 信号 | 来源对象 / API | 最小字段 | 不得记录 | F8 检查 |
|---|---|---|---|---|
| `request_id` | all API envelopes / `ApiRequestTrace` | request id、endpoint_ref、created_at | request / response body 明文 | 每个 response 有 request id；日志可按 id 排障 |
| `trace_id` | all API envelopes / `TraceRef` | trace id、trace kind、target refs | Prompt、completion 原文、provider payload | 前端只显示必要 id，不可展开敏感 trace |
| `ai_task_id` | `AiTask` / AI task endpoints | task id、task_type、status、retry_count、timeout_at | provider task payload、模型参数 | AI task status 全状态可查且 owner scoped |
| `audit_event_id` | `AuditEvent` | event id、actor、target、action、result、timestamp | 正文、token、cookie、secret | 安全关键动作都有 audit event 或 fail closed |
| owner_id / actor_id | `OwnerRef` / `AuditActor` | owner / actor ref、role snapshot、scope | 请求体传入 owner_id 作为授权依据 | owner 过滤和复合资源校验可追踪 |
| endpoint_ref | `ApiEndpointRef` / route inventory | API ID、method、path_template、domain | path 中敏感正文 | route inventory 与实现一致 |
| task_type | `AiTask` | task_type、contract_ids、target_ref | Prompt 文案、provider payload | runbook 能按 task type 分流 |
| contract_ids | `AiTask` / `PROMPT_SPEC.md` | P-* IDs、contract domain | 完整 Prompt 文案 | 所有 AI task 关联合法 P-* contract |
| validation_status | `LlmValidationResult` / `ScoreResult` | status、failure signals、validation_result_ref | 原始模型输出 | validation failed 不 formal write |
| confidence_level | `ScoreResult` / AI result | confidence level、low_confidence_flags | 隐藏评分规则 | low confidence 可统计、可展示 |
| low_confidence_flags | `LowConfidenceFlag` | reason、impact、recommended action | 证据原文 | spike 可排查且不泄露正文 |
| source_availability | `SourceRef` / `EvidenceRef` | source status、source ref、version / snapshot ref | source_deleted 正文 | 新生成阻断或降级，历史只展示状态 |
| rate limit headers | API gateway / app | limit、remaining、reset、retry-after、scope summary | IP 原文长期保留、正文 | 429 可进入 release check |
| provider failure category | `LlmFailureRecord` | category、retryable、task_type、provider family | provider request / response payload | runbook 可判断 retry / no retry |
| copy event summary | report / review copy event | actor、target、copy surface、scope summary、result | 复制正文、报告全文、复盘正文 | copy audit no body |
| confirmation action | `UserConfirmationRef` | action、target_ref、before / after summary ref、result | 大段原文、Prompt、completion | formal object 均可追溯确认 |
| retention / deletion action | `AuditEvent` / source status | action、resource_ref、source status、deleted_at / archived_at | 已删除正文 | 删除后 active 读取失效，历史 source status 可见 |

## 8. Provider failure / rate limit / retry policy handoff

| 类别 | 可重试性 | F8 检查 |
|---|---|---|
| `provider_unavailable` | 可重试，需等待或按退避策略 | retry 不得扩大上下文，不得默认启用互联网检索，不得绕过 owner check |
| provider timeout / `task_timeout` | 可重试或可取消，取决于 `retryable` 和 retry_count | timeout 后不得 late formal write；partial 需明确标记 |
| provider rate limit / HTTP 429 | 可重试，但必须遵守 `Retry-After` / rate limit meta | 前端显示等待；重复提交不新建 task |
| transient network failure | 可重试 | 保留 input refs 和 trace；不保存 request / response body |
| schema invalid / `validation_failed` | 仅在可修复子类或 prompt repair 后可重试 | validation failed 不写 formal object 或正式评分 |
| `source_unavailable` | 用户修复来源后可重试；未修复不可重试 | 不读取不可用正文；不默认恢复来源 |
| owner mismatch / permission denied | 不可重试 | 不暴露资源存在性；记录安全审计 |
| export not supported | 不可重试 | 返回不支持导出；不创建下载物 |
| 已成功且已确认写入 formal object 的任务 | 不可重试为覆盖写入 | 如需重做必须创建新任务 / 新版本，不覆盖历史 |

强制规则：

- retry 不得扩大上下文。
- retry 不得默认启用互联网检索。
- retry 不得绕过 owner check。
- `low_confidence` 和 `partial` 可以展示，但不能伪装高置信。
- rate limit 响应必须能进入 F8 release check，并可由 runbook 判断用户等待、重试或降级路径。

## 9. Retention / deletion / privacy handoff

| 场景 | F8 handoff 规则 |
|---|---|
| 用户删除资源后历史引用如何展示 | 历史报告、复盘、评分和资产候选保留生成时 ref / snapshot / summary status，并展示 `source_deleted` 或具体 source status |
| `source_deleted` / `source_disabled` / `source_archived` / `source_unavailable` | 不参与新生成；历史引用只显示状态和安全摘要；不得读取正文 |
| audit log 与 trace 保留边界 | audit / trace 只保存最小 actor、target、action、result、trace id、failure category 和摘要；具体天数由 F5 / F8 配置冻结 |
| provider payload 保存边界 | 默认不保存 provider payload / completion 原文；如 F5 需要安全摘要，必须脱敏、限期、禁止前端可见 |
| copy event 保存边界 | copy event 只保存复制范围摘要、result、actor、target、timestamp 和 risk flag；不保存复制正文 |
| 删除、禁用、归档对后续 AI 生成的影响 | 后续 Context Assembly、RAG 和 AI task 必须排除不可用正文，或进入 source unavailable / low confidence / manual review |
| backup restore 后校验 | restore 后对账 owner、trace、audit、source availability、version refs、snapshot refs、copy boundary 和 candidate / formal boundary |
| 用户设备副本 | 页面复制后的剪贴板、邮件、聊天工具和本地文件不受系统删除控制；作为 known limitation / accepted risk 进入 release notes |

## 10. Deferred to Backlog mapping

| Deferred item | 来源文档 | 是否阻断 MVP | 承接阶段 | Owner | Backlog ID | 处理方式 |
|---|---|---|---|---|---|---|
| 真实招聘结果校准 | `SCORING_SPEC.md` §9；`PROMPT_SPEC.md` §13 | 否 | LATER | Scoring owner / Product owner | `AIFI-REL-006` | 下一轮算法 / 校准治理；MVP 用固定 rule version、样例回归和免责声明 |
| 复杂动态权重学习 | `SCORING_SPEC.md` §3 / §9 | 否 | LATER | Scoring owner | `AIFI-REL-006` | 作为 advanced scoring item，不阻断 MVP |
| provider-specific tuning | `PROMPT_SPEC.md` §13；`SECURITY_PRIVACY.md` §9.3 | 否 | LATER | Prompt owner / Security owner | `AIFI-REL-006` | 先保持 provider-independent contract；发布前只检查 failure / retry / privacy |
| queue / worker 物理实现 | `TECH_DESIGN.md` §8；`API_SPEC.md` §13；`PERSISTENCE_MODEL.md` §1 | 否 | F5 / LATER | Backend owner / Release owner | `AIFI-BE-001` / `AIFI-REL-006` | F5 可按 API async contract 选择内部实现；独立 worker 后置 |
| DB vendor-specific DDL / index / migration | `PERSISTENCE_MODEL.md` §1 / §2 | 否 | F5 / F8 | Data owner / Backend owner / Release owner | `AIFI-BE-001` / `AIFI-REL-003` | F5 冻结实现 migration；F8 验证 migration / rollback / restore |
| vector database / embedding model selection | `PROMPT_SPEC.md` §6；`SECURITY_PRIVACY.md` §10 | 否 | LATER | Prompt owner / Data owner / Security owner | `AIFI-REL-006` | MVP 不默认绑定向量库；后续补来源、隐私和删除治理 |
| full observability platform | `SECURITY_PRIVACY.md` §12；本文件 §7 | 否 | F8 / LATER | Release owner / Security owner / Backend owner | `AIFI-REL-004` / `AIFI-REL-006` | F8 先用最小 signals 和 release check；平台化后置 |
| full SIEM / log platform | `SECURITY_PRIVACY.md` §12 / §22 | 否 | LATER | Security owner / Release owner | `AIFI-REL-006` | 当前只要求最小 audit / logs redaction；SIEM 后置 |
| enterprise SSO / OAuth | `SECURITY_PRIVACY.md` §2.2 / §22 | 否 | LATER | Security owner / Product owner | `AIFI-REL-006` | 企业身份后置，不阻断个人工作台 MVP |
| organization / team ACL | `SECURITY_PRIVACY.md` §5 / §22 | 否 | LATER | Security owner / Product owner | `AIFI-REL-006` | MVP 使用 owner boundary；组织权限后置 |
| internet search governance | `PROMPT_SPEC.md` §6；`SECURITY_PRIVACY.md` §19 | 否 | LATER | Prompt owner / Security owner / Product owner | `AIFI-REL-006` | 默认不启用互联网检索；如引入需来源、版权、隐私和 SSRF 治理 |
| advanced backup restore automation | `SECURITY_PRIVACY.md` §13；本文件 §6 / §9 | 否 | F8 / LATER | Data owner / Security owner / Release owner | `AIFI-REL-003` / `AIFI-REL-006` | F8 先做 restore validation；自动化后置 |
| advanced semantic dedup / merge algorithm | `DATA_MODEL.md` §12；`PERSISTENCE_MODEL.md` §9 | 否 | LATER | Data owner / Product owner | `AIFI-REL-006` | MVP 只按候选 / 建议 / 用户确认和 owner-scoped key 防明显重复 |
| advanced release automation | `DELIVERY_PLAN.md` §1；本文件 §11 | 否 | LATER | Release owner | `AIFI-REL-007` | F8 先人工生成 checklist / changelog / runbook；自动化后置 |

## 11. F8 output mapping

| F8 产物 | 从本文件生成的输入 | 不在本轮创建 |
|---|---|---|
| `docs/03-delivery/RELEASE_CHECKLIST.md` | §3 checklist matrix、§7 signals、§8 retry / rate limit、§9 retention / deletion | 本轮不创建正式 release checklist |
| `CHANGELOG.md` | route inventory 变化、known limitations、migration / rollback notes、ScoreRuleVersion / API contract 变化摘要 | 本轮不创建 changelog |
| runbook | §5 runbook source 表、§8 provider / retry policy、§9 privacy handoff | 本轮不创建运行手册成品 |
| known limitations | §4 known limitations、§10 deferred mapping | 本轮不创建独立 known limitations 文档 |
| rollback strategy | §6 rollback / migration / restore handoff、`PERSISTENCE_MODEL.md` migration 风险 | 本轮不创建正式 rollback strategy |
| release retrospective | runbook 事件、release blocker、known limitations、rollback decision、source unavailable / low confidence / provider failure 统计 | 本轮不创建复盘 ADR / Issue |
| next iteration backlog | §10 Deferred to Backlog mapping 和 `BACKLOG.md` 的 `AIFI-REL-*` / LATER 任务 | 本轮只补 Backlog 入口，不启动后续任务 |

## 12. AR-F4-F8-003 verification checklist

| 验收条件 | 当前 handoff 证据 |
|---|---|
| F8 能生成 release checklist / known limitations / runbook / rollback strategy / changelog 输入 / 发布复盘输入 | §3、§4、§5、§6、§11 |
| Deferred 项均有承接阶段、owner、Backlog 入口或不阻断理由 | §10 与 `BACKLOG.md` 的 `AIFI-REL-001` 至 `AIFI-REL-007` |
| 发布前检查覆盖 monitoring / observability、logs、audit、trace | §3、§7、`SECURITY_PRIVACY.md` 发布前 checklist |
| 发布前检查覆盖 provider failure、rate limit、retry | §5、§8、`API_SPEC.md` F8 API 发布检查映射 |
| 发布前检查覆盖 retention、deletion、backup restore | §6、§9、`PERSISTENCE_MODEL.md` migration / rollback / restore handoff |
| 发布前检查覆盖 migration / rollback、secrets、owner boundary | §3、§6、§7、`SECURITY_PRIVACY.md` 发布前 checklist |
| 发布前检查覆盖 copy boundary、no export、no exact probability | §3、§4、`API_SPEC.md` §10 / F8 mapping |
| 发布前检查覆盖 candidate not formal、low confidence、source unavailable、validation failed | §3、§7、§8、`SEMANTICS_GLOSSARY.md`、`DATA_MODEL.md`、`API_SPEC.md` |

## 13. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-17 | 初始化 F8 release handoff canonical spec | 修复 `AR-F4-F8-003` 的 active design handoff 缺口；为 F8 release checklist、known limitations、runbook、rollback strategy、changelog input、release retrospective 和 next iteration backlog 提供输入；不创建 F8 正式产物，不进入 implementation |
