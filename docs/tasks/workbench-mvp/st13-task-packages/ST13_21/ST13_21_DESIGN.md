---
title: ST13_21_DESIGN
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-21/st13-21-design
---

# ST13_21 DESIGN：R0 最小 API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务设计文档；记录 ST13_21 R0 minimal API service boundary 的设计边界与实施后同步事实；不是 implementation packet，不是 official state。
- official gate：formal window 已打开；implementation approval 已批准；当前 `implementation_ready=true`，`can_generate_implementation_packet=true`。
- packet 状态：implementation packet 已重新生成并提交，提交为 `89d82cf gov: generate ST13_21 implementation packet`。
- implementation 状态：R0 minimal API service boundary 已完成并通过 acceptance refresh；实现提交为 `b9d7fd3`，TestClient 依赖提交为 `1f65274`。
- 当前定位：为 `ST13_21` post-implementation docs / module sync 提供与 official state 和实际实现一致的文档事实。
- 本窗口不修改 `DOC_STATE.yaml`，不修改 packet，不继续 implementation，不扩大业务 API 范围。

## 2. 关联 ST13 / WT13

- ST13：`ST13_21`
- WT13 alias：`WT13-21`
- 任务名称：API / 后端服务边界
- 当前收敛范围：R0 minimal API service boundary
- 当前 official state：`implementation_doc_state=active_working_doc`，`maturity=L5`，`readiness=downstream_ready`，`formal_window_status=open`，`implementation_approval_status=approved`。
- 当前 evaluate / preflight 派生状态：blockers `[]`，`implementation_ready=true`，`can_generate_implementation_packet=true`。
- 当前实现结果：已按 packet 完成最小 `/api/v1` router registration、`GET /api/v1/health` regression、minimal error envelope、minimal config boundary 和未注册 future route placeholders；acceptance refresh 已通过。

## 3. 当前 official gate 背景

截至本轮 post-implementation 文档同步，`ST13_21` 已完成 state sync、scoped formal window sync、implementation approval、packet generation / commit、minimal API service boundary implementation 和 acceptance refresh。当前 official gate 事实为：

- `formal_window_status=open`
- `implementation_approval_status=approved`
- `implementation_ready=true`
- `can_generate_implementation_packet=true`
- `evaluate-state` / `preflight-open-window` 对 `ST13_21` 的 blocker 结果为 `[]`
- implementation packet 已提交：`89d82cf`
- implementation commit 已提交：`b9d7fd3`
- TestClient smoke 依赖 commit 已提交：`1f65274`

本文只同步 implementation 后事实，不写 official state，不修改 packet，不继续 implementation。

## 4. R0 目标

`ST13_21` 在 R0 的目标不是定义完整业务 API 合同，而是在 `ST01_01` 最小 FastAPI runtime 基础上建立后端服务边界骨架：

- 统一 `/api/v1` prefix。
- 明确 router organization 和 router registration 的最小模式。
- 保持 `GET /api/v1/health` 可达，不因 API 边界整理被迁移或破坏。
- 定义最小 error response / error envelope 边界。
- 定义最小配置读取边界。
- 为后续 Job / Resume / Knowledge / Interview / Score / Review / Export 路由保留 future contract boundary。
- 只消费 M02 的身份上下文和权限语义输入，不实现完整身份系统。

## 5. R0 范围内

本任务已在 implementation window 内只围绕以下最小 API service boundary 做骨架级实现：

