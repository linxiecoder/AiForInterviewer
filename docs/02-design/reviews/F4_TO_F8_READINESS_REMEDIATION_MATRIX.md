---
title: F4_TO_F8_READINESS_REMEDIATION_MATRIX
type: remediation-matrix
status: active-f4
source_task: AIFI-ARCH-005
permalink: ai-for-interviewer/design/reviews/f4-to-f8-readiness-remediation-matrix
---

# F4→F8 交接就绪性整改矩阵

Status: Pending

本矩阵登记整改要求和已授权 remediation 进度。`Fixed` 仅表示 active docs 已完成本轮修复写入，仍需 focused verification；不得等同于 `Verified` 或 final acceptance。

| Finding | Target Active Doc | Required Change | Actual Change | Blocks F5 | Blocks F6 | Blocks F7 | Blocks F8 | Verification Method | Status |
|---|---|---|---|---|---|---|---|---|---|
| AR-F4-F8-001 | `docs/02-design/API_SPEC.md`, `docs/02-design/DATA_MODEL.md` | API 清单、逐接口出入参 schema、error schema、F7 tests、idempotency/task/trace/persistence 承接 | `API_SPEC.md` 新增 API 清单总表、49 个核心 API 逐接口详情、path/query/header/body/success/error/F7 assertion 和 Schema Index；`DATA_MODEL.md` 新增 `IdempotencyRecord`、`AiTask` / `AiTaskResult`、`ApiRequestTrace` / `TraceRef`、`AuditEvent` 覆盖范围和 persistence handoff。 | No | No | No | No | focused verification completed：49 个逐接口详情、字段级 schema、response data 展开、error schema、F7 assertions、idempotency / task / trace / persistence 承接均已核验通过 | Verified |
| AR-F4-F8-002 | `docs/02-design/API_SPEC.md` | 增加 F6 Page/API Handoff Matrix，覆盖页面、endpoint、request、response、view model、状态、错误、权限失败、stale version、candidate confirmation、copy boundary | N/A，本轮未处理 | No | Yes | Yes | Partial | 每个 `AIFI-FE-001` 核心页面都有 endpoint 和字段映射；可生成 mock adapter 和 E2E fixture | Open |
| AR-F4-F8-002 | `docs/02-design/TECH_DESIGN.md` | 增加 F4→F6 handoff 规则，明确 F6 不得从 UX/UI 反向发明 API 字段、状态或错误码 | N/A，本轮未处理 | No | Yes | Yes | Partial | `rg -n "F6|Page/API|handoff|view model" docs/02-design/TECH_DESIGN.md docs/02-design/API_SPEC.md`；人工审计 F6 handoff 是否单一可追踪 | Open |
| AR-F4-F8-002 | `docs/02-design/DATA_MODEL.md` | 若页面展示依赖 candidate、confirmation、version、trace、evidence 字段，补对应引用和状态边界 | N/A，本轮未处理 | No | Yes | Yes | Partial | 抽样资产、薄弱项、训练建议、报告复制和低置信度页面，确认 view model 字段可追踪 | Open |
| AR-F4-F8-003 | `docs/02-design/TECH_DESIGN.md` | 增加 F8 release handoff 小节，列出 release checklist 输入、known limitations、runbook、rollback、observability、Deferred 承接规则 | N/A，本轮未处理 | No | No | Partial | Yes | `rg -n "release|发布|runbook|运行手册|rollback|回滚|known limitations|Deferred|Backlog" docs/02-design/TECH_DESIGN.md` | Open |
| AR-F4-F8-003 | `docs/02-design/SECURITY_PRIVACY.md` | 补充发布前 privacy / logging / retention / deletion / provider / secret / rate limit 检查表 | N/A，本轮未处理 | No | No | Partial | Yes | 检查 provider failure、rate limit、audit/log、retention/deletion、secret 管理均有发布前检查项 | Open |
| AR-F4-F8-003 | `docs/02-design/API_SPEC.md` | 补充 route inventory、no export、copy boundary、rate limit、provider failure、trace/audit 的 F8 检查映射 | N/A，本轮未处理 | No | No | Partial | Yes | 验证 F8 能从 API_SPEC 抽取 route inventory、禁止导出断言、copy boundary 和 provider failure 检查 | Open |
| AR-F4-F8-003 | `docs/02-design/DATA_MODEL.md` | 补充 data migration / rollback / backup restore 的逻辑风险和 F5/F8 handoff | N/A，本轮未处理 | Partial | No | Partial | Yes | 检查迁移 / 回滚风险不只停留在对象版本语义；能输入 F8 rollback strategy | Open |
| AR-F4-F8-003 | `docs/03-delivery/BACKLOG.md` | 将后续承接的 Deferred 项登记为 AIFI-* 任务，或明确 Accepted_Risk / 不阻断理由 | N/A，本轮未处理 | No | No | No | Yes | 每个 Deferred release/privacy/provider/ops 项都能追踪到 Backlog、Accepted_Risk 或 Rejected_False_Positive | Open |
