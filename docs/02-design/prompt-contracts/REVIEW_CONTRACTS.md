---
title: REVIEW_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/review-contracts
---

# REVIEW_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件遵守 `PROMPT_SPEC.md` §13 的 `AR-F4-FULL-001` 处置口径；复杂算法和实现细节按 deferred_non_blocking 承接。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 当前状态

Review contracts 已按主 catalog 更新为 Draft。本文只承载 `P-REVIEW-001` 至 `P-REVIEW-004` 的详细 contract 正文，不新增未登记 ID，不改变 contract ID、名称、目标或状态。

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-REVIEW-001` | Mock Interview Review | 生成模拟面试复盘 | Draft |
| `P-REVIEW-002` | Real Interview Input Structuring | 结构化真实面试输入 | Draft |
| `P-REVIEW-003` | Real Interview Review | 生成真实面试复盘 | Draft |
| `P-REVIEW-004` | Review Item Extraction | 提炼题级复盘项 | Draft |

## 3. Review Contract 细则

### 3.0 Review 公共字段与边界

#### Review 公共职责

Review contracts 只负责生成模拟面试复盘、结构化真实面试输入、生成真实面试复盘，以及提炼题级复盘项。Review contracts 不负责继续提问、重新生成压力面报告、重新评分 Pressure session、正式创建 Weakness、正式创建 Asset、正式创建 TrainingRecommendation，也不实现复盘切分、真实面试输入结构化、题级复盘项合并、薄弱项合并、资产归档或训练优先级的复杂算法。

#### Review 公共上游输入

Review contracts 可以消费 `P-REPORT-001` Interview Report 输出、`P-REPORT-002` Section Score Explanation 输出、`P-REPORT-003` Risk and Pass Tendency Wording 输出、`P-REPORT-004` Copyable Content Assembly 输出、`P-PRESSURE-009` Report Input Assembly 输出、Pressure session summary、Pressure question / answer refs、Answer Quality Assessment refs、Follow-up chain refs、Session Score refs、evidence bundle refs、low confidence flags、risk signal refs、Report sections、用户手动输入的真实面试题目、回答、面试官反馈、结果、时间线、Job Match summary、Polish summary、RAG evidence 和用户复盘偏好。上述输入必须按任务最小必要装配，不得默认塞入全部简历、全部岗位、全部原始回答全文、全部 Polish 历史、全部知识库、全部历史报告或全部真实面试原始文本。

#### Review 公共检索边界

- `JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG。
- Report、Pressure、Polish、Job Match outputs 是结构化上游，不是 RAG。
- 真实面试用户输入是用户提供材料，不是 RAG。
- RAG / 知识库可以用于技术解释、题目归因和复盘建议增强，但不是 Review MVP 硬依赖。
- 互联网检索不是 MVP 默认强依赖，不得默认启用。
- 条件检索必须经过 `P-SHARED-002` Retrieval Planning。
- 无 RAG、无历史报告、无 Polish summary 时不得阻断基础复盘生成。
- 真实面试输入不足时应进入 low confidence 或要求用户补充，不得伪造细节。

#### Review 公共输出边界

Review 输出可以保存为模拟面试复盘、真实面试结构化输入、真实面试复盘、题级复盘项、validation result、low confidence flag、evidence refs、trace refs、audit event，以及 Weakness / Asset / Training 后续入口建议。Review 输出不得直接写入正式 Weakness、正式 Asset、正式 TrainingRecommendation、新的 Pressure 报告或新的 Pressure 评分。如需产生弱项、资产或训练方向，只能输出候选引用、后续 contract 入口建议或用户确认入口。

#### Review 公共 Output Schema

