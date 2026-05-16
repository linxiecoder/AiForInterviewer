---
title: API_SPEC
type: design
status: draft-f4-api-contracts
owner: API / Backend 架构
source_task: AIFI-API-001
permalink: ai-for-interviewer/docs/02-design/api-spec
---

# API_SPEC

## 1. 文档状态与治理边界

- 本文件是 F4 技术设计下的 API 契约子文档，承接 `AIFI-API-001`，并作为 F5 后端实现、F6 前端接入和 F7 API contract tests 的前置硬门槛。
- 本版本回写 `AR-F4-FULL-002`：将原早期占位草案补齐为可交接 API contract。F5 不得绕过本文件自行发明 endpoint、request / response、错误语义、owner enforcement、异步任务、幂等、rate limit 或 copy boundary。
- 本文件只定义 API contract、状态语义和前后端 / 测试交接边界，不实现代码，不定义 ORM、DDL、migration、索引、物理数据库表或运行时队列。
- `PROMPT_SPEC.md` 不能替代 API contract；`P-*` 是 AI Task Contract ID，不是 endpoint、schema、队列任务名或数据库表名。
- `DATA_MODEL.md` 不能替代 API contract；逻辑对象、引用对象和状态域必须通过本文件映射为可调用、可测试的 HTTP API 语义。
- API 不得暴露 `system prompt`、Prompt 模板、provider request / response payload、completion 原文、模型调用参数、密钥、隐藏评分规则或内部评分校准细节。
- API 不提供 PDF、Markdown 文件、Word、docx、批量文件下载或文件导出 endpoint；报告只提供读取和 copy content。
- AI 输出默认只能进入 candidate、draft、suggestion、validation result、trace 或 low confidence 状态；不得静默成为正式事实。
- 正式资产、薄弱项、训练建议、报告复盘结论和训练回流状态必须有用户确认、用户编辑、显式业务动作或明确状态转换记录。
- 本文件不关闭 `AR-F4-FULL-001`、`AR-F4-FULL-003`、Medium 或 Low findings；不标记 `F4_FULL_DESIGN_ACCEPTANCE.md` 为 Accepted；不创建 final acceptance approval。
- 本文件不得把 `archive/**` 作为当前执行依据；历史内容只有迁入 active docs 后才能影响本 API 契约。

## 2. 输入来源与非目标

### 2.1 输入来源

| 来源 | 本文使用方式 |
|---|---|
| `docs/02-design/TECH_DESIGN.md` | API 边界层、应用编排层、LLM 边界、模块划分和 F5/F6/F7 交接原则 |
| `docs/02-design/DATA_MODEL.md` | 逻辑对象、引用对象、状态域、版本 / 快照、candidate / suggestion / confirmation、AI output handoff 和审计对象 |
| `docs/02-design/SECURITY_PRIVACY.md` | 登录态、owner enforcement、隐私裁剪、复制边界、source unavailable、日志脱敏和错误安全表达 |
| `docs/02-design/PROMPT_SPEC.md` | `P-*` AI Task Contract ID、validation、low confidence、failure signal、trace / evidence 和 persistence handoff |
| `docs/02-design/prompt-contracts/*.md` | 业务 AI task 的相关 prompt contract、候选 / 建议 / 用户确认边界和测试策略 |
| `docs/03-delivery/DELIVERY_PLAN.md` | F4 / F5 / F7 阶段交接、无文件导出和 F7 可测试性要求 |
| `docs/03-delivery/BACKLOG.md` | `AIFI-API-001`、`AIFI-BE-001`、`AIFI-FE-001`、`AIFI-QA-001` 的范围和依赖 |

### 2.2 非目标

本文不做以下事项：

- 不定义登录注册完整产品方案、OAuth / SSO、企业级多租户、复杂 ACL 或组织权限树。
- 不定义物理数据库 schema、ORM model、DDL、索引、外键、migration 或缓存方案。
- 不定义 Prompt 文案、模型供应商、模型参数、embedding 模型、向量数据库或联网搜索服务。
- 不定义评分公式、权重、阈值、校准算法、通过概率或真实面试结果预测。
- 不提供文件上传解析、PDF parser、OCR、docx 解析、远程 URL 抓取或对象存储解析链路。
- 不提供文件导出、下载、批量导出、report file、snapshot file、filename hint 或 export artifact。
- 不把项目经历提升为独立一级业务对象；项目经历只作为 `ResumeModule(type=project_experience)` 的子资源被 API 暴露。
- 不把 candidate / suggestion / AI task result 当作正式业务对象。

## 3. 全局 API 约定

### 3.1 Base path 与 versioning

| 项 | 约定 |
|---|---|
| Base path | `/api/v1` |
| API version | 使用 path version；F5/F6/F7 的 contract tests 默认只针对 `/api/v1` |
| Breaking change | 必须新建 `/api/v2` 或在 F4/F5 变更评审中显式登记；不得静默改变 `/api/v1` 字段语义 |
| Resource naming | 使用复数资源名，例如 `/resumes`、`/jobs`、`/reports`；项目经历只出现在 `/resumes/{resume_id}/modules/project-experiences` |
| Identifier | path id 只表达资源引用，不表达 owner；服务端必须从 session / actor 推导 owner |

### 3.2 Auth / session assumption

- 所有业务 API 默认要求已登录 session；未登录只能访问登录入口、公开静态资源和不含个人数据的健康检查。
- F5 可以选择 cookie session 或短期 bearer token，但业务 API contract 只依赖“服务端可解析 actor / role scope / session state”的抽象。
- 如果使用 cookie，必须满足 `HttpOnly`、`SameSite=Lax` 或更严格策略；非本地开发必须 `Secure`。
- 请求体、query 和 header 中的 `owner_id` 不得被当作授权依据；如出现，只能作为服务端校验后返回的只读字段或调试拒绝原因。
- 账号禁用、session 过期、登出失效和权限失败必须返回标准错误 envelope，并产生最小 `AuditEvent`。

### 3.3 Owner boundary

- 列表查询必须默认只返回当前 actor 可访问的 owner scope 数据。
- 详情、更新、删除、复制、生成、RAG、LLM task、确认和回流动作必须在 API 边界层先校验登录态，再在应用编排层和持久化读取层校验 `OwnerRef`。
- 复合资源必须校验所有输入资源 owner 一致，例如 job-resume binding、job match、session start、report generation、review generation 和 training suggestion generation。
- 对可能泄露资源存在性的详情接口，owner mismatch 可以返回 `not_found_or_inaccessible`；对已知目标的动作接口，返回 `permission_denied` 或 `owner_mismatch`。
- F7 必须覆盖用户 A 无法读取、生成、复制、确认、删除用户 B 的资源。

### 3.4 Response envelope

所有成功或业务可处理响应使用统一 envelope：

| 字段 | 必填 | 语义 |
|---|---|---|
| `request_id` | 是 | 本次 API 请求追踪标识；可来自 `X-Request-Id` 或服务端生成 |
| `trace_id` | 是 | 服务端链路追踪标识；不得暴露 provider payload |
| `status` | 是 | API 业务状态，例如 `success`、`partial`、`low_confidence`、`accepted`、`queued`、`running`、`validation_failed`、`generation_failed` |
| `resource_type` | 是 | 返回资源类别，例如 `resume`、`job`、`ai_task`、`candidate`、`suggestion`、`report_copy_content` |
| `resource_ref` | 否 | 单个资源引用；列表、聚合或空态可为空 |
| `data` | 否 | 可展示或可消费的结构化结果；不得包含原始 Prompt、completion 或 provider payload |
| `meta` | 否 | pagination、sorting、filtering、rate limit、version、source availability 或 conflict 信息 |
| `candidate_refs` | 否 | 本次响应涉及的候选引用 |
| `suggestion_refs` | 否 | 本次响应涉及的建议引用 |
| `confirmation_required` | 否 | 是否需要用户确认后才能写入正式对象 |
| `ai_task_id` | 否 | 异步任务 ID；只表示 API task，不等于 prompt contract ID |
| `validation_result_ref` | 否 | 输出校验结果引用 |
| `low_confidence_flags` | 否 | 低置信度、冲突、不完整或来源不可用标记 |
| `source_availability` | 否 | `source_available`、`source_archived`、`source_deleted`、`source_disabled`、`source_unavailable` |
| `evidence_refs` | 否 | 支撑关键结论的证据引用或可展示摘要引用 |
| `trace_refs` | 否 | 检索、上下文装配、模型调用、校验、持久化交接和审计过程引用 |
| `next_actions` | 否 | 可执行动作，例如 `confirm`、`edit`、`skip`、`retry`、`manual_review`；不等于自动写入动作 |

