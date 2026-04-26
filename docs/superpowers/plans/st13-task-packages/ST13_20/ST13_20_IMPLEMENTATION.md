# ST13_20 IMPLEMENTATION：服务端保存 / 数据库

## 1. 文档状态

- 状态：`draft`
- 文档性质：`implementation plan only`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件只描述未来实现窗口如何执行；当前不放行数据库实现。
- W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.implementation_doc` slot，`exists=true`，`template_like=false`；该登记不改变 `implementation_doc_state=missing`、`readiness=blocked` 或 formal window 状态。

## 2. 关联 ST13 / WT13

- ST13：`ST13_20`
- WT13 alias：`WT13-20`
- 设计文档：`docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md`

## 3. 进入实现前置条件

- `ST13_20_DESIGN.md` 完成评审。
- `ST13_21` API contract 已稳定，至少明确核心 domain 与权限上下文。
- M02 权限 / user / role / tenant blocker 已消除，或已由用户另窗确认不阻断 `ST13_20` candidate / formal window。
- schema 文件、migration、ORM 和 PostgreSQL 连接 / 配置 / migration 策略已经用户确认。
- 数据回退策略、脱敏策略、删除 / 归档策略、审计字段和 schema version 已明确。
- `ST13_24` 已把 schema relation、权限过滤、数据一致性、RAG evidence、导出快照和审计日志纳入 required tests。
- formal window 用户确认已完成，且 preflight gate 通过。

## 4. formal window 前置条件

- 用户另窗确认可以打开 `ST13_20` formal window。
- `DOC_STATE.yaml` required doc slot 已由 W13-E8.5 State Update 窗口写入并通过 validate/evaluate；后续仍需单独状态窗口处理 formal window。
- M02 权限 blocker 已评估并闭合，至少不再由 `doc:api`、`doc:open_questions`、`module:M02` 阻断 `ST13_20`。
- schema 文件、migration、ORM、`apps/api/**`、`tests/**` 和 `DOC_STATE.yaml` 写入边界均已由用户明确确认。
- PostgreSQL 连接、配置、migration up/down、rollback、dry-run 和审计 retention 策略已形成可执行输入。
- `ST13_21` API contract 与本数据 contract 的字段映射已完成复核。
- formal window preflight gate 已通过。
- 本文档不得自行声明 formal window open。

## 5. implementation packet 前置条件

- formal window open 前置确认已完成。
- implementation doc 不再只是计划文档。
- allowed modify paths、forbidden paths、required tests、acceptance criteria 均已填实。
- `ST13_21` API contract、M02 权限边界、PostgreSQL schema / migration / rollback 策略均已作为 packet 输入。
- 当前窗口不生成 implementation packet。

## 6. 允许修改范围

未来实现窗口才可能允许：

- 数据库 schema / migration 文件。
- ORM / repository / persistence 相关代码。
- 与数据 contract 直接相关的测试。

当前 W13-E14-D 仍不允许创建数据库、schema 文件、migration、ORM、`apps/api/**` 或测试文件。

## 7. 禁止修改范围

- 当前不创建数据库。
- 当前不创建 schema 文件。
- 当前不创建 migration。
- 当前不创建 ORM。
- 当前不写 SQL。
- 当前不实现 repository。
- 不修改 `DOC_STATE.yaml`。
- 不创建 `apps/api/**`。
- 不创建 `apps/**`、`infra/**`、`tests/**`。
- 不生成 implementation packet。
- 不打开 formal window。

## 8. 预期实现步骤

1. 复核 `ST13_21` API contract。
2. 固定 PostgreSQL schema、实体关系、索引、约束、schema version 和审计字段。
3. 制定 migration up/down、数据回退、脱敏、删除 / 归档和审计策略。
4. 在 formal window 明确授权后，才可实现 persistence 层并补齐测试。
5. 与 `ST13_21` 对齐 API 字段，与 `ST13_24` 对齐数据 DoD。

以上步骤当前均不执行。

## 9. 验证命令

未来实现窗口至少需要：

```bash
python -m tools.test_runner.run_tests
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

若新增 migration 工具或数据库测试，必须补充对应窄范围命令。

## 10. 测试要求

- schema relation validation。
- migration up/down dry-run。
- 权限过滤数据可见性测试。
- 模拟记录、评分、复盘、导出链路数据一致性测试。
- RAG evidence 引用完整性测试。
- 脱敏、删除 / 归档、审计日志和导出快照一致性测试。
- 临时产物必须遵守 `docs/governance/TEST_POLICY.md`。

## 11. 回退策略

- 文档回退：回退本双文档和父索引引用。
- 数据回退：未来 migration 必须提供 up/down 或可恢复方案。
- 状态回退：必须另开 State Update 或治理窗口；本文档不得直接修改 `DOC_STATE.yaml`。

## 12. 日志 / 观测要求

未来实现应记录：

- 数据写入 request_id。
- migration 版本。
- 归档 / 删除操作审计。
- LLM / RAG evidence 保存链路。
- 导出快照生成状态。

## 13. 安全 / 隐私检查

- 用户数据隔离。
- 管理员公共知识库与用户私有知识库隔离。
- LLM prompt / response 脱敏保存。
- 导出快照权限检查。
- 删除 / 归档审计。

## 14. 交接输出格式

未来实现窗口收口时必须输出：

- 修改文件清单。
- schema / migration 摘要。
- 数据回退策略。
- 验证命令和结果。
- 未完成项和 blocker。

## 15. Basic Memory / Superpowers 写回要求

未来收口窗口如获授权，必须先检索、后写入、再回读验证。写回内容至少包含 confirmed 数据策略、风险、下一步和验证结果。

当前 W13-E14-D 不写 Basic Memory。

## 16. 当前未放行实现说明

`ST13_20_IMPLEMENTATION.md` 的存在和 contract_refined 状态都不等于 implementation-ready。当前不创建数据库，不创建 migration，不创建 ORM，不写 SQL，不生成 implementation packet，不打开 formal window。

## 17. W13-E13.5 candidate 表达策略同步

`ST13_20` 在 W13-E13.5 后继续只保留文档层 near-ready：不写正式状态层 `candidate_status`，不写 `readiness=downstream_ready`，不写 formal window candidate，不写 implementation-ready。

## 18. W13-E13.8 facts-only State Update 保持策略

W13-E13.8 只对 `ST13_24 / ST13_25` 执行 facts-only candidate 推荐字段写入；`ST13_20` 保持正式 `DOC_STATE.yaml` 原样，未写 candidate facts，未写 `candidate_status=candidate`，未写 `readiness=downstream_ready`，未写 near-ready 状态。

该保持策略不改变本文件的 implementation plan only 定位。`ST13_20` 仍不得创建数据库、migration、ORM、SQL，不得生成 implementation packet，不得打开 formal window。

该策略不新增实现任务，不改变本文件的 implementation plan only 定位。当前仍不创建数据库、migration、ORM、SQL、implementation packet 或业务代码。

## 19. W13-E14-D 未来实现窗口约束复核

本节只约束未来实现窗口，不授权当前窗口实现。

### 19.1 当前仍禁止

| 项 | 当前结论 |
| --- | --- |
| 创建数据库 | 禁止；当前只复核文档 contract |
| 创建 schema 文件 | 禁止；schema 文件路径、格式、命名和维护职责未授权 |
| 创建 migration | 禁止；migration 工具、up/down、dry-run 和 rollback 策略未授权 |
| 创建 ORM | 禁止；ORM model、repository、persistence layer 均未授权 |
| 创建 `apps/api/**` | 禁止；API / 后端实现必须等待 `ST13_21` formal window 或相关授权 |
| 创建 `tests/**` | 禁止；测试文件需等待 `ST13_24` 或后续 formal window 授权 |
| 生成 implementation packet | 禁止；当前 packet inputs 仍未闭合 |
| 打开 formal window | 禁止；formal window closed |
| 修改 `DOC_STATE.yaml` | 禁止；任何状态层写入必须另开 State Update 窗口 |
| 进入业务实现 | 禁止；当前仍是 implementation plan only |

### 19.2 未来实现必须等待的前置条件

未来实现窗口至少必须等待：

1. 用户另窗确认 `ST13_20` formal window open。
2. `doc-governor` preflight gate 通过，并且 `validate-state` / `evaluate-state` 继续全绿。
3. `implementation_doc_state`、allowed modify paths、forbidden paths、required tests、acceptance criteria 和 packet inputs 已由正式流程处理。
4. M02 权限 / user / role / tenant blocker 已闭合或被确认不阻断。
5. `ST13_21` API contract 稳定，且 request / response、权限上下文、错误态与数据保存字段完成对齐。
6. PostgreSQL schema、连接配置、migration 工具、up/down、dry-run、rollback 和数据修复策略已确认。
7. 数据脱敏、删除 / 归档、审计、保留周期、LLM / RAG 记录保存边界已确认。
8. `ST13_24` 已承接 schema relation、权限过滤、数据一致性、RAG evidence、导出快照和审计日志测试要求。

### 19.3 与 ST13_21 的同步要求

- `ST13_21` 未确认的 API 字段，不得在 `ST13_20` 中提前实现为数据库字段。
- API 的 `permission_denied`、`resource_not_visible`、`archived_resource`、RAG failed、LLM failed 等错误语义，必须能映射到数据状态或审计事件。
- `ST13_20` future schema 只能消费已稳定的 API domain、DTO、权限上下文和错误态；不能反向推动 `ST13_21` 自动创建 `apps/api/**`。
- 若 API contract 与数据 contract 出现字段漂移，应先回到文档评审或 Merge 窗口，而不是进入实现补丁。

### 19.4 formal window closed 保持说明

截至本节补充，`ST13_20` 仍保持：

- `not implementation-ready`
- `formal window closed`
- `implementation packet forbidden`
- 文档层 `near_ready_for_formal_window_candidate_confirmed`
- 正式状态层不写 `candidate_status=candidate`
- 正式状态层不写 `readiness=downstream_ready`
