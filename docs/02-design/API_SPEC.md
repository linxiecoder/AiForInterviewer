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
- 本轮按 `AR-F4-FULL-001` 处置 API 侧 F4 阻断项：endpoint、error semantics、retry、idempotency、rate limit、async task、permission、copy boundary 和 F7 assertion 已作为 F5/F6/F7 handoff 固化；Medium / Low findings 不在本轮变更状态；不标记 `F4_FULL_DESIGN_ACCEPTANCE.md` 为 Accepted；不创建 final acceptance approval。
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
| `score_version` | 否 | 评分结果版本；评分 / 报告 / 复盘 / job match 相关响应返回 |
| `rubric_version` | 否 | rubric / rule version；评分 / 报告 / 复盘 / job match 相关响应返回 |
| `confidence_level` | 否 | `high`、`medium`、`low`、`insufficient`；低置信度不能被正常成功态吞掉 |
| `pass_tendency_level` | 否 | `low`、`medium`、`high`、`caution`、`insufficient_evidence`；不得表达精确通过概率 |
| `risk_level` | 否 | `low`、`medium`、`high`、`unknown`；风险提示必须同时带 `evidence_refs` 或低置信度原因 |
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

### 4.4 评分、通过倾向和风险提示响应语义

评分 / 报告 / job match / review 相关 endpoint 必须遵守以下响应语义：

- API 可以返回 0-100 `score_value` / `display_score`，但必须通过 `score_scale=0_100_product_scale` 说明这是产品评分刻度，不是精确通过概率。
- API 不得返回 `pass_probability`、`offer_probability`、`admission_probability`、`pass_rate_percent` 或任何等价精确概率字段；也不得返回“你有 73% 概率通过”一类文案。
- API 必须返回 `score_version`、`rubric_version`、`score_rule_version_ref`、`confidence_level`、`evidence_refs`、`trace_refs`、`validation_result_ref` 和 `generated_by_task_id`，用于 F5 / F6 / F7 追踪评分来源。
- `pass_tendency_level` 只允许 `low` / `medium` / `high` / `caution` / `insufficient_evidence`，用户可见映射为“偏低 / 中等 / 偏高 / 需谨慎 / 证据不足，无法判断倾向”。
- `low_confidence`、`source_unavailable`、`validation_failed`、`evidence_missing`、`score_rule_version_missing` 或 `manual_check_required` 时，API 不得返回确定性通过倾向；必须返回 `pass_tendency_level=insufficient_evidence` 或不返回该字段，并给出 `low_confidence_flags` / `next_actions`。
- 风险提示必须返回 `risk_level`、`risk_reason`、`confidence_level`、`evidence_refs`、`score_version`、`rubric_version`、`validation_status` 和必要 disclaimer；不得只返回不可解释的风险文案。
- `validation_failed` 的 scoring candidate 不得落为正式 `ScoreResult`，报告读取不得把该候选分展示为正式评分；只能返回 validation failure、repair / retry 或 manual review 状态。
- API 不暴露隐藏评分规则、完整内部权重表、校准样例正文、系统 prompt、provider payload 或可反向复制的内部校准细节；copy content 同样不得包含这些内容。
- 所有用户可见评分、通过倾向和风险提示必须附带可信度说明和非决策性免责声明，说明结果基于当前材料、规则版本和证据，仅用于面试准备辅助。

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

## 6. API 清单总表

本节作为 F5 后端实现、F6 前端接入和 F7 API contract tests 的稳定 route inventory。旧版 endpoint matrix 不再作为唯一交接面；逐接口字段级 contract 见 §7，Schema Index 见 §8。

| API ID | Method | Path | Name | Domain | Sync/Async | Auth | Idempotency | Owner Check | Request Schema | Response Schema | Error Schema | Related Data Objects | Related Prompt Contract | F7 Contract Test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API-RESUME-001 | GET | /api/v1/resumes | List resumes | Resume | sync | required | not required | 按 actor owner scope 过滤列表 | N/A (Query Params) | ResumeSummary[] | ApiErrorEnvelope | Resume, ResumeVersion, OwnerRef | N/A | api.resume.list.owner_scoped |
| API-RESUME-002 | POST | /api/v1/resumes | Create resume | Resume | sync | required | required | 服务端从 session 推导 owner, 请求体不得包含 owner_id | CreateResumeRequest | ResumeDetail | ApiErrorEnvelope | Resume, ResumeVersion, ResumeModule, AuditEvent, IdempotencyRecord | N/A | api.resume.create.success |
| API-RESUME-003 | GET | /api/v1/resumes/{resume_id} | Get resume detail | Resume | sync | required | not required | resume.owner_ref 必须匹配当前 actor | N/A | ResumeDetail | ApiErrorEnvelope | Resume, ResumeVersion, ResumeModule, OwnerRef | N/A | api.resume.get.cross_user_denied |
| API-RESUME-004 | PATCH | /api/v1/resumes/{resume_id} | Update resume | Resume | sync | required | required | resume.owner_ref 与 base_version_ref owner 一致 | UpdateResumeRequest | ResumeDetail | ApiErrorEnvelope | Resume, ResumeVersion, ResumeModule, AuditEvent, IdempotencyRecord | N/A | api.resume.update.stale_version_conflict |
| API-RESUME-005 | GET | /api/v1/resumes/{resume_id}/modules/project-experiences | List resume project experience modules | Resume project experiences | sync | required | not required | resume.owner_ref 必须匹配当前 actor, project experience 不是一级资源 | N/A (Query Params) | ResumeProjectExperienceModule[] | ApiErrorEnvelope | ResumeModule(type=project_experience), ResumeVersion, SourceAvailability | N/A | api.resume_project_experience.list.not_top_level |
| API-RESUME-006 | PATCH | /api/v1/resumes/{resume_id}/modules/project-experiences/{module_id} | Update resume project experience module | Resume project experiences | sync | required | required | module 必须属于当前 resume 且 owner 匹配 | UpdateResumeRequest | ResumeProjectExperienceModule | ApiErrorEnvelope | ResumeModule, ResumeVersion, AuditEvent, IdempotencyRecord | N/A | api.resume_project_experience.update.versioned |
| API-JOB-001 | GET | /api/v1/jobs | List jobs | Job / JD | sync | required | not required | 按 actor owner scope 过滤列表 | N/A (Query Params) | JobSummary[] | ApiErrorEnvelope | Job, JobVersion, JobStatus, OwnerRef | N/A | api.job.list.owner_scoped |
| API-JOB-002 | POST | /api/v1/jobs | Create job manually | Job / JD | sync | required | required | 服务端从 session 推导 owner, 不接受外部材料解析 | CreateJobRequest | JobDetail | ApiErrorEnvelope | Job, JobVersion, JobStatus, AuditEvent, IdempotencyRecord | N/A | api.job.create.manual_only |
| API-JOB-003 | GET | /api/v1/jobs/{job_id} | Get job detail | Job / JD | sync | required | not required | job.owner_ref 必须匹配当前 actor | N/A | JobDetail | ApiErrorEnvelope | Job, JobVersion, JobStatus, OwnerRef | N/A | api.job.get.cross_user_denied |
| API-JOB-004 | PATCH | /api/v1/jobs/{job_id} | Update job | Job / JD | sync | required | required | job.owner_ref 与 base_version_ref owner 一致 | UpdateJobRequest | JobDetail | ApiErrorEnvelope | Job, JobVersion, JobStatus, AuditEvent, IdempotencyRecord | N/A | api.job.update.stale_version_conflict |
| API-BINDING-001 | POST | /api/v1/resume-job-bindings | Create resume-job binding | Resume-job binding | sync | required | required | resume、job、version 必须同 owner | CreateBindingRequest | JobResumeBindingResponse | ApiErrorEnvelope | JobResumeBinding, ResumeVersion, JobVersion, AuditEvent, IdempotencyRecord | N/A | api.binding.create.cross_owner_denied |
| API-JOBMATCH-001 | POST | /api/v1/job-match-analyses | Create job match analysis task | Job match analysis | async | required | required | binding/job/resume/version 必须同 owner 且 source_available | CreateJobMatchAnalysisRequest | AiTaskStatusResponse | ApiErrorEnvelope | JobMatchAnalysis, MatchScore, WeaknessCandidate, AiTask, IdempotencyRecord | P-JOBMATCH-001, P-JOBMATCH-002, P-JOBMATCH-003, P-JOBMATCH-004 | api.job_match.create.async_success |
| API-JOBMATCH-002 | GET | /api/v1/job-match-analyses/{analysis_id} | Get job match analysis | Job match analysis | sync | required | not required | analysis.owner_ref 必须匹配当前 actor | N/A | JobMatchAnalysisResponse | ApiErrorEnvelope | JobMatchAnalysis, ScoreResult, EvidenceRef, TraceRef, SourceAvailability | P-JOBMATCH-* | api.job_match.get.low_confidence_visible |
| API-POLISH-001 | POST | /api/v1/polish-sessions | Create polish session | Polish session | sync | required | required | resume/job/binding/source_refs 必须同 owner | CreatePolishSessionRequest | InterviewSessionResponse | ApiErrorEnvelope | InterviewSession, PolishSessionDetail, ProgressTree, IdempotencyRecord | P-POLISH-001 | api.polish_session.create.success |
| API-POLISH-002 | GET | /api/v1/polish-sessions/{session_id} | Get polish session | Polish session | sync | required | not required | session.owner_ref 必须匹配当前 actor | N/A | InterviewSessionResponse | ApiErrorEnvelope | InterviewSession, PolishSessionDetail, ProgressTree, SessionSummary | N/A | api.polish_session.get.owner_scoped |
| API-POLISH-003 | POST | /api/v1/polish-sessions/{session_id}/questions | Create polish question task | Question | async | required | required | session、progress_node、source_refs 必须同 owner | CreateQuestionTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | Question, AiTask, RAGContextAssembly, IdempotencyRecord | P-POLISH-002, P-SHARED-* | api.polish_question.create.async_success |
| API-POLISH-004 | POST | /api/v1/polish-sessions/{session_id}/answers | Create polish answer | Answer | sync | required | required | session/question.owner_ref 必须匹配当前 actor | CreateAnswerRequest | AnswerResponse | ApiErrorEnvelope | Answer, Question, InterviewSession, AuditEvent, IdempotencyRecord | N/A | api.polish_answer.create.validation_failed |
| API-POLISH-005 | POST | /api/v1/polish-sessions/{session_id}/feedback | Create polish feedback task | Feedback | async | required | required | session/answer/evidence owner 必须匹配当前 actor | CreateFeedbackTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | Feedback, ScoreResult, AssetCandidate, WeaknessCandidate, AiTask, IdempotencyRecord | P-POLISH-003, P-POLISH-004, P-POLISH-005, P-POLISH-006, P-POLISH-007, P-POLISH-008, P-POLISH-009, P-POLISH-010, P-POLISH-011 | api.polish_feedback.create.low_confidence_visible |
| API-PRESSURE-001 | POST | /api/v1/pressure-sessions | Create pressure session | Pressure session | sync | required | required | resume/job/binding/source_refs 必须同 owner | CreatePressureSessionRequest | InterviewSessionResponse | ApiErrorEnvelope | InterviewSession, PressureSessionDetail, ProgressTree, IdempotencyRecord | P-PRESSURE-001 | api.pressure_session.create.success |
| API-PRESSURE-002 | GET | /api/v1/pressure-sessions/{session_id} | Get pressure session | Pressure session | sync | required | not required | session.owner_ref 必须匹配当前 actor | N/A | InterviewSessionResponse | ApiErrorEnvelope | InterviewSession, PressureSessionDetail, ProgressTree, SessionSummary | N/A | api.pressure_session.get.owner_scoped |
| API-PRESSURE-003 | POST | /api/v1/pressure-sessions/{session_id}/questions | Create pressure question task | Question | async | required | required | session/answer/source_refs 必须同 owner | CreateQuestionTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | Question, AiTask, PressureSessionDetail, IdempotencyRecord | P-PRESSURE-002, P-PRESSURE-004, P-PRESSURE-005 | api.pressure_question.create.async_success |
| API-PRESSURE-004 | POST | /api/v1/pressure-sessions/{session_id}/answers | Create pressure answer | Answer | sync | required | required | session/question.owner_ref 必须匹配当前 actor | CreateAnswerRequest | AnswerResponse | ApiErrorEnvelope | Answer, Question, InterviewSession, AuditEvent, IdempotencyRecord | N/A | api.pressure_answer.create.success |
| API-PRESSURE-005 | POST | /api/v1/pressure-sessions/{session_id}/feedback | Create pressure feedback task | Feedback | async | required | required | session/answer/evidence owner 必须匹配当前 actor | CreateFeedbackTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | Feedback, ScoreResult, SessionSummary, AiTask, IdempotencyRecord | P-PRESSURE-003, P-PRESSURE-006, P-PRESSURE-007, P-PRESSURE-008, P-PRESSURE-009 | api.pressure_feedback.create.generation_failed_visible |
| API-PROGRESS-001 | GET | /api/v1/interview-sessions/{session_id}/progress-tree | Get progress tree | Progress tree | sync | required | not required | session.owner_ref 必须匹配当前 actor | N/A | ProgressTreeResponse | ApiErrorEnvelope | ProgressTree, ProgressNode, ProgressPosition, SourceAvailability | N/A | api.progress_tree.get.owner_scoped |
| API-SCORING-001 | POST | /api/v1/scoring-results | Create scoring task | Scoring result | async | required | required | target/input_refs owner 必须匹配当前 actor, hidden scoring rules 不暴露 | CreateScoringTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | ScoreResult, ScoreRuleVersion, ScoreExplanation, AiTask, IdempotencyRecord | P-JOBMATCH-002, P-POLISH-004, P-PRESSURE-008, P-REPORT-002 | api.scoring.create.no_hidden_rules |
| API-SCORING-002 | GET | /api/v1/scoring-results/{score_result_id} | Get scoring result | Scoring result | sync | required | not required | score_result.owner_ref 必须匹配当前 actor | N/A | ScoreResultResponse | ApiErrorEnvelope | ScoreResult, ScoreRuleVersion, EvidenceRef, TraceRef, LowConfidenceFlag | P-JOBMATCH-002, P-POLISH-004, P-PRESSURE-008, P-REPORT-002 | api.scoring.get.no_exact_probability |
| API-REPORT-001 | POST | /api/v1/reports | Create report task | Report | async | required | required | session/input_refs owner 必须匹配当前 actor | CreateReportTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | InterviewReport, ReportSection, ScoreResult, AiTask, IdempotencyRecord | P-REPORT-001, P-REPORT-002, P-REPORT-003, P-REPORT-004 | api.report.create.async_success |
| API-REPORT-002 | GET | /api/v1/reports/{report_id} | Get report | Report | sync | required | not required | report.owner_ref 必须匹配当前 actor | N/A | ReportResponse | ApiErrorEnvelope | InterviewReport, ReportSection, ScoreResult, SourceAvailability | P-REPORT-* | api.report.get.copy_boundary_visible |
| API-REPORT-003 | GET | /api/v1/reports/{report_id}/copy-content | Get report copy content | Report copy content | sync | required | not required | report.owner_ref 必须匹配当前 actor, copy boundary 必须过滤敏感内容 | N/A | ReportCopyContentResponse | ApiErrorEnvelope | CopyableContent, InterviewReport, AuditEvent, EvidenceRef | P-REPORT-004 | api.report.copy_content.no_export_artifact |
| API-REPORT-004 | POST | /api/v1/reports/{report_id}/copy-events | Record report copy event | Report copy content | sync | required | required | report.owner_ref 必须匹配当前 actor, 审计不记录正文 | RecordCopyEventRequest | ReportCopyContentResponse | ApiErrorEnvelope | CopyableContent, AuditEvent, IdempotencyRecord | N/A | api.report.copy_event.audit_without_body |
| API-REVIEW-001 | POST | /api/v1/reviews/mock | Create mock interview review task | Mock interview review | async | required | required | session/report/input_refs owner 必须匹配当前 actor | CreateReviewTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | MockInterviewReview, ReviewItem, AiTask, IdempotencyRecord | P-REVIEW-001, P-REVIEW-004 | api.review.mock.create.async_success |
| API-REVIEW-002 | POST | /api/v1/reviews/real-inputs | Create real interview input | Real interview input / review | sync | required | required | job/resume/input_refs owner 必须匹配当前 actor | CreateRealInterviewInputRequest | ReviewResponse | ApiErrorEnvelope | RealInterviewInput, RealInterviewEvidence, UserConfirmationRef, IdempotencyRecord | P-REVIEW-002 | api.review.real_input.create.requires_confirmation |
| API-REVIEW-003 | POST | /api/v1/reviews/real | Create real interview review task | Real interview input / review | async | required | required | real_interview_input owner 必须匹配当前 actor 且已确认 | CreateReviewTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | RealInterviewReview, ReviewItem, AiTask, IdempotencyRecord | P-REVIEW-003, P-REVIEW-004 | api.review.real.create.confirmed_input_only |
| API-REVIEW-004 | GET | /api/v1/reviews/{review_id} | Get review | Mock interview review / Real interview review | sync | required | not required | review.owner_ref 必须匹配当前 actor | N/A | ReviewResponse | ApiErrorEnvelope | MockInterviewReview, RealInterviewReview, ReviewItem, SourceAvailability | P-REVIEW-* | api.review.get.low_confidence_visible |
| API-ASSET-001 | GET | /api/v1/assets | List assets | Asset | sync | required | not required | 按 actor owner scope 过滤正式资产 | N/A (Query Params) | AssetResponse[] | ApiErrorEnvelope | Asset, AssetVersion, AssetSource, OwnerRef | N/A | api.asset.list.owner_scoped |
| API-ASSET-002 | POST | /api/v1/asset-candidates | Create asset candidate task | Asset candidate / asset version suggestion | async | required | required | source_refs/target_asset owner 必须匹配当前 actor | CreateAssetCandidateTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | AssetCandidate, AssetQualityHint, AssetVersionSuggestion, AiTask, IdempotencyRecord | P-ASSET-001, P-ASSET-002, P-ASSET-003, P-POLISH-010 | api.asset_candidate.create.candidate_not_formal |
| API-ASSET-003 | GET | /api/v1/asset-candidates/{candidate_id} | Get asset candidate | Asset candidate / asset version suggestion | sync | required | not required | candidate.owner_ref 必须匹配当前 actor | N/A | AssetCandidateResponse | ApiErrorEnvelope | AssetCandidate, AssetQualityHint, AssetVersionSuggestion, EvidenceRef, TraceRef | P-ASSET-* | api.asset_candidate.get.low_confidence_visible |
| API-ASSET-004 | POST | /api/v1/asset-candidates/{candidate_id}/confirmations | Confirm asset candidate | Asset candidate / asset version suggestion | sync | required | required | candidate 和 target_asset owner 必须匹配当前 actor, 确认前不得写正式 Asset | ConfirmCandidateRequest | AssetResponse | ApiErrorEnvelope | AssetCandidate, Asset, AssetVersion, UserConfirmationRef, AuditEvent, IdempotencyRecord | P-ASSET-001, P-ASSET-003 | api.asset_candidate.confirm.formal_requires_user_action |
| API-WEAKNESS-001 | GET | /api/v1/weaknesses | List weaknesses | Weakness | sync | required | not required | 按 actor owner scope 过滤正式薄弱项 | N/A (Query Params) | WeaknessResponse[] | ApiErrorEnvelope | Weakness, WeaknessEvidence, WeaknessStatusHistory | N/A | api.weakness.list.owner_scoped |
| API-WEAKNESS-002 | POST | /api/v1/weakness-candidates | Create weakness candidate task | Weakness candidate / merge suggestion | async | required | required | source_refs/input_refs owner 必须匹配当前 actor | CreateWeaknessCandidateTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | WeaknessCandidate, WeaknessMergeSuggestion, WeaknessSeverityAssessment, AiTask, IdempotencyRecord | P-WEAKNESS-001, P-WEAKNESS-002, P-WEAKNESS-003, P-WEAKNESS-004, P-JOBMATCH-004, P-POLISH-011 | api.weakness_candidate.create.candidate_not_formal |
| API-WEAKNESS-003 | POST | /api/v1/weakness-candidates/{candidate_id}/confirmations | Confirm weakness candidate | Weakness candidate / merge suggestion | sync | required | required | candidate 和 target_weakness owner 必须匹配当前 actor, 确认前不得写正式 Weakness | ConfirmCandidateRequest | WeaknessResponse | ApiErrorEnvelope | WeaknessCandidate, Weakness, WeaknessStatusHistory, UserConfirmationRef, AuditEvent, IdempotencyRecord | P-WEAKNESS-001, P-WEAKNESS-002, P-WEAKNESS-004 | api.weakness_candidate.confirm.formal_requires_user_action |
| API-TRAINING-001 | GET | /api/v1/training-suggestions | List training suggestions | Training suggestion | sync | required | not required | 按 actor owner scope 过滤训练建议 | N/A (Query Params) | TrainingSuggestionResponse[] | ApiErrorEnvelope | TrainingRecommendation, TrainingPriorityRanking, OwnerRef | P-TRAINING-001, P-TRAINING-002 | api.training_suggestion.list.owner_scoped |
| API-TRAINING-002 | POST | /api/v1/training-suggestions | Create training suggestion task | Training suggestion | async | required | required | source_refs/weakness_ids/asset_ids owner 必须匹配当前 actor | CreateTrainingSuggestionTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | TrainingRecommendation, TrainingPriorityRanking, AiTask, IdempotencyRecord | P-TRAINING-001, P-TRAINING-002 | api.training_suggestion.create.no_auto_task |
| API-TRAINING-003 | POST | /api/v1/training-suggestions/{suggestion_id}/confirmations | Confirm training suggestion | Training suggestion | sync | required | required | suggestion.owner_ref 必须匹配当前 actor, 确认不等于自动启动 TrainingTask | ConfirmCandidateRequest | TrainingSuggestionResponse | ApiErrorEnvelope | TrainingRecommendation, UserConfirmationRef, AuditEvent, IdempotencyRecord | P-TRAINING-001 | api.training_suggestion.confirm.no_auto_training_task |
| API-AITASK-001 | POST | /api/v1/ai-tasks | Create generic AI task | AI task | async | required | required | target_ref/input_refs owner 必须匹配当前 actor, contract_ids 必须已登记 | CreateAiTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | AiTask, AiTaskResult, LlmValidationResult, IdempotencyRecord | 已登记 P-* | api.ai_task.create.contract_id_registered |
| API-AITASK-002 | GET | /api/v1/ai-tasks/{ai_task_id} | Get AI task status | AI task | sync | required | not required | ai_task.owner_ref 必须匹配当前 actor | N/A | AiTaskStatusResponse | ApiErrorEnvelope | AiTask, AiTaskResult, LlmValidationResult, TraceRef | 已登记 P-* | api.ai_task.status.owner_scoped |
| API-AITASK-003 | GET | /api/v1/ai-tasks/{ai_task_id}/result | Get AI task result | AI task | sync | required | not required | ai_task.owner_ref 必须匹配当前 actor, 不返回 provider payload | N/A | AiTaskResultResponse | ApiErrorEnvelope | AiTaskResult, CandidateRef, SuggestionRef, EvidenceRef, TraceRef | 已登记 P-* | api.ai_task.result.no_provider_payload |
| API-AITASK-004 | POST | /api/v1/ai-tasks/{ai_task_id}/retry | Retry AI task | AI task | async | required | required | ai_task.owner_ref 必须匹配当前 actor, retry 不得扩大上下文 | RetryAiTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | AiTask, AiTaskResult, LlmFailureRecord, IdempotencyRecord | 已登记 P-* | api.ai_task.retry.idempotent_and_scope_safe |
| API-AITASK-005 | POST | /api/v1/ai-tasks/{ai_task_id}/cancel | Cancel AI task | AI task | sync | required | required | ai_task.owner_ref 必须匹配当前 actor, cancel 后不得 late write formal object | CancelAiTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | AiTask, AuditEvent, IdempotencyRecord | 已登记 P-* | api.ai_task.cancel.no_late_write |


