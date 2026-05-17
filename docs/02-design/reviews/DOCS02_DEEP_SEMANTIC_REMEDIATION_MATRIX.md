---
title: DOCS02_DEEP_SEMANTIC_REMEDIATION_MATRIX
type: remediation-matrix
status: pending
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/reviews/docs02-deep-semantic-remediation-matrix
---

# docs/02 设计体系深度语义关联审计整改矩阵

本矩阵描述 required fix 与已执行 remediation。状态允许 `Open` / `Fixed`；`Fixed` 表示已回写 active docs、等待独立 verification，不得写 `Verified`。

| Finding | Target Active Docs | Required Change | Actual Change | Blocks F5 | Blocks F6 | Blocks F7 | Blocks F8 | Verification Method | Status |
|---|---|---|---|---|---|---|---|---|---|
| AR-DOCS02-SEM-001 | `API_SPEC.md`、`DATA_MODEL.md`、`TECH_DESIGN.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`prompt-contracts/REVIEW_CONTRACTS.md` | 补齐岗位解绑、复盘列表、复盘复制、低置信校对保存、内容沉淀 target-level schema；明确 route、request/response、状态、错误态、owner、幂等、copy audit 和 F7 assertion。 | 已新增 / 回写 `API-BINDING-002`、`API-REVIEW-005`、`API-REVIEW-006`、`API-REVIEW-007`、`API-CANDIDATE-001`、`API-DEPOSIT-001`；DATA 增加 `ReviewSummary`、`CopyableReviewContent`、`ReviewCopyEvent`、`CandidateCorrection`、`UserCorrectionRef`、`DepositTarget`；TECH 增加 F6 handoff 规则；PROMPT / REVIEW 明确校对和沉淀目标只走候选 / 建议 / 确认链路；SECURITY 增加 owner、脱敏、copy audit no body 和 target scope 边界。 | Pending Verification | Pending Verification | Pending Verification | Pending Verification | grep API inventory 和逐接口详情；检查 UX 页面动作逐项映射；检查 DATA 状态/对象承接；检查 Prompt / Security 不静默写正式对象且不记录敏感正文；执行 F7 contract fixture review。 | Fixed |
| AR-DOCS02-SEM-002 | `API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`prompt-contracts/*.md` | 统一 task/status enum、`source_availability` enum、typed refs、`UserConfirmationRef`、candidate/suggestion/confirmation/formal object、copy content vs copy event、real interview sensitive/trust flags、LLM trace 最小化。 | N/A（本轮不处理） | Yes | Yes | Yes | Partial | 对比 API shared schemas、DATA refs、Prompt outputs 和 Security boundaries；检查 no raw prompt/completion/provider payload；构造 F7 enum/ref/copy/confirmation 测试样例。 | Open |
| AR-DOCS02-SEM-003 | `TECH_DESIGN.md`、`API_SPEC.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`BACKLOG.md`、`DOCS_INDEX.md`；前序 review banner 需另行授权 | 建立 F8 release checklist matrix、runbook、rollback/migration、observability、provider failure、known limitations、Deferred->Backlog/Accepted_Risk 映射；同步 current-state 和任务状态表达。 | N/A（本轮不处理） | Partial | Partial | Yes | Yes | 检查 `AR-F4-F8-003` 是否被 active docs 闭环；检查 F8 checklist 能从 active docs 生成；检查 DOCS_INDEX/BACKLOG 与 Pending/Verified 状态无冲突。 | Open |
