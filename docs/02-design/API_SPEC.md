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

- 本文件是 F4 技术设计下的 API 契约子文档，承接 `AIFI-API-001`。
- 当前版本是骨架草案，用于先对齐 `DATA_MODEL.md` 与 `PROMPT_SPEC.md` 已出现的候选态、正式态、建议态、用户确认流、状态语义、response envelope、Weakness / Asset / Training API handoff 和 async / retry 后续细化边界。
- 本文件不定义完整 endpoint，不冻结完整 request / response schema，不实现代码，不定义 ORM、DDL、migration、索引或物理数据库设计。
- 本文件不关闭 `F4_TECH_DESIGN` UNKNOWN，不标记 `AIFI-ARCH-002`、`AIFI-API-001`、`AIFI-DATA-001` 或 `AIFI-PROMPT-001` 完成。
- 本文件不得把 `archive/**` 作为当前执行依据；历史内容只有迁入 active docs 后才能影响本 API 契约。

## 2. 输入来源与非目标

### 2.1 输入来源

| 来源 | 本文使用方式 |
|---|---|
| `docs/02-design/TECH_DESIGN.md` | API 边界层、应用编排层、LLM 边界和子文档交接原则 |
| `docs/02-design/DATA_MODEL.md` | 逻辑对象、引用对象、候选 / 建议 / 确认流、状态域和审计边界 |
| `docs/02-design/PROMPT_SPEC.md` | AI Task Contract ID、输出状态、validation、low confidence、trace / evidence 和 persistence handoff |
| `docs/02-design/prompt-contracts/WEAKNESS_CONTRACTS.md` | Weakness candidate、merge suggestion、severity assessment、status update suggestion 和用户确认边界 |
| `docs/02-design/prompt-contracts/ASSET_CONTRACTS.md` | Asset candidate、quality hint、version suggestion、source / evidence 和确认前不得写正式 Asset / AssetVersion 的边界 |
| `docs/02-design/prompt-contracts/TRAINING_CONTRACTS.md` | Training recommendation candidate、priority ranking、result review、回流候选和确认前不得自动创建 TrainingTask / 更新 Weakness / 归档 Asset 的边界 |
| `docs/03-delivery/BACKLOG.md` | `AIFI-API-001` 范围和 F4 任务依赖 |

### 2.2 非目标

本文不做以下事项：

- 不展开所有业务 endpoint、path、method、query 参数和 pagination 细节。
- 不冻结最终 request / response 字段全集。
- 不定义完整错误码表、鉴权 API、权限矩阵、复杂 ACL 或多租户策略。
- 不定义物理数据库 schema、ORM model、DDL、索引、外键或 migration。
- 不实现同步 / 异步任务调度、队列、重试、rate limit 或 idempotency 代码。
- 不定义 Prompt 文案、模型供应商、模型参数、向量数据库或 embedding 模型。
- 不把候选对象、建议对象或 AI task result 当作正式业务对象。

## 3. API 资源边界草案

API 层必须区分以下资源语义，后续 endpoint 设计不得混用：

| 资源类别 | 示例对象 | API 边界 |
|---|---|---|
| 正式业务对象 | `Weakness`、`Asset`、`AssetVersion`、`TrainingRecommendation`、`InterviewReport`、`MockInterviewReview`、`RealInterviewReview` | 具有正式生命周期和业务状态；只能由显式业务动作或用户确认后的回流产生或更新 |
| 候选对象 | `WeaknessCandidate`、`AssetCandidate`、后续 Training candidate | 表示 AI 或用户请求产生的待确认对象；默认不等于正式对象 |
| 建议对象 | `WeaknessMergeSuggestion`、`WeaknessSeverityAssessment`、`WeaknessStatusUpdateSuggestion`、`AssetQualityHint`、`AssetVersionSuggestion`、`TrainingPriorityRanking`、`TrainingResultReview` | 表示推荐动作、提示、排序或评估；不等于实际业务写入动作 |
| 用户确认记录 | `UserConfirmationRef` / `UserConfirmation` | 记录 actor、target、action、before / after summary、结果、失败状态和 audit 引用，不压缩为 boolean |
| AI task result | `AiTaskResultRef` | 记录 `contract_id`、status、validation result、low confidence、trace、evidence 和 source；不暴露 provider response |
| 引用与审计 | `SourceRef`、`EvidenceRef`、`TraceRef`、`LlmValidationResult`、`LowConfidenceFlag`、`AuditEvent` | 支撑可追踪、可解释、可审计展示；具体可见性由安全隐私文档收敛 |

## 4. Response Envelope 草案

后续 API response 应采用统一 envelope 语义。以下字段是 F4 草案，不是最终 schema 冻结：

