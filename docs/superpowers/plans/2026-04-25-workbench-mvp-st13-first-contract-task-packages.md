# AI 模拟面试一期工作台 MVP ST13 第一批 contract 任务包草案

## 1. 文档定位

本文档是 `W13-E6 / ST13 第一批任务包准备窗口` 的输出。

本窗口基于用户已确认的 `OQ-101~OQ-110`：

- `OQ-101=A`：先只生成 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 四个横向 contract / 测试 / 治理任务包草案。
- `OQ-102=A`：任务包生成顺序采用横向 contract 先行。
- `OQ-103=A`：第一批只做 `ST13_21 / ST13_20 / ST13_24 / ST13_25`。
- `OQ-104=B`：先在 `docs/superpowers/plans/**` 生成任务包草案，不创建模块子任务目录。
- `OQ-105=A`：在 formal window 和 implementation packet 之前禁止创建 `apps/api/**`、`apps/web/**` 或 `infra/**`。
- `OQ-106=A`：所有 P0 gate 补齐前禁止生成 implementation packet。
- `OQ-107=A`：每个 ST13 的任务包、双文档、验收、测试和用户确认齐备后再逐个打开 formal window。
- `OQ-108=A`：任务包准备与代码实现严格拆窗。
- `OQ-109=A`：API contract 先行。
- `OQ-110=C`：后端 contract 与前端页面规格可并行准备，等 contract 合并后再实现。

本文档只生成任务包草案，不创建正式子任务双文档，不生成 implementation packet，不打开 formal window，不进入实现，不修改 `docs/governance/DOC_STATE.yaml`。

## 2. 当前状态层摘要

`docs/governance/DOC_STATE.yaml` 当前正式任务入口仍为 `ST13_01~ST13_25`。

本轮基线验证结果：

- `validate-state`: `ok=true,error=0,warning=0`
- `evaluate-state`: `ok=true,error=0,warning=0`
- `documents_blocked_count=0`
- `modules_blocked_count=1`
- `subtasks_blocked_count=25`

因此本轮任务包草案不能被解释为 `implementation-ready`。所有 ST13 仍处于 blocked 状态，核心 blocker 仍包括缺设计文档、缺实施文档、缺验收标准、缺 required tests、formal window closed、implementation doc not active。

## 3. 第一批任务包顺序

第一批任务包草案采用以下顺序：

1. `ST13_21 / WT13-21`：API / 后端服务边界。
2. `ST13_20 / WT13-20`：服务端保存 / 数据库。
3. `ST13_24 / WT13-24`：测试 / 验收 / DoD。
4. `ST13_25 / WT13-25`：文档治理 / 收口 / Basic Memory。

排序理由：

- `ST13_21` 是后续页面、数据、LLM、RAG、评分、复盘和导出的共同 contract 前置。
- `ST13_20` 是所有服务端保存、历史记录、复盘、资产和权限过滤的持久化前置。
- `ST13_24` 需要基于 API 与数据 contract 建立 required tests 和验收矩阵。
- `ST13_25` 负责收口任务包、formal window 条件、写回策略和后续窗口边界。

`OQ-110=C` 表示后续可并行准备前端页面规格文档，但本批不生成 `ST13_23` 页面任务包，也不创建 UI skeleton。

## 4. 通用任务包边界

### 4.1 本轮允许输出

- 任务包草案。
- 任务目标、输入文档、输出物、依赖、验收、测试、数据/API/UI 边界、安全/隐私、日志/观测、回退策略。
- 后续正式子任务双文档的路径建议。
- 后续 formal window 条件建议。
- 后续验证命令建议。

### 4.2 本轮禁止输出

- 任何 `implementation packet`。
- 任何 `ready_for_implementation` 或 `implementation-ready` 结论。
- 任何 formal window open 结论。
- 任何 `apps/**`、`infra/**`、`tools/**`、`tests/**` 代码或目录创建。
- 任何 `docs/governance/DOC_STATE.yaml` 写入。
- 任何模块子任务目录或正式 `SUBTASK_DESIGN.md` / `SUBTASK_IMPLEMENTATION.md` 创建。

### 4.3 通用完成状态

本批四个 ST13 的输出状态均为：

- `task_packet_draft_created`
- `not_ready_for_implementation`
- `formal_window_closed`
- `implementation_packet_forbidden`

## 5. ST13_21 任务包草案：API / 后端服务边界

### 5.1 基本信息

- ST13 ID：`ST13_21`
- WT13 alias：`WT13-21`
- 任务名称：API / 后端服务边界
- 所属模块：M01-M10
- 第一批顺序：1
- 当前状态：`blocked`
- 本轮状态：`task_packet_draft_created`，不是 implementation-ready

### 5.2 任务目标

