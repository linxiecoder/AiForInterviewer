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
- `APPLICATION_FLOW_SPEC.md` 是 endpoint 到 application service / 模型读取 / AiTask / P-* contract / LLM call plan / persistence handoff 的 canonical 编排交接；F5 不得只按本文件字段表自行发明流程。
- `SCORING_SPEC.md` 是评分 score type、维度、权重、公式、低置信度和正式 `ScoreResult` 规则的 canonical 文档；本文只定义 API 字段和状态。
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
| `docs/02-design/SCORING_SPEC.md` | scoring response 字段、score type、低置信度和 F7 scoring fixture 的 canonical 规则 |
| `docs/02-design/SEMANTICS_GLOSSARY.md` | `confidence_level`、`validation_status`、`source_availability` 和 low confidence 状态语义 |
| `docs/02-design/PERSISTENCE_MODEL.md` | API schema 到建议物理模型、join / reference table 和 persistence fixture 的交接 |
| `docs/02-design/APPLICATION_FLOW_SPEC.md` | endpoint 到 use-case orchestration、LLM call plan、Prompt 输入结构和持久化流程的交接 |
| `docs/02-design/PRESSURE_MODE_SPEC.md` | Pressure Mode session lifecycle、turn loop、pause / resume / end、report / review handoff、graph boundary 和实现前 API 承接 |
| `docs/03-implementation/DELIVERY_PLAN.md` | F4 / F5 / F7 阶段交接、无文件导出和 F7 可测试性要求 |
| `docs/03-implementation/BACKLOG.md` | `AIFI-API-001`、`AIFI-BE-001`、`AIFI-FE-001`、`AIFI-QA-001` 的范围和依赖 |

### 2.2 非目标

本文不做以下事项：

- 不定义登录注册完整产品方案、OAuth / SSO、企业级多租户、复杂 ACL 或组织权限树。
- 不定义物理数据库 schema、ORM model、DDL、索引、外键、migration 或缓存方案。
- 不定义 Prompt 文案、模型供应商、模型参数、embedding 模型、向量数据库或联网搜索服务。
- 不在本文重复定义评分公式、权重、阈值和校准算法；评分 canonical 规则见 `SCORING_SPEC.md`。API 不得返回通过概率或真实面试结果预测。
- 不提供文件上传解析、PDF parser、OCR、docx 解析、远程 URL 抓取或对象存储解析链路。
- 不提供文件导出、下载、批量导出、report file、snapshot file、filename hint 或 export artifact。
- 不把项目经历提升为独立一级或二级 API CRUD 资源；项目经历只作为 Markdown 简历正文中的内容片段或派生 outline 节点被引用。
- 不把 candidate / suggestion / AI task result 当作正式业务对象。

## 3. 全局 API 约定

### 3.1 Base path 与 versioning

| 项 | 约定 |
|---|---|
| Base path | `/api/v1` |
| API version | 使用 path version；F5/F6/F7 的 contract tests 默认只针对 `/api/v1` |
| Breaking change | 必须新建 `/api/v2` 或在 F4/F5 变更评审中显式登记；不得静默改变 `/api/v1` 字段语义 |
| Resource naming | 使用复数资源名，例如 `/resumes`、`/jobs`、`/reports`；项目经历不拥有 `/modules/project-experiences` 等独立 CRUD path |
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
| `meta` | 否 | pagination、sorting、filtering、rate limit、version 或 conflict 信息；基础 CRUD 不使用 source availability |
| `candidate_refs` | 否 | 本次响应涉及的候选引用 |
| `suggestion_refs` | 否 | 本次响应涉及的建议引用 |
| `confirmation_required` | 否 | 是否需要用户确认后才能写入正式对象 |
| `ai_task_id` | 否 | 异步任务 ID；只表示 API task，不等于 prompt contract ID |
| `validation_result_ref` | 否 | 输出校验结果引用 |
| `low_confidence_flags` | 否 | 低置信度、冲突、不完整或来源不可用标记 |
| `source_availability` | 否 | 仅用于 AI 结果、历史引用、EvidenceRef、TraceRef、Report、Review、JobMatchAnalysis、ScoreResult；基础 Resume / Job CRUD 不返回该字段 |
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
- `source_unavailable` 在历史 AI 结果读取时可以作为可展示状态返回；在新生成任务创建时通常为 409 / 422 错误。
- Resume / Job 等基础 CRUD 使用对象 `status`、`current_version_ref` / `base_version_ref` 表达可读、可编辑和版本冲突，不使用 `source_availability`。

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

`source_availability` 只用于 AI 结果、历史引用、`EvidenceRef`、`TraceRef`、`Report`、`Review`、`JobMatchAnalysis`、`ScoreResult` 及直接承载这些结果引用的 envelope。`Resume`、`Job` 等基础 CRUD response 只使用对象 `status`、`VersionRef` 和标准错误码；Resume 被删除、归档或禁用后，下游历史 AI 结果可以通过 `source_availability` 表示来源不可用，但普通 Resume / Job 详情不返回该字段。

- `source_available`：可在 owner / scope 校验后读取最小必要片段。
- `source_archived`：历史引用可展示摘要；默认不参与新生成。
- `source_deleted`：历史引用只展示来源状态；不得读取正文或进入新生成。
- `source_disabled`：因风险或维护禁用；不得进入新生成。
- `source_unavailable`：不可访问、缺少快照、无权限或无法读取；新生成通常失败或进入低置信度 / manual review。

低置信度不是普通成功态。AI 结果类 API 必须在 `status`、`low_confidence_flags`、`source_availability`、`next_actions` 中表达影响范围和用户可操作路径；基础 CRUD 的低置信度不应通过 `source_availability` 表达。

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

### 5.4 Agent Runtime API contract skeleton（PR3 / PR4）

本节只登记 PR3 / PR4 Runtime Contracts 的 API skeleton。PR3 / PR4 API exposure 如未实现，只作为后端 contract skeleton，不授权 F6/F7 frontend 接入或普通用户 debug page。PR6 Graph Configuration Backend 可读取 graph descriptor / config，但不得暴露 LangGraph internals。

| Endpoint | 作用 | PR | 关键边界 |
|---|---|---:|---|
| `GET /api/v1/agent-runs/{agent_run_id}` | get agent run status | PR4 skeleton | owner-scoped；返回 sanitized status、graph descriptor refs、task refs、validation / failure summary；不返回 `AgentState` |
| `GET /api/v1/agent-runs/{agent_run_id}/timeline` | get agent run timeline | PR4 skeleton | 只返回 sanitized events、node status、trace refs、checkpoint metadata summary refs；不返回 checkpoint payload |
| `GET /api/v1/agent-interrupts/{interrupt_id}` | get interrupt detail | PR4 skeleton | drawer payload sanitized；只返回 allowed actions、candidate refs、resume schema id、validation summary |
| `POST /api/v1/agent-interrupts/{interrupt_id}/resume` | resume interrupt | PR4 skeleton | required idempotency；owner/base_version/schema 校验；不允许 late formal write 或 raw payload |
| `POST /api/v1/agent-runs/{agent_run_id}/cancel` | cancel run | PR4 skeleton | 可取消状态才允许；取消后阻断 provider continuation 和 formal write |
| `GET /api/v1/graph-descriptors` / `GET /api/v1/graph-descriptors/{graph_name}` | graph descriptor/config read | PR6 | read-only descriptor / config refs；不暴露 provider secrets、LangGraph internals、AgentState、checkpoint payload 或 raw provider data |

所有 Agent Runtime response 必须 sanitized：

- 不返回 `AgentState`、checkpoint payload、raw prompt、raw completion、provider payload、system prompt、hidden scoring rule、token、cookie、secret。
- 不返回 `raw_payload_ciphertext_ref`、`encryption_key_ref` 或 raw debug ref。
- timeline 和 interrupt detail 只返回 refs、hashes、status、validation、failure category、low confidence flags、allowed actions 和 display-safe summary。
- PR3 / PR4 不开放普通用户 debug page；debug raw capture 默认关闭。

## 6. API 清单总表

本节作为 F5 后端实现、F6 前端接入和 F7 API contract tests 的稳定 route inventory。旧版 endpoint matrix 不再作为唯一交接面；逐接口字段级 contract 见 §7，Schema 索引（Schema Index）见 §8。

| API ID | 方法（Method） | 路径（Path） | 名称 | 领域 | 同步 / 异步 | 认证 | 幂等要求 | Owner 校验 | 请求 Schema | 响应 Schema | 错误 Schema | 关联数据对象 | 关联 Prompt Contract | F7 契约测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API-RESUME-001 | GET | /api/v1/resumes | 列出简历（List resumes） | Resume | sync | required | not required | 按 actor owner scope 过滤列表 | N/A（查询参数） | ResumeSummary[] | ApiErrorEnvelope | Resume, ResumeVersion, OwnerRef | N/A | api.resume.list.owner_scoped |
| API-RESUME-002 | POST | /api/v1/resumes | 创建简历（Create resume） | Resume | sync | required | required | 服务端从 session 推导 owner, 请求体不得包含 owner_id | CreateResumeRequest | ResumeDetail | ApiErrorEnvelope | Resume, ResumeVersion, AuditEvent, IdempotencyRecord | N/A | api.resume.create.success |
| API-RESUME-003 | GET | /api/v1/resumes/{resume_id} | 获取简历详情（Get resume detail） | Resume | sync | required | not required | resume.owner_ref 必须匹配当前 actor | N/A | ResumeDetail | ApiErrorEnvelope | Resume, ResumeVersion, OwnerRef | N/A | api.resume.get.cross_user_denied |
| API-RESUME-004 | PATCH | /api/v1/resumes/{resume_id} | 更新简历（Update resume） | Resume | sync | required | required | resume.owner_ref 与 base_version_ref owner 一致；只更新 Markdown 正文并创建新 ResumeVersion | UpdateResumeRequest | ResumeDetail | ApiErrorEnvelope | Resume, ResumeVersion, AuditEvent, IdempotencyRecord | N/A | api.resume.update.stale_version_conflict |
| API-JOB-001 | GET | /api/v1/jobs | 列出岗位（List jobs） | Job / JD | sync | required | not required | 按 actor owner scope 过滤列表 | N/A（查询参数） | JobSummary[] | ApiErrorEnvelope | Job, JobVersion, JobStatus, OwnerRef | N/A | api.job.list.owner_scoped |
| API-JOB-002 | POST | /api/v1/jobs | 手动创建岗位（Create job manually） | Job / JD | sync | required | required | 服务端从 session 推导 owner, 不接受外部材料解析 | CreateJobRequest | JobDetail | ApiErrorEnvelope | Job, JobVersion, JobStatus, AuditEvent, IdempotencyRecord | N/A | api.job.create.manual_only |
| API-JOB-003 | GET | /api/v1/jobs/{job_id} | 获取岗位详情（Get job detail） | Job / JD | sync | required | not required | job.owner_ref 必须匹配当前 actor | N/A | JobDetail | ApiErrorEnvelope | Job, JobVersion, JobStatus, OwnerRef | N/A | api.job.get.cross_user_denied |
| API-JOB-004 | PATCH | /api/v1/jobs/{job_id} | 更新岗位（Update job） | Job / JD | sync | required | required | job.owner_ref 与 base_version_ref owner 一致 | UpdateJobRequest | JobDetail | ApiErrorEnvelope | Job, JobVersion, JobStatus, AuditEvent, IdempotencyRecord | N/A | api.job.update.stale_version_conflict |
| API-BINDING-001 | POST | /api/v1/resume-job-bindings | 创建简历-岗位绑定（Create resume-job binding） | Resume-job binding | sync | required | required | resume、job、version 必须同 owner | CreateBindingRequest | JobResumeBindingResponse | ApiErrorEnvelope | JobResumeBinding, ResumeVersion, JobVersion, AuditEvent, IdempotencyRecord | N/A | api.binding.create.cross_owner_denied |
| API-BINDING-002 | DELETE | /api/v1/resume-job-bindings/{binding_id} | 解除简历-岗位绑定（Unbind resume-job binding） | Resume-job binding | sync | required | required | binding、resume、job、version 必须同 owner；解绑不得删除历史报告 / 复盘 / 匹配结果 | DeleteBindingRequest | JobResumeBindingResponse | ApiErrorEnvelope | JobResumeBinding, JobMatchAnalysis, InterviewReport, MockInterviewReview, RealInterviewReview, AuditEvent, IdempotencyRecord | N/A | binding.delete.success |
| API-JOBMATCH-001 | POST | /api/v1/job-match-analyses | 创建岗位匹配分析任务（Create job match analysis task） | Job match analysis | async | required | required | resume_job_binding_id/job/resume/version 必须同 owner 且 source_available | CreateJobMatchAnalysisRequest | AiTaskStatusResponse | ApiErrorEnvelope | JobMatchAnalysis, MatchScore, WeaknessCandidate, AiTask, IdempotencyRecord | P-JOBMATCH-001, P-JOBMATCH-002, P-JOBMATCH-003, P-JOBMATCH-004 | api.job_match.create.async_success |
| API-JOBMATCH-002 | GET | /api/v1/job-match-analyses/{analysis_id} | 获取岗位匹配分析（Get job match analysis） | Job match analysis | sync | required | not required | analysis.owner_ref 必须匹配当前 actor | N/A | JobMatchAnalysisResponse | ApiErrorEnvelope | JobMatchAnalysis, ScoreResult, EvidenceRef, TraceRef, SourceAvailability | P-JOBMATCH-* | api.job_match.get.low_confidence_visible |
| API-POLISH-001 | POST | /api/v1/polish-sessions | 创建打磨会话（Create polish session） | Polish session | sync | required | required | resume/job/resume_job_binding_id/source_refs 必须同 owner；topic/subtopic 必须来自可用 Polish topic options | CreatePolishSessionRequest | InterviewSessionResponse | ApiErrorEnvelope | InterviewSession, PolishSessionDetail, ProgressTree, IdempotencyRecord | P-POLISH-001 | api.polish_session.create.success; polish.session.create.with_topic_subtopic |
| API-POLISH-002 | GET | /api/v1/polish-sessions/{session_id} | 获取打磨会话（Get polish session） | Polish session | sync | required | not required | session.owner_ref 必须匹配当前 actor | N/A | InterviewSessionResponse | ApiErrorEnvelope | InterviewSession, PolishSessionDetail, ProgressTree, SessionSummary | N/A | api.polish_session.get.owner_scoped |
| API-POLISH-003 | POST | /api/v1/polish-sessions/{session_id}/questions | 创建打磨题目任务（Create polish question task） | Question | async | required | required | session、progress_node、source_refs 必须同 owner | CreateQuestionTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | Question, AiTask, RAGContextAssembly, IdempotencyRecord | P-POLISH-002, P-SHARED-* | api.polish_question.create.async_success |
| API-POLISH-004 | POST | /api/v1/polish-sessions/{session_id}/answers | 创建打磨回答（Create polish answer） | Answer | sync | required | required | session/question.owner_ref 必须匹配当前 actor | CreateAnswerRequest | AnswerResponse | ApiErrorEnvelope | Answer, Question, InterviewSession, AuditEvent, IdempotencyRecord | N/A | api.polish_answer.create.validation_failed |
| API-POLISH-005 | POST | /api/v1/polish-sessions/{session_id}/feedback | 创建打磨反馈任务（Create polish feedback task） | Feedback | async | required | required | session/answer/evidence owner 必须匹配当前 actor | CreateFeedbackTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | Feedback, ScoreResult, AssetCandidate, WeaknessCandidate, AiTask, IdempotencyRecord | P-POLISH-003, P-POLISH-004, P-POLISH-005, P-POLISH-006, P-POLISH-007, P-POLISH-008, P-POLISH-009, P-POLISH-010, P-POLISH-011 | api.polish_feedback.create.low_confidence_visible |
| API-POLISH-006 | GET | /api/v1/polish-topics | 列出打磨主题和次主题（List polish topics and subtopics） | Polish topic options | sync | required | not required | 可选 resume_job_binding_id 必须指向当前 actor 的 JobResumeBinding；主题目录不是正式业务对象 | N/A（查询参数） | PolishTopic[] | ApiErrorEnvelope | PolishTopicRef, PolishSubtopicRef, JobResumeBinding | P-POLISH-001, P-POLISH-002 | polish.topic.list.success |
| API-PRESSURE-001 | POST | /api/v1/pressure-sessions | 创建压力面会话（Create pressure session） | Pressure session | sync | required | required | resume/job/resume_job_binding_id/source_refs 必须同 owner | CreatePressureSessionRequest | InterviewSessionResponse | ApiErrorEnvelope | InterviewSession, PressureSessionDetail, ProgressTree, IdempotencyRecord | P-PRESSURE-001 | api.pressure_session.create.success |
| API-PRESSURE-002 | GET | /api/v1/pressure-sessions/{session_id} | 获取压力面会话（Get pressure session） | Pressure session | sync | required | not required | session.owner_ref 必须匹配当前 actor | N/A | InterviewSessionResponse | ApiErrorEnvelope | InterviewSession, PressureSessionDetail, ProgressTree, SessionSummary | N/A | api.pressure_session.get.owner_scoped |
| API-PRESSURE-003 | POST | /api/v1/pressure-sessions/{session_id}/questions | 创建压力面题目任务（Create pressure question task） | Question | async | required | required | session/answer/source_refs 必须同 owner | CreateQuestionTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | Question, AiTask, PressureSessionDetail, IdempotencyRecord | P-PRESSURE-002, P-PRESSURE-004, P-PRESSURE-005 | api.pressure_question.create.async_success |
| API-PRESSURE-004 | POST | /api/v1/pressure-sessions/{session_id}/answers | 创建压力面回答（Create pressure answer） | Answer | sync | required | required | session/question.owner_ref 必须匹配当前 actor | CreateAnswerRequest | AnswerResponse | ApiErrorEnvelope | Answer, Question, InterviewSession, AuditEvent, IdempotencyRecord | N/A | api.pressure_answer.create.success |
| API-PRESSURE-005 | POST | /api/v1/pressure-sessions/{session_id}/feedback | 创建压力面反馈任务（Create pressure feedback task） | Feedback | async | required | required | session/answer/evidence owner 必须匹配当前 actor | CreateFeedbackTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | Feedback, ScoreResult, SessionSummary, AiTask, IdempotencyRecord | P-PRESSURE-003, P-PRESSURE-006, P-PRESSURE-007, P-PRESSURE-008, P-PRESSURE-009 | api.pressure_feedback.create.generation_failed_visible |
| API-PROGRESS-001 | GET | /api/v1/interview-sessions/{session_id}/progress-tree | 获取进展树（Get progress tree） | Progress tree | sync | required | not required | session.owner_ref 必须匹配当前 actor | N/A | ProgressTreeResponse | ApiErrorEnvelope | ProgressTree, ProgressNode, ProgressPosition | N/A | api.progress_tree.get.owner_scoped |
| API-SCORING-001 | POST | /api/v1/scoring-results | 创建评分任务（Create scoring task） | Scoring result | async | required | required | target/input_refs owner 必须匹配当前 actor, hidden scoring rules 不暴露 | CreateScoringTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | ScoreResult, ScoreRuleVersion, ScoreExplanation, AiTask, IdempotencyRecord | P-JOBMATCH-002, P-POLISH-004, P-PRESSURE-008, P-REPORT-002 | api.scoring.create.no_hidden_rules |
| API-SCORING-002 | GET | /api/v1/scoring-results/{score_result_id} | 获取评分结果（Get scoring result） | Scoring result | sync | required | not required | score_result.owner_ref 必须匹配当前 actor | N/A | ScoreResultResponse | ApiErrorEnvelope | ScoreResult, ScoreRuleVersion, EvidenceRef, TraceRef, LowConfidenceFlag | P-JOBMATCH-002, P-POLISH-004, P-PRESSURE-008, P-REPORT-002 | api.scoring.get.no_exact_probability |
| API-REPORT-001 | POST | /api/v1/reports | 创建报告任务（Create report task） | Report | async | required | required | session/input_refs owner 必须匹配当前 actor | CreateReportTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | InterviewReport, ReportSection, ScoreResult, AiTask, IdempotencyRecord | P-REPORT-001, P-REPORT-002, P-REPORT-003, P-REPORT-004 | api.report.create.async_success |
| API-REPORT-002 | GET | /api/v1/reports/{report_id} | 获取报告（Get report） | Report | sync | required | not required | report.owner_ref 必须匹配当前 actor | N/A | ReportResponse | ApiErrorEnvelope | InterviewReport, ReportSection, ScoreResult, SourceAvailability | P-REPORT-* | api.report.get.copy_boundary_visible |
| API-REPORT-003 | GET | /api/v1/reports/{report_id}/copy-content | 获取报告复制内容（Get report copy content） | Report copy content | sync | required | not required | report.owner_ref 必须匹配当前 actor, copy boundary 必须过滤敏感内容 | N/A | ReportCopyContentResponse | ApiErrorEnvelope | CopyableContent, InterviewReport, AuditEvent, EvidenceRef | P-REPORT-004 | api.report.copy_content.no_export_artifact |
| API-REPORT-004 | POST | /api/v1/reports/{report_id}/copy-events | 记录报告复制事件（Record report copy event） | Report copy content | sync | required | required | report.owner_ref 必须匹配当前 actor, 审计不记录正文 | RecordCopyEventRequest | ReportCopyContentResponse | ApiErrorEnvelope | CopyableContent, AuditEvent, IdempotencyRecord | N/A | api.report.copy_event.audit_without_body |
| API-REVIEW-001 | POST | /api/v1/reviews/mock | 创建模拟面试复盘任务（Create mock interview review task） | Mock interview review | async | required | required | session/report/input_refs owner 必须匹配当前 actor | CreateReviewTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | MockInterviewReview, ReviewItem, AiTask, IdempotencyRecord | P-REVIEW-001, P-REVIEW-004 | api.review.mock.create.async_success |
| API-REVIEW-002 | POST | /api/v1/reviews/real-inputs | 创建真实面试输入（Create real interview input） | Real interview input / review | sync | required | required | job/resume/input_refs owner 必须匹配当前 actor | CreateRealInterviewInputRequest | ReviewResponse | ApiErrorEnvelope | RealInterviewInput, RealInterviewEvidence, UserConfirmationRef, IdempotencyRecord | P-REVIEW-002 | api.review.real_input.create.requires_confirmation |
| API-REVIEW-003 | POST | /api/v1/reviews/real | 创建真实面试复盘任务（Create real interview review task） | Real interview input / review | async | required | required | real_interview_input owner 必须匹配当前 actor 且已确认 | CreateReviewTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | RealInterviewReview, ReviewItem, AiTask, IdempotencyRecord | P-REVIEW-003, P-REVIEW-004 | api.review.real.create.confirmed_input_only |
| API-REVIEW-004 | GET | /api/v1/reviews/{review_id} | 获取复盘（Get review） | Mock interview review / Real interview review | sync | required | not required | review.owner_ref 必须匹配当前 actor | N/A | ReviewResponse | ApiErrorEnvelope | MockInterviewReview, RealInterviewReview, ReviewItem, SourceAvailability | P-REVIEW-* | api.review.get.low_confidence_visible |
| API-REVIEW-005 | GET | /api/v1/reviews | 列出复盘（List reviews） | Review list | sync | required | not required | 按 actor owner scope 过滤复盘列表 | N/A（查询参数） | ReviewSummary[] | ApiErrorEnvelope | InterviewRetrospective, MockInterviewReview, RealInterviewReview, ReviewSourceRef, SourceAvailability | P-REVIEW-* | reviews.list.success |
| API-REVIEW-006 | GET | /api/v1/reviews/{review_id}/copy-content | 获取复盘复制内容（Get review copy content） | Review copy content | sync | required | not required | review.owner_ref 必须匹配当前 actor；copy boundary 必须过滤第三方隐私、Prompt 和 provider payload | N/A | ReviewCopyContentResponse | ApiErrorEnvelope | CopyableReviewContent, MockInterviewReview, RealInterviewReview, ReviewItem, AuditEvent | P-REVIEW-* | review_copy.get.no_prompt_payload |
| API-REVIEW-007 | POST | /api/v1/reviews/{review_id}/copy-events | 记录复盘复制事件（Record review copy event） | Review copy event | sync | required | required | review.owner_ref 必须匹配当前 actor；审计不记录复制正文 | RecordReviewCopyEventRequest | ReviewCopyEventResponse | ApiErrorEnvelope | ReviewCopyEvent, AuditEvent, IdempotencyRecord | N/A | review_copy.audit.no_body_logged |
| API-ASSET-001 | GET | /api/v1/assets | 列出资产（List assets） | Asset | sync | required | not required | 按 actor owner scope 过滤正式资产 | N/A（查询参数） | AssetResponse[] | ApiErrorEnvelope | Asset, AssetVersion, AssetSource, OwnerRef | N/A | api.asset.list.owner_scoped |
| API-ASSET-002 | POST | /api/v1/asset-candidates | 创建资产候选任务（Create asset candidate task） | Asset candidate / asset version suggestion | async | required | required | source_refs/target_asset owner 必须匹配当前 actor | CreateAssetCandidateTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | AssetCandidate, AssetQualityHint, AssetVersionSuggestion, AiTask, IdempotencyRecord | P-ASSET-001, P-ASSET-002, P-ASSET-003, P-POLISH-010 | api.asset_candidate.create.candidate_not_formal |
| API-ASSET-003 | GET | /api/v1/asset-candidates/{candidate_id} | 获取资产候选（Get asset candidate） | Asset candidate / asset version suggestion | sync | required | not required | candidate.owner_ref 必须匹配当前 actor | N/A | AssetCandidateResponse | ApiErrorEnvelope | AssetCandidate, AssetQualityHint, AssetVersionSuggestion, EvidenceRef, TraceRef | P-ASSET-* | api.asset_candidate.get.low_confidence_visible |
| API-ASSET-004 | POST | /api/v1/asset-candidates/{candidate_id}/confirmations | 确认资产候选（Confirm asset candidate） | Asset candidate / asset version suggestion | sync | required | required | candidate 和 target_asset owner 必须匹配当前 actor, 确认前不得写正式 Asset | ConfirmCandidateRequest | AssetResponse | ApiErrorEnvelope | AssetCandidate, Asset, AssetVersion, UserConfirmationRef, AuditEvent, IdempotencyRecord | P-ASSET-001, P-ASSET-003 | api.asset_candidate.confirm.formal_requires_user_action |
| API-WEAKNESS-001 | GET | /api/v1/weaknesses | 列出薄弱项（List weaknesses） | Weakness | sync | required | not required | 按 actor owner scope 过滤正式薄弱项 | N/A（查询参数） | WeaknessResponse[] | ApiErrorEnvelope | Weakness, WeaknessEvidence, WeaknessStatusHistory | N/A | api.weakness.list.owner_scoped |
| API-WEAKNESS-002 | POST | /api/v1/weakness-candidates | 创建薄弱项候选任务（Create weakness candidate task） | Weakness candidate / merge suggestion | async | required | required | source_refs/input_refs owner 必须匹配当前 actor | CreateWeaknessCandidateTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | WeaknessCandidate, WeaknessMergeSuggestion, WeaknessSeverityAssessment, AiTask, IdempotencyRecord | P-WEAKNESS-001, P-WEAKNESS-002, P-WEAKNESS-003, P-WEAKNESS-004, P-JOBMATCH-004, P-POLISH-011 | api.weakness_candidate.create.candidate_not_formal |
| API-WEAKNESS-003 | POST | /api/v1/weakness-candidates/{candidate_id}/confirmations | 确认薄弱项候选（Confirm weakness candidate） | Weakness candidate / merge suggestion | sync | required | required | candidate 和 target_weakness owner 必须匹配当前 actor, 确认前不得写正式 Weakness | ConfirmCandidateRequest | WeaknessResponse | ApiErrorEnvelope | WeaknessCandidate, Weakness, WeaknessStatusHistory, UserConfirmationRef, AuditEvent, IdempotencyRecord | P-WEAKNESS-001, P-WEAKNESS-002, P-WEAKNESS-004 | api.weakness_candidate.confirm.formal_requires_user_action |
| API-TRAINING-001 | GET | /api/v1/training-suggestions | 列出训练建议（List training suggestions） | Training suggestion | sync | required | not required | 按 actor owner scope 过滤训练建议 | N/A（查询参数） | TrainingSuggestionResponse[] | ApiErrorEnvelope | TrainingRecommendation, TrainingPriorityRanking, OwnerRef | P-TRAINING-001, P-TRAINING-002 | api.training_suggestion.list.owner_scoped |
| API-TRAINING-002 | POST | /api/v1/training-suggestions | 创建训练建议任务（Create training suggestion task） | Training suggestion | async | required | required | source_refs/weakness_ids/asset_ids owner 必须匹配当前 actor | CreateTrainingSuggestionTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | TrainingRecommendation, TrainingPriorityRanking, AiTask, IdempotencyRecord | P-TRAINING-001, P-TRAINING-002 | api.training_suggestion.create.no_auto_task |
| API-TRAINING-003 | POST | /api/v1/training-suggestions/{suggestion_id}/confirmations | 确认训练建议（Confirm training suggestion） | Training suggestion | sync | required | required | suggestion.owner_ref 必须匹配当前 actor, 确认不等于自动启动 TrainingTask | ConfirmCandidateRequest | TrainingSuggestionResponse | ApiErrorEnvelope | TrainingRecommendation, UserConfirmationRef, AuditEvent, IdempotencyRecord | P-TRAINING-001 | api.training_suggestion.confirm.no_auto_training_task |
| API-CANDIDATE-001 | POST | /api/v1/candidates/{candidate_id}/corrections | 保存低置信候选校对（Save candidate correction） | Candidate correction | sync | required | required | candidate.owner_ref 必须匹配当前 actor；校对内容不得直接污染 Prompt source 或正式对象 | CandidateCorrectionRequest | CandidateCorrectionResponse | ApiErrorEnvelope | CandidateCorrection, UserCorrectionRef, LlmValidationResult, AuditEvent, IdempotencyRecord | P-SHARED-003, P-SHARED-004 | candidate.correction.save.success |
| API-DEPOSIT-001 | POST | /api/v1/candidates/{candidate_id}/deposit-confirmations | 确认内容沉淀目标（Confirm deposit target） | Deposit target confirmation | sync | required | required | candidate/source/target_ref owner 必须匹配当前 actor；Prompt 只能建议目标，不能静默决定正式沉淀 | ConfirmDepositTargetRequest | DepositTargetConfirmationResponse | ApiErrorEnvelope | DepositTarget, UserConfirmationRef, AuditEvent, IdempotencyRecord | P-ASSET-001, P-WEAKNESS-001, P-TRAINING-001, P-REVIEW-* | deposit_target.confirm.asset |
| API-AITASK-001 | POST | /api/v1/ai-tasks | 创建通用 AI 任务（Create generic AI task） | AI task | async | required | required | target_ref/input_refs owner 必须匹配当前 actor, contract_ids 必须已登记 | CreateAiTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | AiTask, AiTaskResult, LlmValidationResult, IdempotencyRecord | 已登记 P-* | api.ai_task.create.contract_id_registered |
| API-AITASK-002 | GET | /api/v1/ai-tasks/{ai_task_id} | 获取 AI 任务状态（Get AI task status） | AI task | sync | required | not required | ai_task.owner_ref 必须匹配当前 actor | N/A | AiTaskStatusResponse | ApiErrorEnvelope | AiTask, AiTaskResult, LlmValidationResult, TraceRef | 已登记 P-* | api.ai_task.status.owner_scoped |
| API-AITASK-003 | GET | /api/v1/ai-tasks/{ai_task_id}/result | 获取 AI 任务结果（Get AI task result） | AI task | sync | required | not required | ai_task.owner_ref 必须匹配当前 actor, 不返回 provider payload | N/A | AiTaskResultResponse | ApiErrorEnvelope | AiTaskResult, CandidateRef, SuggestionRef, EvidenceRef, TraceRef | 已登记 P-* | api.ai_task.result.no_provider_payload |
| API-AITASK-004 | POST | /api/v1/ai-tasks/{ai_task_id}/retry | 重试 AI 任务（Retry AI task） | AI task | async | required | required | ai_task.owner_ref 必须匹配当前 actor, retry 不得扩大上下文 | RetryAiTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | AiTask, AiTaskResult, LlmFailureRecord, IdempotencyRecord | 已登记 P-* | api.ai_task.retry.idempotent_and_scope_safe |
| API-AITASK-005 | POST | /api/v1/ai-tasks/{ai_task_id}/cancel | 取消 AI 任务（Cancel AI task） | AI task | sync | required | required | ai_task.owner_ref 必须匹配当前 actor, cancel 后不得 late write formal object | CancelAiTaskRequest | AiTaskStatusResponse | ApiErrorEnvelope | AiTask, AuditEvent, IdempotencyRecord | 已登记 P-* | api.ai_task.cancel.no_late_write |
| API-AGENT-RUNTIME-001 | GET | /api/v1/agent-runs/{agent_run_id} | 获取 Agent run 状态（Get agent run status） | Agent runtime | sync | required | not required | agent_run.owner_ref 必须匹配当前 actor；response sanitized | N/A | AgentRunStatusResponse | ApiErrorEnvelope | AgentRun, AiTask, TraceRef, ValidationResultRef | N/A | api.agent_run.status.sanitized |
| API-AGENT-RUNTIME-002 | GET | /api/v1/agent-runs/{agent_run_id}/timeline | 获取 Agent run timeline（Get agent run timeline） | Agent runtime | sync | required | not required | agent_run.owner_ref 必须匹配当前 actor；不返回 AgentState/checkpoint/raw payload | N/A（查询参数） | AgentRunTimelineResponse | ApiErrorEnvelope | AgentRun, AgentNodeRun, AgentCheckpointRef, LlmCall, TraceRef | N/A | api.agent_run.timeline.no_raw_payload |
| API-AGENT-RUNTIME-003 | GET | /api/v1/agent-interrupts/{interrupt_id} | 获取 Agent interrupt 详情（Get interrupt detail） | Agent runtime | sync | required | not required | interrupt.owner_ref 必须匹配当前 actor；drawer payload sanitized | N/A | AgentInterruptDetailResponse | ApiErrorEnvelope | AgentInterrupt, CandidateRef, ValidationResultRef, AuditEvent | N/A | api.agent_interrupt.get.sanitized |
| API-AGENT-RUNTIME-004 | POST | /api/v1/agent-interrupts/{interrupt_id}/resume | 恢复 Agent interrupt（Resume interrupt） | Agent runtime | async | required | required | interrupt/run owner、base_version、resume_schema 和 idempotency 必须通过；不允许 late formal write | ResumeAgentInterruptRequest | AgentRunStatusResponse | ApiErrorEnvelope | AgentInterrupt, AgentRun, IdempotencyRecord, AuditEvent | N/A | api.agent_interrupt.resume.idempotent |
| API-AGENT-RUNTIME-005 | POST | /api/v1/agent-runs/{agent_run_id}/cancel | 取消 Agent run（Cancel agent run） | Agent runtime | sync | required | required | agent_run.owner_ref 必须匹配当前 actor；cancel 后阻断 provider continuation 和 formal write | CancelAgentRunRequest | AgentRunStatusResponse | ApiErrorEnvelope | AgentRun, AgentInterrupt, AuditEvent, IdempotencyRecord | N/A | api.agent_run.cancel.no_late_formal_write |
| API-AGENT-RUNTIME-006 | GET | /api/v1/graph-descriptors | 读取 graph descriptor 列表（List graph descriptors） | Graph configuration | sync | required | not required | PR6 read-only；owner/admin scoped；不暴露 LangGraph internals 或 provider secrets | N/A（查询参数） | GraphDescriptorResponse[] | ApiErrorEnvelope | GraphDescriptor, GraphConfigAuditEvent | N/A | api.graph_descriptor.list.sanitized |


