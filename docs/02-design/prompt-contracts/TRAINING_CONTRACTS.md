---
title: TRAINING_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/training-contracts
---

# TRAINING_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得自行改变 contract ID、名称、目标或状态；状态以主 catalog 为准。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件不关闭 `F4_TECH_DESIGN` UNKNOWN。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 当前状态

Training contracts 已按主 catalog 更新为 Draft。本文只承载 `P-TRAINING-001` 至 `P-TRAINING-003` 的详细 contract 正文，不新增未登记 ID，不改变 contract ID、名称、目标或状态。

### 2.1 Catalog 摘要

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-TRAINING-001` | Training Recommendation | 生成训练建议 | Draft |
| `P-TRAINING-002` | Training Priority Ranking | 训练建议排序 | Draft |
| `P-TRAINING-003` | Training Result Review | 训练结果复盘 | Draft |

## 3. Training Contract 细则

### 3.0 Training 公共字段与边界

#### Training 公共职责

Training contracts 只负责生成训练建议、对训练建议进行优先级排序，以及对训练结果进行复盘。Training contracts 不负责自动执行训练任务、自动更新正式 Weakness 状态、自动归档正式 Asset、自动创建正式 AssetVersion、自动关闭薄弱项、自动关闭训练优先级算法 UNKNOWN、自动关闭训练结果评估规则 UNKNOWN、自动关闭弱项自动消减规则 UNKNOWN、自动关闭资产自动沉淀规则 UNKNOWN，也不替代用户确认。

#### Training 公共上游输入

Training contracts 可以消费 Weakness candidates、confirmed Weakness、WeaknessSeverityAssessment、WeaknessStatusUpdateSuggestion、Review items、Mock / Real Interview Review、Report section explanations、Risk wording、Pressure session score、Polish diagnosis / loss points / next round suggestions、Asset candidates、Asset quality hints、Asset version suggestions、confirmed AssetVersion、Training history、low confidence flags、evidence refs、trace refs、JobVersion / ResumeVersion、UserConfirmationRef、RAG evidence 和公共参考材料。上述输入必须按任务最小必要装配，不得默认塞入全部简历、全部岗位、全部历史会话、全部报告、全部复盘、全部知识库、全部资产、全部薄弱项或全部训练历史。

#### Training 公共检索边界

- `JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG。
- Weakness / Asset / Review / Report / Polish / Pressure outputs 是结构化上游，不是 RAG。
- 既有 `TrainingRecommendation`、`TrainingTask`、`TrainingSession` 和 `TrainingResult` 是条件检索来源，不是默认全量上下文。
- RAG / 知识库可用于训练素材、技术解释和任务建议增强，但不是 Training MVP 硬依赖。
- 互联网检索不是 MVP 默认强依赖，不得默认启用。
- 条件检索必须经过 `P-SHARED-002` Retrieval Planning。
- 证据不足、来源不可用、输入冲突或上下文裁剪影响判断时，必须进入 low confidence 或 manual check。

#### Training 公共输出边界

Training 输出可以保存为 training recommendation、training priority ranking、training result review、TrainingTask / TrainingSession 的初始化建议、Weakness status update suggestion 的上游输入、Asset candidate 的上游输入、validation result、low confidence flag、evidence refs、trace refs 和 audit event。Training 输出不得直接写入正式 Weakness 状态、正式 Asset、正式 AssetVersion、新的 Report 或新的 Review。

训练建议、训练任务创建、结果复盘、弱项状态影响和资产候选沉淀必须保留用户确认、编辑、跳过或人工校对路径。`P-TRAINING-001` 生成的是训练建议候选或建议入口，不自动创建正式 `TrainingRecommendation` 或 `TrainingTask`；`P-TRAINING-003` 的回流输出必须进入候选态或建议态。

#### Training 公共 Output Schema

`P-TRAINING-001` 至 `P-TRAINING-003` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `training_recommendation_refs` | 否 | ref[] | 训练建议引用 |
| `training_task_refs` | 否 | ref[] | 训练任务或训练会话引用 |
| `training_result_refs` | 否 | ref[] | 训练结果引用 |
| `candidate_refs` | 否 | ref[] | 通用候选引用，承接 `CandidateRef` |
| `suggestion_refs` | 否 | ref[] | 通用建议引用，承接 `SuggestionRef` |
| `weakness_refs` | 否 | ref[] | Weakness 或 WeaknessCandidate 引用 |
| `asset_refs` | 否 | ref[] | Asset 或 AssetCandidate 引用 |
| `review_item_refs` | 否 | ref[] | 复盘项引用 |
| `report_refs` | 否 | ref[] | 报告引用 |
| `polish_refs` | 否 | ref[] | Polish 来源引用 |
| `pressure_refs` | 否 | ref[] | Pressure 来源引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的证据 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记 |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能进入正式对象 |