| 范围 | R0 最小含义 | 不代表 |
| --- | --- | --- |
| FastAPI runtime 承接 | 基于 ST01_01 已落地的最小 API runtime 继续组织服务边界 | 不重建 runtime，不扩展基础设施 |
| `/api/v1` prefix | 所有后续业务路由统一挂载到 `/api/v1` 下 | 不实现业务 endpoint |
| Router organization | 明确 API router 的分组、注册入口和未来扩展方式 | 不生成完整 OpenAPI 文件 |
| Health endpoint | 保持 `GET /api/v1/health` 继续可达 | 不把 health 迁入业务 router 导致回归 |
| Error envelope | 定义最小错误响应字段和错误码位置 | 不完成全量业务错误 taxonomy |
| Config boundary | 只读取最小运行参数和非敏感配置 | 不接入 DB、Redis、MinIO、LLM、RAG |
| Future routes placeholder | 为后续业务 domain 保留路由边界或注释型占位 | 不实现 Job / Resume / Interview 等业务 |
| M02 identity input | 消费 `CurrentUserContext`、`401/403/404` 和 admin/member 语义 | 不实现完整 login/session/OAuth/JWT |

## 6. 明确延期 / 排除

以下内容不属于 `ST13_21` R0 minimal scope，后续必须由对应任务或另窗授权承接：

- 完整登录、session、OAuth、JWT、刷新 token、撤销 token。
- 团队管理、成员高级管理、完整成员 CRUD、管理员后台。
- 岗位业务 API、简历业务 API、知识库业务 API。
- 面试会话业务 API、回答提交业务 API、追问业务 API。
- 评分业务 API、复盘业务 API、导出业务 API。
- DB / ORM / migration / repository。
- LLM provider、RAG、embedding、向量检索。
- Redis / PostgreSQL / MinIO 真实接入。
- 文件上传、对象存储、真实 bucket / client / provider 初始化。
- `apps/web/**`、Dashboard、App Shell、PageHeader、DataTable。
- `tests/**`，除非后续 packet 明确授权。
- `.github/**`、完整 CI、E2E、多平台矩阵。
- 大规模重构或跨模块业务实现。

## 7. API service boundary 设计

### 7.1 Prefix 与 router registration

已落地的最小 router registration 模式为：

1. `apps/api/app/main.py` 创建 FastAPI app，并注册 `build_api_v1_router(settings.api_prefix)`。
2. `settings.api_prefix` 默认来自 `API_PREFIX=/api/v1`。
3. `apps/api/app/api/v1/__init__.py` 统一管理 `/api/v1` 下路由注册。
4. 当前只注册 health router，`GET /api/v1/health` 继续返回 `{ "status": "ok" }`。
5. future route names 仅作为未注册常量存在，未创建 `/auth`、`/jobs`、`/resumes`、`/interviews`、`/scores`、`/reviews`、`/exports` 等业务 endpoint。

### 7.2 错误响应与 error envelope

R0 最小错误边界只要求当前服务骨架能表达稳定错误形状：

- `error.code`：机器可读错误码。
- `error.message`：面向调用方的简短说明。
- `error.request_id` / `error.details` 未在本次 R0 implementation 中落地，后续如需扩展必须由单独 contract / test 任务承接。

当前实现通过 `http_exception_handler` 将 Starlette / FastAPI HTTPException 转为 `{"error": {"code": "HTTP_<status>", "message": "<detail>"}}`。R0 只冻结 envelope 位置和最小字段，不完成业务错误全集。完整的权限、RAG、LLM、导出、状态冲突错误 taxonomy 作为后续 contract 或测试任务继续承接。

### 7.3 配置读取边界

R0 配置读取只覆盖最小运行参数：

- API title / version / environment。
- API prefix。
- API host / port。

当前实现通过 `ApiSettings` 读取 `API_TITLE`、`API_VERSION`、`ENVIRONMENT`、`API_PREFIX`、`API_HOST`、`API_PORT`。R0 不读取真实数据库 DSN、Redis URL、MinIO endpoint、LLM provider key、embedding provider 或对象存储 secret。`.env.example` 只能出现安全占位，不得包含真实 secret。

### 7.4 未来路由占位边界

允许在文档和骨架中保留 future contract boundary：

- Auth / Identity：只保留身份上下文与权限语义边界。
- Job / Resume：只保留未来路由分组，不实现保存、读取或业务校验。
- Knowledge / RAG：只保留未来路由分组，不实现上传、切块、索引、检索。
- Interview：只保留未来路由分组，不实现会话启动、回答提交或追问。
- Score / Review / Export：只保留未来路由分组，不实现评分、复盘、导出。

