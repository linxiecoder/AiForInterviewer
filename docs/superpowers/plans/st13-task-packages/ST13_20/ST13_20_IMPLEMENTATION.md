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
- schema / migration 方案已经用户确认。
- 数据回退策略、脱敏策略、删除 / 归档策略、审计字段和 schema version 已明确。
- `ST13_24` 已把 schema relation、权限过滤、数据一致性、RAG evidence、导出快照和审计日志纳入 required tests。

## 4. formal window 前置条件

- 用户另窗确认可以打开 `ST13_20` formal window。
- `DOC_STATE.yaml` required doc slot 已由 W13-E8.5 State Update 窗口写入并通过 validate/evaluate；后续仍需单独状态窗口处理 formal window。
- M02 权限 blocker 已评估。
- 本文档不得自行声明 formal window open。

## 5. implementation packet 前置条件

- formal window 已打开。
- implementation doc 不再只是计划文档。
- allowed modify paths、forbidden paths、required tests、acceptance criteria 均已填实。
- 当前窗口不生成 implementation packet。

## 6. 允许修改范围

未来实现窗口才可能允许：

- 数据库 schema / migration 文件。
- ORM / repository / persistence 相关代码。
- 与数据 contract 直接相关的测试。

当前 W13-E9 不允许创建数据库、migration 或 ORM。

## 7. 禁止修改范围

- 当前不创建数据库。
- 当前不创建 migration。
- 当前不创建 ORM。
- 当前不写 SQL。
- 当前不实现 repository。
- 不修改 `DOC_STATE.yaml`。
- 不创建 `apps/**`、`infra/**`、`tests/**`。

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

当前 W13-E9 不写 Basic Memory。

## 16. 当前未放行实现说明

`ST13_20_IMPLEMENTATION.md` 的存在和 contract_refined 状态都不等于 implementation-ready。当前不创建数据库，不创建 migration，不创建 ORM，不写 SQL，不生成 implementation packet，不打开 formal window。
