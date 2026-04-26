# AI 模拟面试一期工作台 MVP ST13 第一批 contract 双文档准备方案

## 1. 背景

本文档是 `W13-E7 / 第一批 contract 正式子任务双文档准备窗口` 的输出。

本窗口承接 `W13-E6` 已生成的第一批 contract / 测试 / 治理任务包草案，只为 `ST13_21 -> ST13_20 -> ST13_24 -> ST13_25` 设计正式双文档路径、模板结构、父索引挂载方案、任务包前置条件、验收标准、测试要求、允许 / 禁止修改范围和后续开窗规则。

本窗口不写代码，不进入实现，不创建 `apps/**`、`infra/**`，不修改 `tools/**`、`tests/**`，不修改 `docs/governance/DOC_STATE.yaml`，不生成 implementation packet，不打开 formal window，不标记 implementation-ready。

W13-E8 更新：用户已确认 `OQ-111=A`、`OQ-112=A`、`OQ-113=B`。第一批正式双文档已按集中任务包目录创建。

W13-E8.5 更新：已按 `OQ-113=B` 在单独 State Update 窗口中把第一批正式双文档登记到 `DOC_STATE.yaml` required doc slot；仍不实现，不生成 implementation packet，不打开 formal window。

## 2. 第一批 ST13 范围

本窗口只处理以下四个 ST13，顺序固定为：

1. `ST13_21 / WT13-21`：API / 后端服务边界。
2. `ST13_20 / WT13-20`：服务端保存 / 数据库。
3. `ST13_24 / WT13-24`：测试 / 验收 / DoD。
4. `ST13_25 / WT13-25`：文档治理 / 收口 / Basic Memory。

不得扩大到其他 `ST13_*`，不得批量创建全部 25 个 ST13 的双文档，不能把第一批四个任务标记为 implementation-ready。

## 3. 当前限制

- W13 confirmed 边界不回退：一期 MVP 是工作台级，包含真实 LLM、登录 / 权限、服务端保存、历史 / 复盘、`0-100` 多维评分、RAG / 知识库、多轮高阶面试和 Markdown 下载 / 复制。
- `apps/web/**` 仅作为 W10 原型探索参考证据，不作为正式一期 MVP 代码起点。
- `DOC_STATE.yaml` 当前正式状态层入口为 `ST13_01~ST13_25`，但 25 个 ST13 仍 blocked。
- 第一批四个任务在 W13-E7 达到 `double_doc_path_planned`；W13-E8 已推进到 `double_doc_created`；W13-E8.5 已推进到 `double_doc_registered`，仍为 `not_ready_for_implementation`。
- 四个目标任务仍缺验收标准、required tests、允许修改范围、formal window 用户确认和 implementation packet 前置。
- W13-E7 当时推荐路径方案为方案 C；W13-E8 用户已确认方案 A：集中任务包目录，并已创建具体双文档。

## 4. 第一批四个 ST13 当前草案审计