Envelope 规则：

- HTTP status 只表达传输和协议层结果；业务状态必须在 `status` 中表达。
- `data` 只能包含结构化业务结果、低置信度结果、部分可用结果或 copy content；不得直接返回原始 LLM 输出。
- `confirmation_required=true` 时，API 不得把 candidate 或 suggestion 静默写成正式对象。
- `low_confidence` 可以是 200 / 202 下的业务状态，不应被前端当作失败吞掉。
- `source_unavailable` 在历史结果读取时可以作为可展示状态返回；在新生成任务创建时通常为 409 / 422 错误。

### 3.5 Error envelope

所有错误响应使用统一 error envelope：

| 字段 | 必填 | 语义 |
|---|---|---|
| `request_id` | 是 | 本次请求追踪标识 |
| `trace_id` | 是 | 服务端错误追踪标识 |
| `error.code` | 是 | 稳定错误码，见 §4 |
| `error.message` | 是 | 用户可理解摘要，不包含敏感正文 |
| `error.details` | 否 | 字段级校验、冲突资源、source availability、retry hint；不得包含原文 |
| `error.retryable` | 是 | 是否允许按当前请求重试 |
| `error.user_action` | 否 | 建议用户动作，例如 `login`、`fix_input`、`retry_later`、`manual_review`、`choose_available_source` |
| `error.audit_event_ref` | 否 | 关键安全失败或复制失败的审计引用 |

错误 envelope 不得记录或返回 request / response body、简历正文、岗位全文、报告正文、复盘正文、Prompt、completion、provider payload、token、cookie、API key 或环境变量。

### 3.6 Pagination / sorting / filtering

| 机制 | 约定 |
|---|---|
| Pagination | 列表默认 cursor pagination；query 使用 `cursor`、`limit`；`limit` 默认 20，最大 100 |
| Pagination meta | `meta.next_cursor`、`meta.has_more`、`meta.limit`、`meta.total_count_available`；默认不要求精确总数 |
| Sorting | query 使用 `sort`，只允许 endpoint 白名单字段；默认 `updated_at:desc` 或业务定义默认 |
| Filtering | query 使用明确字段，例如 `status`、`mode`、`job_id`、`resume_id`、`source_type`、`created_after`；所有过滤都必须叠加 owner scope |
| Search | 简单文本搜索仅用于 owner scope 内的标题、摘要或可展示字段；不得默认搜索正文或 Prompt / trace payload |

F7 必须覆盖分页边界、非法 sort 字段、非法 filter、跨 owner filter id 和空结果。

### 3.7 Idempotency

| 项 | 约定 |
|---|---|
| Header | `Idempotency-Key` |
| Required for | 所有创建、确认、复制审计、生成任务创建、retry、cancel、可能重复提交的 mutation |
| Scope | `actor_id + method + path + idempotency_key + request_body_hash` |
| TTL | F5 默认不少于 24 小时；具体存储实现由 F5 冻结 |
| Duplicate same body | 返回第一次请求的同等 response 或当前任务状态，不重复创建资源 |
| Same key different body | 返回 `idempotency_conflict`，HTTP 409 |
| Async task | task create 必须保存 idempotency key；重复点击不得重复写 candidate、suggestion、report、review、weakness 或 training recommendation |

### 3.8 Rate limit

- F5 必须按 `actor_id`、IP、endpoint group 和 LLM task type 建立 MVP 级 rate limit。
- LLM 生成类 endpoint 必须比轻量 CRUD 更严格；登录、简历保存、RAG 检索、报告生成、复盘生成、训练建议生成和评分生成必须有测试覆盖。
- Rate limit 响应使用 HTTP 429，错误码 `rate_limited`，并返回 `Retry-After`、`RateLimit-Limit`、`RateLimit-Remaining`、`RateLimit-Reset` 或等价 meta。
- Rate limit 不得通过扩大上下文、降级为未审计生成或绕过 owner 校验来处理。

### 3.9 Trace id / request id / async task id

- 客户端可传 `X-Request-Id`；服务端可拒绝异常长度或非法字符，并生成规范化 `request_id`。
- 每个响应都必须返回 `request_id` 和 `trace_id`。
- 异步任务创建返回 `ai_task_id`；`ai_task_id` 只用于 API task status / result / retry / cancel，不暴露 provider task、Prompt ID 或物理队列 ID。
- `trace_refs` 可以指向 RAG、LLM、validation、audit 等过程引用，但不能让前端读取 Prompt、completion 或 provider payload。

## 4. 标准状态与错误语义

### 4.1 通用 HTTP 到业务错误映射

| HTTP | `error.code` / `status` | 语义 |
|---:|---|---|
| 200 | `success` / `partial` / `low_confidence` | 同步读取或同步 mutation 成功；可带低置信度或部分可用状态 |
| 201 | `success` | 同步创建成功 |
| 202 | `accepted` / `queued` | 异步任务已创建或已复用既有幂等任务 |
| 400 | `invalid_request` | 请求格式错误、非法 query 或非法 path 参数 |
| 401 | `unauthenticated` | 未登录、session 过期或 token 无效 |
| 403 | `permission_denied` / `owner_mismatch` | 已登录但无权限，或资源 owner / scope 不匹配 |
| 404 | `not_found_or_inaccessible` | 资源不存在，或为避免泄露存在性而统一不可访问 |
| 409 | `stale_version_conflict` / `idempotency_conflict` / `source_unavailable` | 版本冲突、幂等冲突或来源状态阻断新生成 |
| 422 | `validation_failed` | 字段、业务前置条件、source availability 或 AI output validation 不通过 |
| 429 | `rate_limited` | 限流 |
| 500 | `internal_error` | 未分类服务端错误；不得暴露内部堆栈 |
| 502 | `provider_unavailable` | LLM / RAG / 外部依赖不可用 |
| 504 | `task_timeout` / `generation_failed` | 生成任务超时或不可恢复失败 |

### 4.2 稳定错误码

| 错误码 | 触发条件 | F7 断言 |
|---|---|---|
| `unauthenticated` | 未登录访问业务 API | `auth.unauthenticated_denied` |
| `permission_denied` | 已登录但角色或 scope 不允许动作 | `auth.permission_denied` |
| `owner_mismatch` | 请求目标资源不属于当前 actor 或复合资源 owner 不一致 | `auth.cross_user_denied` |
| `not_found_or_inaccessible` | 资源不存在或不可暴露存在性 | `auth.not_found_or_inaccessible` |
| `validation_failed` | 请求字段缺失、格式错误、业务前置条件不满足或输出 schema 无效 | `validation.failed` |
| `stale_version_conflict` | `If-Match`、`base_version_ref`、`resume_version_id`、`job_version_id` 或 `score_rule_version_id` 过期 | `conflict.stale_version` |
| `idempotency_required` | mutation 缺少必需 `Idempotency-Key` | `idempotency.required` |
| `idempotency_conflict` | 同一 key 携带不同 request body | `idempotency.conflict` |
| `source_unavailable` | 来源删除、禁用、归档、不可访问或缺少生成时快照 | `source.unavailable` |
| `low_confidence` | 资料不足、证据不足、证据冲突或模型判断不稳定 | `generation.low_confidence_visible` |
| `generation_failed` | LLM / RAG / scoring / report / review / training 生成失败 | `generation.failed_visible` |
| `provider_unavailable` | provider timeout、限流或暂不可用 | `generation.provider_unavailable` |
| `task_timeout` | 异步任务超过 timeout | `async.timeout` |
| `task_cancelled` | 任务已取消，不再生成结果 | `async.cancelled` |
| `task_retry_not_allowed` | 非可重试失败、已成功任务或超过 retry 上限 | `async.retry_not_allowed` |
| `rate_limited` | 达到 actor / IP / endpoint / LLM task 限流 | `rate_limit.enforced` |
| `copy_boundary_violation` | copy content 试图包含无权限来源、Prompt、provider payload、隐藏评分规则或文件产物语义 | `copy.boundary` |
| `export_not_supported` | 命中任何 PDF / Markdown file / Word / docx / export / download 请求 | `export.no_endpoint` |