形成一期工作台 MVP 的 API contract 草案，覆盖账号、权限、岗位、简历、知识库、模拟面试、面试台、多轮状态、评分、复盘、资产、导出、运维观测等服务边界。

该任务只定义 contract，不实现 FastAPI 服务、不创建路由文件、不创建 `apps/api/**`。

### 5.3 输入文档

- `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`
- M01-M10 的模块 API / schema / task index 文档，作为参考输入。

### 5.4 输出物

- API domain list。
- Endpoint / command / query 边界清单。
- Request / response DTO 草案。
- 认证与权限上下文约定。
- 分页、筛选、排序、错误码、幂等和版本策略。
- LLM / RAG / scoring / review 的异步任务与状态查询 contract。
- 下游 `ST13_20`、`ST13_23`、`ST13_24` 的 contract 输入。

### 5.5 允许修改范围

本轮草案允许：

- `docs/superpowers/plans/**`
- 根文档中的计划、索引、进展、开放问题和设计决策同步。

后续正式任务包如需创建子任务双文档，必须先经用户确认；本轮不创建。

### 5.6 禁止修改范围

- `apps/**`
- `infra/**`
- `tools/**`
- `tests/**`
- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- `docs/modules/**` 正式子任务目录
- `package*.json`、`pnpm-lock.yaml`

### 5.7 依赖关系

- 前置依赖：W13 四份事实源、W13-E5 readiness audit、用户确认 `OQ-101~OQ-110`。
- 后置依赖：`ST13_20` 数据库 schema、`ST13_23` 页面规格、`ST13_24` 测试矩阵、`ST13_01` 权限 contract。
- blocked_by：`module:M02` 仍需后续模块同步；不阻断 contract 草案，但阻断 implementation-ready。

### 5.8 验收标准

- API domain 至少覆盖 Auth、User、Role、Job、Resume、Knowledge、Interview、QuestionSet、ProgressTree、Score、Review、Weakness、Training、Asset、Export、Ops。
- 每个 domain 至少有输入对象、输出对象、权限上下文、错误态和下游依赖。
- 明确哪些 API 是一期必须，哪些是 future candidate。
- 明确不创建代码、不生成 OpenAPI 文件、不启动服务。

### 5.9 测试要求

本任务包草案只定义未来 required tests：

- contract schema validation。
- 权限矩阵测试。
- API error taxonomy 测试。
- 幂等与状态流转测试。
- LLM / RAG / scoring 异步任务状态测试。

本轮不新增测试文件。

### 5.10 边界

- 数据边界：只引用对象模型，不落库。
- API 边界：只定义 contract，不实现 endpoint。
- UI 边界：为 `ST13_23` 提供页面调用约束，不做页面规格。
- 安全 / 隐私：必须包含 session、用户可见范围、管理员公共知识库、私有资产隔离。
- 日志 / 观测：必须定义 request_id、task_id、provider、latency、error_code、cost token 等候选字段。
- 回退策略：contract 草案可回退到 W13 四份事实源与 W13-E5 audit，不影响正式状态层。
- Basic Memory / Superpowers：任务包正式确认后再写入会话总结；本草案只记录写回要求。

## 6. ST13_20 任务包草案：服务端保存 / 数据库

### 6.1 基本信息

- ST13 ID：`ST13_20`
- WT13 alias：`WT13-20`
- 任务名称：服务端保存 / 数据库
- 所属模块：M01-M10
- 第一批顺序：2
- 当前状态：`blocked`
- 本轮状态：`task_packet_draft_created`，不是 implementation-ready

### 6.2 任务目标

形成一期工作台 MVP 的 PostgreSQL 数据模型与服务端保存 contract 草案，覆盖用户、岗位、简历、知识库资产、模拟记录、面试轮次、问题、回答、评分、复盘、薄弱项、训练动作、资产归档和导出记录。

该任务只定义 schema / migration / repository 边界，不创建数据库、不写 migration、不实现 repository。

### 6.3 输入文档