| 审计项 | `ST13_21` | `ST13_20` | `ST13_24` | `ST13_25` |
| --- | --- | --- | --- | --- |
| ST13 ID | `ST13_21` | `ST13_20` | `ST13_24` | `ST13_25` |
| WT13 alias | `WT13-21` | `WT13-20` | `WT13-24` | `WT13-25` |
| 任务名称 | API / 后端服务边界 | 服务端保存 / 数据库 | 测试 / 验收 / DoD | 文档治理 / 收口 / Basic Memory |
| 所属模块 | 主模块 M01；关联 M01-M10，M02 仍需重点同步 | 主模块 M01；关联 M01-M10 | 主模块 M01；关联 M10 与全模块 | global、M01、M10 |
| 当前草案来源 | `2026-04-25-workbench-mvp-st13-first-contract-task-packages.md` 第 5 节 | 同文档第 6 节 | 同文档第 7 节 | 同文档第 8 节 |
| 当前草案状态 | `task_packet_draft_created` | `task_packet_draft_created` | `task_packet_draft_created` | `task_packet_draft_created` |
| 缺正式双文档 | 缺 `SUBTASK_DESIGN.md` 与 `SUBTASK_IMPLEMENTATION.md` | 缺 `SUBTASK_DESIGN.md` 与 `SUBTASK_IMPLEMENTATION.md` | 缺 `SUBTASK_DESIGN.md` 与 `SUBTASK_IMPLEMENTATION.md` | 缺 `SUBTASK_DESIGN.md` 与 `SUBTASK_IMPLEMENTATION.md` |
| 缺 contract | 需细化 API domain、DTO、权限、错误、幂等、异步任务、版本策略 | 需细化 schema、实体关系、migration、repository、保留 / 删除策略 | 需细化 required tests、DoD 分层、失败停止条件、验证命令 | 需细化状态写回、formal window、packet、Basic Memory / Superpowers 回写规则 |
| 缺验收标准 | 需逐 domain 定义最小验收 | 需逐实体定义持久化与一致性验收 | 需定义每个 ST13 的验收矩阵 | 需定义治理收口与索引同步验收 |
| 缺测试要求 | 需 API contract、权限、错误、异步状态测试 | 需 schema、migration、数据可见性和一致性测试 | 需测试矩阵自身校验和临时产物治理测试要求 | 需 validate/evaluate、关键词扫描、回读验证要求 |
| 缺允许修改范围 | 需区分文档准备、contract 细化、未来实现范围 | 同左，并明确不得建库或写 migration | 同左，并明确不得新增测试代码 | 同左，并明确不得写 `DOC_STATE.yaml` 或 Basic Memory |
| 缺禁止修改范围 | 需列出 `apps/**`、`infra/**`、`tools/**`、`tests/**`、`docs/governance/**` 等 | 同左 | 同左 | 同左，并额外禁止 Git 写操作和状态层写回 |
| 缺 formal window 条件 | 需双文档、验收、required tests、用户确认、required doc slot | 需 `ST13_21` contract 稳定后再评估 | 需 API / 数据 contract 稳定后再评估 | 需前三个任务包状态和治理卡确认后再评估 |
| 是否依赖其他 ST13 | 作为第一前置，依赖 W13 四份事实源和 W13-E6 草案 | 依赖 `ST13_21` API domain 边界 | 依赖 `ST13_21` 与 `ST13_20` | 依赖 `ST13_21 / ST13_20 / ST13_24` 的治理输入 |
| 是否可并行准备 | 可与路径 / 模板审计并行，但应先完成 API 摘要 | 可在 API domain 初稿后并行补数据草案 | 可在 API / 数据草案存在后并行 | 可与前三项同步准备治理框架 |
| 是否可进入正式双文档准备 | 是，但仅限 W13-E8 在用户确认路径后创建文档 | 是，但仅限 W13-E8 在用户确认路径后创建文档 | 是，但仅限 W13-E8 在用户确认路径后创建文档 | 是，但仅限 W13-E8 在用户确认路径后创建文档 |
| 是否可进入实现 | 否 | 否 | 否 | 否 |
| 结论 | 可进入双文档路径与模板准备；不可实现 | 可进入双文档路径与模板准备；不可实现 | 可进入双文档路径与模板准备；不可实现 | 可进入双文档路径与模板准备；不可实现 |

## 5. 双文档结构

### 5.1 文档一：ST13 子任务设计文档

用途：描述目标、范围、输入输出、依赖、对象、contract、验收、测试、边界、风险。不得包含实现代码。

建议文件名：`ST13_XX_DESIGN.md`，正式槽位语义对应 `SUBTASK_DESIGN.md`。

模板结构：

1. 文档状态：作者写作态、非 official state、自身不能声明 implementation-ready。
2. 关联 ST13 / WT13：`ST13_XX`、`WT13-XX`、任务名称。
3. 关联模块：主模块、相关模块、上游模块 blocker。
4. 关联 W13 事实源：四份 W13 事实源、W13-E5 audit、W13-E6 task package。
5. 背景：为什么该任务需要先做 contract / 测试 / 治理准备。
6. 目标：当前双文档设计要解决的问题。
7. 非目标：不实现、不创建代码目录、不写 `DOC_STATE.yaml`。
8. 输入：事实源、草案来源、状态层摘录、父索引。
9. 输出：contract 摘要、验收、测试、允许 / 禁止范围、确认项。
10. 依赖：前置 ST13、并行 ST13、下游 ST13。
11. contract 范围：API / domain / state / validation / testing / documentation contract。
12. 数据 / API / UI / 状态边界：只定义边界，不落实现。
13. 权限 / 安全 / 隐私边界：用户数据、简历、LLM 日志、RAG evidence、导出内容。
14. 错误态 / 空状态：API 错误、数据缺失、RAG 无命中、LLM 失败、治理失败。
15. 验收标准：文档和 contract 粒度的验收，不等于实现验收。
16. 测试要求：未来 required tests 类别、验证命令、失败停止条件。
17. 允许修改范围：按文档准备、contract 细化、未来实现分别列出。
18. 禁止修改范围：状态层、代码目录、测试代码、治理工具、Git 写操作等。
19. 用户确认项：路径、是否创建双文档、是否更新 required doc slot。
20. 下游任务：会被该任务阻塞或使用的 ST13。
21. 当前不进入实现说明：明确不能生成 implementation packet、不能打开 formal window。