### 6.1 F6 Page/API Handoff Matrix

本节修复 `AR-F4-F8-002`：F6 前端不得从 `UX_SPEC.md`、`UI_DESIGN_SYSTEM.md` 或实现代码反向发明 API 字段、状态、错误码、候选确认流或 copy boundary。F6 页面接入以本矩阵、§3-§5 全局协议、§7 逐接口字段级详情、§8 Schema 索引（Schema Index）和 §9-§10 confirmation / copy 边界为准。

矩阵中的“所需 API（Required APIs）”是 F6 页面可直接接入的最小 API 集；如某页面不需要独立 API，必须在该行说明组合读取来源或入口来源。所有页面默认继承 §6.2 状态映射、§6.3 字段需求、§6.4 confirmation flow、§6.5 禁止能力和 §6.6 F2/F3 一致性规则。

Job 页面摘要状态域固定为：`JobBindingSummary.status` 只允许 `not_bound`、`bound`；`JobMatchSummary.status` 只允许 `match_not_generated`、`match_queued`、`match_running`、`match_succeeded`、`match_low_confidence`、`match_failed`、`match_stale`。`latest_match_summary` 不返回 `pass_probability`、`offer_probability` 或等价精确通过概率字段。

| F6 页面 / Surface | 主要用户任务 | 所需 API | 读取模型 / 响应 Schema | 加载 / 异步状态 | 空态 | 错误态 | 权限态 | 候选 / 确认态 | 复制边界 | F7 断言 |
|---|---|---|---|---|---|---|---|---|---|---|
| 工作台 / Dashboard | 查看最近简历、岗位、待处理任务、薄弱项、训练建议和下一步入口 | `API-RESUME-001`, `API-JOB-001`, `API-ASSET-001`, `API-WEAKNESS-001`, `API-TRAINING-001`, `API-AITASK-002`；无独立 dashboard endpoint，F6 组合读取 | `ResumeSummary[]`, `JobSummary[]`, `AssetResponse[]`, `WeaknessResponse[]`, `TrainingSuggestionResponse[]`, `AiTaskStatusResponse` | 页面级 `loading` 用 Skeleton；异步卡片显示 `queued` / `running` / `partial` / `low_confidence` / `user_visible_status` | 无简历、无岗位、无薄弱项、无训练建议分别展示引导；全空时仍不创建新页面体系 | 列表读取失败显示模块级 retry；`provider_unavailable` / `task_timeout` 只适用于 AI task 卡片；`export_not_supported` 不应出现，命中则显示 no export guard | `permission_denied` / `owner_mismatch` / `not_found_or_inaccessible` 统一清空该模块并提示无权限或不可访问，不暴露资源存在性 | Dashboard 不直接确认 candidate；只展示来自 task result 或源页面的 `candidate_refs` / `suggestion_refs` 待处理入口 | 不提供复制或导出；报告复制只能从报告详情进入 | `f6.dashboard.composes_owner_scoped_lists`, `f6.dashboard.async_badge_visible`, `f6.dashboard.no_export_entry` |
| 简历列表 | 浏览、筛选、进入简历详情或新建简历 | `API-RESUME-001`, `API-RESUME-002` | `ResumeSummary[]`, `ResumeDetail` on create；需要 `title`, `target_direction`, `current_version_ref`, `display_summary`, `status`, `updated_at` | 表格 `loading`；create mutation 显示提交中；无 async task | 无简历时展示创建 / 粘贴 Markdown 入口 | `validation_failed` 用于非法 query 或新建字段；`rate_limited` 显示稍后重试；其它读取失败显示 retry | 列表按 owner scope 过滤；跨 owner filter 返回空或错误，不展示他人数据 | N/A：简历不是 candidate；保存成功返回正式 `ResumeDetail` | 不提供 Markdown 下载；只允许页面内编辑 / 预览 | `f6.resume.list.empty_create`, `f6.resume.create.validation_failed`, `f6.resume.no_download` |
| 简历详情 / Markdown 编辑 | 查看、编辑 Markdown 简历和版本状态 | `API-RESUME-003`, `API-RESUME-004` | `ResumeDetail`；`markdown_text`, `current_version_ref`, `status`, `display_summary`, `updated_at`；更新只提交 Markdown 正文并返回新版本 | 详情抽屉 `loading`；保存按钮 `loading`；无 async task | Markdown 为空时展示可编辑空态；项目经历只是 Markdown 内容片段，不生成模块 CRUD | `validation_failed` 定位字段；`stale_version_conflict` 提示刷新并保留本地编辑；`rate_limited` 稍后再试 | `permission_denied` / `owner_mismatch` / `not_found_or_inaccessible` 关闭编辑入口并提示不可访问 | N/A：简历 Markdown 更新不生成 candidate；打磨结果回写必须先走 Asset / confirmation flow | 不提供 Markdown 下载、docx、PDF、文件上传解析或项目经历 module API | `f6.resume.detail.version_conflict`, `f6.resume.markdown_no_file_upload`, `f6.resume.no_module_crud` |
| 岗位 / JD 列表 | 浏览、筛选、进入岗位详情或新建岗位 | `API-JOB-001`, `API-JOB-002` | `JobSummary[]`, `JobDetail`; `title`, `company`, `application_status`, `current_version_ref`, `binding_summary`, `latest_match_summary`, `updated_at` | 表格 `loading`；创建保存中；无 async task；匹配摘要只展示既有结果状态 | 无岗位时展示手动录入入口；`binding_summary.status=not_bound` 时展示绑定入口；`latest_match_summary.status=match_not_generated` 时展示生成入口 | `validation_failed` 定位岗位字段；`rate_limited` 稍后重试；禁止外部材料解析失败态；匹配摘要失败使用 `match_failed` 而非精确概率 | owner scoped list；跨 owner filter 不返回数据 | N/A：岗位手动录入直接成为正式 Job / JobVersion；匹配候选仍来自 JobMatchAnalysis | 不提供外部材料解析岗位入口，不上传 JD 文件；不展示精确通过概率 | `f6.job.list.manual_create_only`, `f6.job.list.binding_match_summary`, `f6.job.create.no_external_parse` |
| 岗位 / JD 创建 / 编辑 | 手动录入或修改岗位职责、要求和投递状态 | `API-JOB-002`, `API-JOB-004` | `CreateJobRequest`, `UpdateJobRequest`, `JobDetail`; `responsibilities`, `requirements`, `application_status`, `current_version_ref` | 表单保存中；无 async task | 新建表单为空态由字段 placeholder 表达；不可从文件导入填充 | `validation_failed` 定位必填职责 / 要求；`stale_version_conflict` 保留输入并提示刷新；`idempotency_conflict` 阻止重复提交覆盖 | 编辑必须校验 job owner；不可访问时关闭抽屉 | N/A：岗位编辑不是 suggestion；不得由 AI 自动生成岗位 | 不提供文件上传解析、URL 抓取或外部材料解析岗位 | `f6.job.form.validation_failed`, `f6.job.form.stale_version_conflict`, `f6.job.form.no_file_parse` |
| 岗位详情 | 查看岗位信息、绑定状态、解绑状态和匹配分析入口 | `API-JOB-003`, `API-BINDING-001` as action, `API-BINDING-002` as action, `API-JOBMATCH-001` as action, `API-JOBMATCH-002` for existing analysis | `JobDetail`, `JobBindingSummary`, `JobMatchSummary`, `JobResumeBindingResponse`, `JobMatchAnalysisResponse`; `current_version_ref`, `binding_summary`, `latest_match_summary`, `score`, `match_points[]`, `preserved_history_refs[]` | 详情 `loading`；绑定 / 解绑提交中；匹配分析创建返回 `queued` / `running` task；详情摘要可显示 `match_running` / `match_low_confidence` / `match_failed` / `match_stale` | 无绑定简历时展示绑定模块；解绑后展示已解绑和重新绑定入口；无匹配分析时展示生成入口 | Job CRUD 不返回 `source_availability`；解绑失败显示 `unbind_failed` 并保留原绑定；新分析创建可因历史来源不可用返回 `source_unavailable`；`generation_failed` / `provider_unavailable` / `task_timeout` 显示重试；`validation_failed` 表示缺少绑定或输入 | job / resume / binding 必须同 owner；失败不暴露他人资源；解绑跨 owner 返回 `owner_mismatch` | 匹配分析可产生 `WeaknessCandidate`；只展示候选入口，不创建正式 Weakness | 不导出岗位或匹配结果；解绑不得删除历史报告 / 复盘 / 匹配结果；`latest_match_summary` 不返回精确通过概率 | `f6.job.detail.binding_required`, `f6.job.detail.unbind_status_visible`, `f6.job.detail.match_summary_visible`, `f6.job.detail.no_exact_probability` |
| 岗位绑定 / 解绑简历 | 将岗位与简历版本绑定，或解除当前绑定 | `API-RESUME-001`, `API-JOB-003`, `API-BINDING-001`, `API-BINDING-002` | `ResumeSummary[]`, `JobDetail`, `JobResumeBindingResponse`; `resume_ref`, `job_ref`, `binding_status`, `base_version_ref`, `unbound_at`, `unbound_by`, `preserved_history_refs[]`, `affected_default_entry_summary` | 候选简历表格 `loading`；绑定提交中；解绑中；已解绑；无 async task | 无简历时引导创建简历；无岗位时回到岗位列表；已解绑后保留历史结果入口并提供重新绑定 | `validation_failed` 表示缺少 resume/job/version；`idempotency_conflict` 阻止重复绑定 / 解绑请求；`stale_version_conflict` 要求刷新版本；`unbind_failed` 保留原绑定状态 | resume、job、version、binding 必须同 owner；owner mismatch 显示不可绑定或不可解绑 | N/A：绑定 / 解绑是显式用户动作，不是 AI suggestion | 不复制、不导出；解绑只改变当前默认绑定，不删除历史结果 | `f6.binding.create.cross_owner_denied`, `f6.binding.empty_resume`, `f6.binding.idempotent`, `binding.delete.success`, `binding.delete.history_preserved`, `binding.delete.cross_user_denied`, `binding.delete.stale_version_conflict` |
| 岗位匹配分析 | 查看 0-100 匹配分、匹配点、不匹配点、加强点和薄弱项候选入口 | `API-JOBMATCH-001`, `API-AITASK-002`, `API-AITASK-003`, `API-JOBMATCH-002`, optional `API-WEAKNESS-002` for candidate extraction | `AiTaskStatusResponse`, `AiTaskResultResponse`, `JobMatchAnalysisResponse`; `score.score_value`, `low_confidence_flags[]`, `evidence_refs`, `trace_refs` | 创建后显示 `queued` / `running`; result 支持 `partial`, `low_confidence`, `validation_failed`, `source_unavailable`, `generation_failed`, `timed_out` | 无分析时显示生成入口；资料不足提示补简历 / 岗位 / 绑定 | `provider_unavailable`, `task_timeout`, `generation_failed` 可重试；`validation_failed` 不展示正式分；`source_unavailable` 选择可用来源 | analysis / task owner scoped；不可访问统一隐藏 | 薄弱项仅为 `WeaknessCandidate` / `candidate_refs`，确认前不得进入正式列表 | 不展示精确通过概率，不导出分析 | `f6.job_match.async_lifecycle`, `f6.job_match.low_confidence_not_success`, `f6.job_match.weakness_candidate_not_formal` |
| 打磨模式主题 / 次主题选择 | 进入打磨会话前选择主题、次主题或自定义主题文本 | `API-POLISH-006` | `PolishTopic[]`, `PolishSubtopic[]`; `topic_id`, `subtopic_id`, `title`, `description`, `requires_job_binding`, `disabled_reason` | 主题列表 `loading`；无 async task | 无可用主题时展示回到简历 / 岗位补充材料入口；禁用主题显示原因 | `validation_failed` 用于非法 query；`permission_denied` / `owner_mismatch` 不暴露他人 binding；自定义主题文本只作为用户输入标签处理 | topic list owner scoped；可选 `resume_job_binding_id` 必须属于当前 actor | N/A：主题/次主题不是正式业务对象，不经 confirmation 写入 formal object | 不导出主题目录；不把 custom topic 文本作为系统指令 | `polish.topic.list.success`, `polish.session.create.invalid_topic` |
| 打磨模式会话 | 创建和查看打磨会话工作台 | `API-POLISH-006`, `API-POLISH-001`, `API-POLISH-002`, `API-PROGRESS-001` | `CreatePolishSessionRequest`, `InterviewSessionResponse`, `ProgressTreeResponse`; `resume_job_binding_id`, `topic_id`, `subtopic_id`, `custom_topic_text`, `session_status`, `current_question_ref`, `progress_position_ref`, `low_confidence_flags[]` | 会话创建提交中；详情和进展树 `loading`；无题目生成时等待用户动作 | 无当前题或无进展节点时展示生成题目入口 | `validation_failed` 缺简历 / 岗位 / source 或 topic/subtopic 无效；`source_unavailable` 阻止发起；`stale_version_conflict` 刷新输入版本 | session / resume_job_binding owner scoped；跨用户 binding 返回 `owner_mismatch` 或不可访问 | N/A：创建会话不是 candidate；后续反馈可产生候选 | 不支持音频 / 视频 / 文件上传解析；不导出会话；custom topic 文本不得作为 prompt 指令执行 | `polish.session.create.with_topic_subtopic`, `polish.session.create.cross_owner_binding_rejected`, `f6.polish.session.progress_owner_scoped` |
| 打磨模式题目生成 | 生成或选择当前打磨题目 | `API-POLISH-003`, `API-AITASK-002`, `API-AITASK-003` | `AiTaskStatusResponse`, `AiTaskResultResponse`, `QuestionResponse`; `question_text`, `evidence_refs[]`, `generated_by_task_id` | 显示 `queued` / `running`; 成功后读取 result；`partial` / `low_confidence` 可展示但需标记 | 无题目时显示生成按钮；无 source 时提示补材料 | `generation_failed`, `provider_unavailable`, `task_timeout` 可重试；`validation_failed` 不写题目；`source_unavailable` 选择可用来源 | task/session owner scoped | 题目不是 formal 写入候选；低置信题目需人工确认或重新生成 | 不暴露 Prompt / provider payload | `f6.polish.question.task_status`, `f6.polish.question.no_prompt_payload` |
| 打磨模式回答保存 | 保存用户当前回答 | `API-POLISH-004` | `CreateAnswerRequest`, `AnswerResponse`; `answer_text`, `answer_round`, `created_at`, `base_question_version_ref` | 保存按钮 `loading`; 无 async task | 空回答显示字段级 `validation_failed`，不提交 | `validation_failed` 保留输入；`stale_version_conflict` 提示题目版本变化；`idempotency_conflict` 阻止重复提交覆盖 | session/question owner scoped | N/A：回答是用户事实，不是 AI candidate | 不导出回答、不进入 copy content | `f6.polish.answer.validation_failed`, `f6.polish.answer.idempotent` |
| 打磨模式反馈 / 评分 / 参考回答 / 考点解析 | 查看点评、失分点、参考回答、考点解析和候选回流入口 | `API-POLISH-005`, `API-SCORING-001`, `API-SCORING-002`, `API-AITASK-002`, `API-AITASK-003` | `AiTaskStatusResponse`, `AiTaskResultResponse`, `FeedbackResponse`, `ScoreResultResponse`; `summary`, `score_ref`, `candidate_refs[]`, `confidence_level`, `evidence_refs[]` | feedback/scoring task 显示 `queued` / `running`; 支持 `partial` / `low_confidence` 展示 | 无反馈时显示生成入口；无评分时不伪造占位分 | `generation_failed`, `provider_unavailable`, `task_timeout`, `validation_failed`, `source_unavailable`; hidden scoring rule 不可见 | answer/session owner scoped | `AssetCandidate` / `WeaknessCandidate` 只显示待确认入口，确认前不进正式对象 | 不复制隐藏评分规则、Prompt 或 provider payload；不导出 | `f6.polish.feedback.candidates_not_formal`, `f6.polish.feedback.no_hidden_rules`, `f6.polish.feedback.low_confidence_visible` |
| 压力面模式会话 | 创建和查看压力面会话工作台 | `API-PRESSURE-001`, `API-PRESSURE-002`, `API-PROGRESS-001` | `InterviewSessionResponse`, `ProgressTreeResponse`; `mode=pressure`, `session_status`, `current_question_ref`, `progress_position_ref` | 会话创建提交中；详情和进展树 `loading`; 无 async task | 无当前追问时展示首题生成入口 | `validation_failed` 缺输入；`source_unavailable` 阻止发起；恢复失败按 progress/session 状态展示 | owner scoped | N/A：会话不是 candidate；压力反馈可能产生建议 | 不继承打磨模式“继续打磨”动作；不导出 | `f6.pressure.session.action_boundary`, `f6.pressure.session.owner_scoped` |
| 压力面题目生成 | 生成首题或连续追问 | `API-PRESSURE-003`, `API-AITASK-002`, `API-AITASK-003` | `AiTaskStatusResponse`, `AiTaskResultResponse`, `QuestionResponse`; `question_type=pressure_first/pressure_follow_up`, `evidence_refs[]` | 显示 `queued` / `running`; `partial` / `low_confidence` 标记追问可信度 | 无上一回答时只允许首题；无来源时提示补材料 | `generation_failed`, `provider_unavailable`, `task_timeout`, `validation_failed`, `source_unavailable` | task/session owner scoped | 题目不是 formal candidate；失败不得 late write | 不暴露 Prompt / provider payload | `f6.pressure.question.follow_up_owner_scoped`, `f6.pressure.question.failure_visible` |
| 压力面回答保存 | 保存压力面回答并推进连续问答 | `API-PRESSURE-004` | `AnswerResponse`; `question_id`, `answer_text`, `answer_round`, `created_at` | 保存中禁用重复提交；无 async task | 空回答显示字段错误 | `validation_failed`, `stale_version_conflict`, `idempotency_conflict` | session/question owner scoped | N/A：用户回答不是 candidate | 不导出回答 | `f6.pressure.answer.save_success`, `f6.pressure.answer.validation_failed` |
| 压力面反馈 / 整场评分 | 查看压力反馈、整场评分和报告输入状态 | `API-PRESSURE-005`, `API-SCORING-001`, `API-SCORING-002`, `API-AITASK-002`, `API-AITASK-003` | `FeedbackResponse`, `ScoreResultResponse`, `AiTaskStatusResponse`, `AiTaskResultResponse`; `summary`, `score_value`, `confidence_level`, `candidate_refs[]` | 反馈 / 评分 task `queued` / `running`; `partial` / `low_confidence` 可见 | 无反馈时展示生成入口；无整场评分不展示假分 | `generation_failed`, `provider_unavailable`, `task_timeout`, `validation_failed`, `source_unavailable` | owner scoped | 可产生 Weakness / Training / Asset candidate refs；确认前不写正式对象 | 不展示精确通过概率；不导出 | `f6.pressure.feedback.session_score_no_probability`, `f6.pressure.feedback.candidate_only` |
| 进展树 | 查看节点、当前进展、节点生成题目入口 | `API-PROGRESS-001`, plus mode-specific question task APIs | `ProgressTreeResponse`; `nodes[]`, `current_position.node_id`, `node_status` | 进展树 `loading`; 节点生成题目显示 task `queued` / `running` | 无节点时提示资料不足或未开始会话 | 节点生成失败显示 `generation_failed` 可重试；`not_found_or_inaccessible` 不暴露会话；历史来源不可用由具体 AI result / EvidenceRef 表达 | session owner scoped | N/A：节点建议不是正式训练建议；若产生建议必须走 SuggestionRef | 不导出进展树 | `f6.progress_tree.owner_scoped`, `f6.progress_tree.node_status_visible` |
| 面试报告列表或入口 | 从模拟面试列表 / 详情进入报告；当前无一级报告列表 | `API-POLISH-002` / `API-PRESSURE-002` 获取 session report ref；`API-REPORT-001` 创建报告；`API-REPORT-002` 读取报告 | `InterviewSessionResponse`, `AiTaskStatusResponse`, `ReportResponse`; report_id 来源于会话或报告 task result | 报告生成 `queued` / `running`; 报告入口读取 `loading` | 无报告时展示生成入口；无一级报告列表是 F2/F3 冻结边界 | `generation_failed`, `provider_unavailable`, `task_timeout`, `source_unavailable`；无 report_id 不当作 404 噪音 | session/report owner scoped | 报告可产生沉淀 candidate refs，但报告本身不自动沉淀 | 入口不提供下载；复制必须进入报告详情 copy content | `f6.report.entry.no_first_level_list`, `f6.report.entry.create_async` |
| 面试报告详情 | 查看报告分项、评分、风险提示、建议和沉淀入口 | `API-REPORT-002`, optional `API-SCORING-002`, `API-ASSET-002`, `API-WEAKNESS-002`, `API-TRAINING-002` for 沉淀任务 | `ReportResponse`, `ScoreResultResponse`, `AiTaskStatusResponse`; `sections[]`, `score_ref`, `copy_content_available`, `source_availability`, `confidence_level` | 详情 `loading`; 沉淀任务 `queued` / `running`; 报告 `partial` / `low_confidence` 可见 | 报告未生成或 sections 空时展示生成 / 返回来源 | `source_unavailable`, `generation_failed`, `provider_unavailable`, `task_timeout`, `validation_failed`; 风险提示不得确定化 | report/session owner scoped | 沉淀到资产 / 薄弱项 / 训练建议时只创建 candidate / suggestion，必须确认 | 只显示 copy 入口；不显示文件导出、PDF、Markdown 下载 | `f6.report.detail.copy_entry_only`, `f6.report.detail.no_exact_probability`, `f6.report.detail.candidate_deposit` |
| 报告 copy content | 复制报告授权内容并记录审计 | `API-REPORT-003`, `API-REPORT-004` | `ReportCopyContentResponse`, `RecordCopyEventRequest`; `clipboard_blocks[]`, `copy_boundary=clipboard_only`, `export_artifact=null`, `redaction_applied` | copy content 读取 `loading`; copy event 提交中；无 async task | `clipboard_blocks[]` 为空或 `copy_content_available=false` 禁用复制并说明 | `copy_boundary_violation`, `validation_failed`, `source_unavailable`, `rate_limited`, `idempotency_conflict`; `export_not_supported` 用于误触下载/导出请求 | report owner scoped；复制失败也审计 | N/A：复制不是 confirmation；复制不得触发沉淀 | 只能 clipboard；不得返回 filename、download URL、file id 或 export artifact | `f6.report.copy.clipboard_only`, `f6.report.copy.audit_without_body`, `f6.report.copy.no_export_artifact` |
| 面试复盘列表 | 浏览、筛选、分页查看模拟 / 真实复盘 | `API-REVIEW-005` | `ReviewSummary[]`; `review_id`, `review_type`, `display_summary`, `source_summary`, `status`, `confidence_level`, `source_availability`, `related_report_ref`, `related_session_ref`, `next_actions[]`, `created_at`, `updated_at` | 列表 `loading`; 生成中行显示 `generating`; 低置信行显示待校对；source unavailable 行显示来源不可用 | 空列表展示新增复盘入口；无 matching filter 时保留筛选条件和重置入口 | `validation_failed` 定位非法 filter；`generation_failed` 行级可重试；`source_unavailable` 行级可见；分页 cursor 无效要求重置 | review owner scoped；列表不泄露他人复盘数量 | 复盘行可暴露 candidate / suggestion 待处理入口，但不得直接写正式对象 | 不导出列表；复制必须进入复盘详情 copy content | `reviews.list.success`, `reviews.list.filter_by_type`, `reviews.list.owner_scoped`, `reviews.list.source_unavailable_visible` |
| 模拟面试复盘 | 从系统内会话 / 报告生成复盘 | `API-REVIEW-001`, `API-AITASK-002`, `API-AITASK-003`, `API-REVIEW-004` | `CreateReviewTaskRequest`, `AiTaskStatusResponse`, `AiTaskResultResponse`, `ReviewResponse`; `review_type=mock`, `items[]`, `candidate_refs[]` | 复盘 task `queued` / `running`; result 支持 `partial` / `low_confidence` | 无可复盘会话 / 报告时提示返回来源 | `generation_failed`, `provider_unavailable`, `task_timeout`, `validation_failed`, `source_unavailable` | source session/report owner scoped | 复盘提炼的 Asset / Weakness / Training 仅为 candidate / suggestion | 复盘相关复制只允许页面复制，不生成文件 | `f6.review.mock.async_lifecycle`, `f6.review.mock.candidate_only` |
| 真实面试复盘输入 | 用户录入真实面试信息并确认来源可信度 | `API-REVIEW-002` | `CreateRealInterviewInputRequest`, `ReviewResponse`; `review_type=real_input`, `source_refs[]`, `low_confidence_flags[]` | 保存中；无 async task | 表单空字段显示待补充；不要求拥有完整真实面试过程 | `validation_failed` 定位题目 / 回答 / 反馈；`stale_version_conflict` 适用于关联简历 / 岗位版本；`idempotency_conflict` 阻止重复提交 | job/resume/input owner scoped | 输入结构化可要求用户确认；不得自动生成正式 Weakness / Asset / Training | 不上传文件、不解析外部材料、不承诺真实结果预测 | `f6.review.real_input.manual_only`, `f6.review.real_input.requires_confirmation` |
| 真实面试复盘结果 | 查看真实面试复盘、低置信度和沉淀入口 | `API-REVIEW-003`, `API-AITASK-002`, `API-AITASK-003`, `API-REVIEW-004` | `AiTaskStatusResponse`, `AiTaskResultResponse`, `ReviewResponse`; `review_type=real`, `review_status`, `candidate_refs[]`, `low_confidence_flags[]` | 生成 `queued` / `running`; `partial` / `low_confidence` 可见 | 无结果时显示生成入口；材料不足时提示补充输入 | `source_unavailable`, `generation_failed`, `provider_unavailable`, `task_timeout`, `validation_failed` | input/review owner scoped | 复盘产生的沉淀项必须进入 candidate / suggestion / confirmation | 不展示精确通过概率，不导出复盘文件 | `f6.review.real.low_confidence_visible`, `f6.review.real.no_probability`, `f6.review.real.candidate_only` |
| 复盘 copy content | 复制复盘授权内容并记录审计 | `API-REVIEW-006`, `API-REVIEW-007` | `ReviewCopyContentResponse`, `RecordReviewCopyEventRequest`, `ReviewCopyEventResponse`; `clipboard_blocks[]`, `copy_boundary=clipboard_only`, `redaction_applied`, `audit_event_ref` | copy content 读取 `loading`; copy event 提交中；无 async task | 复盘无可复制内容时禁用复制并说明 | `copy_boundary_violation`, `validation_failed`, `source_unavailable`, `rate_limited`, `idempotency_conflict`; `export_not_supported` 用于误触下载/导出请求 | review owner scoped；复制失败也审计 | N/A：复制不是 confirmation；复制不得触发沉淀 | 不返回 system prompt、provider payload、隐藏评分规则、未脱敏第三方 / 公司 / 面试官 / 他人隐私；审计不记录正文 | `review_copy.get.no_prompt_payload`, `review_copy.get.third_party_redacted`, `review_copy.audit.no_body_logged`, `review_copy.boundary_violation` |
| 资产库列表 | 查看正式资产和来源 | `API-ASSET-001` | `AssetResponse[]`; `title`, `asset_type`, `status`, `source_refs[]`, `current_version_ref` | 表格 `loading`; 无 async task | 无资产时引导从打磨 / 报告 / 复盘沉淀 | `source_unavailable` 显示来源不可用；读取失败可 retry | owner scoped list | 列表只展示正式 Asset；未确认 AssetCandidate 不应混入正式列表 | 不允许资产内容拷贝类操作；不导出资产 | `f6.asset.list.formal_only`, `f6.asset.list.source_visible`, `f6.asset.list.no_copy` |
| 资产候选确认 | 查看、编辑、确认、跳过、拒绝资产候选或版本建议 | `API-ASSET-002`, `API-AITASK-002`, `API-AITASK-003`, `API-ASSET-003`, `API-ASSET-004` | `AiTaskStatusResponse`, `AiTaskResultResponse`, `AssetCandidateResponse`, `ConfirmCandidateRequest`, `AssetResponse`; `candidate_status`, `quality_hint_ref`, `version_suggestion_ref`, `user_confirmation_required` | 候选生成 `queued` / `running`; confirmation 提交中；`low_confidence` 候选需标记 | 无候选时返回来源页面；无 target_asset 时按 new asset 处理 | `validation_failed`, `stale_version_conflict`, `source_unavailable`, `generation_failed`, `provider_unavailable`, `task_timeout`, `idempotency_conflict` | candidate / target_asset owner scoped | `confirm` / `edit` -> 正式 Asset / AssetVersion；`skip` / `reject` 不写正式对象；`merge` 仅在有 target 时允许 | 不导出候选内容，不复制 provider payload | `f6.asset_candidate.confirm_formal_requires_user_action`, `f6.asset_candidate.version_suggestion_confirmed_only` |
| 低置信候选校对保存 | 保存用户对低置信 candidate / suggestion 的校对内容 | `API-CANDIDATE-001` | `CandidateCorrectionRequest`, `CandidateCorrectionResponse`; `corrected_content`, `correction_reason`, `base_candidate_version_ref`, `confidence_override_reason`, `validation_status`, `user_confirmation_required`, `next_actions[]` | 保存中；保存成功；validation failed；无 async task | 无 candidate 或 candidate 不可访问时返回来源页面 | `stale_version_conflict` 保留用户修正；`validation_failed` 返回校验问题；`source_unavailable` 要求选择可用来源 | candidate / suggestion owner scoped；跨用户返回 `owner_mismatch` 或不可访问 | 校对内容仍是 candidate correction，不直接污染 Prompt source 或 formal object；用户确认后才成为后续 task input 或正式输入 | 不复制校对正文到日志、Prompt 源或 provider payload | `candidate.correction.save.success`, `candidate.correction.stale_version_conflict`, `candidate.correction.validation_failed`, `candidate.correction.cross_user_denied` |
| 内容沉淀目标确认 | 选择、编辑、确认或跳过沉淀目标 | `API-DEPOSIT-001`, plus domain confirmation endpoints as needed | `ConfirmDepositTargetRequest`, `DepositTargetConfirmationResponse`, `DepositTarget`; `target_type`, `target_ref`, `confirmation_action`, `created_formal_ref`, `target_status`, `next_actions[]` | 待选择沉淀目标；确认提交中；已确认；已跳过；目标不可用；目标冲突 | 无可沉淀内容时显示跳过和返回来源；目标禁用时说明原因 | `target_unavailable`, `target_conflict`, `validation_failed`, `stale_version_conflict`, `source_unavailable`, `idempotency_conflict` | source / candidate / target_ref 必须 owner scoped；跨用户 target 拒绝 | Prompt 只能给 target suggestion；正式 Asset / Weakness / TrainingRecommendation / input ref 必须由用户确认或显式动作创建 | 不静默写入，不导出沉淀内容；审计只记录摘要和引用 | `deposit_target.confirm.asset`, `deposit_target.confirm.weakness`, `deposit_target.skip`, `deposit_target.cross_user_denied`, `deposit_target.source_unavailable` |
| 薄弱项列表 | 查看正式薄弱项、来源证据和训练入口 | `API-WEAKNESS-001`, optional `API-TRAINING-001` | `WeaknessResponse[]`, `TrainingSuggestionResponse[]`; `title`, `status`, `severity_hint`, `evidence_refs[]`, `updated_at` | 表格 / 详情 `loading`; 训练建议区域可显示 `queued` / `running` via task refs | 无薄弱项时展示来源说明；无训练建议时展示生成入口 | `source_unavailable` 表示证据不可用；读取失败 retry；`generation_failed` 适用于训练建议生成 | owner scoped list | 只展示正式 Weakness；WeaknessCandidate 不经确认不得进入列表 | 不导出薄弱项或证据正文 | `f6.weakness.list.formal_only`, `f6.weakness.list.evidence_summary` |
| 薄弱项候选确认 / 合并 | 查看候选、合并建议并确认、编辑、跳过、拒绝或合并 | `API-WEAKNESS-002`, `API-AITASK-002`, `API-AITASK-003`, `API-WEAKNESS-003` | `AiTaskStatusResponse`, `AiTaskResultResponse`, `WeaknessCandidateResponse`, `ConfirmCandidateRequest`, `WeaknessResponse`; `candidate_status`, `merge_suggestion_refs[]`, `user_confirmation_required` | 候选生成 `queued` / `running`; confirmation 提交中；`low_confidence` 需人工校对 | 无候选时返回来源；无可合并对象时只允许创建新 weakness 或跳过 | `validation_failed`, `stale_version_conflict`, `source_unavailable`, `generation_failed`, `provider_unavailable`, `task_timeout`, `idempotency_conflict` | candidate / target_weakness owner scoped | `confirm` / `edit` 创建正式 Weakness；`merge` 更新目标 Weakness；`skip` / `reject` 不写正式对象 | 不导出候选或证据正文 | `f6.weakness_candidate.merge_requires_user_action`, `f6.weakness_candidate.low_confidence_visible` |
| 训练建议列表 | 查看训练建议、优先级提示和关联薄弱项 / 资产 | `API-TRAINING-001`, `API-TRAINING-002`, `API-AITASK-002`, `API-AITASK-003` | `TrainingSuggestionResponse[]`, `AiTaskStatusResponse`, `AiTaskResultResponse`; `topic`, `suggestion_status`, `priority_hint`, `weakness_refs[]`, `asset_refs[]` | 列表 `loading`; 生成 task `queued` / `running`; 支持 `partial` / `low_confidence` | 无训练建议时展示生成入口或返回薄弱项 / 复盘 | `generation_failed`, `provider_unavailable`, `task_timeout`, `validation_failed`, `source_unavailable` | owner scoped list | candidate 状态可展示但不得自动创建 TrainingTask；确认后才成为正式建议 | 不导出训练建议 | `f6.training.list.no_auto_task`, `f6.training.list.low_confidence_visible` |
| 训练建议确认 | 确认、编辑、跳过或拒绝训练建议 | `API-TRAINING-003` | `ConfirmCandidateRequest`, `TrainingSuggestionResponse`; `suggestion_status`, `user_confirmation_required` | confirmation 提交中；无 async task | 无 suggestion 时返回列表 | `validation_failed`, `stale_version_conflict`, `idempotency_conflict`, `source_unavailable` | suggestion owner scoped | `confirm` / `edit` -> confirmed recommendation；不自动启动 `TrainingTask`; `skip` / `reject` 保持非正式或已跳过 | 不导出训练建议，不自动创建训练任务 | `f6.training.confirm.no_auto_training_task`, `f6.training.confirm.idempotent` |
| AI task status surface | 查看任意生成任务状态、结果、重试或取消 | `API-AITASK-002`, `API-AITASK-003`, `API-AITASK-004`, `API-AITASK-005` | `AiTaskStatusResponse`, `AiTaskResultResponse`, `RetryAiTaskRequest`, `CancelAiTaskRequest`; `status`, `retryable`, `user_visible_status`, `candidate_refs[]`, `suggestion_refs[]`, `validation_result_ref` | 原生覆盖 `queued` / `running` / `partial` / `low_confidence` / `validation_failed` / `source_unavailable` / `generation_failed` / `timed_out` / `cancelled` | task 不存在或不可访问时不暴露存在性 | `provider_unavailable`, `task_timeout`, `generation_failed`, `validation_failed`, `rate_limited`, `idempotency_conflict` | task owner scoped；`not_found_or_inaccessible` 隐藏他人 task | result 中 candidate / suggestion 仅给入口，不能 late formal write；cancel 后不得写正式对象 | 不暴露 provider payload、Prompt、completion 或隐藏评分规则 | `f6.ai_task.status_all_states`, `f6.ai_task.retry_scope_safe`, `f6.ai_task.no_late_formal_write` |
| 用户设置 / 账号状态相关 surface | 查看当前账号状态、退出或基础偏好入口 | 当前 API_SPEC 未冻结账号偏好 endpoint；F6 只可读取应用登录态 / session bootstrap；如需持久化偏好，列入 待补缺口（remaining gap） | 账号状态最小字段应为 display name / role / account status / session state；不在本 API contract 中作为业务 resource | UI 壳加载时可显示 session loading；业务 API 401 映射为未登录 / session 过期 | 未登录显示登录入口或不可访问；无偏好数据不阻断业务 | `unauthenticated` / `permission_denied` / `rate_limited`; 不使用 provider errors | 只展示当前 actor，不接受请求体 owner_id | N/A：账号设置不产生业务 candidate | 不提供个人数据导出或下载 | `f6.settings.no_business_data_export`, `f6.settings.session_expired_visible`; 待补缺口（remaining gap）: persisted account preferences API |

