---
title: ASSET_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/asset-contracts
---

# ASSET_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件遵守 `PROMPT_SPEC.md` §13 的 `AR-F4-FULL-001` 处置口径；复杂算法和实现细节按 deferred_non_blocking 承接。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 当前状态

本文件承载主 catalog 中 `P-ASSET-001` 至 `P-ASSET-003` 的详细 contract 正文。Asset contracts 当前为 Draft，仍属于 F4 Prompt / AI 子任务 contract 草案，不代表实现完成，不代表 `AIFI-PROMPT-001` DONE。

## 3. Asset Contract 细则

### 3.0 Asset 公共字段与边界

#### Asset 公共职责

Asset contracts 只负责从 Polish、Report、Review、Weakness 等上游输出中提炼资产候选，生成资产质量提示，并生成资产版本更新建议。Asset contracts 不负责自动创建正式 `TrainingRecommendation`、生成完整训练计划、自动覆盖既有 `Asset`、自动替换 `AssetVersion`，也不实现资产质量、资产归档、资产版本合并或训练优先级复杂算法。

#### Asset 公共上游输入

Asset contracts 可以消费 Polish asset candidates、Report strengths / copyable content / positive evidence、Mock / Real Interview Review、Review items、Weakness outputs、existing `Asset`、`AssetVersion`、`AssetSource`、`UserConfirmationRef`、low confidence flags、evidence refs、trace refs、`JobVersion` / `ResumeVersion`、RAG evidence 和公共参考材料。上述输入必须按任务最小必要装配，不得默认塞入全部简历、全部岗位、全部历史会话、全部报告、全部复盘、全部知识库、全部资产或全部薄弱项。

#### Asset 公共检索边界

- `JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG。
- Polish / Report / Review / Weakness outputs 是结构化上游，不是 RAG。
- 既有 `Asset`、`AssetVersion` 和 `AssetSource` 是条件检索来源，不是默认全量上下文。
- RAG / 知识库可用于技术表达、内容证据和资产复用场景增强，但不是 Asset MVP 硬依赖。
- 互联网检索不是 MVP 默认强依赖，不得默认启用。
- 条件检索必须经过 `P-SHARED-002` Retrieval Planning。
- 证据不足、来源不可用、输入冲突或上下文裁剪影响判断时，必须进入 low confidence 或 manual check。

#### Asset 公共输出边界

Asset 输出可以保存为 asset candidate、asset quality hint、asset version suggestion、`AssetSource`、validation result、low confidence flag、evidence refs、trace refs 和 audit event。Asset 输出不得直接写入 `TrainingRecommendation`、训练任务、新的 Report、新的 Review 或新的 Weakness 状态更新。

正式 `Asset` 的创建、`AssetVersion` 更新、归档、替换和合并必须保留用户确认、编辑、跳过或合并路径。若后续产品允许自动创建候选，也必须保持候选态和证据引用，不得绕过用户确认直接写入正式对象。

#### Asset 公共 Output Schema

`P-ASSET-001` 至 `P-ASSET-003` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `asset_ref` | 否 | ref | 既有或目标 Asset 引用 |
| `asset_version_ref` | 否 | ref | 既有或目标 AssetVersion 引用 |
| `asset_candidate_refs` | 否 | ref[] | 资产候选引用 |
| `candidate_refs` | 否 | ref[] | 通用候选引用，承接 `CandidateRef` |
| `suggestion_refs` | 否 | ref[] | 通用建议引用，承接 `SuggestionRef` |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的证据 |
| `asset_source_refs` | 否 | ref[] | AssetSource 引用 |
| `weakness_refs` | 否 | ref[] | 关联 Weakness 或 WeaknessCandidate 引用 |
| `review_item_refs` | 否 | ref[] | 复盘项引用 |
| `report_refs` | 否 | ref[] | 报告引用 |
| `polish_refs` | 否 | ref[] | Polish 来源引用 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记 |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能进入正式对象 |

`next_recommended_actions` 允许值至少包括 `confirm_asset_candidate`、`edit_asset_candidate`、`skip_asset_candidate`、`merge_asset_candidate`、`create_asset_version`、`request_more_evidence`、`mark_for_training`、`enter_polish_mode`、`enter_pressure_mode` 和 `manual_check_required`。这些 action 只是建议动作或用户确认入口，不得直接写入正式 `TrainingRecommendation`；需要用户确认的 action 必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。

#### Asset 公共校验与失败边界

- 必须引用 `P-SHARED-001` Context Assembly、`P-SHARED-002` Retrieval Planning、`P-SHARED-003` Output Validation、`P-SHARED-004` Low Confidence Classification 和 `P-SHARED-005` Evidence Binding 中与当前任务相关的规则。
- 必须保留 validation、Low Confidence、EvidenceRef、TraceRef、CandidateRef、SuggestionRef 和 AuditEvent 交接。
- 不得生成完整生产 Prompt 文案、原始 Prompt、completion 或 provider payload。
- 不得定义 API endpoint、物理数据库 schema、LLM provider、模型参数、向量数据库、embedding 模型或搜索服务。
- 不得自动创建正式 Asset、自动发布 AssetVersion、自动创建 TrainingRecommendation 或训练任务。
- 不得把资产质量规则、资产归档策略、资产版本合并策略、资产可复用评分或训练优先级算法实现为自动正式写入；这些复杂算法为 deferred_non_blocking。

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-ASSET-001` | Asset Candidate Extraction | 提炼资产候选 | Draft |
| `P-ASSET-002` | Asset Quality Hint | 生成资产质量提示 | Draft |
| `P-ASSET-003` | Asset Version Suggestion | 生成资产版本更新建议 | Draft |