### 5.2 文档二：ST13 子任务实施说明文档

用途：描述未来实现窗口如何执行、允许修改范围、禁止修改范围、验证命令、回退策略、交接要求。本窗口只设计模板，不进入实现。

建议文件名：`ST13_XX_IMPLEMENTATION.md`，正式槽位语义对应 `SUBTASK_IMPLEMENTATION.md`。

模板结构：

1. 文档状态：作者写作态、非 official state、未激活实现。
2. 关联 ST13 / WT13：`ST13_XX`、`WT13-XX`、设计文档路径。
3. 进入实现前置条件：设计文档稳定、contract 冻结、验收和 required tests 非空。
4. formal window 前置条件：用户确认、required doc slot 完整、`formal_window_open` 路径另窗处理。
5. implementation packet 前置条件：状态层 gate 通过、implementation doc 不再是骨架、允许修改范围明确。
6. 允许修改范围：未来实现窗口才允许写入的目录 / 文件。
7. 禁止修改范围：不得顺手扩大到相邻 ST13、不得绕过 contract。
8. 预期实现步骤：只写未来执行顺序，不在本窗口执行。
9. 验证命令：默认 `python -m tools.test_runner.run_tests`，并列出窄范围验证。
10. 测试要求：自动化、手动、回归和失败停止条件。
11. 回退策略：文档回退、代码回退、状态回退的不同边界。
12. 日志 / 观测要求：request_id、task_id、provider、latency、error_code 等候选字段。
13. 安全 / 隐私检查：脱敏、权限过滤、导出内容限制、RAG evidence 可见范围。
14. 交接输出格式：修改清单、验证结果、未完成项、后续窗口建议。
15. Basic Memory / Superpowers 写回要求：仅在后续收口窗口或用户明确允许时执行。
16. 当前未放行实现说明：本模板存在不等于 implementation-ready。

## 6. 双文档路径方案

### 6.1 方案 A：集中任务包目录

路径：

- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md`

解决：集中管理 W13 任务包，避免污染模块目录。

限制：与模块目录物理分离，需要索引映射。

风险：模块视角不直观，未来 required doc slot 写回时需明确这是官方双文档路径。

后续影响：适合 contract-first 和任务包治理。

### 6.2 方案 B：模块子任务目录

路径：

- `docs/modules/M01-foundation-and-platform/sub_modules/ST13_21-api-backend-service-boundary/SUBTASK_DESIGN.md`
- `docs/modules/M01-foundation-and-platform/sub_modules/ST13_21-api-backend-service-boundary/SUBTASK_IMPLEMENTATION.md`

解决：模块归属清晰。

限制：会立即创建模块子任务目录，容易被误认为实现开窗。

风险：可能再次产生孤立文档和模块历史残留。

后续影响：适合正式开窗前，但当前不建议直接执行。

### 6.3 方案 C：先只冻结路径和模板

路径：

- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`

解决：风险最低，先冻结路径方案和模板。

限制：还不能满足 required doc slot。

风险：后续还需 W13-E8 创建正式双文档。

后续影响：适合本窗口。

W13-E7 推荐方案：C。

W13-E8 确认结果：`OQ-111=A`，采用集中任务包目录。正式路径为 `docs/superpowers/plans/st13-task-packages/ST13_XX/ST13_XX_DESIGN.md` 与 `ST13_XX_IMPLEMENTATION.md`。

### 6.4 方案 D：自定义方案

由用户补充。

## 7. 四个 ST13 任务包前置清单

### 7.1 `ST13_21 / WT13-21`：API / 后端服务边界

