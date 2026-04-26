# ST13_21 DESIGN：API / 后端服务边界

## 1. 文档状态

- 状态：`draft`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件是 W13-E8 创建的正式双文档实体之一；W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.design_doc` slot，`exists=true`，`template_like=false`。
- 当前仍未形成 implementation-ready；formal window 仍关闭；implementation packet 仍禁止生成。

## 2. 关联 ST13 / WT13

- ST13：`ST13_21`
- WT13 alias：`WT13-21`
- 任务名称：API / 后端服务边界
- 当前来源状态：`task_packet_draft_created` -> `double_doc_registered` -> `contract_refined`

## 3. 关联模块

- 主模块：M01
- 横向关联：M01-M10
- 关键 blocker：M02 权限边界仍需后续模块同步；该 blocker 不阻止文档创建，但阻止 implementation-ready。

## 4. 关联 W13 事实源

- `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-double-doc-plan.md`

## 5. 背景

一期 MVP 已确认为工作台级范围，包含真实 LLM、登录 / 权限、服务端保存、历史 / 复盘、RAG / 知识库、多轮高阶面试、0-100 多维评分、复制 / Markdown 下载。当前 W10 `apps/web/**` 原型只作为参考证据，不能作为正式一期 MVP 起点。

API / 后端服务边界是后续数据、页面、LLM、RAG、评分、复盘和导出的共同 contract 前置。当前窗口只创建文档，不创建 `apps/api/**`。

## 6. 目标

- 建立一期工作台 MVP 的 API / 后端服务边界设计文档。
- 明确 Auth、权限、岗位、简历、知识库、RAG、面试、多轮、评分、复盘、导出、运维观测的 API domain。
- 为 `ST13_20`、`ST13_24`、`ST13_23` 和后续业务 ST13 提供 contract 输入。

## 7. 非目标

- 不实现 FastAPI 服务。
- 不创建 `apps/api/**`、`apps/web/**`、`infra/**`。
- 不生成 OpenAPI 文件、路由、service、repository 或测试代码。
- 不修改 `docs/governance/DOC_STATE.yaml`。
- 不生成 implementation packet，不打开 formal window。

## 8. 输入

- W13 四份事实源和 W13-E5 / W13-E6 / W13-E7 文档。
- `DOC_STATE.yaml` 中 `ST13_21` 当前 blocked 状态摘录；W13-E8.5 已登记 `facts.design_doc` / `facts.implementation_doc`，但 `implementation_doc_state` 仍为 `missing`，`readiness` 仍为 `blocked`。
- `OPEN_QUESTIONS.md` 中 `OQ-111=A`、`OQ-112=A`、`OQ-113=B` 的用户确认结果。
- M01-M10 模块文档仅作为历史和模块边界参考。

## 9. 输出

- API domain list。
- endpoint / command / query 边界清单。
- request / response DTO 草案。
- 认证、权限、错误态、分页、筛选、排序、幂等、版本、异步任务状态的 contract。
- 下游任务的 API contract 输入和验收要求。

## 10. 依赖

- 前置依赖：W13 四份事实源、W13-E5 readiness audit、W13-E6 第一批任务包草案、用户确认 `OQ-111=A / OQ-112=A / OQ-113=B`。
- 并行依赖：`ST13_20` 数据 contract 可并行草拟，但必须消费本任务的 API domain 边界。
- 下游依赖：`ST13_20`、`ST13_23`、`ST13_24`、`ST13_01` 以及多数业务 ST13。

## 11. contract 范围

### 11.1 API 分组

| 分组 | 主要对象 | 一期 contract 输出 | 下游依赖 |
| --- | --- | --- | --- |
| Auth / Account | `User`、`Account`、`Role`、`Permission`、`Session` | 登录态、当前用户、角色、资源可见范围和权限错误语义 | `ST13_01`、`ST13_20`、`ST13_23`、`ST13_24` |
| Profile / Workspace | `UserProfile`、`Workspace / Organization` | 一期最小个人工作台上下文，不扩展完整团队管理 | `ST13_20`、`ST13_23` |
| Job / Resume | `Job`、`Resume` | 岗位、简历、版本、归档、发起面试输入 | `ST13_03`、`ST13_04`、`ST13_20` |
| Knowledge / Retrieval | `KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`RetrievalQuery`、`RetrievalResult`、`Citation / Evidence` | 知识库、上传 / 解析 / 索引状态、检索、引用和无命中降级 | `ST13_10`、`ST13_20`、`ST13_24` |
| Interview | `InterviewSession`、`InterviewRound`、`InterviewTurn`、`InterviewAnswer` | 发起、轮次、turn、暂停 / 继续、回答提交和完成回写 | `ST13_12`、`ST13_13`、`ST13_20` |
| Generation | `FirstQuestionGeneration`、`FollowUpQuestion`、`LLMGenerationRequest`、`LLMGenerationResult` | 首题、追问、题组、LLM 调用状态、失败和重试语义 | `ST13_11`、`ST13_12`、`ST13_20` |
| Feedback / Score / Review | `FeedbackSummary`、`ScoreReport`、`ScoreDimension`、`MockInterviewReview`、`RealInterviewReview` | 题级反馈、整场评分、证据绑定和复盘入口 | `ST13_14~ST13_17`、`ST13_24` |
| Record / Export | `SessionRecord`、`ExportSnapshot`、`ExportRecord` | 历史记录列表、筛选、复盘入口、复制 / Markdown 下载 | `ST13_05`、`ST13_19`、`ST13_20` |
| Admin / Ops | `OperationLog`、`AuditEvent`、`LLMProviderConfig` | 管理员最小边界、公共知识库管理、health、配置可见项和观测字段 | `ST13_22`、`ST13_25` |

### 11.2 Auth API contract

- 一期默认采用 session cookie 方向；后续 formal window 才能决定具体 cookie 名、CSRF、防重放和过期策略。
- 必须定义 `login`、`logout`、`refresh session`、`current user`、`permission check` 的 contract 语义。
- 请求字段：账号标识、认证凭据、client context、csrf token 候选字段。
- 响应字段：`user_id`、角色集合、权限摘要、session 过期时间、资源可见范围。
- 错误态：未登录、凭据错误、session 过期、账号禁用、频率限制、权限不足。

### 11.3 Account / Role / Permission API contract

- 一期仅覆盖普通用户 / 管理员角色、管理员公共知识库能力、记录可见范围和资源归属检查。
- Account contract 必须支持“我的记录”“管理员可筛选公共知识库和用户范围”的最小查询语义。
- Role / Permission contract 不扩展完整组织管理、团队邀请或复杂 RBAC 配置；这些作为后置能力。
- 权限错误必须返回稳定 reason：`not_authenticated`、`permission_denied`、`resource_not_visible`、`admin_required`、`archived_resource`。

### 11.4 Job API contract

- 覆盖岗位列表、详情、创建、编辑、归档、恢复候选、作为发起模拟面试必选输入。
- 请求字段：岗位名称、目标公司 / 岗位方向、职责、技能要求、面试重点、状态。
- 响应字段：岗位摘要、版本、状态、最近使用时间、关联知识库摘要、创建者和可见范围。
- 错误态：岗位不存在、已归档不可作为新面试输入、无权限、字段校验失败。

### 11.5 Resume API contract

- 覆盖简历列表、详情、上传 / 粘贴 / 编辑、版本、归档、面试和复盘引用。
- 请求字段：简历文本、上传来源、文件元数据候选、版本说明、可见范围。
- 响应字段：简历摘要、版本号、解析状态、最近引用的面试记录、脱敏展示字段。
- 错误态：空简历、解析失败、版本冲突、已归档、无权限、文件类型不支持。

### 11.6 KnowledgeBase API contract

- 覆盖用户私有知识库、管理员公共知识库、可见范围、启用 / 禁用、关联岗位候选。
- 请求字段：知识库名称、作用域、描述、可见范围、默认检索配置候选。
- 响应字段：知识库摘要、文档数量、索引状态、最近更新时间、权限摘要。
- 错误态：空知识库、无权限、公共知识库仅管理员可写、知识库被禁用。

### 11.7 KnowledgeDocument API contract

- 覆盖文档上传、解析状态、索引状态、失败原因、重试、归档。
- 请求字段：知识库 ID、文档来源、文本或文件元数据、解析策略候选。
- 响应字段：文档 ID、状态、chunk 数量、索引任务 ID、失败原因、可重试标记。
- 错误态：上传失败、解析失败、索引失败、文档已归档、超出大小限制。

### 11.8 Retrieval API contract

- 覆盖 `RetrievalQuery`、`RetrievalResult`、`Citation / Evidence`、无命中降级和证据缺口标注。
- 请求字段：会话 ID、问题 / 回答上下文、知识库集合、topK 候选、过滤条件、调用场景。
- 响应字段：命中片段、引用来源、置信摘要、权限过滤结果、无命中原因、降级建议。
- RAG 无命中不得伪装成有证据；复盘和评分引用必须能区分“有证据”“无命中”“检索失败”。

### 11.9 InterviewSession API contract

- 覆盖发起、草稿保存、准备就绪、进行中、暂停、继续、完成、取消、状态查询和历史记录回写。
- 请求字段：岗位、简历、知识库选择、面试模式、策略、用户上下文、启动入口。
- 响应字段：会话状态、当前轮次、当前 turn、策略摘要、RAG 状态、可执行动作集合。
- 错误态：缺岗位、缺简历、知识库不可见、会话状态冲突、重复完成、无权限。

### 11.10 InterviewRound / Turn API contract

- 覆盖多轮状态、当前 turn、上下文保存、回答提交、追问、模式状态和暂停 / 继续恢复。
- Round 字段：轮次类型、目标能力、状态、关联问题集合、RAG 证据摘要。
- Turn 字段：问题、回答、反馈状态、追问状态、评分状态、可修订标记。
- 状态冲突必须可解释：非 active turn 不接受回答、completed round 不接受追加回答。

### 11.11 Question Generation API contract

- 覆盖首题生成、题组生成、打磨模式下一题建议、压力面题组策略。
- 请求字段：岗位 / 简历摘要、知识库证据、模式、策略、历史回答、弱项候选。
- 响应字段：问题文本、问题目的、证据引用、生成状态、LLM 调用摘要、可重试标记。
- LLM 失败时必须返回稳定状态，不得把 fallback 问题误写成真实 LLM 成功。

### 11.12 Follow-up Generation API contract

- 基于用户回答、RAG evidence、岗位 / 简历上下文和当前轮次目标生成追问。
- 请求字段：会话 ID、turn ID、回答摘要、评分候选、证据集合、追问策略。
- 响应字段：追问文本、追问原因、证据引用、失败 / 重试状态。
- 失败时允许用户继续下一步或重试，但必须记录未生成追问的原因。

### 11.13 Answer Submission API contract

- 覆盖回答提交、原文保存、版本 / 时间戳、可见范围、空回答、超时和重复提交。
- 请求字段：turn ID、回答正文、提交来源、耗时、修订标记。
- 响应字段：保存状态、回答版本、下一步动作、是否触发追问 / 评分。
- 错误态：空回答策略、超时、turn 状态不允许、重复提交、无权限。

### 11.14 Feedback / Score API contract

- 覆盖题级反馈、整场评分、`ScoreReport`、`ScoreDimension`、证据绑定、版本化。
- 请求字段：会话 ID、轮次 / turn 范围、评分场景、证据集合、LLM 生成上下文。
- 响应字段：0-100 总分、多维分、反馈摘要、证据引用、薄弱项、训练建议、生成版本。
- 评分失败不得阻断历史记录保存；必须显式标记“评分待生成 / 生成失败 / 已生成”。

### 11.15 SessionRecord API contract

- 覆盖历史模拟记录列表、筛选、排序、复盘入口、导出入口、权限可见范围。
- 请求字段：分页、状态、岗位、简历、模式、时间范围、评分范围、归档状态。
- 响应字段：记录摘要、会话状态、评分摘要、复盘状态、导出状态、最近动作。
- 空状态必须可验收：无记录、筛选无结果、复盘未生成、导出未生成。

### 11.16 Markdown Export API contract

- 覆盖复制内容、Markdown 下载、导出状态、导出记录、禁止完整 PDF。
- 请求字段：会话 / 复盘 ID、导出范围、是否包含 RAG 引用、是否包含训练建议。
- 响应字段：导出快照 ID、文件名候选、内容范围摘要、状态、失败原因。
- 导出必须按权限过滤；无权限 evidence、真实 provider key、敏感日志不得进入导出内容。

### 11.17 Admin / Permission API 一期边界

- 一期仅覆盖管理员用户管理摘要、公共知识库管理、可见范围筛选、审计查询最小入口。
- 不做完整团队管理、组织层计费、复杂角色模板、批量成员导入。
- 管理员 API 必须带 `admin_required` 错误语义和审计事件要求。

### 11.18 Health / Config / Observability contract

- Health contract 覆盖应用存活、数据库连接候选、LLM provider 可用性候选、索引任务健康候选。
- Config contract 只暴露非敏感配置：环境名、功能开关、provider 名称候选、模型 catalog 摘要。
- Observability 字段：`request_id`、`task_id`、`user_id` 脱敏引用、provider、latency、error_code、token / cost 候选字段。
- 不得在文档样例或日志中出现 provider key、session secret、真实用户简历或私有知识库原文。

### 11.19 API error contract

| 类别 | 稳定语义 | 响应要求 |
| --- | --- | --- |
| Auth | 未登录、session 过期、凭据错误 | 返回可重新登录或刷新 session 的动作提示 |
| Permission | 权限不足、资源不可见、管理员要求 | 返回 reason，不泄露资源是否真实存在的敏感细节 |
| Validation | 字段缺失、类型错误、状态不允许 | 返回字段级错误和可修复提示 |
| State Conflict | 重复提交、会话已完成、资源已归档 | 返回当前状态和允许动作 |
| LLM / RAG | provider 失败、超时、无命中、证据不可用 | 返回可重试标记、降级语义和审计字段 |
| Export | 快照生成失败、权限过滤失败、内容为空 | 返回失败原因和可重试 / 可跳过动作 |

### 11.20 权限错误 contract

- 权限错误不得只返回通用失败，必须区分未登录、角色不足、资源不可见、资源已归档、公共知识库仅管理员可写。
- 对私有资源的错误响应不得暴露无权限用户不应知道的原文、摘要或证据内容。
- 所有权限错误都必须进入审计日志候选字段，以便后续 `ST13_25` 收口和安全复核。

### 11.21 LLM / RAG 失败 contract

- LLM 失败分为 provider 不可用、超时、内容不合规、生成空结果、成本 / 限额失败和解析失败。
- RAG 失败分为知识库为空、检索无命中、索引未完成、检索服务不可用、引用不可回溯和权限过滤后为空。
- 面试主链可继续时必须显式标注降级；不可继续时必须返回阻断原因和恢复路径。

### 11.22 request / response 伪结构示例

| 场景 | request 伪结构 | response 伪结构 |
| --- | --- | --- |
| 发起面试 | `job_id`、`resume_id`、`knowledge_base_ids`、`mode`、`strategy` | `session_id`、`status`、`current_round`、`rag_status`、`available_actions` |
| 提交回答 | `session_id`、`turn_id`、`answer_text`、`elapsed_seconds` | `answer_id`、`version`、`next_action`、`follow_up_status`、`score_status` |
| 检索知识库 | `session_id`、`query_context`、`knowledge_base_ids`、`top_k` | `retrieval_id`、`hits`、`citations`、`no_hit_reason`、`permission_filtered` |
| 生成导出 | `session_id`、`include_rag`、`include_training_tasks`、`format=markdown` | `export_snapshot_id`、`status`、`file_name`、`content_scope`、`failure_reason` |

### 11.23 与 ST13_20 数据 contract 的依赖

- API contract 中出现的对象必须能在 `ST13_20` 中找到保存、脱敏、归档或不保存的明确策略。
- `SessionRecord`、`ScoreReport`、`ExportSnapshot`、`LLMGenerationRequest / Result` 的 API 状态必须与数据状态机对齐。
- 数据 contract 未确认的字段不得被 API contract 写成已实现字段。

### 11.24 与 ST13_24 测试 contract 的依赖

- 每个 API domain 至少产生一类 contract 测试要求：schema、权限、错误态、状态流转或降级。
- LLM / RAG / export 的失败 contract 必须进入 ST13_24 P0/P1 测试矩阵。
- `validate-state` / `evaluate-state` 只验证治理状态，不替代 API contract 测试。

### 11.25 与 ST13_25 文档治理 contract 的依赖

- API contract 变更必须回写任务包双文档、父索引和后续 readiness 复核材料。
- 若未来生成 OpenAPI 文件、schema 文件或实现目录，必须另走用户确认卡和 formal window，不得由本文档直接放行。
- 本文档的 contract_refined 状态只表示设计细化完成，不表示实现完成。

## 12. 数据 / API / UI / 状态边界

- 数据边界：只定义 API 需要的数据对象，不落库。
- API 边界：只定义 contract-first 输入输出，不实现 endpoint。
- UI 边界：为 `ST13_23` 页面规格提供调用约束，不做页面设计。
- 状态边界：本窗口不修改 `DOC_STATE.yaml`；W13-E8.5 已登记 required doc slot，但 formal window、implementation doc activation、acceptance criteria、required tests 和 implementation scope 仍未闭合。

## 13. 权限 / 安全 / 隐私边界

- 所有 API 必须带用户身份上下文和资源可见范围。
- 简历、回答、RAG evidence、导出内容、LLM 日志必须有脱敏和权限过滤要求。
- 管理员公共知识库与用户私有知识库必须隔离。
- provider key、session secret、模型密钥不得写入文档样例或日志。

## 14. 错误态 / 空状态

- 未登录、权限不足、资源不存在、已归档、输入校验失败。
- 知识库空、RAG 无命中、LLM provider 失败、异步任务超时。
- 历史记录为空、复盘尚未生成、导出尚未完成。

## 15. 验收标准

- API domain 覆盖 Auth、Account、Role、Permission、Job、Resume、KnowledgeBase、KnowledgeDocument、Retrieval、InterviewSession、InterviewRound、InterviewTurn、Question Generation、Follow-up Generation、Answer Submission、Feedback / Score、SessionRecord、Markdown Export、Admin / Permission、Health / Config / Observability。
- 每个 domain 至少说明输入、输出、权限上下文、错误态和下游依赖。
- API error contract、权限错误 contract、LLM / RAG 失败 contract 均有稳定语义。
- request / response 伪结构只作为文档 contract，不生成 OpenAPI、schema 或代码。
- 与 `ST13_20` 数据 contract、`ST13_24` 测试 contract、`ST13_25` 治理 contract 的依赖清楚。
- 明确 contract-first，且不得出现实现代码或目录创建。

## 16. 测试要求

未来 required tests 至少包括：

- API contract schema validation。
- 权限矩阵测试。
- API error taxonomy 测试。
- 幂等与状态流转测试。
- LLM / RAG / scoring / export 异步任务状态测试。
- request / response 字段最小一致性测试。
- API 与数据 contract 字段漂移检查。

本窗口不创建 `tests/**`。

## 17. 允许修改范围

本窗口允许：

- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md`
- 用户授权的父索引与 W13 计划文档同步。

未来实现窗口是否允许创建 `apps/api/**` 仍需 formal window。

W13-E14-C 复核窗口的实际授权范围进一步收窄为仅修改本节所属 `ST13_21` 双文档；父索引、W13 计划文档、`DOC_STATE.yaml`、模块文档和任何实现目录均不在本窗口授权内。如发现需要同步总控文件，只能交接给 W13-E14-Merge。

## 18. 禁止修改范围

- `apps/**`
- `infra/**`
- `tools/**`
- `tests/**`
- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- `docs/modules/**`
- `package.json`、`package-lock.json`、`pnpm-lock.yaml`
- Git 提交、推送、reset、clean、stash、rebase、merge、checkout

## 19. 用户确认项

- `OQ-111=A`：采用集中任务包目录。
- `OQ-112=A`：允许 W13-E8 创建第一批正式双文档。
- `OQ-113=B`：required doc slot 由 W13-E8.5 单独 State Update 完成；本窗口不修改 `DOC_STATE.yaml`。

## 20. 下游任务

- `ST13_20`：服务端保存 / 数据库。
- `ST13_23`：前端工作台 UI / 页面集合。
- `ST13_24`：测试 / 验收 / DoD。
- `ST13_01`：账号 / 登录 / 权限。
- 后续业务 ST13 的 API 调用和错误态验收。

## 21. 当前不进入实现说明

本文件经 W13-E9 contract 细化后，`ST13_21` 仍是 `not implementation-ready`。当前不创建 `apps/api/**`，不生成 OpenAPI 文件，不生成 schema 文件，不生成 implementation packet，不打开 formal window，不把 API contract 草案写成已实现。

## 22. W13-E13.5 candidate 表达策略同步

W13-E13.5 后，`ST13_21` 继续保持文档层 `near_ready_for_formal_window_candidate_confirmed`，但不写正式状态层 `candidate_status`，不写 `readiness=downstream_ready`，不写 formal window candidate，不写 implementation-ready。

后续只有在 M02 blocker、OpenAPI / `apps/api/**` 授权和 formal window 前置条件闭合后，才重新评估是否进入 candidate 状态表达。当前不创建 `apps/api/**`，不生成 implementation packet，不打开 formal window。

## 23. W13-E13.8 facts-only State Update 保持策略

W13-E13.8 只对 `ST13_24 / ST13_25` 执行 facts-only candidate 推荐字段写入；`ST13_21` 保持正式 `DOC_STATE.yaml` 原样，未写 candidate facts，未写 `candidate_status=candidate`，未写 `readiness=downstream_ready`，未写 near-ready 状态。

`ST13_21` 仍仅在文档层保持 `near_ready_for_formal_window_candidate_confirmed` 口径。后续必须先关闭 M02 blocker、OpenAPI / `apps/api/**` 授权和 formal window 前置条件，才可重新评估状态层 candidate 表达；当前仍不得创建 `apps/api/**`、OpenAPI、schema、implementation packet 或 formal window。

## 24. W13-E14-C near-ready blocker 复核

本节只记录 W13-E14-C 对 `ST13_21 / WT13-21` 的文档层复核结果，不新增状态枚举，不修改 `DOC_STATE.yaml`，不生成 implementation packet，不打开 formal window。

### 24.1 near-ready blocker 清单

| blocker | 当前判断 | 为什么阻止升级为 formal_window_candidate |
| --- | --- | --- |
| M02 权限 / 角色 / session / access control | M02 仍存在 `doc:api`、`doc:open_questions` 等模块文档 blocker，`/members` 共享最小层闭合不能外推为完整权限 ready。 | `ST13_21` 的 Auth、Account、Role、Permission、Session、资源可见范围和权限错误语义都消费 M02；M02 未闭合前，API contract 只能 near-ready。 |
| OpenAPI 文件授权 | 未获得创建或维护 OpenAPI 文件的用户授权。 | OpenAPI 一旦落盘会从文档 contract 进入可执行接口产物，需单独确认文件位置、版本策略和维护责任。 |
| `apps/api/**` 创建授权 | 未获得创建后端服务目录、路由、service、repository 或应用骨架的用户授权。 | 创建目录会被误读为 formal window 或 implementation-ready 已打开，当前明确禁止。 |
| schema / data contract 联动 | API 字段已形成伪结构，但真实 schema 文件、DTO 文件、数据库 schema、migration、ORM 均未授权。 | API request / response 字段必须与 `ST13_20` 保存 / 不保存 / 脱敏 / 归档策略一致，未对齐前不能升级。 |
| `ST13_20` 依赖 | `ST13_20` 同样保持 `near_ready_for_formal_window_candidate_confirmed`，且仍等待 schema / migration / ORM 授权。 | API contract 中的 `SessionRecord`、`ScoreReport`、`ExportSnapshot`、`LLMGenerationRequest / Result` 等状态必须有数据 contract 支撑。 |
| provider / LLM / RAG 错误语义 | provider、模型、embedding、RAG 无命中、检索失败、LLM 失败和成本 / 限额错误已有文档层语义，但未形成可执行错误码或测试矩阵。 | 这些错误会影响发起面试、追问、评分、复盘和导出；未进入 `ST13_24` 可执行测试前不能视为 formal candidate。 |
| 安全 / 隐私 / 脱敏边界 | 身份上下文、资源可见范围、简历 / 回答 / RAG evidence / LLM 日志 / 导出脱敏已有原则，但未完成实现级授权与审计策略落地。 | API 一旦进入 formal window，需要明确日志字段、敏感内容过滤、provider key 保护和导出权限过滤；当前只能停留文档层。 |
| 状态层 gate | `formal_window_open=false`，`implementation_doc_state` 未激活，implementation packet inputs 仍未闭合。 | 当前工具 gate 不允许生成 implementation packet，也不允许标记 implementation-ready。 |

### 24.2 API contract readiness 摘要

已清楚的 API contract：

- API domain 已覆盖 Auth / Account / Role / Permission、Profile / Workspace、Job / Resume、Knowledge / Retrieval、Interview、Generation、Feedback / Score / Review、Record / Export、Admin / Ops。
- Auth、权限错误、RAG 无命中、LLM provider 失败、状态冲突、导出失败等错误语义已在文档层形成稳定分类。
- request / response 伪结构已经能支撑后续 OpenAPI、DTO、schema 和测试矩阵设计。
- 与 `ST13_20`、`ST13_24`、`ST13_25` 的依赖关系已经可用于后续窗口排序。

仍只是文档层的 API contract：

- 所有 endpoint、DTO、错误码、OpenAPI path、schema 文件、后端目录和测试文件都尚未创建。
- `allowed_modify_paths`、`required_tests`、`acceptance_criteria` 尚未作为 implementation packet input 被状态层激活。
- `near_ready_for_formal_window_candidate_confirmed` 只表示文档层接近 candidate，不等于 `candidate_status=candidate`。

必须等待 `ST13_20 / M02` 的 contract：

- `User / Account / Role / Permission / Session` 必须等待 M02 权限边界和 session/access control 消费关系闭合。
- `Job`、`Resume`、`KnowledgeBase`、`KnowledgeDocument`、`InterviewSession`、`ScoreReport`、`ExportSnapshot`、`LLMGenerationRequest / Result` 必须等待 `ST13_20` 明确保存、脱敏、归档、不保存或审计策略。
- RAG / LLM / provider 失败状态必须等待 `ST13_20` 的数据状态机和 `ST13_24` 的 required tests 对齐。

formal window 前不能创建的文件：

- 不创建 OpenAPI 文件。
- 不创建 `apps/api/**`。
- 不创建 schema / DTO / shared type 文件。
- 不创建 `tests/**` 或 API contract 测试文件。

### 24.3 candidate 升级条件

`ST13_21` 从文档层 `near_ready_for_formal_window_candidate_confirmed` 升级为正式 formal window candidate，至少需要同时满足：

1. M02 权限 / 角色 / session / access control blocker 已由模块或总控窗口复核为已闭合，或用户明确确认在未闭合前仍允许以受限方式进入 candidate。
2. 用户明确确认是否允许创建 OpenAPI 文件，并确认路径、格式、版本策略和维护责任。
3. 用户明确确认是否允许创建 `apps/api/**` 或其他后端服务目录。
4. 用户明确确认是否允许创建 schema / DTO / shared contract 文件。
5. `ST13_20` 数据 contract 已明确 API 字段的保存 / 不保存 / 脱敏 / 归档 / 审计策略，且无互斥字段。
6. `ST13_24` 已承接 API schema、权限矩阵、错误态、LLM / RAG 降级、导出权限过滤等 required tests。
7. `preflight-open-window` 或同等状态层 gate 对 `ST13_21` 不再报告阻断 formal window candidate 的 blocker。
8. `validate-state` / `evaluate-state` 仍为 `ok=true,error=0,warning=0`，且不引入 `formal_window_open=false` 与 `candidate_status=candidate` 的规则冲突。

当前未闭合的用户确认项包括：OpenAPI 文件、`apps/api/**`、schema 文件、`DOC_STATE.yaml` candidate 写入、formal window open、implementation packet、candidate 升级、是否扩大 ST13 范围。

当前未通过或未执行的工具 gate 包括：`preflight-open-window`、`open-window`、`generate-implementation-packet`；这些 gate 不应由本设计文档正文替代。

### 24.4 allowed / forbidden paths 当前摘要

当前 W13-E14-C 只允许继续细化文档层说明：

- 允许：`docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`
- 允许：`docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md`

当前仍禁止：

- 禁止创建或修改 `apps/api/**`。
- 禁止创建 OpenAPI 文件。
- 禁止创建 schema、DTO、shared contract 或类型文件。
- 禁止创建或修改 `tests/**`。
- 禁止修改 `docs/governance/**` 和 `docs/governance/DOC_STATE.yaml`。
- 禁止修改 `apps/**`、`infra/**`、`tools/**`、`docs/modules/**`、父索引和全局总控文档。

### 24.5 formal window 前置条件

进入 `ST13_21` formal window open 确认前，至少需要：

1. W13-E14-Merge 或总控窗口吸收本复核结论，并确认是否需要更新索引或状态层准备文档。
2. M02 权限 blocker、OpenAPI 授权、`apps/api/**` 授权、schema / data contract 联动和 `ST13_20` 依赖均有明确处理结论。
3. 用户确认 formal window open 的目标、允许修改范围、禁止修改范围、required tests、acceptance criteria、回退方案和交接输出。
4. 状态层 preview 或 preflight 结果证明不会把 near-ready 误写为 `candidate_status=candidate`、`readiness=downstream_ready` 或 `implementation_ready`。
5. `validate-state` / `evaluate-state` 在正式 `DOC_STATE.yaml` 上保持全绿，并且 `documents_blocked_count=0`。

在上述条件未满足前，`ST13_21` 仍保持文档层 near-ready；仍不能实现，不能生成 implementation packet，不能打开 formal window。