| 字段 | 必填 | 语义 |
|---|---|---|
| `request_id` | 是 | 本次 API 请求追踪标识 |
| `resource_type` | 是 | 返回资源类别，例如 formal object、candidate、suggestion、confirmation、ai_task_result |
| `resource_ref` | 否 | 目标资源引用；列表或聚合响应可为空 |
| `status` | 是 | API 业务状态，不直接等于 HTTP status |
| `data` | 否 | 可展示或可消费的业务结果；不得包含原始 Prompt、completion 或 provider payload |
| `candidate_refs` | 否 | 本次响应涉及的候选引用 |
| `suggestion_refs` | 否 | 本次响应涉及的建议引用 |
| `confirmation_required` | 否 | 是否需要用户确认后才能写入正式对象 |
| `validation_result_ref` | 否 | 输出校验结果引用 |
| `low_confidence_flags` | 否 | 低置信度、冲突、不完整或来源不可用标记 |
| `evidence_refs` | 否 | 支撑关键结论的证据引用 |
| `trace_refs` | 否 | 检索、上下文装配、模型调用、校验、持久化交接和审计过程引用 |
| `error` | 否 | 业务错误摘要；完整错误语义后续收敛 |
| `next_actions` | 否 | 建议动作或确认入口，不等于自动写入动作 |

Envelope 规则：

- HTTP status 只表达传输和协议层结果；业务状态必须在 `status` 或后续等价字段中表达。
- `data` 只能包含通过校验的结构化结果、低置信度结果或部分可用结果，不得直接返回原始 LLM 输出。
- `confirmation_required=true` 时，API 不得把候选或建议静默写成正式对象。
- 低置信度、validation failure、source unavailable 和 manual review 需要有可展示状态和可追踪引用。

## 5. 状态语义草案

以下状态用于 F4 前置同步，不冻结最终 API enum。后续接口设计可以收敛命名，但不得改变候选态、正式态、建议态和用户确认流的语义边界。

| 状态域 | 建议值 | 语义 |
|---|---|---|
| AI task result status | `success`、`partial`、`low_confidence`、`validation_failed`、`generation_failed`、`manual_review_required` | 表达 AI Task Contract 输出结果状态，不等于 provider response 状态 |
| Candidate Status | `candidate_detected`、`awaiting_user_confirmation`、`user_confirmed`、`user_edited`、`user_skipped`、`merged`、`rejected`、`low_confidence`、`manual_review_required` | 表达候选对象从发现到确认、编辑、跳过、合并或拒绝的状态 |
| Suggestion Status | `suggested`、`accepted`、`edited`、`skipped`、`rejected`、`manual_review_required`、`expired` | 表达建议对象是否被采纳、编辑、跳过、拒绝、人工校对或过期 |
| Confirmation Action Type | `confirm`、`edit`、`skip`、`merge`、`reject`、`manual_review` | 表达用户确认动作类型，不压缩为 boolean |
| Weakness Status | `candidate`、`active`、`improving`、`monitoring`、`resolved`、`archived`、`manual_review_required` | 作为 Weakness API 状态收敛占位；不关闭状态流转规则 UNKNOWN |
| Source Availability | `source_available`、`source_archived`、`source_deleted`、`source_disabled`、`source_unavailable` | 表达历史引用来源的当前可用性，不表示历史结论失效 |

## 6. Candidate / Confirmation API 语义草案

本节只定义候选对象、建议对象和用户确认流的通用 API 语义，不定义 endpoint path / method，不冻结完整 request / response schema。后续 Weakness / Asset / Training 相关接口必须复用这些边界。

### 6.1 Candidate lifecycle

candidate 从生成到回流的最小流程如下：

1. `candidate_generated` / `candidate_detected`：AI task 或显式用户请求产生候选；候选必须保留 `CandidateRef`、来源、证据、trace、低置信度和确认要求。
2. `candidate_viewed`：API 可以展示候选内容、来源摘要、证据摘要和低置信度标记，但不得把 candidate 当作正式对象。
3. `candidate_edited`：用户编辑候选时，必须保留 `before_summary` / `after_summary` 和编辑后的确认记录。
4. `candidate_skipped`：用户跳过候选时，保留跳过动作和 audit event，不写正式对象。
5. `candidate_confirmed`：用户确认候选后，才允许进入正式对象创建或更新流程。
6. `candidate_merged`：合并必须保留目标对象、合并前后摘要、冲突信息和确认记录。
7. `candidate_rejected`：拒绝候选时保留拒绝原因、来源和 trace，不能删除原始 AI task result。
8. `manual_review_required`：证据不足、来源不可用、冲突或低置信度时进入人工校对。
9. `failed_to_persist` / `rollback`：回流写入失败时必须保留失败状态、失败原因和 audit event；失败不得破坏原始 AI task result。

