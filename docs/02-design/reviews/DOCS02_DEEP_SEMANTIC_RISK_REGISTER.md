---
title: DOCS02_DEEP_SEMANTIC_RISK_REGISTER
type: risk-register
status: pending
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/reviews/docs02-deep-semantic-risk-register
---

# docs/02 设计体系深度语义关联审计风险登记表

本登记表只记录 AIFI-ARCH-006 本轮审计发现。状态允许 `Open`、`Fixed`、`Deferred`、`Accepted_Risk`、`Rejected_False_Positive`。`Fixed` 表示已回写 active docs、等待独立 verification；本登记表不得写 `Verified`。

| ID | Severity | Category | Affected Chain | Source | Risk | Required Fix | Actual Fix Summary | Status | Owner | Close Condition |
|---|---|---|---|---|---|---|---|---|---|---|
| AR-DOCS02-SEM-001 | High | Product Semantics / UX Handoff / API / Data / F6 / F7 | PRD -> UX -> UI -> DATA -> API -> F5 -> F6 -> F7 | `PRD.md`、`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`API_SPEC.md`、`DATA_MODEL.md` | UX 可见任务到 API / DATA 仍有断链，包含岗位解绑、复盘列表、复盘复制、低置信校对保存和内容沉淀目标级写入。 | 基于既有 UX / UI 动作回写 `API_SPEC.md`、`DATA_MODEL.md`、`TECH_DESIGN.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md` 和相关 prompt contract，补齐 route、schema、状态、错误态、owner、幂等、复制审计和 F7 assertion。 | 已回写五个断链点：岗位-简历解绑 API / DATA / F6 / F7；复盘列表 API / summary projection / 状态 / F7；复盘复制 copy-content / copy-event / 脱敏 / audit no body；低置信候选校对保存 `CandidateCorrection` / `UserCorrectionRef`；内容沉淀 `DepositTarget` / target owner scope / Prompt 只建议不静默写入。 | Fixed | F4 design owners | F6 不再需要猜核心接口或拼接核心信息，F7 能为全部列出的 UX 动作执行 contract / E2E 断言；仍需独立 verification 后才可关闭。 |
| AR-DOCS02-SEM-002 | High | API / Data / Prompt / Security / F5 / F6 / F7 | API -> DATA -> PROMPT -> SECURITY -> F5 -> F6 -> F7 | `API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`prompt-contracts/*.md` | status enum、source availability、typed refs、confirmation schema、copy event、real interview sensitive flags 和 LLM trace 语义未完全归一。 | 回写 API/DATA/PROMPT/SECURITY 和相关 prompt contracts，统一 enum、refs、confirmation、copy content vs copy event、real interview flags 和 trace 最小化。 | N/A（本轮不处理） | Open | F4 design owners | 任意 Prompt 输出可映射到 API/DATA；任意 API shared schema 可映射到 DATA；Security copy/log/trace 边界可由 F7 验证。 |
| AR-DOCS02-SEM-003 | High | F8 / Governance / Security / API / Data | TECH -> DATA -> API -> SECURITY -> BACKLOG -> DOCS_INDEX -> F8 | `DELIVERY_PLAN.md`、`BACKLOG.md`、`DOCS_INDEX.md`、`F4_TO_F8_READINESS_*`、`API_SPEC.md`、`SECURITY_PRIVACY.md` | F8 release / ops / retrospective 输入仍未闭合，`AR-F4-F8-003` Open；治理事实源与 review Pending/Verified 状态存在漂移。 | 回写 TECH/API/DATA/SECURITY/BACKLOG/DOCS_INDEX，建立 release checklist matrix、runbook、rollback/migration、observability、Deferred->Backlog 映射和 current-state 表达。 | N/A（本轮不处理） | Open | F4/F8 governance owners | F8 release checklist 可由 active docs 生成；Deferred 项均被 Backlog / Accepted_Risk / Non-goal 承接；DOCS_INDEX/BACKLOG 不再冲突。 |