`next_recommended_actions` 允许值至少包括 `confirm_training_recommendation`、`edit_training_recommendation`、`skip_training_recommendation`、`start_training_task`、`rank_training_recommendations`、`review_training_result`、`mark_weakness_status_update_candidate`、`mark_asset_candidate`、`enter_polish_mode`、`enter_pressure_mode`、`request_more_evidence` 和 `manual_check_required`。这些 action 只是建议动作或用户确认入口，不得直接写入正式 Weakness、Asset 或 AssetVersion；需要用户确认的 action 必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。

#### Training 公共校验与失败边界

- 必须引用 `P-SHARED-001` Context Assembly、`P-SHARED-002` Retrieval Planning、`P-SHARED-003` Output Validation、`P-SHARED-004` Low Confidence Classification 和 `P-SHARED-005` Evidence Binding 中与当前任务相关的规则。
- 必须保留 validation、Low Confidence、EvidenceRef、TraceRef、CandidateRef、SuggestionRef、UserConfirmationRef 和 AuditEvent 交接。
- 不得生成完整生产 Prompt 文案、原始 Prompt、completion 或 provider payload。
- 不得定义 API endpoint、物理数据库 schema、LLM provider、模型参数、向量数据库、embedding 模型或搜索服务。
- 不得自动创建正式 `TrainingRecommendation`、自动创建 `TrainingTask`、自动更新正式 Weakness 状态、自动归档 Asset 或自动发布 AssetVersion。
- 不得关闭训练优先级算法、训练结果评估规则、弱项自动消减规则或资产自动沉淀规则 UNKNOWN。

### 3.1 P-TRAINING-001 Training Recommendation

- Contract ID: `P-TRAINING-001`
- Name: Training Recommendation
- Mode: `training`
- Trigger:
  - Weakness severity assessment 生成后。
  - Review item 提示需要训练。
  - Report / Risk wording 暴露明显风险。
  - Polish / Pressure 表现反复暴露缺口。
  - Asset quality hint 建议补充表达或案例。
  - 用户请求“下一步怎么练”。
  - 系统需要生成训练建议候选。
- Goal: 基于 Weakness、Asset、Review、Report、Polish、Pressure 等上游结果生成训练建议；本 contract 只生成训练建议候选或建议入口，不自动创建训练任务，不自动更新 Weakness，不自动归档 Asset。
- Required Inputs:
  - `OwnerRef`
  - 至少一个 source artifact：Weakness / Review / Report / Polish / Pressure / Asset 输出之一。
  - evidence refs
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - confirmed Weakness
  - WeaknessSeverityAssessment
  - WeaknessStatusUpdateSuggestion
  - Asset candidates
  - Asset quality hints
  - confirmed AssetVersion
  - Training history
  - JobVersion
  - ResumeVersion
  - user preferences
  - low confidence flags
  - RAG evidence
- Retrieval Sources:
  - 默认使用显式 source artifact、evidence refs、weakness / review / asset 结构化摘要。
  - 条件读取既有 Weakness、Training history、AssetVersion、Job / Resume、Polish / Pressure / Report / Review 摘要和知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
  - 无训练历史或 RAG 时仍可生成基础训练建议，但必须保留低置信度和 evidence 边界。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 source artifact summary、weakness / asset / review signals、evidence refs、低置信度、source availability、用户目标和输出 schema。
  - 不得默认塞入全部历史会话、全部报告、全部复盘、全部资产、全部训练历史或全部知识库。
  - 上下文过长时优先保留高优先级 Weakness、强证据来源、重复出现信号、用户确认记录、当前训练目标和当前候选依据。
