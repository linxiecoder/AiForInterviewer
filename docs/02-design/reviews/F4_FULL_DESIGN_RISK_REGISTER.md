---
title: F4 Full Design Risk Register
type: review
status: active-f4
source_task: AIFI-ARCH-004
permalink: ai-for-interviewer/design/reviews/f4-full-design-risk-register
---

# F4 全量技术设计风险登记表

## 1. 登记结论

本风险登记表记录 `AIFI-ARCH-004` 全量 F4 设计对抗性审计发现，并在后续授权 remediation 中追踪处置状态。初始审计轮登记 7 项风险：0 Critical、4 High、2 Medium、1 Low。

Status 只使用 `Open`、`Fixed`、`Deferred`、`Accepted_Risk`、`Rejected_False_Positive`、`Verified`。`Fixed` 表示 active docs 已完成回写但尚未复核通过；`Deferred` 表示已明确为非当前 M4 / F5 阻断并绑定后续阶段、任务和验证策略；`Verified` 表示本轮 verification 已确认关闭条件满足。

## 2. Risk Register

| ID | Severity | Category | Source | Affected Downstream | Risk | Required Fix | Required Decision | Status | Owner | Close Condition |
|---|---|---|---|---|---|---|---|---|---|---|
| AR-F4-FULL-001 | High | Scope / Governance / Testability | `TECH_DESIGN.md` §16 / §18; `DATA_MODEL.md` §12; `PROMPT_SPEC.md` §13; `API_SPEC.md` §11 / §12; `SECURITY_PRIVACY.md` §22 / §23; `prompt-contracts/*.md` | F5 Backend; F6 Frontend; F7 QA | F4 active docs 的 UNKNOWN 处置表、已冻结设计结论和 deferred_non_blocking 边界已通过 verification | 已复核 TECH / DATA / API / PROMPT / SECURITY / prompt-contracts 中阻断式 `F4_TECH_DESIGN` UNKNOWN 已改为已冻结、已处置或 deferred_non_blocking | 无新增人工阻断决策；`BACKLOG.md` / `DOCS_INDEX.md` 因本轮禁止修改未更新 | Verified | Architecture owner | Verification 已确认所有 F4 UNKNOWN 有处置状态，F7 可验证关闭状态 |
| AR-F4-FULL-002 | High | API / Reliability / Testability | `API_SPEC.md` §1-§10；`TECH_DESIGN.md` §14.1 / §16 / §18；`SECURITY_PRIVACY.md` §21 / §23 | F5 Backend; F6 Frontend; F7 QA | API 契约已从骨架回写并复核为 F5/F6/F7 handoff | 已复核完整 API contract、失败状态协议、endpoint matrix、async task、幂等、rate limit 和 F7 assertions | 同步 / 异步分界、idempotency key、rate limit 维度已在 `API_SPEC.md` 落地，并已通过本轮 verification | Verified | API / Backend owner | F7 可直接从 API_SPEC 生成 contract tests，且 verification 确认无骨架残留 |
| AR-F4-FULL-003 | High | Scoring / Prompt / Testability | `TECH_DESIGN.md` §14.2; `DATA_MODEL.md` §5.5.2 / §10 / §12; `API_SPEC.md` §4.4 / §9; `PROMPT_SPEC.md` §7.2; Prompt scoring contracts; `SECURITY_PRIVACY.md` §17.1 | F5 Backend; F6 Frontend; F7 QA | 评分、通过倾向、风险提示和校准口径已完成 active docs remediation；本轮 verification 已确认 `P-POLISH-004` / `P-PRESSURE-008` remaining gaps 关闭 | 保持已冻结的 0-100 产品评分刻度、rubric / rule version、版本字段、通过倾向分档、risk wording、免责声明、低置信度降级和 F7 fixture；不得标记整体 Accepted | 采用 rubric / rule version；真实结果校准后置为 LATER / SHOULD | Verified | Product / Architecture / Prompt owner | F7 可验证评分、低置信、风险提示、版本字段和禁止精确概率；Polish / Pressure score contract 不再保留冲突开放项，且 verification 已通过 |
| AR-F4-FULL-004 | High | Scope / Prompt / Security / Privacy | `PRD.md` §5.7 / §9; `TECH_DESIGN.md` §4 / §12; `SECURITY_PRIVACY.md` §14 / §22; `REPORT_CONTRACTS.md` §3.0 / §3.4 | F5 Backend; F6 Frontend; F7 QA | Report contract 重新引入 Markdown 下载 / 导出语义，违背 MVP non-goal | 从 Report contract 删除 download/export/filename/snapshot 语义，收敛为页面复制 | `P-REPORT-004` 是否只允许复制，不允许任何下载 / export | Verified | Prompt / Security / Product owner | active docs 只保留复制能力；导出命中仅存在于 non-goal / deferred / finding；verification 已通过 |
| AR-F4-FULL-005 | Medium | State / Reliability / Testability | `DATA_MODEL.md` §5.5 / §12; `API_SPEC.md` §5 / §6 / §9; `SHARED_CONTRACTS.md` §10.6; `PRESSURE_CONTRACTS.md` §3.0 / §14 | F5 Backend; F6 Frontend; F7 QA | 进展树、暂停恢复、异步失败和重试状态机已回写并通过 focused verification | 已冻结打磨 / 压力面暂停恢复最小快照、进展树状态机、status query、retry、cancel、timeout、partial、source unavailable 和恢复失败可见状态 | 打磨 / 压力面均允许暂停恢复；失败路径由 API async task、session summary 和 F7 fixture 承接 | Verified | Data / API / SRE owner | F7 可覆盖 pause / resume / resume failed / partial / timeout / source unavailable / low confidence inherited |
| AR-F4-FULL-006 | Medium | Governance / Frontend Handoff | `DELIVERY_PLAN.md` §3; `UI_DESIGN_SYSTEM.md` §22 / §23 / §24 | F6 Frontend; F7 QA | F3 标为 DONE，但 UI_DESIGN_SYSTEM 仍登记高保真 UNKNOWN / NOT_STARTED；该冲突属于 F3 / F6 设计交接治理，不改变 F4 技术设计事实 | 后续在 F6 前端启动前统一 DELIVERY 与 UI_DESIGN_SYSTEM 状态口径；本轮禁止修改 DELIVERY / UI F3 文档，因此不在 M4 关闭 | F3 DONE 是否包含高保真页面完成需由 F6 handoff / M3-F6 设计复核窗口确认 | Deferred | Delivery / UI owner | 不阻断 M4 或 F5；F6 / F7 进入页面实现和视觉验收前必须区分 approved / candidate / UNKNOWN design input |
| AR-F4-FULL-007 | Low | Governance / Prompt | `PROMPT_SPEC.md` §10 / §14; `POLISH_CONTRACTS.md` §15; `PRESSURE_CONTRACTS.md` §13 / §14; `REPORT_CONTRACTS.md` §3.5; `REVIEW_CONTRACTS.md` §4.5; `WEAKNESS_CONTRACTS.md` §3.5; `ASSET_CONTRACTS.md` §3.4 | PROMPT_SPEC; F7 QA | 子文档过期 Stub 关系说明已更新为当前 Draft registry 事实和候选 / 建议 / 用户确认边界 | 已更新关系说明，统一为当前 Draft 事实，且保留 UNKNOWN / deferred_non_blocking / 不自动写正式对象边界 | 无新增产品决策；统一采用“已 Draft，但不关闭 deferred_non_blocking / 不自动写正式对象”口径 | Verified | Prompt / Governance owner | 过期 Stub 说明不再命中；真实 Stub 仅保留在主文件模板或历史变更记录中 |