- 任务目标：形成一期工作台 MVP API contract，覆盖 Auth、User、Role、Job、Resume、Knowledge、Interview、QuestionSet、ProgressTree、Score、Review、Weakness、Training、Asset、Export、Ops。
- 输入文档：四份 W13 事实源、W13-E5 readiness audit、W13-E6 第一批任务包草案、`DOC_STATE.yaml` 当前状态摘录。
- 输出物：API domain list、endpoint / command / query 边界、DTO 草案、权限上下文、错误码、幂等、异步任务状态、版本策略。
- 双文档路径候选：优先方案 C；后续若采用方案 A，则为 `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md` 与 `ST13_21_IMPLEMENTATION.md`。
- 关联 contract：API / domain / state / validation / documentation / testing contract。
- 允许修改范围：W13-E7 准备阶段仅限本文档和父索引；W13-E8 已创建 plans 下正式双文档，后续 contract 细化仍不得进入实现。
- 禁止修改范围：`apps/**`、`infra/**`、`tools/**`、`tests/**`、`docs/governance/**`、`docs/modules/**` 实现目录。
- 验收标准：API domain 覆盖完整，权限、错误、分页、幂等、异步状态和下游依赖清晰。
- 测试要求：未来 required tests 至少包含 contract schema validation、权限矩阵、API error taxonomy、幂等与状态流转、LLM / RAG / scoring 异步状态。
- 数据 / API / UI 边界：只定义 API contract，不建 endpoint；只给 `ST13_23` 页面规格提供调用边界。
- 安全 / 隐私边界：session、记录可见范围、管理员公共知识库、用户私有资产隔离、LLM 日志脱敏。
- 日志 / 观测边界：request_id、task_id、provider、latency、error_code、token / cost 候选字段。
- 回退策略：文档路径和 contract 草案可回退，不影响正式 `DOC_STATE.yaml`。
- 用户确认项：路径方案、是否 W13-E8 创建双文档、是否后续单独更新 required doc slot。
- 下游任务：`ST13_20`、`ST13_23`、`ST13_24`，以及多数业务 ST13。
- formal window 条件：双文档完成、contract 冻结、验收和 required tests 非空、用户确认、状态层另窗更新。
- implementation packet 条件：formal window 另窗打开且 `implementation_doc_state` 进入有效工作态；当前禁止。
- 当前阻断原因：缺双文档、缺 required doc slot、缺验收与 tests、formal window closed、M02 blocker 未消除。

### 7.2 `ST13_20 / WT13-20`：服务端保存 / 数据库

- 任务目标：形成 PostgreSQL 数据模型与服务端保存 contract，覆盖用户、岗位、简历、知识库资产、模拟记录、轮次、题目、回答、评分、复盘、薄弱项、训练动作、资产归档、导出记录。
- 输入文档：四份 W13 事实源、`ST13_21` API contract 摘要、W13-E5 audit、W13-E6 草案。
- 输出物：数据域清单、核心实体关系、关键字段、索引、唯一约束、审计字段、migration 策略和回退策略草案。
- 双文档路径候选：优先方案 C；后续若采用方案 A，则为 `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md` 与 `ST13_20_IMPLEMENTATION.md`。
- 关联 contract：domain / schema / migration / repository / privacy / testing contract。
- 允许修改范围：W13-E7 准备阶段仅限本文档和父索引；W13-E8 已创建 plans 下正式双文档，后续 contract 细化仍不建库、不写 migration。
- 禁止修改范围：数据库配置、migration 文件、ORM 模型、repository 代码、`apps/**`、`infra/**`、`tools/**`、`tests/**`、`docs/governance/**`。
- 验收标准：核心实体、关系、可见范围、软删除、审计字段、导出和删除策略清晰。
- 测试要求：未来 required tests 至少包含 schema relation validation、migration up/down dry-run、权限过滤数据可见性、模拟记录 / 评分 / 复盘 / 导出数据一致性、RAG evidence 引用完整性。
- 数据 / API / UI 边界：定义 schema 草案，不建库；依赖 `ST13_21` API domain；只说明页面数据需求，不做 UI。
- 安全 / 隐私边界：用户数据隔离、管理员公共知识库、私有上传、导出记录、删除与保留策略。
- 日志 / 观测边界：数据写入、异步任务、导出、LLM/RAG evidence 的追踪字段。
- 回退策略：schema 草案回退不影响状态层；正式 migration 必须另开窗口。
- 用户确认项：路径方案、实体范围、migration 是否进入后续 contract 细化。
- 下游任务：`ST13_24`、`ST13_05`、`ST13_10`、`ST13_13~ST13_19`。
- formal window 条件：`ST13_21` contract 至少形成可评审输入，双文档和测试要求齐备。
- implementation packet 条件：数据 contract 冻结、允许修改范围与 rollback 明确、状态层另窗放行；当前禁止。
- 当前阻断原因：依赖 API contract，缺双文档、验收、tests、formal window，M02 权限 blocker 仍在。

### 7.3 `ST13_24 / WT13-24`：测试 / 验收 / DoD

