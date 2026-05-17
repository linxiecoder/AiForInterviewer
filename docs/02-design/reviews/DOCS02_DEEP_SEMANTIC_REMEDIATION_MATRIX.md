---
title: DOCS02_DEEP_SEMANTIC_REMEDIATION_MATRIX
type: remediation-matrix
status: pending
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/reviews/docs02-deep-semantic-remediation-matrix
---

# docs/02 设计体系深度语义关联审计整改矩阵

本矩阵只描述 required fix，不代表本轮已经修复。状态仅使用 `Open`，不得写 `Fixed` / `Verified`。

| Finding | Target Active Docs | Required Change | Blocks F5 | Blocks F6 | Blocks F7 | Blocks F8 | Verification Method | Status |
|---|---|---|---|---|---|---|---|---|
| AR-DOCS02-SEM-001 | `API_SPEC.md`、`DATA_MODEL.md`、必要的 `UX_SPEC.md` / `UI_DESIGN_SYSTEM.md`、`SECURITY_PRIVACY.md`、相关 `prompt-contracts/*.md` | 补齐岗位解绑、复盘列表、复盘复制、低置信校对保存、内容沉淀 target-level schema；明确 route、request/response、状态、错误态、owner、幂等、copy audit 和 F7 assertion。 | Yes | Yes | Yes | Partial | grep API inventory 和逐接口详情；检查 UX 页面动作逐项映射；检查 DATA 状态/对象承接；执行 contract fixture review。 | Open |
| AR-DOCS02-SEM-002 | `API_SPEC.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`prompt-contracts/*.md` | 统一 task/status enum、`source_availability` enum、typed refs、`UserConfirmationRef`、candidate/suggestion/confirmation/formal object、copy content vs copy event、real interview sensitive/trust flags、LLM trace 最小化。 | Yes | Yes | Yes | Partial | 对比 API shared schemas、DATA refs、Prompt outputs 和 Security boundaries；检查 no raw prompt/completion/provider payload；构造 F7 enum/ref/copy/confirmation 测试样例。 | Open |
| AR-DOCS02-SEM-003 | `TECH_DESIGN.md`、`API_SPEC.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`BACKLOG.md`、`DOCS_INDEX.md`；前序 review banner 需另行授权 | 建立 F8 release checklist matrix、runbook、rollback/migration、observability、provider failure、known limitations、Deferred->Backlog/Accepted_Risk 映射；同步 current-state 和任务状态表达。 | Partial | Partial | Yes | Yes | 检查 `AR-F4-F8-003` 是否被 active docs 闭环；检查 F8 checklist 能从 active docs 生成；检查 DOCS_INDEX/BACKLOG 与 Pending/Verified 状态无冲突。 | Open |

