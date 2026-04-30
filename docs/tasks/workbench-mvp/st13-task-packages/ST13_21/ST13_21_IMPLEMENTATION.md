---
title: ST13_21_IMPLEMENTATION
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-21/st13-21-implementation
---

# ST13_21 IMPLEMENTATION：R0 最小 API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务实施说明；当前用于授权 `R1-DEV-07-WORKBENCH-TRUSTED-FRONTEND-SURFACE-WITH-E2E` 的最小前端可信展示面与浏览器 E2E，不是 implementation packet 本体。
- official gate：formal window 已打开；implementation approval 已批准；当前 `implementation_ready=true`，`can_generate_implementation_packet=true`。
- packet 状态：本轮 Phase A 允许刷新 implementation packet，使后续 Phase B 可以在授权路径内实现 `apps/web` 前端消费面与最小 E2E。
- implementation 状态：R0 minimal API service boundary 已完成；ST13_20 traceability write integration 已完成；ST13_21 trace read surface 已完成；本轮只补 R1 可信数据的前端可见面。
- 当前定位：让 history/detail/review/export 中的 session、turn、answer、RAG citation、evidence gap、score、review、export trace reference 能在真实前端页面被安全展示和 E2E 保护。
- 本窗口 Phase B 不修改 `DOC_STATE.yaml`，不修改后端 schema/migration/ORM，不扩大到完整知识库后台、复杂 RAG provider、批量导出或 R2 训练闭环。

## 2. 本轮实施目标

- 目标：在已完成 ST13_20 traceability write integration 与 ST13_21 trace read API surface 的基础上，为 apps/web 增加最小 R1 可信工作台展示面和真实浏览器 E2E；页面必须能展示 trace_summary、session / turn / answer trace reference、RAG citation、evidence gap、degraded / failed / retryable / empty 状态、score / review / export trace reference 和 Markdown export status，同时不得泄露完整 prompt、完整 LLM response、secret、对象存储真实路径或不可见 resource id。

## 3. 前置条件

进入 implementation 前已满足以下条件：

- `ST13_21_DESIGN.md` 已保持 R0 minimal API service boundary，不再以完整 API 合同作为本任务实施范围。
- M02 只作为 downstream identity boundary input；完整身份系统不由本任务实现。
- ST01_01 runtime baseline 已存在，且 health endpoint 不被本任务破坏。
- `DOC_STATE.yaml` 仍由专门状态窗口维护；本文档正文不替代 official state。
- 当前 official state 已满足 formal window open、`implementation_doc_state=active_working_doc`、implementation approval approved、`implementation_ready=true`。
- 已基于修正后的文档提交 packet，并已通过 packet acceptance review / commit-prep。
- implementation 已按提交后的 packet 执行并通过 acceptance refresh。

## 4. 范围内

本轮 Phase B implementation 只覆盖：

- 在现有 `apps/web` React / Vite 页面中增加最小可信数据展示区域，不做全站 UI 重构。
- 前端 API client / types 消费 `trace_summary`、RAG citation / evidence gap、score / review / export trace reference、export status / failure reason / retryable。
- 旧记录或 mock response 中没有 trace 时显示稳定 empty state，不白屏、不报错。
- degraded、failed、retryable、empty 等状态以用户可见文案呈现。
- 真实浏览器 E2E 访问实际 route，可 mock API response，但必须验证用户实际能看到的 R1 能力。
- 敏感字段过滤在页面与 E2E 中显式保护，不展示完整 prompt、完整 LLM response、secret、对象存储真实路径或不可见 resource id。
- 复用现有 API/read surface，不修改后端 schema/migration/ORM，不重写主链路。

本任务不实现完整知识库后台、复杂 RAG ingestion、embedding/vector store、schema/migration/ORM 大改、新状态管理库、批量导出或 R2 训练闭环。

## 5. 允许修改范围

packet allowed paths 限定如下，且不得自行扩大：

- `apps/web/src/**`
- `apps/web/e2e/**`
- `apps/web/playwright.config.ts`
- `apps/web/package.json`
- `package.json`
- `package-lock.json`
- `docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md`
- `docs/governance/packets/ST13_21.implementation.packet.json`
- `docs/governance/packets/ST13_21.implementation.packet.md`