## 2.1 Actual Fix Summary

| ID | Actual Fix Summary | Verification State |
|---|---|---|
| AR-F4-FULL-001 | 已将 `TECH_DESIGN.md` 增加 F4 UNKNOWN 收敛与后置边界表，明确评分、API、数据结构、Prompt contract、模型结果状态、安全边界、候选 / 正式对象、资产回流、真实面试复盘、文件导出 non-goal 和复杂算法后置关系；`DATA_MODEL.md` 将 `DM-UNK-*` 改为 F4 待决策项处置表，冻结简历 / 岗位版本、项目经历表达版本、暂停恢复最小快照、进展树最小状态、复盘切分、trace / evidence、候选 / 正式对象和训练 / 资产 / 弱项 deferred_non_blocking 边界；`API_SPEC.md` 明确 endpoint、error envelope、async task、retry、idempotency、rate limit、permission、copy boundary 和 F7 assertion 已可交接；`PROMPT_SPEC.md` 和 `prompt-contracts/*.md` 将 Open Questions 统一改为已冻结边界或 deferred_non_blocking；`SECURITY_PRIVACY.md` 明确 owner、visibility、LLM 输入最小化、provider payload、system prompt、隐藏评分规则、日志、trace、copy boundary 和第三方隐私边界。未修改 `BACKLOG.md`、`DOCS_INDEX.md`、Medium / Low finding 状态、业务代码或 final acceptance approval。 | Verified |
| AR-F4-FULL-002 | 已将 `API_SPEC.md` 从“不定义完整 endpoint”的骨架改为 F5/F6/F7 可交接 API contract：补齐 base path / versioning、auth / session assumption、owner boundary、response / error envelope、pagination、sorting、filtering、idempotency、rate limit、request id / trace id、async task id、标准错误码、同步 / 异步策略、AI task create / status / result / retry / cancel 协议、核心 endpoint matrix、candidate / suggestion / confirmation 写入边界、报告 copy content 与 no export 边界、F7 可测试性矩阵；并最小同步 `TECH_DESIGN.md` 与 `SECURITY_PRIVACY.md` 中 API handoff 当前性。未修改业务代码，未修改 prompt-contracts 正文，未处理其它 finding。 | Verified |
| AR-F4-FULL-003 | 已将评分、通过倾向、风险提示和校准口径回写到主要 active docs：`TECH_DESIGN.md` 新增专项规则；`DATA_MODEL.md` 补 `ScoreResult`、`ScoreRuleVersion`、`risk_level`、`confidence_level`、`score_version` / `rubric_version` 和历史解释规则；`API_SPEC.md` 补评分 / 风险响应语义和 F7 断言；`PROMPT_SPEC.md` 与 `SHARED_CONTRACTS.md` 冻结 scoring candidate 校验、禁止精确概率、低置信度降级；`JOB_MATCH_CONTRACTS.md` 与 `REPORT_CONTRACTS.md` 同步 output schema / validation / fallback；`SECURITY_PRIVACY.md` 补隐藏评分规则、provider payload、第三方隐私和 copy content 边界。本轮 verification 已确认 `POLISH_CONTRACTS.md` 的 `P-POLISH-004` 与 `PRESSURE_CONTRACTS.md` 的 `P-PRESSURE-008` 补齐 `score_version` / `rubric_version` / confidence / evidence / validation / trace 字段，Pressure 补 `risk_level` / `risk_reason`，且不再保留 scoring UNKNOWN 开放项。本轮未处理 AR-F4-FULL-001、Medium、Low，未进入 implementation，未标记 acceptance。 | Verified |
| AR-F4-FULL-004 | 已将 `REPORT_CONTRACTS.md` 的 Report 公共 action 和 `P-REPORT-004` 从 Markdown 下载 / 文件产物语义改为报告内容复制 / copy content；明确 MVP 不生成 PDF、Markdown 文件、Word / docx 或批量文件；复制内容不得包含 `system prompt`、provider payload、隐藏评分规则或未经脱敏的第三方 / 公司 / 个人敏感信息；`API_SPEC.md` 已补充报告 API 只提供读取和复制所需内容，不提供下载 / 导出 endpoint。 | Verified |
| AR-F4-FULL-005 | 已将暂停恢复状态机补齐到 active docs：`DATA_MODEL.md` 明确打磨 / 压力面共享最小恢复快照、`source_session_snapshot_ref`、`covered_turn_refs`、`ProgressPosition`、恢复失败、来源不可用、partial 和低置信度继承；`API_SPEC.md` 已有 async task status / retry / cancel / timeout，并新增压力面 `PATCH /api/v1/pressure-sessions/{session_id}` 状态更新 endpoint 与 F7 pause / resume state-machine assertion；`SHARED_CONTRACTS.md` 已定义 `summary_failed`、`pause_snapshot_unavailable`、`resume_failed`、`low_confidence_inherited` 等状态。未进入 implementation。 | Verified |
| AR-F4-FULL-006 | 本轮判定为 Deferred：证据来自 `DELIVERY_PLAN.md` F3 DONE 与 `UI_DESIGN_SYSTEM.md` §22 / §23 的 UNKNOWN / NOT_STARTED / candidate 状态并存；该问题属于 F3 / F6 设计交接治理，不属于 F4 active technical design truth。由于本轮禁止修改非 F4 active design docs，未修改 `DELIVERY_PLAN.md` 或 `UI_DESIGN_SYSTEM.md`。 | Deferred |
| AR-F4-FULL-007 | 已将 `POLISH_CONTRACTS.md`、`PRESSURE_CONTRACTS.md`、`REPORT_CONTRACTS.md`、`REVIEW_CONTRACTS.md`、`WEAKNESS_CONTRACTS.md` 和 `ASSET_CONTRACTS.md` 的过期“仍保持 Stub”关系说明改为当前 Draft registry 事实，并明确候选 / 建议 / 用户确认边界、不得自动写正式对象、deferred_non_blocking 不被关闭。未新增 contract ID，未改变主 registry 状态。 | Verified |