- Excluded Inputs:
  - 全量简历、全量岗位、全量历史会话、全量报告、全量复盘、全量资产、全量薄弱项、全量训练历史、全量知识库和默认互联网检索结果。
  - 未经 source refs 或 evidence refs 支撑的训练建议、训练收益、训练优先级或能力改善判断。
  - 自动创建 `TrainingTask`、自动更新正式 Weakness、自动归档 Asset、自动发布 AssetVersion 或自动创建新的 Report / Review 的写入动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Training 公共 Output Schema。
  - `training_recommendations`
  - 每个 recommendation 的 `recommendation_id`
  - 每个 recommendation 的 `recommendation_status`
  - 每个 recommendation 的 `title`
  - 每个 recommendation 的 `description`
  - 每个 recommendation 的 `training_type_hint`
  - 每个 recommendation 的 `target_weakness_refs`
  - 每个 recommendation 的 `target_asset_refs`
  - 每个 recommendation 的 `source_refs`
  - 每个 recommendation 的 `evidence_refs`
  - 每个 recommendation 的 `expected_outcome`
  - 每个 recommendation 的 `suggested_entry_mode`
  - 每个 recommendation 的 `suggested_task_shape`
  - 每个 recommendation 的 `estimated_effort_hint`
  - 每个 recommendation 的 `low_confidence_impact`
  - 每个 recommendation 的 `user_confirmation_required`
  - `recommendation_summary`
  - `candidate_ordering`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 每个训练建议必须绑定 source refs 和 evidence refs。
  - 不得把 severity hint 直接等同训练优先级。
  - 不得把 Asset `mark_for_training` 直接写成正式 `TrainingRecommendation`。
  - 不得自动创建训练任务。
  - 不得自动更新正式 Weakness 状态。
  - 不得自动归档 Asset。
  - `training_type_hint` 只是训练类型提示，不冻结训练分类算法。
  - `suggested_task_shape` 只是任务形态建议，不等同正式训练任务。
  - 证据不足时必须低置信度或 manual review。
- Low Confidence Rules:
  - evidence 不足。
  - Weakness severity 低置信度。
  - source artifact 低置信度。
  - 用户目标不清。
  - 训练历史缺失。
  - 与既有训练建议冲突。
  - source unavailable。
  - 技术训练需要知识 evidence 但 RAG 不可用。
  - 上下文裁剪影响建议归因。