### 3.1 P-ASSET-001 Asset Candidate Extraction

- Contract ID: `P-ASSET-001`
- Name: Asset Candidate Extraction
- Mode: `asset`
- Trigger:
  - Polish 产生 asset candidate。
  - Report 产生 strengths summary、copyable content 或 positive evidence。
  - Review 产生 asset candidate refs 或高价值表达片段。
  - Weakness / Review 暴露可沉淀的改进表达、项目表述或技术解释。
  - 用户请求保存为资产。
  - 系统需要把多来源内容收敛为资产候选。
- Goal: 从 Polish、Report、Review、Weakness 等上游结果中提炼资产候选；本 contract 只提炼候选，不绕过用户确认创建正式 `Asset` 或 `AssetVersion`。
- Required Inputs:
  - `OwnerRef`
  - 至少一个 source artifact：Polish / Report / Review / Weakness 输出之一
  - evidence refs
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - existing `Asset`
  - `AssetVersion`
  - `AssetSource`
  - `JobVersion`
  - `ResumeVersion`
  - user confirmations
  - low confidence flags
  - RAG evidence
- Retrieval Sources:
  - 默认使用显式 source artifact 和 evidence refs。
  - 条件读取既有 `Asset`、`AssetVersion`、`AssetSource`、Polish / Report / Review / Weakness 结构化摘要。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
  - 无既有 `Asset` 时仍可生成候选，但必须保留候选态。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 source artifact summary、candidate content、evidence refs、低置信度、source availability、已有 Asset 摘要和输出 schema。
  - 不得默认塞入全部历史会话、全部报告、全部复盘、全部资产或全部知识库。
  - 上下文过长时优先保留用户原始表达、用户确认事实、可复用表达、证据、适用场景和当前候选依据。