## 2.2 Verification Summary

| ID | Verification Summary | Verification State |
|---|---|---|
| AR-F4-FULL-001 | 已复核 F4 active docs 不再存在阻断 M4 的 `F4_TECH_DESIGN` UNKNOWN；`UNKNOWN` 命中仅为 PRD / DELIVERY 历史输入、F4 UNKNOWN 收敛标题、审计追踪或非阻断分类；`TECH_DESIGN.md` §16、`DATA_MODEL.md` §12、`API_SPEC.md` §11、`PROMPT_SPEC.md` §13、`SECURITY_PRIVACY.md` §22 和 `prompt-contracts/*.md` 均将 must-close 项改为已冻结设计结论，复杂算法、provider 选择、UX 文案、企业治理、文件解析 / 导出等均明确为 deferred_non_blocking / non-goal；未发现 `requires_human_decision` 或 must_close_in_F4 未关闭项。 | Verified |
| AR-F4-FULL-002 | 已复核 `API_SPEC.md` 明确为 F5 后端实现、F6 前端接入和 F7 API contract tests 的前置硬门槛；全局约定覆盖 `/api/v1`、auth / session、owner boundary、response / error envelope、pagination / sorting / filtering、idempotency、rate limit、request / trace id、async task id 与标准错误码；endpoint matrix 覆盖核心资源域，且每行具备 method、path、purpose、request、response、error cases、owner check、idempotency、related data objects、related prompt contract 和 F7 assertion；async task protocol 覆盖 create / status / result / retry / cancel、idempotency、timeout、failure 和 user-visible status；F7 matrix 覆盖 success、validation failed、cross-user、source unavailable、low confidence、generation failed、idempotent retry、stale conflict、no export endpoint 和 copy boundary；`TECH_DESIGN.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`PROMPT_SPEC.md` 与该 handoff 边界一致。 | Verified |
| AR-F4-FULL-003 | 本轮已复核主要 active docs 的 0-100 产品刻度、禁止精确概率、rule / rubric version、通过倾向分档、风险证据绑定、低置信度降级、copy boundary 和 F7 断言；并定向复核上轮 remaining gaps：`POLISH_CONTRACTS.md` 的 `P-POLISH-004` 已补齐 `score_version`、`rubric_version` / `rule_version`、`confidence_level`、`validation_status`、`generated_by_task_id`、`risk_level=not_applicable`、`evidence_refs` / `trace_refs` 等字段，并明确为单轮 polish scoring candidate；`PRESSURE_CONTRACTS.md` 的 `P-PRESSURE-008` 已补齐 `score_version`、`rubric_version` / `rule_version`、`confidence_level`、`validation_status`、`generated_by_task_id`、`risk_level`、`risk_reason`、`evidence_refs` / `trace_refs` 等字段，并明确为 pressure session scoring candidate / draft。未发现允许精确概率、隐藏评分规则外泄或评分 / 通过倾向 UNKNOWN 重新阻断本 finding。整体 acceptance 仍保持 Pending。 | Verified |
| AR-F4-FULL-004 | 已复核 `REPORT_CONTRACTS.md` 无 `download` / `export` / `下载` / `导出` / `filename` / `MarkdownExport` 命中；`CopyableReportContent` 仅作为可复制内容对象并明确不是外部文件产物；`API_SPEC.md` 明确不提供文件下载 / 导出 endpoint；`SECURITY_PRIVACY.md` 保持页面复制、复制审计、Deferred 下载和 non-goal 边界一致；未发现 archive、snapshot file、report file、markdown artifact 或 downloadable content 等替代命名承接文件导出能力。 | Verified |
| AR-F4-FULL-005 | 已复核 `DATA_MODEL.md` 的最小恢复快照、`ProgressTree` / `ProgressNode` / `ProgressPosition`、`SessionSummary`、`covered_turn_refs`、会话状态、摘要状态和进展节点状态；`API_SPEC.md` 的 AI task create / status / result / retry / cancel、压力面 pause / resume / end / mark_resume_failed endpoint、F7 pause / resume assertion；`SHARED_CONTRACTS.md` 的 summary failure / resume failure / low confidence inherited 语义；`PRESSURE_CONTRACTS.md` 的 pause / resume next action。当前可形成 F7 fixture，不再保持 Open。 | Verified |
| AR-F4-FULL-006 | 本轮只做 triage，不修改 F3 / delivery 文档。Deferred 理由：该 finding 不改变 F4 技术设计事实，不阻断 M4 或 F5 后端启动；它影响 F6 UI 输入可信度和 F7 视觉 / 交互验收，承接阶段为 F6 前端启动前设计交接复核，承接任务为 `AIFI-FE-001` 前置 handoff gate 或后续独立 F3/F6 状态同步任务。 | Deferred |
| AR-F4-FULL-007 | 已复核过期关系说明清理结果：`rg -n "仍保持 Stub|仍是 Stub|保持 Stub" docs/02-design/PROMPT_SPEC.md docs/02-design/prompt-contracts` 不再命中过期状态说明；主 `PROMPT_SPEC.md` 中 `Stub` 仅保留为状态定义、单个 Contract Stub 模板或历史变更记录。 | Verified |

## 3. Critical / High Blocking Scope

| ID | Blocks F4 Exit | Blocks F5 | Blocks F7 | Reason |
|---|---|---|---|---|
| AR-F4-FULL-001 | No | No | No | 已 Verified；active docs 的 F4 UNKNOWN 均已关闭、已处置或 deferred_non_blocking，不再因本 finding 阻断 F4 / F5 / F7 |
| AR-F4-FULL-002 | No | No | No | 已 Verified；API handoff 不再因本 finding 阻断 F4 / F5 / F7 |
| AR-F4-FULL-003 | No | No | No | 已通过本轮 verification；本 finding 不再阻断 F4 / F5 / F7 |
| AR-F4-FULL-004 | No | No | No | 已验证为页面复制边界，不再因本 finding 阻断退出 |

## 3.1 Medium / Low Triage Scope

| ID | Severity | Final Status | Blocks F4 Exit | Blocks F5 | Blocks F7 | Reason |
|---|---|---|---|---|---|---|
| AR-F4-FULL-005 | Medium | Verified | No | No | No | 暂停恢复、进展树、async failure、retry、timeout、partial 和 source unavailable 已在 DATA / API / Shared / Pressure 边界形成可执行状态机与 F7 fixture |
| AR-F4-FULL-006 | Medium | Deferred | No | No | Yes | F3 / F6 交接状态冲突不改变 F4 技术设计事实，也不影响 F5 后端启动；必须在 F6 页面实现前完成 approved / candidate / UNKNOWN 输入分层 |
| AR-F4-FULL-007 | Low | Verified | No | No | No | 过期 Stub 关系说明已清理，当前 Draft registry 与子文档关系说明一致 |

## 4. Residual Risk

即使完成本轮整改，仍需在 F5 / F7 验证：

- 实际 API / service / persistence 是否强制 owner 过滤。
- LLM / RAG failure 是否不保存 raw prompt、completion 或 provider payload。
- `source_unavailable`、`validation_failed`、`low_confidence` 是否不被 UI 静默吞掉。
- Report copy 在本轮验证中已确认严格停留在页面复制；后续实现仍需在 F5 / F7 按无文件生成、无文件下载和复制审计继续回归。
- `API_SPEC.md` 已补齐并通过本轮 verification；后续 F5 / F7 仍需用 contract tests 防止实现偏离 API contract。
- F3 / F6 交接状态是否有人工确认或 active docs 关闭证据。