placeholder 不等于 endpoint 已实现，也不等于 OpenAPI 已冻结。当前实现只保留未注册 placeholder 常量，不暴露业务 endpoint。

## 8. M02 downstream input 边界

M02 当前只作为 `ST13_21` 的 downstream identity boundary input：

- `CurrentUserContext`：`user_id / team_id / role / status`。
- 开发态 auth 语义：`/api/v1/auth/login`、`/api/v1/auth/me`、`/api/v1/auth/logout=204`。
- 成员目录最小读取语义：`GET /api/v1/members`、`GET /api/v1/members/{member_id}`。
- 权限错误语义：`401 / 403 / 404`。

`ST13_21` 不在本任务中实现完整身份系统，不扩展 session、OAuth、JWT、团队管理或成员管理后台。

## 9. 与 ST13_20 的关系

`ST13_20` 承接服务端保存 / 数据库边界。`ST13_21` R0 minimal scope 只提供 API service skeleton，不提前实现：

- PostgreSQL schema。
- migration。
- ORM model。
- repository。
- 业务数据保存。
- 数据回退或审计 retention。

如果后续 API 字段需要保存、不保存、脱敏、归档或审计策略，必须回到 `ST13_20` 数据 contract 复核。

## 10. 与 ST13_24 的关系

`ST13_24` 承接测试 / 验收 / DoD。`ST13_21` 只在实施文档中提供 required validation，不创建测试文件。

当前已完成的验证事实：

- `validate-state`、`evaluate-state ST13_21`、`preflight-open-window ST13_21` 通过。
- `git diff --check` 通过。
- 非 sandbox 环境 uvicorn + curl smoke 通过，`GET /api/v1/health` 返回 HTTP 200 + `{ "status": "ok" }`。
- missing route 返回 minimal error envelope。
- `httpx>=0.27,<1.0` 已加入 `requirements.txt`，用于 FastAPI `TestClient` smoke。
- 非 sandbox 环境 `TestClient` smoke 通过；sandbox 内 TestClient 可能超时，记录为 runtime limitation。
- 未新增或修改 `tests/**`。

这些验证不等于 ST13_24 测试体系已完成，也不授权新增 `tests/**`。

## 11. 验收结果

当前 acceptance refresh 可从本文和实施文档中消费以下事实：

- goal 仍只覆盖 R0 minimal API service boundary。
- allowed / forbidden paths 未突破 packet。
- `/api/v1` router registration 已落地。
- `GET /api/v1/health` 已验证。
- minimal error envelope 已落地。
- minimal config boundary 已落地，且不读取外部服务配置。
- future route placeholders 仅为未注册常量。
- M02 关系仍为 downstream input / placeholder。
- 完整 API contract、DB、LLM、RAG、Redis、PostgreSQL、MinIO、业务 API 均未实现。
- `tests/**` 与 `apps/web/**` 未修改。

## 12. 当前 state 与后续收口说明

`ST13_21` implementation 已完成并通过 acceptance refresh，但 official `DOC_STATE.yaml` 尚未在本窗口写入 accepted / done / implementation result。当前事实为：

- official `DOC_STATE.yaml` 已记录 `implementation_doc_state=active_working_doc`、`maturity=L5`、`readiness=downstream_ready`、`formal_window_status=open`、`implementation_approval_status=approved`。
- `evaluate-state` / `preflight-open-window` 派生 `implementation_ready=true`、`can_generate_implementation_packet=true`。
- packet 已生成并提交：`89d82cf gov: generate ST13_21 implementation packet`。
- implementation 已提交：`b9d7fd3 feat(ST13_21): add minimal API service boundary`。
- TestClient 依赖已提交：`1f65274 test(ST13_21): add httpx for FastAPI TestClient smoke`。
- 本窗口不写 official state，不修改 packet，不继续 implementation。

## 13. R1 API 契约冻结范围