### 6.2 F6 状态映射

以下 19 个状态必须在 F6 页面适配层中显式处理。页面矩阵某一行没有列出该状态时，按本表的 `N/A rule / reason` 处理；不得把未知状态当作普通 `success`。

| 状态 | F6 处理规则 | 适用范围 | N/A 规则 / 原因 |
|---|---|---|---|
| `loading` | 表格、卡片、抽屉、报告和工作台使用 loading skeleton 或按钮 loading；不得遮挡已有主体 | 全部页面 | N/A 不允许；所有页面都必须有加载态 |
| `empty` | 使用页面或模块空态，提供创建、返回来源、补充材料或等待生成入口 | 列表、详情模块、报告、复盘、候选确认 | 对纯 mutation 按字段级空输入处理为 `validation_failed` |
| `success` | 展示正式 schema 数据并同步页面状态；Toast 不能作为唯一反馈 | 全部成功读取 / mutation | N/A 不允许；所有成功响应都必须可见 |
| `queued` | 显示任务已排队和 `user_visible_status`，允许返回列表或等待 | 所有 AI task 创建 / status surface | 同步 CRUD N/A，原因是无异步任务 |
| `running` | 显示生成中、禁用重复提交，可轮询或由 F5 事件机制刷新 | 所有 AI task | 同步 CRUD N/A |
| `partial` | 展示可用部分并标记不完整；不得当作高置信完成态 | job match、feedback、report、review、training、task result | 纯列表或保存 N/A，原因是无生成结果 |
| `low_confidence` | 展示低置信标记、原因、可校对 / 补充 / 重试动作 | job match、评分、反馈、报告、复盘、候选、训练、task result | 纯 CRUD N/A，除非 response envelope 返回 `low_confidence_flags` |
| `validation_failed` | 字段级错误定位或生成结果校验失败；不得写 formal object | 全部 mutation、AI output validation | 只读详情 N/A，除非读取 schema 明确返回 validation result |
| `source_unavailable` | 展示来源删除 / 归档 / 禁用 / 不可访问；新生成需停止或选择可用来源 | 生成类页面、历史报告 / 复盘 / 资产 / 弱项证据 | 无来源依赖页面 N/A，例如账号设置 |
| `generation_failed` | 展示生成失败、可重试条件和保留输入；不得展示完成态 | AI task result、报告、复盘、反馈、训练、候选生成 | 同步 CRUD N/A |
| `provider_unavailable` | 展示稍后重试和 provider 不可用摘要；不得扩大上下文或启用未授权检索 | AI task create/status/retry | 非 AI 页面 N/A |
| `task_timeout` | 展示超时、可重试或取消后的状态；不得 late formal write | AI task status/result | 非 AI 页面 N/A |
| `rate_limited` | 展示稍后重试、`Retry-After` 或 rate limit meta；避免重复提交 | 全部 API，尤其 LLM task、保存和复制审计 | N/A 不允许；全局错误码 |
| `stale_version_conflict` | 保留用户输入，提示刷新 / 对比 / 重试；需要 `base_version_ref` / `target_version_ref` | 编辑简历、岗位、候选确认、回答保存等版本化 mutation | 无版本 mutation N/A |
| `unbinding` | 显示解除绑定中，禁用重复解绑动作，保留当前绑定摘要直到 mutation 返回 | 岗位详情、岗位绑定简历 | 非绑定页面 N/A |
| `unbound` | 显示已解绑、重新绑定入口和历史报告 / 复盘 / 匹配结果仍可回看的提示 | 岗位详情、岗位绑定简历 | 非绑定页面 N/A |
| `unbind_failed` | 显示解除绑定失败，保留原绑定状态和重试入口 | 岗位详情、岗位绑定简历 | 非绑定页面 N/A |
| `pending_deposit_target` | 显示待选择沉淀目标，要求用户确认、编辑、跳过或返回来源 | 内容沉淀确认、candidate confirmation | 非沉淀页面 N/A |
| `deposit_target_unavailable` | 显示目标不可用和禁用原因，不允许静默写入 | 内容沉淀确认 | 非沉淀页面 N/A |
| `deposit_target_conflict` | 显示目标冲突，要求用户重新选择目标或编辑内容 | 内容沉淀确认 | 非沉淀页面 N/A |
| `permission_denied` | 显示无权限，不展示敏感资源摘要 | 全部业务 API | N/A 不允许；全局错误码 |
| `owner_mismatch` | 显示不可访问或资源不匹配，不暴露他人资源存在性 | 复合资源、绑定、生成、确认、复制 | N/A 不允许；全局 owner boundary |
| `not_found_or_inaccessible` | 详情、task、report、candidate 不存在或不可访问时统一返回来源页 | 全部详情 / task / candidate / report | N/A 不允许；避免资源枚举 |
| `idempotency_conflict` | 阻止重复 mutation 覆盖；提示刷新或重新提交新的幂等 key | 所有 required idempotency mutation | GET / list N/A，原因是不要求 `Idempotency-Key` |
| `export_not_supported` | 显示“仅支持页面复制，不支持文件导出”并记录 no export assertion | 任何误触 export / download / file / pdf / docx / markdown-file 行为 | 正常页面不应触发；但 F7 必须断言无入口、无 route |

### 6.3 F6 前端字段需求

每个 F6 页面 view model 必须能从 success envelope、error envelope、response data schema、`meta` 或 task result 中取得以下字段族。若当前 schema 未提供页面需要的具体展示字段，F6 不得发明假数据，必须按 §6.6 待补缺口（remaining gap） 处理。

| 字段需求 | API 来源 | F6 使用规则 |
|---|---|---|
| display title / summary | `title`, `topic`, `summary`, `user_visible_status`, `sections[].title`, `EvidenceRef.summary` | 页面标题、列表名称、卡片摘要必须来自 schema；不得用 Prompt 输出或隐藏 payload 拼接 |
| status | envelope `status`, resource `status`, `session_status`, `report_status`, `review_status`, `candidate_status`, `suggestion_status`, `AiTaskStatusResponse.status` | 每页必须映射到 §6.2；未知 enum 必须进入 error / manual review，不当作 success |
| timestamps | `created_at`, `updated_at`, `generated_at`, `timeout_at`, `cancelled_at`, `meta.version` 或任务 / 确认记录 timestamp | 列表和详情优先展示对象更新时间；AI task 至少展示用户可见状态，不得伪造时间 |
| version / current_version_ref | `current_version_ref`, `base_version_ref`, `target_version_ref`, `VersionRef`, `resume_ref`, `job_ref` | 编辑、绑定、确认和历史结果必须保留版本引用，用于 stale conflict 和稳定回看 |
| confidence_level | `confidence_level`, `EvidenceRef.confidence_level`, scoring / report / review fields | 低置信、证据不足和风险提示必须显示用户可见降级 |
| source_availability | AI 结果、历史引用、`EvidenceRef`、`TraceRef`、`Report`、`Review`、`JobMatchAnalysis`、`ScoreResult` 的 `source_availability` / `SourceAvailability.status` / `source_refs[]` | 来源不可用时阻止新生成或展示历史 AI 结果来源状态；Resume / Job 基础 CRUD 不使用该字段 |
| low_confidence_flags | envelope `low_confidence_flags`, `LowConfidenceFlag[]`, response data `low_confidence_flags[]` | 作为警告、校对入口和 next action 来源 |
| validation_status | `validation_result_ref.status`, `ValidationResultRef.status`, task result validation fields | `validation_failed` 不得进入正式展示；可进入修复 / retry / manual review |
| evidence_refs / displayable_evidence_summary | `evidence_refs[]`, `EvidenceRef.summary`, `ScoreEvidenceLink` 的可展示摘要 | 页面只展示可脱敏摘要或 ref；不得读取原始敏感正文 |
| trace_id / trace_refs | envelope `trace_id`, `trace_refs[]`, `TraceRef` | 默认仅用于问题排查 / 支持信息；前端不得展开 provider payload、Prompt 或隐藏评分规则 |
| next_actions | envelope `next_actions`, `LowConfidenceFlag.recommended_action`, error `user_action`, task `retryable` | 按 `confirm` / `edit` / `skip` / `retry` / `manual_review` 渲染可操作入口 |
| confirmation_required | envelope `confirmation_required`, `user_confirmation_required` | true 时必须进入 confirmation surface；不得静默写 formal object |
| candidate_refs / suggestion_refs | envelope `candidate_refs`, `suggestion_refs`, `AiTaskResultResponse.candidate_refs[]`, `suggestion_refs[]` | 只作为入口引用；正式 Asset / Weakness / Training 必须由确认 endpoint 返回 |
| copyable content fields | `ReportCopyContentResponse.clipboard_blocks[]`, `copy_boundary`, `export_artifact=null`, `redaction_applied`, `copy_content_id` | 只服务 clipboard；不得渲染下载、文件名或导出物 |
| user_visible_status for async task | `AiTaskStatusResponse.user_visible_status` | `queued` / `running` / `partial` / `low_confidence` / failure 状态必须有用户可读摘要 |