## 7. 逐接口字段级详情

通用约束：所有接口默认 `Auth: required`，成功响应使用 `ApiSuccessEnvelope`，错误响应使用 `ApiErrorEnvelope`。`Sensitive / Loggable` 中 `sensitive_not_loggable` 表示字段可持久化但不得进入日志、trace 明文或 copy event；`sensitive_summary_only` 表示只允许脱敏摘要进入可观测性或前端摘要。

### API-RESUME-001 List resumes

Method: GET
Path: `/api/v1/resumes`
Domain: Resume
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: 按 actor owner scope 过滤列表
Related Data Objects: Resume, ResumeVersion, OwnerRef
Related Prompt Contracts: N/A
F7 Contract Tests: api.resume.list.owner_scoped, api.resume.list.validation_failed, api.resume.list.cross_user_denied

#### Path Params

N/A

#### Query Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume | 资源域 | loggable |
| data.resume_id | 是 | string | res_* | 简历 ID | loggable |
| data.title | 是 | string | 1..120 | 简历标题 | loggable |
| data.target_direction | 否 | string | <=120 | 目标方向 | loggable |
| data.current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本引用 | loggable |
| data.module_summary.project_experience_count | 是 | integer | >=0 | 项目经历模块数量 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| meta.pagination | 否 | PaginationMeta | cursor pagination | 列表分页信息 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.resume.list.owner_scoped`
- `api.resume.list.validation_failed`
- `api.resume.list.cross_user_denied`

### API-RESUME-002 Create resume

Method: POST
Path: `/api/v1/resumes`
Domain: Resume
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: 服务端从 session 推导 owner, 请求体不得包含 owner_id
Related Data Objects: Resume, ResumeVersion, ResumeModule, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.resume.create.success, api.resume.create.validation_failed, api.resume.create.cross_user_denied, api.resume.create.idempotency_required, api.resume.create.idempotency_conflict

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 是 | string | 1..120 | 简历标题 | loggable |
| markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| target_direction | 否 | string | <=120 | 目标方向 | loggable |
| client_draft_id | 否 | string | client generated | 客户端草稿 ID | loggable |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume | 资源域 | loggable |
| data.resume_id | 是 | string | res_* | 简历 ID | loggable |
| data.title | 是 | string | 1..120 | 简历标题 | loggable |
| data.markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本 | loggable |
| data.modules[] | 是 | ResumeProjectExperienceModule[] | includes project_experience | 简历模块 | sensitive_summary_only |
| data.source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.resume.create.success`
- `api.resume.create.validation_failed`
- `api.resume.create.cross_user_denied`
- `api.resume.create.idempotency_required`
- `api.resume.create.idempotency_conflict`

### API-RESUME-003 Get resume detail

Method: GET
Path: `/api/v1/resumes/{resume_id}`
Domain: Resume
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: resume.owner_ref 必须匹配当前 actor
Related Data Objects: Resume, ResumeVersion, ResumeModule, OwnerRef
Related Prompt Contracts: N/A
F7 Contract Tests: api.resume.get.cross_user_denied, api.resume.get.validation_failed, api.resume.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | resume_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume | 资源域 | loggable |
| data.resume_id | 是 | string | res_* | 简历 ID | loggable |
| data.title | 是 | string | 1..120 | 简历标题 | loggable |
| data.markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本 | loggable |
| data.modules[] | 是 | ResumeProjectExperienceModule[] | includes project_experience | 简历模块 | sensitive_summary_only |
| data.source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.resume.get.cross_user_denied`
- `api.resume.get.validation_failed`
- `api.resume.get.cross_user_denied`

### API-RESUME-004 Update resume

Method: PATCH
Path: `/api/v1/resumes/{resume_id}`
Domain: Resume
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: resume.owner_ref 与 base_version_ref owner 一致
Related Data Objects: Resume, ResumeVersion, ResumeModule, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.resume.update.stale_version_conflict, api.resume.update.validation_failed, api.resume.update.cross_user_denied, api.resume.update.idempotency_required, api.resume.update.idempotency_conflict, api.resume.update.stale_version_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | resume_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 否 | string | 1..120 | 新标题 | loggable |
| markdown_text | 否 | string | 1..60000 | 新简历正文 | sensitive_not_loggable |
| content_markdown | 否 | string | 1..20000 | 项目经历模块正文 | sensitive_not_loggable |
| base_version_ref | 是 | VersionRef | ResumeVersion | 基础版本 | loggable |
| change_reason | 否 | string | <=240 | 变更原因 | loggable |

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume | 资源域 | loggable |
| data.resume_id | 是 | string | res_* | 简历 ID | loggable |
| data.title | 是 | string | 1..120 | 简历标题 | loggable |
| data.markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本 | loggable |
| data.modules[] | 是 | ResumeProjectExperienceModule[] | includes project_experience | 简历模块 | sensitive_summary_only |
| data.source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.resume.update.stale_version_conflict`
- `api.resume.update.validation_failed`
- `api.resume.update.cross_user_denied`
- `api.resume.update.idempotency_required`
- `api.resume.update.idempotency_conflict`
- `api.resume.update.stale_version_conflict`

### API-RESUME-005 List resume project experience modules

Method: GET
Path: `/api/v1/resumes/{resume_id}/modules/project-experiences`
Domain: Resume project experiences
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: resume.owner_ref 必须匹配当前 actor, project experience 不是一级资源
Related Data Objects: ResumeModule(type=project_experience), ResumeVersion, SourceAvailability
Related Prompt Contracts: N/A
F7 Contract Tests: api.resume_project_experience.list.not_top_level, api.resume_project_experience.list.validation_failed, api.resume_project_experience.list.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | resume_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| version_id | 否 | string | ResumeVersion id | 读取指定版本模块；缺省读取当前版本 | loggable |

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume project experiences | 资源域 | loggable |
| data.module_id | 是 | string | mod_* | 模块 ID | loggable |
| data.resume_id | 是 | string | res_* | 所属简历 | loggable |
| data.module_type | 是 | enum | project_experience | 项目经历模块 | loggable |
| data.content_markdown | 是 | string | 1..20000 | 模块正文 | sensitive_not_loggable |
| data.base_version_ref | 是 | VersionRef | ResumeVersion | 来源版本 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| meta.pagination | 否 | PaginationMeta | cursor pagination | 列表分页信息 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.resume_project_experience.list.not_top_level`
- `api.resume_project_experience.list.validation_failed`
- `api.resume_project_experience.list.cross_user_denied`

### API-RESUME-006 Update resume project experience module

Method: PATCH
Path: `/api/v1/resumes/{resume_id}/modules/project-experiences/{module_id}`
Domain: Resume project experiences
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: module 必须属于当前 resume 且 owner 匹配
Related Data Objects: ResumeModule, ResumeVersion, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.resume_project_experience.update.versioned, api.resume_project_experience.update.validation_failed, api.resume_project_experience.update.cross_user_denied, api.resume_project_experience.update.idempotency_required, api.resume_project_experience.update.idempotency_conflict, api.resume_project_experience.update.stale_version_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | resume_id path id | 路径资源标识；服务端必须做 owner check | loggable |
| module_id | 是 | string | module_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 否 | string | 1..120 | 新标题 | loggable |
| markdown_text | 否 | string | 1..60000 | 新简历正文 | sensitive_not_loggable |
| content_markdown | 否 | string | 1..20000 | 项目经历模块正文 | sensitive_not_loggable |
| base_version_ref | 是 | VersionRef | ResumeVersion | 基础版本 | loggable |
| change_reason | 否 | string | <=240 | 变更原因 | loggable |

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume project experiences | 资源域 | loggable |
| data.module_id | 是 | string | mod_* | 模块 ID | loggable |
| data.resume_id | 是 | string | res_* | 所属简历 | loggable |
| data.module_type | 是 | enum | project_experience | 项目经历模块 | loggable |
| data.content_markdown | 是 | string | 1..20000 | 模块正文 | sensitive_not_loggable |
| data.base_version_ref | 是 | VersionRef | ResumeVersion | 来源版本 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.resume_project_experience.update.versioned`
- `api.resume_project_experience.update.validation_failed`
- `api.resume_project_experience.update.cross_user_denied`
- `api.resume_project_experience.update.idempotency_required`
- `api.resume_project_experience.update.idempotency_conflict`
- `api.resume_project_experience.update.stale_version_conflict`