- Evidence Requirements: 每个训练建议的标题、描述、目标弱项 / 资产、expected outcome、suggested entry mode、suggested task shape、low confidence impact 和 candidate ordering 必须绑定 source refs、evidence refs、validation result refs 和 trace refs；无法绑定时必须输出低置信度、要求补充 evidence 或进入 manual review。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、训练建议生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff、UserConfirmationRef 交接和 AuditEvent。
- Persistence Targets:
  - `TrainingRecommendation` candidate 或等价待确认对象。
  - `CandidateRef`
  - `SuggestionRef`
  - `UserConfirmationRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 默认需要用户确认后才能成为正式 `TrainingRecommendation` 或 `TrainingTask`。
  - 用户可以确认、编辑、跳过、排序、进入训练或要求重新生成。
  - 用户确认动作必须形成 `UserConfirmationRef` 或等价记录。
- Retry / Fallback:
  - `OwnerRef`、source artifact、evidence refs、Context Assembly 或 owner 校验缺失时停止正常建议，返回失败或补充材料路径。
  - 无训练历史、RAG 不可用或 source unavailable 时可生成基础建议，但必须标记缺失来源、低置信度和 manual check 入口。
  - 重试不得默认启用互联网检索、扩大到全量历史上下文、创建正式 TrainingRecommendation、创建 TrainingTask、更新 Weakness 或归档 Asset。
- API State Mapping: 只定义状态语义，包括 `training_recommendation_candidate_available`、`training_recommendation_partial`、`training_recommendation_low_confidence`、`training_recommendation_validation_failed`、`manual_review_required` 和 `user_confirmation_required`；不定义 endpoint 或 schema。
- Security Notes: 训练建议只使用当前 owner 的授权来源、可展示证据摘要和必要 trace id；不得暴露无权限来源正文、原始 Prompt、completion、provider payload 或隐私字段。
- Test Strategy: 使用 fixture 覆盖 Weakness severity 后建议、Review item 建议、Report risk 建议、Polish / Pressure 重复缺口、Asset quality hint 建议、用户请求下一步训练、无训练历史、RAG 不可用、source unavailable、与既有建议冲突、用户确认 / 编辑 / 跳过和不得自动创建 TrainingTask / 更新 Weakness / 归档 Asset。
- Open Questions: 训练分类算法、训练建议去重规则、建议质量评估、训练入口推荐阈值和正式 TrainingRecommendation API 字段仍待后续 Training / API / UX 收敛，不在本 contract 关闭。

### 3.2 P-TRAINING-002 Training Priority Ranking

- Contract ID: `P-TRAINING-002`
- Name: Training Priority Ranking
- Mode: `training`
- Trigger:
  - `P-TRAINING-001` 生成多个训练建议后。
  - 用户请求排序训练建议。
  - 新的 Weakness / Review / Asset / Report 证据出现后。
  - 系统需要决定推荐用户先练什么。
- Goal: 对训练建议进行优先级排序；本 contract 不冻结训练优先级算法，只生成基于证据、弱项严重度、复现频率、用户目标和可执行性的 priority hint。
- Required Inputs:
  - `OwnerRef`
  - Training recommendation refs
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
  - WeaknessSeverityAssessment
  - Review items
  - Report risk wording
  - Asset quality hints
  - Training history
  - user preferences
  - time budget
  - JobVersion
  - ResumeVersion
  - low confidence flags
- Retrieval Sources:
  - 默认使用训练建议、source refs 和 evidence refs。
  - 条件读取 Weakness severity、Review items、Report risk、Asset quality、训练历史、用户偏好和时间预算。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 recommendation summaries、weakness / asset / review signals、evidence、用户目标、时间预算和输出 schema。
  - 不得默认塞入全部训练历史、全部报告、全部资产或全部知识库。
  - 上下文过长时优先保留高证据强度训练建议、重复出现弱项、用户目标、训练成本和低置信度标记。
- Excluded Inputs:
  - 全量训练历史、全量报告、全量资产、全量知识库和默认互联网检索结果。
  - 未经 evidence 支撑的时间预算、训练收益、影响面、改善幅度或优先级理由。
  - 把 Weakness severity、单次低分或 Asset quality hint 直接等同于最高优先级的判断。
  - 自动创建 TrainingTask、自动更新正式 Weakness、自动归档 Asset 或发布 AssetVersion 的写入动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Training 公共 Output Schema。
  - `training_priority_ranking_id_candidate`
  - `ranked_recommendations`
  - 每个 ranked item 的 `recommendation_ref`
  - 每个 ranked item 的 `priority_rank`
  - 每个 ranked item 的 `priority_hint`
  - 每个 ranked item 的 `priority_reason`
  - 每个 ranked item 的 `evidence_refs`
  - 每个 ranked item 的 `impact_signals`
  - 每个 ranked item 的 `effort_signals`
  - 每个 ranked item 的 `confidence`
  - `ranking_unknown_flags`
  - `manual_review_required`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 排序必须基于训练建议、evidence、用户目标或弱项 / 资产 / 复盘信号。
  - `priority_hint` 只是提示，不冻结训练优先级算法。
  - 不得把 Weakness severity 直接等同训练优先级。
  - 不得把单次低分直接排到最高优先级，除非标记低置信度。
  - 不得虚构时间预算、训练收益或影响面。
  - 证据冲突时必须进入 manual review。
  - 排序结果不得自动创建训练任务。
- Low Confidence Rules:
  - 训练建议缺失。
  - evidence 不足。
  - Weakness severity 低置信度。
  - 用户目标或时间预算缺失。
  - impact / effort 信号不足。
  - 排序依据冲突。
  - 上下文裁剪影响排序判断。
- Evidence Requirements: 每个 ranked item 的 priority rank、priority hint、priority reason、impact signals、effort signals 和 confidence 必须绑定 recommendation refs、source refs、evidence refs、validation result refs 和 trace refs；证据冲突或优先级规则未冻结时必须输出 `ranking_unknown_flags` 或 `manual_review_required`。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、训练建议排序、冲突证据检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `TrainingPriorityRanking` 或等价排序建议对象。
  - `SuggestionRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 排序建议可展示给用户。
  - 用户可以调整排序、确认开始某项训练、跳过或进入 manual review。
  - 本 contract 不自动创建 TrainingTask。