### 4.3 Source availability 与低置信度

- `source_available`：可在 owner / scope 校验后读取最小必要片段。
- `source_archived`：历史引用可展示摘要；默认不参与新生成。
- `source_deleted`：历史引用只展示来源状态；不得读取正文或进入新生成。
- `source_disabled`：因风险或维护禁用；不得进入新生成。
- `source_unavailable`：不可访问、缺少快照、无权限或无法读取；新生成通常失败或进入低置信度 / manual review。

低置信度不是普通成功态。API 必须在 `status`、`low_confidence_flags`、`source_availability`、`next_actions` 中表达影响范围和用户可操作路径。

## 5. 同步 / 异步任务边界

### 5.1 同步 API

以下能力可以同步完成：

- 轻量读取：列表、详情、版本读取、报告读取、copy content 读取、task status 读取。
- CRUD 和显式用户动作：简历 / 岗位保存、绑定 / 解绑、会话创建、回答保存、确认 / 编辑 / 跳过 / 拒绝 / 合并、训练任务显式启动。
- 复制审计：记录用户复制动作，不能生成文件。

同步 mutation 仍需 `Idempotency-Key`，并必须做 owner 校验、版本冲突校验和审计。

### 5.2 必须使用异步任务协议的 AI 生成类能力

以下能力必须明确使用异步任务协议，即使 F5 初版内部实现为快速同步执行，也必须对外返回 `ai_task_id` 和可查询状态：

- job match analysis。
- report generation。
- simulated interview review analysis。
- real interview review analysis。
- training suggestion generation。
- weakness extraction。
- AI scoring。
- question generation。
- feedback / diagnosis generation。
- asset candidate extraction 或 asset version suggestion generation。

### 5.3 Async task protocol

| Endpoint | 作用 |
|---|---|
| `POST /api/v1/ai-tasks` | 创建通用 AI task；domain endpoint 也可创建 task，但必须复用本协议 |
| `GET /api/v1/ai-tasks/{ai_task_id}` | 查询任务状态 |
| `GET /api/v1/ai-tasks/{ai_task_id}/result` | 查询任务结果或结果引用 |
| `POST /api/v1/ai-tasks/{ai_task_id}/retry` | 按 retry rule 重试失败或低置信度任务 |
| `POST /api/v1/ai-tasks/{ai_task_id}/cancel` | 在可取消阶段取消任务 |

Async task 字段：

| 字段 | 语义 |
|---|---|
| `ai_task_id` | API 任务 ID，不等于 provider task 或 Prompt contract ID |
| `task_type` | `job_match_analysis`、`report_generation`、`review_analysis`、`training_suggestion_generation`、`weakness_extraction`、`ai_scoring`、`question_generation`、`feedback_generation`、`asset_candidate_extraction` |
| `contract_ids` | 相关 `P-*` contract ID 列表 |
| `target_ref` | 目标业务对象或候选对象引用 |
| `input_refs` | `ResumeVersion`、`JobVersion`、`InterviewSession`、`Report`、`Review`、`Weakness`、`Asset` 等输入引用 |
| `status` | `queued`、`running`、`succeeded`、`partial`、`low_confidence`、`validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled` |
| `retry_count` | 已重试次数 |
| `retryable` | 是否可重试 |
| `timeout_at` | 任务超时时间 |
| `result_ref` | 成功或部分成功后的业务结果引用 |
| `candidate_refs` / `suggestion_refs` | 候选或建议引用 |
| `validation_result_ref` | 校验结果引用 |
| `low_confidence_flags` | 低置信度原因 |
| `trace_refs` / `evidence_refs` | 追踪和证据引用 |
| `user_visible_status` | 前端可展示状态摘要 |

Async 规则：

- 创建 AI task 必须要求 `Idempotency-Key`。
- 同一 actor、同一 endpoint、同一 request body、同一 idempotency key 的重复请求返回同一个 `ai_task_id`。
- task status 查询只允许 owner 读取；跨 owner 返回 `not_found_or_inaccessible` 或 `owner_mismatch`。
- `retry` 不得扩大上下文范围、不得默认启用互联网检索、不得记录原始 Prompt / completion / provider payload。
- 可重试条件：`provider_unavailable`、`task_timeout`、`generation_failed`、`validation_failed` 的可修复子类、`source_unavailable` 被用户修复后。
- 不可重试条件：`owner_mismatch`、`permission_denied`、`export_not_supported`、已成功且结果已确认写入正式对象的任务。
- 取消只允许 `queued` 或可中断 `running`；取消后不得产生新的 formal object。
- timeout 后必须返回 `task_timeout` 或 `generation_failed`，保留可用输入和部分结果引用。
- `low_confidence` 和 `partial` 结果可以读取，但不得被前端展示为高置信完成态。

## 6. 资源域与核心 endpoint contract

### 6.1 Endpoint contract 共同字段

每个 endpoint 至少遵守以下共同规则：

- `Method` 和 `Path` 必须稳定，除非走 versioning。
- `Request` 只列 API contract 必要字段，不等同最终 TypeScript / Pydantic 类型全集。
- `Response` 必须使用 §3.4 envelope。
- `Error cases` 必须从 §4 选择稳定错误码。
- `Permission / owner check` 必须说明 owner 校验位置。
- `Idempotency requirement` 必须说明是否必需。
- `Related data objects` 必须来自 `DATA_MODEL.md` 已登记对象或 API protocol 对象。
- `Related prompt contract` 只引用已登记 `P-*`；不适用时写 `N/A`。
- `Related F7 test assertion` 必须能转成 contract test。

### 6.2 Core endpoint matrix

