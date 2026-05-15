---
title: WEAKNESS_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/weakness-contracts
---

# WEAKNESS_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件不关闭 `F4_TECH_DESIGN` UNKNOWN。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 当前状态

本文件承载主 catalog 中 `P-WEAKNESS-001` 至 `P-WEAKNESS-004` 的详细 contract 正文。Weakness contracts 当前为 Draft，仍属于 F4 Prompt / AI 子任务 contract 草案，不代表实现完成，不代表 `AIFI-PROMPT-001` DONE，也不关闭任何 `F4_TECH_DESIGN` UNKNOWN。

## 3. Weakness Contract 细则

### 3.0 Weakness 公共字段与边界

#### Weakness 公共职责

Weakness contracts 只负责从 Job Match、Polish、Pressure、Report、Review 等上游输出中提炼薄弱项候选，生成薄弱项合并建议，判断薄弱项严重度提示，并生成薄弱项状态更新建议。Weakness contracts 不负责自动创建正式 `TrainingRecommendation`、自动归档 `Asset`、生成完整训练计划、替代用户确认、关闭薄弱项合并算法 UNKNOWN、关闭严重度规则 UNKNOWN、关闭状态流转规则 UNKNOWN 或关闭训练优先级 UNKNOWN。

#### Weakness 公共上游输入

Weakness contracts 可以消费 Job Match weakness candidates、Polish weakness candidates、Pressure risk signals / answer quality / session score、Report risk items / section score explanations、Mock / Real Interview Review、Review items、existing Weakness、WeaknessEvidence、user confirmation refs、low confidence flags、evidence refs、trace refs、JobVersion / ResumeVersion、RAG evidence 和公共参考材料。上述输入必须按任务最小必要装配，不得默认塞入全部简历、全部岗位、全部历史会话、全部报告、全部复盘、全部知识库或全部资产。

#### Weakness 公共检索边界