本节记录 `R1-W02-ST13_21-API-CONTRACT-FREEZE` 的 docs-only contract freeze 结论。它只冻结 R1 API contract 讨论范围，为 `ST13_20` data / schema / migration readiness 提供稳定输入；不修改 official state，不生成 packet，不打开 formal window，不授权业务代码、测试代码、schema、migration 或依赖变更。

### 13.1 R1 API 领域边界

R1 API contract 覆盖以下 domain boundary：

| Domain | R1 API 边界 | ST13_20 是否消费 |
| --- | --- | --- |
| Identity / Auth context | 统一表达用户、角色、workspace / tenant、资源可见性和最小权限结果 | 是，作为 owner、visibility、audit 和 permission snapshot 输入 |
| Job / Resume | 支持创建、读取、更新、归档、历史快照引用和启动面试时的引用 | 是，作为 `Job` / `Resume` schema、版本和归档策略输入 |
| Knowledge / RAG | 支持资料上传状态、切块 / 索引状态、检索请求、引用和证据缺口 | 是，作为 `KnowledgeDocument`、`KnowledgeChunk`、`RetrievalQuery`、`RetrievalResult`、`Citation`、`Evidence` 输入 |
| Interview | 支持启动、恢复、提交回答、结束、历史列表和详情读取 | 是，作为 `InterviewSession`、`InterviewTurn`、`InterviewAnswer` 输入 |
| Score | 支持 `0-100` 总分、多维评分、题级反馈和低置信度提示 | 是，作为 `ScoreReport`、`ScoreDimension`、`QuestionReviewItem` 输入 |
| Review | 支持模拟面试复盘摘要、证据、建议和降级说明 | 是，作为 `MockInterviewReview`、`FeedbackSummary` 输入 |
| Export | 支持 Markdown 复制 / 下载请求、导出快照和失败状态 | 是，作为 `ExportSnapshot`、`ExportRecord` 输入 |
| History | 支持历史记录列表、筛选、恢复入口和复盘入口 | 是，作为可回看、可恢复和索引字段输入 |

R1 不冻结完整管理员后台、团队共享知识库、高级检索质量平台、完整训练闭环、批量导出或资产归档实现。

### 13.2 接口动作清单

R1 API contract 以 action 级语义冻结，不在本窗口创建 endpoint 或 OpenAPI 文件。后续 endpoint 命名可在 implementation packet 中细化，但语义边界不得越过下表：

| Action group | R1 actions | R2 / excluded actions |
| --- | --- | --- |
| Auth context | `get current user context`、`check resource visibility`、`return permission denied / resource not visible` | OAuth、JWT rotation、企业级 RBAC 管理 |
| Job / Resume | create / read / update / archive / list active snapshots | 批量导入、复杂版本对比 |
| Knowledge / RAG | upload metadata、index status、search context、return citations / evidence gaps | 检索质量平台、复杂团队共享知识库 |
| Interview | start / restore / submit answer / finish / read detail / list history | 多模式高阶面试、实时语音视频 |
| Score / Review | generate or read score、read dimensions、read review、read question-level feedback | 训练闭环自动调度 |
| Export | create markdown export snapshot、read export status、retry failed export | PDF、批量导出、外部分享权限 |

### 13.3 请求契约

R1 request contract 至少需要稳定以下字段族，供 `ST13_20` 判断保存、不保存、脱敏、索引和审计策略：

| 字段族 | 必须表达 | ST13_20 消费用途 |
| --- | --- | --- |
| Actor context | `user_id`、`role`、`workspace_id` / `tenant_id` 候选、request source | owner、权限过滤、审计入口 |
| Resource identity | `job_id`、`resume_id`、`knowledge_document_id`、`interview_session_id`、`turn_id`、`score_report_id`、`review_id`、`export_id` | 主键 / 外键 / 历史引用候选 |
| Snapshot / version | `source_version`、`schema_version`、`content_version`、`prompt_version` 候选 | migration、回放、导出重现 |
| Operation intent | create、read、update、archive、restore、generate、retry | audit event、状态机和幂等策略 |
| RAG query context | query text 或脱敏摘要、topK、scope、selected materials、retrieval mode 候选 | `RetrievalQuery` 和 evidence 追踪 |
| LLM / generation context | generation purpose、provider alias、model alias、input snapshot reference、低置信度标记 | 脱敏 LLM 记录和失败排查 |