`P-REVIEW-001` 至 `P-REVIEW-004` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `review_ref` | 否 | ref | 复盘结果引用 |
| `review_type` | 是 | `mock_interview` / `real_interview` / `review_item_extraction` | 复盘类型 |
| `job_version_ref` | 否 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 否 | ref | 生成时简历版本或快照引用 |
| `report_ref` | 否 | ref | 报告引用 |
| `pressure_session_ref` | 否 | ref | 压力面会话引用 |
| `real_interview_input_ref` | 否 | ref | 真实面试结构化输入引用 |
| `question_answer_refs` | 否 | ref[] | 题答引用 |
| `feedback_refs` | 否 | ref[] | 面试官反馈或用户补充反馈引用 |
| `score_result_refs` | 否 | ref[] | 评分结果引用 |
| `risk_signal_refs` | 否 | ref[] | 风险信号引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的证据 |
| `displayable_evidence_summary` | 否 | object[] | 可展示证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记 |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能进入正式回流对象 |

`next_recommended_actions` 允许值至少包括 `view_review`、`extract_review_items`、`mark_weakness_candidate`、`mark_asset_candidate`、`generate_training_later`、`enter_polish_mode`、`enter_pressure_mode`、`provide_more_interview_detail`、`provide_interviewer_feedback` 和 `manual_check_required`。这些 action 只是建议动作或流程入口，不得直接写入正式 Weakness、正式 Asset 或 TrainingRecommendation；需要用户确认的 action 必须进入用户确认流。

#### Review 公共校验与失败边界

- 必须引用 `P-SHARED-001` Context Assembly、`P-SHARED-002` Retrieval Planning、`P-SHARED-003` Output Validation、`P-SHARED-004` Low Confidence Classification 和 `P-SHARED-005` Evidence Binding 中与当前任务相关的规则。
- 必须保留 validation、Low Confidence、EvidenceRef、TraceRef 和 AuditEvent 交接。
- 不得生成完整生产 Prompt 文案、原始 Prompt、completion 或 provider payload。
- 不得定义 API endpoint、物理数据库 schema、LLM provider、模型参数、向量数据库、embedding 模型或搜索服务。
- 不得生成真实复盘实例，不得输出“必过”“必挂”等确定性录用预测。
- 不得把复盘切分、真实面试输入结构化、题级复盘项合并、薄弱项合并算法、资产归档策略或训练优先级算法实现为自动正式写入；这些复杂算法为 deferred_non_blocking。

### 3.1 P-REVIEW-001 Mock Interview Review

- Contract ID: `P-REVIEW-001`
- Name: Mock Interview Review
- Mode: `review`
- Trigger:
  - `P-REPORT-001` Interview Report Generation 完成后。
  - 用户请求生成模拟面试复盘。
  - 用户查看报告后请求“复盘这场模拟面试”。
  - 系统需要将报告结果转化为复盘视角。
- Goal: 基于模拟面试报告、Pressure session、题答、评分、风险提示、低置信度和 evidence 生成模拟面试复盘；本 contract 不重新生成报告，不重新评分，不自动创建正式 Weakness、正式 Asset 或 TrainingRecommendation。
- Required Inputs:
  - `OwnerRef`
  - `report_ref`
  - `pressure_session_ref`
  - Report sections
  - Section score explanations
  - Risk wording
  - Pressure question / answer refs
  - Answer quality refs
  - evidence refs
  - low confidence flags
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - Job Match summary
  - Polish summary
  - weakness candidate refs
  - asset candidate refs
  - user review preferences
  - RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用 report、pressure session summary、question / answer refs、score explanations、risk wording 和 evidence refs。
  - 条件读取 Job Match、Polish、候选弱项、候选资产、知识库 evidence 和用户复盘偏好。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG 或 Polish summary 时仍可生成基础模拟面试复盘。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 report summary、关键题答、分项解释、风险提示、低置信度、source availability 和输出 schema。
  - 上下文过长时优先保留结构化报告、关键题答、负向证据、改进方向、低置信度和复盘必要 refs。
  - 不得默认塞入全部原始回答全文、全部 Polish 历史、全部知识库或全部历史报告。