- Retry / Fallback:
  - Training recommendation refs、source refs、evidence refs、Context Assembly 或 owner 校验缺失时停止正常排序，返回失败或补充材料路径。
  - 用户目标、时间预算、impact / effort 信号缺失时仍可输出低置信度排序草案，但必须保留 manual review 入口。
  - 重试不得默认启用互联网检索、虚构排序依据、创建 TrainingTask、更新 Weakness 或归档 Asset。
- API State Mapping: 只定义状态语义，包括 `training_priority_ranking_available`、`training_priority_ranking_partial`、`training_priority_ranking_low_confidence`、`training_priority_ranking_validation_failed`、`priority_rule_unknown` 和 `manual_review_required`；不定义 endpoint 或 schema。
- Security Notes: 排序只使用当前 owner 的训练建议、授权来源、可展示证据摘要、用户偏好和必要 trace id；不得暴露无权限来源正文、原始 Prompt、completion、provider payload 或隐私字段。
- Test Strategy: 使用 fixture 覆盖多个训练建议排序、用户请求排序、新 Weakness / Review / Asset / Report 证据、无用户目标、无时间预算、impact / effort 信号不足、证据冲突、单次低分不得高置信排首、severity 不等于 priority 和不得自动创建 TrainingTask。
- Open Questions: 训练优先级算法、impact / effort 计算、时间预算映射、排序刷新策略和正式 TrainingPriorityRanking API 字段仍待后续 Training / API / UX 收敛，不在本 contract 关闭。

### 3.3 P-TRAINING-003 Training Result Review

- Contract ID: `P-TRAINING-003`
- Name: Training Result Review
- Mode: `training`
- Trigger:
  - 用户完成 TrainingTask 或 TrainingSession。
  - 用户提交训练结果。
  - 系统检测到训练输出可复盘。
  - 用户请求查看训练效果。
  - 系统需要判断训练是否对弱项、资产或下一步建议产生影响。
- Goal: 对训练结果进行复盘，并为 Weakness 状态更新、Asset 候选和后续训练建议提供输入；本 contract 不自动更新正式 Weakness，不自动归档 Asset，不自动创建下一轮 `TrainingRecommendation`。
- Required Inputs:
  - `OwnerRef`
  - TrainingTask 或 TrainingSession refs
  - TrainingRecommendation refs
  - 用户训练输出或训练结果摘要
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
  - target Weakness refs
  - related Asset refs
  - previous TrainingResult
  - Review items
  - Report / Polish / Pressure summaries
  - user self assessment
  - RAG evidence
  - low confidence flags
- Retrieval Sources:
  - 默认使用训练任务、训练建议、用户训练输出、source refs 和 evidence refs。
  - 条件读取目标 Weakness、相关 Asset、历史 TrainingResult、Review items、Report / Polish / Pressure 摘要和知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 不默认启用互联网检索。
  - 无历史训练时仍可生成基础训练结果复盘。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 training task / session、training recommendation、用户训练输出、目标弱项 / 资产、evidence、低置信度和输出 schema。
  - 不得默认塞入全部训练历史、全部报告、全部资产或全部知识库。
  - 上下文过长时优先保留本次训练输入输出、目标、证据、用户自评和潜在回流项。
- Excluded Inputs:
  - 全量训练历史、全量报告、全量资产、全量知识库和默认互联网检索结果。
  - 未经训练输出、训练任务或 evidence 支撑的改善信号、能力提升、弱项消减或资产沉淀判断。
  - 自动更新正式 Weakness、自动归档 Asset、自动发布 AssetVersion、自动创建下一轮 TrainingRecommendation 或自动创建新的 Report / Review 的写入动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Training 公共 Output Schema。
  - `training_result_review_id_candidate`
  - `training_result_summary`
  - `target_weakness_refs`
  - `related_asset_refs`
  - `improvement_signals`
  - `remaining_gap_signals`
  - `weakness_status_update_candidate_refs`
  - `asset_candidate_refs`
  - `next_training_recommendation_candidate_refs`
  - `evidence_refs`
  - `low_confidence_summary`
  - `manual_review_required`
  - `next_recommended_actions`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 训练结果复盘必须基于用户训练输出、训练任务或训练建议。
  - 不得自动更新正式 Weakness 状态。
  - 不得自动归档 Asset。
  - 不得自动创建下一轮 `TrainingRecommendation`。
  - 不得虚构训练效果、改善幅度或能力提升。
  - improvement signals 必须绑定 evidence 或标记低置信度。
  - 若训练输出不足，必须要求补充或进入 low confidence。
  - 回流到 Weakness / Asset / Training 必须保留候选态或建议态。