### API-JOB-001 List jobs

Method: GET
Path: `/api/v1/jobs`
Domain: Job / JD
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: 按 actor owner scope 过滤列表
Related Data Objects: Job, JobVersion, JobStatus, OwnerRef
Related Prompt Contracts: N/A
F7 Contract Tests: api.job.list.owner_scoped, api.job.list.validation_failed, api.job.list.cross_user_denied

#### Path Params

N/A

#### Query Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Job / JD | 资源域 | loggable |
| data.job_id | 是 | string | job_* | 岗位 ID | loggable |
| data.title | 是 | string | 1..160 | 岗位名称 | loggable |
| data.company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| data.application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |
| data.current_version_ref | 是 | VersionRef | JobVersion | 当前版本 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| meta.pagination | 否 | PaginationMeta | cursor pagination | 列表分页信息 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.job.list.owner_scoped`
- `api.job.list.validation_failed`
- `api.job.list.cross_user_denied`

### API-JOB-002 Create job manually

Method: POST
Path: `/api/v1/jobs`
Domain: Job / JD
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: 服务端从 session 推导 owner, 不接受外部材料解析
Related Data Objects: Job, JobVersion, JobStatus, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.job.create.manual_only, api.job.create.validation_failed, api.job.create.cross_user_denied, api.job.create.idempotency_required, api.job.create.idempotency_conflict

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 是 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| department | 否 | string | <=160 | 部门 | sensitive_summary_only |
| responsibilities | 是 | string[] | 1..100 items | 职责 | sensitive_not_loggable |
| requirements | 是 | string[] | 1..100 items | 要求 | sensitive_not_loggable |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Job / JD | 资源域 | loggable |
| data.job_id | 是 | string | job_* | 岗位 ID | loggable |
| data.title | 是 | string | 1..160 | 岗位名称 | loggable |
| data.company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| data.responsibilities | 是 | string[] | item<=1000 | 职责列表 | sensitive_not_loggable |
| data.requirements | 是 | string[] | item<=1000 | 要求列表 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | JobVersion | 当前版本 | loggable |
| data.source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.job.create.manual_only`
- `api.job.create.validation_failed`
- `api.job.create.cross_user_denied`
- `api.job.create.idempotency_required`
- `api.job.create.idempotency_conflict`

### API-JOB-003 Get job detail

Method: GET
Path: `/api/v1/jobs/{job_id}`
Domain: Job / JD
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: job.owner_ref 必须匹配当前 actor
Related Data Objects: Job, JobVersion, JobStatus, OwnerRef
Related Prompt Contracts: N/A
F7 Contract Tests: api.job.get.cross_user_denied, api.job.get.validation_failed, api.job.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| job_id | 是 | string | job_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Job / JD | 资源域 | loggable |
| data.job_id | 是 | string | job_* | 岗位 ID | loggable |
| data.title | 是 | string | 1..160 | 岗位名称 | loggable |
| data.company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| data.responsibilities | 是 | string[] | item<=1000 | 职责列表 | sensitive_not_loggable |
| data.requirements | 是 | string[] | item<=1000 | 要求列表 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | JobVersion | 当前版本 | loggable |
| data.source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.job.get.cross_user_denied`
- `api.job.get.validation_failed`
- `api.job.get.cross_user_denied`

### API-JOB-004 Update job

Method: PATCH
Path: `/api/v1/jobs/{job_id}`
Domain: Job / JD
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: job.owner_ref 与 base_version_ref owner 一致
Related Data Objects: Job, JobVersion, JobStatus, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.job.update.stale_version_conflict, api.job.update.validation_failed, api.job.update.cross_user_denied, api.job.update.idempotency_required, api.job.update.idempotency_conflict, api.job.update.stale_version_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| job_id | 是 | string | job_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 否 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| responsibilities | 否 | string[] | <=100 items | 职责 | sensitive_not_loggable |
| requirements | 否 | string[] | <=100 items | 要求 | sensitive_not_loggable |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |
| base_version_ref | 是 | VersionRef | JobVersion | 基础版本 | loggable |

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Job / JD | 资源域 | loggable |
| data.job_id | 是 | string | job_* | 岗位 ID | loggable |
| data.title | 是 | string | 1..160 | 岗位名称 | loggable |
| data.company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| data.responsibilities | 是 | string[] | item<=1000 | 职责列表 | sensitive_not_loggable |
| data.requirements | 是 | string[] | item<=1000 | 要求列表 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | JobVersion | 当前版本 | loggable |
| data.source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.job.update.stale_version_conflict`
- `api.job.update.validation_failed`
- `api.job.update.cross_user_denied`
- `api.job.update.idempotency_required`
- `api.job.update.idempotency_conflict`
- `api.job.update.stale_version_conflict`

### API-BINDING-001 Create resume-job binding

Method: POST
Path: `/api/v1/resume-job-bindings`
Domain: Resume-job binding
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: resume、job、version 必须同 owner
Related Data Objects: JobResumeBinding, ResumeVersion, JobVersion, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.binding.create.cross_owner_denied, api.binding.create.validation_failed, api.binding.create.cross_user_denied, api.binding.create.idempotency_required, api.binding.create.idempotency_conflict

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 是 | string | job_* | 岗位 ID | loggable |
| resume_version_id | 否 | string | version id | 指定简历版本 | loggable |
| job_version_id | 否 | string | version id | 指定岗位版本 | loggable |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume-job binding | 资源域 | loggable |
| data.binding_id | 是 | string | bind_* | 绑定 ID | loggable |
| data.resume_ref | 是 | VersionRef | ResumeVersion | 绑定简历版本 | loggable |
| data.job_ref | 是 | VersionRef | JobVersion | 绑定岗位版本 | loggable |
| data.binding_status | 是 | enum | active / inactive | 绑定状态 | loggable |
| data.created_at | 是 | datetime | ISO-8601 | 创建时间 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.binding.create.cross_owner_denied`
- `api.binding.create.validation_failed`
- `api.binding.create.cross_user_denied`
- `api.binding.create.idempotency_required`
- `api.binding.create.idempotency_conflict`

### API-JOBMATCH-001 Create job match analysis task

Method: POST
Path: `/api/v1/job-match-analyses`
Domain: Job match analysis
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: binding/job/resume/version 必须同 owner 且 source_available
Related Data Objects: JobMatchAnalysis, MatchScore, WeaknessCandidate, AiTask, IdempotencyRecord
Related Prompt Contracts: P-JOBMATCH-001, P-JOBMATCH-002, P-JOBMATCH-003, P-JOBMATCH-004
F7 Contract Tests: api.job_match.create.async_success, api.job_match.create.validation_failed, api.job_match.create.cross_user_denied, api.job_match.create.idempotency_required, api.job_match.create.idempotency_conflict, api.job_match.create.source_unavailable, api.job_match.create.provider_unavailable, api.job_match.create.task_timeout

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| binding_id | 否 | string | bind_* | 绑定 ID | loggable |
| resume_id | 条件 | string | res_* | 无 binding 时必填 | loggable |
| job_id | 条件 | string | job_* | 无 binding 时必填 | loggable |
| requested_outputs | 否 | string[] | score / points / weakness_candidates | 请求输出 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Job match analysis | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.job_match.create.async_success`
- `api.job_match.create.validation_failed`
- `api.job_match.create.cross_user_denied`
- `api.job_match.create.idempotency_required`
- `api.job_match.create.idempotency_conflict`
- `api.job_match.create.source_unavailable`
- `api.job_match.create.provider_unavailable`
- `api.job_match.create.task_timeout`

### API-JOBMATCH-002 Get job match analysis

Method: GET
Path: `/api/v1/job-match-analyses/{analysis_id}`
Domain: Job match analysis
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: analysis.owner_ref 必须匹配当前 actor
Related Data Objects: JobMatchAnalysis, ScoreResult, EvidenceRef, TraceRef, SourceAvailability
Related Prompt Contracts: P-JOBMATCH-*
F7 Contract Tests: api.job_match.get.low_confidence_visible, api.job_match.get.validation_failed, api.job_match.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| analysis_id | 是 | string | analysis_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Job match analysis | 资源域 | loggable |
| data.analysis_id | 是 | string | jma_* | 分析 ID | loggable |
| data.binding_ref | 是 | string | bind_* | 绑定引用 | loggable |
| data.score.score_value | 是 | integer | 0..100 | 匹配分 | loggable |
| data.match_points[] | 是 | object[] | >=0 | 匹配点 | sensitive_summary_only |
| data.mismatch_points[] | 是 | object[] | >=0 | 不匹配点 | sensitive_summary_only |
| data.improvement_points[] | 是 | object[] | >=0 | 加强点 | sensitive_summary_only |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.job_match.get.low_confidence_visible`
- `api.job_match.get.validation_failed`
- `api.job_match.get.cross_user_denied`

### API-POLISH-001 Create polish session

Method: POST
Path: `/api/v1/polish-sessions`
Domain: Polish session
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: resume/job/binding/source_refs 必须同 owner
Related Data Objects: InterviewSession, PolishSessionDetail, ProgressTree, IdempotencyRecord
Related Prompt Contracts: P-POLISH-001
F7 Contract Tests: api.polish_session.create.success, api.polish_session.create.validation_failed, api.polish_session.create.cross_user_denied, api.polish_session.create.idempotency_required, api.polish_session.create.idempotency_conflict

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| binding_id | 否 | string | bind_* | 绑定 ID | loggable |
| topic_hint | 否 | string | <=240 | 打磨主题提示 | sensitive_summary_only |
| source_refs | 否 | SourceRef[] | owner scoped | 增强来源 | loggable |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Polish session | 资源域 | loggable |
| data.session_id | 是 | string | ses_* | 会话 ID | loggable |
| data.mode | 是 | enum | polish / pressure | 模式 | loggable |
| data.session_status | 是 | enum | created / running / paused / completed / failed | 会话状态 | loggable |
| data.current_question_ref | 否 | string | question_* | 当前题目 | loggable |
| data.progress_position_ref | 否 | string | progress_pos_* | 进展位置 | loggable |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.polish_session.create.success`
- `api.polish_session.create.validation_failed`
- `api.polish_session.create.cross_user_denied`
- `api.polish_session.create.idempotency_required`
- `api.polish_session.create.idempotency_conflict`

### API-POLISH-002 Get polish session

Method: GET
Path: `/api/v1/polish-sessions/{session_id}`
Domain: Polish session
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: session.owner_ref 必须匹配当前 actor
Related Data Objects: InterviewSession, PolishSessionDetail, ProgressTree, SessionSummary
Related Prompt Contracts: N/A
F7 Contract Tests: api.polish_session.get.owner_scoped, api.polish_session.get.validation_failed, api.polish_session.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Polish session | 资源域 | loggable |
| data.session_id | 是 | string | ses_* | 会话 ID | loggable |
| data.mode | 是 | enum | polish / pressure | 模式 | loggable |
| data.session_status | 是 | enum | created / running / paused / completed / failed | 会话状态 | loggable |
| data.current_question_ref | 否 | string | question_* | 当前题目 | loggable |
| data.progress_position_ref | 否 | string | progress_pos_* | 进展位置 | loggable |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.polish_session.get.owner_scoped`
- `api.polish_session.get.validation_failed`
- `api.polish_session.get.cross_user_denied`

### API-POLISH-003 Create polish question task

Method: POST
Path: `/api/v1/polish-sessions/{session_id}/questions`
Domain: Question
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: session、progress_node、source_refs 必须同 owner
Related Data Objects: Question, AiTask, RAGContextAssembly, IdempotencyRecord
Related Prompt Contracts: P-POLISH-002, P-SHARED-*
F7 Contract Tests: api.polish_question.create.async_success, api.polish_question.create.validation_failed, api.polish_question.create.cross_user_denied, api.polish_question.create.idempotency_required, api.polish_question.create.idempotency_conflict, api.polish_question.create.source_unavailable, api.polish_question.create.provider_unavailable, api.polish_question.create.task_timeout

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| progress_node_ref | 否 | TraceRef | node ref | 进展节点 | loggable |
| topic_ref | 否 | TraceRef | topic ref | 主题引用 | loggable |
| question_type | 否 | enum | first / follow_up / polish | 题目类型 | loggable |
| answer_id | 否 | string | ans_* | 追问时的上一回答 | loggable |
| difficulty_hint | 否 | enum | easy / medium / hard / adaptive | 难度提示 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Question | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.polish_question.create.async_success`
- `api.polish_question.create.validation_failed`
- `api.polish_question.create.cross_user_denied`
- `api.polish_question.create.idempotency_required`
- `api.polish_question.create.idempotency_conflict`
- `api.polish_question.create.source_unavailable`
- `api.polish_question.create.provider_unavailable`
- `api.polish_question.create.task_timeout`

### API-POLISH-004 Create polish answer