- Excluded Inputs:
  - 用户未表达或未确认的项目、数据、职责、成果或技术经验作为事实。
  - 未确认资产候选作为正式资产事实。
  - 正式 `TrainingRecommendation`、训练任务、新 Report、新 Review 或 Weakness 状态更新写入动作。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 全量历史会话、全量报告、全量复盘、全量资产、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Asset 公共 Output Schema。
  - `asset_candidates`
  - 每个候选的 `candidate_id`
  - 每个候选的 `candidate_status`
  - 每个候选的 `asset_type_hint`
  - 每个候选的 `title`
  - 每个候选的 `content_draft`
  - 每个候选的 `source_type`
  - 每个候选的 `source_refs`
  - 每个候选的 `evidence_refs`
  - 每个候选的 `facts_used_from_user`
  - 每个候选的 `model_suggested_phrasing`
  - 每个候选的 `facts_requiring_user_confirmation`
  - 每个候选的 `not_assumed_facts`
  - 每个候选的 `reuse_scenarios`
  - 每个候选的 `related_job_requirements`
  - 每个候选的 `related_resume_modules`
  - 每个候选的 `related_weakness_refs`
  - 每个候选的 `merge_candidate_asset_refs`
  - 每个候选的 `user_edit_required`
  - `extraction_summary`
  - `candidate_ordering`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 每个候选必须绑定 source refs 和 evidence refs。
  - 不得把模型生成内容伪装成用户真实经历。
  - 不得虚构用户项目、数据、职责、成果或技术经验。
  - 不得把低置信度内容包装成可直接归档资产。
  - 不得静默覆盖既有 `Asset`。
  - 如可能与既有 `Asset` 重复，应输出 merge candidate refs。
  - `asset_type_hint` 只是候选分类，不冻结资产分类算法。
  - `content_draft` 必须区分用户事实、模型建议表达和待用户确认内容。
- Low Confidence Rules:
  - evidence 不足。
  - source artifact 低置信度。
  - 用户事实不足。
  - 无法区分用户事实和模型建议表达。
  - 与既有 `Asset` 冲突。
  - source unavailable。
  - 技术内容缺少知识 evidence。
  - 上下文裁剪影响候选归因。