R1 request contract 暂不冻结真实 provider key、完整 prompt 原文、embedding 向量、数据库连接、对象存储路径或 migration 细节。

### 13.4 响应契约

R1 response contract 必须保持业务结果、状态、证据和错误语义可追踪：

| Response family | 必须字段 | 说明 |
| --- | --- | --- |
| Resource response | `id`、`type`、`status`、`created_at`、`updated_at`、`version` 候选 | 字段名可在 packet 中最终确认，但语义必须稳定 |
| Permission-aware response | `visibility`、`owner_ref` / `workspace_ref`、`permission_result` 候选 | 不暴露不该可见的资源；404 可用于隐藏存在性 |
| Async response | `operation_id`、`operation_status`、`retryable`、`last_error` 候选 | 支撑索引、评分、复盘、导出等异步链路 |
| Evidence response | `citations`、`evidence_items`、`evidence_gap`、`confidence` 候选 | RAG 失败时仍返回可解释缺口 |
| Review / score response | `score_total`、`dimensions`、`question_feedback`、`recommendations`、`low_confidence_reason` 候选 | 支撑 0-100 多维评分和复盘可信度 |
| Export response | `export_snapshot_id`、`format`、`content_version`、`status`、`failure_reason` 候选 | 一期只覆盖 Markdown 复制 / 下载 |

### 13.5 错误信封

R1 error envelope 在 R0 最小 `error.code` / `error.message` 基础上扩展为可追踪、可降级、可审计的 contract。后续实现可分阶段落地，但语义必须固定：

| 字段 | R1 contract |
| --- | --- |
| `error.code` | 稳定机器可读错误码 |
| `error.message` | 面向调用方的简短说明 |
| `error.reason` | 业务 reason，例如 `permission_denied`、`resource_not_visible`、`archived_resource`、`validation_failed`、`rag_unavailable`、`llm_failed`、`export_failed` |
| `error.request_id` | 请求追踪 ID；用于日志和审计关联 |
| `error.resource_ref` | 可选脱敏资源引用；不得泄露不可见资源 |
| `error.retryable` | 是否建议重试 |
| `error.degraded` | 是否已进入降级路径 |
| `error.details` | 仅允许安全、脱敏、可展示的细节 |

必须标准化的错误场景包括：未登录、无权限、资源不可见、资源已归档、输入校验失败、状态冲突、RAG 无结果、RAG 索引未完成、LLM 调用失败、解析低置信度、评分未生成、复盘生成失败、导出失败、历史记录不可恢复。

### 13.6 身份、权限、租户与工作区上下文

R1 API contract 必须把权限语义作为显式 API contract，而不是隐含在实现中：

- 每个读写类 action 都必须携带或解析 actor context。
- `workspace_id` / `tenant_id` 在 R1 中作为隔离字段候选进入 API 语义；是否最终命名为 workspace、tenant 或 account scope 由后续 M02 / ST13_20 readiness 确认。
- list / detail / export / restore 必须区分 `permission_denied` 与 `resource_not_visible`。
- 历史记录、评分、复盘、导出和 RAG evidence 必须继承来源对象的 resource visibility。
- 管理员或内容维护者能力只限一期最小边界；企业级权限矩阵、复杂组织管理和团队共享知识库不进入 R1。

### 13.7 异步、降级与回退语义

R1 需要统一异步和降级语义：