Method: POST
Path: `/api/v1/polish-sessions/{session_id}/answers`
Domain: Answer
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: session/question.owner_ref 必须匹配当前 actor
Related Data Objects: Answer, Question, InterviewSession, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.polish_answer.create.validation_failed, api.polish_answer.create.validation_failed, api.polish_answer.create.cross_user_denied, api.polish_answer.create.idempotency_required, api.polish_answer.create.idempotency_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| answer_round | 否 | integer | >=1 | 轮次 | loggable |
| base_question_version_ref | 否 | VersionRef | Question | 题目版本 | loggable |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Answer | 资源域 | loggable |
| data.answer_id | 是 | string | ans_* | 回答 ID | loggable |
| data.question_id | 是 | string | q_* | 题目 ID | loggable |
| data.answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| data.answer_round | 否 | integer | >=1 | 回答轮次 | loggable |
| data.created_at | 是 | datetime | ISO-8601 | 提交时间 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.polish_answer.create.validation_failed`
- `api.polish_answer.create.validation_failed`
- `api.polish_answer.create.cross_user_denied`
- `api.polish_answer.create.idempotency_required`
- `api.polish_answer.create.idempotency_conflict`

### API-POLISH-005 Create polish feedback task

Method: POST
Path: `/api/v1/polish-sessions/{session_id}/feedback`
Domain: Feedback
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: session/answer/evidence owner 必须匹配当前 actor
Related Data Objects: Feedback, ScoreResult, AssetCandidate, WeaknessCandidate, AiTask, IdempotencyRecord
Related Prompt Contracts: P-POLISH-003, P-POLISH-004, P-POLISH-005, P-POLISH-006, P-POLISH-007, P-POLISH-008, P-POLISH-009, P-POLISH-010, P-POLISH-011
F7 Contract Tests: api.polish_feedback.create.low_confidence_visible, api.polish_feedback.create.validation_failed, api.polish_feedback.create.cross_user_denied, api.polish_feedback.create.idempotency_required, api.polish_feedback.create.idempotency_conflict, api.polish_feedback.create.source_unavailable, api.polish_feedback.create.provider_unavailable, api.polish_feedback.create.task_timeout

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| requested_outputs | 否 | string[] | diagnosis / score / loss_points / reference_answer / knowledge / next_action / asset_candidate / weakness_candidate | 请求输出 | loggable |
| session_summary_ref | 否 | TraceRef | summary ref | 会话摘要 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Feedback | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.polish_feedback.create.low_confidence_visible`
- `api.polish_feedback.create.validation_failed`
- `api.polish_feedback.create.cross_user_denied`
- `api.polish_feedback.create.idempotency_required`
- `api.polish_feedback.create.idempotency_conflict`
- `api.polish_feedback.create.source_unavailable`
- `api.polish_feedback.create.provider_unavailable`
- `api.polish_feedback.create.task_timeout`

### API-PRESSURE-001 Create pressure session

Method: POST
Path: `/api/v1/pressure-sessions`
Domain: Pressure session
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: resume/job/binding/source_refs 必须同 owner
Related Data Objects: InterviewSession, PressureSessionDetail, ProgressTree, IdempotencyRecord
Related Prompt Contracts: P-PRESSURE-001
F7 Contract Tests: api.pressure_session.create.success, api.pressure_session.create.validation_failed, api.pressure_session.create.cross_user_denied, api.pressure_session.create.idempotency_required, api.pressure_session.create.idempotency_conflict

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| binding_id | 否 | string | bind_* | 绑定 ID | loggable |
| start_mode | 否 | enum | first_question / continue_from_weakness / manual_topic | 启动模式 | loggable |
| source_refs | 否 | SourceRef[] | owner scoped | 增强来源 | loggable |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Pressure session | 资源域 | loggable |
| data.session_id | 是 | string | ses_* | 会话 ID | loggable |
| data.mode | 是 | enum | polish / pressure | 模式 | loggable |
| data.session_status | 是 | enum | created / running / paused / completed / failed | 会话状态 | loggable |
| data.current_question_ref | 否 | string | question_* | 当前题目 | loggable |
| data.progress_position_ref | 否 | string | progress_pos_* | 进展位置 | loggable |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.pressure_session.create.success`
- `api.pressure_session.create.validation_failed`
- `api.pressure_session.create.cross_user_denied`
- `api.pressure_session.create.idempotency_required`
- `api.pressure_session.create.idempotency_conflict`

### API-PRESSURE-002 Get pressure session

Method: GET
Path: `/api/v1/pressure-sessions/{session_id}`
Domain: Pressure session
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: session.owner_ref 必须匹配当前 actor
Related Data Objects: InterviewSession, PressureSessionDetail, ProgressTree, SessionSummary
Related Prompt Contracts: N/A
F7 Contract Tests: api.pressure_session.get.owner_scoped, api.pressure_session.get.validation_failed, api.pressure_session.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Pressure session | 资源域 | loggable |
| data.session_id | 是 | string | ses_* | 会话 ID | loggable |
| data.mode | 是 | enum | polish / pressure | 模式 | loggable |
| data.session_status | 是 | enum | created / running / paused / completed / failed | 会话状态 | loggable |
| data.current_question_ref | 否 | string | question_* | 当前题目 | loggable |
| data.progress_position_ref | 否 | string | progress_pos_* | 进展位置 | loggable |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.pressure_session.get.owner_scoped`
- `api.pressure_session.get.validation_failed`
- `api.pressure_session.get.cross_user_denied`

### API-PRESSURE-003 Create pressure question task

Method: POST
Path: `/api/v1/pressure-sessions/{session_id}/questions`
Domain: Question
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: session/answer/source_refs 必须同 owner
Related Data Objects: Question, AiTask, PressureSessionDetail, IdempotencyRecord
Related Prompt Contracts: P-PRESSURE-002, P-PRESSURE-004, P-PRESSURE-005
F7 Contract Tests: api.pressure_question.create.async_success, api.pressure_question.create.validation_failed, api.pressure_question.create.cross_user_denied, api.pressure_question.create.idempotency_required, api.pressure_question.create.idempotency_conflict, api.pressure_question.create.source_unavailable, api.pressure_question.create.provider_unavailable, api.pressure_question.create.task_timeout

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| progress_node_ref | 否 | TraceRef | node ref | 进展节点 | loggable |
| topic_ref | 否 | TraceRef | topic ref | 主题引用 | loggable |
| question_type | 否 | enum | first / follow_up / polish | 题目类型 | loggable |
| answer_id | 否 | string | ans_* | 追问时的上一回答 | loggable |
| difficulty_hint | 否 | enum | easy / medium / hard / adaptive | 难度提示 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Question | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.pressure_question.create.async_success`
- `api.pressure_question.create.validation_failed`
- `api.pressure_question.create.cross_user_denied`
- `api.pressure_question.create.idempotency_required`
- `api.pressure_question.create.idempotency_conflict`
- `api.pressure_question.create.source_unavailable`
- `api.pressure_question.create.provider_unavailable`
- `api.pressure_question.create.task_timeout`

### API-PRESSURE-004 Create pressure answer

Method: POST
Path: `/api/v1/pressure-sessions/{session_id}/answers`
Domain: Answer
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: session/question.owner_ref 必须匹配当前 actor
Related Data Objects: Answer, Question, InterviewSession, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.pressure_answer.create.success, api.pressure_answer.create.validation_failed, api.pressure_answer.create.cross_user_denied, api.pressure_answer.create.idempotency_required, api.pressure_answer.create.idempotency_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| answer_round | 否 | integer | >=1 | 轮次 | loggable |
| base_question_version_ref | 否 | VersionRef | Question | 题目版本 | loggable |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Answer | 资源域 | loggable |
| data.answer_id | 是 | string | ans_* | 回答 ID | loggable |
| data.question_id | 是 | string | q_* | 题目 ID | loggable |
| data.answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| data.answer_round | 否 | integer | >=1 | 回答轮次 | loggable |
| data.created_at | 是 | datetime | ISO-8601 | 提交时间 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 Contract Tests

- `api.pressure_answer.create.success`
- `api.pressure_answer.create.validation_failed`
- `api.pressure_answer.create.cross_user_denied`
- `api.pressure_answer.create.idempotency_required`
- `api.pressure_answer.create.idempotency_conflict`

### API-PRESSURE-005 Create pressure feedback task

Method: POST
Path: `/api/v1/pressure-sessions/{session_id}/feedback`
Domain: Feedback
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: session/answer/evidence owner 必须匹配当前 actor
Related Data Objects: Feedback, ScoreResult, SessionSummary, AiTask, IdempotencyRecord
Related Prompt Contracts: P-PRESSURE-003, P-PRESSURE-006, P-PRESSURE-007, P-PRESSURE-008, P-PRESSURE-009
F7 Contract Tests: api.pressure_feedback.create.generation_failed_visible, api.pressure_feedback.create.validation_failed, api.pressure_feedback.create.cross_user_denied, api.pressure_feedback.create.idempotency_required, api.pressure_feedback.create.idempotency_conflict, api.pressure_feedback.create.source_unavailable, api.pressure_feedback.create.provider_unavailable, api.pressure_feedback.create.task_timeout

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| requested_outputs | 否 | string[] | diagnosis / score / loss_points / reference_answer / knowledge / next_action / asset_candidate / weakness_candidate | 请求输出 | loggable |
| session_summary_ref | 否 | TraceRef | summary ref | 会话摘要 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Feedback | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.pressure_feedback.create.generation_failed_visible`
- `api.pressure_feedback.create.validation_failed`
- `api.pressure_feedback.create.cross_user_denied`
- `api.pressure_feedback.create.idempotency_required`
- `api.pressure_feedback.create.idempotency_conflict`
- `api.pressure_feedback.create.source_unavailable`
- `api.pressure_feedback.create.provider_unavailable`
- `api.pressure_feedback.create.task_timeout`

### API-PROGRESS-001 Get progress tree

Method: GET
Path: `/api/v1/interview-sessions/{session_id}/progress-tree`
Domain: Progress tree
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: session.owner_ref 必须匹配当前 actor
Related Data Objects: ProgressTree, ProgressNode, ProgressPosition, SourceAvailability
Related Prompt Contracts: N/A
F7 Contract Tests: api.progress_tree.get.owner_scoped, api.progress_tree.get.validation_failed, api.progress_tree.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Progress tree | 资源域 | loggable |
| data.progress_tree_id | 是 | string | pt_* | 进展树 ID | loggable |
| data.session_id | 是 | string | ses_* | 会话 ID | loggable |
| data.nodes[] | 是 | object[] | >=0 | 节点列表 | loggable |
| data.current_position.node_id | 否 | string | node_* | 当前位置 | loggable |
| data.source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.progress_tree.get.owner_scoped`
- `api.progress_tree.get.validation_failed`
- `api.progress_tree.get.cross_user_denied`

### API-SCORING-001 Create scoring task

Method: POST
Path: `/api/v1/scoring-results`
Domain: Scoring result
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: target/input_refs owner 必须匹配当前 actor, hidden scoring rules 不暴露
Related Data Objects: ScoreResult, ScoreRuleVersion, ScoreExplanation, AiTask, IdempotencyRecord
Related Prompt Contracts: P-JOBMATCH-002, P-POLISH-004, P-PRESSURE-008, P-REPORT-002
F7 Contract Tests: api.scoring.create.no_hidden_rules, api.scoring.create.validation_failed, api.scoring.create.cross_user_denied, api.scoring.create.idempotency_required, api.scoring.create.idempotency_conflict, api.scoring.create.source_unavailable, api.scoring.create.provider_unavailable, api.scoring.create.task_timeout

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| target_type | 是 | enum | job_match / answer / session / report / review / training_result | 评分目标类型 | loggable |
| target_id | 是 | string | typed id | 评分目标 ID | loggable |
| score_type | 是 | enum | job_match / polish_round / pressure_session / report_section | 评分类型 | loggable |
| input_refs | 是 | SourceRef[] | owner scoped | 输入引用 | loggable |
| score_rule_version_id | 否 | string | rule version | 指定评分规则版本 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Scoring result | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.scoring.create.no_hidden_rules`
- `api.scoring.create.validation_failed`
- `api.scoring.create.cross_user_denied`
- `api.scoring.create.idempotency_required`
- `api.scoring.create.idempotency_conflict`
- `api.scoring.create.source_unavailable`
- `api.scoring.create.provider_unavailable`
- `api.scoring.create.task_timeout`

### API-SCORING-002 Get scoring result

Method: GET
Path: `/api/v1/scoring-results/{score_result_id}`
Domain: Scoring result
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: score_result.owner_ref 必须匹配当前 actor
Related Data Objects: ScoreResult, ScoreRuleVersion, EvidenceRef, TraceRef, LowConfidenceFlag
Related Prompt Contracts: P-JOBMATCH-002, P-POLISH-004, P-PRESSURE-008, P-REPORT-002
F7 Contract Tests: api.scoring.get.no_exact_probability, api.scoring.get.validation_failed, api.scoring.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| score_result_id | 是 | string | score_result_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Scoring result | 资源域 | loggable |
| data.score_result_id | 是 | string | score_* | 评分 ID | loggable |
| data.target_ref | 是 | TraceRef | typed ref | 评分目标 | loggable |
| data.score_value | 是 | integer | 0..100 | 0-100 产品刻度 | loggable |
| data.score_scale | 是 | enum | 0_100_product_scale | 分数刻度 | loggable |
| data.score_version | 是 | string | semver/date | 评分版本 | loggable |
| data.rubric_version | 是 | string | semver/date | Rubric 版本 | loggable |
| data.confidence_level | 是 | enum | high / medium / low / insufficient | 置信度 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.scoring.get.no_exact_probability`
- `api.scoring.get.validation_failed`
- `api.scoring.get.cross_user_denied`

### API-REPORT-001 Create report task

Method: POST
Path: `/api/v1/reports`
Domain: Report
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: session/input_refs owner 必须匹配当前 actor
Related Data Objects: InterviewReport, ReportSection, ScoreResult, AiTask, IdempotencyRecord
Related Prompt Contracts: P-REPORT-001, P-REPORT-002, P-REPORT-003, P-REPORT-004
F7 Contract Tests: api.report.create.async_success, api.report.create.validation_failed, api.report.create.cross_user_denied, api.report.create.idempotency_required, api.report.create.idempotency_conflict, api.report.create.source_unavailable, api.report.create.provider_unavailable, api.report.create.task_timeout, api.report.no_export_endpoint

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| report_type | 是 | enum | polish_summary / pressure_full | 报告类型 | loggable |
| input_refs | 否 | SourceRef[] | owner scoped | 输入引用 | loggable |
| requested_sections | 否 | string[] | summary / score / risk / weakness / training / copy_content | 请求分项 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Report | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |
| 404 / 405 | export_not_supported | 请求 PDF、Markdown file、Word、docx、download 或 export 语义 | use_copy_content | false | export.no_endpoint |

#### F7 Contract Tests

- `api.report.create.async_success`
- `api.report.create.validation_failed`
- `api.report.create.cross_user_denied`
- `api.report.create.idempotency_required`
- `api.report.create.idempotency_conflict`
- `api.report.create.source_unavailable`
- `api.report.create.provider_unavailable`
- `api.report.create.task_timeout`
- `api.report.no_export_endpoint`

### API-REPORT-002 Get report

Method: GET
Path: `/api/v1/reports/{report_id}`
Domain: Report
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: report.owner_ref 必须匹配当前 actor
Related Data Objects: InterviewReport, ReportSection, ScoreResult, SourceAvailability
Related Prompt Contracts: P-REPORT-*
F7 Contract Tests: api.report.get.copy_boundary_visible, api.report.get.validation_failed, api.report.get.cross_user_denied, api.report.no_export_endpoint

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | report_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Report | 资源域 | loggable |
| data.report_id | 是 | string | rep_* | 报告 ID | loggable |
| data.session_ref | 是 | string | ses_* | 会话引用 | loggable |
| data.report_status | 是 | enum | generating / available / partial / failed | 报告状态 | loggable |
| data.sections[] | 是 | object[] | >=0 | 报告分项 | sensitive_summary_only |
| data.score_ref | 否 | string | score_* | 总评分引用 | loggable |
| data.copy_content_available | 是 | boolean | true / false | 是否可复制 | loggable |
| data.source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |
| 404 / 405 | export_not_supported | 请求 PDF、Markdown file、Word、docx、download 或 export 语义 | use_copy_content | false | export.no_endpoint |

#### F7 Contract Tests

- `api.report.get.copy_boundary_visible`
- `api.report.get.validation_failed`
- `api.report.get.cross_user_denied`
- `api.report.no_export_endpoint`

### API-REPORT-003 Get report copy content

Method: GET
Path: `/api/v1/reports/{report_id}/copy-content`
Domain: Report copy content
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: report.owner_ref 必须匹配当前 actor, copy boundary 必须过滤敏感内容
Related Data Objects: CopyableContent, InterviewReport, AuditEvent, EvidenceRef
Related Prompt Contracts: P-REPORT-004
F7 Contract Tests: api.report.copy_content.no_export_artifact, api.report.copy_content.validation_failed, api.report.copy_content.cross_user_denied, api.report.no_export_endpoint

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | report_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Report copy content | 资源域 | loggable |
| data.report_id | 是 | string | rep_* | 报告 ID | loggable |
| data.copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| data.clipboard_blocks[] | 是 | object[] | plain text blocks | 剪贴板块 | sensitive_not_loggable |
| data.redaction_applied | 是 | boolean | true / false | 是否脱敏 | loggable |
| data.copy_boundary | 是 | enum | clipboard_only | 复制边界 | loggable |
| data.export_artifact | 是 | null | must be null | 不得返回导出物 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |
| 404 / 405 | export_not_supported | 请求 PDF、Markdown file、Word、docx、download 或 export 语义 | use_copy_content | false | export.no_endpoint |

#### F7 Contract Tests

- `api.report.copy_content.no_export_artifact`
- `api.report.copy_content.validation_failed`
- `api.report.copy_content.cross_user_denied`
- `api.report.no_export_endpoint`

### API-REPORT-004 Record report copy event

Method: POST
Path: `/api/v1/reports/{report_id}/copy-events`
Domain: Report copy content
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: report.owner_ref 必须匹配当前 actor, 审计不记录正文
Related Data Objects: CopyableContent, AuditEvent, IdempotencyRecord
Related Prompt Contracts: N/A
F7 Contract Tests: api.report.copy_event.audit_without_body, api.report.copy_event.validation_failed, api.report.copy_event.cross_user_denied, api.report.copy_event.idempotency_required, api.report.copy_event.idempotency_conflict, api.report.no_export_endpoint

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | report_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| copy_surface | 是 | enum | report_detail / review_detail | 复制位置 | loggable |
| client_event_id | 否 | string | client generated | 客户端事件 ID | loggable |
| selected_block_ids | 否 | string[] | copy block ids | 复制块 ID | loggable |

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Report copy content | 资源域 | loggable |
| data.report_id | 是 | string | rep_* | 报告 ID | loggable |
| data.copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| data.clipboard_blocks[] | 是 | object[] | plain text blocks | 剪贴板块 | sensitive_not_loggable |
| data.redaction_applied | 是 | boolean | true / false | 是否脱敏 | loggable |
| data.copy_boundary | 是 | enum | clipboard_only | 复制边界 | loggable |
| data.export_artifact | 是 | null | must be null | 不得返回导出物 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |
| 404 / 405 | export_not_supported | 请求 PDF、Markdown file、Word、docx、download 或 export 语义 | use_copy_content | false | export.no_endpoint |

#### F7 Contract Tests

- `api.report.copy_event.audit_without_body`
- `api.report.copy_event.validation_failed`
- `api.report.copy_event.cross_user_denied`
- `api.report.copy_event.idempotency_required`
- `api.report.copy_event.idempotency_conflict`
- `api.report.no_export_endpoint`

### API-REVIEW-001 Create mock interview review task

Method: POST
Path: `/api/v1/reviews/mock`
Domain: Mock interview review
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: session/report/input_refs owner 必须匹配当前 actor
Related Data Objects: MockInterviewReview, ReviewItem, AiTask, IdempotencyRecord
Related Prompt Contracts: P-REVIEW-001, P-REVIEW-004
F7 Contract Tests: api.review.mock.create.async_success, api.review.mock.create.validation_failed, api.review.mock.create.cross_user_denied, api.review.mock.create.idempotency_required, api.review.mock.create.idempotency_conflict, api.review.mock.create.source_unavailable, api.review.mock.create.provider_unavailable, api.review.mock.create.task_timeout

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | mock_session / report / real_interview_input | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| requested_outputs | 否 | string[] | review_summary / review_items / weakness_candidates / asset_candidates / training_suggestions | 请求输出 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Mock interview review | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.review.mock.create.async_success`
- `api.review.mock.create.validation_failed`
- `api.review.mock.create.cross_user_denied`
- `api.review.mock.create.idempotency_required`
- `api.review.mock.create.idempotency_conflict`
- `api.review.mock.create.source_unavailable`
- `api.review.mock.create.provider_unavailable`
- `api.review.mock.create.task_timeout`