- 任务目标：形成一期工作台 MVP required tests、验收标准和五层 DoD 草案。
- 输入文档：四份 W13 事实源、`ST13_21` API contract 摘要、`ST13_20` 数据 contract 摘要、`docs/governance/TEST_POLICY.md`、W13-E5 audit。
- 输出物：ST13 required tests matrix、文档 / contract / 功能 / 体验 / 安全运维五层 DoD、P0/P1/P2/P3 验收分级、formal window 前检查清单。
- 双文档路径候选：优先方案 C；后续若采用方案 A，则为 `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md` 与 `ST13_24_IMPLEMENTATION.md`。
- 关联 contract：testing / acceptance / DoD / validation / temporary artifact governance contract。
- 允许修改范围：W13-E7 准备阶段仅限本文档和父索引；W13-E8 已创建 plans 下正式双文档，后续 contract 细化只写测试策略文档。
- 禁止修改范围：`tests/**`、`tools/**`、test runner、pytest fixture、CI 配置、`apps/**`、`infra/**`、`docs/governance/DOC_STATE.yaml`。
- 验收标准：每个 ST13 至少有验收目标、required tests 类别、最低验证命令和失败停止条件。
- 测试要求：本任务未来 required tests 包括 doc-governor validate/evaluate 不退化、required tests 字段非空、acceptance criteria 可追溯、临时产物治理符合 `TEST_POLICY.md`。
- 数据 / API / UI 边界：引用 `ST13_20` schema 和 `ST13_21` API；为 `ST13_23` 提供页面验收维度。
- 安全 / 隐私边界：测试矩阵必须包含权限、隐私隔离、导出、日志脱敏。
- 日志 / 观测边界：覆盖请求追踪、LLM/RAG provider、异步任务和导出链路。
- 回退策略：测试矩阵草案可回退，不影响状态层或测试代码。
- 用户确认项：是否把 required tests 写入每个 ST13 双文档，是否后续单独更新 state required doc slot。
- 下游任务：所有 ST13 的 formal window 和实现窗口。
- formal window 条件：测试矩阵可追溯到 API / 数据 contract，且不再只是空表。
- implementation packet 条件：required tests 可执行或可明确补齐，状态层另窗放行；当前禁止。
- 当前阻断原因：依赖 API / 数据 contract，缺正式双文档和每任务验收矩阵。

### 7.4 `ST13_25 / WT13-25`：文档治理 / 收口 / Basic Memory

- 任务目标：形成任务包准备、formal window、implementation packet、状态写回、Basic Memory / Superpowers 写回和收口验证的治理规则。
- 输入文档：`AGENTS.md`、`docs/DOC_GOVERNANCE.md`、`docs/governance/DOC_AUTOMATION.md`、`docs/governance/TEST_POLICY.md`、W13-E5 audit、W13-E6 草案、本文档前三个 ST13 摘要。
- 输出物：formal window 前置条件清单、implementation packet 禁止与放行条件清单、任务包草案到双文档的迁移策略、父索引同步方案、后续窗口计划。
- 双文档路径候选：优先方案 C；后续若采用方案 A，则为 `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md` 与 `ST13_25_IMPLEMENTATION.md`。
- 关联 contract：governance / writeback / formal-window / packet / memory / index synchronization contract。
- 允许修改范围：W13-E7 准备阶段仅限本文档和父索引；W13-E8 已创建 plans 下正式双文档，后续治理细化仍不写 state。
- 禁止修改范围：`docs/governance/DOC_STATE.yaml`、`docs/governance/**` 自动化状态文件、`tools/**`、`tests/**`、`apps/**`、`infra/**`、Git 写操作、Basic Memory 写入。
- 验收标准：明确任务包草案、正式双文档、formal window、implementation packet、实现窗口之间的先后关系。
- 测试要求：validate-state、evaluate-state、关键词扫描、Markdown UTF-8 / mojibake 扫描；后续不执行 open-window 或 packet dry-run，除非另窗授权。
- 数据 / API / UI 边界：无数据实现；只引用 API / 数据 / UI 文档，不定义业务 endpoint。
- 安全 / 隐私边界：治理写回不得泄露用户简历、LLM provider key 或私有知识库内容。
- 日志 / 观测边界：后续窗口必须保留验证命令、结果和失败停止条件。
- 回退策略：治理文档可回退，不影响正式状态层。
- 用户确认项：是否采用路径方案、是否允许 W13-E8 创建双文档、是否允许后续 required doc slot 单独 state update。
- 下游任务：W13-E8、W13-E9、W13-E10、W13-E11。
- formal window 条件：所有前置治理规则与索引同步规则明确；仍需用户确认。
- implementation packet 条件：formal window 已打开、双文档和 state slot 已对齐；当前禁止。
- 当前阻断原因：路径和模板未确认，双文档未创建，state slot 未更新，Basic Memory 写回未授权。

