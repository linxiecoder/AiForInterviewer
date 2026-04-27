# ST13_21 IMPLEMENTATION：API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务实施说明；只定义后续执行条件，不是 implementation packet
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件只描述未来实现窗口如何执行；当前不放行代码。
- W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.implementation_doc` slot，`exists=true`，`template_like=false`；该登记不改变 `implementation_doc_state=missing`、`readiness=blocked` 或 formal window 状态。

## 2. 关联 ST13 / WT13

- ST13：`ST13_21`
- WT13 alias：`WT13-21`
- 设计文档：`docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`

## 3. 进入实现前置条件

- `ST13_21_DESIGN.md` 完成评审并形成稳定 API contract。
- Auth、Account / Role / Permission、Job、Resume、Knowledge、Interview、Score、Review、Export、Ops domain 已有非空验收标准。
- API error contract、权限错误 contract、LLM / RAG 失败 contract 已被 `ST13_24` 纳入 required tests。
- `ST13_20` 至少提供数据 contract 输入，避免 API 与 schema 互相漂移。
- required tests 已由 `ST13_24` 或后续测试窗口明确。

## 4. formal window 前置条件

- 用户另窗确认可以打开 `ST13_21` formal window。
- `DOC_STATE.yaml` required doc slot 已由 W13-E8.5 State Update 窗口写入并通过 validate/evaluate；后续仍需单独状态窗口处理 formal window。
- `formal_window_open` 相关状态不得由本文档自行声明。
- M02 权限 blocker 已被评估为可接受或已另窗消除。

## 5. implementation packet 前置条件

- formal window open 前置确认需在后续状态窗口完成。
- implementation doc 不再只是计划文档，且允许修改范围、禁止范围、required tests、acceptance criteria 均非空。
- `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml` 对该任务不再给出 implementation-ready blocker。
- 当前窗口不生成 implementation packet。

## 6. 允许修改范围

未来实现窗口才可能允许：

- `apps/api/**`，但必须由 formal window 明确授权。
- 共享 contract 或类型目录，若后续仓库结构确认存在。
- 与 API contract 直接相关的文档和测试。

当前 W13-E9 禁止创建上述目录。

## 7. 禁止修改范围

- 未经 formal window 授权不得创建 `apps/api/**`。
- 不得创建 OpenAPI 文件、schema 文件、路由文件、service、repository 或测试代码。
- 不得顺手实现 `ST13_20` 数据库、`ST13_23` 前端、`ST13_24` 测试代码。
- 不得修改 `docs/governance/DOC_STATE.yaml`。
- 不得生成 implementation packet。
- 不得写 provider key、真实用户简历、私有知识库内容到代码、日志或测试 fixture。

## 8. 预期实现步骤

1. 复核 `ST13_21_DESIGN.md` 与 `ST13_20` 数据 contract。
2. 固定 API domain、DTO、错误码、权限上下文、异步任务状态和 request / response 最小字段。
3. 在 formal window 明确授权后，才可生成或维护后端服务边界，优先 contract-first。
4. 补齐 API contract tests、权限 tests、错误态 tests、LLM / RAG 失败 tests。
5. 与 `ST13_20` 对齐数据保存字段，与 `ST13_24` 对齐验收矩阵，与 `ST13_25` 对齐收口写回要求。

以上步骤当前均不执行。

## 9. 验证命令

未来实现窗口至少需要：

```bash
python -m tools.test_runner.run_tests
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

若后续新增 API 测试，必须补充对应窄范围命令。

## 10. 测试要求

- contract schema validation。
- 权限矩阵测试。
- API error taxonomy 测试。
- 幂等和状态流转测试。
- LLM / RAG / scoring / export 异步任务状态测试。
- request / response 字段最小一致性测试。
- API 与数据 contract 字段漂移检查。
- 失败时停止，不得继续扩展实现。

## 11. 回退策略

- 文档回退：回退本双文档和父索引引用。
- 代码回退：仅限未来实现窗口中被授权的 `apps/api/**` 变更。
- 状态回退：必须另开 State Update 或治理窗口；本文档不得直接修改 `DOC_STATE.yaml`。

## 12. 日志 / 观测要求

未来实现应保留：

- `request_id`
- `task_id`
- `user_id` 或脱敏用户引用
- `provider`
- `latency_ms`
- `error_code`
- token / cost 候选字段

## 13. 安全 / 隐私检查

- session cookie 与权限过滤必须覆盖全部业务 API。
- LLM prompt / response 日志必须脱敏。
- RAG evidence 必须按用户可见范围过滤。
- Markdown export 不得导出无权限原文。

## 14. 交接输出格式

未来实现窗口收口时必须输出：

- 修改文件清单。
- API domain / endpoint 变更摘要。
- 验证命令和结果。
- 未完成项和 blocker。
- 是否仍可进入下一个 ST13。

## 15. Basic Memory / Superpowers 写回要求

未来收口窗口如获授权，必须先检索、后写入、再回读验证。写回内容至少包含 confirmed 结论、风险、下一步和验证结果。

当前 W13-E9 不写 Basic Memory。

## 16. 当前未放行实现说明

`ST13_21_IMPLEMENTATION.md` 的存在和 contract_refined 状态都不等于 implementation-ready。当前不创建 `apps/api/**`，不生成 OpenAPI 文件，不生成 schema 文件，不生成 implementation packet，不打开 formal window，不实现 API。

## 17. W13-E13.5 candidate 表达策略同步

`ST13_21` 在 W13-E13.5 后继续只保留文档层 near-ready：不写正式状态层 `candidate_status`，不写 `readiness=downstream_ready`，不写 formal window candidate，不写 implementation-ready。

## 18. W13-E13.8 facts-only State Update 保持策略

W13-E13.8 只对 `ST13_24 / ST13_25` 执行 facts-only candidate 推荐字段写入；`ST13_21` 保持正式 `DOC_STATE.yaml` 原样，未写 candidate facts，未写 `candidate_status=candidate`，未写 `readiness=downstream_ready`，未写 near-ready 状态。

该保持策略不改变本文件的 implementation plan only 定位。`ST13_21` 仍不得创建 `apps/api/**`、OpenAPI 或 schema，不得生成 implementation packet，不得打开 formal window。

该策略不新增实现任务，不改变本文件的 implementation plan only 定位。当前仍不创建 `apps/api/**`、OpenAPI、schema、implementation packet 或业务代码。

## 19. W13-E14-C 未来实现窗口约束复核

本节只同步 W13-E14-C 的 near-ready blocker 复核结论；不把本文件升级为 active implementation doc，不生成 implementation packet，不创建任何实现文件。

### 19.1 当前硬约束

- 当前不创建 `apps/api/**`。
- 当前不创建 OpenAPI 文件。
- 当前不创建 schema、DTO、shared contract 或类型文件。
- 当前不创建 `tests/**`。
- 当前不生成 implementation packet。
- 当前不打开 formal window。
- 当前不修改 `DOC_STATE.yaml`。
- 当前不把 `ST13_21` 标记为 implementation-ready。

### 19.2 未来实现前必须等待的确认

未来实现窗口至少需要用户明确确认：

1. 是否打开 `ST13_21` formal window。
2. 是否允许创建 `apps/api/**` 或其他后端服务目录。
3. 是否允许创建 OpenAPI 文件，并确认路径、版本策略和维护责任。
4. 是否允许创建 schema / DTO / shared contract 文件。
5. 是否允许生成 implementation packet。
6. 是否允许修改 `DOC_STATE.yaml` 中与 `ST13_21` 相关的 candidate、readiness、formal window 或 implementation doc 字段。
7. 是否扩大 ST13 范围，或只限 `ST13_21` API / 后端服务边界。

在上述确认前，任何实现步骤都只能作为未来计划，不得执行。

### 19.3 preflight gate 要求

未来实现窗口必须先通过状态层或等价 gate：

- `validate-state` 必须保持 `ok=true,error=0,warning=0`。
- `evaluate-state` 必须保持 `ok=true,error=0,warning=0`，且不得新增 documents blocker。
- `preflight-open-window` 或同等开窗检查必须确认 `formal_window_open`、candidate 表达、implementation doc activation、allowed paths、forbidden paths、required tests 和 acceptance criteria 均满足开窗要求。
- `generate-implementation-packet` 只能在 formal window 已打开、implementation doc 已激活、implementation packet inputs 已闭合后执行。

不得用本文档正文声明替代工具 gate。

### 19.4 与 ST13_20 数据 contract 的对齐要求

未来实现前必须复核 `ST13_20`：

- API request / response 字段必须能映射到 `ST13_20` 的保存、不保存、脱敏、归档或审计策略。
- `User / Account / Role / Permission / Session` 必须与 M02 权限边界和 `ST13_20` 数据保存策略一致。
- `SessionRecord`、`ScoreReport`、`ExportSnapshot`、`LLMGenerationRequest / Result` 的 API 状态必须与数据状态机一致。
- RAG / LLM / provider 失败语义必须能被数据状态、审计事件和 `ST13_24` required tests 覆盖。
- 若 `ST13_20` 仍保持 near-ready 或 schema / migration / ORM 未授权，`ST13_21` 不得单独进入实现。

### 19.5 当前执行结论

`ST13_21` 当前仍保持 `near_ready_for_formal_window_candidate_confirmed` 的文档层口径；正式状态层不写 candidate，不写 `readiness=downstream_ready`，不打开 formal window，不生成 implementation packet，不进入实现。
