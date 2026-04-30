# ST13_20 IMPLEMENTATION：服务端保存 / 数据库

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务实施说明；只定义后续执行条件，不是 implementation packet
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件只描述未来实现窗口如何执行；当前不放行数据库实现。
- W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.implementation_doc` slot，`exists=true`，`template_like=false`；该登记不改变 `implementation_doc_state=missing`、`readiness=blocked` 或 formal window 状态。

## 2. 关联 ST13 / WT13

- ST13：`ST13_20`
- WT13 alias：`WT13-20`
- 设计文档：`docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_DESIGN.md`

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

- formal window open 前置确认需在后续状态窗口完成。
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

## 20. R0-W13Z.16 gate 输入就绪修正

本节在第 1/5、2/5 次文档 readiness 输入基础上，补齐第 3/5 次 official state / formal window 打开后的 implementation packet 输入。第 3/5 次不进入业务代码；第 4/5 次必须先生成并复核 implementation packet，再按 packet 授权进入最小实现。

### 20.1 本轮实施目标

- 为 R0 可运行主链路实现最小服务端保存 / 数据库边界。
- 覆盖岗位、简历、模拟面试记录、回答、最小评分 / 反馈、最小复盘和 Markdown 导出的最小持久化与追溯边界。
- 第 3/5 次只完成 official gate 前置状态打开；第 4/5 次先生成 implementation packet，再在 packet 授权路径内实现。

### 20.2 实施范围边界

R0 最小持久化边界只覆盖一次真实模拟面试主链路的保存、回看和最小复盘追溯：

- 身份引用：记录归属、权限过滤和审计入口候选。
- 岗位与简历：岗位目标、简历正文或脱敏摘要、版本或快照引用。
- 面试记录：会话、问题、回答、状态、时间戳和完成结果。
- 评分 / 反馈 / 复盘：最小评分、反馈摘要、复盘摘要、失败状态和证据引用候选。
- 导出追溯：Markdown 复制 / 下载的来源对象、内容版本、脱敏状态和失败原因候选。
- 审计与生成记录：必要 request_id、脱敏 LLM 生成状态、失败原因和关键操作审计候选。

保存、恢复、历史、复盘和导出可追溯代表 R0 implementation packet 的候选能力边界。第 3/5 次不实现业务代码；第 4/5 次只允许在 packet 授权后实现最小持久化边界，不覆盖完整后端、完整数据库模型、R1 可信工作台增强、R2 训练闭环或资产沉淀。

### 20.3 允许修改

- `apps/api/**`
- `tests/**`
- `requirements.txt`
- `.env.example`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_DESIGN.md`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md`

### 20.4 禁止修改

- `docs/governance/DOC_STATE.yaml`
- `docs/governance/transition_history.jsonl`
- `docs/governance/previews/**`
- `docs/governance/packets/**`
- `apps/web/**`
- `tools/**`
- `infra/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_24/**`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_25/**`
- `docs/requirements/workbench-mvp/**`
- `docs/design/workbench-mvp/**`
- `M02/**`
- `package.json`
- `package-lock.json`
- 完整后端重构
- 完整 migration 体系
- 完整 ORM model 体系
- 完整业务 API 扩展
- LLM / RAG provider implementation

### 20.4.1 Packet 边界说明

上述 allowed / forbidden paths 只作为 formal window 已打开后的 implementation packet 输入。第 3/5 次执行仍不修改业务代码；第 4/5 次必须先生成并复核 implementation packet，且 packet 禁止范围优先级高于允许范围。

### 20.5 自动化验证

- `git diff --check`
- `python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-id ST13_20`
- `python3 -m tools.doc_governor.cli preflight-open-window --state docs/governance/DOC_STATE.yaml --subtask ST13_20`
- `python3 -m tools.doc_governor.cli generate-implementation-packet --input docs/governance/DOC_STATE.yaml --entity-id ST13_20`
- `python3 -m tools.test_runner.run_tests --pytest-args tests -q`
- `git status --short`

### 20.6 手动验证

- 检查 IMPLEMENTATION 中 goal、allowed paths、forbidden paths、required tests、acceptance criteria、scope boundary、stop conditions 均非空且不互相冲突。
- 检查 required tests 输入覆盖保存、恢复、历史查询、复盘读取、Markdown 导出可追溯、权限过滤、脱敏、失败状态和审计候选。
- 检查实现不扩大到完整 DB 重构、完整 migration 体系、完整 ORM 体系、完整业务 API、LLM / RAG provider、R1 或 R2。
- 检查 apps/api 目录的最小持久化边界不反向修改 ST13_21，tests 目录的测试只验证 ST13_20 R0 最小保存 / 恢复 / 历史 / 复盘 / 导出追溯口径。
- 检查 IMPLEMENTATION 与 DESIGN 第 25 节的 R0 最小数据保存边界、禁止范围和最新 official gate 状态保持一致。

### 20.7 测试与验证

- governance tests：validate-state、evaluate-state、git diff --check、git status 范围核对和 UTF-8 乱码扫描。
- contract tests 输入：R0 最小对象关系、权限过滤、状态字段、归档 / 软删除语义、审计字段、导出快照追溯和 LLM / RAG 脱敏记录边界。
- integration tests 输入：未来获授权后验证岗位、简历、面试记录、回答、评分、复盘和 Markdown 导出之间的数据一致性。
- failure tests 输入：无权限、资源不可见、记录归档、LLM 失败、RAG 无命中、评分未生成、复盘失败、导出失败时不得丢失已保存回答和历史记录。
- 第 3/5 当前动作：只打开 official gate 前置状态，不创建 tests，不启动 dev server，不执行数据库或业务集成测试。

### 20.8 完成判定

- implementation packet 已基于 official state 生成并复核，且 allowed / forbidden paths 与本节一致。
- 代码实现只触及 packet 授权路径，不修改禁止路径，不扩大到 R1 / R2。
- R0 最小保存、恢复、历史查询、复盘读取和 Markdown 导出追溯的持久化边界可被验证。
- git diff --check 通过。
- validate-state、evaluate-state、preflight-open-window 和 required tests 通过，或明确记录环境阻断原因。
- acceptance 不以完整数据库模型、完整 migration、完整 ORM、完整业务 API、LLM / RAG provider 或训练闭环作为完成标准。

### 20.9 停止条件

出现以下任一情况必须停止：

1. 需要手工绕过 `confirm-transition` 或 wrapper 修改 official state。
2. implementation packet 生成失败、packet allowed / forbidden paths 与本节冲突，或 packet 未授权目标文件。
3. 需要扩大到 `apps/web/**`、`tools/**`、`infra/**`、其他 ST13 目录、M02、R1 或 R2。
4. 需要实现完整 migration 体系、完整 ORM 体系、完整业务 API、LLM / RAG provider、RAG 检索或训练闭环。
5. `git status --short` 出现本轮允许范围外的新增 tracked diff 或未解释改动。
6. `validate-state`、`evaluate-state --entity-id ST13_20`、`preflight-open-window --subtask ST13_20` 或 required tests 无法执行，或出现新的 error / warning / hard blocker。

### 20.10 剩余正式 blocker

R0-W13Z.16-ST13_20 第 3/5 次已通过 official state / wrapper 流程解除以下 blocker：

- `gate:maturity_missing`
- `gate:implementation_approval_missing`
- `policy:formal_window_closed`
- `gate:implementation_doc_not_active`

当前 official state 已对齐为：

- `maturity=L5`
- `implementation_approval_status=approved`
- `implementation_doc_state=active_working_doc`
- `formal_window_status=open`
- `readiness=downstream_ready`
- `can_generate_implementation_packet=true`
- `can_mark_implementation_ready=true`
- `implementation_ready=true`

第 3/5 次不生成 implementation packet，不进入业务代码。第 4/5 次必须先生成并复核 implementation packet，再按 packet allowed / forbidden paths 进入最小实现。

## 21. R0-W13Z.16 第 4/5 次实现事实同步

第 4/5 次已基于 official state 生成并复核 `ST13_20` implementation packet，随后只在 packet 授权范围内完成 R0 最小后端持久化实现。

### 21.1 Packet 结果

- packet JSON：`docs/governance/packets/ST13_20.implementation.packet.json`
- packet Markdown：`docs/governance/packets/ST13_20.implementation.packet.md`
- `implementation_ready=true`
- allowed paths 覆盖 `apps/api/**`、`tests/**`、`.env.example`、`requirements.txt` 与 `ST13_20` 双文档同步路径。
- forbidden paths 明确排除 `apps/web/**`、`tools/**`、`infra/**`、其他 ST13 目录、requirements/design 正文、完整 migration、完整 ORM、完整业务 API、LLM / RAG provider 与 R1 / R2。

### 21.2 已实现最小边界

- 在 `apps/api/app/persistence.py` 新增最小 `sqlite3` 持久化 adapter，不引入 ORM，不创建 migration 框架。
- 将 R0 最小 DDL 拆入 `apps/api/app/schema/interview_records.sql`，Python 只通过显式 schema loader 初始化。
- 在 `apps/api/app/api/v1/interview_records.py` 新增 `/api/v1/interview-records` 最小路由，覆盖保存、按 id 恢复、历史列表、复盘读取和导出追溯读取。
- 在 `apps/api/app/main.py` 新增 `create_app()`，在 app state 中挂载最小持久化 store；schema 初始化发生在 runtime startup 或测试显式初始化边界，不在 import 时自动建表。
- 在 `apps/api/app/boundary.py` 新增 `API_DATABASE_PATH` 配置读取，默认落到系统临时目录，不写仓库根目录。
- 在 `.env.example` 增加 `API_DATABASE_PATH=` 占位。

### 21.3 已验证最小口径

- `tests/api/test_interview_records.py` 覆盖一次记录保存、恢复、历史查询、复盘读取、导出追溯 metadata 和 404 error envelope。
- 当前验证使用 `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_interview_records.py -q`。
- 系统 `python3` 环境缺少 `pytest`，因此应用测试使用仓库 `.venv` 运行；governance CLI 仍使用 `python3` 运行。

### 21.4 第 5/5 次剩余范围

- 复跑 governance 验证、packet 状态核对和 apps/api 最小测试。
- 视时间补充 owner_id 过滤、空 payload、metadata 字段和错误路径的测试。
- 做提交前 diff 范围核对，确认没有 forbidden paths 或无关格式化。
- 不关闭 formal window，不修改 official state，不 commit / push，除非用户另行明确授权。

## 22. R0-W13Z.16 第 5/5 次最终收口事实同步

第 5/5 次执行范围限定为最终测试补齐、规则一致性审计、ST13_20 实现规范复核和提交前收口；本次不修改 official state，不修改 packet，不 commit / push。

### 22.1 规则承载一致性

- `AGENTS.md` 保留规则承载边界和工程规范入口。
- 企业 Python 工程规范细则统一承载在 `TECHNICAL_STANDARDS.md`。
- 本轮不再把完整“工程卫生规则”重复写回 `AGENTS.md`。

### 22.2 最终补齐测试范围

`tests/api/test_interview_records.py` 已从单一 smoke test 扩展为 ST13_20 R0 最小持久化边界测试，覆盖：

- `owner_id` 历史列表过滤，不泄漏其他 owner 记录。
- 空 payload 默认值、`source` / `version` / `created_at` / `updated_at` traceability metadata。
- 按 id 恢复已存在记录，以及缺失 id 的 404 error envelope。
- 历史列表最小字段、无大 payload 返回、`created_at DESC` 语义。
- 复盘读取、导出追溯 metadata 读取，以及缺失记录的 404 error envelope。
- 非法创建请求的 422 minimal error envelope。

测试临时数据库改用 `ManagedTempArtifacts` 管理，不再使用 `tmp_path`，以对齐 `docs/governance/TEST_POLICY.md`。

### 22.3 最小实现修正

- `apps/api/app/boundary.py` 新增 request validation error handler，使 422 校验失败复用现有 `{error:{code,message}}` 最小 envelope。
- `apps/api/app/main.py` 将 `RequestValidationError` 绑定到上述 handler。
- 未引入 ORM、migration 框架、完整业务 API、LLM / RAG provider、前端或 R1 / R2 能力。

### 22.4 最终验证命令

第 5/5 次收口必须复跑：

- `git diff --check`
- `python3 -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `python3 -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-id ST13_20`
- `python3 -m tools.doc_governor.cli preflight-open-window --state docs/governance/DOC_STATE.yaml --subtask ST13_20`
- `rg -n "CREATE TABLE|CREATE INDEX|ALTER TABLE|DROP TABLE" apps/api -g "*.py"`
- `.venv/bin/python -m py_compile apps/api/app/api/v1/interview_records.py apps/api/app/boundary.py apps/api/app/main.py apps/api/app/persistence.py apps/api/app/interview_record_contract.py`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_interview_records.py -q`
- `git status --short`

若上述命令通过且 forbidden path audit 无新增问题，`ST13_20` 可进入提交前候选状态；实际 commit / push 仍需用户另行授权。

## 23. R1 data / schema / migration readiness 执行边界

本节记录 `R1-W03-ST13_20-DATA-SCHEMA-MIGRATION-READINESS` 对未来执行窗口的输入约束。它只把已冻结的 `ST13_21` R1 API contract 转换为 `ST13_20` data / schema / migration readiness，不代表 schema implementation，不生成 migration，不创建 ORM model，不修改 persistence 代码，不新增测试，不生成 packet，不打开 formal window。

### 23.1 本窗口新增的执行输入

后续 schema / migration / ORM 窗口可以从 `ST13_20_DESIGN.md` 第 26 节消费以下输入：

- R1 data domain boundary：身份权限、岗位简历、知识库 / RAG、面试记录、评分复盘、导出历史、审计追踪。
- `ST13_21` 到 `ST13_20` 的字段映射：actor context、resource identity、snapshot / version、operation intent、RAG query context、LLM / generation context、response status、evidence、score / review、export。
- resource identity / resource reference / source snapshot reference 的区分。
- actor、owner、visibility、permission snapshot、workspace / tenant 候选字段边界。
- job、resume、knowledge document、interview session、turn、answer、score、review、export、history 的数据关系。
- request_id、operation_id、audit event、source snapshot、schema version、content version、created_at、updated_at 等 traceability 字段族。
- pending、running、failed、completed、generated、archived、deleted candidate、degraded、retryable 等状态语义。
- RAG citation、evidence、source snapshot、evidence gap 的持久化候选边界。
- `0-100` 多维评分、可信复盘、Markdown export snapshot、history recovery / replay 的数据边界。
- 前端展示字段与后端 trace / debug / audit 字段的分工。

### 23.2 R1 必须落入后续 schema / migration 讨论的字段族

以下字段族不是本窗口已落库字段，但后续 schema / migration / ORM 实现窗口必须逐项处理：

- 核心资源 id / ref：job、resume、knowledge document、chunk、session、turn、answer、score、review、export。
- 权限字段：owner、created_by、updated_by、visibility、workspace / tenant 候选、permission snapshot。
- 关系字段：session -> job / resume / knowledge scope，turn -> answer / citation，score / review -> session / turn / evidence，export -> review / score / session snapshot。
- 状态字段：session、RAG indexing、score / review generation、export、archive / delete candidate 的状态语义。
- 追踪字段：request_id、operation_id、audit event ref、source snapshot ref、schema version、content version、created_at、updated_at。
- RAG 字段：retrieval query summary、topK、scope、result summary、citation / evidence refs、evidence gap、source snapshot。
- 评分复盘字段：score_total、dimensions、question feedback、recommendations、low confidence、evidence refs、review summary。
- 导出历史字段：export snapshot、format、content version、status、failure reason、history summary fields。

### 23.3 R1 候选字段与不落库字段

R1 候选字段只能进入后续评审，不得在本窗口被写成已实现 schema：

- workspace / tenant 命名与隔离粒度。
- provider alias、model alias、prompt version。
- retrieval mode、confidence label、token / cost summary。
- idempotency key、retry policy、retention policy。

R1 明确不落库或不得作为必落库字段：

- provider secret、真实 token、真实 password、数据库连接串。
- 完整 prompt 原文、完整 LLM response 原文。
- embedding 向量和向量库内部结构。
- 对象存储真实路径、真实 bucket / client / provider 初始化信息。
- 完整权限矩阵、enterprise organization / RBAC 配置。
- PDF 模板配置、训练任务调度参数、资产归档策略。

如后续确需保存上述任一内容，必须另开安全、隐私、存储和 retention 策略窗口。

### 23.4 前端消费与后端 trace 分工

未来实现不得把所有后端 trace 字段直接暴露给前端：

- 前端可展示：资源摘要、状态、评分、复盘、RAG citation、evidence gap、failure reason 安全摘要、retryable、empty state、permission / visibility 安全文案。
- 前端可有限展示：脱敏 `request_id`，用于用户反馈或排查。
- 后端默认保留：`operation_id`、audit event ref、source snapshot ref、provider / model alias、schema version、content version、failure source。
- 不得展示或保存为普通业务字段：provider secret、完整 prompt、完整 LLM response、embedding 向量、对象存储真实路径、不可见资源真实 id。

### 23.5 后续实现窗口进入条件

未来若要进入 schema / migration / ORM 实现，必须先满足：

1. 用户另窗确认 formal window 或实现窗口目标。
2. implementation packet 已生成并复核，且 allowed / forbidden paths 明确授权 schema、migration、ORM、tests 或 `apps/api/**` 的具体范围。
3. `ST13_20_DESIGN.md` 第 26 节中的 R1 must-persist 字段族已经转换为明确 schema 设计。
4. R1 candidate 字段已逐项确认落库、暂缓或不落库。
5. M02 权限 / workspace / tenant / resource visibility 语义已闭合或被明确接受为非阻断。
6. `ST13_24` 已承接 schema relation、权限过滤、RAG evidence、评分复盘、导出快照、历史恢复和失败状态 required tests。
7. validate-state、evaluate-state、preflight / packet 相关命令继续通过。

### 23.6 当前仍禁止

本 R1 readiness 窗口仍禁止：

- 修改 `apps/**`、`tests/**`、`docs/governance/**`、`DOC_STATE.yaml`、`ST13_21/**`、`ST13_10/**`。
- 创建 schema 文件、migration 文件、ORM model、repository、SQL 或数据库配置。
- 新增依赖、环境变量、provider、queue、worker、object storage 或 RAG / LLM implementation。
- 把 R1 readiness 字段表直接当作已冻结数据库 schema、OpenAPI 文件或 implementation-ready 状态。
- 生成 packet、打开 formal window、commit、push 或修改任何长期状态入口。

### 23.7 验证口径

本窗口完成判定只面向文档与治理：

- `ST13_20_DESIGN.md` 已明确 R1 data / schema / migration readiness 范围。
- `ST13_20_IMPLEMENTATION.md` 已明确后续 schema / migration / ORM 实现窗口的输入和停止条件。
- R1 必落库讨论字段、R1 候选字段、R1 不落库字段和 R2 延后范围已区分。
- RAG evidence、score、review、export、history、permission / visibility、frontend-visible vs backend-trace 字段分工已明确。
- 未修改代码、测试、governance state、packet、formal window、schema、migration 或 ORM。