- Evidence Requirements: 每个候选的标题、正文草案、用户事实、模型建议表达、复用场景、关联岗位 / 简历 / Weakness 和合并候选都必须绑定 source refs、evidence refs、validation result refs 和 trace refs；无法绑定时必须输出低置信度或要求用户补充。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、资产候选提炼、重复或合并线索检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `AssetCandidate` 或等价待确认对象。
  - `AssetSource`
  - `CandidateRef`
  - `UserConfirmationRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 默认需要用户确认后才能成为正式 `Asset` 或 `AssetVersion`。
  - 用户可以确认、编辑、跳过、合并或要求重新生成。
  - 用户确认动作必须形成 `UserConfirmationRef` 或等价记录。
- Retry / Fallback:
  - `OwnerRef`、source artifact、evidence refs 或 owner 校验缺失时停止正常提炼，返回失败或补充材料路径。
  - 用户事实不足、技术证据不足、source unavailable 或与既有资产冲突时可保存低置信度候选、要求用户编辑确认或降级为待补充草稿。
  - 重试不得默认启用互联网检索、扩大到全量历史上下文、虚构用户经历、覆盖既有资产或自动归档正式资产。
- API State Mapping: 只定义状态语义，包括 `asset_candidate_available`、`asset_candidate_partial`、`asset_candidate_low_confidence`、`asset_candidate_validation_failed`、`user_confirmation_required`、`merge_candidate_detected` 和 `user_facts_insufficient`；不定义 endpoint 或 schema。
- Security Notes: 资产候选只使用当前 owner 的授权来源、可展示证据摘要和必要 trace id；不得暴露无权限来源正文、原始 Prompt、completion、provider payload 或隐私字段。
- Test Strategy: 使用 fixture 覆盖 Polish 候选、Report strengths / copyable content、Review item、高价值表达片段、Weakness 改进表达、用户主动保存、无既有资产、重复资产合并线索、用户事实不足、技术证据缺失、source unavailable、用户确认 / 编辑 / 跳过 / 合并和不得自动创建正式 Asset / AssetVersion / TrainingRecommendation。
- Open Questions: 资产分类算法、资产质量规则、资产归档策略、资产合并算法、版本替代规则和正式 Asset API 字段仍待后续 Asset / API / UX 收敛，为 deferred_non_blocking。

### 3.2 P-ASSET-002 Asset Quality Hint

- Contract ID: `P-ASSET-002`
- Name: Asset Quality Hint
- Mode: `asset`
- Trigger:
  - `P-ASSET-001` 产生资产候选后。
  - 用户请求查看资产质量。
  - 既有 `AssetVersion` 更新前。
  - 报告 / 复盘 / Polish 产生新的表达证据后。
  - 系统需要判断候选是否适合归档或是否需要用户编辑。
- Goal: 对资产候选或既有 `Asset` / `AssetVersion` 生成质量提示；本 contract 不冻结资产质量算法，只生成基于证据和上下文的 quality hint、风险提示和改进建议。
- Required Inputs:
  - `OwnerRef`
  - Asset candidate 或 `Asset` / `AssetVersion` refs
  - source refs
  - evidence refs
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - `JobVersion`
  - `ResumeVersion`
  - related Weakness / Review items
  - existing AssetVersion history
  - user confirmation history
  - RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用资产候选或目标 `AssetVersion`、source refs、evidence refs。
  - 条件读取历史 `AssetVersion`、相关 Weakness、Review items、Job / Resume、RAG evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 candidate / asset content、source refs、evidence refs、用户事实标记、待确认字段、适用场景和输出 schema。
  - 不得默认塞入全部资产、全部报告、全部复盘或全部知识库。
  - 上下文过长时优先保留资产正文、事实边界、证据、适用场景、冲突和低置信度。
- Excluded Inputs:
  - 未确认项目、数据、职责、成果或技术经验作为质量结论依据。
  - 自动归档、自动创建版本或自动创建 TrainingRecommendation 的写入动作。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 全量资产库、全量报告、全量复盘、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Asset 公共 Output Schema。
  - `asset_quality_hints`
  - 每个 hint 的 `target_asset_ref`
  - 每个 hint 的 `target_candidate_ref`
  - 每个 hint 的 `quality_level_hint`
  - 每个 hint 的 `quality_reason`
  - 每个 hint 的 `reuse_readiness_hint`
  - 每个 hint 的 `fact_boundary_risks`
  - 每个 hint 的 `phrasing_risks`
  - 每个 hint 的 `technical_accuracy_risks`
  - 每个 hint 的 `missing_context`
  - 每个 hint 的 `evidence_refs`
  - 每个 hint 的 `confidence`
  - `edit_recommendations`
  - `manual_review_required`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 质量提示必须基于 candidate / `AssetVersion`、source refs 和 evidence。
  - `quality_level_hint` 只是提示，不冻结资产质量算法。
  - 不得把模型建议表达当成用户事实。
  - 不得确认未被用户确认的项目、数据、职责、成果。
  - 技术准确性风险缺少 evidence 时必须低置信度。
  - `reuse_readiness_hint` 只是复用准备度提示，不等于自动归档。
  - 质量不足时必须建议用户编辑或 manual review。
- Low Confidence Rules:
  - source evidence 不足。
  - 用户事实边界不清。
  - 技术内容缺少 evidence。
  - 与既有 `Asset` 冲突。
  - 适用场景不明确。
  - 上下文裁剪影响质量判断。
  - 用户确认缺失。
- Evidence Requirements: 每个质量提示的目标对象、质量原因、事实边界风险、表达风险、技术准确性风险、缺失上下文、编辑建议和置信度都必须绑定 source refs、evidence refs、validation result refs 和 trace refs；证据不足时必须输出低置信度或 manual review。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、质量提示生成、事实边界检查、技术证据检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `AssetQualityHint` 或等价质量提示对象。
  - `SuggestionRef`
  - `AssetSource`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 质量提示可展示给用户。
  - 用户可以编辑候选、确认归档、跳过、合并或请求人工校对。
  - 本 contract 不自动归档 `Asset`，不自动创建 `AssetVersion`。
- Retry / Fallback:
  - 目标 candidate / asset、source refs、evidence refs 或 owner 校验缺失时停止正常提示，返回失败或补充材料路径。
  - 事实边界不清、技术 evidence 不足、适用场景不明确或质量判断受裁剪影响时输出低置信度、建议用户编辑或进入 manual review。
  - 重试不得默认启用互联网检索、扩大到全量资产 / 知识库、把质量提示写成算法结论或自动归档正式资产。
- API State Mapping: 只定义状态语义，包括 `asset_quality_hint_available`、`asset_quality_hint_partial`、`asset_quality_hint_low_confidence`、`asset_quality_hint_validation_failed`、`manual_review_required` 和 `asset_edit_recommended`；不定义 endpoint 或 schema。
- Security Notes: 质量提示只使用当前 owner 的候选、资产、授权来源、可展示证据摘要和必要 trace id；不得暴露无权限来源正文、原始 Prompt、completion、provider payload 或隐私字段。
- Test Strategy: 使用 fixture 覆盖候选质量提示、既有 AssetVersion 质量提示、用户请求查看质量、报告 / 复盘 / Polish 新证据、用户事实边界不清、技术 evidence 缺失、适用场景不明确、与既有资产冲突、用户确认缺失、低质量建议编辑和不得自动归档 / 创建版本 / 创建 TrainingRecommendation。
- Open Questions: 资产质量算法、质量等级枚举、复用准备度评分、质量不足归档策略和正式展示规则仍待后续 Asset / API / UX 收敛，为 deferred_non_blocking。

### 3.3 P-ASSET-003 Asset Version Suggestion

- Contract ID: `P-ASSET-003`
- Name: Asset Version Suggestion
- Mode: `asset`
- Trigger:
  - 新 AssetCandidate 与既有 `Asset` 可能相关。
  - 用户编辑资产候选后请求保存为新版本。
  - 资产质量提示建议更新版本。
  - Report / Review / Polish 产生更好的表达或更准确事实。
  - 系统需要判断创建新 `Asset` 还是更新既有 `AssetVersion`。
- Goal: 对既有 `Asset` 生成版本更新建议；本 contract 只生成版本更新建议，不自动替换、覆盖或发布 `AssetVersion`。
- Required Inputs:
  - `OwnerRef`
  - Asset candidate refs 或 edited candidate content
  - existing Asset refs
  - existing AssetVersion refs
  - evidence refs
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - AssetQualityHint
  - AssetSource history
  - user confirmation history
  - related Weakness / Review items
  - `JobVersion`
  - `ResumeVersion`
  - RAG evidence
- Retrieval Sources:
  - 默认使用候选内容、既有 `Asset`、`AssetVersion` 和 evidence refs。
  - 条件读取 AssetSource history、相关 Weakness / Review、岗位 / 简历、RAG evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含候选内容、既有 Asset 当前版本摘要、版本历史摘要、差异点、证据、用户确认状态和输出 schema。
  - 不得默认塞入全部资产历史、全部报告、全部复盘或全部知识库。
  - 上下文过长时优先保留当前版本、候选差异、关键证据、用户确认内容和冲突点。
- Excluded Inputs:
  - 未确认事实作为新版本内容。
  - 自动替换、覆盖、发布或归档 `AssetVersion` 的写入动作。
  - 自动创建正式 `TrainingRecommendation` 或训练任务的写入动作。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 全量资产历史、全量报告、全量复盘、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Asset 公共 Output Schema。
  - `asset_version_suggestions`
  - 每个 suggestion 的 `suggestion_id`
  - 每个 suggestion 的 `target_asset_ref`
  - 每个 suggestion 的 `base_asset_version_ref`
  - 每个 suggestion 的 `candidate_ref`
  - 每个 suggestion 的 `suggested_action`
  - 每个 suggestion 的 `suggested_content_delta`
  - 每个 suggestion 的 `version_update_reason`
  - 每个 suggestion 的 `evidence_refs`
  - 每个 suggestion 的 `conflict_signals`
  - 每个 suggestion 的 `confidence`
  - 每个 suggestion 的 `user_confirmation_required`
  - `no_update_reasons`
  - `manual_review_required`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 版本建议必须基于候选内容、既有 `AssetVersion` 和 evidence。
  - 不得自动替换、覆盖或发布 `AssetVersion`。
  - 不得丢失既有资产可追溯来源。
  - 不得把未确认事实写入新版本。
  - `suggested_action` 必须是稳定枚举或等价描述，例如 `create_new_asset` / `create_new_version` / `merge_into_existing` / `keep_separate` / `manual_review` / `insufficient_evidence`。
  - 冲突证据必须进入 manual review。
  - 低置信度候选不得高置信建议覆盖既有 `AssetVersion`。
- Low Confidence Rules:
  - 既有 `AssetVersion` 缺失。
  - candidate evidence 不足。
  - 用户确认缺失。
  - 版本历史不完整。
  - 内容差异不清。
  - 与既有 `Asset` 冲突。
  - evidence 冲突。
  - 上下文裁剪影响版本判断。
- Evidence Requirements: 每条版本建议的候选、目标资产、基础版本、差异、版本更新原因、冲突信号、no update reason 和置信度必须绑定 source refs、evidence refs、validation result refs 和 trace refs；证据不足时必须输出 `insufficient_evidence` 或 `manual_review`。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、候选与既有版本对比、冲突检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `AssetVersionSuggestion` 或等价版本更新建议对象。
  - `AssetCandidate`
  - `AssetSource`
  - `UserConfirmationRef`
  - `SuggestionRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 版本更新建议必须由用户确认、编辑、跳过或人工校对。
  - 本 contract 不自动替换、覆盖或发布 `AssetVersion`。
  - 回流失败不得影响原始 `Asset` 或 `AssetVersion`。