### API-REVIEW-002 Create real interview input

Method: POST
Path: `/api/v1/reviews/real-inputs`
Domain: Real interview input / review
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: job/resume/input_refs owner 必须匹配当前 actor
Related Data Objects: RealInterviewInput, RealInterviewEvidence, UserConfirmationRef, IdempotencyRecord
Related Prompt Contracts: P-REVIEW-002
F7 Contract Tests: api.review.real_input.create.requires_confirmation, api.review.real_input.create.validation_failed, api.review.real_input.create.cross_user_denied, api.review.real_input.create.idempotency_required, api.review.real_input.create.idempotency_conflict

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| resume_id | 否 | string | res_* | 简历 ID | loggable |
| interview_time | 否 | datetime | ISO-8601 | 面试时间 | sensitive_summary_only |
| question_recall | 否 | string | <=20000 | 问题回忆 | sensitive_not_loggable |
| answer_recall | 否 | string | <=20000 | 回答回忆 | sensitive_not_loggable |
| interviewer_feedback | 否 | string | <=12000 | 面试官反馈 | sensitive_not_loggable |
| result_status | 否 | enum | unknown / passed / failed / pending / no_response | 结果状态 | sensitive_summary_only |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Real interview input / review | 资源域 | loggable |
| data.review_id | 是 | string | rev_* | 复盘 ID | loggable |
| data.review_type | 是 | enum | mock / real_input / real | 复盘类型 | loggable |
| data.review_status | 是 | enum | available / partial / low_confidence / failed | 状态 | loggable |
| data.items[] | 否 | object[] | >=0 | 题级复盘项 | sensitive_summary_only |
| data.source_refs[] | 是 | SourceRef[] | >=1 | 来源 | loggable |
| data.candidate_refs[] | 否 | CandidateRef[] | >=0 | 候选回流 | loggable |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.review.real_input.create.requires_confirmation`
- `api.review.real_input.create.validation_failed`
- `api.review.real_input.create.cross_user_denied`
- `api.review.real_input.create.idempotency_required`
- `api.review.real_input.create.idempotency_conflict`

### API-REVIEW-003 Create real interview review task

Method: POST
Path: `/api/v1/reviews/real`
Domain: Real interview input / review
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: real_interview_input owner 必须匹配当前 actor 且已确认
Related Data Objects: RealInterviewReview, ReviewItem, AiTask, IdempotencyRecord
Related Prompt Contracts: P-REVIEW-003, P-REVIEW-004
F7 Contract Tests: api.review.real.create.confirmed_input_only, api.review.real.create.validation_failed, api.review.real.create.cross_user_denied, api.review.real.create.idempotency_required, api.review.real.create.idempotency_conflict, api.review.real.create.source_unavailable, api.review.real.create.provider_unavailable, api.review.real.create.task_timeout

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | mock_session / report / real_interview_input | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| requested_outputs | 否 | string[] | review_summary / review_items / weakness_candidates / asset_candidates / training_suggestions | 请求输出 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Real interview input / review | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.review.real.create.confirmed_input_only`
- `api.review.real.create.validation_failed`
- `api.review.real.create.cross_user_denied`
- `api.review.real.create.idempotency_required`
- `api.review.real.create.idempotency_conflict`
- `api.review.real.create.source_unavailable`
- `api.review.real.create.provider_unavailable`
- `api.review.real.create.task_timeout`

### API-REVIEW-004 Get review

Method: GET
Path: `/api/v1/reviews/{review_id}`
Domain: Mock interview review / Real interview review
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: review.owner_ref 必须匹配当前 actor
Related Data Objects: MockInterviewReview, RealInterviewReview, ReviewItem, SourceAvailability
Related Prompt Contracts: P-REVIEW-*
F7 Contract Tests: api.review.get.low_confidence_visible, api.review.get.validation_failed, api.review.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | review_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Mock interview review / Real interview review | 资源域 | loggable |
| data.review_id | 是 | string | rev_* | 复盘 ID | loggable |
| data.review_type | 是 | enum | mock / real_input / real | 复盘类型 | loggable |
| data.review_status | 是 | enum | available / partial / low_confidence / failed | 状态 | loggable |
| data.items[] | 否 | object[] | >=0 | 题级复盘项 | sensitive_summary_only |
| data.source_refs[] | 是 | SourceRef[] | >=1 | 来源 | loggable |
| data.candidate_refs[] | 否 | CandidateRef[] | >=0 | 候选回流 | loggable |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.review.get.low_confidence_visible`
- `api.review.get.validation_failed`
- `api.review.get.cross_user_denied`

### API-ASSET-001 List assets

Method: GET
Path: `/api/v1/assets`
Domain: Asset
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: 按 actor owner scope 过滤正式资产
Related Data Objects: Asset, AssetVersion, AssetSource, OwnerRef
Related Prompt Contracts: N/A
F7 Contract Tests: api.asset.list.owner_scoped, api.asset.list.validation_failed, api.asset.list.cross_user_denied

#### Path Params

N/A

#### Query Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Asset | 资源域 | loggable |
| data.asset_id | 是 | string | asset_* | 资产 ID | loggable |
| data.current_version_ref | 是 | VersionRef | AssetVersion | 当前版本 | loggable |
| data.title | 是 | string | 1..160 | 资产标题 | loggable |
| data.asset_type | 是 | enum | answer_material / project_expression / job_material / feedback_summary | 资产类型 | loggable |
| data.status | 是 | enum | active / archived / disabled | 状态 | loggable |
| data.source_refs[] | 是 | SourceRef[] | >=1 | 来源 | loggable |
| meta.pagination | 否 | PaginationMeta | cursor pagination | 列表分页信息 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.asset.list.owner_scoped`
- `api.asset.list.validation_failed`
- `api.asset.list.cross_user_denied`

### API-ASSET-002 Create asset candidate task

Method: POST
Path: `/api/v1/asset-candidates`
Domain: Asset candidate / asset version suggestion
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: source_refs/target_asset owner 必须匹配当前 actor
Related Data Objects: AssetCandidate, AssetQualityHint, AssetVersionSuggestion, AiTask, IdempotencyRecord
Related Prompt Contracts: P-ASSET-001, P-ASSET-002, P-ASSET-003, P-POLISH-010
F7 Contract Tests: api.asset_candidate.create.candidate_not_formal, api.asset_candidate.create.validation_failed, api.asset_candidate.create.cross_user_denied, api.asset_candidate.create.idempotency_required, api.asset_candidate.create.idempotency_conflict, api.asset_candidate.create.source_unavailable, api.asset_candidate.create.provider_unavailable, api.asset_candidate.create.task_timeout

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | answer / feedback / report / review / training_result / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| target_asset_id | 否 | string | asset_* | 目标资产 | loggable |
| candidate_goal | 否 | enum | new_asset / version_update / quality_hint | 候选目标 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Asset candidate / asset version suggestion | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.asset_candidate.create.candidate_not_formal`
- `api.asset_candidate.create.validation_failed`
- `api.asset_candidate.create.cross_user_denied`
- `api.asset_candidate.create.idempotency_required`
- `api.asset_candidate.create.idempotency_conflict`
- `api.asset_candidate.create.source_unavailable`
- `api.asset_candidate.create.provider_unavailable`
- `api.asset_candidate.create.task_timeout`

### API-ASSET-003 Get asset candidate

Method: GET
Path: `/api/v1/asset-candidates/{candidate_id}`
Domain: Asset candidate / asset version suggestion
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: candidate.owner_ref 必须匹配当前 actor
Related Data Objects: AssetCandidate, AssetQualityHint, AssetVersionSuggestion, EvidenceRef, TraceRef
Related Prompt Contracts: P-ASSET-*
F7 Contract Tests: api.asset_candidate.get.low_confidence_visible, api.asset_candidate.get.validation_failed, api.asset_candidate.get.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | candidate_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Asset candidate / asset version suggestion | 资源域 | loggable |
| data.candidate_id | 是 | string | cand_* | 候选 ID | loggable |
| data.candidate_status | 是 | enum | draft / needs_confirmation / confirmed / rejected / low_confidence | 候选状态 | loggable |
| data.content_draft | 是 | string | <=12000 | 候选内容 | sensitive_not_loggable |
| data.target_asset_ref | 否 | string | asset_* | 目标资产 | loggable |
| data.quality_hint_ref | 否 | string | hint_* | 质量提示 | loggable |
| data.version_suggestion_ref | 否 | string | avs_* | 资产版本建议 | loggable |
| data.user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.asset_candidate.get.low_confidence_visible`
- `api.asset_candidate.get.validation_failed`
- `api.asset_candidate.get.cross_user_denied`

### API-ASSET-004 Confirm asset candidate

Method: POST
Path: `/api/v1/asset-candidates/{candidate_id}/confirmations`
Domain: Asset candidate / asset version suggestion
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: candidate 和 target_asset owner 必须匹配当前 actor, 确认前不得写正式 Asset
Related Data Objects: AssetCandidate, Asset, AssetVersion, UserConfirmationRef, AuditEvent, IdempotencyRecord
Related Prompt Contracts: P-ASSET-001, P-ASSET-003
F7 Contract Tests: api.asset_candidate.confirm.formal_requires_user_action, api.asset_candidate.confirm.validation_failed, api.asset_candidate.confirm.cross_user_denied, api.asset_candidate.confirm.idempotency_required, api.asset_candidate.confirm.idempotency_conflict, api.asset_candidate.confirm.stale_version_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | candidate_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| action | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 确认动作 | loggable |
| target_version_ref | 否 | VersionRef | target version | 目标版本 | loggable |
| target_formal_ref | 否 | TraceRef | typed ref | 合并或更新目标 | loggable |
| edited_content | 否 | object | schema depends on target | 用户编辑内容 | sensitive_not_loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Asset candidate / asset version suggestion | 资源域 | loggable |
| data.asset_id | 是 | string | asset_* | 资产 ID | loggable |
| data.current_version_ref | 是 | VersionRef | AssetVersion | 当前版本 | loggable |
| data.title | 是 | string | 1..160 | 资产标题 | loggable |
| data.asset_type | 是 | enum | answer_material / project_expression / job_material / feedback_summary | 资产类型 | loggable |
| data.status | 是 | enum | active / archived / disabled | 状态 | loggable |
| data.source_refs[] | 是 | SourceRef[] | >=1 | 来源 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.asset_candidate.confirm.formal_requires_user_action`
- `api.asset_candidate.confirm.validation_failed`
- `api.asset_candidate.confirm.cross_user_denied`
- `api.asset_candidate.confirm.idempotency_required`
- `api.asset_candidate.confirm.idempotency_conflict`
- `api.asset_candidate.confirm.stale_version_conflict`

### API-WEAKNESS-001 List weaknesses

Method: GET
Path: `/api/v1/weaknesses`
Domain: Weakness
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: 按 actor owner scope 过滤正式薄弱项
Related Data Objects: Weakness, WeaknessEvidence, WeaknessStatusHistory
Related Prompt Contracts: N/A
F7 Contract Tests: api.weakness.list.owner_scoped, api.weakness.list.validation_failed, api.weakness.list.cross_user_denied

#### Path Params

N/A

#### Query Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Weakness | 资源域 | loggable |
| data.weakness_id | 是 | string | weak_* | 薄弱项 ID | loggable |
| data.title | 是 | string | 1..160 | 主题 | sensitive_summary_only |
| data.status | 是 | enum | confirmed / low_priority / ignored / resolved_candidate / resolved / reopened | 状态 | loggable |
| data.severity_hint | 否 | enum | low / medium / high / unknown | 严重度提示 | loggable |
| data.evidence_refs[] | 是 | EvidenceRef[] | >=1 | 证据 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| meta.pagination | 否 | PaginationMeta | cursor pagination | 列表分页信息 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 Contract Tests

- `api.weakness.list.owner_scoped`
- `api.weakness.list.validation_failed`
- `api.weakness.list.cross_user_denied`

### API-WEAKNESS-002 Create weakness candidate task

Method: POST
Path: `/api/v1/weakness-candidates`
Domain: Weakness candidate / merge suggestion
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: source_refs/input_refs owner 必须匹配当前 actor
Related Data Objects: WeaknessCandidate, WeaknessMergeSuggestion, WeaknessSeverityAssessment, AiTask, IdempotencyRecord
Related Prompt Contracts: P-WEAKNESS-001, P-WEAKNESS-002, P-WEAKNESS-003, P-WEAKNESS-004, P-JOBMATCH-004, P-POLISH-011
F7 Contract Tests: api.weakness_candidate.create.candidate_not_formal, api.weakness_candidate.create.validation_failed, api.weakness_candidate.create.cross_user_denied, api.weakness_candidate.create.idempotency_required, api.weakness_candidate.create.idempotency_conflict, api.weakness_candidate.create.source_unavailable, api.weakness_candidate.create.provider_unavailable, api.weakness_candidate.create.task_timeout

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | job_match / polish / pressure / report / review / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| candidate_goal | 否 | enum | new_weakness / merge_suggestion / status_update / severity_assessment | 候选目标 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Weakness candidate / merge suggestion | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.weakness_candidate.create.candidate_not_formal`
- `api.weakness_candidate.create.validation_failed`
- `api.weakness_candidate.create.cross_user_denied`
- `api.weakness_candidate.create.idempotency_required`
- `api.weakness_candidate.create.idempotency_conflict`
- `api.weakness_candidate.create.source_unavailable`
- `api.weakness_candidate.create.provider_unavailable`
- `api.weakness_candidate.create.task_timeout`