Candidate 规则：

- candidate 不是正式对象。
- candidate confirmation 前不得写入正式对象。
- candidate 编辑后需要保留 before / after summary。
- candidate 回流失败不得破坏原始 AI task result。
- candidate 与 suggestion 可以引用同一个 `SourceRef`、`EvidenceRef`、`TraceRef` 或等价证据链。

### 6.2 Confirmation lifecycle

用户确认流最小动作包括 `confirm`、`edit`、`skip`、`merge`、`reject` 和 `manual_review`。这些动作必须生成 `UserConfirmationRef` 或等价确认记录；`UserConfirmationRef` 不是 boolean，不能只用 `true` / `false` 表达确认状态。

确认记录必须能关联：

- `actor_ref`
- `target_ref`
- `confirmation_action`
- `before_summary`
- `after_summary`
- `confirmation_result`
- `trace_refs`
- `audit_event_ref`

确认失败时必须保留失败状态、失败原因、目标对象、trace 和 audit event。若确认动作产生部分成功或需要人工继续处理，API 应表达为 `partial` 或 `manual_review_required`，不得静默改写为成功。

### 6.3 Common candidate / confirmation response fields

以下字段是通用 response 语义，不是完整 response schema 冻结。

| 字段 | 说明 |
|---|---|
| `candidate_refs` | 候选引用 |
| `suggestion_refs` | 建议引用 |
| `confirmation_required` | 是否需要用户确认 |
| `confirmation_ref` | 确认记录 |
| `confirmation_action` | `confirm` / `edit` / `skip` / `merge` / `reject` / `manual_review` |
| `confirmation_result` | `success` / `failed` / `partial` / `manual_review_required` |
| `before_summary` | 确认前摘要 |
| `after_summary` | 确认后摘要 |
| `rollback_safe` | 回流失败是否不破坏原 AI 输出 |
| `audit_event_ref` | 审计引用 |

## 7. Weakness API Handoff 草案

Weakness 相关 API 后续必须至少覆盖以下语义，当前不定义具体 endpoint：

| 资源 / 动作族 | 承接对象 | 边界 |
|---|---|---|
| 薄弱项候选读取与展示 | `WeaknessCandidate`、`CandidateRef`、`AiTaskResultRef` | 展示候选标题、描述、来源、证据、低置信度和确认要求；不得当作正式 Weakness |
| 薄弱项候选确认 | `UserConfirmationRef`、`Weakness` | 用户确认或编辑后才可产生或更新正式 Weakness；失败必须保留确认记录和 audit event |
| 合并建议读取与确认 | `WeaknessMergeSuggestion`、`SuggestionRef`、`UserConfirmationRef` | 合并建议不自动应用；用户确认前不得覆盖既有 Weakness |
| 严重度提示读取 | `WeaknessSeverityAssessment`、`SuggestionRef` | 严重度是 hint，不冻结算法，不等于训练优先级 |
| 状态更新建议读取与确认 | `WeaknessStatusUpdateSuggestion`、`UserConfirmationRef` | 状态更新建议不自动变更正式 Weakness 状态 |
| 证据与 trace 展示 | `WeaknessEvidence`、`EvidenceRef`、`TraceRef`、`LlmValidationResult`、`LowConfidenceFlag` | 展示最小可解释信息；source unavailable 时不得重新读取原文 |

## 8. Asset API Handoff 草案

Asset 相关 API 后续必须至少覆盖以下语义，当前不定义具体 endpoint：

| 资源 / 动作族 | 承接对象 | 边界 |
|---|---|---|
| 资产候选读取与展示 | `AssetCandidate`、`CandidateRef`、`AiTaskResultRef` | 展示候选内容、来源、证据、事实边界、低置信度和确认要求；不得当作正式 `Asset` |
| 资产候选确认 | `UserConfirmationRef`、`Asset`、`AssetVersion` | 用户确认或编辑后才可产生正式 `Asset` 或 `AssetVersion`；失败必须保留确认记录和 audit event |
| 资产质量提示读取 | `AssetQualityHint` 或 `SuggestionRef` | 质量只是 hint，不冻结资产质量算法，不自动归档 |
| 资产版本建议读取与确认 | `AssetVersionSuggestion`、`SuggestionRef`、`UserConfirmationRef` | 版本建议不自动替换、覆盖或发布 `AssetVersion` |
| 资产来源与证据展示 | `AssetSource`、`EvidenceRef`、`TraceRef`、`LowConfidenceFlag` | 展示最小可解释来源；source unavailable 时不得重新读取正文 |

Asset API 规则：