- `JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG。
- Job Match / Polish / Pressure / Report / Review outputs 是结构化上游，不是 RAG。
- 既有 Weakness 和 WeaknessEvidence 是条件检索来源，不是默认全量上下文。
- RAG / 知识库可用于技术弱项解释或证据增强，但不是 Weakness MVP 硬依赖。
- 互联网检索不是 MVP 默认强依赖，不得默认启用。
- 条件检索必须经过 `P-SHARED-002` Retrieval Planning。
- 证据不足、来源不可用、输入冲突或上下文裁剪影响判断时，必须进入 low confidence 或 manual check。

#### Weakness 公共输出边界

Weakness 输出可以保存为 Weakness candidate、merge suggestion、severity hint、status update suggestion、WeaknessEvidence、validation result、low confidence flag、evidence refs、trace refs 和 audit event。Weakness 输出不得直接写入正式 `TrainingRecommendation`、正式 `Asset`、训练任务、新的 Report 或新的 Review。正式 Weakness 的创建、合并和状态更新必须保留用户确认、编辑、跳过或合并路径；若后续产品允许自动创建候选，也必须保持候选态和证据引用。

#### Weakness 公共 Output Schema

`P-WEAKNESS-001` 至 `P-WEAKNESS-004` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `weakness_ref` | 否 | ref | 既有或新建候选 Weakness 引用 |
| `weakness_candidate_refs` | 否 | ref[] | 薄弱项候选引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的证据 |
| `weakness_evidence_refs` | 否 | ref[] | WeaknessEvidence 引用 |
| `review_item_refs` | 否 | ref[] | 复盘项引用 |
| `report_refs` | 否 | ref[] | 报告引用 |
| `polish_refs` | 否 | ref[] | Polish 来源引用 |
| `pressure_refs` | 否 | ref[] | Pressure 来源引用 |
| `job_match_refs` | 否 | ref[] | Job Match 来源引用 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记 |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能进入正式对象 |

`next_recommended_actions` 允许值至少包括 `confirm_weakness_candidate`、`edit_weakness_candidate`、`skip_weakness_candidate`、`merge_weakness_candidate`、`request_more_evidence`、`mark_for_training`、`enter_polish_mode`、`enter_pressure_mode` 和 `manual_check_required`。这些 action 只是建议动作或用户确认入口，不得直接写入正式 `TrainingRecommendation` 或 `Asset`；需要用户确认的 action 必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。

#### Weakness 公共校验与失败边界

- 必须引用 `P-SHARED-001` Context Assembly、`P-SHARED-002` Retrieval Planning、`P-SHARED-003` Output Validation、`P-SHARED-004` Low Confidence Classification 和 `P-SHARED-005` Evidence Binding 中与当前任务相关的规则。
- 必须保留 validation、Low Confidence、EvidenceRef、TraceRef 和 AuditEvent 交接。
- 不得生成完整生产 Prompt 文案、原始 Prompt、completion 或 provider payload。
- 不得定义 API endpoint、物理数据库 schema、LLM provider、模型参数、向量数据库、embedding 模型或搜索服务。
- 不得自动创建正式 Weakness、正式 Asset、正式 TrainingRecommendation 或训练任务。
- 不得关闭薄弱项合并算法、严重度规则、状态流转规则或训练优先级 UNKNOWN。

### 3.1 P-WEAKNESS-001 Weakness Extraction

- Contract ID: `P-WEAKNESS-001`
- Name: Weakness Extraction
- Mode: `weakness`
- Trigger:
  - Job Match 产生 weakness candidate。
  - Polish 产生 weakness candidate。
  - Pressure / Report / Review 暴露明显弱项。
  - Review Item Extraction 产生相关 weakness candidate refs。
  - 用户请求提炼薄弱项。
  - 系统需要把多来源证据收敛为候选 Weakness。
- Goal: 从 Job Match、Polish、Pressure、Report、Review 等上游结果中提炼薄弱项候选；本 contract 只提炼候选，不绕过用户确认创建正式 Weakness。
- Required Inputs:
  - `OwnerRef`
  - 至少一个 source artifact：Job Match / Polish / Pressure / Report / Review 输出之一。
  - evidence refs
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - existing Weakness
  - WeaknessEvidence
  - JobVersion
  - ResumeVersion
  - user confirmations
  - low confidence flags
  - RAG evidence
- Retrieval Sources:
  - 默认使用显式 source artifact 和 evidence refs。
  - 条件读取既有 Weakness、WeaknessEvidence、Job Match / Polish / Pressure / Report / Review 结构化摘要。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
  - 无既有 Weakness 时仍可生成候选，但必须保留候选态。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 source artifact summary、evidence refs、低置信度、source availability、已有 Weakness 摘要和输出 schema。
  - 不得默认塞入全部历史会话、全部报告、全部复盘或全部知识库。
  - 上下文过长时优先保留高证据强度来源、重复信号、用户确认记录和当前候选依据。
- Excluded Inputs:
  - 全部简历、全部岗位、全部历史会话、全部报告、全部复盘、全部知识库和默认互联网检索结果。
  - 单次轻微失误作为稳定能力缺陷的确定事实。
  - 岗位匹配缺口作为用户能力缺陷的直接替代。
  - 未确认候选对象作为正式 Weakness 事实。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 正式 `TrainingRecommendation`、正式 `Asset`、训练任务、新 Report、新 Review、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Weakness 公共 Output Schema。
  - `weakness_candidates`
  - 每个候选的 `candidate_id`
  - 每个候选的 `candidate_status`
  - 每个候选的 `title`
  - 每个候选的 `description`
  - 每个候选的 `source_type`
  - 每个候选的 `source_refs`
  - 每个候选的 `evidence_refs`
  - 每个候选的 `severity_hint`
  - 每个候选的 `confidence`
  - 每个候选的 `related_job_requirements`
  - 每个候选的 `related_resume_modules`
  - 每个候选的 `related_review_item_refs`
  - 每个候选的 `merge_candidate_refs`
  - 每个候选的 `suggested_training_direction`
  - `extraction_summary`
  - `candidate_ordering`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 每个候选必须绑定 source refs 和 evidence refs。
  - 不得把单次轻微失误直接包装为稳定能力缺陷，除非标记低置信度。
  - 不得把岗位匹配缺口直接包装为用户能力缺陷。
  - 不得虚构用户未表现出的薄弱项。
  - 不得静默覆盖既有 Weakness。
  - 如可能与既有 Weakness 重复，应输出 merge candidate refs。
  - `severity_hint` 只是提示，不冻结严重度算法。
  - `suggested_training_direction` 只是训练方向，不等同正式训练任务。
- Low Confidence Rules:
  - 证据不足。
  - source artifact 低置信度。
  - 单轮证据不足以判断稳定弱项。
  - 与既有 Weakness 冲突。
  - source unavailable。
  - 用户输入过短。
  - 事实和推测混杂。
  - 上下文裁剪影响候选归因。
- Evidence Requirements: 每个候选的标题、描述、来源类型、严重度提示、训练方向和合并候选必须绑定 source refs、evidence refs、validation result refs 和 trace refs；缺少 evidence 时不得生成高置信候选。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、薄弱项候选生成、重复或合并线索检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `Weakness` candidate 或等价待确认对象。
  - `WeaknessEvidence`
  - `UserConfirmationRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 默认需要用户确认后才能成为正式 Weakness。
  - 用户可以确认、编辑、跳过、合并或要求重新生成。
  - 用户确认动作必须形成 `UserConfirmationRef` 或等价记录。