- Excluded Inputs:
  - 新的 Pressure 评分、报告重生成请求、完整原始 Prompt、completion、provider payload。
  - 无权限来源正文、source deleted / disabled / unavailable 的正文和不可展示敏感原文。
  - 全部原始回答全文、全部 Polish 历史、全部知识库、全部历史报告和默认互联网检索结果。
  - 正式 Weakness、正式 Asset 或 TrainingRecommendation 的写入动作。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Review 公共 Output Schema。
  - `mock_review_id_candidate`
  - `review_summary`
  - `what_went_well`
  - `what_went_wrong`
  - `key_turning_points`
  - `missed_opportunities`
  - `improvement_themes`
  - `question_level_review_refs`
  - `weakness_candidate_refs`
  - `asset_candidate_refs`
  - `training_direction_hints`
  - `low_confidence_summary`
  - `evidence_summary_refs`
  - `next_recommended_actions`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 复盘必须基于报告、Pressure session 或题答证据。
  - 不得重新评分 Pressure session。
  - 不得生成新的报告结论。
  - 不得虚构用户回答、题目、面试官反馈或结果。
  - 不得把候选 Weakness / Asset 写成正式对象。
  - 不得自动创建 TrainingRecommendation。
  - 低置信度或 source unavailable 必须反映在复盘 caveat 中。
  - 复盘不得承诺精确通过概率或确定性结果。
- Low Confidence Rules:
  - report_ref 缺失。
  - question / answer refs 不足。
  - section score explanation 缺失。
  - risk wording 缺失。
  - evidence refs 不足。
  - source unavailable。
  - 关键输入被裁剪。
  - 报告本身低置信度。
- Evidence Requirements: 复盘摘要、表现亮点、问题、转折点、错失机会、改进主题、候选弱项、候选资产和训练方向提示必须绑定 report、Pressure session、题答、score explanation、risk wording 或 evidence refs；无法绑定时必须输出低置信度或要求补充。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、复盘生成、source availability 聚合、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `MockInterviewReview` 或等价模拟面试复盘对象。
  - `ReviewSection` 或等价复盘章节对象。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 复盘可直接展示给用户。
  - 用户可以进入题级复盘、确认候选弱项、确认资产候选、进入 Polish 或手动校对。
  - 由复盘派生的正式 Weakness、Asset 或 TrainingRecommendation 必须进入后续候选 / 确认链路。
- Retry / Fallback:
  - report_ref、pressure_session_ref、owner 校验或核心题答 refs 缺失时停止正常复盘生成，返回失败或补充材料路径。
  - RAG、Polish summary 或用户复盘偏好缺失时可降级生成基础模拟面试复盘，并标记缺失输入和低置信度。
  - 重试不得重新评分、重新生成报告、默认启用互联网检索或创建正式回流对象。
- API State Mapping: 只定义状态语义，包括 `mock_review_available`、`mock_review_partial`、`mock_review_low_confidence`、`mock_review_validation_failed` 和 `mock_review_blocked_by_missing_inputs`；不定义 endpoint 或 schema。
- Security Notes: 模拟面试复盘只使用当前 owner 的 report、Pressure session、题答和授权 evidence；用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖完整报告输入、缺少 report_ref、缺少题答、报告低置信度、无 RAG 降级、禁止重新评分、禁止重新生成报告、禁止正式 Weakness / Asset / TrainingRecommendation 写入和禁止确定性通过预测。
- Open Questions: 复盘切分规则、题级复盘项合并规则、薄弱项合并算法、资产归档策略和训练优先级仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 3.2 P-REVIEW-002 Real Interview Input Structuring

- Contract ID: `P-REVIEW-002`
- Name: Real Interview Input Structuring
- Mode: `review`
- Trigger:
  - 用户提交真实面试回忆。
  - 用户补充真实面试题目、回答、面试官反馈或结果。
  - 用户请求复盘真实面试。
  - 系统需要先将非结构化真实面试材料整理为可复盘输入。
