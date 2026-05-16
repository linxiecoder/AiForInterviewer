---
title: F4 Full Design Risk Register
type: review
status: active-f4
source_task: AIFI-ARCH-004
permalink: ai-for-interviewer/design/reviews/f4-full-design-risk-register
---

# F4 全量技术设计风险登记表

## 1. 登记结论

本风险登记表只记录 `AIFI-ARCH-004` 全量 F4 设计对抗性审计发现，不修复 active design docs。本轮登记 7 项风险：0 Critical、4 High、2 Medium、1 Low。

Status 只使用 `Open`、`Deferred`、`Rejected_False_Positive`。本轮不标记 `Fixed` 或 `Verified`。

## 2. Risk Register

| ID | Severity | Category | Source | Affected Downstream | Risk | Required Fix | Required Decision | Status | Owner | Close Condition |
|---|---|---|---|---|---|---|---|---|---|---|
| AR-F4-FULL-001 | High | Scope / Governance / Testability | `DELIVERY_PLAN.md` F4 exit; `BACKLOG.md` `AIFI-ARCH-002`; `TECH_DESIGN.md` §16 / §18; `DATA_MODEL.md` §12; `PROMPT_SPEC.md` §13; `API_SPEC.md` §12 | F5 Backend; F6 Frontend; F7 QA | `F4_TECH_DESIGN` UNKNOWN 仍显式保留，M4 退出标准未满足 | 回写 TECH / DATA / API / PROMPT / SECURITY，逐项关闭、Deferred 或 Accepted Risk | 哪些 UNKNOWN 必须 F4 关闭，哪些允许后置 | Open | Architecture owner | 所有 F4 UNKNOWN 有处置状态，F7 可验证关闭状态 |
| AR-F4-FULL-002 | High | API / Reliability / Testability | `API_SPEC.md` §1 / §2 / §10 / §11 / §12 | F5 Backend; F6 Frontend; F7 QA | API 契约仍为骨架，endpoint/schema/error/auth/retry/idempotency/rate limit 未冻结 | 补齐完整 API contract 和失败状态协议 | 同步 / 异步分界、idempotency key、rate limit 维度 | Open | API / Backend owner | F7 可直接从 API_SPEC 生成 contract tests |
| AR-F4-FULL-003 | High | Scoring / Prompt / Testability | `PRD.md` §5.7 / §10; `DATA_MODEL.md` §10 / §12; Prompt scoring contracts | F5 Backend; F6 Frontend; F7 QA | 评分公式、权重、阈值、校准、通过倾向和免责声明仍未冻结 | 冻结最小评分规则版本、risk wording、免责声明和测试 fixture | 采用固定公式还是 rubric / rule version 替代口径 | Open | Product / Architecture / Prompt owner | F7 可验证评分、低置信、风险提示和禁止精确概率 |
| AR-F4-FULL-004 | High | Scope / Prompt / Security / Privacy | `PRD.md` §5.7 / §9; `TECH_DESIGN.md` §4 / §12; `SECURITY_PRIVACY.md` §14 / §22; `REPORT_CONTRACTS.md` §3.0 / §3.4 | F5 Backend; F6 Frontend; F7 QA | Report contract 重新引入 Markdown 下载 / 导出语义，违背 MVP non-goal | 从 Report contract 删除 download/export/filename/snapshot 语义，收敛为页面复制 | `P-REPORT-004` 是否只允许复制，不允许任何下载 / export | Open | Prompt / Security / Product owner | active docs 只保留复制能力；导出命中仅存在于 non-goal / deferred / finding |
| AR-F4-FULL-005 | Medium | State / Reliability / Testability | `DATA_MODEL.md` §12; `API_SPEC.md` §10 / §12; `SHARED_CONTRACTS.md` §10.6 | F5 Backend; F6 Frontend; F7 QA | 进展树、暂停恢复、异步失败和重试缺少可执行状态机 | 冻结暂停恢复快照、进展树状态机、status query/retry/cancel/timeout | 打磨 / 压力面暂停恢复范围和失败路径 | Open | Data / API / SRE owner | F7 覆盖 pause/resume/resume failed/partial/timeout |
| AR-F4-FULL-006 | Medium | Governance / Frontend Handoff | `DELIVERY_PLAN.md` §3; `UI_DESIGN_SYSTEM.md` §22 / §25 | F6 Frontend; F7 QA | F3 标为 DONE，但 UI_DESIGN_SYSTEM 仍登记高保真 UNKNOWN / NOT_STARTED | 统一 DELIVERY 与 UI_DESIGN_SYSTEM 状态口径 | F3 DONE 是否包含高保真页面完成 | Open | Delivery / UI owner | F6 可区分 approved / candidate / UNKNOWN design input |
| AR-F4-FULL-007 | Low | Governance / Prompt | `PROMPT_SPEC.md` §10 / §14; `REPORT_CONTRACTS.md` §3.5; `REVIEW_CONTRACTS.md` §4.5; `WEAKNESS_CONTRACTS.md` §4.5; `ASSET_CONTRACTS.md` §3.5 | PROMPT_SPEC; F7 QA | 子文档保留过期 Stub 状态说明，和当前 Draft registry 不一致 | 更新关系说明，统一为当前 Draft 事实和 UNKNOWN 保留边界 | 是否统一改为“已 Draft，但不关闭 UNKNOWN / 不自动写正式对象” | Open | Prompt / Governance owner | 过期 Stub 说明不再命中，真实 Stub 或历史记录除外 |

## 3. Critical / High Blocking Scope

| ID | Blocks F4 Exit | Blocks F5 | Blocks F7 | Reason |
|---|---|---|---|---|
| AR-F4-FULL-001 | Yes | Yes | Yes | F4 UNKNOWN 未关闭，M4 退出标准不满足 |
| AR-F4-FULL-002 | Yes | Yes | Yes | API handoff 不可实现、不可测试 |
| AR-F4-FULL-003 | Yes | Yes | Yes | 评分和风险提示无法形成稳定实现 / 验收 |
| AR-F4-FULL-004 | Yes | Yes | Yes | 违反 MVP no export 边界，可能诱导实现越界 |

## 4. Residual Risk

即使完成本轮整改，仍需在 F5 / F7 验证：

- 实际 API / service / persistence 是否强制 owner 过滤。
- LLM / RAG failure 是否不保存 raw prompt、completion 或 provider payload。
- `source_unavailable`、`validation_failed`、`low_confidence` 是否不被 UI 静默吞掉。
- Report copy 是否严格停留在页面复制，不扩展为下载 / export。
- F3 / F6 交接状态是否有人工确认或 active docs 关闭证据。