- API 不得把 `AssetCandidate` 当作正式 `Asset`。
- API 不得把 `AssetQualityHint` 当作归档规则。
- API 不得把 `AssetVersionSuggestion` 当作实际发布动作。
- API 不得在确认前写入正式 `Asset` / `AssetVersion`。
- API 不得暴露原始 Prompt、completion 或 provider payload。

## 9. Training API Handoff 草案

Training 相关 API 后续必须至少覆盖以下语义，当前不定义具体 endpoint：

| 资源 / 动作族 | 承接对象 | 边界 |
|---|---|---|
| 训练建议读取与展示 | `TrainingRecommendation` candidate、`CandidateRef`、`AiTaskResultRef` | 展示建议、来源、证据、目标 Weakness / Asset 和低置信度；不得自动创建 `TrainingTask` |
| 训练建议确认 | `UserConfirmationRef`、`TrainingRecommendation` | 用户确认或编辑后才可进入正式训练建议或后续任务创建 |
| 训练优先级排序读取 | `TrainingPriorityRanking` 或 `SuggestionRef` | priority 是 hint，不冻结训练优先级算法 |
| 训练任务启动建议 | `TrainingTask` / `TrainingSession` 初始化建议 | 本轮只定义语义，不定义 endpoint；不得自动启动训练 |
| 训练结果复盘读取 | `TrainingResultReview`、`TrainingResult` | 结果复盘不自动更新 Weakness、不自动归档 Asset、不自动创建下一轮 TrainingRecommendation |
| 训练回流候选 | `WeaknessStatusUpdateSuggestion`、`AssetCandidate`、Training candidate | 回流必须保持候选态 / 建议态和用户确认路径 |

Training API 规则：

- API 不得把 training recommendation candidate 当作正式 `TrainingRecommendation`。
- API 不得自动创建 `TrainingTask`。
- API 不得自动更新正式 Weakness 状态。
- API 不得自动归档 `Asset` 或发布 `AssetVersion`。
- API 不得把 Weakness severity hint 直接等同训练优先级。

## 10. Async / Status / Retry / Idempotency 待收敛项

本节只作为后续 API 细化占位，不定义 endpoint，不实现队列、调度、retry 或 idempotency 代码。

- 长耗时 AI task 后续可能需要 async job。
- MVP 可先同步实现，保持 response envelope、状态语义和失败回滚可追踪。
- 后续需要定义 status query、retry、idempotency key、cancellation、timeout、partial result、validation failed、low confidence 和 manual review required 的 API 语义。
- 本轮不关闭 async / retry / idempotency UNKNOWN。

## 11. 后续接口占位

后续 `AIFI-API-001` 需要在不改变上述语义边界的前提下继续展开以下接口族：

- 简历、简历版本和简历模块。
- 岗位 / JD、岗位版本和岗位-简历绑定。
- 岗位匹配分析、评分结果、匹配点、不匹配点和加强点。
- 打磨模式会话、压力面会话、题目、回答、点评和会话摘要。
- 面试报告、报告分项、可复制内容和低置信度提示。
- 报告相关 API 只提供读取报告、读取报告分项和返回复制所需内容的语义边界；MVP 不提供 PDF / Markdown / Word / docx / 批量文件下载或导出 endpoint，不返回文件名、文件快照或文件生成结果。
- 模拟面试复盘、真实面试输入、真实面试复盘和题级复盘项。
- Weakness candidate、正式 Weakness、合并建议、严重度提示和状态更新建议。
- Asset candidate、正式 Asset、AssetVersion 和资产来源。
- Training recommendation、训练任务、训练结果和训练回流。
- AI task result、validation result、low confidence flag、trace、evidence、audit event 和用户确认记录。

## 12. UNKNOWN / 待收敛项

本文件当前不关闭以下 UNKNOWN：

- 完整 endpoint path、method、request / response 字段全集。
- API error code、retry、idempotency、rate limit、timeout 和异步任务协议。
- 正式 Weakness 状态流转规则、合并规则、关闭阈值和自动消减规则。
- Asset 质量判断、版本合并、归档和替代规则。
- Training 优先级、推荐排序和训练结果映射规则。
- 鉴权 API、权限矩阵、审计保留和日志脱敏细则。

## 13. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-16 | 同步 Asset / Training handoff 与候选确认集中语义 | 补 Candidate / Confirmation 集中语义、Asset API handoff、Training API handoff 和 async / status / retry / idempotency 占位；不定义 endpoint，不关闭 UNKNOWN |
| 2026-05-16 | 初始化 F4 API 契约骨架草案 | 对齐 DATA_MODEL 与 Prompt contracts 中的候选态、建议态、用户确认流、AI task result、response envelope 和 Weakness API handoff；不定义完整 endpoint，不关闭 `F4_TECH_DESIGN` UNKNOWN |