- Low Confidence Rules:
  - 用户训练输出缺失。
  - TrainingTask / TrainingSession 缺失。
  - TrainingRecommendation 缺失。
  - evidence 不足。
  - 用户自评与输出冲突。
  - 无法判断改善信号。
  - 训练目标与输出不匹配。
  - 上下文裁剪影响结果归因。
- Evidence Requirements: 训练结果摘要、improvement signals、remaining gap signals、弱项状态更新候选、资产候选、下一步训练建议候选和 low confidence summary 必须绑定 source refs、evidence refs、validation result refs 和 trace refs；训练输出不足、证据冲突或归因受裁剪影响时必须输出 low confidence 或 manual review。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、训练结果复盘、改善 / 缺口信号归因、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff、UserConfirmationRef 交接和 AuditEvent。
- Persistence Targets:
  - `TrainingResult` 或等价训练结果对象。
  - `TrainingResultReview` 或等价训练复盘对象。
  - `WeaknessStatusUpdateSuggestion`
  - `AssetCandidate`
  - `TrainingRecommendation` candidate
  - `CandidateRef`
  - `SuggestionRef`
  - `UserConfirmationRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 训练结果复盘可展示给用户。
  - 用户可以确认弱项状态更新候选、确认资产候选、继续训练、进入 Polish 或重新训练。
  - 本 contract 不自动更新正式 Weakness，不自动归档 Asset，不自动创建下一轮 `TrainingRecommendation`。
- Retry / Fallback:
  - TrainingTask / TrainingSession refs、TrainingRecommendation refs、用户训练输出、evidence refs、Context Assembly 或 owner 校验缺失时停止正常复盘，返回失败或补充材料路径。
  - 训练输出不足、用户自评冲突、改善信号无法判断或上下文裁剪影响归因时输出 low confidence、补充材料请求或 manual review。
  - 重试不得默认启用互联网检索、虚构训练效果、自动更新 Weakness、归档 Asset 或创建下一轮 TrainingRecommendation。
- API State Mapping: 只定义状态语义，包括 `training_result_review_available`、`training_result_review_partial`、`training_result_review_low_confidence`、`training_result_review_validation_failed`、`manual_review_required` 和 `user_confirmation_required`；不定义 endpoint 或 schema。
- Security Notes: 训练结果复盘只使用当前 owner 的训练任务、训练建议、用户训练输出、授权来源、可展示证据摘要和必要 trace id；不得暴露无权限来源正文、原始 Prompt、completion、provider payload 或隐私字段。
- Test Strategy: 使用 fixture 覆盖训练完成复盘、用户提交训练结果、用户查看训练效果、目标 Weakness 改善信号、关联 Asset 候选、下一步训练建议候选、训练输出缺失、TrainingTask 缺失、Recommendation 缺失、用户自评冲突、训练目标不匹配和不得自动更新 Weakness / 归档 Asset / 创建下一轮 TrainingRecommendation。
- Open Questions: 训练结果评估规则、弱项状态影响映射、资产自动沉淀规则、下一轮训练建议生成规则和正式 TrainingResultReview API 字段仍待后续 Training / Weakness / Asset / API / UX 收敛，不在本 contract 关闭。

### 3.4 Training Contract 关系

- `P-TRAINING-001` 基于 Weakness / Asset / Review / Report / Polish / Pressure 等上游生成训练建议候选。
- `P-TRAINING-002` 对训练建议生成优先级排序。
- `P-TRAINING-003` 对训练结果进行复盘，并为 Weakness 状态更新、Asset 候选和后续 `TrainingRecommendation` 提供输入。
- Training contracts 可以消费 Weakness / Asset / Review / Report / Polish / Pressure 输出，但不得重新生成这些上游结果。
- Training contracts 不得自动更新正式 Weakness 状态。
- Training contracts 不得自动归档 Asset 或发布 AssetVersion。
- Training contracts 不得关闭训练优先级算法、训练结果评估规则、弱项自动消减规则或资产自动沉淀规则 UNKNOWN。
- `P-TRAINING-003` 的回流输出必须进入对应 Weakness / Asset / Training 候选或建议链路，不得直接写正式对象。