### 6.4 用户确认流和 formal object 转换

F6 所有 candidate / suggestion / confirmation surface 必须使用 `ConfirmCandidateRequest` 与对应 confirmation endpoint，且必须保留 `target_version_ref` 防 stale update。以下对象不得在用户确认前升级为 formal object。

| 对象 | F6 入口 | 允许用户动作 | API / schema | 正式对象转换（Formal object） |
|---|---|---|---|---|
| `AssetCandidate` | 报告、复盘、打磨反馈、资产候选确认 | `confirm` / `edit` / `skip` / `reject` / `manual_review` | `API-ASSET-003`, `API-ASSET-004`, `AssetCandidateResponse`, `ConfirmCandidateRequest` | `confirm` / `edit` 成功后返回 `AssetResponse`，才允许展示为正式 `Asset` / `AssetVersion` |
| `AssetVersionSuggestion` | 资产候选确认中的版本更新建议 | `confirm` / `edit` / `skip` / `reject` / `manual_review` | `AssetCandidateResponse.version_suggestion_ref`, `API-ASSET-004` | 用户确认后才允许发布、替换或覆盖正式 `AssetVersion` |
| `WeaknessCandidate` | 岗位匹配、报告、复盘、反馈后的薄弱项候选确认 | `confirm` / `edit` / `skip` / `reject` / `manual_review` | `API-WEAKNESS-002`, `API-WEAKNESS-003`, `WeaknessCandidateResponse` | `confirm` / `edit` 成功后返回 `WeaknessResponse`，才进入正式薄弱项列表 |
| `WeaknessMergeSuggestion` | 薄弱项候选确认 / 合并 surface | `merge` / `edit` / `skip` / `reject` / `manual_review` | `WeaknessCandidateResponse.merge_suggestion_refs[]`, `ConfirmCandidateRequest.target_formal_ref` | `merge` 成功后才更新目标 `Weakness`；失败或跳过不改变 formal object |
| `TrainingSuggestion` / `TrainingRecommendation` candidate | 训练建议列表、复盘报告、薄弱项详情 | `confirm` / `edit` / `skip` / `reject` / `manual_review` | `API-TRAINING-001`, `API-TRAINING-003`, `TrainingSuggestionResponse` | 确认后才成为正式训练建议；不得自动创建 `TrainingTask` |
| Report / Review 中需用户确认的沉淀项 | 报告详情、模拟复盘、真实复盘、内容沉淀确认抽屉 | 按目标分别 `confirm` / `edit` / `skip` / `reject` / `manual_review` | `candidate_refs[]`, `suggestion_refs[]`, `API-ASSET-*`, `API-WEAKNESS-*`, `API-TRAINING-*` | Report / Review 本身可读，但其沉淀项必须先成为 candidate / suggestion，再经确认 endpoint 写 formal object |
| Candidate / draft / suggestion -> formal object | 所有 confirmation surface | 用户确认、编辑、合并或显式业务动作 | `UserConfirmationRef`, `AuditEvent`, `IdempotencyRecord` | 只有 confirmation response 成功且返回 formal schema 后，F6 才更新正式列表；`skip` / `reject` / `manual_review` 不写 formal object |

### 6.5 F6 不得实现的能力

F6 页面、组件、mock adapter、E2E fixture 和 API client 均不得出现以下能力或入口：

- 文件导出入口。
- PDF 导出入口。
- Markdown 下载入口。
- Word / docx 下载入口。
- 文件上传解析入口。
- 外部材料解析岗位入口。
- 精确通过概率、录取概率、offer 概率或通过率百分比展示。
- `system prompt`、Prompt 模板、provider request / response payload、completion 原文、隐藏评分规则、内部校准细节展示。

F6 如果收到 `/exports`、`/download`、`/files`、`/pdf`、`/docx`、`/markdown-file`、`/report-file`、`filename`、`download_url`、`export_artifact` 非 null 或类似字段，必须按 `export_not_supported` / `copy_boundary_violation` 处理，并作为 F7 contract failure。

### 6.6 与 F2 / F3 一致性和待补缺口（remaining gaps）

- 本矩阵不改变 `UX_SPEC.md` / `UI_DESIGN_SYSTEM.md` 已冻结页面体系，不新增独立项目一级入口、独立报告一级入口、独立报告复制一级入口或独立 candidate inbox。
- 报告当前没有一级列表；F6 报告入口来自模拟面试列表 / 详情、会话详情、报告生成结果或已有 report ref。若 F6 后续需要“报告历史列表”，必须另行补 API / UX / Backlog，不得在前端自行发明。
- 工作台当前没有独立 dashboard aggregate API；F6 可以组合读取 owner-scoped list APIs。若组合读取性能或排序无法满足实现，需要后续补 dashboard summary endpoint。
- 用户设置 / 账号状态 surface 只允许承接当前登录态和会话过期表达；持久化账号偏好、通知设置、管理员管理台 API 尚未在本文件冻结，属于 待补缺口（remaining gap），不能阻断本轮 AR-F4-F8-002 的页面 / API / 状态矩阵修复。
- 候选列表发现当前通过 `candidate_refs` / `suggestion_refs` 和源页面进入；若 F6 需要全局待确认中心，需要后续补 candidate inbox API 和 UX，不得复用正式 Asset / Weakness / Training 列表混展示。
- `UX_SPEC.md` 和 `UI_DESIGN_SYSTEM.md` 中仍标记为字段待复核的页面，不由 F6 自行补字段；F6 只能消费本 API contract 已冻结的 schema 字段，并把缺口列入后续 API / UX refinement。

## 7. 逐接口字段级详情

通用约束：所有接口默认 `Auth: required`，成功响应使用 `ApiSuccessEnvelope`，错误响应使用 `ApiErrorEnvelope`。`敏感性 / 是否可记录` 中的 `sensitive_not_loggable` 表示字段可持久化但不得进入日志、trace 明文或 copy event；`sensitive_summary_only` 表示只允许脱敏摘要进入可观测性或前端摘要。

### API-RESUME-001 列出简历（List resumes）

方法（Method）： GET
路径（Path）： `/api/v1/resumes`
领域（Domain）： Resume
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： 按 actor owner scope 过滤列表
关联数据对象： Resume, ResumeVersion, OwnerRef
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.resume.list.owner_scoped, api.resume.list.validation_failed, api.resume.list.cross_user_denied

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume | 资源域 | loggable |
| data.resume_id | 是 | string | res_* | 简历 ID | loggable |
| data.title | 是 | string | 1..120 | 简历标题 | loggable |
| data.target_direction | 否 | string | <=120 | 目标方向 | loggable |
| data.current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本引用 | loggable |
| data.status | 是 | enum | active / archived / deleted | 简历状态 | loggable |
| data.display_summary | 否 | string | redacted summary | 列表摘要；不得替代 Markdown 正文 | sensitive_summary_only |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| meta.pagination | 否 | PaginationMeta | cursor pagination | 列表分页信息 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.resume.list.owner_scoped`
- `api.resume.list.validation_failed`
- `api.resume.list.cross_user_denied`

### API-RESUME-002 创建简历（Create resume）

方法（Method）： POST
路径（Path）： `/api/v1/resumes`
领域（Domain）： Resume
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： 服务端从 session 推导 owner, 请求体不得包含 owner_id
关联数据对象： Resume, ResumeVersion, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.resume.create.success, api.resume.create.validation_failed, api.resume.create.cross_user_denied, api.resume.create.idempotency_required, api.resume.create.idempotency_conflict

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| title | 是 | string | 1..120 | 简历标题 | loggable |
| markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| target_direction | 否 | string | <=120 | 目标方向 | loggable |
| client_draft_id | 否 | string | client generated | 客户端草稿 ID | loggable |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume | 资源域 | loggable |
| data.resume_id | 是 | string | res_* | 简历 ID | loggable |
| data.title | 是 | string | 1..120 | 简历标题 | loggable |
| data.markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| data.status | 是 | enum | active / archived / deleted | 简历状态 | loggable |
| data.display_summary | 否 | string | redacted summary | 展示摘要；不得替代 Markdown 正文 | sensitive_summary_only |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.resume.create.success`
- `api.resume.create.validation_failed`
- `api.resume.create.cross_user_denied`
- `api.resume.create.idempotency_required`
- `api.resume.create.idempotency_conflict`

### API-RESUME-003 获取简历详情（Get resume detail）

方法（Method）： GET
路径（Path）： `/api/v1/resumes/{resume_id}`
领域（Domain）： Resume
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： resume.owner_ref 必须匹配当前 actor
关联数据对象： Resume, ResumeVersion, OwnerRef
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.resume.get.cross_user_denied, api.resume.get.validation_failed, api.resume.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | resume_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume | 资源域 | loggable |
| data.resume_id | 是 | string | res_* | 简历 ID | loggable |
| data.title | 是 | string | 1..120 | 简历标题 | loggable |
| data.markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| data.status | 是 | enum | active / archived / deleted | 简历状态 | loggable |
| data.display_summary | 否 | string | redacted summary | 展示摘要；不得替代 Markdown 正文 | sensitive_summary_only |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.resume.get.cross_user_denied`
- `api.resume.get.validation_failed`
- `api.resume.get.cross_user_denied`

### API-RESUME-004 更新简历（Update resume）

方法（Method）： PATCH
路径（Path）： `/api/v1/resumes/{resume_id}`
领域（Domain）： Resume
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： resume.owner_ref 与 base_version_ref owner 一致
关联数据对象： Resume, ResumeVersion, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.resume.update.stale_version_conflict, api.resume.update.validation_failed, api.resume.update.cross_user_denied, api.resume.update.idempotency_required, api.resume.update.idempotency_conflict, api.resume.update.stale_version_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | resume_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| markdown_text | 是 | string | 1..60000 | 新 Markdown 简历正文；项目经历只是正文片段，不单独提交模块字段 | sensitive_not_loggable |
| base_version_ref | 是 | VersionRef | ResumeVersion | 基础版本 | loggable |
| edit_reason | 否 | string | <=240 | 编辑原因 | loggable |

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume | 资源域 | loggable |
| data.resume_id | 是 | string | res_* | 简历 ID | loggable |
| data.title | 是 | string | 1..120 | 简历标题 | loggable |
| data.markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| data.current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| data.status | 是 | enum | active / archived / deleted | 简历状态 | loggable |
| data.display_summary | 否 | string | redacted summary | 展示摘要；不得替代 Markdown 正文 | sensitive_summary_only |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.resume.update.stale_version_conflict`
- `api.resume.update.validation_failed`
- `api.resume.update.cross_user_denied`
- `api.resume.update.idempotency_required`
- `api.resume.update.idempotency_conflict`
- `api.resume.update.stale_version_conflict`

### API-JOB-001 列出岗位（List jobs）

方法（Method）： GET
路径（Path）： `/api/v1/jobs`
领域（Domain）： Job / JD
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： 按 actor owner scope 过滤列表
关联数据对象： Job, JobVersion, JobStatus, OwnerRef
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.job.list.owner_scoped, api.job.list.validation_failed, api.job.list.cross_user_denied

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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
| data.binding_summary | 是 | JobBindingSummary | not_bound / bound | 当前绑定简历摘要 | sensitive_summary_only |
| data.latest_match_summary | 是 | JobMatchSummary | match_* | 最新岗位-简历匹配摘要；不得返回精确通过概率 | sensitive_summary_only |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| meta.pagination | 否 | PaginationMeta | cursor pagination | 列表分页信息 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.job.list.owner_scoped`
- `api.job.list.validation_failed`
- `api.job.list.cross_user_denied`

### API-JOB-002 手动创建岗位（Create job manually）

方法（Method）： POST
路径（Path）： `/api/v1/jobs`
领域（Domain）： Job / JD
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： 服务端从 session 推导 owner, 不接受外部材料解析
关联数据对象： Job, JobVersion, JobStatus, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.job.create.manual_only, api.job.create.validation_failed, api.job.create.cross_user_denied, api.job.create.idempotency_required, api.job.create.idempotency_conflict

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| title | 是 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| department | 否 | string | <=160 | 部门 | sensitive_summary_only |
| responsibilities | 是 | string[] | 1..100 items | 职责 | sensitive_not_loggable |
| requirements | 是 | string[] | 1..100 items | 要求 | sensitive_not_loggable |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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
| data.binding_summary | 是 | JobBindingSummary | not_bound | 新建岗位默认未绑定简历 | sensitive_summary_only |
| data.latest_match_summary | 是 | JobMatchSummary | match_not_generated | 新建岗位默认未生成匹配分析；不得返回精确通过概率 | sensitive_summary_only |
| data.status | 是 | enum | draft / active / archived / deleted | 岗位状态 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.job.create.manual_only`
- `api.job.create.validation_failed`
- `api.job.create.cross_user_denied`
- `api.job.create.idempotency_required`
- `api.job.create.idempotency_conflict`

### API-JOB-003 获取岗位详情（Get job detail）

方法（Method）： GET
路径（Path）： `/api/v1/jobs/{job_id}`
领域（Domain）： Job / JD
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： job.owner_ref 必须匹配当前 actor
关联数据对象： Job, JobVersion, JobStatus, OwnerRef
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.job.get.cross_user_denied, api.job.get.validation_failed, api.job.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| job_id | 是 | string | job_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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
| data.binding_summary | 是 | JobBindingSummary | not_bound / bound | 当前绑定简历摘要 | sensitive_summary_only |
| data.latest_match_summary | 是 | JobMatchSummary | match_* | 最新岗位-简历匹配摘要；不得返回精确通过概率 | sensitive_summary_only |
| data.status | 是 | enum | draft / active / archived / deleted | 岗位状态 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.job.get.cross_user_denied`
- `api.job.get.validation_failed`
- `api.job.get.cross_user_denied`

### API-JOB-004 更新岗位（Update job）

方法（Method）： PATCH
路径（Path）： `/api/v1/jobs/{job_id}`
领域（Domain）： Job / JD
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： job.owner_ref 与 base_version_ref owner 一致
关联数据对象： Job, JobVersion, JobStatus, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.job.update.stale_version_conflict, api.job.update.validation_failed, api.job.update.cross_user_denied, api.job.update.idempotency_required, api.job.update.idempotency_conflict, api.job.update.stale_version_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| job_id | 是 | string | job_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| title | 否 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| responsibilities | 否 | string[] | <=100 items | 职责 | sensitive_not_loggable |
| requirements | 否 | string[] | <=100 items | 要求 | sensitive_not_loggable |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |
| base_version_ref | 是 | VersionRef | JobVersion | 基础版本 | loggable |

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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
| data.binding_summary | 是 | JobBindingSummary | not_bound / bound | 当前绑定简历摘要 | sensitive_summary_only |
| data.latest_match_summary | 是 | JobMatchSummary | match_* | 最新岗位-简历匹配摘要；不得返回精确通过概率 | sensitive_summary_only |
| data.status | 是 | enum | draft / active / archived / deleted | 岗位状态 | loggable |
| data.updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.job.update.stale_version_conflict`
- `api.job.update.validation_failed`
- `api.job.update.cross_user_denied`
- `api.job.update.idempotency_required`
- `api.job.update.idempotency_conflict`
- `api.job.update.stale_version_conflict`

### API-BINDING-001 创建简历-岗位绑定（Create resume-job binding）

方法（Method）： POST
路径（Path）： `/api/v1/resume-job-bindings`
领域（Domain）： Resume-job binding
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： resume、job、version 必须同 owner
关联数据对象： JobResumeBinding, ResumeVersion, JobVersion, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.binding.create.cross_owner_denied, api.binding.create.validation_failed, api.binding.create.cross_user_denied, api.binding.create.idempotency_required, api.binding.create.idempotency_conflict

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 是 | string | job_* | 岗位 ID | loggable |
| resume_version_id | 否 | string | version id | 指定简历版本 | loggable |
| job_version_id | 否 | string | version id | 指定岗位版本 | loggable |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.binding.create.cross_owner_denied`
- `api.binding.create.validation_failed`
- `api.binding.create.cross_user_denied`
- `api.binding.create.idempotency_required`
- `api.binding.create.idempotency_conflict`

### API-BINDING-002 解除简历-岗位绑定（Unbind resume-job binding）

方法（Method）： DELETE
路径（Path）： `/api/v1/resume-job-bindings/{binding_id}`
领域（Domain）： Resume-job binding
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： binding、resume、job、version 必须同 owner；解绑只影响当前默认绑定，不删除历史报告 / 复盘 / 匹配结果
关联数据对象： JobResumeBinding, JobMatchAnalysis, InterviewReport, MockInterviewReview, RealInterviewReview, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： binding.delete.success, binding.delete.history_preserved, binding.delete.cross_user_denied, binding.delete.stale_version_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| binding_id | 是 | string | bind_* | 绑定 ID；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| base_version_ref | 是 | VersionRef | JobResumeBinding version | 防 stale unbind 的绑定版本 | loggable |
| reason | 否 | string | <=240 | 用户解除绑定原因 | sensitive_summary_only |

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Resume-job binding | 资源域 | loggable |
| data.binding_id | 是 | string | bind_* | 绑定 ID | loggable |
| data.binding_status | 是 | enum | unbound | 解绑后绑定状态 | loggable |
| data.unbound_at | 是 | datetime | ISO-8601 | 解绑时间 | loggable |
| data.unbound_by | 是 | OwnerRef | current actor | 解绑操作者 | loggable |
| data.preserved_history_refs[] | 是 | TraceRef[] | report / review / job_match refs | 保留的历史报告、复盘、匹配结果引用摘要 | loggable |
| data.affected_default_entry_summary | 是 | object | display summary | 受影响的默认入口摘要，例如岗位详情绑定模块和后续默认发起入口 | sensitive_summary_only |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问 binding、resume 或 job | manual_review | false | binding.delete.cross_user_denied |
| 404 | not_found_or_inaccessible | 绑定不存在或不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 409 | stale_version_conflict | `base_version_ref` 已过期或当前绑定已变化 | reload_and_retry | true | binding.delete.stale_version_conflict |
| 422 | validation_failed | 字段缺失或当前绑定不可解除 | fix_input | false | validation.failed |
| 400 | idempotency_required | 缺少 `Idempotency-Key` | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `binding.delete.success`
- `binding.delete.history_preserved`
- `binding.delete.cross_user_denied`
- `binding.delete.stale_version_conflict`

### API-JOBMATCH-001 创建岗位匹配分析任务（Create job match analysis task）

方法（Method）： POST
路径（Path）： `/api/v1/job-match-analyses`
领域（Domain）： Job match analysis
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： binding/job/resume/version 必须同 owner 且 source_available
关联数据对象： JobMatchAnalysis, MatchScore, WeaknessCandidate, AiTask, IdempotencyRecord
关联 Prompt Contract： P-JOBMATCH-001, P-JOBMATCH-002, P-JOBMATCH-003, P-JOBMATCH-004
F7 契约测试（F7 Contract Tests）： api.job_match.create.async_success, api.job_match.create.validation_failed, api.job_match.create.cross_user_denied, api.job_match.create.idempotency_required, api.job_match.create.idempotency_conflict, api.job_match.create.source_unavailable, api.job_match.create.provider_unavailable, api.job_match.create.task_timeout

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_job_binding_id | 否 | string | bind_* | `JobResumeBinding` ID；优先于 resume_id/job_id 组合 | loggable |
| resume_id | 条件 | string | res_* | 无 resume_job_binding_id 时必填 | loggable |
| job_id | 条件 | string | job_* | 无 resume_job_binding_id 时必填 | loggable |
| requested_outputs | 否 | string[] | score / points / weakness_candidates | 请求输出 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.job_match.create.async_success`
- `api.job_match.create.validation_failed`
- `api.job_match.create.cross_user_denied`
- `api.job_match.create.idempotency_required`
- `api.job_match.create.idempotency_conflict`
- `api.job_match.create.source_unavailable`
- `api.job_match.create.provider_unavailable`
- `api.job_match.create.task_timeout`

### API-JOBMATCH-002 获取岗位匹配分析（Get job match analysis）

方法（Method）： GET
路径（Path）： `/api/v1/job-match-analyses/{analysis_id}`
领域（Domain）： Job match analysis
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： analysis.owner_ref 必须匹配当前 actor
关联数据对象： JobMatchAnalysis, ScoreResult, EvidenceRef, TraceRef, SourceAvailability
关联 Prompt Contract： P-JOBMATCH-*
F7 契约测试（F7 Contract Tests）： api.job_match.get.low_confidence_visible, api.job_match.get.validation_failed, api.job_match.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| analysis_id | 是 | string | analysis_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.job_match.get.low_confidence_visible`
- `api.job_match.get.validation_failed`
- `api.job_match.get.cross_user_denied`

### API-POLISH-001 创建打磨会话（Create polish session）

方法（Method）： POST
路径（Path）： `/api/v1/polish-sessions`
领域（Domain）： Polish session
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： resume/job/resume_job_binding_id/source_refs 必须同 owner；topic/subtopic 必须来自可用 Polish topic options
关联数据对象： InterviewSession, PolishSessionDetail, ProgressTree, IdempotencyRecord
关联 Prompt Contract： P-POLISH-001
F7 契约测试（F7 Contract Tests）： api.polish_session.create.success, polish.session.create.with_topic_subtopic, polish.session.create.invalid_topic, polish.session.create.cross_owner_binding_rejected, api.polish_session.create.validation_failed, api.polish_session.create.cross_user_denied, api.polish_session.create.idempotency_required, api.polish_session.create.idempotency_conflict

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| resume_job_binding_id | 否 | string | bind_* | `JobResumeBinding` 引用；用于绑定简历与岗位上下文 | loggable |
| topic_id | 否 | string | topic_* | 来自 `GET /api/v1/polish-topics` 的主题 ID | loggable |
| subtopic_id | 否 | string | subtopic_* | 归属于 topic_id 的次主题 ID | loggable |
| custom_topic_text | 否 | string | 1..240 | 用户自定义主题文本；只作为内容标签进入安全输入处理，不作为系统指令 | sensitive_summary_only |
| source_refs | 否 | SourceRef[] | owner scoped | 增强来源 | loggable |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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
| data.topic_ref | 否 | PolishTopicRef | topic_* | 本会话主题引用 | loggable |
| data.subtopic_ref | 否 | PolishSubtopicRef | subtopic_* | 本会话次主题引用 | loggable |
| data.custom_topic_text_summary | 否 | string | redacted summary | 自定义主题摘要；不得作为 Prompt 指令回显 | sensitive_summary_only |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、topic/subtopic 不匹配、custom_topic_text 未通过安全输入处理、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.polish_session.create.success`
- `polish.session.create.with_topic_subtopic`
- `polish.session.create.invalid_topic`
- `polish.session.create.cross_owner_binding_rejected`
- `api.polish_session.create.validation_failed`
- `api.polish_session.create.cross_user_denied`
- `api.polish_session.create.idempotency_required`
- `api.polish_session.create.idempotency_conflict`

### API-POLISH-002 获取打磨会话（Get polish session）

方法（Method）： GET
路径（Path）： `/api/v1/polish-sessions/{session_id}`
领域（Domain）： Polish session
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： session.owner_ref 必须匹配当前 actor
关联数据对象： InterviewSession, PolishSessionDetail, ProgressTree, SessionSummary
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.polish_session.get.owner_scoped, api.polish_session.get.validation_failed, api.polish_session.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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
| data.topic_ref | 否 | PolishTopicRef | topic_* | 本会话主题引用 | loggable |
| data.subtopic_ref | 否 | PolishSubtopicRef | subtopic_* | 本会话次主题引用 | loggable |
| data.custom_topic_text_summary | 否 | string | redacted summary | 自定义主题摘要；不得作为 Prompt 指令回显 | sensitive_summary_only |
| data.low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.polish_session.get.owner_scoped`
- `api.polish_session.get.validation_failed`
- `api.polish_session.get.cross_user_denied`

### API-POLISH-003 创建打磨题目任务（Create polish question task）

方法（Method）： POST
路径（Path）： `/api/v1/polish-sessions/{session_id}/questions`
领域（Domain）： Question
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： session、progress_node、source_refs 必须同 owner
关联数据对象： Question, AiTask, RAGContextAssembly, IdempotencyRecord
关联 Prompt Contract： P-POLISH-002, P-SHARED-*
F7 契约测试（F7 Contract Tests）： api.polish_question.create.async_success, api.polish_question.create.validation_failed, api.polish_question.create.cross_user_denied, api.polish_question.create.idempotency_required, api.polish_question.create.idempotency_conflict, api.polish_question.create.source_unavailable, api.polish_question.create.provider_unavailable, api.polish_question.create.task_timeout

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| progress_node_ref | 否 | TraceRef | node ref | 进展节点 | loggable |
| topic_ref | 否 | TraceRef | topic ref | 主题引用 | loggable |
| question_type | 否 | enum | first / follow_up / polish | 题目类型 | loggable |
| answer_id | 否 | string | ans_* | 追问时的上一回答 | loggable |
| difficulty_hint | 否 | enum | easy / medium / hard / adaptive | 难度提示 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.polish_question.create.async_success`
- `api.polish_question.create.validation_failed`
- `api.polish_question.create.cross_user_denied`
- `api.polish_question.create.idempotency_required`
- `api.polish_question.create.idempotency_conflict`
- `api.polish_question.create.source_unavailable`
- `api.polish_question.create.provider_unavailable`
- `api.polish_question.create.task_timeout`

### API-POLISH-004 创建打磨回答（Create polish answer）