| 场景 | R1 API 语义 |
| --- | --- |
| RAG indexing | 返回 `pending` / `running` / `failed` / `completed` 类状态和可展示失败原因 |
| RAG no result | 主链路可继续；response 标注 `evidence_gap` |
| LLM failed | 返回可重试状态或降级说明；不得丢失已保存回答 |
| Parsing low confidence | 返回低置信度提示，等待用户校对或人工确认 |
| Score / review pending | 历史详情可展示未生成或失败状态 |
| Export failed | 保留复盘内容和导出请求记录，允许 retry |
| Restore failed | 明确无法恢复的 session / turn / snapshot 原因 |

这些语义是 contract freeze，不代表本窗口实现 async worker、queue、retry service、provider adapter 或持久化层。

### 13.8 ST13_20 必须消费的可追溯字段

`ST13_20` 后续 data / schema / migration readiness 至少需要消费以下字段族：

| Field group | 示例语义 | 保存判断 |
| --- | --- | --- |
| `request_id` / `operation_id` | 请求与异步操作追踪 | 应进入 audit / operation log 候选 |
| actor / workspace scope | `user_id`、role、workspace / tenant 候选 | 应进入权限过滤和审计候选 |
| resource refs | job、resume、document、session、turn、score、review、export refs | 应进入关系和索引候选 |
| source snapshot refs | job / resume / answer / RAG / prompt / model version refs | 应进入历史重放和导出快照候选 |
| status fields | pending、running、failed、completed、archived、deleted candidate | 应进入状态机和查询候选 |
| evidence refs | citation、evidence item、evidence gap、confidence | 应进入 RAG / score / review 追溯候选 |
| error refs | reason、retryable、degraded、failure source | 应进入失败排查和降级记录候选 |
| export refs | export snapshot、format、content version、permission context | 应进入导出追溯候选 |

暂时只作为 contract 占位、不应直接落库的字段包括：完整 prompt 原文、完整 LLM response 原文、embedding 向量、provider secret、对象存储真实路径、完整权限矩阵、企业级 tenant 配置、PDF 模板配置、训练任务调度参数。

### 13.9 RAG 证据与引用契约

R1 RAG contract 只冻结最小可用 evidence 语义：

- request 需要表达检索 scope、query 或脱敏摘要、材料选择、topK 候选。
- response 需要表达 citation 列表、evidence item、source reference、confidence / low confidence、evidence gap。
- RAG evidence 可以进入评分和复盘证据，但不直接决定分数。
- RAG 无结果或索引失败时，面试和复盘主链路应可继续，并明确标注证据缺口。
- 不在 R1 冻结高级检索质量评估、复杂排序算法、embedding provider、向量存储结构或团队共享知识库治理。

### 13.10 评分、复盘、导出与历史契约

评分、复盘、导出和历史回看共享以下 API 语义：

- score response 必须能表达 `0-100` 总分、多维评分、题级反馈、证据引用、低置信度和改进建议。
- review response 必须能表达整场判断、岗位匹配、关键缺口、证据、建议和降级说明。
- export action 必须引用来源 review / score / interview snapshot，并表达 Markdown content version、权限上下文、脱敏状态和失败原因。
- history list / detail 必须能恢复到 session、turn、answer、score、review、export 的当前状态或失败状态。
- 所有历史回看必须遵循 resource visibility，不得通过导出或 citation 泄露不可见资源。

训练任务、训练抽屉、资产归档、真实面试复盘增强和 Markdown 导出增强属于 R2 或后续增强；R1 只保留与复盘可信度和历史回看有关的最小 contract。

### 13.11 R0 / R1 / R2 范围切分

| Iteration | ST13_21 API contract 边界 |
| --- | --- |
| R0 | 最小 `/api/v1` skeleton、health、minimal error envelope、minimal config boundary、future placeholder |
| R1 | API contract 收敛、权限上下文、业务 domain action list、request / response / error / async / degradation / traceability / RAG evidence / score-review-export-history 语义 |
| R2 | 训练闭环、资产归档、真实面试复盘增强、批量或增强导出、复杂组织和高级运营后台 |

### 13.12 仍禁止进入实现的内容

本 R1 contract freeze 后仍禁止：