- Retry / Fallback:
  - `OwnerRef`、source artifact 或 evidence refs 缺失时停止正常提炼，返回失败或补充材料路径。
  - 证据不足、来源不可用、上下游冲突或候选重复不确定时可保存低置信度候选、要求用户确认或进入 manual check。
  - 重试不得默认启用互联网检索、扩大到全量历史上下文、把岗位缺口包装成能力缺陷或创建正式 Weakness。
- API State Mapping: 只定义状态语义，包括 `weakness_extraction_available`、`weakness_extraction_partial`、`weakness_extraction_low_confidence`、`weakness_extraction_validation_failed`、`user_confirmation_required` 和 `merge_candidate_detected`；不定义 endpoint 或 schema。
- Security Notes: 薄弱项提炼只使用当前 owner 的授权来源、摘要、证据和可展示 evidence summary；不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖 Job Match 候选、Polish 候选、Pressure 风险信号、Report risk item、Review item、无既有 Weakness、重复候选、source unavailable、单次轻微失误低置信度、岗位缺口不转能力缺陷、用户确认 / 编辑 / 跳过 / 合并和不得自动创建正式 Weakness。
- Open Questions: 薄弱项合并算法、严重度规则、状态生命周期、训练优先级和正式 Weakness API 字段仍待后续 Weakness / Training / API / UX 收敛，不在本 contract 关闭。

### 3.2 P-WEAKNESS-002 Weakness Merge Suggestion

- Contract ID: `P-WEAKNESS-002`
- Name: Weakness Merge Suggestion
- Mode: `weakness`
- Trigger:
  - `P-WEAKNESS-001` 产生候选后。
  - 新候选与既有 Weakness 存在相似 title、source、evidence 或训练方向。
  - 用户请求整理薄弱项。
  - 系统需要避免重复 Weakness 膨胀。
- Goal: 判断新候选 Weakness 是否与既有 Weakness 重复、相近、可合并或应保持独立，并生成合并建议；本 contract 只生成合并建议，不自动合并或覆盖既有 Weakness。
- Required Inputs:
  - `OwnerRef`
  - weakness candidate refs
  - existing Weakness refs
  - evidence refs
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - WeaknessEvidence history
  - review item refs
  - training history
  - user confirmation history
  - low confidence flags
- Retrieval Sources:
  - 默认使用候选 Weakness、既有 Weakness 和 evidence。
  - 条件读取 WeaknessEvidence、历史训练结果、用户确认记录和相关 review items。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含候选摘要、既有 Weakness 摘要、evidence、来源、历史确认状态和输出 schema。
  - 不得默认塞入全部历史训练或全部复盘。
  - 上下文过长时优先保留相似候选、强证据来源、历史确认和冲突信息。
- Excluded Inputs:
  - 全量历史训练、全量复盘、全量知识库、全量资产和默认互联网检索结果。
  - 无 evidence 支撑的相似度判断。
  - 覆盖既有 Weakness 标题、描述、证据或状态的写入动作。
  - 自动合并、自动删除 Weakness 或自动创建 TrainingRecommendation 的动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Weakness 公共 Output Schema。
  - `merge_suggestions`
  - 每个 suggestion 的 `suggestion_id`
  - 每个 suggestion 的 `candidate_ref`
  - 每个 suggestion 的 `target_weakness_ref`
  - 每个 suggestion 的 `merge_recommendation`
  - 每个 suggestion 的 `merge_reason`
  - 每个 suggestion 的 `similarity_signals`
  - 每个 suggestion 的 `conflict_signals`
  - 每个 suggestion 的 `evidence_refs`
  - 每个 suggestion 的 `confidence`
  - 每个 suggestion 的 `user_confirmation_required`
  - `no_merge_reasons`
  - `manual_review_required`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 合并建议必须基于候选、既有 Weakness 和 evidence。
  - 不得自动合并。
  - 不得覆盖既有 Weakness 标题、描述、证据或状态。
  - 不得因名称相似就强制合并。
  - 若证据冲突，应建议人工确认。
  - low confidence candidate 不得高置信合并。
  - `merge_recommendation` 必须是稳定枚举或等价描述，例如 `merge` / `keep_separate` / `manual_review` / `insufficient_evidence`。
