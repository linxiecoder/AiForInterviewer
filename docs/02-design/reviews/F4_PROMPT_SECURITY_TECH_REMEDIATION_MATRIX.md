---
title: F4 Prompt / Security / Tech Remediation Matrix
type: review
status: active-f4
permalink: ai-for-interviewer/design/reviews/f4-prompt-security-tech-remediation-matrix
---

# F4 Prompt / 安全隐私 / 技术设计整改矩阵

## 1. 使用边界

本矩阵只描述建议整改，不在本轮直接修改原始设计文档。所有整改都必须在后续授权轮次内按治理入口进入对应 active docs，不能通过本 review 文件替代 `PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`TECH_DESIGN.md`、`API_SPEC.md` 或 Prompt 子合同。

## 2. Remediation Matrix

| Finding ID | Severity | Recommended Remediation | Target Active Doc(s) | Downstream Validation | Required Decision | Priority | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AR-F4-001 | High | 补齐 Report / Review / Weakness / Asset / Training 的完整 Prompt contract 模板字段；或显式声明这些能力不进入当前 F5/F7 范围。High findings 关闭前，AIFI-ARCH-003 不收口。 | `PROMPT_SPEC.md`; `prompt-contracts/REPORT_CONTRACTS.md`; `prompt-contracts/REVIEW_CONTRACTS.md`; `prompt-contracts/WEAKNESS_CONTRACTS.md`; `prompt-contracts/ASSET_CONTRACTS.md`; `prompt-contracts/TRAINING_CONTRACTS.md`; `BACKLOG.md` | F7 fixture 能覆盖各合同 output schema、low confidence、evidence、trace、validation failure、prompt injection 和 user confirmation。 | 已决：不按“审查完成但设计阻断”收口；继续 remediation 直到 High findings 关闭。 | P0 | Not started |
| AR-F4-002 | High | 创建或补齐 `API_SPEC.md`，将 Prompt contract state 映射到 endpoint、request / response、error、auth、owner、retry、idempotency 和 frontend-visible state，并冻结 AI 相关接口状态、错误语义、异步 / 同步模式。 | `API_SPEC.md`; `TECH_DESIGN.md`; `PROMPT_SPEC.md`; `BACKLOG.md` | API contract test 覆盖 auth / owner / failure / retry / no raw model exposure。 | 已决：`API_SPEC.md` 是 F5 前置硬门槛。 | P0 | Not started |
| AR-F4-003 | Medium | 更新 active docs 中关于 `PROMPT_SPEC.md` 状态的过期描述，统一为“Prompt spec 已存在，部分子合同为 Stub；API_SPEC 未创建”。 | `TECH_DESIGN.md`; `SECURITY_PRIVACY.md`; `DOCS_INDEX.md` if needed | 文档 grep 不再出现误导性“PROMPT_SPEC 未创建”当前口径。 | 是否列为 AIFI-ARCH-002 前置修补。 | P1 | Not started |
| AR-F4-004 | High | 补齐 `P-REPORT-003`，定义风险提示 / 通过倾向的允许表达、禁用表达、评分版本、低置信度、证据要求和 exact probability 负例；允许趋势性、等级性提示，但禁止精确通过概率。 | `REPORT_CONTRACTS.md`; `PROMPT_SPEC.md`; `PRD.md` if product decision changes | F7 验证不输出精确通过概率，不泄露隐藏评分规则，所有风险提示绑定评分版本和 evidence，评分规则 UNKNOWN 时低置信度。 | 已决：展示只能是趋势性 / 等级性风险提示，且必须绑定评分版本和 evidence。 | P0 | Not started |
| AR-F4-005 | High | 补齐 Review contracts，定义真实复盘最小输入、第三方 / 公司信息默认脱敏、source trust、completeness、prompt injection 隔离、低置信度和禁止预测；原文不得进入 LLM。 | `REVIEW_CONTRACTS.md`; `SECURITY_PRIVACY.md`; `PROMPT_SPEC.md` | Review fixture 覆盖第三方 PII、公司机密、注入指令、可信度低、证据不足、禁止预测、raw text 不入模和用户确认摘要。 | 已决：第三方 / 公司信息默认脱敏，展示层只显示用户确认后的摘要。 | P0 | Not started |
| AR-F4-006 | High | 补齐 Weakness / Asset / Training 正式写入合同，定义 candidate / draft 到 formal fact 的用户确认、合并、去重、版本、trace、owner 和覆盖禁令。 | `WEAKNESS_CONTRACTS.md`; `ASSET_CONTRACTS.md`; `TRAINING_CONTRACTS.md`; `DATA_MODEL.md`; `SECURITY_PRIVACY.md` | F7 验证 AI 输出不会静默写入或覆盖正式事实，所有正式写入有 `UserConfirmationRef` / `TraceRef` / `VersionRef`。 | 已决：AI 只能生成 candidate / draft，不得自动创建正式事实。 | P0 | Not started |
| AR-F4-007 | Medium | 为每个业务 contract 定义 key claim list 和 evidence requirement matrix，明确哪些字段必须绑定 owner/source/version/snapshot/trace。 | `PROMPT_SPEC.md`; `SHARED_CONTRACTS.md`; all business contract docs | Evidence fixture 覆盖 missing owner/source/version/snapshot/trace、conflict、source unavailable、evidence insufficient。 | 哪些用户可见字段必须 evidence-backed。 | P1 | Not started |
| AR-F4-008 | Medium | 定义 LLM / RAG runtime failure policy 和混合编排规则：轻量任务同步，报告 / 训练 / 复盘类任务异步，并覆盖 retry budget、idempotency key、rate limit、timeout、degrade、duplicate submission 和 recovery state。 | `API_SPEC.md`; `TECH_DESIGN.md`; `PROMPT_SPEC.md`; backend implementation plan | F7 覆盖 timeout、rate limit、RAG unavailable、validation failed、重复提交、取消 / 重试路径，并区分同步 / 异步任务状态。 | 已决：F5 AI 任务采用混合编排；必须定义 retry、idempotency 和 rate limit。 | P1 | Not started |

## 3. 建议整改顺序

1. P0: AIFI-ARCH-003 不收口；先推进 remediation，直到 High findings 关闭。
2. P0: 补 `API_SPEC.md`，冻结 AI 相关接口状态、错误语义、异步 / 同步模式、retry、idempotency 和 rate limit。
3. P0: 补 Report 合同，确保通过倾向 / 风险提示只使用趋势性或等级性表达，并绑定评分版本和 evidence。
4. P0: 补 Review 合同，确保第三方 / 公司信息默认脱敏、原文不入 LLM、展示层只显示用户确认摘要。
5. P0: 补 Weakness / Asset / Training 合同，确保 AI 只产出 candidate / draft，用户确认后才转正式事实。
6. P1: 统一 active docs 状态口径，清理 `PROMPT_SPEC.md` 创建状态的旧描述。
7. P1: 补 evidence key claim matrix 与 runtime failure policy。

## 4. 不建议整改方式

- 不建议在 review 文件中补写正式 Prompt contract 字段。
- 不建议让 F5 实现自行定义缺失 schema、状态或错误码。
- 不建议用 `archive/` 中历史文档替代 active docs 决策。
- 不建议在评分规则、通过倾向和正式写入策略未决时承诺 F7 完整通过。
