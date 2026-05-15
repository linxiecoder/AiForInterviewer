---
title: F4 Prompt / Security / Tech Acceptance
type: review
status: active-f4
permalink: ai-for-interviewer/design/reviews/f4-prompt-security-tech-acceptance
---

# F4 Prompt / 安全隐私 / 技术设计审查验收记录

## 1. 验收结论

审查产物当前状态：已吸收本轮 Dashboard Request Changes / Reject 批注，等待重新审批。

AIFI-ARCH-003 收口结论：不收口。继续推进 remediation，直到 High findings 关闭。

设计 readiness 结论：Blocked for F5/F7 full implementation.

原因：本轮登记 8 个 findings，其中 5 个 High。阻断集中在 Stub Prompt contracts、API handoff、报告通过倾向、真实复盘隐私 / 注入、正式写入边界。当前 F4 设计不能直接作为 F5/F7 的完整实现和验收依据，本文件也不构成最终验收通过。

## 2. Findings 统计

| Severity | Count |
| --- | ---: |
| Critical | 0 |
| High | 5 |
| Medium | 3 |
| Low | 0 |
| Total | 8 |

## 3. Critical / High 列表

| Finding ID | Severity | Title | Blocking Scope |
| --- | --- | --- | --- |
| AR-F4-001 | High | 核心业务 Prompt contract 仍为 Stub，无法支撑 F5/F7 负例与验收 | F5/F7 full implementation |
| AR-F4-002 | High | API handoff 缺口会把 Prompt 状态误当成接口合同 | API/backend/frontend handoff |
| AR-F4-004 | High | Report 风险提示合同未定义，精确通过概率禁令缺少落点 | Report scoring and product non-goal |
| AR-F4-005 | High | Real Interview Review 合同缺失会放大第三方隐私和 prompt injection 风险 | Review privacy and injection safety |
| AR-F4-006 | High | 候选资产 / 薄弱项 / 训练建议到正式事实的写入边界不足 | Formal persistence and user confirmation |

## 4. Acceptance Gate

| Gate | Status | Evidence / Rationale |
| --- | --- | --- |
| 必审文档已覆盖 | Pass | 已审 `TECH_DESIGN.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`prompt-contracts/*.md`。 |
| 只读参考文档未作为当前执行依据 | Pass | `PRD.md`、`DATA_MODEL.md` 仅用于交叉验证需求、对象和状态边界。 |
| 未使用 archive 作为当前事实源 | Pass | 本轮 findings 不引用 archive 作为 current basis。 |
| 子文档新增未登记 `P-*` ID | Pass | 未发现 child-only `P-*` ID。 |
| Prompt injection / exfiltration 场景覆盖 | Partial | Shared / Security 有原则，但 Report / Review / Weakness / Asset / Training Stub 无合同级 fixture。 |
| LLM privacy 最小化输入覆盖 | Partial | Security 有原则，部分业务 Stub 尚未落地到 contract。 |
| RAG evidence owner/source/version/snapshot/trace 覆盖 | Partial | Shared 有规则，业务 key claim list 未定义。 |
| Output schema / failure / low confidence 覆盖 | Partial | Prompt 模板完整，但多个核心业务 contract 未填充。 |
| 静默写入 / 静默覆盖防护 | Partial | Security / Data 有边界，正式 Weakness / Asset / Training contract 未填充。 |
| API handoff 可实施性 | Fail | `API_SPEC.md` 未落地，Prompt 状态不能替代接口合同。 |
| F5/F7 fixture readiness | Fail | 5 个 High 风险阻断完整 fixture 和验收断言。 |

## 5. 已吸收人工决策

| Decision ID | Decision | Required Follow-up |
| --- | --- | --- |
| D-F4-PST-001 | AIFI-ARCH-003 不按“审查完成但设计阻断”收口；继续推进 remediation，直到 High findings 关闭。 | High findings 关闭前不得创建最终验收 approval，也不得把 acceptance 标记为通过。 |
| D-F4-PST-002 | `API_SPEC.md` 是 F5 前置硬门槛；至少 AI 相关接口状态、错误语义、异步 / 同步模式必须在 F5 前冻结。 | `API_SPEC.md` 补齐前，F5 backend implementation 不能进入完整 handoff。 |
| D-F4-PST-003 | 报告允许趋势性、等级性风险提示；禁止精确通过概率；展示必须绑定评分版本和 evidence。 | Report contract completion 必须包含 allowed wording、forbidden wording、score version 和 evidence binding fixture。 |
| D-F4-PST-004 | 真实面试复盘的第三方 / 公司信息默认脱敏；原文不进入 LLM；展示层只显示用户确认后的摘要。 | Review contract completion 必须覆盖 raw text 不入模、摘要确认和展示边界。 |
| D-F4-PST-005 | AI 输出不得自动创建正式资产、薄弱项或训练建议；只能生成 candidate / draft，并经用户确认后转正式事实。 | Weakness / Asset / Training persistence 必须要求 `UserConfirmationRef`，并覆盖静默写入 / 覆盖负例。 |
| D-F4-PST-006 | F5 AI 任务采用混合编排：轻量任务同步，报告 / 训练 / 复盘类任务异步；必须定义 retry、idempotency 和 rate limit。 | `API_SPEC.md` 和 backend orchestration 必须按任务类型冻结同步 / 异步模式、retry budget、idempotency key 和 rate limit。 |

## 6. Exit Criteria for Design Readiness

F4 Prompt / Security / Tech 进入 F5/F7 full readiness 前，至少需要满足：

- `API_SPEC.md` 已存在并覆盖 AI 任务 endpoint、schema、error、auth、owner、retry、idempotency 和 frontend-visible state。
- `API_SPEC.md` 已冻结 AI 相关接口状态、错误语义、异步 / 同步模式、retry、idempotency 和 rate limit。
- Report / Review / Weakness / Asset / Training Prompt contracts 脱离 Stub，具备完整模板字段。
- `P-REPORT-003` 明确禁止精确通过概率，仅允许趋势性 / 等级性提示，并提供评分版本、evidence binding 和负例 fixture。
- Review contracts 覆盖真实复盘的第三方隐私、公司信息、默认脱敏、原文不入 LLM、用户确认摘要、source trust、完整性、prompt injection 和禁止预测。
- Weakness / Asset / Training contracts 明确 AI 只能生成 candidate / draft，formal fact 必须经用户确认，并具备版本、trace、owner、合并和覆盖规则。
- 每类业务输出有 key claim list，缺失 owner/source/version/snapshot/trace 时不得输出正式关键结论。
- Runtime failure policy 覆盖 timeout、rate limit、RAG unavailable、validation failed、重复提交和取消 / 重试。

## 7. 本轮产物验收

| Artifact | Status |
| --- | --- |
| `F4_PROMPT_SECURITY_TECH_ADVERSARIAL_REVIEW.md` | Revised, pending Dashboard approval |
| `F4_PROMPT_SECURITY_TECH_RISK_REGISTER.md` | Revised, pending Dashboard approval |
| `F4_PROMPT_SECURITY_TECH_REMEDIATION_MATRIX.md` | Revised, pending Dashboard approval |
| `F4_PROMPT_SECURITY_TECH_ACCEPTANCE.md` | Updated as blocking record; no final acceptance approval requested |

本验收记录不修改 `PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`TECH_DESIGN.md` 或 `prompt-contracts/*.md`，也不关闭这些文档中的 UNKNOWN。

本验收记录不是最终通过判定。High findings 关闭前，AIFI-ARCH-003 维持 Blocked。