方法（Method）： POST
路径（Path）： `/api/v1/polish-sessions/{session_id}/answers`
领域（Domain）： Answer
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： session/question.owner_ref 必须匹配当前 actor
关联数据对象： Answer, Question, InterviewSession, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.polish_answer.create.validation_failed, api.polish_answer.create.validation_failed, api.polish_answer.create.cross_user_denied, api.polish_answer.create.idempotency_required, api.polish_answer.create.idempotency_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| answer_round | 否 | integer | >=1 | 轮次 | loggable |
| base_question_version_ref | 否 | VersionRef | Question | 题目版本 | loggable |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.polish_answer.create.validation_failed`
- `api.polish_answer.create.validation_failed`
- `api.polish_answer.create.cross_user_denied`
- `api.polish_answer.create.idempotency_required`
- `api.polish_answer.create.idempotency_conflict`

### API-POLISH-005 创建打磨反馈任务（Create polish feedback task）

方法（Method）： POST
路径（Path）： `/api/v1/polish-sessions/{session_id}/feedback`
领域（Domain）： Feedback
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： session/answer/evidence owner 必须匹配当前 actor
关联数据对象： Feedback, ScoreResult, AssetCandidate, WeaknessCandidate, AiTask, IdempotencyRecord
关联 Prompt Contract： P-POLISH-003, P-POLISH-004, P-POLISH-005, P-POLISH-006, P-POLISH-007, P-POLISH-008, P-POLISH-009, P-POLISH-010, P-POLISH-011
F7 契约测试（F7 Contract Tests）： api.polish_feedback.create.low_confidence_visible, api.polish_feedback.create.validation_failed, api.polish_feedback.create.cross_user_denied, api.polish_feedback.create.idempotency_required, api.polish_feedback.create.idempotency_conflict, api.polish_feedback.create.source_unavailable, api.polish_feedback.create.provider_unavailable, api.polish_feedback.create.task_timeout

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| requested_outputs | 否 | string[] | diagnosis / score / loss_points / reference_answer / knowledge / next_action / asset_candidate / weakness_candidate | 请求输出 | loggable |
| session_summary_ref | 否 | TraceRef | summary ref | 会话摘要 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.polish_feedback.create.low_confidence_visible`
- `api.polish_feedback.create.validation_failed`
- `api.polish_feedback.create.cross_user_denied`
- `api.polish_feedback.create.idempotency_required`
- `api.polish_feedback.create.idempotency_conflict`
- `api.polish_feedback.create.source_unavailable`
- `api.polish_feedback.create.provider_unavailable`
- `api.polish_feedback.create.task_timeout`

### API-POLISH-006 列出打磨主题和次主题（List polish topics and subtopics）

方法（Method）： GET
路径（Path）： `/api/v1/polish-topics`
领域（Domain）： Polish topic options
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： 可选 `resume_job_binding_id` 必须指向当前 actor 的 `JobResumeBinding`
关联数据对象： PolishTopicRef, PolishSubtopicRef, JobResumeBinding
关联 Prompt Contract： P-POLISH-001, P-POLISH-002
F7 契约测试（F7 Contract Tests）： polish.topic.list.success, polish.topic.list.cross_owner_binding_rejected

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_job_binding_id | 否 | string | bind_* | 用于按绑定上下文禁用或推荐主题；必须 owner scoped | loggable |
| include_disabled | 否 | boolean | default=false | 是否返回禁用主题和禁用原因 | loggable |

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success | 业务状态 | loggable |
| resource_type | 是 | string | Polish topic options | 资源域 | loggable |
| data.topics[] | 是 | PolishTopic[] | >=1 | 可选主题；不是正式业务对象 | loggable |
| data.default_topic_id | 否 | string | topic_* | 默认推荐主题 | loggable |
| data.binding_context_available | 是 | boolean | true / false | 是否已按绑定上下文计算可用性 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | resume_job_binding_id 不属于当前 actor | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | binding 不存在或不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | query 非法或绑定上下文无法解析 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `polish.topic.list.success`
- `polish.topic.list.cross_owner_binding_rejected`

### API-PRESSURE-001 创建压力面会话（Create pressure session）

方法（Method）： POST
路径（Path）： `/api/v1/pressure-sessions`
领域（Domain）： Pressure session
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： resume/job/resume_job_binding_id/source_refs 必须同 owner
关联数据对象： InterviewSession, PressureSessionDetail, ProgressTree, IdempotencyRecord
关联 Prompt Contract： P-PRESSURE-001
F7 契约测试（F7 Contract Tests）： api.pressure_session.create.success, api.pressure_session.create.validation_failed, api.pressure_session.create.cross_user_denied, api.pressure_session.create.idempotency_required, api.pressure_session.create.idempotency_conflict

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| resume_job_binding_id | 否 | string | bind_* | `JobResumeBinding` ID；用于绑定简历与岗位上下文 | loggable |
| start_mode | 否 | enum | first_question / continue_from_weakness / manual_topic | 启动模式 | loggable |
| source_refs | 否 | SourceRef[] | owner scoped | 增强来源 | loggable |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.pressure_session.create.success`
- `api.pressure_session.create.validation_failed`
- `api.pressure_session.create.cross_user_denied`
- `api.pressure_session.create.idempotency_required`
- `api.pressure_session.create.idempotency_conflict`

### API-PRESSURE-002 获取压力面会话（Get pressure session）

方法（Method）： GET
路径（Path）： `/api/v1/pressure-sessions/{session_id}`
领域（Domain）： Pressure session
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： session.owner_ref 必须匹配当前 actor
关联数据对象： InterviewSession, PressureSessionDetail, ProgressTree, SessionSummary
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.pressure_session.get.owner_scoped, api.pressure_session.get.validation_failed, api.pressure_session.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.pressure_session.get.owner_scoped`
- `api.pressure_session.get.validation_failed`
- `api.pressure_session.get.cross_user_denied`

### API-PRESSURE-003 创建压力面题目任务（Create pressure question task）

方法（Method）： POST
路径（Path）： `/api/v1/pressure-sessions/{session_id}/questions`
领域（Domain）： Question
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： session/answer/source_refs 必须同 owner
关联数据对象： Question, AiTask, PressureSessionDetail, IdempotencyRecord
关联 Prompt Contract： P-PRESSURE-002, P-PRESSURE-004, P-PRESSURE-005
F7 契约测试（F7 Contract Tests）： api.pressure_question.create.async_success, api.pressure_question.create.validation_failed, api.pressure_question.create.cross_user_denied, api.pressure_question.create.idempotency_required, api.pressure_question.create.idempotency_conflict, api.pressure_question.create.source_unavailable, api.pressure_question.create.provider_unavailable, api.pressure_question.create.task_timeout

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| progress_node_ref | 否 | TraceRef | node ref | 进展节点 | loggable |
| topic_ref | 否 | TraceRef | topic ref | 主题引用 | loggable |
| question_type | 否 | enum | first / follow_up / polish | 题目类型 | loggable |
| answer_id | 否 | string | ans_* | 追问时的上一回答 | loggable |
| difficulty_hint | 否 | enum | easy / medium / hard / adaptive | 难度提示 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.pressure_question.create.async_success`
- `api.pressure_question.create.validation_failed`
- `api.pressure_question.create.cross_user_denied`
- `api.pressure_question.create.idempotency_required`
- `api.pressure_question.create.idempotency_conflict`
- `api.pressure_question.create.source_unavailable`
- `api.pressure_question.create.provider_unavailable`
- `api.pressure_question.create.task_timeout`

### API-PRESSURE-004 创建压力面回答（Create pressure answer）

方法（Method）： POST
路径（Path）： `/api/v1/pressure-sessions/{session_id}/answers`
领域（Domain）： Answer
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： session/question.owner_ref 必须匹配当前 actor
关联数据对象： Answer, Question, InterviewSession, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.pressure_answer.create.success, api.pressure_answer.create.validation_failed, api.pressure_answer.create.cross_user_denied, api.pressure_answer.create.idempotency_required, api.pressure_answer.create.idempotency_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| answer_round | 否 | integer | >=1 | 轮次 | loggable |
| base_question_version_ref | 否 | VersionRef | Question | 题目版本 | loggable |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |
| 409 | stale_version_conflict | If-Match、base_version_ref 或 source version 过期 | reload_and_retry | true | conflict.stale_version |
| 400 | idempotency_required | 需要 Idempotency-Key 的 mutation 未提供 header | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `api.pressure_answer.create.success`
- `api.pressure_answer.create.validation_failed`
- `api.pressure_answer.create.cross_user_denied`
- `api.pressure_answer.create.idempotency_required`
- `api.pressure_answer.create.idempotency_conflict`

### API-PRESSURE-005 创建压力面反馈任务（Create pressure feedback task）

方法（Method）： POST
路径（Path）： `/api/v1/pressure-sessions/{session_id}/feedback`
领域（Domain）： Feedback
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： session/answer/evidence owner 必须匹配当前 actor
关联数据对象： Feedback, ScoreResult, SessionSummary, AiTask, IdempotencyRecord
关联 Prompt Contract： P-PRESSURE-003, P-PRESSURE-006, P-PRESSURE-007, P-PRESSURE-008, P-PRESSURE-009
F7 契约测试（F7 Contract Tests）： api.pressure_feedback.create.generation_failed_visible, api.pressure_feedback.create.validation_failed, api.pressure_feedback.create.cross_user_denied, api.pressure_feedback.create.idempotency_required, api.pressure_feedback.create.idempotency_conflict, api.pressure_feedback.create.source_unavailable, api.pressure_feedback.create.provider_unavailable, api.pressure_feedback.create.task_timeout

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| requested_outputs | 否 | string[] | diagnosis / score / loss_points / reference_answer / knowledge / next_action / asset_candidate / weakness_candidate | 请求输出 | loggable |
| session_summary_ref | 否 | TraceRef | summary ref | 会话摘要 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.pressure_feedback.create.generation_failed_visible`
- `api.pressure_feedback.create.validation_failed`
- `api.pressure_feedback.create.cross_user_denied`
- `api.pressure_feedback.create.idempotency_required`
- `api.pressure_feedback.create.idempotency_conflict`
- `api.pressure_feedback.create.source_unavailable`
- `api.pressure_feedback.create.provider_unavailable`
- `api.pressure_feedback.create.task_timeout`

### AIFI-BE-004 Pressure mode API handoff

`PRESSURE_MODE_SPEC.md` 冻结 Pressure Mode 的 mode-level API 承接。当前 `API-PRESSURE-001` 至 `API-PRESSURE-005` 覆盖 create / get / question / answer / feedback，但 `pressure_interview_graph` 实现前，active API contract 必须能表达 start、pause、resume、end、report handoff 和 mock review handoff；可以扩展现有 request / response schema，也可以另行登记 dedicated endpoint，但代码不得发明未登记 route。

本节只增加 AIFI-BE-004 交叉引用，不实现 endpoint、不修改 schema 文件、不进入 PR2 code implementation。

### API-PROGRESS-001 获取进展树（Get progress tree）

方法（Method）： GET
路径（Path）： `/api/v1/interview-sessions/{session_id}/progress-tree`
领域（Domain）： Progress tree
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： session.owner_ref 必须匹配当前 actor
关联数据对象： ProgressTree, ProgressNode, ProgressPosition, SourceAvailability
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.progress_tree.get.owner_scoped, api.progress_tree.get.validation_failed, api.progress_tree.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | session_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Progress tree | 资源域 | loggable |
| data.progress_tree_id | 是 | string | pt_* | 进展树 ID | loggable |
| data.session_id | 是 | string | ses_* | 会话 ID | loggable |
| data.nodes[] | 是 | object[] | >=0 | 节点列表 | loggable |
| data.current_position.node_id | 否 | string | node_* | 当前位置 | loggable |
| data.node_status | 否 | enum | ready / unavailable / needs_generation / failed | 当前节点状态；历史来源不可用由具体 AI result / EvidenceRef 表达 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.progress_tree.get.owner_scoped`
- `api.progress_tree.get.validation_failed`
- `api.progress_tree.get.cross_user_denied`

### API-SCORING-001 创建评分任务（Create scoring task）

方法（Method）： POST
路径（Path）： `/api/v1/scoring-results`
领域（Domain）： Scoring result
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： target/input_refs owner 必须匹配当前 actor, hidden scoring rules 不暴露
关联数据对象： ScoreResult, ScoreRuleVersion, ScoreExplanation, AiTask, IdempotencyRecord
关联 Prompt Contract： P-JOBMATCH-002, P-POLISH-004, P-PRESSURE-008, P-REPORT-002
F7 契约测试（F7 Contract Tests）： api.scoring.create.no_hidden_rules, api.scoring.create.validation_failed, api.scoring.create.cross_user_denied, api.scoring.create.idempotency_required, api.scoring.create.idempotency_conflict, api.scoring.create.source_unavailable, api.scoring.create.provider_unavailable, api.scoring.create.task_timeout

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| target_type | 是 | enum | job_match / answer / session / report / review / training_result | 评分目标类型 | loggable |
| target_id | 是 | string | typed id | 评分目标 ID | loggable |
| score_type | 是 | enum | job_match / polish_answer / polish_report / pressure_session / report_section | 评分类型；旧 `polish_round` 只可作为兼容别名映射到 `polish_answer`，不得作为新 canonical 值 | loggable |
| input_refs | 是 | SourceRef[] | owner scoped | 输入引用 | loggable |
| score_rule_version_id | 否 | string | rule version | 指定评分规则版本 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.scoring.create.no_hidden_rules`
- `api.scoring.create.validation_failed`
- `api.scoring.create.cross_user_denied`
- `api.scoring.create.idempotency_required`
- `api.scoring.create.idempotency_conflict`
- `api.scoring.create.source_unavailable`
- `api.scoring.create.provider_unavailable`
- `api.scoring.create.task_timeout`

### API-SCORING-002 获取评分结果（Get scoring result）

方法（Method）： GET
路径（Path）： `/api/v1/scoring-results/{score_result_id}`
领域（Domain）： Scoring result
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： score_result.owner_ref 必须匹配当前 actor
关联数据对象： ScoreResult, ScoreRuleVersion, EvidenceRef, TraceRef, LowConfidenceFlag
关联 Prompt Contract： P-JOBMATCH-002, P-POLISH-004, P-PRESSURE-008, P-REPORT-002
F7 契约测试（F7 Contract Tests）： api.scoring.get.no_exact_probability, api.scoring.get.validation_failed, api.scoring.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| score_result_id | 是 | string | score_result_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.scoring.get.no_exact_probability`
- `api.scoring.get.validation_failed`
- `api.scoring.get.cross_user_denied`

### API-REPORT-001 创建报告任务（Create report task）

方法（Method）： POST
路径（Path）： `/api/v1/reports`
领域（Domain）： Report
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： session/input_refs owner 必须匹配当前 actor
关联数据对象： InterviewReport, ReportSection, ScoreResult, AiTask, IdempotencyRecord
关联 Prompt Contract： P-REPORT-001, P-REPORT-002, P-REPORT-003, P-REPORT-004
F7 契约测试（F7 Contract Tests）： api.report.create.async_success, api.report.create.validation_failed, api.report.create.cross_user_denied, api.report.create.idempotency_required, api.report.create.idempotency_conflict, api.report.create.source_unavailable, api.report.create.provider_unavailable, api.report.create.task_timeout, api.report.no_export_endpoint

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| report_type | 是 | enum | polish_summary / pressure_full | 报告类型 | loggable |
| input_refs | 否 | SourceRef[] | owner scoped | 输入引用 | loggable |
| requested_sections | 否 | string[] | summary / score / risk / weakness / training / copy_content | 请求分项 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.report.create.async_success`
- `api.report.create.validation_failed`
- `api.report.create.cross_user_denied`
- `api.report.create.idempotency_required`
- `api.report.create.idempotency_conflict`
- `api.report.create.source_unavailable`
- `api.report.create.provider_unavailable`
- `api.report.create.task_timeout`
- `api.report.no_export_endpoint`

### API-REPORT-002 获取报告（Get report）

方法（Method）： GET
路径（Path）： `/api/v1/reports/{report_id}`
领域（Domain）： Report
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： report.owner_ref 必须匹配当前 actor
关联数据对象： InterviewReport, ReportSection, ScoreResult, SourceAvailability
关联 Prompt Contract： P-REPORT-*
F7 契约测试（F7 Contract Tests）： api.report.get.copy_boundary_visible, api.report.get.validation_failed, api.report.get.cross_user_denied, api.report.no_export_endpoint

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | report_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.report.get.copy_boundary_visible`
- `api.report.get.validation_failed`
- `api.report.get.cross_user_denied`
- `api.report.no_export_endpoint`

### API-REPORT-003 获取报告复制内容（Get report copy content）

方法（Method）： GET
路径（Path）： `/api/v1/reports/{report_id}/copy-content`
领域（Domain）： Report copy content
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： report.owner_ref 必须匹配当前 actor, copy boundary 必须过滤敏感内容
关联数据对象： CopyableContent, InterviewReport, AuditEvent, EvidenceRef
关联 Prompt Contract： P-REPORT-004
F7 契约测试（F7 Contract Tests）： api.report.copy_content.no_export_artifact, api.report.copy_content.validation_failed, api.report.copy_content.cross_user_denied, api.report.no_export_endpoint

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | report_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.report.copy_content.no_export_artifact`
- `api.report.copy_content.validation_failed`
- `api.report.copy_content.cross_user_denied`
- `api.report.no_export_endpoint`

### API-REPORT-004 记录报告复制事件（Record report copy event）

方法（Method）： POST
路径（Path）： `/api/v1/reports/{report_id}/copy-events`
领域（Domain）： Report copy content
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： report.owner_ref 必须匹配当前 actor, 审计不记录正文
关联数据对象： CopyableContent, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.report.copy_event.audit_without_body, api.report.copy_event.validation_failed, api.report.copy_event.cross_user_denied, api.report.copy_event.idempotency_required, api.report.copy_event.idempotency_conflict, api.report.no_export_endpoint

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | report_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| copy_surface | 是 | enum | report_detail / review_detail | 复制位置 | loggable |
| client_event_id | 否 | string | client generated | 客户端事件 ID | loggable |
| selected_block_ids | 否 | string[] | copy block ids | 复制块 ID | loggable |

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.report.copy_event.audit_without_body`
- `api.report.copy_event.validation_failed`
- `api.report.copy_event.cross_user_denied`
- `api.report.copy_event.idempotency_required`
- `api.report.copy_event.idempotency_conflict`
- `api.report.no_export_endpoint`

### API-REVIEW-005 列出复盘（List reviews）

方法（Method）： GET
路径（Path）： `/api/v1/reviews`
领域（Domain）： Review list
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： 按 actor owner scope 过滤复盘列表
关联数据对象： InterviewRetrospective, MockInterviewReview, RealInterviewReview, ReviewSourceRef, SourceAvailability
关联 Prompt Contract： P-REVIEW-*
F7 契约测试（F7 Contract Tests）： reviews.list.success, reviews.list.filter_by_type, reviews.list.owner_scoped, reviews.list.source_unavailable_visible

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| review_type | 否 | enum | mock / real_input / real | 复盘类型过滤 | loggable |
| source_type | 否 | enum | mock_session / report / real_interview_input | 来源类型过滤 | loggable |
| job_id | 否 | string | job_* | 关联岗位过滤；必须 owner scoped | loggable |
| resume_id | 否 | string | res_* | 关联简历过滤；必须 owner scoped | loggable |
| status | 否 | enum | generating / available / low_confidence / source_unavailable / generation_failed | 复盘状态过滤 | loggable |
| created_after | 否 | datetime | ISO-8601 | 创建时间下界 | loggable |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Review list | 资源域 | loggable |
| data.items[] | 是 | ReviewSummary[] | >=0 | 复盘列表摘要 | sensitive_summary_only |
| data.next_cursor | 否 | string | opaque cursor | 下一页游标 | loggable |
| data.limit | 是 | integer | 1..100 | 分页大小 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权使用目标 job / resume 过滤条件 | manual_review | false | reviews.list.owner_scoped |
| 422 | validation_failed | 非法 filter、cursor 或 limit | fix_filter | false | reviews.list.filter_by_type |
| 429 | rate_limited | 达到 actor/IP/endpoint 限流 | retry_later | true | rate_limit.enforced |

#### F7 契约测试（F7 Contract Tests）

- `reviews.list.success`
- `reviews.list.filter_by_type`
- `reviews.list.owner_scoped`
- `reviews.list.source_unavailable_visible`

### API-REVIEW-001 创建模拟面试复盘任务（Create mock interview review task）

方法（Method）： POST
路径（Path）： `/api/v1/reviews/mock`
领域（Domain）： Mock interview review
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： session/report/input_refs owner 必须匹配当前 actor
关联数据对象： MockInterviewReview, ReviewItem, AiTask, IdempotencyRecord
关联 Prompt Contract： P-REVIEW-001, P-REVIEW-004
F7 契约测试（F7 Contract Tests）： api.review.mock.create.async_success, api.review.mock.create.validation_failed, api.review.mock.create.cross_user_denied, api.review.mock.create.idempotency_required, api.review.mock.create.idempotency_conflict, api.review.mock.create.source_unavailable, api.review.mock.create.provider_unavailable, api.review.mock.create.task_timeout

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | mock_session / report / real_interview_input | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| requested_outputs | 否 | string[] | review_summary / review_items / weakness_candidates / asset_candidates / training_suggestions | 请求输出 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.review.mock.create.async_success`
- `api.review.mock.create.validation_failed`
- `api.review.mock.create.cross_user_denied`
- `api.review.mock.create.idempotency_required`
- `api.review.mock.create.idempotency_conflict`
- `api.review.mock.create.source_unavailable`
- `api.review.mock.create.provider_unavailable`
- `api.review.mock.create.task_timeout`

### API-REVIEW-002 创建真实面试输入（Create real interview input）

方法（Method）： POST
路径（Path）： `/api/v1/reviews/real-inputs`
领域（Domain）： Real interview input / review
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： job/resume/input_refs owner 必须匹配当前 actor
关联数据对象： RealInterviewInput, RealInterviewEvidence, UserConfirmationRef, IdempotencyRecord
关联 Prompt Contract： P-REVIEW-002
F7 契约测试（F7 Contract Tests）： api.review.real_input.create.requires_confirmation, api.review.real_input.create.validation_failed, api.review.real_input.create.cross_user_denied, api.review.real_input.create.idempotency_required, api.review.real_input.create.idempotency_conflict

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| resume_id | 否 | string | res_* | 简历 ID | loggable |
| interview_time | 否 | datetime | ISO-8601 | 面试时间 | sensitive_summary_only |
| question_recall | 否 | string | <=20000 | 问题回忆 | sensitive_not_loggable |
| answer_recall | 否 | string | <=20000 | 回答回忆 | sensitive_not_loggable |
| interviewer_feedback | 否 | string | <=12000 | 面试官反馈 | sensitive_not_loggable |
| result_status | 否 | enum | unknown / passed / failed / pending / no_response | 结果状态 | sensitive_summary_only |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.review.real_input.create.requires_confirmation`
- `api.review.real_input.create.validation_failed`
- `api.review.real_input.create.cross_user_denied`
- `api.review.real_input.create.idempotency_required`
- `api.review.real_input.create.idempotency_conflict`

### API-REVIEW-003 创建真实面试复盘任务（Create real interview review task）

方法（Method）： POST
路径（Path）： `/api/v1/reviews/real`
领域（Domain）： Real interview input / review
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： real_interview_input owner 必须匹配当前 actor 且已确认
关联数据对象： RealInterviewReview, ReviewItem, AiTask, IdempotencyRecord
关联 Prompt Contract： P-REVIEW-003, P-REVIEW-004
F7 契约测试（F7 Contract Tests）： api.review.real.create.confirmed_input_only, api.review.real.create.validation_failed, api.review.real.create.cross_user_denied, api.review.real.create.idempotency_required, api.review.real.create.idempotency_conflict, api.review.real.create.source_unavailable, api.review.real.create.provider_unavailable, api.review.real.create.task_timeout

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | mock_session / report / real_interview_input | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| requested_outputs | 否 | string[] | review_summary / review_items / weakness_candidates / asset_candidates / training_suggestions | 请求输出 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.review.real.create.confirmed_input_only`
- `api.review.real.create.validation_failed`
- `api.review.real.create.cross_user_denied`
- `api.review.real.create.idempotency_required`
- `api.review.real.create.idempotency_conflict`
- `api.review.real.create.source_unavailable`
- `api.review.real.create.provider_unavailable`
- `api.review.real.create.task_timeout`

### API-REVIEW-004 获取复盘（Get review）

方法（Method）： GET
路径（Path）： `/api/v1/reviews/{review_id}`
领域（Domain）： Mock interview review / Real interview review
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： review.owner_ref 必须匹配当前 actor
关联数据对象： MockInterviewReview, RealInterviewReview, ReviewItem, SourceAvailability
关联 Prompt Contract： P-REVIEW-*
F7 契约测试（F7 Contract Tests）： api.review.get.low_confidence_visible, api.review.get.validation_failed, api.review.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | review_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.review.get.low_confidence_visible`
- `api.review.get.validation_failed`
- `api.review.get.cross_user_denied`

### API-REVIEW-006 获取复盘复制内容（Get review copy content）

方法（Method）： GET
路径（Path）： `/api/v1/reviews/{review_id}/copy-content`
领域（Domain）： Review copy content
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： review.owner_ref 必须匹配当前 actor；copy boundary 必须过滤第三方隐私、Prompt 和 provider payload
关联数据对象： CopyableReviewContent, MockInterviewReview, RealInterviewReview, ReviewItem, AuditEvent
关联 Prompt Contract： P-REVIEW-*
F7 契约测试（F7 Contract Tests）： review_copy.get.no_prompt_payload, review_copy.get.third_party_redacted, review_copy.boundary_violation

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | rev_* | 复盘 ID；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Review copy content | 资源域 | loggable |
| data.review_id | 是 | string | rev_* | 复盘 ID | loggable |
| data.copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| data.clipboard_blocks[] | 是 | object[] | plain text blocks | 剪贴板块；不得包含 system prompt、provider payload、隐藏评分规则或未脱敏第三方信息 | sensitive_not_loggable |
| data.redaction_applied | 是 | boolean | true / false | 是否脱敏 | loggable |
| data.third_party_redaction_summary | 否 | string | <=240 | 第三方 / 公司 / 面试官 / 他人隐私脱敏摘要 | sensitive_summary_only |
| data.copy_boundary | 是 | enum | clipboard_only | 复制边界 | loggable |
| data.export_artifact | 是 | null | must be null | 不得返回导出物 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问复盘 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 复盘不存在或不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 409 | source_unavailable | 复盘来源删除、禁用、归档、不可访问或缺少快照 | choose_available_source | false | source.unavailable |
| 422 | copy_boundary_violation | 请求内容越过复制边界或包含不可复制敏感内容 | narrow_copy_scope | false | review_copy.boundary_violation |
| 404 / 405 | export_not_supported | 请求 PDF、Markdown file、Word、docx、download 或 export 语义 | use_copy_content | false | export.no_endpoint |

#### F7 契约测试（F7 Contract Tests）

- `review_copy.get.no_prompt_payload`
- `review_copy.get.third_party_redacted`
- `review_copy.boundary_violation`

### API-REVIEW-007 记录复盘复制事件（Record review copy event）

方法（Method）： POST
路径（Path）： `/api/v1/reviews/{review_id}/copy-events`
领域（Domain）： Review copy event
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： review.owner_ref 必须匹配当前 actor；审计不记录复制正文
关联数据对象： ReviewCopyEvent, AuditEvent, IdempotencyRecord
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： review_copy.audit.no_body_logged, review_copy.boundary_violation

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | rev_* | 复盘 ID；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| copy_surface | 是 | enum | review_detail | 复制位置 | loggable |
| client_event_id | 否 | string | client generated | 客户端事件 ID | loggable |
| selected_block_ids | 否 | string[] | copy block ids | 复制块 ID；不得提交正文 | loggable |

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Review copy event | 资源域 | loggable |
| data.review_id | 是 | string | rev_* | 复盘 ID | loggable |
| data.copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| data.audit_event_ref | 是 | TraceRef | audit event | 审计事件引用；不含复制正文 | loggable |
| data.body_logged | 是 | boolean | false | 必须为 false | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问复盘 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 复盘不存在或不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum 或提交正文 | fix_input | false | review_copy.audit.no_body_logged |
| 400 | idempotency_required | 缺少 `Idempotency-Key` | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `review_copy.audit.no_body_logged`
- `review_copy.boundary_violation`

### API-ASSET-001 列出资产（List assets）

方法（Method）： GET
路径（Path）： `/api/v1/assets`
领域（Domain）： Asset
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： 按 actor owner scope 过滤正式资产
关联数据对象： Asset, AssetVersion, AssetSource, OwnerRef
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.asset.list.owner_scoped, api.asset.list.validation_failed, api.asset.list.cross_user_denied

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.asset.list.owner_scoped`
- `api.asset.list.validation_failed`
- `api.asset.list.cross_user_denied`