如果后续确实需要其它路径，只能作为另窗建议或确认卡，不得在本任务内直接扩大。

## 6. 禁止修改

packet forbidden paths 已包含且本次不得触碰：

- `apps/api/app/schema/**`
- `apps/api/app/llm/**`
- `apps/api/app/persistence.py`
- `apps/api/app/api/v1/interviews.py`
- `apps/api/app/interview_flow/**`
- `apps/api/app/rag/**`
- `apps/api/app/review/**`
- `apps/api/app/export/**`
- `.github/**`
- `tools/**`
- `docs/governance/DOC_STATE.yaml`
- `docs/governance/transition_history.jsonl`
- `docs/governance/previews/**`
- `infra/**`
- `requirements.txt`
- `.env.example`
- DB / ORM / migration / repository 大改
- LLM provider
- 完整 RAG ingestion / indexing / embedding / vector store / reranking
- Redis / PostgreSQL / MinIO
- 真实对象存储
- M02 / M03 业务实现
- 登录 / 权限完整实现
- 资产归档
- 批量导出
- R2 训练闭环
- 完整 CI / 多平台矩阵
- Cypress 或多套 E2E 工具并存
- 新状态管理库
- 全站 UI 重构

禁止范围优先级高于 allowed paths。若后续 packet 发现 path conflict，必须停止。

## 7. 已执行实施步骤

本次 implementation 已按以下顺序完成：

1. 复核 official `DOC_STATE.yaml`、`evaluate-state` 和 `preflight-open-window`。
2. 复核 ST01_01 runtime baseline 中 health endpoint 的当前入口。
3. 建立或整理 `/api/v1` router registration 的最小骨架。
4. 保持 health endpoint 可达，避免迁移回归。
5. 添加最小 error response / error envelope。
6. 添加最小配置读取边界，且不读取外部服务 secret。
7. 只保留 future route placeholders 为未注册常量，不实现业务逻辑。
8. 补充 `httpx` 依赖以支持 FastAPI `TestClient` smoke。
9. 运行 required validation；非 sandbox 环境 API smoke / TestClient smoke 已通过，sandbox 内 TestClient 超时记录为 runtime limitation。

## 8. 测试与验证

本任务 required validation 至少包含：