## 8. Contract 草案摘要

### 8.1 `ST13_21` contract 草案摘要

- 任务目标：冻结 API / 后端服务边界的第一版正式 contract 输入。
- 所属模块：主模块 M01；横向关联 M01-M10，M02 权限模块是关键 blocker。
- contract 类型：API、domain、state、validation、testing、documentation。
- 关联对象：`User`、`Role`、`Job`、`Resume`、`KnowledgeAsset`、`InterviewSession`、`InterviewQuestionSet`、`ProgressTree`、`ScoreReport`、`ReviewReport`、`WeaknessItem`、`TrainingAction`、`ExportRecord`、`OperationLog`。
- 上游依赖：W13 四份事实源、W13-E5 readiness audit、W13-E6 草案、`OQ-101~OQ-110` confirmed 边界。
- 下游依赖：`ST13_20`、`ST13_23`、`ST13_24` 和后续业务 ST13。
- 需要的 API / domain / state / validation contract：endpoint 分层、request / response DTO、权限上下文、分页过滤排序、错误码、幂等、异步任务状态、版本策略。
- 需要的测试 contract：contract schema validation、权限矩阵、错误 taxonomy、幂等状态流转、异步任务状态。
- 需要的文档 contract：双文档、父索引引用、required doc slot 路径候选、formal window 前置说明。
- 当前缺口：无正式双文档，无 required doc slot，无验收和 tests 完整矩阵，无 formal window。
- 双文档应包含章节：第 5 节模板全部章节，并在 contract 范围中细分 API/domain/state/validation/testing。
- 不进入实现说明：不得创建 `apps/api/**`、OpenAPI 文件、路由、服务或测试代码。

### 8.2 `ST13_20` contract 草案摘要

- 任务目标：冻结数据模型、服务端保存、schema / migration 和 repository 边界的正式 contract 输入。
- 所属模块：主模块 M01；横向关联 M01-M10，M02 权限和 M05 RAG / 资产是关键输入。
- contract 类型：domain、schema、migration、repository、privacy、testing、documentation。
- 关联对象：`User`、`Role`、`Job`、`Resume`、`KnowledgeAsset`、`InterviewSession`、`InterviewRound`、`Answer`、`ScoreReport`、`ScoreDimension`、`RealInterviewReview`、`MockInterviewReview`、`WeaknessItem`、`TrainingAction`、`AssetArchive`、`ExportRecord`。
- 上游依赖：`ST13_21` API domain、W13 对象模型、权限可见范围和 RAG / 导出事实源。
- 下游依赖：`ST13_24`、模拟记录、评分、复盘、资产、导出和训练相关任务。
- 需要的 API / domain / state / validation contract：实体关系、生命周期、软删除、审计字段、索引、唯一约束、数据可见范围、导出 / 删除策略。
- 需要的测试 contract：schema relation validation、migration dry-run、权限过滤、数据一致性、evidence 引用完整性。
- 需要的文档 contract：双文档、schema 摘要、migration 禁止实现说明、required doc slot 路径候选。
- 当前缺口：依赖 API contract 细化，缺正式双文档和 migration / rollback 验收。
- 双文档应包含章节：第 5 节模板全部章节，并额外展开数据 / API / 状态边界。
- 不进入实现说明：不得建库、不得写 migration、不得实现 ORM 或 repository。

### 8.3 `ST13_24` contract 草案摘要

- 任务目标：冻结测试 / 验收 / DoD 的正式 contract 输入。
- 所属模块：主模块 M01；关联 M10 与全模块。
- contract 类型：testing、acceptance、DoD、validation、temporary artifact governance、documentation。
- 关联对象：所有 `ST13_*`、required tests matrix、acceptance criteria、DoD layer、verification command、failure stop rule。
- 上游依赖：`ST13_21` API contract、`ST13_20` 数据 contract、`TEST_POLICY.md`。
- 下游依赖：所有后续 formal window 和 implementation packet。
- 需要的 API / domain / state / validation contract：验证命令、测试分层、失败停止条件、临时产物治理规则。
- 需要的测试 contract：每个 ST13 的 required tests 类别、最低验证命令、自动化 / 手动 / 回归矩阵。
- 需要的文档 contract：双文档、父索引、各 ST13 验收与 tests 非空要求。
- 当前缺口：缺正式测试矩阵、缺每个 ST13 的 required tests 落点、缺双文档路径确认。
- 双文档应包含章节：第 5 节模板全部章节，并额外展开测试矩阵和 DoD 层级。
- 不进入实现说明：不得新增 `tests/**`，不得修改 test runner 或 CI。