### API-WEAKNESS-003 Confirm weakness candidate

Method: POST
Path: `/api/v1/weakness-candidates/{candidate_id}/confirmations`
Domain: Weakness candidate / merge suggestion
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: candidate 和 target_weakness owner 必须匹配当前 actor, 确认前不得写正式 Weakness
Related Data Objects: WeaknessCandidate, Weakness, WeaknessStatusHistory, UserConfirmationRef, AuditEvent, IdempotencyRecord
Related Prompt Contracts: P-WEAKNESS-001, P-WEAKNESS-002, P-WEAKNESS-004
F7 Contract Tests: api.weakness_candidate.confirm.formal_requires_user_action, api.weakness_candidate.confirm.validation_failed, api.weakness_candidate.confirm.cross_user_denied, api.weakness_candidate.confirm.idempotency_required, api.weakness_candidate.confirm.idempotency_conflict, api.weakness_candidate.confirm.stale_version_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | candidate_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| action | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 确认动作 | loggable |
| target_version_ref | 否 | VersionRef | target version | 目标版本 | loggable |
| target_formal_ref | 否 | TraceRef | typed ref | 合并或更新目标 | loggable |
| edited_content | 否 | object | schema depends on target | 用户编辑内容 | sensitive_not_loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Weakness candidate / merge suggestion | 资源域 | loggable |
| data.weakness_id | 是 | string | weak_* | 薄弱项 ID | loggable |
| data.title | 是 | string | 1..160 | 主题 | sensitive_summary_only |
| data.status | 是 | enum | confirmed / low_priority / ignored / resolved_candidate / resolved / reopened | 状态 | loggable |
| data.severity_hint | 否 | enum | low / medium / high / unknown | 严重度提示 | loggable |
| data.evidence_refs[] | 是 | EvidenceRef[] | >=1 | 证据 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.weakness_candidate.confirm.formal_requires_user_action`
- `api.weakness_candidate.confirm.validation_failed`
- `api.weakness_candidate.confirm.cross_user_denied`
- `api.weakness_candidate.confirm.idempotency_required`
- `api.weakness_candidate.confirm.idempotency_conflict`
- `api.weakness_candidate.confirm.stale_version_conflict`

### API-TRAINING-001 List training suggestions

Method: GET
Path: `/api/v1/training-suggestions`
Domain: Training suggestion
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: 按 actor owner scope 过滤训练建议
Related Data Objects: TrainingRecommendation, TrainingPriorityRanking, OwnerRef
Related Prompt Contracts: P-TRAINING-001, P-TRAINING-002
F7 Contract Tests: api.training_suggestion.list.owner_scoped, api.training_suggestion.list.validation_failed, api.training_suggestion.list.cross_user_denied

#### Path Params

N/A

#### Query Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Training suggestion | 资源域 | loggable |
| data.suggestion_id | 是 | string | tr_* | 训练建议 ID | loggable |
| data.suggestion_status | 是 | enum | candidate / confirmed / skipped / rejected / low_confidence | 建议状态 | loggable |
| data.topic | 是 | string | 1..160 | 训练主题 | sensitive_summary_only |
| data.priority_hint | 否 | enum | low / medium / high / unknown | 优先级提示 | loggable |
| data.weakness_refs[] | 否 | string[] | >=0 | 关联薄弱项 | loggable |
| data.asset_refs[] | 否 | string[] | >=0 | 关联资产 | loggable |
| data.user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |
| meta.pagination | 否 | PaginationMeta | cursor pagination | 列表分页信息 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.training_suggestion.list.owner_scoped`
- `api.training_suggestion.list.validation_failed`
- `api.training_suggestion.list.cross_user_denied`

### API-TRAINING-002 Create training suggestion task

Method: POST
Path: `/api/v1/training-suggestions`
Domain: Training suggestion
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: source_refs/weakness_ids/asset_ids owner 必须匹配当前 actor
Related Data Objects: TrainingRecommendation, TrainingPriorityRanking, AiTask, IdempotencyRecord
Related Prompt Contracts: P-TRAINING-001, P-TRAINING-002
F7 Contract Tests: api.training_suggestion.create.no_auto_task, api.training_suggestion.create.validation_failed, api.training_suggestion.create.cross_user_denied, api.training_suggestion.create.idempotency_required, api.training_suggestion.create.idempotency_conflict, api.training_suggestion.create.source_unavailable, api.training_suggestion.create.provider_unavailable, api.training_suggestion.create.task_timeout

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | weakness / report / review / asset / training_result / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| weakness_ids | 否 | string[] | weak_* | 薄弱项 | loggable |
| asset_ids | 否 | string[] | asset_* | 资产 | loggable |
| requested_outputs | 否 | string[] | recommendation / priority_ranking | 请求输出 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Training suggestion | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.training_suggestion.create.no_auto_task`
- `api.training_suggestion.create.validation_failed`
- `api.training_suggestion.create.cross_user_denied`
- `api.training_suggestion.create.idempotency_required`
- `api.training_suggestion.create.idempotency_conflict`
- `api.training_suggestion.create.source_unavailable`
- `api.training_suggestion.create.provider_unavailable`
- `api.training_suggestion.create.task_timeout`

### API-TRAINING-003 Confirm training suggestion

Method: POST
Path: `/api/v1/training-suggestions/{suggestion_id}/confirmations`
Domain: Training suggestion
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: suggestion.owner_ref 必须匹配当前 actor, 确认不等于自动启动 TrainingTask
Related Data Objects: TrainingRecommendation, UserConfirmationRef, AuditEvent, IdempotencyRecord
Related Prompt Contracts: P-TRAINING-001
F7 Contract Tests: api.training_suggestion.confirm.no_auto_training_task, api.training_suggestion.confirm.validation_failed, api.training_suggestion.confirm.cross_user_denied, api.training_suggestion.confirm.idempotency_required, api.training_suggestion.confirm.idempotency_conflict, api.training_suggestion.confirm.stale_version_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| suggestion_id | 是 | string | suggestion_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| action | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 确认动作 | loggable |
| target_version_ref | 否 | VersionRef | target version | 目标版本 | loggable |
| target_formal_ref | 否 | TraceRef | typed ref | 合并或更新目标 | loggable |
| edited_content | 否 | object | schema depends on target | 用户编辑内容 | sensitive_not_loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### Success Response

HTTP: 201 Created

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Training suggestion | 资源域 | loggable |
| data.suggestion_id | 是 | string | tr_* | 训练建议 ID | loggable |
| data.suggestion_status | 是 | enum | candidate / confirmed / skipped / rejected / low_confidence | 建议状态 | loggable |
| data.topic | 是 | string | 1..160 | 训练主题 | sensitive_summary_only |
| data.priority_hint | 否 | enum | low / medium / high / unknown | 优先级提示 | loggable |
| data.weakness_refs[] | 否 | string[] | >=0 | 关联薄弱项 | loggable |
| data.asset_refs[] | 否 | string[] | >=0 | 关联资产 | loggable |
| data.user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.training_suggestion.confirm.no_auto_training_task`
- `api.training_suggestion.confirm.validation_failed`
- `api.training_suggestion.confirm.cross_user_denied`
- `api.training_suggestion.confirm.idempotency_required`
- `api.training_suggestion.confirm.idempotency_conflict`
- `api.training_suggestion.confirm.stale_version_conflict`

### API-AITASK-001 Create generic AI task

Method: POST
Path: `/api/v1/ai-tasks`
Domain: AI task
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: target_ref/input_refs owner 必须匹配当前 actor, contract_ids 必须已登记
Related Data Objects: AiTask, AiTaskResult, LlmValidationResult, IdempotencyRecord
Related Prompt Contracts: 已登记 P-*
F7 Contract Tests: api.ai_task.create.contract_id_registered, api.ai_task.create.validation_failed, api.ai_task.create.cross_user_denied, api.ai_task.create.idempotency_required, api.ai_task.create.idempotency_conflict, api.ai_task.create.source_unavailable, api.ai_task.create.provider_unavailable, api.ai_task.create.task_timeout

#### Path Params

N/A

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| task_type | 是 | enum | registered AI task type | 任务类型 | loggable |
| contract_ids | 是 | string[] | P-* registered | 相关 contract | loggable |
| target_ref | 是 | TraceRef | typed ref | 目标引用 | loggable |
| input_refs | 是 | SourceRef[] | owner scoped | 输入引用 | loggable |
| requested_outputs | 否 | string[] | contract scoped | 请求输出 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | AI task | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.ai_task.create.contract_id_registered`
- `api.ai_task.create.validation_failed`
- `api.ai_task.create.cross_user_denied`
- `api.ai_task.create.idempotency_required`
- `api.ai_task.create.idempotency_conflict`
- `api.ai_task.create.source_unavailable`
- `api.ai_task.create.provider_unavailable`
- `api.ai_task.create.task_timeout`

### API-AITASK-002 Get AI task status

Method: GET
Path: `/api/v1/ai-tasks/{ai_task_id}`
Domain: AI task
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: ai_task.owner_ref 必须匹配当前 actor
Related Data Objects: AiTask, AiTaskResult, LlmValidationResult, TraceRef
Related Prompt Contracts: 已登记 P-*
F7 Contract Tests: api.ai_task.status.owner_scoped, api.ai_task.status.validation_failed, api.ai_task.status.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ai_task_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | AI task | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.ai_task.status.owner_scoped`
- `api.ai_task.status.validation_failed`
- `api.ai_task.status.cross_user_denied`

### API-AITASK-003 Get AI task result

Method: GET
Path: `/api/v1/ai-tasks/{ai_task_id}/result`
Domain: AI task
Sync/Async: sync
Auth: required
Idempotency-Key: not required
Owner Check: ai_task.owner_ref 必须匹配当前 actor, 不返回 provider payload
Related Data Objects: AiTaskResult, CandidateRef, SuggestionRef, EvidenceRef, TraceRef
Related Prompt Contracts: 已登记 P-*
F7 Contract Tests: api.ai_task.result.no_provider_payload, api.ai_task.result.validation_failed, api.ai_task.result.cross_user_denied

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ai_task_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### Request Body

N/A

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | AI task | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | 任务 ID | loggable |
| data.status | 是 | enum | succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 结果状态 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.candidate_refs[] | 否 | CandidateRef[] | >=0 | 候选引用 | loggable |
| data.suggestion_refs[] | 否 | SuggestionRef[] | >=0 | 建议引用 | loggable |
| data.validation_result_ref | 否 | ValidationResultRef | val_* | 校验结果 | loggable |
| data.provider_payload | 是 | null | must be null | 不得返回 provider payload | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.ai_task.result.no_provider_payload`
- `api.ai_task.result.validation_failed`
- `api.ai_task.result.cross_user_denied`

### API-AITASK-004 Retry AI task

Method: POST
Path: `/api/v1/ai-tasks/{ai_task_id}/retry`
Domain: AI task
Sync/Async: async
Auth: required
Idempotency-Key: required
Owner Check: ai_task.owner_ref 必须匹配当前 actor, retry 不得扩大上下文
Related Data Objects: AiTask, AiTaskResult, LlmFailureRecord, IdempotencyRecord
Related Prompt Contracts: 已登记 P-*
F7 Contract Tests: api.ai_task.retry.idempotent_and_scope_safe, api.ai_task.retry.validation_failed, api.ai_task.retry.cross_user_denied, api.ai_task.retry.idempotency_required, api.ai_task.retry.idempotency_conflict, api.ai_task.retry.source_unavailable, api.ai_task.retry.provider_unavailable, api.ai_task.retry.task_timeout

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ai_task_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| reason | 是 | enum | provider_unavailable / task_timeout / generation_failed / validation_failed / source_fixed / manual_retry | 重试原因 | loggable |
| fixed_input_refs | 否 | SourceRef[] | owner scoped | 修复后的输入 | loggable |

#### Success Response

HTTP: 202 Accepted

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | AI task | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.ai_task.retry.idempotent_and_scope_safe`
- `api.ai_task.retry.validation_failed`
- `api.ai_task.retry.cross_user_denied`
- `api.ai_task.retry.idempotency_required`
- `api.ai_task.retry.idempotency_conflict`
- `api.ai_task.retry.source_unavailable`
- `api.ai_task.retry.provider_unavailable`
- `api.ai_task.retry.task_timeout`

### API-AITASK-005 Cancel AI task

Method: POST
Path: `/api/v1/ai-tasks/{ai_task_id}/cancel`
Domain: AI task
Sync/Async: sync
Auth: required
Idempotency-Key: required
Owner Check: ai_task.owner_ref 必须匹配当前 actor, cancel 后不得 late write formal object
Related Data Objects: AiTask, AuditEvent, IdempotencyRecord
Related Prompt Contracts: 已登记 P-*
F7 Contract Tests: api.ai_task.cancel.no_late_write, api.ai_task.cancel.validation_failed, api.ai_task.cancel.cross_user_denied, api.ai_task.cancel.idempotency_required, api.ai_task.cancel.idempotency_conflict

#### Path Params

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ai_task_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### Query Params

N/A

#### Headers

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### Request Body

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| reason | 是 | enum | user_cancelled / source_changed / no_longer_needed / manual_review | 取消原因 | loggable |

#### Success Response

HTTP: 200 OK

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | AI task | 资源域 | loggable |
| data.ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| data.task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| data.status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| data.contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| data.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| data.result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| data.user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### Error Responses