- `npm --workspace apps/web run build`
- `npm --workspace apps/web run test`
- `npm --workspace apps/web run e2e`
- `.venv/bin/python -m tools.test_runner.run_tests --pytest-args tests/api/test_traceability_integration.py tests/api/test_rag_foundation.py tests/api/test_rag_persistence.py tests/api/test_review_export.py -q`
- `.venv/bin/python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml`
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`
- `.venv/bin/python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml --entity-type subtask --entity-id ST13_21`
- `git diff --check`
- `git status --short`

### 当前已确认

- `validate-state`、`evaluate-state ST13_21`、`preflight-open-window ST13_21` 通过。
- `git diff --check` 通过。
- 非 sandbox 环境 uvicorn + curl smoke 通过，`GET /api/v1/health` 返回 HTTP 200 + `{ "status": "ok" }`。
- missing route 返回 minimal error envelope。
- `httpx>=0.27,<1.0` 已加入 `requirements.txt`，用于 FastAPI `TestClient` smoke。
- 非 sandbox 环境 `TestClient` smoke 通过；sandbox 内 TestClient 可能超时，记录为 runtime limitation。
- 未新增或修改 `tests/**`。

## 9. 完成判定

本轮 R1 trace read surface 的 acceptance criteria 与当前结果：

- 页面能真实打开，且通过浏览器访问实际 route。
- 页面展示 trace_summary、session / turn / answer trace reference 的安全摘要。
- 页面展示 RAG citation 列表，包括 source summary、chunk summary、chunk index 或位置。
- 页面展示 evidence gap：no_result、permission_filtered、index_pending、index_failed、rag_unavailable 至少覆盖当前 slice 可消费状态。
- 页面展示 degraded / failed / retryable / empty 状态。
- 页面展示 score / review / export trace reference 的安全摘要。
- Markdown export 区域展示 export status、failure reason、retryable。
- 旧记录无 trace 时显示稳定空态，不白屏、不报错。
- 页面不得展示完整 prompt、完整 LLM response、secret、对象存储真实路径、不可见 resource id 或 provider secret。
- 至少一条真实浏览器 E2E 测试通过。
- 继续复用现有 trace read API surface，不新增后端 schema/migration/ORM，不新增无关依赖。
- 不修改后端 schema / migration / ORM、复杂 RAG provider、R2 训练闭环或资产归档。

完成判定不扩大实现范围；后续 implementation 仍必须受 packet allowed / forbidden paths 限制。

## 10. 停止条件

出现以下任一情况必须停止：

- 需要修改 `DOC_STATE.yaml` 或 `transition_history.jsonl`。
- 需要修改 formal window 或 implementation approval 状态。
- 需要手工修改、覆盖或重新生成 implementation packet，除非处于本任务 Phase A 的官方 packet generation 步骤。
- 需要修改 `tools/**`、`.github/**`、未授权后端测试文件或 `apps/api/app/schema/**`。
- 需要实现超出 trace/read surface 前端消费面的 Job / Resume / Knowledge / Interview / Score / Review / Export 业务 API。
- 需要接入 DB、ORM、migration、LLM、RAG、Redis、PostgreSQL、MinIO 或对象存储。
- 需要实现完整 RAG ingestion、embedding、vector store、reranking、资产归档、批量导出或 R2 训练闭环。
- 需要扩大 M02 / M03 业务实现范围。
- 需要新增非 E2E / UI 必要第三方依赖或环境变量。
- 依赖不可用但有人要求通过 vendor code 或临时大改绕过。

## 11. 回退策略

- 文档回退：只回退本双文档中本次 scope correction 内容。
- 状态回退：必须另开 State Update 或治理窗口；本文档不得直接修改 `DOC_STATE.yaml`。
- 代码回退：仅适用于已提交的 implementation commit；需另窗按允许路径处理。
- 验证失败：停止后续 state sync / formal window 讨论，先输出失败命令、失败原因和受影响范围。

## 12. 当前 gate 与实施验收说明

`ST13_21_IMPLEMENTATION.md` 已在 official state 中登记为 active working doc；当前 confirmed / derived gate 事实为：

- `implementation_doc_state=active_working_doc`
- `maturity=L5`
- `readiness=downstream_ready`
- `implementation_approval_status=approved`
- `implementation_ready=true`
- formal window open
- `can_generate_implementation_packet=true`

上述状态仍是 official state / gate 事实，不等于 accepted / done state 已写回。本轮 R1 trace/read surface 的 packet 输入为：

- 目标：暴露 history/detail/review/export 可消费的最小 trace summary read surface。
- 允许路径：API router、interview_flow service/contract、traceability read helper、persistence read helper、RAG/review/export 最小读集成和 `tests/api/test_traceability_integration.py`。
- 禁止路径：UI、schema/migration/ORM、依赖、LLM provider、完整 RAG ingestion、未授权测试、governance state、R2 能力。

## 13. R1 API 契约冻结执行说明

`R1-W02-ST13_21-API-CONTRACT-FREEZE` 只执行 docs-only contract freeze。本文档记录后续执行边界，不代表本窗口进入 implementation，不生成 packet，不打开 formal window，不修改 official state。

### 13.1 本窗口新增的实施输入

后续 `ST13_20` R1 data / schema / migration readiness 可以从 `ST13_21_DESIGN.md` 第 13 节消费以下输入：

- R1 API domain boundary：Identity / Auth context、Job / Resume、Knowledge / RAG、Interview、Score、Review、Export、History。
- action list：以 create / read / update / archive / restore / generate / retry / list / detail 等 action 语义为边界，不在本窗口创建 endpoint。
- request contract：actor context、resource identity、snapshot / version、operation intent、RAG query context、LLM / generation context。
- response contract：resource response、permission-aware response、async response、evidence response、review / score response、export response。
- error envelope：`error.code`、`error.message`、`error.reason`、`error.request_id`、`error.resource_ref`、`error.retryable`、`error.degraded`、`error.details`。
- permission context：user / role / workspace / tenant 候选、resource visibility、permission denied 与 resource not visible 的区分。
- async / degradation semantics：RAG indexing、RAG no result、LLM failed、parsing low confidence、score / review pending、export failed、restore failed。
- traceability fields：request / operation、actor / workspace scope、resource refs、source snapshot refs、status fields、evidence refs、error refs、export refs。
- RAG evidence / citation、score / review / export / history 的共享 API 语义。

### 13.2 ST13_20 下游消费边界

`ST13_20` 可以把本窗口冻结内容作为 data / schema / migration readiness 的上游输入，但必须遵守：

- 只有已在 `ST13_21_DESIGN.md` 第 13 节稳定表达的 API 语义，才能进入 `ST13_20` 的字段、状态、错误、traceability 讨论。
- `ST13_21` 中标注为 contract 占位的字段，不得被 `ST13_20` 直接写成数据库字段或 migration。
- 完整 prompt 原文、完整 LLM response 原文、embedding 向量、provider secret、对象存储真实路径、完整权限矩阵、企业级 tenant 配置、PDF 模板配置和训练任务调度参数不得在 `ST13_20` 中直接落库。
- 如果 `ST13_20` 发现 API contract 与 data contract 字段漂移，应回到文档评审窗口，不得通过实现补丁临时修正。

### 13.3 本窗口仍禁止的内容

本窗口明确未执行且仍禁止：

- 不写业务 API。
- 不创建 endpoint、OpenAPI 文件、schema、migration、ORM、repository、worker、queue、provider adapter 或测试文件。
- 不修改 `apps/**`、`tests/**`、`docs/governance/**`、`DOC_STATE.yaml`。
- 不生成 implementation packet。
- 不打开 formal window。
- 不新增依赖、环境变量或长期状态入口。
- 不把 R1 contract freeze 写成 accepted / done / implementation-ready 状态。

### 13.4 后续验证口径

本窗口的完成判定只面向文档与治理：

- `ST13_21_DESIGN.md` 已明确 R1 API contract freeze 范围。
- R1 API contract 已从 R0 minimal service boundary 扩展为可供 `ST13_20` 消费的 domain、request、response、error、permission、async、degradation、traceability 和 evidence contract。
- R0 / R1 / R2 scope split 已明确。
- 禁止实现范围已明确。
- 代码、测试、governance state、packet 和 formal window 未修改。

### 13.5 前端消费边界补丁

`R1-W02a-ST13_21-FRONTEND-UI-CONSUMER-CONTRACT-PATCH` 在 `ST13_21_DESIGN.md` 第 14 节补齐前端消费边界。该补丁只说明前端如何消费 R1 API contract，不实现页面、组件、测试或 endpoint。

后续前端或测试窗口可以消费以下 contract 信息：

- R1 用户可见 surface：工作台概览、模拟记录列表、发起模拟入口、面试台、评分 / 复盘详情、知识库入口、Markdown 导出入口、账号 / 权限提示。
- 前端直接消费 action：current user / permission context、job / resume list and detail、knowledge / RAG status and search context、interview start / restore / submit / finish / detail / history、score / review read or generate status、export create / status / retry。
- 前端展示字段：资源摘要、评分与复盘、RAG citation / evidence / evidence gap、异步状态、权限和可见性安全摘要。
- 后端追踪字段：`request_id`、`operation_id`、audit event id、source snapshot refs、provider alias、model alias 等默认不直接展示。
- 错误和状态：permission denied、resource not visible、archived resource、validation failed、RAG unavailable、LLM failed、pending / running、retryable、empty history / empty knowledge。
- R1 / R2 UI 边界：R1 只要求主链路、证据、评分复盘、导出、历史回看、权限 / 降级 / 空状态可感知；训练抽屉完整闭环、资产归档、复杂组织后台和团队共享知识库治理延后。

本补丁仍禁止修改 `apps/**`、`tests/**`、`docs/governance/**`、`DOC_STATE.yaml`，禁止新增依赖、schema、migration、packet 或 formal window。

## 14. 下一步

下一步建议开启 `R1-W03-ST13_20-DATA-SCHEMA-MIGRATION-READINESS`。该窗口应只消费本次 `ST13_21` R1 API contract freeze 结果，先做 data / schema / migration readiness，不直接创建 schema、migration、ORM、业务代码或测试。