### 8.4 `ST13_25` contract 草案摘要

- 任务目标：冻结文档治理、formal window、implementation packet、状态写回和长期上下文写回的正式治理输入。
- 所属模块：global、M01、M10。
- contract 类型：governance、writeback、formal-window、packet、memory、index synchronization、documentation。
- 关联对象：`TASK_INDEX.md`、`MODULE_INDEX.md`、`OPEN_QUESTIONS.md`、`DOC_STATE.yaml` required doc slot、Basic Memory / Superpowers 写回、W13-E8~E11 窗口。
- 上游依赖：`AGENTS.md`、`DOC_GOVERNANCE.md`、`DOC_AUTOMATION.md`、W13-E5 / E6 / E7 文档。
- 下游依赖：W13-E8 创建双文档、W13-E9 细化 contract、W13-E10 readiness 复核、W13-E11 formal window 候选评估。
- 需要的 API / domain / state / validation contract：不直接定义业务 API；定义 state update、required doc slot、验证命令和写回规则。
- 需要的测试 contract：validate-state、evaluate-state、关键词扫描、UTF-8 回读、无实现目录检查。
- 需要的文档 contract：双文档路径、父索引挂载、OQ 确认卡、执行日志和进展成熟度同步。
- 当前缺口：路径方案未由用户确认，W13-E8 未创建双文档，state slot 未写回。
- 双文档应包含章节：第 5 节模板全部章节，并额外展开治理写回和确认卡。
- 不进入实现说明：不得打开 formal window，不得生成 packet，不得写 Basic Memory，除非后续窗口授权。

## 9. 父索引和状态同步方案

未来创建双文档后应同步：

1. `AGENTS.md`：需要索引 W13-E7 plan；若后续创建正式双文档，也应补充对应入口或引用任务包目录。
2. `TASK_INDEX.md`：在 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 下引用双文档路径，状态只能从 `task_packet_draft_created` 过渡到 `double_doc_created`、`double_doc_path_planned` 或 W13-E8.5 后的 `double_doc_registered`，不得写 implementation-ready。
3. `MODULE_INDEX.md`：记录四个 ST13 的模块映射和双文档路径方案，明确不创建模块实现目录、不升级模块成熟度。
4. W13-E6 task package：引用 W13-E7 plan 和后续正式双文档路径。
5. W13-E5 readiness audit：引用 W13-E7 plan 作为缺口收敛输入，但保留不实现结论。
6. `DOC_STATE.yaml`：W13-E7 / W13-E8 均未修改；W13-E8.5 已另开 State Update 窗口写入第一批 required doc slot，并跑 validate/evaluate。
7. formal window：打开前必须已有双文档路径、验收标准、required tests、允许 / 禁止修改范围和用户确认。
8. 避免孤立：双文档路径必须同时出现在 `AGENTS.md`、`TASK_INDEX.md`、`MODULE_INDEX.md`、W13-E6 草案和后续 W13-E8 执行日志中。
9. 避免误当实现完成：所有父索引都必须写明 `double_doc_path_planned`、`double_doc_created` 或 `double_doc_registered` 不等于 implementation-ready。

## 10. 后续窗口计划

| 窗口 | 目标 | 当前限制 |
| --- | --- | --- |
| W13-E8 | 第一批 ST13 正式双文档创建窗口；基于 W13-E7 冻结的路径方案，为 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 创建正式双文档 | 仍不实现，不写 `DOC_STATE.yaml`，不生成 packet |
| W13-E8.5 | 第一批 ST13 required doc slot State Update；把第一批双文档路径登记到 `DOC_STATE.yaml` 既有 required doc slot | 已完成；仍不实现，不生成 packet，不打开 formal window |
| W13-E9 | 第一批 ST13 contract 细化窗口；填充 API / domain / state / validation / testing contract | 仍不实现，不创建代码或测试 |
| W13-E10 | 第一批 ST13 readiness 复核窗口；检查验收标准、测试要求、允许 / 禁止修改范围和剩余 blocker | 仍不实现，若需继续 state 更新另开窗口 |
| W13-E11 | formal window 候选评估窗口；判断是否可以对某个 ST13 打开 formal window | 仍需用户确认，不得自动打开 |

这些窗口只是建议路线，不是已确认开窗。

## 11. 用户确认卡