- Low Confidence Rules:
  - existing Weakness 缺失。
  - candidate evidence 不足。
  - similarity signals 弱。
  - evidence 冲突。
  - 历史确认状态缺失。
  - 用户输入不足。
  - 合并会丢失重要语义。
  - 上下文裁剪影响相似度判断。
- Evidence Requirements: 每条合并建议的 candidate、target Weakness、merge reason、similarity signals、conflict signals 和 confidence 必须绑定 source refs、evidence refs、validation result refs 和 trace refs；证据不足时必须输出 `insufficient_evidence` 或 `manual_review`。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、候选和既有 Weakness 对比、冲突检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `WeaknessMergeSuggestion` 或等价合并建议对象。
  - `WeaknessEvidence`
  - `UserConfirmationRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 合并建议必须由用户确认、编辑、跳过或人工校对。
  - 回流失败不得影响原始 candidate 或既有 Weakness。
  - 本 contract 不自动合并或删除 Weakness。
- Retry / Fallback:
  - 候选、既有 Weakness、owner 校验或 evidence 缺失时停止正常合并建议，返回补充材料路径或 `insufficient_evidence`。
  - 相似度弱、证据冲突或历史确认缺失时输出 manual review，不覆盖任何既有对象。
  - 重试不得默认启用互联网检索、扩大到全量历史训练或自动合并。
- API State Mapping: 只定义状态语义，包括 `weakness_merge_suggestion_available`、`weakness_merge_suggestion_partial`、`weakness_merge_suggestion_low_confidence`、`weakness_merge_suggestion_validation_failed`、`manual_review_required` 和 `insufficient_evidence`；不定义 endpoint 或 schema。
- Security Notes: 合并建议只使用当前 owner 的候选、既有 Weakness 摘要、授权 evidence 和用户确认记录；不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖可合并候选、应保持独立候选、名称相似但证据不同、低置信候选、evidence 冲突、缺少 existing Weakness、用户确认 / 编辑 / 跳过 / 人工校对和不得自动合并 / 覆盖 / 删除 Weakness。
- Open Questions: 薄弱项合并算法、相似度阈值、合并后字段保留策略和正式 Weakness merge API 字段仍待后续 Weakness / API / UX 收敛，不在本 contract 关闭。

### 3.3 P-WEAKNESS-003 Weakness Severity Assessment

- Contract ID: `P-WEAKNESS-003`
- Name: Weakness Severity Assessment
- Mode: `weakness`
- Trigger:
  - `P-WEAKNESS-001` 提炼候选后。
  - `P-WEAKNESS-002` 合并建议后。
  - 既有 Weakness 新增证据后。
  - 用户请求查看薄弱项优先级。
  - 系统需要为 TrainingRecommendation 提供上游提示。
- Goal: 评估 Weakness 或候选 Weakness 的严重度提示；本 contract 不冻结严重度算法，只生成基于证据的 severity hint 和解释。
- Required Inputs:
  - `OwnerRef`
  - Weakness 或 weakness candidate refs
  - evidence refs
  - source artifact refs
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - historical WeaknessEvidence
  - repeated review items
  - training history
  - recent scores
  - user confirmation history
  - Job Match / Report / Review summaries
- Retrieval Sources:
  - 默认使用当前 Weakness / candidate 和 evidence。
  - 条件读取历史证据、重复出现次数、训练历史、分数趋势、复盘项。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 Weakness 摘要、证据、来源、重复信号、最近表现和输出 schema。
  - 不得默认塞入全部历史训练、全部报告或全部复盘。
  - 上下文过长时优先保留强证据、多次重复、最近性和用户确认状态。
- Excluded Inputs:
  - 全量历史训练、全量报告、全量复盘、全量知识库和默认互联网检索结果。
  - 未绑定 evidence 的重复频次、影响范围或训练优先级。
  - 将岗位不匹配包装为高严重度能力缺陷的判断。
  - 自动创建正式 TrainingRecommendation、训练任务、正式 Asset 或状态更新动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Weakness 公共 Output Schema。
  - `severity_assessments`
  - 每个 assessment 的 `weakness_ref`
  - 每个 assessment 的 `severity_hint`
  - 每个 assessment 的 `severity_reason`
  - 每个 assessment 的 `evidence_refs`
  - 每个 assessment 的 `recency_signals`
  - 每个 assessment 的 `frequency_signals`
  - 每个 assessment 的 `impact_signals`
  - 每个 assessment 的 `training_priority_hint`
  - 每个 assessment 的 `confidence`
  - `severity_unknown_flags`
  - `manual_review_required`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 严重度必须绑定 evidence refs。
  - `severity_hint` 只是提示，不冻结严重度算法。
  - 不得把单次低质量回答自动判为高严重度。
  - 不得虚构重复频次或影响范围。
  - 不得把岗位不匹配直接包装为高严重度能力缺陷。
  - `training_priority_hint` 只是训练上游提示，不等同正式训练计划。
  - 证据不足时必须低置信度或 manual review。
- Low Confidence Rules:
  - evidence 不足。
  - 历史证据缺失。
  - 频次信号缺失。
  - 最近性不清。
  - 影响范围不明。
  - Weakness 与候选状态不清。
  - 证据冲突。
  - 上下文裁剪影响严重度判断。
- Evidence Requirements: 每个 severity hint、severity reason、recency signal、frequency signal、impact signal 和 training priority hint 必须绑定 source refs、evidence refs、validation result refs 和 trace refs；证据不足时必须输出低置信度或 manual review。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、严重度提示生成、证据强度检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `WeaknessSeverityAssessment` 或等价严重度评估对象。
  - `WeaknessEvidence`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 严重度提示可展示给用户。
  - 用户可以确认、调整、请求人工校对或进入训练建议。
  - 本 contract 不自动创建 TrainingRecommendation。
- Retry / Fallback:
  - Weakness / candidate、source artifact、owner 校验或 evidence 缺失时停止正常评估，返回失败或补充材料路径。
  - 频次、最近性、影响范围或证据冲突不足以支持判断时输出 low confidence 或 manual review。
  - 重试不得默认启用互联网检索、扩大到全量历史上下文、虚构严重度依据或生成正式训练计划。
- API State Mapping: 只定义状态语义，包括 `weakness_severity_available`、`weakness_severity_partial`、`weakness_severity_low_confidence`、`weakness_severity_validation_failed`、`severity_unknown` 和 `manual_review_required`；不定义 endpoint 或 schema。
- Security Notes: 严重度提示只使用当前 owner 的 Weakness / candidate、授权 evidence 和可展示证据摘要；不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖候选严重度、既有 Weakness 严重度、新增证据后重评、重复信号、最近性强、频次缺失、单次低质量回答低置信度、岗位不匹配不转高严重度、训练优先级只是 hint 和不得创建 TrainingRecommendation。
- Open Questions: 严重度算法、severity 枚举、训练优先级映射、状态生命周期和正式展示规则仍待后续 Weakness / Training / API / UX 收敛，不在本 contract 关闭。

### 3.4 P-WEAKNESS-004 Weakness Status Update Suggestion

- Contract ID: `P-WEAKNESS-004`
- Name: Weakness Status Update Suggestion
- Mode: `weakness`
- Trigger:
  - 新增 WeaknessEvidence。
  - 用户完成训练或复盘后。
  - 新报告 / 新复盘显示薄弱项改善或恶化。
  - 用户请求更新薄弱项状态。
  - 系统需要判断薄弱项是否仍活跃、改善、待观察或需要人工校对。
- Goal: 基于新增证据、训练历史、复盘结果、用户确认和最近表现生成 Weakness 状态更新建议；本 contract 只生成状态更新建议，不自动变更正式 Weakness 状态。
- Required Inputs:
  - `OwnerRef`
  - existing Weakness refs
  - WeaknessEvidence refs
  - recent source artifact refs
  - current Weakness status
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - Training history
  - recent review items
  - recent scores
  - user confirmation history
  - status update history
  - low confidence flags
- Retrieval Sources:
  - 默认使用 existing Weakness、current status、WeaknessEvidence 和 recent source artifacts。
  - 条件读取训练历史、复盘项、评分趋势、用户确认和状态更新历史。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前 Weakness 状态、证据、最近表现、训练 / 复盘结果、用户确认状态和输出 schema。
  - 不得默认塞入全部历史训练、全部报告或全部复盘。
  - 上下文过长时优先保留当前状态、最近证据、改善 / 恶化信号和用户确认记录。
- Excluded Inputs:
  - 全量历史训练、全量报告、全量复盘、全量知识库和默认互联网检索结果。
  - 未经 evidence 支撑的改善、恶化或关闭判断。
  - 自动变更正式 Weakness 状态、自动创建 TrainingRecommendation、自动归档 Asset 或删除 Weakness 的动作。
  - 单次好表现作为关闭 Weakness 的充分依据，或单次差表现作为升级状态的充分依据。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Weakness 公共 Output Schema。
  - `status_update_suggestions`
  - 每个 suggestion 的 `weakness_ref`
  - 每个 suggestion 的 `current_status`
  - 每个 suggestion 的 `suggested_status`
  - 每个 suggestion 的 `status_update_reason`
  - 每个 suggestion 的 `supporting_evidence_refs`
  - 每个 suggestion 的 `conflicting_evidence_refs`
  - 每个 suggestion 的 `confidence`
  - 每个 suggestion 的 `user_confirmation_required`
  - `manual_review_required`
  - `status_unknown_flags`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 状态更新建议必须基于 evidence、训练历史、复盘结果或用户确认。
  - 不得自动变更正式 Weakness 状态。
  - 不得因单次好表现直接关闭 Weakness。
  - 不得因单次差表现直接升级状态。
  - `suggested_status` 必须使用稳定枚举或等价描述。
  - 证据冲突时必须进入 manual review。
  - 不得生成正式 TrainingRecommendation。
- Low Confidence Rules:
  - current status 缺失。
  - WeaknessEvidence 不足。
  - recent performance 不足。
  - training history 缺失。
  - 证据冲突。
  - 用户确认缺失。
  - 状态流转规则未冻结。
  - 上下文裁剪影响状态判断。
- Evidence Requirements: 每条状态更新建议的 current status、suggested status、更新原因、supporting evidence、conflicting evidence 和 confidence 必须绑定 source refs、evidence refs、validation result refs 和 trace refs；证据冲突或状态规则未冻结时必须输出 manual review 或 status unknown flag。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、状态更新建议生成、冲突证据检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `WeaknessStatusUpdateSuggestion` 或等价状态更新建议对象。
  - `WeaknessEvidence`
  - `UserConfirmationRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 状态更新建议必须由用户确认、编辑、跳过或人工校对。
  - 本 contract 不自动更新正式 Weakness 状态。
  - 回流失败不得影响原始 Weakness 或 evidence。