### API-ASSET-002 创建资产候选任务（Create asset candidate task）

方法（Method）： POST
路径（Path）： `/api/v1/asset-candidates`
领域（Domain）： Asset candidate / asset version suggestion
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： source_refs/target_asset owner 必须匹配当前 actor
关联数据对象： AssetCandidate, AssetQualityHint, AssetVersionSuggestion, AiTask, IdempotencyRecord
关联 Prompt Contract： P-ASSET-001, P-ASSET-002, P-ASSET-003, P-POLISH-010
F7 契约测试（F7 Contract Tests）： api.asset_candidate.create.candidate_not_formal, api.asset_candidate.create.validation_failed, api.asset_candidate.create.cross_user_denied, api.asset_candidate.create.idempotency_required, api.asset_candidate.create.idempotency_conflict, api.asset_candidate.create.source_unavailable, api.asset_candidate.create.provider_unavailable, api.asset_candidate.create.task_timeout

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | answer / feedback / report / review / training_result / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| target_asset_id | 否 | string | asset_* | 目标资产 | loggable |
| candidate_goal | 否 | enum | new_asset / version_update / quality_hint | 候选目标 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.asset_candidate.create.candidate_not_formal`
- `api.asset_candidate.create.validation_failed`
- `api.asset_candidate.create.cross_user_denied`
- `api.asset_candidate.create.idempotency_required`
- `api.asset_candidate.create.idempotency_conflict`
- `api.asset_candidate.create.source_unavailable`
- `api.asset_candidate.create.provider_unavailable`
- `api.asset_candidate.create.task_timeout`

### API-ASSET-003 获取资产候选（Get asset candidate）

方法（Method）： GET
路径（Path）： `/api/v1/asset-candidates/{candidate_id}`
领域（Domain）： Asset candidate / asset version suggestion
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： candidate.owner_ref 必须匹配当前 actor
关联数据对象： AssetCandidate, AssetQualityHint, AssetVersionSuggestion, EvidenceRef, TraceRef
关联 Prompt Contract： P-ASSET-*
F7 契约测试（F7 Contract Tests）： api.asset_candidate.get.low_confidence_visible, api.asset_candidate.get.validation_failed, api.asset_candidate.get.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | candidate_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.asset_candidate.get.low_confidence_visible`
- `api.asset_candidate.get.validation_failed`
- `api.asset_candidate.get.cross_user_denied`

### API-ASSET-004 确认资产候选（Confirm asset candidate）

方法（Method）： POST
路径（Path）： `/api/v1/asset-candidates/{candidate_id}/confirmations`
领域（Domain）： Asset candidate / asset version suggestion
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： candidate 和 target_asset owner 必须匹配当前 actor, 确认前不得写正式 Asset
关联数据对象： AssetCandidate, Asset, AssetVersion, UserConfirmationRef, AuditEvent, IdempotencyRecord
关联 Prompt Contract： P-ASSET-001, P-ASSET-003
F7 契约测试（F7 Contract Tests）： api.asset_candidate.confirm.formal_requires_user_action, api.asset_candidate.confirm.validation_failed, api.asset_candidate.confirm.cross_user_denied, api.asset_candidate.confirm.idempotency_required, api.asset_candidate.confirm.idempotency_conflict, api.asset_candidate.confirm.stale_version_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | candidate_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| action | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 确认动作 | loggable |
| target_version_ref | 否 | VersionRef | target version | 目标版本 | loggable |
| target_formal_ref | 否 | TraceRef | typed ref | 合并或更新目标 | loggable |
| edited_content | 否 | object | schema depends on target | 用户编辑内容 | sensitive_not_loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.asset_candidate.confirm.formal_requires_user_action`
- `api.asset_candidate.confirm.validation_failed`
- `api.asset_candidate.confirm.cross_user_denied`
- `api.asset_candidate.confirm.idempotency_required`
- `api.asset_candidate.confirm.idempotency_conflict`
- `api.asset_candidate.confirm.stale_version_conflict`

### API-WEAKNESS-001 列出薄弱项（List weaknesses）

方法（Method）： GET
路径（Path）： `/api/v1/weaknesses`
领域（Domain）： Weakness
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： 按 actor owner scope 过滤正式薄弱项
关联数据对象： Weakness, WeaknessEvidence, WeaknessStatusHistory
关联 Prompt Contract： N/A
F7 契约测试（F7 Contract Tests）： api.weakness.list.owner_scoped, api.weakness.list.validation_failed, api.weakness.list.cross_user_denied

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问目标或复合资源 owner 不一致 | manual_review | false | auth.cross_user_denied |
| 404 | not_found_or_inaccessible | 资源不存在或为避免泄露存在性统一不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 422 | validation_failed | 字段缺失、非法 enum、业务前置条件不满足或输出校验失败 | fix_input | false | validation.failed |

#### F7 契约测试（F7 Contract Tests）

- `api.weakness.list.owner_scoped`
- `api.weakness.list.validation_failed`
- `api.weakness.list.cross_user_denied`

### API-WEAKNESS-002 创建薄弱项候选任务（Create weakness candidate task）

方法（Method）： POST
路径（Path）： `/api/v1/weakness-candidates`
领域（Domain）： Weakness candidate / merge suggestion
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： source_refs/input_refs owner 必须匹配当前 actor
关联数据对象： WeaknessCandidate, WeaknessMergeSuggestion, WeaknessSeverityAssessment, AiTask, IdempotencyRecord
关联 Prompt Contract： P-WEAKNESS-001, P-WEAKNESS-002, P-WEAKNESS-003, P-WEAKNESS-004, P-JOBMATCH-004, P-POLISH-011
F7 契约测试（F7 Contract Tests）： api.weakness_candidate.create.candidate_not_formal, api.weakness_candidate.create.validation_failed, api.weakness_candidate.create.cross_user_denied, api.weakness_candidate.create.idempotency_required, api.weakness_candidate.create.idempotency_conflict, api.weakness_candidate.create.source_unavailable, api.weakness_candidate.create.provider_unavailable, api.weakness_candidate.create.task_timeout

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | job_match / polish / pressure / report / review / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| candidate_goal | 否 | enum | new_weakness / merge_suggestion / status_update / severity_assessment | 候选目标 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.weakness_candidate.create.candidate_not_formal`
- `api.weakness_candidate.create.validation_failed`
- `api.weakness_candidate.create.cross_user_denied`
- `api.weakness_candidate.create.idempotency_required`
- `api.weakness_candidate.create.idempotency_conflict`
- `api.weakness_candidate.create.source_unavailable`
- `api.weakness_candidate.create.provider_unavailable`
- `api.weakness_candidate.create.task_timeout`

### API-WEAKNESS-003 确认薄弱项候选（Confirm weakness candidate）

方法（Method）： POST
路径（Path）： `/api/v1/weakness-candidates/{candidate_id}/confirmations`
领域（Domain）： Weakness candidate / merge suggestion
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： candidate 和 target_weakness owner 必须匹配当前 actor, 确认前不得写正式 Weakness
关联数据对象： WeaknessCandidate, Weakness, WeaknessStatusHistory, UserConfirmationRef, AuditEvent, IdempotencyRecord
关联 Prompt Contract： P-WEAKNESS-001, P-WEAKNESS-002, P-WEAKNESS-004
F7 契约测试（F7 Contract Tests）： api.weakness_candidate.confirm.formal_requires_user_action, api.weakness_candidate.confirm.validation_failed, api.weakness_candidate.confirm.cross_user_denied, api.weakness_candidate.confirm.idempotency_required, api.weakness_candidate.confirm.idempotency_conflict, api.weakness_candidate.confirm.stale_version_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | candidate_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| action | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 确认动作 | loggable |
| target_version_ref | 否 | VersionRef | target version | 目标版本 | loggable |
| target_formal_ref | 否 | TraceRef | typed ref | 合并或更新目标 | loggable |
| edited_content | 否 | object | schema depends on target | 用户编辑内容 | sensitive_not_loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.weakness_candidate.confirm.formal_requires_user_action`
- `api.weakness_candidate.confirm.validation_failed`
- `api.weakness_candidate.confirm.cross_user_denied`
- `api.weakness_candidate.confirm.idempotency_required`
- `api.weakness_candidate.confirm.idempotency_conflict`
- `api.weakness_candidate.confirm.stale_version_conflict`

### API-TRAINING-001 列出训练建议（List training suggestions）

方法（Method）： GET
路径（Path）： `/api/v1/training-suggestions`
领域（Domain）： Training suggestion
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： 按 actor owner scope 过滤训练建议
关联数据对象： TrainingRecommendation, TrainingPriorityRanking, OwnerRef
关联 Prompt Contract： P-TRAINING-001, P-TRAINING-002
F7 契约测试（F7 Contract Tests）： api.training_suggestion.list.owner_scoped, api.training_suggestion.list.validation_failed, api.training_suggestion.list.cross_user_denied

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| cursor | 否 | string | opaque cursor | 分页游标 | loggable |
| limit | 否 | integer | 1..100 default 20 | 分页大小 | loggable |
| status | 否 | string | endpoint whitelist | 状态过滤 | loggable |
| sort | 否 | string | endpoint whitelist | 排序字段 | loggable |

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.training_suggestion.list.owner_scoped`
- `api.training_suggestion.list.validation_failed`
- `api.training_suggestion.list.cross_user_denied`

### API-TRAINING-002 创建训练建议任务（Create training suggestion task）

方法（Method）： POST
路径（Path）： `/api/v1/training-suggestions`
领域（Domain）： Training suggestion
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： source_refs/weakness_ids/asset_ids owner 必须匹配当前 actor
关联数据对象： TrainingRecommendation, TrainingPriorityRanking, AiTask, IdempotencyRecord
关联 Prompt Contract： P-TRAINING-001, P-TRAINING-002
F7 契约测试（F7 Contract Tests）： api.training_suggestion.create.no_auto_task, api.training_suggestion.create.validation_failed, api.training_suggestion.create.cross_user_denied, api.training_suggestion.create.idempotency_required, api.training_suggestion.create.idempotency_conflict, api.training_suggestion.create.source_unavailable, api.training_suggestion.create.provider_unavailable, api.training_suggestion.create.task_timeout

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | weakness / report / review / asset / training_result / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| weakness_ids | 否 | string[] | weak_* | 薄弱项 | loggable |
| asset_ids | 否 | string[] | asset_* | 资产 | loggable |
| requested_outputs | 否 | string[] | recommendation / priority_ranking | 请求输出 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.training_suggestion.create.no_auto_task`
- `api.training_suggestion.create.validation_failed`
- `api.training_suggestion.create.cross_user_denied`
- `api.training_suggestion.create.idempotency_required`
- `api.training_suggestion.create.idempotency_conflict`
- `api.training_suggestion.create.source_unavailable`
- `api.training_suggestion.create.provider_unavailable`
- `api.training_suggestion.create.task_timeout`

### API-TRAINING-003 确认训练建议（Confirm training suggestion）

方法（Method）： POST
路径（Path）： `/api/v1/training-suggestions/{suggestion_id}/confirmations`
领域（Domain）： Training suggestion
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： suggestion.owner_ref 必须匹配当前 actor, 确认不等于自动启动 TrainingTask
关联数据对象： TrainingRecommendation, UserConfirmationRef, AuditEvent, IdempotencyRecord
关联 Prompt Contract： P-TRAINING-001
F7 契约测试（F7 Contract Tests）： api.training_suggestion.confirm.no_auto_training_task, api.training_suggestion.confirm.validation_failed, api.training_suggestion.confirm.cross_user_denied, api.training_suggestion.confirm.idempotency_required, api.training_suggestion.confirm.idempotency_conflict, api.training_suggestion.confirm.stale_version_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| suggestion_id | 是 | string | suggestion_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |
| If-Match | 条件 | string | VersionRef or ETag | 更新正式对象、确认或复制审计需要防 stale write 时必填 | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| action | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 确认动作 | loggable |
| target_version_ref | 否 | VersionRef | target version | 目标版本 | loggable |
| target_formal_ref | 否 | TraceRef | typed ref | 合并或更新目标 | loggable |
| edited_content | 否 | object | schema depends on target | 用户编辑内容 | sensitive_not_loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.training_suggestion.confirm.no_auto_training_task`
- `api.training_suggestion.confirm.validation_failed`
- `api.training_suggestion.confirm.cross_user_denied`
- `api.training_suggestion.confirm.idempotency_required`
- `api.training_suggestion.confirm.idempotency_conflict`
- `api.training_suggestion.confirm.stale_version_conflict`

### API-CANDIDATE-001 保存低置信候选校对（Save candidate correction）

方法（Method）： POST
路径（Path）： `/api/v1/candidates/{candidate_id}/corrections`
领域（Domain）： Candidate correction
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： candidate.owner_ref 必须匹配当前 actor；校对内容不得直接污染 Prompt source 或正式对象
关联数据对象： CandidateCorrection, UserCorrectionRef, LlmValidationResult, AuditEvent, IdempotencyRecord
关联 Prompt Contract： P-SHARED-003, P-SHARED-004
F7 契约测试（F7 Contract Tests）： candidate.correction.save.success, candidate.correction.stale_version_conflict, candidate.correction.validation_failed, candidate.correction.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | cand_* / wc_* / typed candidate id | 候选 ID；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| corrected_content | 是 | object | candidate schema subset | 用户校对后的内容；仍需校验和敏感信息处理 | sensitive_not_loggable |
| correction_reason | 是 | string | 1..1000 | 校对原因 | sensitive_summary_only |
| base_candidate_version_ref | 是 | VersionRef | candidate version | 防 stale correction 的候选版本 | loggable |
| confidence_override_reason | 否 | string | <=1000 | 用户认为可以降低或移除低置信标记的理由；仅作为确认输入 | sensitive_summary_only |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Candidate correction | 资源域 | loggable |
| data.candidate_id | 是 | string | typed candidate id | 候选 ID | loggable |
| data.correction_id | 是 | string | corr_* | 校对记录 ID | loggable |
| data.updated_candidate_ref | 是 | CandidateRef | candidate ref | 更新后的候选引用 | loggable |
| data.validation_status | 是 | enum | passed / failed / manual_review_required | 校验状态 | loggable |
| data.user_confirmation_required | 是 | boolean | true / false | 是否仍需用户确认后才能写正式对象 | loggable |
| data.next_actions[] | 是 | string[] | confirm / edit / skip / retry_validation / choose_deposit_target | 下一步动作 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | actor 无权访问 candidate | manual_review | false | candidate.correction.cross_user_denied |
| 404 | not_found_or_inaccessible | candidate 不存在或不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 409 | stale_version_conflict | `base_candidate_version_ref` 过期 | reload_and_retry | true | candidate.correction.stale_version_conflict |
| 422 | validation_failed | 校对内容 schema 或业务语义校验失败 | fix_input | false | candidate.correction.validation_failed |
| 400 | idempotency_required | 缺少 `Idempotency-Key` | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `candidate.correction.save.success`
- `candidate.correction.stale_version_conflict`
- `candidate.correction.validation_failed`
- `candidate.correction.cross_user_denied`

### API-DEPOSIT-001 确认内容沉淀目标（Confirm deposit target）

方法（Method）： POST
路径（Path）： `/api/v1/candidates/{candidate_id}/deposit-confirmations`
领域（Domain）： Deposit target confirmation
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： candidate/source/target_ref owner 必须匹配当前 actor；Prompt 只能建议目标，不能静默决定正式沉淀
关联数据对象： DepositTarget, UserConfirmationRef, AuditEvent, IdempotencyRecord
关联 Prompt Contract： P-ASSET-001, P-WEAKNESS-001, P-TRAINING-001, P-REVIEW-*
F7 契约测试（F7 Contract Tests）： deposit_target.confirm.asset, deposit_target.confirm.weakness, deposit_target.skip, deposit_target.cross_user_denied, deposit_target.source_unavailable

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | cand_* / wc_* / typed candidate id | 候选 ID；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| target_type | 是 | enum | asset / weakness / training_suggestion / polish_input / pressure_input / next_interview_input / review_note / none / skip | 用户选择的沉淀目标类型 | loggable |
| target_ref | 否 | TraceRef | typed ref | 目标引用；新建目标或 skip 时可为空 | loggable |
| confirmation_action | 是 | enum | confirm / edit / skip / reject / manual_review | 确认动作 | loggable |
| edited_content | 否 | object | target schema subset | 用户编辑后的目标内容 | sensitive_not_loggable |
| base_candidate_version_ref | 是 | VersionRef | candidate version | 防 stale confirmation 的候选版本 | loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### 成功响应（Success Response）

HTTP: 201 Created

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | Deposit target confirmation | 资源域 | loggable |
| data.deposit_target | 是 | DepositTarget | target summary | 目标选择与状态 | sensitive_summary_only |
| data.user_confirmation_ref | 是 | UserConfirmationRef | uc_* | 用户确认记录 | loggable |
| data.created_formal_ref | 否 | TraceRef | Asset / Weakness / TrainingRecommendation / input ref | 已创建或更新的正式对象 / 后续输入引用；skip 时为空 | loggable |
| data.next_actions[] | 是 | string[] | view_target / retry / skip / return_to_source | 下一步动作 | loggable |

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
| --- | --- | --- | --- | --- | --- |
| 401 | unauthenticated | 未登录或 session 过期 | login | false | auth.unauthenticated_denied |
| 403 | permission_denied / owner_mismatch | candidate/source/target_ref 不属于当前 actor | manual_review | false | deposit_target.cross_user_denied |
| 404 | not_found_or_inaccessible | candidate 或 target 不存在或不可访问 | check_target | false | auth.not_found_or_inaccessible |
| 409 | stale_version_conflict | `base_candidate_version_ref` 过期 | reload_and_retry | true | conflict.stale_version |
| 409 | source_unavailable | 来源删除、禁用、归档、不可访问或缺少快照 | choose_available_source | false | deposit_target.source_unavailable |
| 409 | target_conflict | 目标对象已变化或与候选语义冲突 | choose_target | true | deposit_target.target_conflict |
| 422 | validation_failed | target_type、target_ref 或 edited_content 不合法 | fix_input | false | validation.failed |
| 400 | idempotency_required | 缺少 `Idempotency-Key` | retry_with_key | true | idempotency.required |
| 409 | idempotency_conflict | 同一 key 对应不同 request body hash | manual_review | false | idempotency.conflict |

#### F7 契约测试（F7 Contract Tests）

- `deposit_target.confirm.asset`
- `deposit_target.confirm.weakness`
- `deposit_target.skip`
- `deposit_target.cross_user_denied`
- `deposit_target.source_unavailable`

### API-AITASK-001 创建通用 AI 任务（Create generic AI task）

方法（Method）： POST
路径（Path）： `/api/v1/ai-tasks`
领域（Domain）： AI task
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： target_ref/input_refs owner 必须匹配当前 actor, contract_ids 必须已登记
关联数据对象： AiTask, AiTaskResult, LlmValidationResult, IdempotencyRecord
关联 Prompt Contract： 已登记 P-*
F7 契约测试（F7 Contract Tests）： api.ai_task.create.contract_id_registered, api.ai_task.create.validation_failed, api.ai_task.create.cross_user_denied, api.ai_task.create.idempotency_required, api.ai_task.create.idempotency_conflict, api.ai_task.create.source_unavailable, api.ai_task.create.provider_unavailable, api.ai_task.create.task_timeout

#### 路径参数（Path Params）

N/A

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| task_type | 是 | enum | registered AI task type | 任务类型 | loggable |
| contract_ids | 是 | string[] | P-* registered | 相关 contract | loggable |
| target_ref | 是 | TraceRef | typed ref | 目标引用 | loggable |
| input_refs | 是 | SourceRef[] | owner scoped | 输入引用 | loggable |
| requested_outputs | 否 | string[] | contract scoped | 请求输出 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.ai_task.create.contract_id_registered`
- `api.ai_task.create.validation_failed`
- `api.ai_task.create.cross_user_denied`
- `api.ai_task.create.idempotency_required`
- `api.ai_task.create.idempotency_conflict`
- `api.ai_task.create.source_unavailable`
- `api.ai_task.create.provider_unavailable`
- `api.ai_task.create.task_timeout`

### API-AITASK-002 获取 AI 任务状态（Get AI task status）

方法（Method）： GET
路径（Path）： `/api/v1/ai-tasks/{ai_task_id}`
领域（Domain）： AI task
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： ai_task.owner_ref 必须匹配当前 actor
关联数据对象： AiTask, AiTaskResult, LlmValidationResult, TraceRef
关联 Prompt Contract： 已登记 P-*
F7 契约测试（F7 Contract Tests）： api.ai_task.status.owner_scoped, api.ai_task.status.validation_failed, api.ai_task.status.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ai_task_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.ai_task.status.owner_scoped`
- `api.ai_task.status.validation_failed`
- `api.ai_task.status.cross_user_denied`

### API-AITASK-003 获取 AI 任务结果（Get AI task result）

方法（Method）： GET
路径（Path）： `/api/v1/ai-tasks/{ai_task_id}/result`
领域（Domain）： AI task
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： not required
Owner 校验（Owner Check）： ai_task.owner_ref 必须匹配当前 actor, 不返回 provider payload
关联数据对象： AiTaskResult, CandidateRef, SuggestionRef, EvidenceRef, TraceRef
关联 Prompt Contract： 已登记 P-*
F7 契约测试（F7 Contract Tests）： api.ai_task.result.no_provider_payload, api.ai_task.result.validation_failed, api.ai_task.result.cross_user_denied

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ai_task_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |

#### 请求体（Request Body）

N/A

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.ai_task.result.no_provider_payload`
- `api.ai_task.result.validation_failed`
- `api.ai_task.result.cross_user_denied`

### API-AITASK-004 重试 AI 任务（Retry AI task）

方法（Method）： POST
路径（Path）： `/api/v1/ai-tasks/{ai_task_id}/retry`
领域（Domain）： AI task
同步 / 异步（Sync/Async）： async
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： ai_task.owner_ref 必须匹配当前 actor, retry 不得扩大上下文
关联数据对象： AiTask, AiTaskResult, LlmFailureRecord, IdempotencyRecord
关联 Prompt Contract： 已登记 P-*
F7 契约测试（F7 Contract Tests）： api.ai_task.retry.idempotent_and_scope_safe, api.ai_task.retry.validation_failed, api.ai_task.retry.cross_user_denied, api.ai_task.retry.idempotency_required, api.ai_task.retry.idempotency_conflict, api.ai_task.retry.source_unavailable, api.ai_task.retry.provider_unavailable, api.ai_task.retry.task_timeout

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ai_task_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| reason | 是 | enum | provider_unavailable / task_timeout / generation_failed / validation_failed / source_fixed / manual_retry | 重试原因 | loggable |
| fixed_input_refs | 否 | SourceRef[] | owner scoped | 修复后的输入 | loggable |

#### 成功响应（Success Response）

HTTP: 202 Accepted

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.ai_task.retry.idempotent_and_scope_safe`
- `api.ai_task.retry.validation_failed`
- `api.ai_task.retry.cross_user_denied`
- `api.ai_task.retry.idempotency_required`
- `api.ai_task.retry.idempotency_conflict`
- `api.ai_task.retry.source_unavailable`
- `api.ai_task.retry.provider_unavailable`
- `api.ai_task.retry.task_timeout`

### API-AITASK-005 取消 AI 任务（Cancel AI task）

方法（Method）： POST
路径（Path）： `/api/v1/ai-tasks/{ai_task_id}/cancel`
领域（Domain）： AI task
同步 / 异步（Sync/Async）： sync
认证（Auth）： required
幂等键（Idempotency-Key）： required
Owner 校验（Owner Check）： ai_task.owner_ref 必须匹配当前 actor, cancel 后不得 late write formal object
关联数据对象： AiTask, AuditEvent, IdempotencyRecord
关联 Prompt Contract： 已登记 P-*
F7 契约测试（F7 Contract Tests）： api.ai_task.cancel.no_late_write, api.ai_task.cancel.validation_failed, api.ai_task.cancel.cross_user_denied, api.ai_task.cancel.idempotency_required, api.ai_task.cancel.idempotency_conflict

#### 路径参数（Path Params）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ai_task_id path id | 路径资源标识；服务端必须做 owner check | loggable |

#### 查询参数（Query Params）

N/A

#### 请求头（Headers）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| X-Request-Id | 否 | string | 8..128 visible chars | 客户端请求追踪 ID；非法时服务端生成新值 | loggable |
| Idempotency-Key | 是 | string | 8..128 stable key | mutation 幂等键；scope=actor_id+method+path+key+request_body_hash | loggable |

#### 请求体（Request Body）

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| reason | 是 | enum | user_cancelled / source_changed / no_longer_needed / manual_review | 取消原因 | loggable |

#### 成功响应（Success Response）

HTTP: 200 OK

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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

#### 错误响应（Error Responses）

| HTTP | error.code | 触发条件 | 用户动作 | 是否可重试 | F7 断言 |
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

#### F7 契约测试（F7 Contract Tests）

- `api.ai_task.cancel.no_late_write`
- `api.ai_task.cancel.validation_failed`
- `api.ai_task.cancel.cross_user_denied`
- `api.ai_task.cancel.idempotency_required`
- `api.ai_task.cancel.idempotency_conflict`


## 8. Schema 索引（Schema Index）

Schema 索引（Schema Index）冻结字段级 contract 的最小交接面。F5 可以在实现中拆分 TypeScript / Pydantic 类型，但不得删除必填字段、放宽 owner/source/idempotency 边界或把敏感字段写入日志。

### 8.1 通用 Schema（Common schemas）

#### ApiSuccessEnvelope

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| status | 是 | enum | success / partial / low_confidence / accepted / queued / running | 业务状态 | loggable |
| resource_type | 是 | string | registered resource type | 资源类型 | loggable |
| data | 否 | object | schema specific | 业务数据 | schema_defined |
| meta | 否 | object | PaginationMeta / RateLimitMeta / version meta | 元数据 | loggable |
| ai_task_id | 否 | string | ait_* | 异步任务 ID | loggable |

