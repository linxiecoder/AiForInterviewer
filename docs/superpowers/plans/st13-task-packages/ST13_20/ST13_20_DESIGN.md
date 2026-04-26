# ST13_20 DESIGN：服务端保存 / 数据库

## 1. 文档状态

- 状态：`draft`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件是 W13-E8 创建的正式双文档实体之一；W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.design_doc` slot，`exists=true`，`template_like=false`。
- 当前仍未形成 implementation-ready；formal window 仍关闭；implementation packet 仍禁止生成。

## 2. 关联 ST13 / WT13

- ST13：`ST13_20`
- WT13 alias：`WT13-20`
- 任务名称：服务端保存 / 数据库
- 当前来源状态：`task_packet_draft_created` -> `double_doc_registered` -> `contract_refined`

## 3. 关联模块

- 主模块：M01
- 横向关联：M01-M10
- 关键 blocker：M02 权限边界仍需后续模块同步；数据 contract 可以创建文档，但不能进入实现。

## 4. 关联 W13 事实源

- `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-readiness-audit.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-first-contract-task-packages.md`
- `docs/superpowers/plans/st13-task-packages/ST13_21/ST13_21_DESIGN.md`

## 5. 背景

一期 MVP 已 confirmed 必须服务端保存简历、面试过程、历史记录、复盘、评分证据、RAG query/topK、脱敏 LLM 记录、导出记录和训练相关结果。PostgreSQL 是当前已确认主路线，但 schema、migration、ORM、repository 都仍未放行实现。

## 6. 目标

- 建立服务端保存和数据库 contract。
- 明确 PostgreSQL 数据域、核心对象、关系、审计、删除、归档、隐私隔离和回退策略。
- 为 `ST13_21` API、`ST13_24` 测试验收和后续业务任务提供数据 contract 输入。

## 7. 非目标

- 不创建数据库。
- 不创建 migration。
- 不创建 ORM model。
- 不实现 repository、service 或 API。
- 不修改 `DOC_STATE.yaml`。
- 不生成 implementation packet，不打开 formal window。

## 8. 输入

- W13 四份事实源。
- `ST13_21` API / 后端服务边界设计。
- W13-E5 readiness audit 和 W13-E6 / E7 任务包文档。
- 当前状态层中 `ST13_20` 的 blocked 事实；W13-E8.5 已登记 `facts.design_doc` / `facts.implementation_doc`，但 `implementation_doc_state` 仍为 `missing`，`readiness` 仍为 `blocked`。
- `OQ-111=A`、`OQ-112=A`、`OQ-113=B` 用户确认结果。

## 9. 输出

- PostgreSQL 数据域清单。
- 核心实体、关系、生命周期、索引、唯一约束、审计字段草案。
- 数据保存、脱敏、删除、归档、导出、回退策略。
- 下游 `ST13_24` required tests 输入。

## 10. 依赖

- 前置依赖：`ST13_21` API domain 边界。
- 并行依赖：权限、RAG、导出、评分、复盘对象模型。
- 下游依赖：`ST13_24`、`ST13_05`、`ST13_10`、`ST13_13~ST13_19`。

## 11. contract 范围

### 11.1 数据对象分组

| 分组 | 对象 | 保存目标 | 主要消费者 |
| --- | --- | --- | --- |
| 账号与权限 | `User`、`Account`、`Role`、`Permission`、`Session` | 用户身份、角色、权限、资源可见范围和审计入口 | `ST13_01`、`ST13_21`、`ST13_23` |
| 岗位与简历 | `Job`、`Resume` | 岗位、简历、版本、归档和面试引用 | `ST13_03`、`ST13_04`、`ST13_21` |
| 知识库与检索 | `KnowledgeBase`、`KnowledgeDocument`、`KnowledgeChunk`、`RetrievalQuery`、`RetrievalResult`、`Citation / Evidence` | 知识库、文档、chunk、检索结果、引用证据和权限过滤 | `ST13_10`、`ST13_21`、`ST13_24` |
| 面试过程 | `InterviewSession`、`InterviewRound`、`InterviewTurn`、`InterviewAnswer` | 发起、轮次、turn、回答、暂停 / 继续和完成状态 | `ST13_12`、`ST13_13`、`ST13_21` |
| 反馈评分复盘 | `FeedbackSummary`、`ScoreReport`、`ScoreDimension`、`WeaknessItem`、`TrainingTask` | 题级反馈、整场评分、证据绑定、薄弱项和训练任务 | `ST13_14~ST13_17`、`ST13_24` |
| 资产与导出 | `Asset`、`AssetArchive`、`ExportSnapshot`、`ExportRecord` | 归档资产、复制 / Markdown 下载快照和导出动作 | `ST13_18`、`ST13_19` |
| LLM 与审计 | `LLMGenerationRequest`、`LLMGenerationResult`、`AuditEvent`、`OperationLog` | 脱敏生成记录、provider 状态、失败原因、关键操作审计 | `ST13_11`、`ST13_22`、`ST13_25` |

### 11.2 PostgreSQL 主路线边界

- PostgreSQL 是 confirmed 主路线；当前只定义 schema contract，不创建数据库、migration、ORM model 或 SQL。
- 数据 contract 必须给后续 migration 留出版本字段、状态字段、创建 / 更新时间、归档标记、审计字段和外键关系候选。
- 具体表名、索引名、迁移工具、ORM 框架和部署连接方式必须留到 formal window。

### 11.3 User / Account / Role / Permission 保存 contract

- 保存目标：用户身份、账号状态、角色、权限摘要、管理员能力边界和 session 关联。
- 关系：用户可以拥有多个资源；资源必须能回溯 owner、created_by、updated_by 和 visibility。
- 权限字段必须支撑“我的记录”、管理员筛选、公共知识库管理和资源不可见错误。
- 不在一期扩展完整团队组织、邀请、复杂 RBAC 模板或计费权限。

### 11.4 Job 保存 contract

- 保存目标：岗位名称、公司 / 方向、职责、技能要求、面试重点、状态、版本和归档标记。
- 关系：`Job` 被 `InterviewSession`、`ScoreReport`、`SessionRecord` 和导出快照引用。
- 归档后不作为新面试默认输入，但历史会话和复盘必须仍能引用快照或摘要。
- 删除策略默认先归档，硬删除必须另行确认。

### 11.5 Resume 保存 contract

- 保存目标：简历正文、解析摘要、上传 / 粘贴来源、版本、状态、归档标记和脱敏展示字段。
- 关系：`Resume` 被面试发起、评分、复盘、导出和训练建议引用。
- 版本策略必须避免历史面试引用被新编辑内容覆盖；历史记录应引用版本或快照摘要。
- 简历原文属于高敏数据，默认要求权限过滤和导出脱敏检查。

### 11.6 KnowledgeBase 保存 contract

- 保存目标：知识库名称、作用域、可见范围、默认检索配置候选、启用状态和统计摘要。
- 用户私有知识库与管理员公共知识库必须隔离，公共知识库写权限只给管理员。
- `KnowledgeBase` 可被面试发起选择，且需要支持后续 `RetrievalQuery` 回溯。
- 空知识库、禁用知识库和权限过滤后为空必须有可保存状态。

### 11.7 KnowledgeDocument / KnowledgeChunk 保存 contract

- `KnowledgeDocument` 保存上传来源、解析状态、索引状态、失败原因、归档状态和文档摘要。
- `KnowledgeChunk` 保存可检索片段、来源位置、chunk 序号、embedding 状态候选和权限范围。
- 索引失败不能丢失上传记录；必须保留失败原因和可重试标记。
- 具体 embedding provider、向量库和 chunk 算法仍未确认，不在本文档写成实现事实。

### 11.8 RetrievalQuery / RetrievalResult / Citation / Evidence 保存 contract

- `RetrievalQuery` 保存查询上下文、触发场景、知识库范围、过滤条件、topK 候选和执行状态。
- `RetrievalResult` 保存命中摘要、命中数量、无命中原因、权限过滤结果和降级状态。
- `Citation / Evidence` 保存引用来源、chunk 引用、证据摘要、置信说明和被使用场景。
- RAG evidence 可支持评分证据，但不得直接决定分数；评分仍由 `ScoreReport` contract 表达。

### 11.9 InterviewSession 保存 contract

- 保存目标：会话入口、用户、岗位、简历、知识库选择、面试模式、策略、状态、当前轮次和完成时间。
- 状态至少覆盖 `draft / ready / in_progress / paused / completed / reviewed / archived` 的语义。
- 会话必须能回写 `SessionRecord`，并支撑暂停 / 继续、复盘、评分和导出。
- 会话归档不应破坏历史评分、复盘、导出和证据引用。

### 11.10 InterviewRound / InterviewTurn 保存 contract

- `InterviewRound` 保存轮次序号、轮次目标、模式、状态、关联问题集合和证据摘要。
- `InterviewTurn` 保存问题、回答状态、反馈状态、追问状态、评分状态、修订标记和时间戳。
- 状态必须支持打磨模式持续出题、压力面题组完成后结束这两类 confirmed 多轮路径。
- 不在本文档固定“三轮”作为总规则；固定 3 轮只能作为题组策略候选。

### 11.11 InterviewAnswer 保存 contract

- 保存目标：回答正文、提交时间、耗时、版本、是否修订、所属 turn、可见范围。
- 空回答、超时、重复提交必须能被状态字段或事件记录解释。
- 回答原文是敏感数据，导出、日志、Basic Memory 和测试 fixture 均不得泄露真实样例。

### 11.12 FeedbackSummary 保存 contract

- 保存目标：题级反馈、整场反馈摘要、改进建议、证据引用、生成状态和版本。
- 反馈可以先于整场评分存在，也可以因 LLM 失败处于待生成 / 生成失败状态。
- 反馈必须能关联 `InterviewAnswer`、`Citation / Evidence`、`LLMGenerationResult` 和后续 `TrainingTask`。

### 11.13 ScoreReport / ScoreDimension 保存 contract

- `ScoreReport` 保存 0-100 总分、多维评分、生成状态、版本、证据摘要和修订状态。
- `ScoreDimension` 保存维度名、分值、权重候选、解释、证据引用和风险标记。
- 评分失败不能覆盖已保存回答和会话；必须保存失败原因和可重试语义。
- RAG 证据不足时必须能标注“无证据支撑”或“部分轮次未命中”。

### 11.14 WeaknessItem / TrainingTask 保存 contract

- `WeaknessItem` 保存薄弱项、来源证据、影响维度、状态、累计 / 消减记录。
- `TrainingTask` 保存训练动作、目标、关联弱项、完成状态和训练抽屉入口。
- 训练任务不等于二期训练中心完整实现；一期只保存和展示最小闭环所需字段。

### 11.15 Asset / AssetArchive 保存 contract

- `Asset` 保存可复用资产的类型、来源、引用对象、状态和权限。
- `AssetArchive` 保存归档请求、归档时间、原始来源引用、归档快照和恢复候选。
- 资产归档不能绕过简历、回答、RAG evidence 和复盘的权限过滤。

### 11.16 ExportSnapshot / ExportRecord 保存 contract

- `ExportSnapshot` 保存导出时的内容快照、文件名候选、导出范围、RAG 引用范围和脱敏状态。
- `ExportRecord` 保存复制 / Markdown 下载动作、执行用户、时间、状态和失败原因。
- 一期仅支持复制 / Markdown 下载，不做完整 PDF；导出必须可追溯到会话、评分、复盘和证据。

### 11.17 LLMGenerationRequest / LLMGenerationResult 保存 contract

- `LLMGenerationRequest` 保存调用场景、provider 名称、模型名、模板版本、脱敏 prompt 摘要、上下文摘要和关联对象。
- `LLMGenerationResult` 保存生成状态、输出摘要、失败类型、重试次数、latency、token / cost 候选字段。
- 不保存 provider key，不保存未经脱敏的完整 prompt / response，完整保存策略需要后续用户确认。
- LLM 失败必须支撑 API 降级、复盘说明和审计排查。

### 11.18 脱敏策略

- 高敏数据：简历原文、真实面试材料、私有知识库内容、LLM prompt / response、导出快照。
- 默认策略：业务保存可保留必要原文，但日志、测试 fixture、Basic Memory、导出和外部报告必须按权限与脱敏规则过滤。
- 文档样例只能使用字段名和伪结构，不得使用真实用户内容。

### 11.19 删除 / 归档策略

- 一期默认优先归档而不是硬删除，确保历史记录、评分、复盘、导出和证据链可回溯。
- 用户可见删除与系统保留审计之间的关系需后续确认；本文档不直接确认硬删除策略。
- 归档资源不得作为新面试默认输入，但历史引用仍可显示脱敏快照或摘要。

### 11.20 审计日志 contract

- 必须记录登录 / 登出、权限拒绝、知识库上传 / 索引、RAG 检索、LLM 调用、导出、归档 / 删除、状态写回候选事件。
- 审计字段候选：request_id、user 脱敏引用、resource_type、resource_id、action、result、error_code、timestamp。
- 审计日志不保存 provider key、真实简历原文或私有知识库原文。

### 11.21 数据版本 / schema version

- 每个核心保存对象需要版本、状态或 schema version 候选字段，支撑后续 migration、导出重放和历史复盘可解释。
- `ExportSnapshot` 和 `ScoreReport` 必须记录生成版本，避免后续规则变更污染历史结果。
- schema version 只作为 contract 要求，不在本文档定义具体 migration 实现。

### 11.22 与 ST13_21 API contract 的关系

- `ST13_21` 的 request / response 字段必须能映射到本数据 contract 的保存或“不保存”策略。
- API 错误态中的 archived、permission denied、RAG failed、LLM failed 必须能被数据状态和审计事件支撑。
- API contract 未确认的字段不得被本文档写成数据库字段实现。

### 11.23 与 ST13_24 测试 contract 的关系

- 本数据 contract 需要输出 schema relation、权限过滤、数据一致性、RAG evidence 引用完整性和导出快照一致性测试要求。
- migration dry-run 只作为未来测试要求，不表示当前创建 migration。
- 数据脱敏、删除 / 归档和审计日志必须进入后续 P0/P1 验收矩阵。

## 12. 数据 / API / UI / 状态边界

- 数据边界：只定义 schema contract，不建库。
- API 边界：依赖 `ST13_21`，不定义 endpoint 实现。
- UI 边界：只说明页面数据需求，不设计页面。
- 状态边界：本窗口不修改 `DOC_STATE.yaml`；W13-E8.5 已登记 required doc slot，但 formal window、implementation doc activation、acceptance criteria、required tests 和 implementation scope 仍未闭合。

## 13. 权限 / 安全 / 隐私边界

- 用户私有数据、管理员公共知识库和导出记录必须按角色过滤。
- LLMGenerationRequest / Result 必须脱敏保存。
- 删除和归档要保留审计要求，避免误删评分、复盘、导出 evidence。

## 14. 错误态 / 空状态

- 数据不存在、已归档、无权限、schema 不匹配、索引未完成。
- 知识库空、检索无结果、会话中断、评分未生成、导出失败。

## 15. 验收标准

- 明确 User / Account / Role / Permission、Job、Resume、KnowledgeBase / KnowledgeDocument / KnowledgeChunk、RetrievalQuery / RetrievalResult / Citation / Evidence、InterviewSession / InterviewRound / InterviewTurn、InterviewAnswer / FeedbackSummary / ScoreReport、WeaknessItem / TrainingTask / Asset、ExportSnapshot / ExportRecord、LLMGenerationRequest / Result 的保存边界。
- 明确 PostgreSQL 主路线和未来 schema / migration 前置条件。
- 明确脱敏策略、删除 / 归档策略、审计日志、数据版本 / schema version 和 API / 测试依赖。
- 明确不创建数据库、migration、ORM 或 repository。

## 16. 测试要求

未来 required tests 至少包括：

- schema relation validation。
- migration up/down dry-run。
- 权限过滤数据可见性测试。
- 模拟记录、评分、复盘、导出链路数据一致性测试。
- RAG evidence 引用完整性测试。
- 脱敏、删除 / 归档、审计日志和导出快照一致性测试。

本窗口不创建 `tests/**`。

## 17. 允许修改范围

本窗口允许：

- `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md`
- 用户授权的父索引与 W13 计划文档同步。

## 18. 禁止修改范围

- `apps/**`
- `infra/**`
- `tools/**`
- `tests/**`
- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- 数据库配置、migration、ORM、repository 代码
- `docs/modules/**`
- `package.json`、`package-lock.json`、`pnpm-lock.yaml`

## 19. 用户确认项

- `OQ-111=A`：采用集中任务包目录。
- `OQ-112=A`：允许创建第一批正式双文档。
- `OQ-113=B`：required doc slot 由 W13-E8.5 单独 State Update 完成；本窗口不修改 `DOC_STATE.yaml`。

## 20. 下游任务

- `ST13_21`：API contract 的数据对象消费者。
- `ST13_24`：测试 / 验收 / DoD。
- `ST13_05`、`ST13_10`、`ST13_13~ST13_19`：记录、RAG、评分、复盘、导出和训练链路。

## 21. 当前不进入实现说明

本文件经 W13-E9 contract 细化后，`ST13_20` 仍是 `not implementation-ready`。当前不创建数据库，不创建 migration，不创建 ORM，不写 SQL，不生成 implementation packet，不打开 formal window。