| Method | Path | Purpose | Request / Query | Response | Error cases | Permission / owner check | Idempotency requirement | Related data objects | Related prompt contract | Related F7 test assertion |
|---|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/v1/resumes` | 查询当前用户简历列表 | `cursor`、`limit`、`status`、`sort` | `resume[]` + pagination meta | `unauthenticated`、`validation_failed` | 列表按 actor owner scope 过滤 | 不需要 | `Resume`、`ResumeVersion`、`OwnerRef` | N/A | `resumes.list.owner_scoped` |
| POST | `/api/v1/resumes` | 创建 Markdown 简历 | `title`、`markdown_text`、`target_direction`、`client_draft_id` | 201 `resume`、当前 `ResumeVersion` | `validation_failed`、`rate_limited`、`idempotency_required` | 服务端写入当前 actor owner；不得接受请求体 owner | 必需 | `Resume`、`ResumeVersion`、`ResumeModule`、`AuditEvent` | N/A | `resumes.create.success`、`resumes.create.validation_failed` |
| GET | `/api/v1/resumes/{resume_id}` | 读取简历详情和当前版本摘要 | path `resume_id` | `resume` + `current_version_ref` + modules summary | `not_found_or_inaccessible`、`owner_mismatch` | 校验 resume owner | 不需要 | `Resume`、`ResumeVersion`、`ResumeModule` | N/A | `resumes.get.cross_user_denied` |
| PATCH | `/api/v1/resumes/{resume_id}` | 编辑简历并产生新版本 | `markdown_text`、`base_version_ref`、`title`、`If-Match` | `resume` + new `ResumeVersion` | `validation_failed`、`stale_version_conflict`、`owner_mismatch` | 校验 resume owner；版本必须属于同 owner | 必需 | `Resume`、`ResumeVersion`、`AuditEvent` | N/A | `resumes.update.stale_version_conflict` |
| DELETE | `/api/v1/resumes/{resume_id}` | soft delete 简历并阻断 active 读取 | `delete_reason` | `status=success` + `source_deleted` impact summary | `owner_mismatch`、`stale_version_conflict` | 校验 resume owner；关联 active 生成阻断 | 必需 | `Resume`、`ResumeVersion`、`SourceRef`、`AuditEvent` | N/A | `resumes.delete.source_unavailable_for_new_generation` |
| GET | `/api/v1/resumes/{resume_id}/versions/{version_id}` | 读取历史简历版本摘要 | path ids | `resume_version` + source availability | `not_found_or_inaccessible`、`source_unavailable` | 校验 resume/version owner | 不需要 | `ResumeVersion`、`VersionRef`、`SnapshotRef` | N/A | `resumes.version.history_read_owner_scoped` |
| GET | `/api/v1/resumes/{resume_id}/modules/project-experiences` | 查询简历中的项目经历模块 | `version_id` 可选 | `ResumeModule(type=project_experience)[]` | `owner_mismatch`、`source_unavailable` | 校验 resume owner；项目经历不是一级资源 | 不需要 | `ResumeModule(type=project_experience)` | N/A | `resume_project_experiences.not_top_level_resource` |
| PATCH | `/api/v1/resumes/{resume_id}/modules/project-experiences/{module_id}` | 编辑项目经历模块并产生简历新版本或模块修正 | `content`、`base_version_ref` | updated module + `ResumeVersion` ref | `validation_failed`、`stale_version_conflict`、`owner_mismatch` | 校验 resume owner 和 module 属于 resume | 必需 | `ResumeModule`、`ResumeVersion`、`AuditEvent` | N/A | `resume_project_experiences.update.versioned` |
| GET | `/api/v1/jobs` | 查询当前用户岗位 / JD 列表 | `cursor`、`limit`、`status`、`application_status`、`sort` | `job[]` + pagination meta | `unauthenticated`、`validation_failed` | 列表按 actor owner scope 过滤 | 不需要 | `Job`、`JobVersion`、`JobStatus` | N/A | `jobs.list.owner_scoped` |
| POST | `/api/v1/jobs` | 手动创建岗位 / JD | `title`、`company`、`department`、`responsibilities`、`requirements`、`other`、`application_status` | 201 `job` + current `JobVersion` | `validation_failed`、`idempotency_required` | 写入当前 actor owner；不支持外部材料解析 | 必需 | `Job`、`JobVersion`、`JobStatus`、`AuditEvent` | N/A | `jobs.create.manual_only` |
| GET | `/api/v1/jobs/{job_id}` | 读取岗位详情 | path `job_id` | `job` + current version summary | `not_found_or_inaccessible`、`owner_mismatch` | 校验 job owner | 不需要 | `Job`、`JobVersion` | N/A | `jobs.get.cross_user_denied` |
| PATCH | `/api/v1/jobs/{job_id}` | 编辑岗位并产生新版本 | job fields + `base_version_ref` | updated `job` + new `JobVersion` | `validation_failed`、`stale_version_conflict`、`owner_mismatch` | 校验 job owner；版本必须同 owner | 必需 | `Job`、`JobVersion`、`AuditEvent` | N/A | `jobs.update.stale_version_conflict` |
| DELETE | `/api/v1/jobs/{job_id}` | soft delete 岗位 | `delete_reason` | `status=success` + `source_deleted` impact summary | `owner_mismatch`、`stale_version_conflict` | 校验 job owner；新生成不得读取 deleted job | 必需 | `Job`、`JobVersion`、`SourceRef` | N/A | `jobs.delete.source_unavailable_for_new_generation` |
| GET | `/api/v1/jobs/{job_id}/versions/{version_id}` | 读取岗位历史版本 | path ids | `job_version` + source availability | `not_found_or_inaccessible` | 校验 job/version owner | 不需要 | `JobVersion`、`VersionRef`、`SnapshotRef` | N/A | `jobs.version.history_read_owner_scoped` |
| GET | `/api/v1/resume-job-bindings` | 查询岗位-简历绑定 | `job_id`、`resume_id`、`status` | `JobResumeBinding[]` | `validation_failed`、`owner_mismatch` | filter 中 job/resume 必须属于 actor | 不需要 | `JobResumeBinding`、`ResumeVersion`、`JobVersion` | N/A | `bindings.list.owner_scoped` |
| POST | `/api/v1/resume-job-bindings` | 建立岗位与简历绑定 | `job_id`、`resume_id`、`job_version_id` 可选、`resume_version_id` 可选 | 201 `JobResumeBinding` | `validation_failed`、`owner_mismatch`、`stale_version_conflict`、`idempotency_required` | 校验 job 和 resume owner 均为 actor 且版本可用 | 必需 | `JobResumeBinding`、`JobVersion`、`ResumeVersion`、`AuditEvent` | N/A | `bindings.create.cross_owner_rejected` |
| DELETE | `/api/v1/resume-job-bindings/{binding_id}` | 解除绑定 | `reason`、`base_version_ref` | `status=success` + historical reference preserved | `owner_mismatch`、`stale_version_conflict` | 校验 binding owner；历史报告不被破坏 | 必需 | `JobResumeBinding`、`AuditEvent` | N/A | `bindings.delete.history_preserved` |
| POST | `/api/v1/job-match-analyses` | 创建岗位匹配分析 AI task | `binding_id` 或 `job_id` + `resume_id`、`job_version_id`、`resume_version_id`、`requested_outputs` | 202 `ai_task_id`; result is `JobMatchAnalysis` | `validation_failed`、`owner_mismatch`、`source_unavailable`、`rate_limited`、`idempotency_required` | 校验 job、resume、binding、version 同 owner 且可用 | 必需 | `JobMatchAnalysis`、`MatchScore`、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`WeaknessCandidate`、`AiTaskResultRef` | `P-JOBMATCH-001`、`P-JOBMATCH-002`、`P-JOBMATCH-003`、`P-JOBMATCH-004` | `job_match.create.async_success`、`job_match.create.idempotent_retry` |
| GET | `/api/v1/job-match-analyses/{analysis_id}` | 读取岗位匹配分析结果 | path `analysis_id` | `JobMatchAnalysis` + score + points + low confidence flags | `not_found_or_inaccessible`、`owner_mismatch`、`source_unavailable` | 校验 analysis owner；历史来源不可用只展示状态 | 不需要 | `JobMatchAnalysis`、`ScoreResult`、`EvidenceRef`、`TraceRef` | `P-JOBMATCH-*` | `job_match.get.low_confidence_visible` |
| GET | `/api/v1/job-match-analyses/{analysis_id}/points` | 读取匹配点、不匹配点、加强点 | `type`、`cursor`、`limit` | points list | `owner_mismatch`、`validation_failed` | 校验 analysis owner | 不需要 | `MatchPoint`、`MismatchPoint`、`ImprovementPoint` | `P-JOBMATCH-003` | `job_match.points.pagination_and_filtering` |
| POST | `/api/v1/polish-sessions` | 创建打磨模式会话 | `resume_id`、`job_id` 可选、`binding_id` 可选、`topic_hint`、`source_refs` | 201 `InterviewSession(mode=polish)` + `PolishSessionDetail` | `validation_failed`、`owner_mismatch`、`source_unavailable` | 校验所有输入 owner；缺失增强输入返回低置信或可继续状态 | 必需 | `InterviewSession`、`PolishSessionDetail`、`ProgressTree` | `P-POLISH-001` 可后续触发 | `polish_sessions.create.success` |
| GET | `/api/v1/polish-sessions/{session_id}` | 读取打磨会话状态 | path `session_id` | session + current question + progress summary | `not_found_or_inaccessible` | 校验 session owner | 不需要 | `InterviewSession`、`PolishSessionDetail`、`SessionSummary` | N/A | `polish_sessions.get.owner_scoped` |
| PATCH | `/api/v1/polish-sessions/{session_id}` | 暂停、恢复或更新用户可见会话状态 | `action=pause,resume,end`、`base_session_version_ref` | updated session state | `validation_failed`、`stale_version_conflict`、`source_unavailable` | 校验 session owner；resume 前校验恢复来源可用性 | 必需 | `InterviewSession`、`ProgressPosition`、`SessionSummary` | `P-SHARED-006` 状态交接 | `polish_sessions.resume.source_unavailable` |
| POST | `/api/v1/polish-sessions/{session_id}/questions` | 生成或选择打磨题目 | `topic_ref`、`progress_node_ref`、`difficulty_hint` | 202 `ai_task_id`; result is `Question` | `owner_mismatch`、`source_unavailable`、`generation_failed`、`rate_limited` | 校验 session owner 和上下文来源 owner | 必需 | `Question`、`RAGContextAssembly`、`AiTaskResultRef` | `P-POLISH-002`、`P-SHARED-*` | `questions.polish_generation.async_failure_visible` |
| POST | `/api/v1/polish-sessions/{session_id}/answers` | 保存用户回答 | `question_id`、`answer_text`、`answer_round`、`base_question_version_ref` | 201 `Answer` | `validation_failed`、`owner_mismatch`、`stale_version_conflict` | 校验 session/question owner | 必需 | `Answer`、`Question`、`AuditEvent` | N/A | `answers.create.validation_failed` |
| POST | `/api/v1/polish-sessions/{session_id}/feedback` | 生成打磨点评、失分点、参考回答、考点解析或下一轮建议 | `answer_id`、`requested_outputs` | 202 `ai_task_id`; result includes `Feedback` and related refs | `owner_mismatch`、`source_unavailable`、`generation_failed`、`low_confidence` | 校验 session/answer owner 和 evidence owner | 必需 | `Feedback`、`LossPoint`、`ReferenceAnswer`、`KnowledgePointExplanation`、`ScoreResult`、`AssetCandidate`、`WeaknessCandidate` | `P-POLISH-003` 至 `P-POLISH-011` | `feedback.polish.low_confidence_visible` |
| POST | `/api/v1/pressure-sessions` | 创建压力面会话 | `resume_id`、`job_id` 可选、`binding_id` 可选、`start_mode` | 201 `InterviewSession(mode=pressure)` + `PressureSessionDetail` | `validation_failed`、`owner_mismatch`、`source_unavailable` | 校验输入 owner；缺失增强输入可生成低置信提示 | 必需 | `InterviewSession`、`PressureSessionDetail`、`ProgressTree` | `P-PRESSURE-001` 可后续触发 | `pressure_sessions.create.success` |
| GET | `/api/v1/pressure-sessions/{session_id}` | 读取压力面会话状态 | path `session_id` | session + pace + current question summary | `not_found_or_inaccessible` | 校验 session owner | 不需要 | `InterviewSession`、`PressureSessionDetail`、`SessionSummary` | N/A | `pressure_sessions.get.owner_scoped` |
| POST | `/api/v1/pressure-sessions/{session_id}/questions` | 生成首题或追问 | `question_type=first,follow_up`、`answer_id` 可选、`pace_state` | 202 `ai_task_id`; result is `Question` | `owner_mismatch`、`source_unavailable`、`generation_failed`、`rate_limited` | 校验 session、answer、source owner | 必需 | `Question`、`PressureSessionDetail`、`AiTaskResultRef` | `P-PRESSURE-002`、`P-PRESSURE-004`、`P-PRESSURE-005` | `questions.pressure_generation.async_success` |
| POST | `/api/v1/pressure-sessions/{session_id}/answers` | 保存压力面回答 | `question_id`、`answer_text`、`answer_order` | 201 `Answer` | `validation_failed`、`owner_mismatch`、`stale_version_conflict` | 校验 session/question owner | 必需 | `Answer`、`Question`、`AuditEvent` | N/A | `answers.pressure.create_success` |
| POST | `/api/v1/pressure-sessions/{session_id}/feedback` | 生成回答质量、节奏控制、结束判断、整场评分或报告输入 | `answer_id`、`requested_outputs` | 202 `ai_task_id`; result includes feedback / score / report input refs | `owner_mismatch`、`source_unavailable`、`generation_failed`、`low_confidence` | 校验 session/answer owner 和 evidence owner | 必需 | `Feedback`、`ScoreResult`、`SessionSummary`、`AiTaskResultRef` | `P-PRESSURE-003`、`P-PRESSURE-006`、`P-PRESSURE-007`、`P-PRESSURE-008`、`P-PRESSURE-009` | `feedback.pressure.generation_failed_visible` |
| GET | `/api/v1/interview-sessions/{session_id}/progress-tree` | 读取会话进展树 | path `session_id` | `ProgressTree` + nodes + position | `owner_mismatch`、`source_unavailable` | 校验 session owner；历史来源不可用只展示状态 | 不需要 | `ProgressTree`、`ProgressNode`、`ProgressPosition` | N/A | `progress_tree.get.owner_scoped` |
| PATCH | `/api/v1/interview-sessions/{session_id}/progress-tree/position` | 更新当前进展位置或用户选择节点 | `progress_node_id`、`base_position_ref` | updated `ProgressPosition` | `validation_failed`、`stale_version_conflict`、`owner_mismatch` | 校验 session/tree/node owner | 必需 | `ProgressPosition`、`ProgressNode` | N/A | `progress_tree.position.stale_version_conflict` |
| GET | `/api/v1/interview-sessions/{session_id}/questions` | 查询会话题目列表 | `cursor`、`limit`、`status` | `Question[]` | `owner_mismatch`、`validation_failed` | 校验 session owner | 不需要 | `Question`、`InterviewSession` | `P-POLISH-002` 或 `P-PRESSURE-002/005` | `questions.list.owner_scoped` |
| GET | `/api/v1/questions/{question_id}` | 读取单题详情 | path `question_id` | `Question` + source refs | `not_found_or_inaccessible` | 校验 question 所属 session owner | 不需要 | `Question`、`SourceRef`、`EvidenceRef` | N/A | `questions.get.cross_user_denied` |
| GET | `/api/v1/answers/{answer_id}` | 读取回答详情 | path `answer_id` | `Answer` | `not_found_or_inaccessible` | 校验 answer 所属 session owner | 不需要 | `Answer` | N/A | `answers.get.cross_user_denied` |
| GET | `/api/v1/feedback/{feedback_id}` | 读取点评 / 反馈详情 | path `feedback_id` | `Feedback` + score / loss / reference refs | `not_found_or_inaccessible`、`low_confidence` | 校验 feedback owner；低置信度必须显式返回 | 不需要 | `Feedback`、`ScoreResult`、`LossPoint`、`ReferenceAnswer` | `P-POLISH-003` 至 `P-POLISH-009` 或 `P-PRESSURE-003/006/007` | `feedback.get.low_confidence_visible` |
| POST | `/api/v1/scoring-results` | 创建 AI scoring task | `target_type`、`target_id`、`score_type`、`input_refs`、`score_rule_version_id` 可选 | 202 `ai_task_id`; result is `ScoreResult` | `validation_failed`、`owner_mismatch`、`source_unavailable`、`generation_failed` | 校验 target/input owner；不得暴露隐藏评分规则 | 必需 | `ScoreResult`、`ScoreRuleVersion`、`ScoreExplanation`、`LowConfidenceFlag` | `P-JOBMATCH-002`、`P-POLISH-004`、`P-PRESSURE-008`、`P-REPORT-002` | `scoring.create.async_low_confidence` |
| GET | `/api/v1/scoring-results/{score_result_id}` | 读取评分结果 | path `score_result_id` | `ScoreResult` + explanation + evidence refs | `not_found_or_inaccessible`、`low_confidence` | 校验 score owner；不返回隐藏规则细节 | 不需要 | `ScoreResult`、`ScoreExplanation`、`ScoreEvidenceLink` | score-producing contracts | `scoring.get.no_hidden_rules` |
| POST | `/api/v1/reports` | 创建面试报告生成任务 | `session_id`、`report_type`、`requested_sections` | 202 `ai_task_id`; result is `InterviewReport` | `validation_failed`、`owner_mismatch`、`source_unavailable`、`generation_failed`、`rate_limited` | 校验 session、resume、job、score refs owner | 必需 | `InterviewReport`、`ReportSection`、`CopyableContent`、`ScoreResult` | `P-REPORT-001`、`P-REPORT-002`、`P-REPORT-003`、`P-REPORT-004` | `reports.create.async_success`、`reports.create.idempotent_retry` |
| GET | `/api/v1/reports/{report_id}` | 读取报告详情 | path `report_id` | `InterviewReport` + sections summary + low confidence flags | `not_found_or_inaccessible`、`source_unavailable` | 校验 report owner；历史来源不可用只展示状态 | 不需要 | `InterviewReport`、`ReportSection` | `P-REPORT-*` | `reports.get.source_unavailable_visible` |
| GET | `/api/v1/reports/{report_id}/sections` | 读取报告分项 | `cursor`、`limit`、`section_type` | `ReportSection[]` | `owner_mismatch`、`validation_failed` | 校验 report owner | 不需要 | `ReportSection`、`ScoreResult` | `P-REPORT-002`、`P-REPORT-003` | `reports.sections.pagination` |
| GET | `/api/v1/reports/{report_id}/copy-content` | 读取可复制报告内容，不生成文件 | `section_ids` 可选、`format=clipboard_text,structured` | `CopyableContent` with `copy_boundary=clipboard_only` | `owner_mismatch`、`source_unavailable`、`copy_boundary_violation`、`export_not_supported` | 校验 report owner、source availability 和 copy scope | 不需要 | `CopyableContent`、`ReportSection`、`AuditEvent` | `P-REPORT-004` | `report_copy.get.no_export`、`report_copy.get.no_prompt_payload` |
| POST | `/api/v1/reports/{report_id}/copy-events` | 记录复制动作和结果 | `copy_content_id`、`copy_scope_summary`、`client_result=success,failed` | 201 `AuditEvent` ref | `owner_mismatch`、`copy_boundary_violation`、`idempotency_required` | 校验 report/copy content owner；不记录复制正文 | 必需 | `AuditEvent`、`CopyableContent` | N/A | `report_copy.audit.no_body_logged` |
| POST | `/api/v1/reviews/mock` | 创建模拟面试复盘分析任务 | `session_id` 或 `report_id`、`requested_items` | 202 `ai_task_id`; result is `MockInterviewReview` | `validation_failed`、`owner_mismatch`、`source_unavailable`、`generation_failed` | 校验 session/report owner 和来源可用性 | 必需 | `InterviewRetrospective`、`MockInterviewReview`、`ReviewItem` | `P-REVIEW-001`、`P-REVIEW-004` | `reviews.mock.create.async_success` |
| POST | `/api/v1/reviews/real-inputs` | 保存真实面试复盘输入 | `job_id` 可选、`resume_id` 可选、`interview_time`、`questions_recalled`、`answers_recalled`、`feedback_text`、`result_status` | 201 `RealInterviewInput` | `validation_failed`、`owner_mismatch` | 写入当前 actor owner；第三方信息不得进日志 | 必需 | `RealInterviewInput`、`RealInterviewEvidence`、`AuditEvent` | N/A | `reviews.real_input.create.validation_failed` |
| POST | `/api/v1/reviews/real` | 创建真实面试复盘分析任务 | `real_interview_input_id`、`requested_items` | 202 `ai_task_id`; result is `RealInterviewReview` | `validation_failed`、`owner_mismatch`、`source_unavailable`、`generation_failed`、`low_confidence` | 校验 input、job、resume owner；标记可信度和完整度 | 必需 | `InterviewRetrospective`、`RealInterviewReview`、`ReviewItem` | `P-REVIEW-002`、`P-REVIEW-003`、`P-REVIEW-004` | `reviews.real.create.low_confidence_visible` |
| GET | `/api/v1/reviews/{review_id}` | 读取模拟或真实复盘 | path `review_id` | review + review items + source confidence | `not_found_or_inaccessible`、`source_unavailable` | 校验 review owner | 不需要 | `MockInterviewReview`、`RealInterviewReview`、`ReviewItem` | `P-REVIEW-*` | `reviews.get.cross_user_denied` |
| GET | `/api/v1/assets` | 查询正式资产 | `cursor`、`limit`、`status`、`asset_type`、`source_type` | `Asset[]` + pagination | `validation_failed`、`unauthenticated` | owner scope 过滤；不返回其他用户资产 | 不需要 | `Asset`、`AssetVersion` | N/A | `assets.list.owner_scoped` |
| GET | `/api/v1/assets/{asset_id}` | 读取正式资产详情 | path `asset_id` | `Asset` + current version + source summary | `not_found_or_inaccessible`、`source_unavailable` | 校验 asset owner | 不需要 | `Asset`、`AssetVersion`、`AssetSource` | N/A | `assets.get.cross_user_denied` |
| GET | `/api/v1/assets/{asset_id}/versions/{version_id}` | 读取资产版本 | path ids | `AssetVersion` + source availability | `not_found_or_inaccessible` | 校验 asset/version owner | 不需要 | `AssetVersion`、`VersionRef` | N/A | `assets.version.history_read_owner_scoped` |
| POST | `/api/v1/asset-candidates` | 创建资产候选提炼任务 | `source_type`、`source_ref`、`target_asset_id` 可选、`candidate_goal` | 202 `ai_task_id`; result is `AssetCandidate` / suggestions | `validation_failed`、`owner_mismatch`、`source_unavailable`、`generation_failed` | 校验 source owner；不得自动写正式 Asset | 必需 | `AssetCandidate`、`AssetQualityHint`、`AssetVersionSuggestion`、`AiTaskResultRef` | `P-ASSET-001`、`P-ASSET-002`、`P-ASSET-003`、`P-POLISH-010` | `asset_candidates.create.candidate_not_formal` |
| GET | `/api/v1/asset-candidates/{candidate_id}` | 读取资产候选 | path `candidate_id` | `AssetCandidate` + evidence + confirmation state | `not_found_or_inaccessible`、`low_confidence` | 校验 candidate owner | 不需要 | `AssetCandidate`、`CandidateRef`、`EvidenceRef` | `P-ASSET-001` | `asset_candidates.get.low_confidence_visible` |
| POST | `/api/v1/asset-candidates/{candidate_id}/confirmations` | 确认、编辑、跳过或拒绝资产候选 | `action=confirm,edit,skip,reject,manual_review`、`edited_content` 可选、`base_candidate_version_ref` | `UserConfirmationRef`; confirm 后可返回 `Asset` / `AssetVersion` ref | `validation_failed`、`owner_mismatch`、`stale_version_conflict` | 校验 candidate owner；确认前不得写正式资产 | 必需 | `UserConfirmationRef`、`Asset`、`AssetVersion`、`AuditEvent` | N/A | `asset_candidates.confirm.formal_requires_user_action` |
| POST | `/api/v1/asset-version-suggestions/{suggestion_id}/confirmations` | 确认或拒绝资产版本建议 | `action=confirm,edit,skip,reject`、`edited_delta` 可选 | `UserConfirmationRef`; confirm 后返回 new `AssetVersion` ref | `validation_failed`、`owner_mismatch`、`stale_version_conflict` | 校验 suggestion 和 target asset owner | 必需 | `AssetVersionSuggestion`、`AssetVersion`、`UserConfirmationRef` | `P-ASSET-003` | `asset_version_suggestions.confirm.no_silent_publish` |
| GET | `/api/v1/weaknesses` | 查询正式薄弱项 | `cursor`、`limit`、`status`、`severity_hint`、`source_type` | `Weakness[]` + pagination | `validation_failed`、`unauthenticated` | owner scope 过滤 | 不需要 | `Weakness`、`WeaknessEvidence` | N/A | `weaknesses.list.owner_scoped` |
| GET | `/api/v1/weaknesses/{weakness_id}` | 读取正式薄弱项详情 | path `weakness_id` | `Weakness` + evidence + status history | `not_found_or_inaccessible` | 校验 weakness owner | 不需要 | `Weakness`、`WeaknessEvidence`、`WeaknessStatusHistory` | N/A | `weaknesses.get.cross_user_denied` |
| PATCH | `/api/v1/weaknesses/{weakness_id}` | 用户显式编辑薄弱项状态或摘要 | `status`、`user_note`、`base_status_ref` | updated `Weakness` + audit ref | `validation_failed`、`stale_version_conflict`、`owner_mismatch` | 校验 weakness owner；AI suggestion 不能直接调用该路径 | 必需 | `Weakness`、`WeaknessStatusHistory`、`AuditEvent` | N/A | `weaknesses.update.user_action_only` |
| POST | `/api/v1/weakness-candidates` | 创建薄弱项提炼任务 | `source_type`、`source_ref`、`candidate_goal` | 202 `ai_task_id`; result is `WeaknessCandidate` / suggestions | `validation_failed`、`owner_mismatch`、`source_unavailable`、`generation_failed` | 校验 source owner；不得自动写正式 Weakness | 必需 | `WeaknessCandidate`、`WeaknessMergeSuggestion`、`WeaknessSeverityAssessment`、`WeaknessStatusUpdateSuggestion` | `P-WEAKNESS-001`、`P-WEAKNESS-002`、`P-WEAKNESS-003`、`P-WEAKNESS-004`、`P-JOBMATCH-004`、`P-POLISH-011` | `weakness_candidates.create.candidate_not_formal` |
| GET | `/api/v1/weakness-candidates/{candidate_id}` | 读取薄弱项候选 | path `candidate_id` | `WeaknessCandidate` + evidence + merge suggestions | `not_found_or_inaccessible`、`low_confidence` | 校验 candidate owner | 不需要 | `WeaknessCandidate`、`CandidateRef`、`EvidenceRef` | `P-WEAKNESS-001` | `weakness_candidates.get.low_confidence_visible` |
| POST | `/api/v1/weakness-candidates/{candidate_id}/confirmations` | 确认、编辑、合并、跳过或拒绝薄弱项候选 | `action=confirm,edit,merge,skip,reject,manual_review`、`target_weakness_id` 可选、`edited_summary` 可选 | `UserConfirmationRef`; confirm / merge 后返回 `Weakness` ref | `validation_failed`、`owner_mismatch`、`stale_version_conflict` | 校验 candidate 和 target weakness owner；确认前不得写正式 Weakness | 必需 | `UserConfirmationRef`、`Weakness`、`WeaknessStatusHistory` | N/A | `weakness_candidates.confirm.formal_requires_user_action` |
| POST | `/api/v1/weakness-merge-suggestions/{suggestion_id}/confirmations` | 确认或拒绝薄弱项合并建议 | `action=merge,edit,skip,reject`、`target_weakness_id` | `UserConfirmationRef` + optional merged `Weakness` ref | `validation_failed`、`owner_mismatch`、`stale_version_conflict` | 校验 suggestion、candidate、target weakness owner | 必需 | `WeaknessMergeSuggestion`、`UserConfirmationRef` | `P-WEAKNESS-002` | `weakness_merge.confirm.no_silent_merge` |
| POST | `/api/v1/weakness-status-suggestions/{suggestion_id}/confirmations` | 确认或拒绝薄弱项状态更新建议 | `action=confirm,edit,skip,reject`、`edited_status` 可选 | `UserConfirmationRef` + optional updated `Weakness` ref | `validation_failed`、`owner_mismatch`、`stale_version_conflict` | 校验 suggestion 和 weakness owner | 必需 | `WeaknessStatusUpdateSuggestion`、`WeaknessStatusHistory` | `P-WEAKNESS-004` | `weakness_status.confirm.no_silent_update` |
| POST | `/api/v1/training-suggestions` | 创建训练建议生成任务 | `source_type`、`source_ref`、`weakness_ids` 可选、`asset_ids` 可选 | 202 `ai_task_id`; result is recommendation candidates / ranking | `validation_failed`、`owner_mismatch`、`source_unavailable`、`generation_failed` | 校验所有 input owner；不得自动创建 TrainingTask | 必需 | `TrainingRecommendation`、`TrainingPriorityRanking`、`AiTaskResultRef` | `P-TRAINING-001`、`P-TRAINING-002` | `training_suggestions.create.no_auto_task` |
| GET | `/api/v1/training-suggestions/{recommendation_id}` | 读取训练建议或候选 | path `recommendation_id` | `TrainingRecommendation` + status + evidence | `not_found_or_inaccessible`、`low_confidence` | 校验 recommendation owner | 不需要 | `TrainingRecommendation`、`EvidenceRef` | `P-TRAINING-001` | `training_suggestions.get.low_confidence_visible` |
| POST | `/api/v1/training-suggestions/{recommendation_id}/confirmations` | 确认、编辑、跳过或拒绝训练建议 | `action=confirm,edit,skip,reject,manual_review`、`edited_recommendation` 可选 | `UserConfirmationRef`; confirm 后 recommendation 可进入正式状态 | `validation_failed`、`owner_mismatch`、`stale_version_conflict` | 校验 recommendation owner；确认不等于自动启动 TrainingTask | 必需 | `TrainingRecommendation`、`UserConfirmationRef` | N/A | `training_suggestions.confirm.no_auto_training_task` |
| POST | `/api/v1/training-tasks` | 用户显式启动训练任务 | `training_recommendation_id`、`entry_mode=polish,pressure,manual`、`scheduled_at` 可选 | 201 `TrainingTask` / `TrainingSession` | `validation_failed`、`owner_mismatch`、`source_unavailable` | 校验 recommendation owner；必须是用户动作或明确确认后动作 | 必需 | `TrainingTask`、`TrainingSession`、`AuditEvent` | N/A | `training_tasks.create.user_action_required` |
| GET | `/api/v1/training-tasks/{training_task_id}` | 读取训练任务状态 | path `training_task_id` | `TrainingTask` + optional `TrainingResult` | `not_found_or_inaccessible` | 校验 task owner | 不需要 | `TrainingTask`、`TrainingResult` | N/A | `training_tasks.get.owner_scoped` |
| POST | `/api/v1/training-results/{training_result_id}/review` | 创建训练结果复盘任务 | `training_result_id`、`requested_outputs` | 202 `ai_task_id`; result is `TrainingResultReview` suggestions | `validation_failed`、`owner_mismatch`、`source_unavailable`、`generation_failed` | 校验 result/task owner；回流只产候选 / 建议 | 必需 | `TrainingResultReview`、`WeaknessStatusUpdateSuggestion`、`AssetCandidate`、`TrainingRecommendation` candidate | `P-TRAINING-003` | `training_result_review.create.candidate_only` |
| POST | `/api/v1/ai-tasks` | 创建通用 AI task；用于 domain endpoint 未覆盖的 F5 内部显式任务 | `task_type`、`contract_ids`、`target_ref`、`input_refs`、`requested_outputs` | 202 `ai_task_id` + task status | `validation_failed`、`owner_mismatch`、`source_unavailable`、`rate_limited`、`idempotency_required` | 校验所有 input refs owner；contract id 必须已登记 | 必需 | `AiTaskResultRef`、`LlmValidationResult`、`TraceRef` | 已登记 `P-*` | `ai_tasks.create.contract_id_registered` |
| GET | `/api/v1/ai-tasks/{ai_task_id}` | 查询 AI task 状态 | path `ai_task_id` | task status envelope | `not_found_or_inaccessible`、`owner_mismatch` | 校验 task owner | 不需要 | `AiTaskResultRef`、`LlmValidationResult` | related `P-*` | `ai_tasks.status.owner_scoped` |
| GET | `/api/v1/ai-tasks/{ai_task_id}/result` | 读取 AI task 结果引用或候选 / 建议 | path `ai_task_id` | result refs + candidate / suggestion / low confidence flags | `not_found_or_inaccessible`、`generation_failed`、`task_timeout`、`source_unavailable` | 校验 task owner；不得返回 raw provider payload | 不需要 | `AiTaskResultRef`、`CandidateRef`、`SuggestionRef` | related `P-*` | `ai_tasks.result.no_provider_payload` |
| POST | `/api/v1/ai-tasks/{ai_task_id}/retry` | 重试失败、timeout、source 修复后或可重试低置信度任务 | `reason`、`fixed_input_refs` 可选 | 202 new or same `ai_task_id` per retry policy | `task_retry_not_allowed`、`owner_mismatch`、`idempotency_required`、`source_unavailable` | 校验 task owner；重试不得扩大未授权上下文 | 必需 | `AiTaskResultRef`、`LlmFailureRecord` | related `P-*` | `ai_tasks.retry.idempotent_and_scope_safe` |
| POST | `/api/v1/ai-tasks/{ai_task_id}/cancel` | 取消 queued 或可中断 running 任务 | `reason` | task `status=cancelled` | `task_cancelled`、`task_retry_not_allowed`、`owner_mismatch` | 校验 task owner；取消后不得写 formal object | 必需 | `AiTaskResultRef`、`AuditEvent` | related `P-*` | `ai_tasks.cancel.no_late_write` |

## 7. Candidate / suggestion / confirmation 写入边界

### 7.1 通用 confirmation request

候选、建议、合并、状态更新、资产版本发布和训练建议确认类 endpoint 必须使用同一类确认语义：

| 字段 | 语义 |
|---|---|
| `action` | `confirm`、`edit`、`skip`、`merge`、`reject`、`manual_review` |
| `target_ref` | 被确认的 candidate、suggestion 或 formal object |
| `target_version_ref` | 防 stale update 的版本或状态引用 |
| `edited_content` / `edited_summary` | 用户编辑后的结构化摘要或内容；不得保存过量正文到审计 |
| `target_formal_ref` | merge 或 update 时的正式对象引用 |
| `confirmation_note` | 用户备注，可为空 |

确认响应必须返回 `UserConfirmationRef` 或等价确认记录，包含 actor、target、action、before / after summary、result、trace 和 audit event。

### 7.2 Formal object 写入规则

- `WeaknessCandidate` 只有在用户 `confirm`、`edit` 或 `merge` 后，才允许产生或更新正式 `Weakness`。
- `AssetCandidate` 只有在用户 `confirm` 或 `edit` 后，才允许产生正式 `Asset` 或 `AssetVersion`。
- `AssetVersionSuggestion` 只有在用户确认后，才允许发布、替换或覆盖正式 `AssetVersion`。
- `TrainingRecommendation` candidate 只有在用户确认后，才允许成为正式训练建议；正式训练任务仍必须由用户显式启动或明确确认动作创建。
- `TrainingResultReview`、`WeaknessStatusUpdateSuggestion`、`AssetQualityHint` 和 `TrainingPriorityRanking` 只能作为 suggestion / hint；不得自动更新正式 Weakness、归档 Asset 或创建下一轮 TrainingRecommendation。
- `InterviewReport`、`MockInterviewReview` 和 `RealInterviewReview` 作为生成结果可被读取，但其提炼出的薄弱项、资产、训练建议仍必须走 candidate / suggestion / confirmation。

## 8. 报告读取、copy content 与禁止 export

报告 API 只允许：

- `GET /api/v1/reports/{report_id}` 读取报告。
- `GET /api/v1/reports/{report_id}/sections` 读取报告分项。
- `GET /api/v1/reports/{report_id}/copy-content` 返回剪贴板可用内容结构。
- `POST /api/v1/reports/{report_id}/copy-events` 记录复制事件。

禁止 endpoint 和语义：

- 不得提供 `/exports`、`/download`、`/files`、`/pdf`、`/docx`、`/markdown-file`、`/report-file`、`/snapshot-file` 或批量下载 endpoint。
- 不得返回 filename、download URL、file id、file snapshot、Markdown export artifact 或外部文件生成结果。
- `CopyableContent` 只能表示页面复制所需结构化内容，不是下载物、导出物或文件快照。
- copy content 不得包含 `system prompt`、Prompt 模板、completion、provider payload、隐藏评分规则、无权限来源正文或未经脱敏的第三方 / 公司 / 个人敏感信息。
- F7 必须使用 route inventory 或 OpenAPI route list 断言不存在 export/download endpoint，并用 copy content fixture 断言 copy boundary。

## 9. F7 可测试性矩阵

| 能力 | 必测断言 |
|---|---|
| Success | 每个核心 endpoint 至少一个 owner 内成功路径；异步 task 能从 create 到 status 到 result |
| Validation failed | 字段缺失、非法 enum、非法 sort/filter、空 Markdown、过长文本、缺少必要 source ref 返回 `validation_failed` |
| Permission denied / cross-user access | 用户 A 无法 list/get/update/delete/generate/copy/confirm 用户 B 的任何资源 |
| Source unavailable | deleted / archived / disabled / inaccessible source 不能进入新生成；历史结果只展示 source availability |
| Low confidence | low confidence 以 `status`、`low_confidence_flags` 和 `next_actions` 返回，不被前端当作高置信成功 |
| Generation failed | provider timeout、schema invalid、semantic invalid、RAG failure 返回 `generation_failed` 或 `validation_failed`，不写 formal object |
| Idempotent retry | mutation 和 AI task create 使用同一 `Idempotency-Key` 不重复创建；同 key 不同 body 返回 `idempotency_conflict` |
| Stale version / conflict | `If-Match`、`base_version_ref`、`target_version_ref` 过期返回 `stale_version_conflict` |
| No export endpoint | route inventory 不存在 PDF / Markdown file / Word / docx / export / download endpoint；命中时返回 `export_not_supported` |
| Copy boundary | copy content 仅为 clipboard 结构，不含 prompt/provider payload/hidden scoring rules/sensitive raw text；复制事件审计不记录正文 |
| Formal object confirmation | candidate / suggestion 不经用户确认不得成为正式 Asset、Weakness、TrainingRecommendation、AssetVersion 或 TrainingTask |
| Rate limit | 登录、简历保存、LLM 生成、RAG 检索、报告生成、复盘生成、训练建议生成触发 429 和 retry metadata |
| Async cancellation / timeout | queued/running task 可取消；timeout 可见；取消或 timeout 不产生 late formal write |

## 10. 与 TECH / DATA / SECURITY / PROMPT 的一致性边界

| 子文档 | 一致性点 |
|---|---|
| `TECH_DESIGN.md` | API 继续位于 API 边界层；前端只依赖 API contract，不直接读库或调用 LLM；AI 生成任务由应用编排层串联领域能力、LLM 边界、持久化、trace 和审计 |
| `DATA_MODEL.md` | endpoint 只使用已登记逻辑对象、引用对象和状态域；项目经历作为 `ResumeModule(type=project_experience)` 子资源；`AiTaskResultRef`、`CandidateRef`、`SuggestionRef`、`UserConfirmationRef`、`VersionRef`、`TraceRef`、`EvidenceRef` 进入 API envelope |
| `SECURITY_PRIVACY.md` | 未登录拒绝、owner enforcement、source unavailable、复制审计、日志脱敏、Prompt / provider payload 不暴露、copy 非 export 与本文一致 |
| `PROMPT_SPEC.md` | `P-*` 只作为 related prompt contract 和 trace / validation 引用；Prompt contract 的 `api_state_mapping` 不替代 endpoint；failure signals 映射为 API status / error / low confidence |

本文件不新增未登记业务对象，不把项目经历提升为一级业务对象，不引入 MVP non-goal，不定义文件导出，不绕过 candidate / confirmation / formal object 边界。

## 11. Deferred / 非本轮关闭项

以下事项不属于 `AR-F4-FULL-002` 的 API handoff 缺口，仍按对应 finding、UNKNOWN 或后续任务处理：

- `AR-F4-FULL-001`：所有 `F4_TECH_DESIGN` UNKNOWN 的关闭 / Deferred / Accepted Risk。
- `AR-F4-FULL-003`：评分公式、权重、阈值、校准、风险提示和免责声明。
- `AR-F4-FULL-005`：进展树、暂停恢复和异步失败状态机的完整状态机冻结；本文只定义 API status / retry / cancel / timeout 协议。
- 正式 Weakness 生命周期、合并规则、关闭阈值和自动消减规则。
- Asset 质量判断、版本合并、归档、替代和去重算法。
- Training 优先级、训练结果评估、弱项自动消减和自动训练策略。
- 鉴权 API 的完整登录注册产品流程、复杂 ACL、企业多租户和组织权限模型。
- 物理数据库、队列、缓存、日志平台、监控告警和部署拓扑。

## 12. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-16 | 修复 `AR-F4-FULL-002` API handoff 缺口 | 将 `API_SPEC.md` 从早期占位草案补齐为 F5/F6/F7 可交接 API contract；新增全局约定、错误 envelope、分页 / sorting / filtering、idempotency、rate limit、async task protocol、核心 endpoint matrix、copy boundary 和 F7 test assertions；不写实现代码，不关闭其它 finding，不标记 acceptance |
| 2026-05-16 | 同步 Asset / Training handoff 与候选确认集中语义 | 补 Candidate / Confirmation 集中语义、Asset API handoff、Training API handoff 和 async / status / retry / idempotency 占位；不定义 endpoint，不关闭 UNKNOWN |
| 2026-05-16 | 初始化 F4 API 契约早期草案 | 对齐 DATA_MODEL 与 Prompt contracts 中的候选态、建议态、用户确认流、AI task result、response envelope 和 Weakness API handoff；后续已由 `AR-F4-FULL-002` remediation 补齐 endpoint contract，不关闭 `F4_TECH_DESIGN` UNKNOWN |
