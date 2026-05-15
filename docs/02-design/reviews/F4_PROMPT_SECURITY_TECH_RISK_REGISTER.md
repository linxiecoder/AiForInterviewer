---
title: F4 Prompt / Security / Tech Risk Register
type: review
status: active-f4
permalink: ai-for-interviewer/design/reviews/f4-prompt-security-tech-risk-register
---

# F4 Prompt / 安全隐私 / 技术设计风险登记表

## 1. 登记结论

本风险登记表只记录 AIFI-ARCH-003 对抗性审查发现，不修复原始设计文档。当前登记 8 项风险：0 Critical、5 High、3 Medium、0 Low。

整体风险判断：F4 Prompt / Security / Tech 设计可以作为继续补齐合同的基础，但不能直接作为 F5/F7 全量实施和验收依据。

Dashboard 批注已将 6 个原待决项转化为明确约束；这些约束降低了决策歧义，但不关闭对应 High 风险。所有 High 风险仍保持 Open，直到 active design docs 和后续验证补齐。

## 2. 风险登记

| Risk ID | Finding ID | Severity | Category | Risk Statement | Affected Area | Likelihood | Impact | Owner / Decision Role | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F4-PST-RISK-001 | AR-F4-001 | High | Prompt Contract Coverage / Testability | Report / Review / Weakness / Asset / Training 仍为 Stub，F5/F7 无法生成完整负例 fixture 和验收断言。 | Prompt contracts; F5; F7 | High | High | Architecture / Prompt Contract owner | Open |
| F4-PST-RISK-002 | AR-F4-002 | High | API Handoff / Orchestration | API_SPEC 缺失会导致 Prompt 状态被误当成接口合同，放大鉴权、owner、重试和错误处理分歧。 | API design; backend; frontend | High | High | Architecture / API owner | Open |
| F4-PST-RISK-003 | AR-F4-003 | Medium | Governance Consistency | `TECH_DESIGN.md` / `SECURITY_PRIVACY.md` 状态口径过期，可能导致重复创建 Prompt 入口或绕过现有 registry。 | Active docs governance | Medium | Medium | Documentation governor | Open |
| F4-PST-RISK-004 | AR-F4-004 | High | Product Non-goal / Scoring | Report 风险提示合同未定义，精确通过概率禁令缺少正式输出 schema 和负例验收落点。 | Report generation; scoring display | Medium | High | Product / Architecture | Open |
| F4-PST-RISK-005 | AR-F4-005 | High | LLM Privacy / Prompt Injection | Real Interview Review 合同缺失，真实复盘中的第三方信息、公司信息和注入指令缺少合同级处理规则。 | Review flow; privacy; RAG trust | Medium | High | Security / Prompt Contract owner | Open |
| F4-PST-RISK-006 | AR-F4-006 | High | Data Consistency / Silent Write | 候选资产、薄弱项、训练建议到正式事实的写入边界不足，可能出现静默写入或静默覆盖。 | Persistence; asset/weakness/training | Medium | High | Data / Product / Security | Open |
| F4-PST-RISK-007 | AR-F4-007 | Medium | RAG / Evidence | 业务合同缺少关键结论清单，通用 evidence binding 难以转化为字段级验收断言。 | Evidence binding; report/review outputs | Medium | Medium | Prompt Contract owner / QA | Open |
| F4-PST-RISK-008 | AR-F4-008 | Medium | Reliability / SRE | LLM / RAG timeout、rate limit、重试、幂等和重复提交策略未成合同，F7 故障验收不足。 | Backend orchestration; SRE; QA | Medium | Medium | Backend / SRE / API owner | Open |

## 3. Critical / High 风险

| Risk ID | Severity | Blocking Scope | Blocked Until |
| --- | --- | --- | --- |
| F4-PST-RISK-001 | High | F5/F7 full Prompt implementation and fixture generation | Core business contracts leave Stub state or explicitly defer implementation scope |
| F4-PST-RISK-002 | High | API/backend/frontend handoff | `API_SPEC.md` maps contract states to endpoint, schema, auth, retry, error and owner rules |
| F4-PST-RISK-004 | High | Report scoring and risk wording | `P-REPORT-003` defines allowed / forbidden wording and no exact pass probability fixtures |
| F4-PST-RISK-005 | High | Real interview review | Review contracts define privacy minimization, source trust and prompt injection handling |
| F4-PST-RISK-006 | High | Formal asset / weakness / training persistence | Formal write contracts define confirmation, trace, version, merge and overwrite boundaries |

## 4. 人工决策登记

| Decision ID | Related Risk | Absorbed Decision | Risk / Remediation Effect |
| --- | --- | --- | --- |
| D-F4-PST-001 | F4-PST-RISK-001 | AIFI-ARCH-003 不按“审查完成但设计阻断”收口；继续推进 remediation，直到 High findings 关闭。 | AIFI-ARCH-003 保持阻断；review artifacts 只能作为 remediation 输入，不作为最终验收通过证据。 |
| D-F4-PST-002 | F4-PST-RISK-002 | `API_SPEC.md` 是 F5 前置硬门槛；至少 AI 相关接口状态、错误语义、异步 / 同步模式必须在 F5 前冻结。 | F5 API/backend/frontend handoff 在 `API_SPEC.md` 补齐前不得进入完整实现承诺。 |
| D-F4-PST-003 | F4-PST-RISK-004 | 报告允许趋势性、等级性风险提示；禁止精确通过概率；展示必须绑定评分版本和 evidence。 | `P-REPORT-003` 需把 allowed wording、forbidden wording、score version 和 evidence binding 转为 schema 与 fixture。 |
| D-F4-PST-004 | F4-PST-RISK-005 | 真实面试复盘的第三方 / 公司信息默认脱敏；原文不进入 LLM；展示层只显示用户确认后的摘要。 | Review contracts 需定义 redaction、summary confirmation、source trust 和禁止 raw third-party / company text 入模。 |
| D-F4-PST-005 | F4-PST-RISK-006 | AI 输出不得自动创建正式资产、薄弱项或训练建议；只能生成 candidate / draft，并经用户确认后转正式事实。 | Weakness / Asset / Training contracts 需显式区分 candidate / draft / formal fact，并要求 `UserConfirmationRef`。 |
| D-F4-PST-006 | F4-PST-RISK-008 | F5 AI 任务采用混合编排：轻量任务同步，报告 / 训练 / 复盘类任务异步；必须定义 retry、idempotency 和 rate limit。 | `API_SPEC.md` 和 backend orchestration 需按任务类型冻结 sync / async、retry budget、idempotency key 和 rate limit。 |

## 5. Residual Risk

即使完成上述 remediation，仍需在 F5/F7 通过实现级验证确认：

- 实际 provider SDK 不记录 raw prompt、raw completion 或 provider payload。
- owner / scope / evidence / trace 字段在 API、service、persistence 和测试 fixture 中一致。
- 低置信度、证据不足、source unavailable、validation failed、generation failed 状态不会被 UI 静默吞掉。
- 用户复制边界与隐私文档一致，不扩展为文件导出、后台分享或跨用户可见能力。