- Retry / Fallback:
  - candidate、existing Asset、existing AssetVersion、evidence refs、Retrieval Planning 或 owner 校验缺失时停止正常建议，返回失败或补充材料路径。
  - 版本历史不完整、差异不清、证据冲突或用户确认缺失时输出低置信度、`insufficient_evidence` 或 manual review。
  - 重试不得默认启用互联网检索、扩大到全量资产历史、自动替换既有版本或自动发布新版本。
- API State Mapping: 只定义状态语义，包括 `asset_version_suggestion_available`、`asset_version_suggestion_partial`、`asset_version_suggestion_low_confidence`、`asset_version_suggestion_validation_failed`、`manual_review_required`、`insufficient_evidence` 和 `user_confirmation_required`；不定义 endpoint 或 schema。
- Security Notes: 版本建议只使用当前 owner 的候选、既有资产摘要、授权 evidence、用户确认记录和必要 trace id；不得暴露无权限来源正文、原始 Prompt、completion、provider payload 或隐私字段。
- Test Strategy: 使用 fixture 覆盖候选关联既有资产、用户编辑后保存为版本、质量提示建议更新、Report / Review / Polish 更好表达、创建新资产建议、创建新版本建议、合并建议、保持独立建议、证据冲突 manual review、低置信候选不得覆盖版本和不得自动替换 / 覆盖 / 发布 AssetVersion。
- Open Questions: 资产版本合并算法、版本替代规则、合并后字段保留策略、资产归档策略、资产可复用评分和正式 AssetVersion API 字段仍待后续 Asset / API / UX 收敛，为 deferred_non_blocking。

### 3.4 Asset Contract 关系

- `P-ASSET-001` 从 Polish / Report / Review / Weakness 等上游提炼资产候选。
- `P-ASSET-002` 对资产候选或既有资产生成质量提示。
- `P-ASSET-003` 对候选与既有 `Asset` / `AssetVersion` 生成版本更新建议。
- Asset contracts 可以消费 Weakness / Review / Report / Polish 输出，但不得重新生成这些上游结果。
- Asset contracts 不得直接创建 `TrainingRecommendation`。
- Asset contracts 不得自动归档 `Asset` 或替换 `AssetVersion`。
- Asset contracts 不实现资产质量规则、资产归档策略、资产版本合并策略或训练优先级复杂算法；这些为 deferred_non_blocking，且不得绕过用户确认发布正式 AssetVersion。
- Training contracts 仍保持 Stub，等待后续阶段授权填充。