- 修改 `apps/**`、`tests/**`、`docs/governance/**` 或 `DOC_STATE.yaml`。
- 生成或修改 implementation packet。
- 打开 formal window 或修改 official state。
- 创建业务 endpoint、schema 文件、migration、ORM、repository、worker、queue、provider adapter 或测试文件。
- 新增依赖或环境变量。
- 把本文字段表直接当作数据库 schema、OpenAPI 已冻结文件或 implementation-ready 状态。

## 14. R1 前端消费边界

本节记录 `R1-W02a-ST13_21-FRONTEND-UI-CONSUMER-CONTRACT-PATCH` 的 docs-only contract patch。它只冻结前端如何消费 R1 API contract，不创建 endpoint，不设计具体 UI 组件，不实现页面，不进入 `ST13_20` schema / migration 细节。

### 14.1 R1 用户可见界面范围

R1 前端消费边界覆盖以下用户可见 surface：

| UI surface | R1 必须可感知的 API 语义 | 不在本窗口处理 |
| --- | --- | --- |
| 工作台概览 | 近期模拟、待处理复盘、知识库 / RAG 状态、失败或降级提示 | 不设计 dashboard 组件 |
| 模拟记录列表 | session 状态、岗位 / 简历快照、评分 / 复盘入口、恢复入口、空状态 | 不实现列表页面 |
| 发起模拟入口 | 可选岗位、简历、参考材料、权限可见性和缺失材料提示 | 不实现表单 |
| 面试台 | 当前问题、回答提交、RAG citation、evidence gap、LLM / RAG 降级提示 | 不实现交互页面 |
| 评分 / 复盘详情 | `0-100` 总分、多维评分、题级反馈、证据、建议、低置信度 | 不实现可视化组件 |
| 知识库入口 | 上传 / 索引 / 检索状态、RAG 无结果或索引失败提示 | 不实现上传流程 |
| Markdown 导出入口 | export status、失败原因、重试语义、导出快照版本 | 不实现下载逻辑 |
| 账号 / 权限提示 | 未登录、无权限、资源不可见、归档资源提示 | 不实现完整权限后台 |

### 14.2 前端直接消费的 API action

R1 前端可以直接消费以下 action 语义，具体 endpoint 命名仍留给后续 implementation packet：

| Action group | 前端直接消费目的 |
| --- | --- |
| current user / permission context | 决定入口可见性、权限提示和资源不可见文案 |
| job / resume list and detail | 发起模拟、历史回看和快照说明 |
| knowledge / RAG status and search context | 展示资料可用性、索引状态、引用和证据缺口 |
| interview start / restore / submit / finish / detail / history | 驱动主链路、恢复和历史回看 |
| score / review read or generate status | 展示评分、复盘、pending / failed 状态和建议 |
| export create / status / retry | 展示 Markdown 复制 / 下载入口、失败原因和重试 |

R1 前端不得假设 placeholder 已等于可用 endpoint；没有 packet 和实现前，只能把这些 action 作为消费契约。

### 14.3 前端展示字段与后端追踪字段

| 字段类型 | 前端是否展示 | 示例 |
| --- | --- | --- |
| 资源摘要字段 | 展示 | title、status、updated_at、snapshot label、visibility label |
| 评分与复盘字段 | 展示 | score_total、dimensions、question_feedback、recommendations、low_confidence_reason |
| RAG 证据字段 | 展示 | citations、evidence_items、evidence_gap、confidence label |
| 异步状态字段 | 展示 | pending、running、failed、completed、retryable、failure_reason |
| 权限与可见性字段 | 展示安全摘要 | permission_result、resource_not_visible、archived_resource |
| traceability 字段 | 默认不展示 | request_id、operation_id、audit event id、source snapshot refs、provider alias、model alias |
| debug / audit 字段 | 不直接展示 | token / cost 候选、internal error details、audit retention、migration version |