- W13 四份事实源。
- `ST13_21` API contract 草案。
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`
- M01-M10 的模块 schema 文档，作为历史参考。

### 6.4 输出物

- 一期 MVP 数据域清单。
- 核心实体与关系草案。
- 关键字段、索引、唯一约束、软删除和审计字段建议。
- migration 策略和回退策略草案。
- 数据保留、隐私隔离、导出和删除策略草案。
- 下游 `ST13_24` 测试矩阵输入。

### 6.5 允许修改范围

本轮草案允许：

- `docs/superpowers/plans/**`
- 根文档中的计划、索引、进展、开放问题和设计决策同步。

### 6.6 禁止修改范围

- `apps/**`
- `infra/**`
- `tools/**`
- `tests/**`
- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- 数据库配置、migration 文件、ORM 模型和 repository 代码。

### 6.7 依赖关系

- 前置依赖：`ST13_21` API domain 边界。
- 后置依赖：`ST13_01` 权限、`ST13_05` 记录列表、`ST13_10` RAG、`ST13_13~ST13_19` 评分复盘导出链路。
- blocked_by：`module:M02` 权限文档仍 blocked；数据 contract 可草拟，但不能 implementation-ready。

### 6.8 验收标准

- 至少覆盖 User、Role、Job、Resume、KnowledgeAsset、InterviewSession、InterviewRound、InterviewQuestionSet、Answer、ScoreReport、ScoreDimension、RealInterviewReview、MockInterviewReview、WeaknessItem、TrainingAction、AssetArchive、ExportRecord。
- 明确哪些实体必须持久化，哪些可派生，哪些是 future candidate。
- 明确用户可见范围、管理员公共知识库、私有知识库和资产归档的隔离关系。
- 明确 migration 和 rollback 策略，但不生成 migration。

### 6.9 测试要求

本任务包草案只定义未来 required tests：

- schema relation validation。
- migration up/down dry-run。
- 权限过滤数据可见性测试。
- 模拟记录、评分、复盘、导出链路的数据一致性测试。
- RAG asset 与 evidence 引用完整性测试。

本轮不新增测试文件。

### 6.10 边界

- 数据边界：定义 PostgreSQL schema 草案，不建库。
- API 边界：依赖 `ST13_21`，不定义 endpoint 细节。
- UI 边界：只说明页面所需数据，不做页面设计。
- 安全 / 隐私：必须覆盖用户数据隔离、管理员公共知识库、私有上传、导出记录、删除与保留。
- 日志 / 观测：需要定义数据写入、异步任务、导出、LLM/RAG evidence 的追踪字段。
- 回退策略：schema 草案回退不影响正式状态层；正式 migration 必须另开窗口。
- Basic Memory / Superpowers：后续正式确认后写入数据模型决策摘要。

## 7. ST13_24 任务包草案：测试 / 验收 / DoD

### 7.1 基本信息

- ST13 ID：`ST13_24`
- WT13 alias：`WT13-24`
- 任务名称：测试 / 验收 / DoD
- 所属模块：M01、M10、全模块
- 第一批顺序：3
- 当前状态：`blocked`
- 本轮状态：`task_packet_draft_created`，不是 implementation-ready

### 7.2 任务目标

形成一期工作台 MVP 的验收标准、required tests 和五层 DoD 草案，使后续每个 ST13 都能拥有明确的测试入口和开窗完成标准。

该任务只定义测试矩阵，不创建测试文件，不运行实现测试。

### 7.3 输入文档

- W13 四份事实源。
- `ST13_21` API contract 草案。
- `ST13_20` 数据库 contract 草案。
- `docs/governance/TEST_POLICY.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`

### 7.4 输出物

- ST13 required tests matrix。
- 五层 DoD 映射：文档、contract、功能、体验、安全/运维。
- P0/P1/P2/P3 验收分级。
- 每个 ST13 的最低 required tests 候选。
- 后续 formal window 打开前检查清单。

### 7.5 允许修改范围

本轮草案允许：

- `docs/superpowers/plans/**`
- 根文档中的计划、索引、进展、开放问题和设计决策同步。

### 7.6 禁止修改范围

- `tests/**`
- `tools/**`
- `apps/**`
- `infra/**`
- `docs/governance/DOC_STATE.yaml`
- test runner、pytest fixture、CI 配置。

### 7.7 依赖关系

- 前置依赖：`ST13_21` API contract、`ST13_20` 数据模型。
- 后置依赖：所有 ST13 的正式任务包和 formal window。
- blocked_by：全部 ST13 仍缺正式双文档和 implementation scope；本任务只能形成测试草案。

### 7.8 验收标准

- 每个 ST13 至少拥有验收目标、required tests 类别、最低验证命令和失败停止条件。
- 明确哪些测试必须在实现前定义，哪些测试可在 implementation window 中补齐。
- 明确默认测试入口优先使用 `python -m tools.test_runner.run_tests`。
- 明确本轮不创建测试、不运行业务实现测试。

### 7.9 测试要求

本任务本身的未来 required tests 包括：

- doc-governor validate/evaluate 不退化。
- 任务包中的 required tests 字段非空。
- 每个 ST13 的 acceptance criteria 与 required tests 可追溯到 W13 事实源。
- 临时产物治理符合 `TEST_POLICY.md`。

本轮仅运行状态验证和关键词扫描。

### 7.10 边界

- 数据边界：只引用 `ST13_20` schema 草案。
- API 边界：只引用 `ST13_21` contract 草案。
- UI 边界：为后续 `ST13_23` 页面规格提供验收维度。
- 安全 / 隐私：测试矩阵必须包含权限、隐私隔离、导出、日志脱敏。
- 日志 / 观测：必须覆盖请求追踪、LLM/RAG provider、异步任务和导出链路。
- 回退策略：测试矩阵草案可回退，不影响正式状态层。
- Basic Memory / Superpowers：正式收口时写入测试策略摘要。

## 8. ST13_25 任务包草案：文档治理 / 收口 / Basic Memory

### 8.1 基本信息

- ST13 ID：`ST13_25`
- WT13 alias：`WT13-25`
- 任务名称：文档治理 / 收口 / Basic Memory
- 所属模块：global、M01、M10
- 第一批顺序：4
- 当前状态：`blocked`
- 本轮状态：`task_packet_draft_created`，不是 implementation-ready

### 8.2 任务目标

形成 ST13 任务包准备、formal window、implementation packet、状态写回、Basic Memory / Superpowers 写回和收口验证的治理草案。

该任务只定义治理流程，不打开 formal window，不生成 implementation packet，不写 `DOC_STATE.yaml`。

### 8.3 输入文档

- `AGENTS.md`
- `docs/DOC_GOVERNANCE.md`
- `docs/governance/DOC_AUTOMATION.md`
- `docs/governance/TEST_POLICY.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`
- 本文档中 `ST13_21 / ST13_20 / ST13_24` 的任务包草案。

### 8.4 输出物

- ST13 formal window 前置条件清单。
- implementation packet 禁止与放行条件清单。
- 任务包草案到正式子任务双文档的迁移策略。
- Basic Memory / Superpowers 写回策略。
- 后续 W13-E7 / W13-F 窗口建议。

### 8.5 允许修改范围

本轮草案允许：

- `docs/superpowers/plans/**`
- 根文档中的计划、索引、进展、开放问题和设计决策同步。

### 8.6 禁止修改范围

- `docs/governance/DOC_STATE.yaml`
- `docs/governance/**` 自动化状态文件
- `tools/**`
- `tests/**`
- `apps/**`
- `infra/**`
- Git 提交或推送

### 8.7 依赖关系

- 前置依赖：用户确认 `OQ-101~OQ-110`。
- 后置依赖：后续正式子任务双文档创建、formal window open、implementation packet。
- blocked_by：所有 ST13 仍缺 formal window 与双文档；治理任务不能替代状态层放行。

### 8.8 验收标准

- 明确任务包草案、正式子任务双文档、formal window、implementation packet、实现窗口之间的先后关系。
- 明确任何 ST13 在缺双文档、验收、测试和用户确认前不得 implementation-ready。
- 明确 Basic Memory 只作为长期上下文层，不能反推 `DOC_STATE.yaml`。
- 明确后续若写 Basic Memory，必须先检索、后写入、再回读验证。

### 8.9 测试要求

本任务包草案只定义治理验证：

- `validate-state`。
- `evaluate-state`。
- 关键词扫描。
- Markdown UTF-8 / mojibake 扫描。
- 后续正式文档创建后再执行 doc-governor 相关 open-window / packet dry-run。

本轮不执行 open-window，不执行 packet dry-run。

### 8.10 边界

- 数据边界：无数据实现。
- API 边界：只依赖 `ST13_21`。
- UI 边界：只记录 `OQ-110=C` 的后续并行准备口径，不生成页面规格。
- 安全 / 隐私：治理写回不得泄露用户简历、LLM provider key 或私有知识库内容。
- 日志 / 观测：记录后续窗口应保留验证命令、结果和失败停止条件。
- 回退策略：本文档可作为草案回退；不影响正式状态层。
- Basic Memory / Superpowers：本任务定义写回要求，实际写回应在后续收口窗口或用户明确允许时执行。

## 9. 后续窗口建议

### 9.1 W13-E7：第一批 contract 正式子任务双文档准备

建议目标：

1. 基于本文档为 `ST13_21 / ST13_20 / ST13_24 / ST13_25` 生成正式子任务双文档路径方案。
2. 若用户确认，创建正式 `SUBTASK_DESIGN.md` / `SUBTASK_IMPLEMENTATION.md`，但仍不实现。
3. 将每个任务的验收标准、required tests、允许修改范围、禁止修改范围写入正式双文档。
4. 不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet。

### 9.2 W13-E8：ST13_23 前端页面规格并行准备

在 `OQ-110=C` 下，后续可并行准备 `ST13_23` 前端工作台页面集合规格，但必须等待 `ST13_21` API contract 合并后再进入实现。

## 10. 当前不进入实现说明

本轮输出不能作为实现放行依据。

截至本文档完成：

- formal window 未打开。
- implementation packet 未生成。
- `DOC_STATE.yaml` 未修改。
- `apps/**`、`infra/**`、`tools/**`、`tests/**` 未修改。
- `ST13_21 / ST13_20 / ST13_24 / ST13_25` 只是任务包草案完成，不是 implementation-ready。