- Retry / Fallback:
  - existing Weakness、current status、WeaknessEvidence、owner 校验或 recent source artifact 缺失时停止正常建议，返回失败或补充材料路径。
  - 最近表现不足、训练历史缺失、证据冲突或状态流转规则未冻结时输出 low confidence、status unknown flag 或 manual review。
  - 重试不得默认启用互联网检索、自动关闭 / 升级 Weakness 状态或创建正式 TrainingRecommendation。
- API State Mapping: 只定义状态语义，包括 `weakness_status_suggestion_available`、`weakness_status_suggestion_partial`、`weakness_status_suggestion_low_confidence`、`weakness_status_suggestion_validation_failed`、`status_rule_unknown` 和 `manual_review_required`；不定义 endpoint 或 schema。
- Security Notes: 状态更新建议只使用当前 owner 的 existing Weakness、WeaknessEvidence、最近来源、训练 / 复盘摘要和用户确认记录；不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖新增证据、训练后改善、复盘后恶化、用户请求更新、current status 缺失、单次好表现不得关闭、单次差表现不得升级、证据冲突 manual review、用户确认 / 编辑 / 跳过和不得自动更新正式 Weakness 状态。
- Open Questions: 状态流转规则、自动消减规则、关闭阈值、训练结果映射和正式 Weakness 状态 API 字段仍待后续 Weakness / Training / API / UX 收敛，不在本 contract 关闭。

### 3.5 Weakness Contract 关系

- `P-WEAKNESS-001` 从 Job Match、Polish、Pressure、Report、Review 等多来源上游提炼薄弱项候选。
- `P-WEAKNESS-002` 对候选与既有 Weakness 生成合并建议。
- `P-WEAKNESS-003` 对 Weakness 或候选生成严重度提示。
- `P-WEAKNESS-004` 对既有 Weakness 生成状态更新建议。
- Weakness contracts 可以消费 Review / Report / Polish / Pressure / Job Match 输出，但不得重新生成这些上游结果。
- Weakness contracts 不得直接创建 TrainingRecommendation。
- Weakness contracts 不得自动归档 Asset。
- Weakness contracts 不得关闭合并算法、严重度规则、状态流转规则或训练优先级 UNKNOWN。
- Asset / Training contracts 仍保持 Stub，等待后续阶段授权填充。
