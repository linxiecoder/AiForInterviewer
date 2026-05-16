---
title: F4 Full Design Acceptance
type: review
status: active-f4
source_task: AIFI-ARCH-004
permalink: ai-for-interviewer/design/reviews/f4-full-design-acceptance
---

# F4 全量技术设计审计验收记录

Status: Pending

## 1. 审计范围清单

本轮范围覆盖：

- 技术架构：`TECH_DESIGN.md`
- 数据模型：`DATA_MODEL.md`
- 安全隐私：`SECURITY_PRIVACY.md`
- API 契约：`API_SPEC.md`
- Prompt / AI contract registry：`PROMPT_SPEC.md`
- Prompt contract 子文档：`prompt-contracts/*.md`
- PRD / UX / F3 / ADR 只作为上游边界和治理证据
- 旧 `AIFI-ARCH-003` 审计产物只作为前序审计证据

## 2. 已读取 active docs 清单

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/AI_WORKFLOW.md`
- `docs/03-delivery/DELIVERY_PLAN.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/01-product/PRD.md`
- `docs/01-product/REQUIREMENT_TRACEABILITY.md`
- `docs/02-design/UX_SPEC.md`
- `docs/02-design/UI_DESIGN_SYSTEM.md`
- `docs/02-design/TECH_DESIGN.md`
- `docs/02-design/DATA_MODEL.md`
- `docs/02-design/SECURITY_PRIVACY.md`
- `docs/02-design/API_SPEC.md`
- `docs/02-design/PROMPT_SPEC.md`
- `docs/02-design/prompt-contracts/ASSET_CONTRACTS.md`
- `docs/02-design/prompt-contracts/JOB_MATCH_CONTRACTS.md`
- `docs/02-design/prompt-contracts/POLISH_CONTRACTS.md`
- `docs/02-design/prompt-contracts/PRESSURE_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REPORT_CONTRACTS.md`
- `docs/02-design/prompt-contracts/REVIEW_CONTRACTS.md`
- `docs/02-design/prompt-contracts/SHARED_CONTRACTS.md`
- `docs/02-design/prompt-contracts/TRAINING_CONTRACTS.md`
- `docs/02-design/prompt-contracts/WEAKNESS_CONTRACTS.md`
- `docs/04-decisions/ADR-0001-document-governance.md`
- `docs/04-decisions/ADR-0002-unified-delivery-system.md`
- `docs/04-decisions/ADR-0004-ai-collaboration-governance.md`

## 3. 未读取但应读取的文件清单

无。`docs/02-design/prompt-contracts/` 下未发现额外 `.md` 文件。

## 4. Findings 统计

| Severity | Count |
|---|---:|
| Critical | 0 |
| High | 4 |
| Medium | 2 |
| Low | 1 |
| Total | 7 |

Open Critical 数量：0  
Open High 数量：2
Fixed 但未 Verified High 数量：0
Verified High 数量：2

## 5. Critical / High 摘要

| Finding | Severity | Summary |
|---|---|---|
| AR-F4-FULL-001 | High | `F4_TECH_DESIGN` UNKNOWN 仍显式保留，M4 退出标准未满足 |
| AR-F4-FULL-002 | High | `API_SPEC.md` 已从骨架补齐并通过 verification，可作为 F5/F6/F7 API handoff |
| AR-F4-FULL-003 | High | 评分、通过倾向、风险提示和校准口径仍未冻结 |
| AR-F4-FULL-004 | High | `REPORT_CONTRACTS.md` 重新引入 Markdown 下载 / 导出语义，违背 MVP non-goal；当前已 Verified |

## 6. Exit 判定

F4 是否允许退出：否。  
F5 是否允许启动：否。  
F7 是否具备可测试输入：部分具备，但不足以进入全链路验收。

判定依据：

- Critical = 0。
- Open High = 2。
- Fixed 但未 Verified High = 0。
- Verified High = 2。
- 根据 F4 退出判定规则，只要仍存在 Open High，F4 不允许退出，F5 不允许启动；可以继续 remediation / verification，但不能进入 implementation。

## 7. 人工决策项

1. 是否允许任何 Markdown 下载 / export / filename / export snapshot 语义进入 MVP；当前审计建议不允许。
2. API 任务同步 / 异步边界已在 `API_SPEC.md` 作为 F5/F6/F7 handoff 落地并通过 verification：轻量 CRUD / 读取可同步，job match analysis、report generation、review analysis、training suggestion generation、weakness extraction、AI scoring、question generation、feedback generation 等 AI 生成类任务按异步任务协议交接。
3. MVP 评分采用固定公式 / 权重 / 阈值，还是采用 rubric + `ScoreRuleVersion` + 低置信度替代口径。
4. 通过倾向是否展示；若展示，是否只允许趋势性 / 等级性表达。
5. 哪些 `F4_TECH_DESIGN` UNKNOWN 必须在 F4 关闭，哪些可以 Deferred 或 Accepted Risk。
6. F3 `DONE` 是否包含高保真页面交付完成；若包含，需要补齐 `UI_DESIGN_SYSTEM.md` 关闭证据。
7. Prompt contract 子文档中的过期 Stub 关系说明是否统一改为“已 Draft，但不关闭 UNKNOWN / 不自动写正式对象”。

## 8. 必须 remediation 后复核的事项

- `REPORT_CONTRACTS.md` 不再出现下载 / 导出实现语义。当前 AR-F4-FULL-004 已 Verified；本记录仍保持 `Status: Pending`，不是 Accepted。
- `API_SPEC.md` 已从语义骨架补齐到可实现、可测试 contract；当前 AR-F4-FULL-002 已 Verified。
- 评分、风险提示、通过倾向和免责声明可被 F7 fixture 验证。
- `AIFI-ARCH-002` 对 `F4_TECH_DESIGN` UNKNOWN 给出关闭 / 后置 / 接受风险状态。
- 进展树、暂停恢复、异步任务、幂等、重试和 timeout 状态机可测试。
- F3 / F6 设计交接状态一致。
- prompt-contract 子文档不再保留与当前 registry 冲突的 Stub 状态说明。

## 9. MCP approval 状态占位

本轮完成后只为以下三个文档创建 approval request：

- `docs/02-design/reviews/F4_FULL_DESIGN_ADVERSARIAL_REVIEW.md`
- `docs/02-design/reviews/F4_FULL_DESIGN_RISK_REGISTER.md`
- `docs/02-design/reviews/F4_FULL_DESIGN_REMEDIATION_MATRIX.md`

不为本验收记录创建最终 acceptance approval。原因：当前 `Status: Pending`，且仍有 Open High findings 尚未 remediation / verification。

## 10. 当前结论

本验收记录不是 Accepted。Open High 关闭前，F4 全量设计只能进入 remediation / verification，不能进入 F5 implementation。