### 11.1 确认卡 1：ST13 双文档路径方案

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| A | 放在 `docs/superpowers/plans/st13-task-packages/ST13_XX/` 下，例如 `ST13_21_DESIGN.md` / `ST13_21_IMPLEMENTATION.md` | 集中管理 W13 任务包，避免污染模块目录 | 与模块目录物理分离，需要索引映射 | 模块视角不直观 | 适合 contract-first 和任务包治理 |
| B | 放在对应 `docs/modules/Mxx-*/sub_modules/ST13_XX-*/` 下 | 模块归属清晰 | 会立即创建模块子任务目录，容易被误认为实现开窗 | 可能再次产生孤立文档和模块历史残留 | 适合正式开窗前，但当前不建议直接执行 |
| C | 先只在本文档中设计路径和模板，不创建具体双文档 | 风险最低，先冻结路径方案 | 还不能满足 required doc slot | 后续还需 W13-E8 创建正式双文档 | 适合本窗口 |
| D | 自定义方案 / 其他 | 由用户补充 | 由用户补充 | 由用户补充 | 由用户补充 |

W13-E7 推荐方案：C。

W13-E8 确认结果：用户已确认 `OQ-111=A`，实际采用方案 A 集中任务包目录。

### 11.2 确认卡 2：是否允许下一窗口创建第一批正式双文档

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| A | 允许 W13-E8 创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 的正式双文档 | 开始补 required doc slot | 仍不实现 | 如果模板不稳，会产生新过时文档 | 推荐在确认卡 1 路径确认后执行 |
| B | 暂不创建双文档，只继续细化草案 | 风险最低 | 无法推进 required doc slot | 任务包准备停滞 | 适合用户还没确认路径时 |
| C | 只创建一个 ST13 的双文档试点 | 降低批量风险 | 进度较慢 | 后续仍需批量复制 | 适合对模板不放心时 |
| D | 自定义方案 / 其他 | 由用户补充 | 由用户补充 | 由用户补充 | 由用户补充 |

W13-E7 推荐方案：A，前提是确认卡 1 路径确认后执行。

W13-E8 确认结果：用户已确认 `OQ-112=A`，已创建 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 正式双文档。

### 11.3 确认卡 3：是否允许下一窗口更新 `DOC_STATE.yaml` 的 required doc slot

| 方案 | 内容 | 解决 | 限制 | 风险 | 后续影响 |
| --- | --- | --- | --- | --- | --- |
| A | 暂不更新 `DOC_STATE.yaml`，只创建文档并更新索引 | 风险最低 | 状态层 blocker 暂不减少 | required doc slot 仍缺失 | 适合先验证文档结构 |
| B | 创建双文档后，在后续单独 State Update 窗口更新 required doc slot | 状态层逐步收敛 | 多一个窗口 | 需 validate/evaluate | 推荐 |
| C | 创建双文档同窗更新 `DOC_STATE.yaml` required doc slot | 最快减少 blocker | 风险较高 | 路径或字段错误可能导致 blocker | 不推荐当前执行 |
| D | 自定义方案 / 其他 | 由用户补充 | 由用户补充 | 由用户补充 | 由用户补充 |

W13-E7 推荐方案：B。

W13-E8 确认结果：用户已确认 `OQ-113=B`，required doc slot 留给后续单独 State Update，本窗口不修改 `DOC_STATE.yaml`。

W13-E8.5 执行结果：已按 `OQ-113=B` 在单独 State Update 窗口中更新第一批 required doc slot。

## 12. 当前不进入实现说明

截至 W13-E8.5：

- 已审计 `ST13_21 / ST13_20 / ST13_24 / ST13_25`。
- 已定义正式双文档结构。
- 已确认双文档路径方案 A：集中任务包目录。
- 已定义四个 ST13 的任务包前置清单。
- 已形成四个 ST13 的 contract 草案摘要。
- 已形成父索引和状态同步方案。
- 已输出后续窗口计划和用户确认卡。
- 已创建 `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md` 与 `ST13_21_IMPLEMENTATION.md`。
- 已创建 `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md` 与 `ST13_20_IMPLEMENTATION.md`。
- 已创建 `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md` 与 `ST13_24_IMPLEMENTATION.md`。
- 已创建 `docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md` 与 `ST13_25_IMPLEMENTATION.md`。
- 已将上述 8 个双文档路径登记到 `DOC_STATE.yaml` required doc slot。
- 未创建 `apps/**`、`infra/**`。
- 未修改 `tools/**`、`tests/**`。
- 未生成 implementation packet。
- 未打开 formal window。
- 未标记 implementation-ready。

当前状态建议写法为：`double_doc_registered` / `not_ready_for_implementation`。