- Goal: 将用户输入的真实面试经历结构化为可复盘的输入包；本 contract 只结构化用户提供的真实面试材料，不虚构题目、回答、反馈、结果或时间线。
- Required Inputs:
  - `OwnerRef`
  - 用户原始真实面试输入
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
  - Job Match summary
  - 历史模拟面试报告 / 复盘
  - 用户补充材料
  - RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用用户原始真实面试输入和用户补充材料。
  - 条件读取岗位、简历、Job Match、历史模拟面试复盘和知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 用户输入不足时不得伪造，只能结构化已知内容并标记 missing fields。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含用户原始输入、已知时间线、题目片段、回答片段、反馈片段、结果片段、缺失字段和输出 schema。
  - 上下文过长时优先保留用户原始事实、明确题答、面试官反馈、时间线和来源 refs。
  - 不得默认塞入全部历史报告、全部 Polish 历史或全部知识库材料。
- Excluded Inputs:
  - 未经用户提供或确认的题目、回答、反馈、结果和时间线。
  - 全部历史报告、全部 Polish 历史、全部知识库和默认互联网检索结果。
  - 对真实面试结果的确定性预测。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Review 公共 Output Schema。
  - `real_interview_input_ref_candidate`
  - `structured_interview_summary`
  - `interview_context`
  - `timeline_items`
  - `question_items`
  - 每个 question item 的 `question_text`
  - 每个 question item 的 `user_answer_summary`
  - 每个 question item 的 `interviewer_feedback`
  - 每个 question item 的 `user_self_assessment`
  - `known_result`
  - `unknown_or_missing_fields`
  - `source_user_input_refs`
  - `confidence_by_field`
  - `needs_user_confirmation`
  - `follow_up_questions_for_user`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 不得虚构用户未提供的题目、回答、反馈、结果或时间线。
  - 不得把用户推测包装成事实。
  - 不得把真实面试结果预测成确定结论。
  - 缺失字段必须显式标记。
  - 用户输入不完整时必须低置信度或要求补充。
  - 结构化结果必须能追溯到用户原始输入。
  - 如需用户确认，必须进入用户确认流。
- Low Confidence Rules:
  - 用户输入过短。
  - 题目缺失。
  - 回答缺失。
  - 面试官反馈缺失。
  - 结果未知。
  - 时间线混乱。
  - 用户输入中事实和推测混杂。
  - 无法关联岗位或简历。
  - 关键字段无法从原始输入支持。
