---
title: F4_TO_F8_READINESS_RISK_REGISTER
type: risk-register
status: active-f4
source_task: AIFI-ARCH-005
permalink: ai-for-interviewer/design/reviews/f4-to-f8-readiness-risk-register
---

# F4→F8 交接就绪性风险登记表

Status: Pending

本文件登记 `AIFI-ARCH-005` 的 F4→F8 严格审计风险。本轮只允许状态：`Open`、`Deferred`、`Accepted_Risk`、`Rejected_False_Positive`。本轮只审计不修复，因此所有有效 finding 均保持 `Open`。

| ID | Severity | Category | Affected Phase | Source | Risk | Required Fix | Status | Owner | Close Condition |
|---|---|---|---|---|---|---|---|---|---|
| AR-F4-F8-001 | High | API / Data / F5 Backend / F6 Frontend / F7 QA | F5 / F6 / F7 | `API_SPEC.md` §6.1-§6.2；`DATA_MODEL.md` §4.1、§12-§13 | `API_SPEC.md` 只有 endpoint matrix 和对象名级响应，缺逐接口字段级 contract；`DATA_MODEL.md` 缺幂等持久化承接 | 在 `API_SPEC.md` 增加 API 清单、逐接口详情、字段级 schema、headers、error responses、examples；在 `DATA_MODEL.md` 增加 `IdempotencyRecord` 或等价对象 | Open | F4 Architecture / API / Data owners | 所有核心 endpoint 可生成后端 / 前端类型和 F7 contract tests；幂等重试、stale version、owner boundary、AI task schema 可验证 |
| AR-F4-F8-002 | High | F6 Frontend / API / Governance | F6 / F7 / F8 | `API_SPEC.md` §4、§6.2、§7；`UX_SPEC.md` §5.17；`UI_DESIGN_SYSTEM.md` §18-§19 | 缺页面到 API / response / view model / 状态 / 错误态 / confirmation / copy boundary 的 F6 接入矩阵 | 在 `API_SPEC.md` / `TECH_DESIGN.md` 增加 F6 Page/API Handoff Matrix，并为候选确认、错误态、空态、低置信度、source unavailable、stale version、copy boundary 定义页面规则 | Open | F4 Architecture / API / Frontend owners | 每个 F6 页面能追踪 endpoint、字段、状态和错误展示；F7 能生成页面 E2E 和 API mock fixtures |
| AR-F4-F8-003 | High | F8 Release / Security / Governance | F8 | `DELIVERY_PLAN.md` §1；`BACKLOG.md` §1；`SECURITY_PRIVACY.md` §12、§22；`API_SPEC.md` §11；`DATA_MODEL.md` §12 | F4 缺 release checklist 来源矩阵、runbook、known limitations、rollback / migration、observability、provider failure 和 Deferred→Backlog 映射 | 在 `TECH_DESIGN.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`DATA_MODEL.md` 和必要的 `BACKLOG.md` 中补 F8 release handoff、发布前检查、运维隐私、回滚迁移和 Deferred 承接 | Open | F4 Architecture / Security / Release owners | F8 可从 active docs 直接生成 release checklist、known issues、runbook、rollback strategy、changelog 输入和下一轮 Backlog |