| HTTP | error.code | Condition | User Action | Retryable | F7 Assertion |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少生成快照 | choose_available_source | false | source.unavailable |
| 200 / 422 | low_confidence | 资料不足、证据冲突或输出弱通过 | manual_review | true | generation.low_confidence_visible |
| 502 | provider_unavailable | LLM/RAG provider timeout、限流或暂不可用 | retry_later | true | generation.provider_unavailable |
| 504 | task_timeout / generation_failed | 生成任务超时或不可恢复失败 | retry_later | true | async.timeout |
| 429 | rate_limited | 达到 actor/IP/endpoint/task_type 限流 | retry_later | true | rate_limit.enforced |

#### F7 Contract Tests

- `api.ai_task.cancel.no_late_write`
- `api.ai_task.cancel.validation_failed`
- `api.ai_task.cancel.cross_user_denied`
- `api.ai_task.cancel.idempotency_required`
- `api.ai_task.cancel.idempotency_conflict`


## 8. Schema Index

Schema Index 冻结字段级 contract 的最小交接面。F5 可以在实现中拆分 TypeScript / Pydantic 类型，但不得删除必填字段、放宽 owner/source/idempotency 边界或把敏感字段写入日志。

### 8.1 Common schemas

#### ApiSuccessEnvelope

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | registered resource type | 资源类型 | loggable |
| data | 否 | object | schema specific | 业务数据 | schema_defined |
| meta | 否 | object | PaginationMeta / RateLimitMeta / version meta | 元数据 | loggable |
| ai_task_id | 否 | string | ait_* | 异步任务 ID | loggable |

#### ApiErrorEnvelope

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| error.code | 是 | enum | stable error code | 稳定错误码 | loggable |
| error.message | 是 | string | safe summary | 用户可理解摘要 | loggable |
| error.details | 否 | object | redacted | 字段或冲突细节 | no_sensitive_body |
| error.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| error.user_action | 否 | enum | login / fix_input / retry_later / manual_review / choose_available_source | 用户动作 | loggable |

#### PaginationMeta

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| next_cursor | 否 | string | opaque | 下一页游标 | loggable |
| has_more | 是 | boolean | true / false | 是否有更多 | loggable |
| limit | 是 | integer | 1..100 | 本页大小 | loggable |
| total_count_available | 是 | boolean | true / false | 是否提供总数 | loggable |

#### RateLimitMeta

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| limit | 是 | integer | >0 | 限制值 | loggable |
| remaining | 是 | integer | >=0 | 剩余额度 | loggable |
| reset_at | 是 | datetime | ISO-8601 | 重置时间 | loggable |
| retry_after_seconds | 否 | integer | >=0 | 建议重试秒数 | loggable |

#### SourceAvailability

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_ref | 是 | SourceRef | typed ref | 来源引用 | loggable |
| status | 是 | enum | source_available / source_archived / source_deleted / source_disabled / source_unavailable | 来源状态 | loggable |
| can_read_for_generation | 是 | boolean | true / false | 能否用于新生成 | loggable |
| display_summary | 否 | string | redacted | 可展示摘要 | sensitive_summary_only |

#### LowConfidenceFlag

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| flag_id | 是 | string | lcf_* | 标记 ID | loggable |
| reason | 是 | enum | evidence_missing / evidence_conflict / source_unavailable / output_incomplete / manual_check_required | 原因 | loggable |
| impact_scope | 是 | string | <=240 | 影响范围 | loggable |
| recommended_action | 否 | enum | manual_review / provide_more_input / retry / ignore | 建议动作 | loggable |

#### EvidenceRef

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| evidence_ref_id | 是 | string | ev_* | 证据引用 ID | loggable |
| source_ref | 是 | SourceRef | typed ref | 来源 | loggable |
| version_ref | 否 | VersionRef | typed ref | 版本 | loggable |
| summary | 否 | string | redacted | 可展示摘要 | sensitive_summary_only |
| confidence_level | 否 | enum | high / medium / low / insufficient | 证据置信度 | loggable |

#### TraceRef

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| trace_ref_id | 是 | string | tr_* | 追踪引用 ID | loggable |
| trace_type | 是 | enum | api_request / rag / llm / validation / audit / persistence | 追踪类型 | loggable |
| created_at | 是 | datetime | ISO-8601 | 创建时间 | loggable |
| redaction_boundary | 是 | string | no raw payload | 脱敏边界 | loggable |

#### ValidationResultRef

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| validation_result_id | 是 | string | val_* | 校验结果 ID | loggable |
| status | 是 | enum | passed / partial / failed | 校验状态 | loggable |
| failure_signals[] | 否 | string[] | shared failure signals | 失败信号 | loggable |
| repair_hint | 否 | string | <=240 | 修复提示 | loggable |

#### UserConfirmationRef

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| confirmation_id | 是 | string | uc_* | 确认 ID | loggable |
| actor_ref | 是 | OwnerRef | current actor | 确认人 | loggable |
| target_ref | 是 | TraceRef | typed ref | 确认目标 | loggable |
| action_type | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 动作 | loggable |
| action_result | 是 | enum | succeeded / failed / pending | 结果 | loggable |
| audit_event_ref | 是 | TraceRef | audit | 审计引用 | loggable |

#### AiTaskRef

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ait_* | AI task ID | loggable |
| task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 状态 | loggable |
| contract_ids[] | 是 | string[] | P-* | 相关 contract | loggable |
| owner_ref | 是 | OwnerRef | current actor | 归属 | loggable |

### 8.2 Request schemas

#### CreateResumeRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 是 | string | 1..120 | 简历标题 | loggable |
| markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| target_direction | 否 | string | <=120 | 目标方向 | loggable |
| client_draft_id | 否 | string | client generated | 客户端草稿 ID | loggable |

#### UpdateResumeRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 否 | string | 1..120 | 新标题 | loggable |
| markdown_text | 否 | string | 1..60000 | 新简历正文 | sensitive_not_loggable |
| content_markdown | 否 | string | 1..20000 | 项目经历模块正文 | sensitive_not_loggable |
| base_version_ref | 是 | VersionRef | ResumeVersion | 基础版本 | loggable |
| change_reason | 否 | string | <=240 | 变更原因 | loggable |

#### CreateJobRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 是 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| department | 否 | string | <=160 | 部门 | sensitive_summary_only |
| responsibilities | 是 | string[] | 1..100 items | 职责 | sensitive_not_loggable |
| requirements | 是 | string[] | 1..100 items | 要求 | sensitive_not_loggable |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |

#### UpdateJobRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| title | 否 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| responsibilities | 否 | string[] | <=100 items | 职责 | sensitive_not_loggable |
| requirements | 否 | string[] | <=100 items | 要求 | sensitive_not_loggable |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |
| base_version_ref | 是 | VersionRef | JobVersion | 基础版本 | loggable |

#### CreateBindingRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 是 | string | job_* | 岗位 ID | loggable |
| resume_version_id | 否 | string | version id | 指定简历版本 | loggable |
| job_version_id | 否 | string | version id | 指定岗位版本 | loggable |

#### CreateJobMatchAnalysisRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| binding_id | 否 | string | bind_* | 绑定 ID | loggable |
| resume_id | 条件 | string | res_* | 无 binding 时必填 | loggable |
| job_id | 条件 | string | job_* | 无 binding 时必填 | loggable |
| requested_outputs | 否 | string[] | score / points / weakness_candidates | 请求输出 | loggable |

#### CreatePolishSessionRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| binding_id | 否 | string | bind_* | 绑定 ID | loggable |
| topic_hint | 否 | string | <=240 | 打磨主题提示 | sensitive_summary_only |
| source_refs | 否 | SourceRef[] | owner scoped | 增强来源 | loggable |

#### CreatePressureSessionRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| binding_id | 否 | string | bind_* | 绑定 ID | loggable |
| start_mode | 否 | enum | first_question / continue_from_weakness / manual_topic | 启动模式 | loggable |
| source_refs | 否 | SourceRef[] | owner scoped | 增强来源 | loggable |

#### CreateQuestionTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| progress_node_ref | 否 | TraceRef | node ref | 进展节点 | loggable |
| topic_ref | 否 | TraceRef | topic ref | 主题引用 | loggable |
| question_type | 否 | enum | first / follow_up / polish | 题目类型 | loggable |
| answer_id | 否 | string | ans_* | 追问时的上一回答 | loggable |
| difficulty_hint | 否 | enum | easy / medium / hard / adaptive | 难度提示 | loggable |

#### CreateAnswerRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| answer_round | 否 | integer | >=1 | 轮次 | loggable |
| base_question_version_ref | 否 | VersionRef | Question | 题目版本 | loggable |

#### CreateFeedbackTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| requested_outputs | 否 | string[] | diagnosis / score / loss_points / reference_answer / knowledge / next_action / asset_candidate / weakness_candidate | 请求输出 | loggable |
| session_summary_ref | 否 | TraceRef | summary ref | 会话摘要 | loggable |

#### CreateScoringTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| target_type | 是 | enum | job_match / answer / session / report / review / training_result | 评分目标类型 | loggable |
| target_id | 是 | string | typed id | 评分目标 ID | loggable |
| score_type | 是 | enum | job_match / polish_round / pressure_session / report_section | 评分类型 | loggable |
| input_refs | 是 | SourceRef[] | owner scoped | 输入引用 | loggable |
| score_rule_version_id | 否 | string | rule version | 指定评分规则版本 | loggable |

#### CreateReportTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| report_type | 是 | enum | polish_summary / pressure_full | 报告类型 | loggable |
| input_refs | 否 | SourceRef[] | owner scoped | 输入引用 | loggable |
| requested_sections | 否 | string[] | summary / score / risk / weakness / training / copy_content | 请求分项 | loggable |

#### CreateRealInterviewInputRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| resume_id | 否 | string | res_* | 简历 ID | loggable |
| interview_time | 否 | datetime | ISO-8601 | 面试时间 | sensitive_summary_only |
| question_recall | 否 | string | <=20000 | 问题回忆 | sensitive_not_loggable |
| answer_recall | 否 | string | <=20000 | 回答回忆 | sensitive_not_loggable |
| interviewer_feedback | 否 | string | <=12000 | 面试官反馈 | sensitive_not_loggable |
| result_status | 否 | enum | unknown / passed / failed / pending / no_response | 结果状态 | sensitive_summary_only |

#### CreateReviewTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | mock_session / report / real_interview_input | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| requested_outputs | 否 | string[] | review_summary / review_items / weakness_candidates / asset_candidates / training_suggestions | 请求输出 | loggable |

#### CreateAssetCandidateTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | answer / feedback / report / review / training_result / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| target_asset_id | 否 | string | asset_* | 目标资产 | loggable |
| candidate_goal | 否 | enum | new_asset / version_update / quality_hint | 候选目标 | loggable |

#### ConfirmCandidateRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| action | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 确认动作 | loggable |
| target_version_ref | 否 | VersionRef | target version | 目标版本 | loggable |
| target_formal_ref | 否 | TraceRef | typed ref | 合并或更新目标 | loggable |
| edited_content | 否 | object | schema depends on target | 用户编辑内容 | sensitive_not_loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### CreateWeaknessCandidateTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | job_match / polish / pressure / report / review / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| candidate_goal | 否 | enum | new_weakness / merge_suggestion / status_update / severity_assessment | 候选目标 | loggable |

#### CreateTrainingSuggestionTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | weakness / report / review / asset / training_result / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| weakness_ids | 否 | string[] | weak_* | 薄弱项 | loggable |
| asset_ids | 否 | string[] | asset_* | 资产 | loggable |
| requested_outputs | 否 | string[] | recommendation / priority_ranking | 请求输出 | loggable |

#### CreateAiTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| task_type | 是 | enum | registered AI task type | 任务类型 | loggable |
| contract_ids | 是 | string[] | P-* registered | 相关 contract | loggable |
| target_ref | 是 | TraceRef | typed ref | 目标引用 | loggable |
| input_refs | 是 | SourceRef[] | owner scoped | 输入引用 | loggable |
| requested_outputs | 否 | string[] | contract scoped | 请求输出 | loggable |

#### RetryAiTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| reason | 是 | enum | provider_unavailable / task_timeout / generation_failed / validation_failed / source_fixed / manual_retry | 重试原因 | loggable |
| fixed_input_refs | 否 | SourceRef[] | owner scoped | 修复后的输入 | loggable |

#### CancelAiTaskRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| reason | 是 | enum | user_cancelled / source_changed / no_longer_needed / manual_review | 取消原因 | loggable |

#### RecordCopyEventRequest

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| copy_surface | 是 | enum | report_detail / review_detail | 复制位置 | loggable |
| client_event_id | 否 | string | client generated | 客户端事件 ID | loggable |
| selected_block_ids | 否 | string[] | copy block ids | 复制块 ID | loggable |

### 8.3 Response data schemas

#### ResumeSummary

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| title | 是 | string | 1..120 | 简历标题 | loggable |
| target_direction | 否 | string | <=120 | 目标方向 | loggable |
| current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本引用 | loggable |
| module_summary.project_experience_count | 是 | integer | >=0 | 项目经历模块数量 | loggable |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### ResumeDetail

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| title | 是 | string | 1..120 | 简历标题 | loggable |
| markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本 | loggable |
| modules[] | 是 | ResumeProjectExperienceModule[] | includes project_experience | 简历模块 | sensitive_summary_only |
| source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### ResumeProjectExperienceModule

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| module_id | 是 | string | mod_* | 模块 ID | loggable |
| resume_id | 是 | string | res_* | 所属简历 | loggable |
| module_type | 是 | enum | project_experience | 项目经历模块 | loggable |
| content_markdown | 是 | string | 1..20000 | 模块正文 | sensitive_not_loggable |
| base_version_ref | 是 | VersionRef | ResumeVersion | 来源版本 | loggable |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### JobSummary

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| job_id | 是 | string | job_* | 岗位 ID | loggable |
| title | 是 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |
| current_version_ref | 是 | VersionRef | JobVersion | 当前版本 | loggable |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### JobDetail

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| job_id | 是 | string | job_* | 岗位 ID | loggable |
| title | 是 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| responsibilities | 是 | string[] | item<=1000 | 职责列表 | sensitive_not_loggable |
| requirements | 是 | string[] | item<=1000 | 要求列表 | sensitive_not_loggable |
| current_version_ref | 是 | VersionRef | JobVersion | 当前版本 | loggable |
| source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### JobResumeBindingResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| binding_id | 是 | string | bind_* | 绑定 ID | loggable |
| resume_ref | 是 | VersionRef | ResumeVersion | 绑定简历版本 | loggable |
| job_ref | 是 | VersionRef | JobVersion | 绑定岗位版本 | loggable |
| binding_status | 是 | enum | active / inactive | 绑定状态 | loggable |
| created_at | 是 | datetime | ISO-8601 | 创建时间 | loggable |

#### JobMatchAnalysisResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| analysis_id | 是 | string | jma_* | 分析 ID | loggable |
| binding_ref | 是 | string | bind_* | 绑定引用 | loggable |
| score.score_value | 是 | integer | 0..100 | 匹配分 | loggable |
| match_points[] | 是 | object[] | >=0 | 匹配点 | sensitive_summary_only |
| mismatch_points[] | 是 | object[] | >=0 | 不匹配点 | sensitive_summary_only |
| improvement_points[] | 是 | object[] | >=0 | 加强点 | sensitive_summary_only |
| low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### InterviewSessionResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| mode | 是 | enum | polish / pressure | 模式 | loggable |
| session_status | 是 | enum | created / running / paused / completed / failed | 会话状态 | loggable |
| current_question_ref | 否 | string | question_* | 当前题目 | loggable |
| progress_position_ref | 否 | string | progress_pos_* | 进展位置 | loggable |
| low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### ProgressTreeResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| progress_tree_id | 是 | string | pt_* | 进展树 ID | loggable |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| nodes[] | 是 | object[] | >=0 | 节点列表 | loggable |
| current_position.node_id | 否 | string | node_* | 当前位置 | loggable |
| source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### QuestionResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| question_text | 是 | string | 1..4000 | 题目正文 | sensitive_summary_only |
| question_type | 是 | enum | polish / pressure_first / pressure_follow_up | 题目类型 | loggable |
| evidence_refs[] | 否 | EvidenceRef[] | >=0 | 证据引用 | loggable |
| generated_by_task_id | 否 | string | ait_* | 生成任务 | loggable |

#### AnswerResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| answer_round | 否 | integer | >=1 | 回答轮次 | loggable |
| created_at | 是 | datetime | ISO-8601 | 提交时间 | loggable |

#### FeedbackResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| feedback_id | 是 | string | fb_* | 反馈 ID | loggable |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| summary | 是 | string | <=2000 | 点评摘要 | sensitive_summary_only |
| score_ref | 否 | string | score_* | 评分引用 | loggable |
| loss_point_refs[] | 否 | string[] | >=0 | 失分点引用 | loggable |
| candidate_refs[] | 否 | CandidateRef[] | >=0 | 候选回流 | loggable |

#### ScoreResultResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| score_result_id | 是 | string | score_* | 评分 ID | loggable |
| target_ref | 是 | TraceRef | typed ref | 评分目标 | loggable |
| score_value | 是 | integer | 0..100 | 0-100 产品刻度 | loggable |
| score_scale | 是 | enum | 0_100_product_scale | 分数刻度 | loggable |
| score_version | 是 | string | semver/date | 评分版本 | loggable |
| rubric_version | 是 | string | semver/date | Rubric 版本 | loggable |
| confidence_level | 是 | enum | high / medium / low / insufficient | 置信度 | loggable |
| evidence_refs[] | 是 | EvidenceRef[] | >=1 unless insufficient | 证据 | loggable |

#### ReportResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | rep_* | 报告 ID | loggable |
| session_ref | 是 | string | ses_* | 会话引用 | loggable |
| report_status | 是 | enum | generating / available / partial / failed | 报告状态 | loggable |
| sections[] | 是 | object[] | >=0 | 报告分项 | sensitive_summary_only |
| score_ref | 否 | string | score_* | 总评分引用 | loggable |
| copy_content_available | 是 | boolean | true / false | 是否可复制 | loggable |
| source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### ReportCopyContentResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | rep_* | 报告 ID | loggable |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| clipboard_blocks[] | 是 | object[] | plain text blocks | 剪贴板块 | sensitive_not_loggable |
| redaction_applied | 是 | boolean | true / false | 是否脱敏 | loggable |
| copy_boundary | 是 | enum | clipboard_only | 复制边界 | loggable |
| export_artifact | 是 | null | must be null | 不得返回导出物 | loggable |

#### ReviewResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | rev_* | 复盘 ID | loggable |
| review_type | 是 | enum | mock / real_input / real | 复盘类型 | loggable |
| review_status | 是 | enum | available / partial / low_confidence / failed | 状态 | loggable |
| items[] | 否 | object[] | >=0 | 题级复盘项 | sensitive_summary_only |
| source_refs[] | 是 | SourceRef[] | >=1 | 来源 | loggable |
| candidate_refs[] | 否 | CandidateRef[] | >=0 | 候选回流 | loggable |
| low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### AssetResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| asset_id | 是 | string | asset_* | 资产 ID | loggable |
| current_version_ref | 是 | VersionRef | AssetVersion | 当前版本 | loggable |
| title | 是 | string | 1..160 | 资产标题 | loggable |
| asset_type | 是 | enum | answer_material / project_expression / job_material / feedback_summary | 资产类型 | loggable |
| status | 是 | enum | active / archived / disabled | 状态 | loggable |
| source_refs[] | 是 | SourceRef[] | >=1 | 来源 | loggable |

#### AssetCandidateResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | cand_* | 候选 ID | loggable |
| candidate_status | 是 | enum | draft / needs_confirmation / confirmed / rejected / low_confidence | 候选状态 | loggable |
| content_draft | 是 | string | <=12000 | 候选内容 | sensitive_not_loggable |
| target_asset_ref | 否 | string | asset_* | 目标资产 | loggable |
| quality_hint_ref | 否 | string | hint_* | 质量提示 | loggable |
| version_suggestion_ref | 否 | string | avs_* | 资产版本建议 | loggable |
| user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |

#### WeaknessResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| weakness_id | 是 | string | weak_* | 薄弱项 ID | loggable |
| title | 是 | string | 1..160 | 主题 | sensitive_summary_only |
| status | 是 | enum | confirmed / low_priority / ignored / resolved_candidate / resolved / reopened | 状态 | loggable |
| severity_hint | 否 | enum | low / medium / high / unknown | 严重度提示 | loggable |
| evidence_refs[] | 是 | EvidenceRef[] | >=1 | 证据 | loggable |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### WeaknessCandidateResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | wc_* | 候选 ID | loggable |
| candidate_status | 是 | enum | draft / needs_confirmation / merge_suggested / low_confidence / rejected | 候选状态 | loggable |
| title | 是 | string | 1..160 | 候选主题 | sensitive_summary_only |
| evidence_refs[] | 是 | EvidenceRef[] | >=1 | 证据 | loggable |
| merge_suggestion_refs[] | 否 | SuggestionRef[] | >=0 | 合并建议 | loggable |
| user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |

#### TrainingSuggestionResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| suggestion_id | 是 | string | tr_* | 训练建议 ID | loggable |
| suggestion_status | 是 | enum | candidate / confirmed / skipped / rejected / low_confidence | 建议状态 | loggable |
| topic | 是 | string | 1..160 | 训练主题 | sensitive_summary_only |
| priority_hint | 否 | enum | low / medium / high / unknown | 优先级提示 | loggable |
| weakness_refs[] | 否 | string[] | >=0 | 关联薄弱项 | loggable |
| asset_refs[] | 否 | string[] | >=0 | 关联资产 | loggable |
| user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |

#### AiTaskStatusResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### AiTaskResultResponse

| Field | Required | Type | Enum / Constraint | Description | Sensitive / Loggable |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ait_* | 任务 ID | loggable |
| status | 是 | enum | succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 结果状态 | loggable |
| result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| candidate_refs[] | 否 | CandidateRef[] | >=0 | 候选引用 | loggable |
| suggestion_refs[] | 否 | SuggestionRef[] | >=0 | 建议引用 | loggable |
| validation_result_ref | 否 | ValidationResultRef | val_* | 校验结果 | loggable |
| provider_payload | 是 | null | must be null | 不得返回 provider payload | loggable |

## 9. Candidate / suggestion / confirmation 写入边界

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

## 10. 报告读取、copy content 与禁止 export

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

## 11. F7 可测试性矩阵

| 能力 | 必测断言 |
|---|---|
| Success | 每个核心 endpoint 至少一个 owner 内成功路径；异步 task 能从 create 到 status 到 result |
| Validation failed | 字段缺失、非法 enum、非法 sort/filter、空 Markdown、过长文本、缺少必要 source ref 返回 `validation_failed` |
| Permission denied / cross-user access | 用户 A 无法 list/get/update/delete/generate/copy/confirm 用户 B 的任何资源 |
| Source unavailable | deleted / archived / disabled / inaccessible source 不能进入新生成；历史结果只展示 source availability |
| Low confidence | low confidence 以 `status`、`low_confidence_flags` 和 `next_actions` 返回，不被前端当作高置信成功 |
| Generation failed | provider timeout、schema invalid、semantic invalid、RAG failure 返回 `generation_failed` 或 `validation_failed`，不写 formal object |
| Scoring | 0-100 `score_value` 正常生成；`score_version`、`rubric_version`、`confidence_level`、`evidence_refs` 必须存在；`validation_failed` 不落正式报告评分 |
| Pass tendency | 不返回精确通过概率、录取概率、offer 概率或通过率百分比；低置信度 / source unavailable / validation failed 时不返回确定倾向 |
| Risk wording | `risk_level` 与 `evidence_refs` 同步存在；风险提示带 `risk_reason`、`confidence_level`、版本字段和免责声明 |
| Idempotent retry | mutation 和 AI task create 使用同一 `Idempotency-Key` 不重复创建；同 key 不同 body 返回 `idempotency_conflict` |
| Stale version / conflict | `If-Match`、`base_version_ref`、`target_version_ref` 过期返回 `stale_version_conflict` |
| No export endpoint | route inventory 不存在 PDF / Markdown file / Word / docx / export / download endpoint；命中时返回 `export_not_supported` |
| Copy boundary | copy content 仅为 clipboard 结构，不含 prompt/provider payload/hidden scoring rules/internal calibration details/sensitive raw text；复制事件审计不记录正文 |
| Formal object confirmation | candidate / suggestion 不经用户确认不得成为正式 Asset、Weakness、TrainingRecommendation、AssetVersion 或 TrainingTask |
| Rate limit | 登录、简历保存、LLM 生成、RAG 检索、报告生成、复盘生成、训练建议生成触发 429 和 retry metadata |
| Async cancellation / timeout | queued/running task 可取消；timeout 可见；取消或 timeout 不产生 late formal write |
| Pause / resume state machine | 打磨模式和压力面模式暂停均保存最小恢复快照；恢复必须校验 `source_session_snapshot_ref`、`covered_turn_refs`、`ProgressPosition`、owner 和 source availability；缺失时返回 `pause_snapshot_unavailable`、`resume_failed`、`source_unavailable` 或 `partial`，不得重复生成题目、丢弃进展或隐藏低置信度继承 |

## 12. 与 TECH / DATA / SECURITY / PROMPT 的一致性边界

| 子文档 | 一致性点 |
|---|---|
| `TECH_DESIGN.md` | API 继续位于 API 边界层；前端只依赖 API contract，不直接读库或调用 LLM；AI 生成任务由应用编排层串联领域能力、LLM 边界、持久化、trace 和审计 |
| `DATA_MODEL.md` | endpoint 只使用已登记逻辑对象、引用对象和状态域；项目经历作为 `ResumeModule(type=project_experience)` 子资源；`AiTaskResultRef`、`CandidateRef`、`SuggestionRef`、`UserConfirmationRef`、`VersionRef`、`TraceRef`、`EvidenceRef` 进入 API envelope |
| `SECURITY_PRIVACY.md` | 未登录拒绝、owner enforcement、source unavailable、复制审计、日志脱敏、Prompt / provider payload 不暴露、copy 非 export 与本文一致 |
| `PROMPT_SPEC.md` | `P-*` 只作为 related prompt contract 和 trace / validation 引用；Prompt contract 的 `api_state_mapping` 不替代 endpoint；failure signals 映射为 API status / error / low confidence |

本文件不新增未登记业务对象，不把项目经历提升为一级业务对象，不引入 MVP non-goal，不定义文件导出，不绕过 candidate / confirmation / formal object 边界。

## 13. Deferred / 非阻断项

以下事项已分类为 deferred_non_blocking 或后续 verification 项，不再作为 `AR-F4-FULL-001` 的 M4 阻断 API UNKNOWN：

- `AR-F4-FULL-003`：评分产品刻度、rubric / rule version、通过倾向分档、风险提示、低置信度降级、版本字段和免责声明已回写并通过 verification；真实招聘结果校准、隐藏规则实现细节和复杂算法调参按 `SHOULD` / `LATER` 处理。
- `AR-F4-FULL-005`：本文已定义 API status / retry / cancel / timeout、`ai_task_id`、`Idempotency-Key` 和 F7 assertion；进展树 / 暂停恢复的完整状态机 fixture 仍由该 Medium finding 后续验证，不改变本轮 AR-F4-FULL-001 的 Fixed 状态。
- 正式 Weakness 生命周期、合并规则、关闭阈值和自动消减规则：API 只允许 candidate / suggestion / confirmation / formal object 边界，自动算法后置。
- Asset 质量判断、版本合并、归档、替代和去重算法：API 只允许候选、质量提示、版本建议和用户确认 endpoint；复杂算法后置。
- Training 优先级、训练结果评估、弱项自动消减和自动训练策略：API 只允许训练建议、训练排序提示、训练任务显式启动和训练结果复盘；自动训练后置。
- 鉴权 API 的完整登录注册产品流程、复杂 ACL、企业多租户和组织权限模型：MVP 使用登录态 actor、owner enforcement、role scope 和标准错误语义；企业治理后置。
- 物理数据库、队列、缓存、日志平台、监控告警和部署拓扑：不属于 API contract 事实源；F5 可以按本 API contract 选择实现方式。

## 14. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-17 | 修复 `AR-F4-F8-001` API 字段级 contract 缺口 | 新增 API 清单总表、49 个核心接口逐接口字段级详情和 Schema Index；逐接口展开 Path Params、Query Params、Headers、Request Body、Success Response、Error Responses 和 F7 Contract Tests；不新增导出、文件上传解析或实现代码；等待 focused verification |
| 2026-05-16 | 修复 `AR-F4-FULL-001` API 阻断项 | 明确 API endpoint、response / error envelope、async task、retry、idempotency、rate limit、permission、copy boundary 和 F7 assertion 已作为 F5/F6/F7 handoff 固化；将剩余算法、状态机和治理细节改为 deferred_non_blocking 或后续 verification 项；等待 verification |
| 2026-05-16 | 修复 `AR-F4-FULL-003` 评分 / 风险 API 语义 | 明确评分不是精确通过概率；补 `score_version`、`rubric_version`、`confidence_level`、`pass_tendency_level`、`risk_level`、`evidence_refs` 响应语义；规定 low confidence / source unavailable / validation failed 降级；增加 F7 断言；不暴露隐藏评分规则 |
| 2026-05-16 | 修复 `AR-F4-FULL-002` API handoff 缺口 | 将 `API_SPEC.md` 从早期占位草案补齐为 F5/F6/F7 可交接 API contract；新增全局约定、错误 envelope、分页 / sorting / filtering、idempotency、rate limit、async task protocol、核心 endpoint matrix、copy boundary 和 F7 test assertions；不写实现代码，不改变其它 finding 状态，不标记 acceptance |
| 2026-05-16 | 修复 `AR-F4-FULL-005` 压力面暂停恢复 API 缺口 | 为压力面会话补充 `pause` / `resume` / `end` / `mark_resume_failed` 状态更新 endpoint，并在 F7 矩阵增加暂停恢复状态机断言；不进入 implementation，不改变 final acceptance 状态 |
| 2026-05-16 | 同步 Asset / Training handoff 与候选确认集中语义 | 补 Candidate / Confirmation 集中语义、Asset API handoff、Training API handoff 和 async / status / retry / idempotency 占位；后续已由 AR-F4-FULL-001 统一分类为已冻结或 deferred_non_blocking |
| 2026-05-16 | 初始化 F4 API 契约早期草案 | 对齐 DATA_MODEL 与 Prompt contracts 中的候选态、建议态、用户确认流、AI task result、response envelope 和 Weakness API handoff；后续已由 `AR-F4-FULL-002` remediation 补齐 endpoint contract，并由 AR-F4-FULL-001 处置表分类 |