#### ApiErrorEnvelope

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| request_id | 是 | string | X-Request-Id or generated | 请求追踪 ID | loggable |
| trace_id | 是 | string | server trace | 链路追踪 ID | loggable |
| error.code | 是 | enum | stable error code | 稳定错误码 | loggable |
| error.message | 是 | string | safe summary | 用户可理解摘要 | loggable |
| error.details | 否 | object | redacted | 字段或冲突细节 | no_sensitive_body |
| error.retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| error.user_action | 否 | enum | login / fix_input / retry_later / manual_review / choose_available_source | 用户动作 | loggable |

#### PaginationMeta

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| next_cursor | 否 | string | opaque | 下一页游标 | loggable |
| has_more | 是 | boolean | true / false | 是否有更多 | loggable |
| limit | 是 | integer | 1..100 | 本页大小 | loggable |
| total_count_available | 是 | boolean | true / false | 是否提供总数 | loggable |

#### RateLimitMeta

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| limit | 是 | integer | >0 | 限制值 | loggable |
| remaining | 是 | integer | >=0 | 剩余额度 | loggable |
| reset_at | 是 | datetime | ISO-8601 | 重置时间 | loggable |
| retry_after_seconds | 否 | integer | >=0 | 建议重试秒数 | loggable |

#### SourceAvailability

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_ref | 是 | SourceRef | typed ref | 来源引用 | loggable |
| status | 是 | enum | source_available / source_archived / source_deleted / source_disabled / source_unavailable | 来源状态 | loggable |
| can_read_for_generation | 是 | boolean | true / false | 能否用于新生成 | loggable |
| display_summary | 否 | string | redacted | 可展示摘要 | sensitive_summary_only |

#### LowConfidenceFlag

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| flag_id | 是 | string | lcf_* | 标记 ID | loggable |
| reason | 是 | enum | evidence_missing / evidence_conflict / source_unavailable / output_incomplete / manual_check_required | 原因 | loggable |
| impact_scope | 是 | string | <=240 | 影响范围 | loggable |
| recommended_action | 否 | enum | manual_review / provide_more_input / retry / ignore | 建议动作 | loggable |

#### EvidenceRef

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| evidence_ref_id | 是 | string | ev_* | 证据引用 ID | loggable |
| source_ref | 是 | SourceRef | typed ref | 来源 | loggable |
| version_ref | 否 | VersionRef | typed ref | 版本 | loggable |
| summary | 否 | string | redacted | 可展示摘要 | sensitive_summary_only |
| confidence_level | 否 | enum | high / medium / low / insufficient | 证据置信度 | loggable |

#### TraceRef

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| trace_ref_id | 是 | string | tr_* | 追踪引用 ID | loggable |
| trace_type | 是 | enum | api_request / rag / llm / validation / audit / persistence | 追踪类型 | loggable |
| created_at | 是 | datetime | ISO-8601 | 创建时间 | loggable |
| redaction_boundary | 是 | string | no raw payload | 脱敏边界 | loggable |

#### ValidationResultRef

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| validation_result_id | 是 | string | val_* | 校验结果 ID | loggable |
| status | 是 | enum | passed / partial / failed | 校验状态 | loggable |
| failure_signals[] | 否 | string[] | shared failure signals | 失败信号 | loggable |
| repair_hint | 否 | string | <=240 | 修复提示 | loggable |

#### UserConfirmationRef

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| confirmation_id | 是 | string | uc_* | 确认 ID | loggable |
| actor_ref | 是 | OwnerRef | current actor | 确认人 | loggable |
| target_ref | 是 | TraceRef | typed ref | 确认目标 | loggable |
| action_type | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 动作 | loggable |
| action_result | 是 | enum | succeeded / failed / pending | 结果 | loggable |
| audit_event_ref | 是 | TraceRef | audit | 审计引用 | loggable |

#### UserCorrectionRef

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| correction_id | 是 | string | corr_* | 用户校对记录 ID | loggable |
| actor_ref | 是 | OwnerRef | current actor | 校对人 | loggable |
| candidate_ref | 是 | CandidateRef | candidate ref | 被校对候选 | loggable |
| validation_result_ref | 是 | ValidationResultRef | val_* | 校对后校验结果 | loggable |
| audit_event_ref | 是 | TraceRef | audit | 审计引用 | loggable |
| corrected_at | 是 | datetime | ISO-8601 | 校对时间 | loggable |

#### AiTaskRef

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ait_* | AI task ID | loggable |
| task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 状态 | loggable |
| contract_ids[] | 是 | string[] | P-* | 相关 contract | loggable |
| owner_ref | 是 | OwnerRef | current actor | 归属 | loggable |

#### PolishTopicRef

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| topic_id | 是 | string | topic_* | 打磨主题 ID；来自 `PolishTopic` 受控选项 | loggable |
| title_snapshot | 是 | string | 1..80 | 创建会话时的主题标题快照 | loggable |

#### PolishSubtopicRef

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| subtopic_id | 是 | string | subtopic_* | 打磨次主题 ID；来自 `PolishSubtopic` 受控选项 | loggable |
| topic_id | 是 | string | topic_* | 所属主题 ID | loggable |
| title_snapshot | 是 | string | 1..80 | 创建会话时的次主题标题快照 | loggable |

### 8.2 请求 Schema（Request schemas）

#### CreateResumeRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| title | 是 | string | 1..120 | 简历标题 | loggable |
| markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| target_direction | 否 | string | <=120 | 目标方向 | loggable |
| client_draft_id | 否 | string | client generated | 客户端草稿 ID | loggable |

#### UpdateResumeRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| markdown_text | 是 | string | 1..60000 | 新 Markdown 简历正文；项目经历只是正文片段，不单独提交模块字段 | sensitive_not_loggable |
| base_version_ref | 是 | VersionRef | ResumeVersion | 基础版本 | loggable |
| edit_reason | 否 | string | <=240 | 编辑原因 | loggable |

#### CreateJobRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| title | 是 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| department | 否 | string | <=160 | 部门 | sensitive_summary_only |
| responsibilities | 是 | string[] | 1..100 items | 职责 | sensitive_not_loggable |
| requirements | 是 | string[] | 1..100 items | 要求 | sensitive_not_loggable |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |

#### UpdateJobRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| title | 否 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| responsibilities | 否 | string[] | <=100 items | 职责 | sensitive_not_loggable |
| requirements | 否 | string[] | <=100 items | 要求 | sensitive_not_loggable |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |
| base_version_ref | 是 | VersionRef | JobVersion | 基础版本 | loggable |

#### CreateBindingRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 是 | string | job_* | 岗位 ID | loggable |
| resume_version_id | 否 | string | version id | 指定简历版本 | loggable |
| job_version_id | 否 | string | version id | 指定岗位版本 | loggable |

#### DeleteBindingRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| base_version_ref | 是 | VersionRef | JobResumeBinding version | 防 stale unbind 的绑定版本 | loggable |
| reason | 否 | string | <=240 | 用户解除绑定原因 | sensitive_summary_only |

#### CreateJobMatchAnalysisRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_job_binding_id | 否 | string | bind_* | `JobResumeBinding` ID；优先于 resume_id/job_id 组合 | loggable |
| resume_id | 条件 | string | res_* | 无 resume_job_binding_id 时必填 | loggable |
| job_id | 条件 | string | job_* | 无 resume_job_binding_id 时必填 | loggable |
| requested_outputs | 否 | string[] | score / points / weakness_candidates | 请求输出 | loggable |

#### CreatePolishSessionRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| resume_job_binding_id | 否 | string | bind_* | `JobResumeBinding` 引用；用于绑定简历与岗位上下文 | loggable |
| topic_id | 否 | string | topic_* | 来自 `GET /api/v1/polish-topics` 的主题 ID | loggable |
| subtopic_id | 否 | string | subtopic_* | 归属于 topic_id 的次主题 ID | loggable |
| custom_topic_text | 否 | string | 1..240 | 用户自定义主题文本；必须经过安全输入处理和 prompt injection 防护 | sensitive_summary_only |
| source_refs | 否 | SourceRef[] | owner scoped | 增强来源 | loggable |

#### CreatePressureSessionRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| resume_job_binding_id | 否 | string | bind_* | `JobResumeBinding` ID；用于绑定简历与岗位上下文 | loggable |
| start_mode | 否 | enum | first_question / continue_from_weakness / manual_topic | 启动模式 | loggable |
| source_refs | 否 | SourceRef[] | owner scoped | 增强来源 | loggable |

#### CreateQuestionTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| progress_node_ref | 否 | TraceRef | node ref | 进展节点 | loggable |
| topic_ref | 否 | TraceRef | topic ref | 主题引用 | loggable |
| question_type | 否 | enum | first / follow_up / polish | 题目类型 | loggable |
| answer_id | 否 | string | ans_* | 追问时的上一回答 | loggable |
| difficulty_hint | 否 | enum | easy / medium / hard / adaptive | 难度提示 | loggable |

#### CreateAnswerRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| answer_round | 否 | integer | >=1 | 轮次 | loggable |
| base_question_version_ref | 否 | VersionRef | Question | 题目版本 | loggable |

#### CreateFeedbackTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| requested_outputs | 否 | string[] | diagnosis / score / loss_points / reference_answer / knowledge / next_action / asset_candidate / weakness_candidate | 请求输出 | loggable |
| session_summary_ref | 否 | TraceRef | summary ref | 会话摘要 | loggable |

#### CreateScoringTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| target_type | 是 | enum | job_match / answer / session / report / review / training_result | 评分目标类型 | loggable |
| target_id | 是 | string | typed id | 评分目标 ID | loggable |
| score_type | 是 | enum | job_match / polish_answer / polish_report / pressure_session / report_section | 评分类型；旧 `polish_round` 只可作为兼容别名映射到 `polish_answer` | loggable |
| input_refs | 是 | SourceRef[] | owner scoped | 输入引用 | loggable |
| score_rule_version_id | 否 | string | rule version | 指定评分规则版本 | loggable |

#### CreateReportTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| report_type | 是 | enum | polish_summary / pressure_full | 报告类型 | loggable |
| input_refs | 否 | SourceRef[] | owner scoped | 输入引用 | loggable |
| requested_sections | 否 | string[] | summary / score / risk / weakness / training / copy_content | 请求分项 | loggable |

#### CreateRealInterviewInputRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| job_id | 否 | string | job_* | 岗位 ID | loggable |
| resume_id | 否 | string | res_* | 简历 ID | loggable |
| interview_time | 否 | datetime | ISO-8601 | 面试时间 | sensitive_summary_only |
| question_recall | 否 | string | <=20000 | 问题回忆 | sensitive_not_loggable |
| answer_recall | 否 | string | <=20000 | 回答回忆 | sensitive_not_loggable |
| interviewer_feedback | 否 | string | <=12000 | 面试官反馈 | sensitive_not_loggable |
| result_status | 否 | enum | unknown / passed / failed / pending / no_response | 结果状态 | sensitive_summary_only |

#### CreateReviewTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | mock_session / report / real_interview_input | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| requested_outputs | 否 | string[] | review_summary / review_items / weakness_candidates / asset_candidates / training_suggestions | 请求输出 | loggable |

#### CreateAssetCandidateTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | answer / feedback / report / review / training_result / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| target_asset_id | 否 | string | asset_* | 目标资产 | loggable |
| candidate_goal | 否 | enum | new_asset / version_update / quality_hint | 候选目标 | loggable |

#### ConfirmCandidateRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| action | 是 | enum | confirm / edit / skip / reject / merge / manual_review | 确认动作 | loggable |
| target_type | 否 | enum | asset / weakness / training_suggestion / polish_input / pressure_input / next_interview_input / review_note / none / skip | 内容沉淀目标类型；不适用时为空 | loggable |
| target_ref | 否 | TraceRef | typed ref | 内容沉淀或合并目标引用；必须 owner scoped | loggable |
| target_version_ref | 否 | VersionRef | target version | 目标版本 | loggable |
| target_formal_ref | 否 | TraceRef | typed ref | 合并或更新目标 | loggable |
| deposit_target | 否 | DepositTarget | target summary | 用户选择的沉淀目标；Prompt 只能建议，不可静默决定 | sensitive_summary_only |
| edited_content | 否 | object | schema depends on target | 用户编辑内容 | sensitive_not_loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### CandidateCorrectionRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| corrected_content | 是 | object | candidate schema subset | 用户校对后的内容；仍需校验和敏感信息处理 | sensitive_not_loggable |
| correction_reason | 是 | string | 1..1000 | 校对原因 | sensitive_summary_only |
| base_candidate_version_ref | 是 | VersionRef | candidate version | 防 stale correction 的候选版本 | loggable |
| confidence_override_reason | 否 | string | <=1000 | 用户认为可以降低或移除低置信标记的理由；仅作为确认输入 | sensitive_summary_only |

#### ConfirmDepositTargetRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| target_type | 是 | enum | asset / weakness / training_suggestion / polish_input / pressure_input / next_interview_input / review_note / none / skip | 用户选择的沉淀目标类型 | loggable |
| target_ref | 否 | TraceRef | typed ref | 目标引用；新建目标或 skip 时可为空 | loggable |
| confirmation_action | 是 | enum | confirm / edit / skip / reject / manual_review | 目标确认动作 | loggable |
| edited_content | 否 | object | target schema subset | 用户编辑后的目标内容 | sensitive_not_loggable |
| base_candidate_version_ref | 是 | VersionRef | candidate version | 防 stale confirmation 的候选版本 | loggable |
| confirmation_note | 否 | string | <=1000 | 用户备注 | sensitive_summary_only |

#### CreateWeaknessCandidateTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | job_match / polish / pressure / report / review / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| candidate_goal | 否 | enum | new_weakness / merge_suggestion / status_update / severity_assessment | 候选目标 | loggable |

#### CreateTrainingSuggestionTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| source_type | 是 | enum | weakness / report / review / asset / training_result / manual | 来源类型 | loggable |
| source_ref | 是 | SourceRef | owner scoped | 来源引用 | loggable |
| weakness_ids | 否 | string[] | weak_* | 薄弱项 | loggable |
| asset_ids | 否 | string[] | asset_* | 资产 | loggable |
| requested_outputs | 否 | string[] | recommendation / priority_ranking | 请求输出 | loggable |

#### CreateAiTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| task_type | 是 | enum | registered AI task type | 任务类型 | loggable |
| contract_ids | 是 | string[] | P-* registered | 相关 contract | loggable |
| target_ref | 是 | TraceRef | typed ref | 目标引用 | loggable |
| input_refs | 是 | SourceRef[] | owner scoped | 输入引用 | loggable |
| requested_outputs | 否 | string[] | contract scoped | 请求输出 | loggable |

#### RetryAiTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| reason | 是 | enum | provider_unavailable / task_timeout / generation_failed / validation_failed / source_fixed / manual_retry | 重试原因 | loggable |
| fixed_input_refs | 否 | SourceRef[] | owner scoped | 修复后的输入 | loggable |

#### CancelAiTaskRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| reason | 是 | enum | user_cancelled / source_changed / no_longer_needed / manual_review | 取消原因 | loggable |

#### RecordCopyEventRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| copy_surface | 是 | enum | report_detail / review_detail | 复制位置 | loggable |
| client_event_id | 否 | string | client generated | 客户端事件 ID | loggable |
| selected_block_ids | 否 | string[] | copy block ids | 复制块 ID | loggable |

#### RecordReviewCopyEventRequest

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| copy_surface | 是 | enum | review_detail | 复制位置 | loggable |
| client_event_id | 否 | string | client generated | 客户端事件 ID | loggable |
| selected_block_ids | 否 | string[] | copy block ids | 复制块 ID；不得提交复制正文 | loggable |

### 8.3 响应数据 Schema（Response data schemas）

#### ResumeSummary

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| title | 是 | string | 1..120 | 简历标题 | loggable |
| target_direction | 否 | string | <=120 | 目标方向 | loggable |
| current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本引用 | loggable |
| status | 是 | enum | active / archived / deleted | 简历状态 | loggable |
| display_summary | 否 | string | redacted summary | 列表摘要；不得替代 Markdown 正文 | sensitive_summary_only |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### ResumeDetail

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| resume_id | 是 | string | res_* | 简历 ID | loggable |
| title | 是 | string | 1..120 | 简历标题 | loggable |
| markdown_text | 是 | string | 1..60000 | Markdown 简历正文 | sensitive_not_loggable |
| current_version_ref | 是 | VersionRef | ResumeVersion | 当前版本 | loggable |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| status | 是 | enum | active / archived / deleted | 简历状态 | loggable |
| display_summary | 否 | string | redacted summary | 展示摘要；项目经历仍只存在于 markdown_text 中 | sensitive_summary_only |

#### JobSummary

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| job_id | 是 | string | job_* | 岗位 ID | loggable |
| title | 是 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| application_status | 否 | enum | draft / applied / interviewing / closed | 投递状态 | loggable |
| current_version_ref | 是 | VersionRef | JobVersion | 当前版本 | loggable |
| binding_summary | 是 | JobBindingSummary | not_bound / bound | 当前绑定简历摘要 | sensitive_summary_only |
| latest_match_summary | 是 | JobMatchSummary | match_* | 最新匹配摘要；不含精确通过概率 | sensitive_summary_only |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### JobDetail

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| job_id | 是 | string | job_* | 岗位 ID | loggable |
| title | 是 | string | 1..160 | 岗位名称 | loggable |
| company | 否 | string | <=160 | 公司名 | sensitive_summary_only |
| responsibilities | 是 | string[] | item<=1000 | 职责列表 | sensitive_not_loggable |
| requirements | 是 | string[] | item<=1000 | 要求列表 | sensitive_not_loggable |
| current_version_ref | 是 | VersionRef | JobVersion | 当前版本 | loggable |
| binding_summary | 是 | JobBindingSummary | not_bound / bound | 当前绑定简历摘要 | sensitive_summary_only |
| latest_match_summary | 是 | JobMatchSummary | match_* | 最新匹配摘要；不含精确通过概率 | sensitive_summary_only |
| status | 是 | enum | draft / active / archived / deleted | 岗位状态 | loggable |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### JobBindingSummary

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| status | 是 | enum | not_bound / bound | 岗位是否已有当前绑定简历 | loggable |
| resume_job_binding_id | 否 | string | bind_* | 当前绑定 ID；仅 status=bound 返回 | loggable |
| resume_id | 否 | string | res_* | 绑定简历 ID | loggable |
| resume_title | 否 | string | 1..120 | 绑定简历标题 | sensitive_summary_only |
| resume_version_ref | 否 | VersionRef | ResumeVersion | 绑定简历版本 | loggable |
| bound_at | 否 | datetime | ISO-8601 | 绑定时间 | loggable |

#### JobMatchSummary

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| status | 是 | enum | match_not_generated / match_queued / match_running / match_succeeded / match_low_confidence / match_failed / match_stale | 最新匹配分析状态 | loggable |
| analysis_id | 否 | string | jma_* | 最新分析 ID | loggable |
| display_score | 否 | integer | 0..100 | 产品匹配分，不是精确通过概率 | loggable |
| score_scale | 否 | enum | 0_100_product_scale | 分数刻度；有 display_score 时必须返回 | loggable |
| score_version | 否 | string | semver/date | 生成该摘要分数时使用的评分版本 | loggable |
| rubric_version | 否 | string | semver/date | 生成该摘要分数时使用的 rubric / rule version | loggable |
| confidence_level | 否 | enum | high / medium / low / insufficient | 摘要置信度 | loggable |
| summary_text | 否 | string | redacted summary | 匹配摘要 | sensitive_summary_only |
| generated_at | 否 | datetime | ISO-8601 | 生成时间 | loggable |
| stale_reason | 否 | enum | resume_version_changed / job_version_changed / binding_changed | `match_stale` 原因 | loggable |

#### JobResumeBindingResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| binding_id | 是 | string | bind_* | 绑定 ID | loggable |
| resume_ref | 是 | VersionRef | ResumeVersion | 绑定简历版本 | loggable |
| job_ref | 是 | VersionRef | JobVersion | 绑定岗位版本 | loggable |
| binding_status | 是 | enum | active / unbinding / unbound / failed | 绑定状态 | loggable |
| created_at | 是 | datetime | ISO-8601 | 创建时间 | loggable |
| unbound_at | 否 | datetime | ISO-8601 | 解绑时间；仅 unbound 返回 | loggable |
| unbound_by | 否 | OwnerRef | current actor | 解绑操作者；仅 unbound 返回 | loggable |
| preserved_history_refs[] | 否 | TraceRef[] | report / review / job_match refs | 保留的历史报告、复盘、匹配结果引用摘要 | loggable |
| affected_default_entry_summary | 否 | object | display summary | 受影响的默认入口摘要 | sensitive_summary_only |

#### JobMatchAnalysisResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| analysis_id | 是 | string | jma_* | 分析 ID | loggable |
| binding_ref | 是 | string | bind_* | 绑定引用 | loggable |
| score.score_value | 是 | integer | 0..100 | 匹配分 | loggable |
| match_points[] | 是 | object[] | >=0 | 匹配点 | sensitive_summary_only |
| mismatch_points[] | 是 | object[] | >=0 | 不匹配点 | sensitive_summary_only |
| improvement_points[] | 是 | object[] | >=0 | 加强点 | sensitive_summary_only |
| low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### InterviewSessionResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| mode | 是 | enum | polish / pressure | 模式 | loggable |
| session_status | 是 | enum | created / running / paused / completed / failed | 会话状态 | loggable |
| current_question_ref | 否 | string | question_* | 当前题目 | loggable |
| progress_position_ref | 否 | string | progress_pos_* | 进展位置 | loggable |
| topic_ref | 否 | PolishTopicRef | topic_* | 打磨主题引用 | loggable |
| subtopic_ref | 否 | PolishSubtopicRef | subtopic_* | 打磨次主题引用 | loggable |
| custom_topic_text_summary | 否 | string | redacted summary | 自定义主题摘要；不得作为 Prompt 指令回显 | sensitive_summary_only |
| low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### ProgressTreeResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| progress_tree_id | 是 | string | pt_* | 进展树 ID | loggable |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| nodes[] | 是 | object[] | >=0 | 节点列表 | loggable |
| current_position.node_id | 否 | string | node_* | 当前位置 | loggable |
| node_status | 否 | enum | ready / unavailable / needs_generation / failed | 当前节点状态；历史来源不可用由具体 AI result / EvidenceRef 表达 | loggable |

#### PolishTopic

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| topic_id | 是 | string | topic_* | 主题 ID；受控选项，不是正式业务对象 | loggable |
| title | 是 | string | 1..80 | 主题标题 | loggable |
| description | 否 | string | <=240 | 主题说明 | loggable |
| requires_job_binding | 是 | boolean | true / false | 是否建议结合岗位绑定使用 | loggable |
| disabled_reason | 否 | string | <=240 | 不可用原因 | loggable |
| subtopics[] | 是 | PolishSubtopic[] | >=0 | 次主题列表 | loggable |

#### PolishSubtopic

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| subtopic_id | 是 | string | subtopic_* | 次主题 ID；归属于 `topic_id` | loggable |
| topic_id | 是 | string | topic_* | 所属主题 ID | loggable |
| title | 是 | string | 1..80 | 次主题标题 | loggable |
| description | 否 | string | <=240 | 次主题说明 | loggable |
| disabled_reason | 否 | string | <=240 | 不可用原因 | loggable |

#### QuestionResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| session_id | 是 | string | ses_* | 会话 ID | loggable |
| question_text | 是 | string | 1..4000 | 题目正文 | sensitive_summary_only |
| question_type | 是 | enum | polish / pressure_first / pressure_follow_up | 题目类型 | loggable |
| evidence_refs[] | 否 | EvidenceRef[] | >=0 | 证据引用 | loggable |
| generated_by_task_id | 否 | string | ait_* | 生成任务 | loggable |

#### AnswerResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| question_id | 是 | string | q_* | 题目 ID | loggable |
| answer_text | 是 | string | 1..20000 | 回答正文 | sensitive_not_loggable |
| answer_round | 否 | integer | >=1 | 回答轮次 | loggable |
| created_at | 是 | datetime | ISO-8601 | 提交时间 | loggable |

#### FeedbackResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| feedback_id | 是 | string | fb_* | 反馈 ID | loggable |
| answer_id | 是 | string | ans_* | 回答 ID | loggable |
| summary | 是 | string | <=2000 | 点评摘要 | sensitive_summary_only |
| score_ref | 否 | string | score_* | 评分引用 | loggable |
| loss_point_refs[] | 否 | string[] | >=0 | 失分点引用 | loggable |
| candidate_refs[] | 否 | CandidateRef[] | >=0 | 候选回流 | loggable |

#### ScoreResultResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| score_result_id | 是 | string | score_* | 评分 ID | loggable |
| target_ref | 是 | TraceRef | typed ref | 评分目标 | loggable |
| score_type | 是 | enum | job_match / polish_answer / polish_report / pressure_session / report_section | canonical 评分类型 | loggable |
| score_value | 是 | integer | 0..100 | 0-100 产品刻度 | loggable |
| score_scale | 是 | enum | 0_100_product_scale | 分数刻度 | loggable |
| score_version | 是 | string | semver/date | 评分版本 | loggable |
| rubric_version | 是 | string | semver/date | Rubric 版本 | loggable |
| score_rule_version_ref | 是 | TraceRef | ScoreRuleVersion | 评分规则版本引用 | loggable |
| validation_status | 是 | enum | valid / valid_with_warnings / invalid / manual_review_required | 评分校验状态 | loggable |
| confidence_level | 是 | enum | high / medium / low / insufficient | 置信度 | loggable |
| dimension_scores[] | 是 | object[] | dimensions from `ScoreRuleVersion` | 维度分、权重、解释和证据引用摘要；不得包含隐藏校准样例正文 | loggable |
| evidence_refs[] | 是 | EvidenceRef[] | >=1 unless insufficient | 证据 | loggable |
| trace_refs[] | 是 | TraceRef[] | >=1 | context / LLM / validation / persistence / audit trace | loggable |
| low_confidence_flags[] | 是 | LowConfidenceFlag[] | >=0 | 低置信度标记 | loggable |
| allowed_as_formal_score | 是 | boolean | true / false | 是否允许作为正式 `ScoreResult` 展示或写入报告评分 | loggable |

#### ReportResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | rep_* | 报告 ID | loggable |
| session_ref | 是 | string | ses_* | 会话引用 | loggable |
| report_status | 是 | enum | generating / available / partial / failed | 报告状态 | loggable |
| sections[] | 是 | object[] | >=0 | 报告分项 | sensitive_summary_only |
| score_ref | 否 | string | score_* | 总评分引用 | loggable |
| copy_content_available | 是 | boolean | true / false | 是否可复制 | loggable |
| source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |

#### ReportCopyContentResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| report_id | 是 | string | rep_* | 报告 ID | loggable |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| clipboard_blocks[] | 是 | object[] | plain text blocks | 剪贴板块 | sensitive_not_loggable |
| redaction_applied | 是 | boolean | true / false | 是否脱敏 | loggable |
| copy_boundary | 是 | enum | clipboard_only | 复制边界 | loggable |
| export_artifact | 是 | null | must be null | 不得返回导出物 | loggable |

#### ReviewResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | rev_* | 复盘 ID | loggable |
| review_type | 是 | enum | mock / real_input / real | 复盘类型 | loggable |
| review_status | 是 | enum | available / partial / low_confidence / failed | 状态 | loggable |
| items[] | 否 | object[] | >=0 | 题级复盘项 | sensitive_summary_only |
| source_refs[] | 是 | SourceRef[] | >=1 | 来源 | loggable |
| candidate_refs[] | 否 | CandidateRef[] | >=0 | 候选回流 | loggable |
| low_confidence_flags[] | 否 | LowConfidenceFlag[] | >=0 | 低置信度 | loggable |

#### ReviewSummary

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | rev_* | 复盘 ID | loggable |
| review_type | 是 | enum | mock / real_input / real | 复盘类型 | loggable |
| title | 否 | string | 1..160 | 复盘标题 | sensitive_summary_only |
| display_summary | 是 | string | redacted summary | 列表摘要 | sensitive_summary_only |
| source_summary | 是 | object | redacted source summary | 来源摘要，区分模拟会话、报告或真实面试输入 | sensitive_summary_only |
| created_at | 是 | datetime | ISO-8601 | 创建时间 | loggable |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |
| status | 是 | enum | generating / available / low_confidence / source_unavailable / generation_failed | 列表状态 | loggable |
| confidence_level | 否 | enum | high / medium / low / insufficient | 置信度 | loggable |
| source_availability | 是 | SourceAvailability | source_* | 来源可用性 | loggable |
| related_report_ref | 否 | TraceRef | report ref | 关联报告引用 | loggable |
| related_session_ref | 否 | TraceRef | session ref | 关联会话引用 | loggable |
| next_actions[] | 是 | string[] | open_detail / correct_low_confidence / retry_generation / choose_deposit_target / copy_content | 下一步动作 | loggable |

#### ReviewCopyContentResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | rev_* | 复盘 ID | loggable |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| clipboard_blocks[] | 是 | object[] | plain text blocks | 剪贴板块；不得包含 system prompt、provider payload、隐藏评分规则或未脱敏第三方信息 | sensitive_not_loggable |
| redaction_applied | 是 | boolean | true / false | 是否脱敏 | loggable |
| third_party_redaction_summary | 否 | string | <=240 | 第三方 / 公司 / 面试官 / 他人隐私脱敏摘要 | sensitive_summary_only |
| copy_boundary | 是 | enum | clipboard_only | 复制边界 | loggable |
| export_artifact | 是 | null | must be null | 不得返回导出物 | loggable |

#### ReviewCopyEventResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| review_id | 是 | string | rev_* | 复盘 ID | loggable |
| copy_content_id | 是 | string | copy_* | 复制内容 ID | loggable |
| audit_event_ref | 是 | TraceRef | audit event | 审计事件引用；不含复制正文 | loggable |
| body_logged | 是 | boolean | false | 必须为 false | loggable |

#### CandidateCorrectionResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | typed candidate id | 候选 ID | loggable |
| correction_id | 是 | string | corr_* | 校对记录 ID | loggable |
| updated_candidate_ref | 是 | CandidateRef | candidate ref | 更新后的候选引用 | loggable |
| validation_status | 是 | enum | passed / failed / manual_review_required | 校验状态 | loggable |
| user_confirmation_required | 是 | boolean | true / false | 是否仍需确认后才能写正式对象 | loggable |
| next_actions[] | 是 | string[] | confirm / edit / skip / retry_validation / choose_deposit_target | 下一步动作 | loggable |

#### DepositTarget

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| target_type | 是 | enum | asset / weakness / training_suggestion / polish_input / pressure_input / next_interview_input / review_note / none / skip | 沉淀目标类型 | loggable |
| target_ref | 否 | TraceRef | typed ref | 既有目标引用；必须 owner scoped | loggable |
| target_status | 是 | enum | pending_selection / confirmed / skipped / unavailable / conflict / failed | 目标状态 | loggable |
| disabled_reason | 否 | string | <=240 | 目标不可用原因 | sensitive_summary_only |

#### DepositTargetConfirmationResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| deposit_target | 是 | DepositTarget | target summary | 用户选择的沉淀目标 | sensitive_summary_only |
| user_confirmation_ref | 是 | UserConfirmationRef | uc_* | 用户确认记录 | loggable |
| created_formal_ref | 否 | TraceRef | Asset / Weakness / TrainingRecommendation / input ref | 已创建或更新的正式对象 / 后续输入引用；skip 时为空 | loggable |
| next_actions[] | 是 | string[] | view_target / retry / skip / return_to_source | 下一步动作 | loggable |

#### AssetResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| asset_id | 是 | string | asset_* | 资产 ID | loggable |
| current_version_ref | 是 | VersionRef | AssetVersion | 当前版本 | loggable |
| title | 是 | string | 1..160 | 资产标题 | loggable |
| asset_type | 是 | enum | answer_material / project_expression / job_material / feedback_summary | 资产类型 | loggable |
| status | 是 | enum | active / archived / disabled | 状态 | loggable |
| source_refs[] | 是 | SourceRef[] | >=1 | 来源 | loggable |

#### AssetCandidateResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | cand_* | 候选 ID | loggable |
| candidate_status | 是 | enum | draft / needs_confirmation / confirmed / rejected / low_confidence | 候选状态 | loggable |
| content_draft | 是 | string | <=12000 | 候选内容 | sensitive_not_loggable |
| target_asset_ref | 否 | string | asset_* | 目标资产 | loggable |
| quality_hint_ref | 否 | string | hint_* | 质量提示 | loggable |
| version_suggestion_ref | 否 | string | avs_* | 资产版本建议 | loggable |
| user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |

#### WeaknessResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| weakness_id | 是 | string | weak_* | 薄弱项 ID | loggable |
| title | 是 | string | 1..160 | 主题 | sensitive_summary_only |
| status | 是 | enum | confirmed / low_priority / ignored / resolved_candidate / resolved / reopened | 状态 | loggable |
| severity_hint | 否 | enum | low / medium / high / unknown | 严重度提示 | loggable |
| evidence_refs[] | 是 | EvidenceRef[] | >=1 | 证据 | loggable |
| updated_at | 是 | datetime | ISO-8601 | 更新时间 | loggable |

#### WeaknessCandidateResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| candidate_id | 是 | string | wc_* | 候选 ID | loggable |
| candidate_status | 是 | enum | draft / needs_confirmation / merge_suggested / low_confidence / rejected | 候选状态 | loggable |
| title | 是 | string | 1..160 | 候选主题 | sensitive_summary_only |
| evidence_refs[] | 是 | EvidenceRef[] | >=1 | 证据 | loggable |
| merge_suggestion_refs[] | 否 | SuggestionRef[] | >=0 | 合并建议 | loggable |
| user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |

#### TrainingSuggestionResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| suggestion_id | 是 | string | tr_* | 训练建议 ID | loggable |
| suggestion_status | 是 | enum | candidate / confirmed / skipped / rejected / low_confidence | 建议状态 | loggable |
| topic | 是 | string | 1..160 | 训练主题 | sensitive_summary_only |
| priority_hint | 否 | enum | low / medium / high / unknown | 优先级提示 | loggable |
| weakness_refs[] | 否 | string[] | >=0 | 关联薄弱项 | loggable |
| asset_refs[] | 否 | string[] | >=0 | 关联资产 | loggable |
| user_confirmation_required | 是 | boolean | true / false | 是否需要确认 | loggable |

#### AiTaskStatusResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
| --- | --- | --- | --- | --- | --- |
| ai_task_id | 是 | string | ait_* | API AI task ID | loggable |
| task_type | 是 | enum | registered task_type | 任务类型 | loggable |
| status | 是 | enum | queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled | 任务状态 | loggable |
| contract_ids[] | 是 | string[] | P-* | 相关 Prompt contract | loggable |
| retryable | 是 | boolean | true / false | 是否可重试 | loggable |
| result_ref | 否 | TraceRef | typed ref | 结果引用 | loggable |
| user_visible_status | 是 | string | <=240 | 用户可见状态摘要 | loggable |

#### AiTaskResultResponse

| 字段 | 是否必填 | 类型 | 枚举 / 约束 | 说明 | 敏感性 / 是否可记录 |
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
| `target_type` | 内容沉淀目标类型，允许 `asset`、`weakness`、`training_suggestion`、`polish_input`、`pressure_input`、`next_interview_input`、`review_note`、`none` / `skip` |
| `target_version_ref` | 防 stale update 的版本或状态引用 |
| `edited_content` / `edited_summary` | 用户编辑后的结构化摘要或内容；不得保存过量正文到审计 |
| `target_formal_ref` | merge 或 update 时的正式对象引用 |
| `deposit_target` | 用户选择的内容沉淀目标；Prompt 输出只能给 target suggestion，不能静默决定正式沉淀目标 |
| `confirmation_note` | 用户备注，可为空 |

确认响应必须返回 `UserConfirmationRef` 或等价确认记录，包含 actor、target、action、before / after summary、result、trace 和 audit event。
低置信候选的校对保存必须先形成 `CandidateCorrection` / `UserCorrectionRef`，通过 validation 后才允许作为后续 task input 或 confirmation 输入；不得直接反向污染 Prompt source、覆盖原始候选或创建正式对象。

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
- 报告分项通过 `GET /api/v1/reports/{report_id}` 的 `data.sections[]` 返回；不得新增未登记的 sections endpoint。
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
| 成功路径（Success） | 每个核心 endpoint 至少一个 owner 内成功路径；异步 task 能从 create 到 status 到 result |
| Validation failed | 字段缺失、非法 enum、非法 sort/filter、空 Markdown、过长文本、缺少必要 source ref 返回 `validation_failed` |
| 权限拒绝 / 跨用户访问（Permission denied / cross-user access） | 用户 A 无法 list/get/update/delete/generate/copy/confirm 用户 B 的任何资源 |
| Source unavailable | deleted / archived / disabled / inaccessible source 不能进入新生成；历史结果只展示 source availability |
| Low confidence | low confidence 以 `status`、`low_confidence_flags` 和 `next_actions` 返回，不被前端当作高置信成功 |
| Generation failed | provider timeout、schema invalid、semantic invalid、RAG failure 返回 `generation_failed` 或 `validation_failed`，不写 formal object |
| Scoring | 0-100 `score_value` 正常生成；`score_version`、`rubric_version`、`confidence_level`、`evidence_refs` 必须存在；`validation_failed` 不落正式报告评分 |
| Pass tendency | 不返回精确通过概率、录取概率、offer 概率或通过率百分比；低置信度 / source unavailable / validation failed 时不返回确定倾向 |
| Risk wording | `risk_level` 与 `evidence_refs` 同步存在；风险提示带 `risk_reason`、`confidence_level`、版本字段和免责声明 |
| 幂等重试（Idempotent retry） | mutation 和 AI task create 使用同一 `Idempotency-Key` 不重复创建；同 key 不同 body 返回 `idempotency_conflict` |
| Stale version / conflict | `If-Match`、`base_version_ref`、`target_version_ref` 过期返回 `stale_version_conflict` |
| No export endpoint | route inventory 不存在 PDF / Markdown file / Word / docx / export / download endpoint；命中时返回 `export_not_supported` |
| Copy boundary | copy content 仅为 clipboard 结构，不含 prompt/provider payload/hidden scoring rules/internal calibration details/sensitive raw text；复制事件审计不记录正文 |
| 正式对象确认（Formal object confirmation） | candidate / suggestion 不经用户确认不得成为正式 Asset、Weakness、TrainingRecommendation、AssetVersion 或 TrainingTask |
| Rate limit | 登录、简历保存、LLM 生成、RAG 检索、报告生成、复盘生成、训练建议生成触发 429 和 retry metadata |
| 异步取消 / 超时（Async cancellation / timeout） | queued/running task 可取消；timeout 可见；取消或 timeout 不产生 late formal write |
| Pause / resume state machine | 打磨模式和压力面模式暂停均保存最小恢复快照；恢复必须校验 `source_session_snapshot_ref`、`covered_turn_refs`、`ProgressPosition`、owner 和 source availability；缺失时返回 `pause_snapshot_unavailable`、`resume_failed`、`source_unavailable` 或 `partial`，不得重复生成题目、丢弃进展或隐藏低置信度继承 |

## 12. 与 TECH / DATA / SECURITY / PROMPT 的一致性边界

| 子文档 | 一致性点 |
|---|---|
| `TECH_DESIGN.md` | API 继续位于 API 边界层；前端只依赖 API contract，不直接读库或调用 LLM；AI 生成任务由应用编排层串联领域能力、LLM 边界、持久化、trace 和审计 |
| `DATA_MODEL.md` | endpoint 只使用已登记逻辑对象、引用对象和状态域；项目经历只是 Resume Markdown 内容片段或派生 non-persistent outline 节点，不是 API CRUD 子资源；`JobBindingSummary` / `JobMatchSummary` 由 `JobResumeBinding` 和 `JobMatchAnalysis` 派生；`PolishTopicRef` / `PolishSubtopicRef` 只作为打磨上下文选项引用；`AiTaskResultRef`、`CandidateRef`、`SuggestionRef`、`UserConfirmationRef`、`VersionRef`、`TraceRef`、`EvidenceRef` 进入 API envelope |
| `SECURITY_PRIVACY.md` | 未登录拒绝、owner enforcement、source unavailable、复制审计、日志脱敏、Prompt / provider payload 不暴露、copy 非 export 与本文一致 |
| `PROMPT_SPEC.md` | `P-*` 只作为 related prompt contract 和 trace / validation 引用；Prompt contract 的 `api_state_mapping` 不替代 endpoint；failure signals 映射为 API status / error / low confidence |
| `SCORING_SPEC.md` | 本文评分字段必须使用 `SCORING_SPEC.md` 的 score type、`ScoreRuleVersion`、维度、validation、confidence、low confidence 和 forbidden probability 规则；API 不返回隐藏评分规则或完整内部权重表 |
| `SEMANTICS_GLOSSARY.md` | `confidence_level`、`validation_status`、`source_availability` 和 candidate / suggestion / formal object 语义必须与词汇表一致；`available / partial / unavailable / mixed` 只可作为聚合状态 |
| `PERSISTENCE_MODEL.md` | API schema 必须能映射到建议物理模型、join / reference table、owner、version、status、trace、evidence 和 confirmation 记录 |
| `APPLICATION_FLOW_SPEC.md` | endpoint 的同步 / 异步、模型读取 / 写入、AiTask、P-* contract、LLM call plan、Prompt 结构、validation、low confidence 和 persistence handoff 以该文档为编排交接 |

本文件不新增未登记业务对象，不把项目经历提升为一级或二级 CRUD 资源，不引入 MVP non-goal，不定义文件导出，不绕过 candidate / confirmation / formal object 边界。

## 13. Deferred / 非阻断项

以下事项已分类为 deferred_non_blocking 或后续 verification 项，不再作为 `AR-F4-FULL-001` 的 M4 阻断 API UNKNOWN：

- `AR-F4-FULL-003`：评分产品刻度、rubric / rule version、通过倾向分档、风险提示、低置信度降级、版本字段和免责声明已回写并通过 verification；评分公式、score type、维度、权重、低置信度和 F7 fixture 的 canonical 位置为 `SCORING_SPEC.md`；真实招聘结果校准、隐藏规则实现细节和复杂算法调参按 `SHOULD` / `LATER` 处理。
- `AR-F4-FULL-005`：本文已定义 API status / retry / cancel / timeout、`ai_task_id`、`Idempotency-Key` 和 F7 assertion；进展树 / 暂停恢复的完整状态机 fixture 仍由该 Medium finding 后续验证，不改变本轮 AR-F4-FULL-001 的 Fixed 状态。
- 正式 Weakness 生命周期、合并规则、关闭阈值和自动消减规则：API 只允许 candidate / suggestion / confirmation / formal object 边界，自动算法后置。
- Asset 质量判断、版本合并、归档、替代和去重算法：API 只允许候选、质量提示、版本建议和用户确认 endpoint；复杂算法后置。
- Training 优先级、训练结果评估、弱项自动消减和自动训练策略：API 只允许训练建议、训练排序提示、训练任务显式启动和训练结果复盘；自动训练后置。
- 鉴权 API 的完整登录注册产品流程、复杂 ACL、企业多租户和组织权限模型：MVP 使用登录态 actor、owner enforcement、role scope 和标准错误语义；企业治理后置。
- 物理数据库、队列、缓存、日志平台、监控告警和部署拓扑：不属于 API contract 事实源；F5 可以按本 API contract 选择实现方式。

## 14. F8 API 发布检查映射

本节补充 `AR-F4-F8-003` 的 API release check handoff。它只定义 F8 release checklist / runbook / changelog input 的来源映射，不表示健康检查、监控平台、部署拓扑或运维自动化已在 F4 实现。F8 的 canonical release handoff 文档为 `RELEASE_HANDOFF_SPEC.md`。

| 发布检查项 | API 来源 | F8 检查方式 | 不得发生 |
|---|---|---|---|
| route inventory | §6 API 清单总表、§7 逐接口详情 | 对账实现路由的 method + path + API ID；新增 / 删除 / 变更进入 changelog input | F5 自行新增未登记 endpoint |
| no export endpoint | §4.2 `export_not_supported`、§6.5、§10、§11 | route inventory 不存在 `/exports`、`/download`、`/files`、`/pdf`、`/docx`、`/markdown-file`、`/report-file`、download URL 或 filename hint | 用 copy content 伪装下载或返回 export artifact |
| copy content endpoint | `API-REPORT-003`、`API-REVIEW-006`、§10 | 仅返回 clipboard blocks、copy boundary、redaction 状态和 copy content ref | 返回 system prompt、provider payload、completion 原文、hidden scoring rules、无权限正文或下载物 |
| copy event endpoint | `API-REPORT-004`、`API-REVIEW-007`、§10 | 只记录 actor、target、copy surface、scope summary、result、audit ref | 保存复制正文、报告全文、复盘正文或文件产物 |
| rate limit | §3.8、§4.2、§6.2、§11 | 429 返回 `rate_limited`、`Retry-After` / rate limit meta，并按 actor / IP / endpoint / LLM task type 可追踪 | 通过扩大上下文、降级为未审计生成或绕过 owner 校验处理限流 |
| provider failure | §4.1-§4.2、§5.3、§6.2 | `provider_unavailable`、`generation_failed`、`task_timeout`、`validation_failed` 可见且映射 runbook | 把失败结果展示为高置信 success 或写 formal object |
| async task status | §5.2-§5.3、`API-AITASK-*`、`AiTaskStatusResponse` | `queued`、`running`、`partial`、`low_confidence`、`validation_failed`、`source_unavailable`、`generation_failed`、`timed_out`、`cancelled` 均可查询 | cancel / timeout 后 late formal write |
| retry / cancel | `API-AITASK-004`、`API-AITASK-005`、§5.3 | retryable / non-retryable 条件清楚；cancel 只作用于可取消阶段 | retry 扩大上下文、默认启用互联网检索、绕过 owner check |
| health check / trace / audit visibility boundary | §3.2、§3.9、§8.1、§12 | 不含个人数据的健康检查可公开；业务 trace / audit 仅返回必要 id / ref / 摘要 | 前端展开 Prompt、completion、provider payload、request / response body 或 secret |
| response envelope / error envelope | §3.4、§3.5 | 所有响应有 `request_id` / `trace_id`；错误不含敏感正文；业务失败不被 HTTP 200 success 吞掉 | error details 返回正文、token、cookie、provider payload、隐藏评分规则 |
| source unavailable / low confidence / validation failed | §4.3、§6.2、§11 | 新生成阻断或降级；历史结果只展示 source status；validation failed 不 formal write | 读取 `source_deleted` / `source_disabled` 正文或展示为高置信完成 |
| no exact probability | §4.4、§6.5、§11 | 不返回 `pass_probability`、`offer_probability`、`admission_probability`、`pass_rate_percent` 或等价文案 | 将 0-100 product score 解释为真实通过概率 |
| no provider payload / system prompt / hidden scoring rules | §1、§3.5、§10、§11、§12 | API response、copy content、trace 可见内容、error envelope 和日志摘要均不包含这些内容 | 暴露 provider payload、system prompt、completion 原文、hidden scoring rules、完整内部权重表或校准样例正文 |

F8 changelog input 至少从以下 API 变化提取：

- route inventory 的 method / path / API ID 增删改。
- response envelope / error envelope 字段变更。
- async task status、retry / cancel、rate limit、source availability、low confidence 或 validation status 语义变更。
- copy content / copy event / no export boundary 变更。
- scoring response 中 `score_version`、`rubric_version`、`score_rule_version_ref`、`evidence_refs` 或 `trace_refs` 的变更。

## 15. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-24 | 增加 PR3 / PR4 Agent Runtime API contract skeleton | 登记 Agent run status、timeline、interrupt detail、resume interrupt、cancel run 和 PR6 graph descriptor read-only skeleton，并明确 sanitized response、no AgentState、no checkpoint payload、no raw prompt/completion/provider payload、no normal-user debug page |
| 2026-05-24 | 增加 AIFI-BE-004 Pressure mode API handoff | 将 Pressure start / pause / resume / end / report / review handoff 的实现前置条件交给 `PRESSURE_MODE_SPEC.md`；不新增 endpoint，不修改代码，不授权 PR2 graph |
| 2026-05-17 | 修复 `AR-F4-F8-003` API release handoff 缺口 | 新增 F8 API 发布检查映射，覆盖 route inventory、no export endpoint、copy content / copy event、rate limit、provider failure、async task status、retry / cancel、health / trace / audit 可见性、response / error envelope、source unavailable、low confidence、validation failed、no exact probability 和 provider payload / system prompt / hidden scoring rules 禁止项；不新增 endpoint，不进入 implementation |
| 2026-05-17 | 增加 scoring / semantics / persistence / application flow 交接 | 将评分 canonical 规则交给 `SCORING_SPEC.md`，语义枚举交给 `SEMANTICS_GLOSSARY.md`，物理关系交给 `PERSISTENCE_MODEL.md`，应用编排交给 `APPLICATION_FLOW_SPEC.md`；更新 `score_type` canonical enum 和 `ScoreResultResponse` 必填字段 |
| 2026-05-17 | 修复 `AR-DOCS02-SEM-001` UX 可见任务 API 断链 | 新增岗位-简历解绑、复盘列表、复盘复制内容 / 复制事件、低置信候选校对保存和内容沉淀目标确认 endpoint；补齐 request / response、状态、错误、owner、幂等、历史保留和 F7 assertion；不处理 `AR-DOCS02-SEM-002/003`，不进入 implementation |
| 2026-05-17 | 修复 `AR-F4-F8-008` API path / 技术标识符原样性风险 | 回读 API 清单总表、逐接口详情、报告 copy boundary、Schema 索引和 F7 assertion 引用；删除未登记的 report sections endpoint 说明并改为 `data.sections[]`，修正受中文化括注污染的接口名称；当前 API 清单总表与逐接口详情均为 48 个 Method + Path，且不恢复 project-experience module CRUD；不处理 `AR-F4-F8-003`，不进入 implementation |
| 2026-05-17 | 修复 `AR-F4-F8-004` / `AR-F4-F8-005` / `AR-F4-F8-006` 人工审计 API 语义偏差 | Resume API 收敛为 Markdown-only，删除 project-experience module CRUD 和 `modules[]`；`source_availability` 只用于 AI 结果 / 历史引用；Job list/detail 增加 `binding_summary` 与 `latest_match_summary`；Polish session 使用 `resume_job_binding_id`、`topic_id`、`subtopic_id`、`custom_topic_text` 并新增 `GET /api/v1/polish-topics`；不处理 `AR-F4-F8-003`，不进入 implementation |
| 2026-05-17 | 修复 `AR-F4-F8-002` F6 页面接入矩阵缺口 | 新增 F6 Page/API Handoff Matrix，覆盖 32 个 page / surface、19 个状态、前端字段族、candidate / suggestion / confirmation flow、copy boundary、no export / no upload / no exact probability 禁止项和 F2/F3 一致性待补缺口（remaining gaps）；不进入 implementation，不处理 `AR-F4-F8-003` |
| 2026-05-17 | 修复 `AR-F4-F8-001` API 字段级 contract 缺口 | 新增 API 清单总表、当时 49 个核心接口逐接口字段级详情和 Schema 索引（Schema Index）；本轮人工语义修复已删除无效 Resume module CRUD 并新增 Polish topic options API，当前 route inventory 需由 `AR-F4-F8-004` / `005` / `006` focused verification 复核；不新增导出、文件上传解析或实现代码 |
| 2026-05-16 | 修复 `AR-F4-FULL-001` API 阻断项 | 明确 API endpoint、response / error envelope、async task、retry、idempotency、rate limit、permission、copy boundary 和 F7 assertion 已作为 F5/F6/F7 handoff 固化；将剩余算法、状态机和治理细节改为 deferred_non_blocking 或后续 verification 项；等待 verification |
| 2026-05-16 | 修复 `AR-F4-FULL-003` 评分 / 风险 API 语义 | 明确评分不是精确通过概率；补 `score_version`、`rubric_version`、`confidence_level`、`pass_tendency_level`、`risk_level`、`evidence_refs` 响应语义；规定 low confidence / source unavailable / validation failed 降级；增加 F7 断言；不暴露隐藏评分规则 |
| 2026-05-16 | 修复 `AR-F4-FULL-002` API handoff 缺口 | 将 `API_SPEC.md` 从早期占位草案补齐为 F5/F6/F7 可交接 API contract；新增全局约定、错误 envelope、分页 / sorting / filtering、idempotency、rate limit、async task protocol、核心 endpoint matrix、copy boundary 和 F7 test assertions；不写实现代码，不改变其它 finding 状态，不标记 acceptance |
| 2026-05-16 | 修复 `AR-F4-FULL-005` 压力面暂停恢复 API 缺口 | 为压力面会话补充 `pause` / `resume` / `end` / `mark_resume_failed` 状态更新 endpoint，并在 F7 矩阵增加暂停恢复状态机断言；不进入 implementation，不改变 final acceptance 状态 |
| 2026-05-16 | 同步 Asset / Training handoff 与候选确认集中语义 | 补 Candidate / Confirmation 集中语义、Asset API handoff、Training API handoff 和 async / status / retry / idempotency 占位；后续已由 AR-F4-FULL-001 统一分类为已冻结或 deferred_non_blocking |
| 2026-05-16 | 初始化 F4 API 契约早期草案 | 对齐 DATA_MODEL 与 Prompt contracts 中的候选态、建议态、用户确认流、AI task result、response envelope 和 Weakness API handoff；后续已由 `AR-F4-FULL-002` remediation 补齐 endpoint contract，并由 AR-F4-FULL-001 处置表分类 |