- Evidence Requirements: 结构化摘要、时间线、题目、回答、反馈、结果、缺失字段和置信度必须绑定用户原始输入或用户补充材料；来自用户推测的内容必须保留推测标记，不能写成事实。
- Trace Requirements: 必须记录 `TraceRef`，覆盖用户输入接收、条件 Retrieval Planning、Context Assembly、字段抽取、missing fields 标记、Output Evidence Binding、Output Validation、Low Confidence Classification、用户确认 handoff、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `RealInterviewInput` 或等价真实面试结构化输入对象。
  - `RealInterviewQuestionItem` 或等价题项对象。
  - `UserConfirmationRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 结构化结果默认需要用户确认或编辑后再进入正式真实面试复盘。
  - 用户可以确认、编辑、补充、跳过未知字段或重新结构化。
  - 本 contract 不生成真实面试复盘结论。
- Retry / Fallback:
  - 用户输入缺失、owner 校验失败或关键事实无法抽取时停止正常结构化，返回补充材料路径。
  - 岗位、简历、历史模拟面试复盘或 RAG 缺失时可只结构化用户已提供材料，并标记低置信度或 missing fields。
  - 重试不得默认启用互联网检索、伪造细节或生成复盘结论。
- API State Mapping: 只定义状态语义，包括 `real_interview_input_structured`、`real_interview_input_partial`、`real_interview_input_low_confidence`、`real_interview_input_validation_failed` 和 `real_interview_input_confirmation_required`；不定义 endpoint 或 schema。
- Security Notes: 真实面试输入结构化只使用当前 owner 提供或授权的材料；用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖完整真实面试输入、短输入、缺少题目、缺少回答、缺少反馈、事实和推测混杂、结果未知、需要用户确认、禁止虚构字段和禁止生成复盘结论。
- Open Questions: 真实面试输入结构化规则、字段合并规则、用户确认 UI 和复盘切分规则仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 3.3 P-REVIEW-003 Real Interview Review

- Contract ID: `P-REVIEW-003`
- Name: Real Interview Review
- Mode: `review`
- Trigger:
  - `P-REVIEW-002` Real Interview Input Structuring 完成并经用户确认后。
  - 用户请求真实面试复盘。
  - 用户补充真实面试信息后重新复盘。
  - 系统需要从真实面试输入中提炼表现、风险、机会和后续行动。
- Goal: 基于结构化真实面试输入生成真实面试复盘；本 contract 不虚构真实面试细节，不承诺录用结果，不自动创建正式 Weakness、正式 Asset 或 TrainingRecommendation。
- Required Inputs:
  - `OwnerRef`
  - `RealInterviewInput`
  - 结构化题项
  - 用户确认记录或等价确认状态
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
  - Job Match summary
  - Mock Interview Review
  - Report summary
  - existing Weakness
  - confirmed AssetVersion
  - RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用结构化真实面试输入、用户确认记录和题项。
  - 条件读取岗位、简历、Job Match、模拟面试复盘、报告、既有弱项、已确认资产、知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG、无历史模拟面试时仍可基于真实面试输入生成基础复盘。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含真实面试结构化输入、用户确认状态、题项、反馈、结果、缺失字段、低置信度和输出 schema。
  - 上下文过长时优先保留用户确认事实、题答、面试官反馈、结果、关键不确定点和 evidence refs。
  - 不得默认塞入全部历史模拟面试、全部 Polish 历史、全部知识库或全部资产。
- Excluded Inputs:
  - 未确认或无法追溯的真实面试细节。
  - 面试官意图、录用结果和通过概率的确定性预测。
  - 全部历史模拟面试、全部 Polish 历史、全部知识库、全部资产和默认互联网检索结果。
  - 正式 Weakness、正式 Asset 或 TrainingRecommendation 的写入动作。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Review 公共 Output Schema。
  - `real_review_id_candidate`
  - `review_summary`
  - `performance_highlights`
  - `performance_risks`
  - `missed_opportunities`
  - `interviewer_signal_interpretation`
  - `question_level_review_refs`
  - `weakness_candidate_refs`
  - `asset_candidate_refs`
  - `follow_up_action_hints`
  - `uncertain_or_missing_context`
  - `low_confidence_summary`
  - `evidence_summary_refs`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 复盘必须基于用户确认的真实面试输入或明确标记未确认。
  - 不得虚构题目、回答、反馈、结果或面试官意图。
  - 不得承诺录用结果。
  - 不得输出“必过”“必挂”等确定性预测。
  - 不得把用户推测包装成事实。
  - 不得把候选 Weakness / Asset 写成正式对象。
  - 不得自动创建 TrainingRecommendation。
  - 低置信度、缺失字段和 source unavailable 必须反映在复盘 caveat 中。
- Low Confidence Rules:
  - 真实面试输入未确认。
  - 题目 / 回答 / 反馈缺失。
  - 结果未知。
  - 用户输入中事实和推测混杂。
  - 与岗位 / 简历关联不足。
  - evidence refs 不足。
  - RAG evidence 不可用但技术解释需要。
  - 缺失字段影响复盘结论。
- Evidence Requirements: 复盘摘要、表现亮点、风险、错失机会、面试官信号解读、候选弱项、候选资产和后续行动提示必须绑定用户确认事实、结构化题项、反馈、结果、岗位 / 简历引用或授权 evidence；无法绑定时必须输出低置信度或要求补充。
- Trace Requirements: 必须记录 `TraceRef`，覆盖用户确认检查、条件 Retrieval Planning、Input Evidence Selection、Context Assembly、真实面试复盘生成、source availability 聚合、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `RealInterviewReview` 或等价真实面试复盘对象。
  - `ReviewSection`
  - `ReviewItem`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 真实面试复盘可展示给用户。
  - 用户可以补充输入、修正事实、进入题级复盘、确认候选弱项、确认资产候选或进入 Polish。
  - 由复盘派生的正式 Weakness、Asset 或 TrainingRecommendation 必须进入后续候选 / 确认链路。
- Retry / Fallback:
  - `RealInterviewInput`、结构化题项、owner 校验或用户确认状态缺失时停止正常复盘生成，返回补充或确认路径。
  - 岗位、简历、历史模拟面试、报告或 RAG 缺失时可生成基础真实面试复盘，并标记低置信度或缺失上下文。
  - 重试不得默认启用互联网检索、虚构真实面试细节、承诺录用结果或创建正式回流对象。
- API State Mapping: 只定义状态语义，包括 `real_review_available`、`real_review_partial`、`real_review_low_confidence`、`real_review_validation_failed` 和 `real_review_blocked_by_confirmation`；不定义 endpoint 或 schema。
- Security Notes: 真实面试复盘只使用当前 owner 已确认或授权的输入和 evidence；用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖用户已确认输入、未确认输入、缺少反馈、结果未知、事实和推测混杂、无 RAG 降级、禁止虚构面试官意图、禁止录用确定性预测和禁止正式 Weakness / Asset / TrainingRecommendation 写入。
- Open Questions: 复盘切分规则、题级复盘项合并、薄弱项合并算法、资产归档策略和训练优先级仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 3.4 P-REVIEW-004 Review Item Extraction

- Contract ID: `P-REVIEW-004`
- Name: Review Item Extraction
- Mode: `review`
- Trigger:
  - `P-REVIEW-001` Mock Interview Review 完成后。
  - `P-REVIEW-003` Real Interview Review 完成后。
  - 用户请求查看题级复盘。
  - 系统需要将复盘拆解为可追踪题项、问题项、改进项和候选回流输入。
- Goal: 从模拟面试复盘或真实面试复盘中提炼题级复盘项；本 contract 只提炼 review items，不自动创建正式 Weakness、正式 Asset 或 TrainingRecommendation。
- Required Inputs:
  - `OwnerRef`
  - Mock Interview Review 或 Real Interview Review
  - source review type
  - question / answer refs 或 real interview question items
  - evidence refs
  - low confidence flags
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - section score explanations
  - risk wording
  - weakness candidate refs
  - asset candidate refs
  - existing Weakness
  - confirmed AssetVersion
  - RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用复盘对象、题答或真实面试题项、evidence refs 和 low confidence flags。
  - 条件读取报告、评分解释、风险提示、已有弱项、资产、知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含复盘摘要、题答或题项、问题描述、证据、低置信度和输出 schema。
  - 上下文过长时优先保留题级事实、用户回答、面试官反馈、复盘结论、证据 refs 和候选回流线索。
  - 不得默认塞入全部报告、全部历史复盘、全部知识库或全部资产。
- Excluded Inputs:
  - 无来源支撑的题目、回答、反馈或复盘结论。
  - 全部报告、全部历史复盘、全部知识库、全部资产和默认互联网检索结果。
  - 正式 Weakness、正式 Asset、TrainingRecommendation 或自动合并动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §3.0 的 Review 公共 Output Schema。
  - `review_item_extraction_id_candidate`
  - `review_items`
  - 每个 item 的 `review_item_id_candidate`
  - 每个 item 的 `source_review_ref`
  - 每个 item 的 `source_question_ref`
  - 每个 item 的 `item_type`
  - 每个 item 的 `title`
  - 每个 item 的 `description`
  - 每个 item 的 `evidence_refs`
  - 每个 item 的 `low_confidence_flags`
  - 每个 item 的 `related_weakness_candidate_refs`
  - 每个 item 的 `related_asset_candidate_refs`
  - 每个 item 的 `suggested_follow_up_action`
  - `item_ordering`
  - `merge_candidate_refs`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 每个 review item 必须来源于复盘、题答、真实面试题项或 evidence。
  - 不得虚构题目、回答、反馈或复盘结论。
  - 不得把单个 item 自动升级为正式 Weakness。
  - 不得把参考表达自动归档为正式 Asset。
  - `suggested_follow_up_action` 只是入口建议，不等同正式训练任务。
  - 如果 item 与既有 Weakness / Asset 可能重复，应输出 merge candidate refs，不得自动合并。
  - 低置信度 item 必须保留标记。
- Low Confidence Rules:
  - 复盘对象低置信度。
  - 题答或题项缺失。
  - evidence refs 不足。
  - item 类型无法确定。
  - 与已有弱项 / 资产冲突。
  - 用户输入事实与推测混杂。
  - 上下文裁剪影响题级归因。
- Evidence Requirements: 每个 review item 的标题、描述、item type、证据、候选弱项、候选资产、后续动作和合并候选必须绑定 source review、source question、题答、真实面试题项或 evidence refs；无法绑定时必须标记低置信度。
- Trace Requirements: 必须记录 `TraceRef`，覆盖源复盘读取、条件 Retrieval Planning、Context Assembly、题级拆解、候选重复检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `ReviewItem` 或等价题级复盘项对象。
  - `ReviewItemEvidence`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- User Confirmation Requirement:
  - 题级复盘项可展示给用户。
  - 用户可以确认、编辑、跳过、合并或进入后续 Weakness / Asset / Training contract。
  - 本 contract 不直接创建正式 Weakness、Asset 或 TrainingRecommendation。
- Retry / Fallback:
  - 源复盘、题答或题项、owner 校验或 evidence refs 缺失时停止正常提取，返回补充材料路径。
  - 报告、评分解释、风险提示、已有弱项、资产或 RAG 缺失时可基于源复盘提炼基础 review items，并标记低置信度。
  - 重试不得默认启用互联网检索、自动合并弱项 / 资产或创建正式训练任务。
- API State Mapping: 只定义状态语义，包括 `review_items_available`、`review_items_partial`、`review_items_low_confidence`、`review_items_validation_failed` 和 `review_items_blocked_by_missing_source`；不定义 endpoint 或 schema。
- Security Notes: 题级复盘项提取只使用当前 owner 的源复盘、题答、题项和授权 evidence；用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖模拟面试复盘来源、真实面试复盘来源、缺少题答、低置信源复盘、可能重复弱项 / 资产、无 RAG 降级、禁止虚构 item、禁止自动创建正式 Weakness / Asset / TrainingRecommendation 和禁止自动合并。
- Open Questions: 题级复盘项合并规则、薄弱项合并算法、资产归档策略、训练优先级和跨复盘聚合规则仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 3.5 Review Contract 关系

- `P-REVIEW-001` 基于模拟面试报告、Pressure session 和 evidence 生成模拟面试复盘。
- `P-REVIEW-002` 将用户提供的真实面试输入结构化。
- `P-REVIEW-003` 基于结构化真实面试输入生成真实面试复盘。
- `P-REVIEW-004` 从模拟或真实面试复盘中提炼题级复盘项。
- `P-REVIEW-001` 和 `P-REVIEW-003` 都可作为 `P-REVIEW-004` 的上游。
- Review contracts 可以消费 Report / Pressure 输出，但不得重新评分或重新生成报告。
- Review contracts 不得直接写入正式 Weakness、正式 Asset 或 TrainingRecommendation。
- Review contracts 不实现复盘切分、真实面试输入结构化、题级复盘项合并、薄弱项合并、资产归档或训练优先级复杂算法；这些为 deferred_non_blocking，且不得绕过候选 / 建议 / 用户确认边界。
- Weakness / Asset / Training contracts 仍保持 Stub，等待后续阶段授权填充。