前端可在错误排查文案中展示脱敏 `request_id`，但不得展示 provider secret、完整 prompt、完整 LLM response、embedding、对象存储真实路径或不可见资源标识。

### 14.4 RAG citation / evidence / evidence gap 前端呈现语义

R1 前端需要能感知以下 RAG contract：

- citation 应以可读来源、片段摘要、来源类型和置信度提示呈现。
- evidence item 可以进入面试台参考材料、评分理由和复盘证据。
- evidence gap 必须明确提示“缺少可引用证据”或等价语义，不能静默隐藏。
- RAG 无结果、索引未完成或索引失败时，面试和复盘主链路仍可继续，但前端必须展示降级状态。
- 前端不得把 RAG citation 展示为评分唯一依据，也不得暴露用户无权限访问的 source。

### 14.5 评分、复盘、导出与历史回看的前端影响

| 业务面 | 前端 contract 影响 |
| --- | --- |
| Score | 页面需要展示 `0-100` 总分、多维评分、题级反馈、证据引用和低置信度提示 |
| Review | 页面需要展示整场判断、岗位匹配、关键缺口、建议、RAG 证据和降级说明 |
| Export | 页面需要展示 Markdown 导出入口、export status、content version、失败原因和 retryable 状态 |
| History | 页面需要展示 session 状态、可恢复入口、复盘入口、失败状态和资源可见性 |

这些字段只冻结前端消费语义，不定义页面布局、组件树、路由文件或状态管理实现。

### 14.6 错误、降级、重试、等待与空状态

R1 前端必须能从 API contract 区分并展示以下状态：

| 状态 | 前端语义 |
| --- | --- |
| `permission_denied` | 显示无权限，保留安全边界，不提示资源真实存在性 |
| `resource_not_visible` | 显示资源不可见或不存在的安全文案 |
| `archived_resource` | 显示已归档，不作为默认输入 |
| `validation_failed` | 显示可修正输入项或通用校验失败 |
| `rag_unavailable` / RAG no result | 显示证据缺口和可继续路径 |
| `llm_failed` | 显示生成失败、重试或降级路径 |
| `pending` / `running` | 显示等待状态，避免误判为空结果 |
| `retryable=true` | 显示可重试入口或建议 |
| empty history / empty knowledge | 显示发起入口、准备项或补充资料提示 |

错误细节必须遵守脱敏和权限约束；前端不展示 internal stack、完整 prompt、provider secret 或不可见资源 ID。

### 14.7 R1 必做、R1 可选与 R2 延后 UI 边界

| 层级 | UI contract 边界 |
| --- | --- |
| R1 必做 | 历史记录、发起模拟、面试台、评分 / 复盘详情、RAG citation / evidence gap、Markdown 导出入口、权限 / 降级 / 空状态可感知 |
| R1 可选 | 工作台概览中的轻量状态聚合、知识库状态摘要、导出失败 retry 提示增强 |
| R2 延后 | 训练抽屉完整闭环、训练任务入列、资产归档、真实面试复盘增强、批量导出、复杂组织后台、团队共享知识库治理 |

本窗口不提前把 R2 训练闭环、资产归档、复杂组织后台或高级运营能力纳入 R1 UI 必做范围。

### 14.8 仍禁止进入前端实现

本节只冻结 UI consumption boundary，仍禁止：

- 修改 `apps/**` 或创建页面、组件、hook、store、route、样式文件。
- 修改 `tests/**` 或新增前端测试。
- 创建 endpoint、OpenAPI 文件、mock server 或 schema。
- 修改 `docs/governance/**`、`DOC_STATE.yaml`、packet 或 formal window。
- 把本节写成前端 implementation-ready 或 UI DoD 已完成。

## 15. 后续动作

建议下一窗口进入 `ST13_20` R1 data / schema / migration readiness。该窗口应消费本节冻结的 domain、request / response、错误、权限、异步、降级、traceability、RAG evidence、score / review / export / history contract，但仍不得直接创建 schema、migration、ORM 或业务代码，除非另有 formal window、implementation packet 和用户授权。