---
title: PRESSURE_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/pressure-contracts
---

# PRESSURE_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件不关闭 `F4_TECH_DESIGN` UNKNOWN。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 适用范围

本文件承载主 catalog 中 `P-PRESSURE-001` 至 `P-PRESSURE-004` 的详细 contract 正文，并保留 `P-PRESSURE-005` 至 `P-PRESSURE-009` 的 Stub 摘要。

## 13. Pressure Contract 细则

### 13.0 Pressure 第一组公共字段与边界

#### Pressure 第一组公共边界

Pressure 是压力面模式，不是打磨模式。Pressure 侧重真实面试节奏、连续追问、回答质量判断和面试状态推进，不允许像 Polish 一样围绕同一道题无限打磨。

Pressure 第一组只负责开场策略、首题生成、回答质量判断和追问策略选择。第一组不直接生成连续追问题目，不直接控制整场节奏，不直接判断整场结束，不生成整场评分，不生成最终面试报告，也不直接写入正式 `Weakness`、正式 `Asset` 或正式 `TrainingRecommendation`。如需产生弱项、资产、报告或训练方向，只能输出后续 contract 入口建议、候选引用或 session summary update 输入。

压力强度、追问深度、结束条件和整场评分公式仍为 UNKNOWN，本阶段不关闭这些 `F4_TECH_DESIGN` UNKNOWN。Pressure 第一组也不得退化为一次 LLM 调用；应用编排层必须串联 Shared Contracts、会话状态、用户动作、校验、证据绑定、trace 和持久化交接。

Pressure 第一组可以条件消费 `JobVersion`、`ResumeVersion`、`JobMatchAnalysis`、`ScoreResult` canonical score、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、Polish session summary、Polish 已问问题、Polish 诊断 / 得分 / 失分点 / 弱项候选 / 资产候选、既有 `Weakness`、已确认 `AssetVersion`、历史模拟面试报告 / 复盘、当前 Pressure session summary、最近若干 Pressure turns、RAG evidence 和公共参考材料。上述输入必须按任务最小必要裁剪，不得默认塞入全部简历、全部岗位、全部历史会话、全部资产、全部 Polish 记录、全部知识库材料或全部报告。

`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG；Job Match 和 Polish 输出是结构化上游，不是 RAG。资产库、薄弱项、历史 Polish turns、历史 Pressure turns、历史报告、复盘和知识库是条件检索来源；条件检索必须经过 `P-SHARED-002`。RAG / 知识库可用于问题素材、技术准确性和考点评估增强，但不是 Pressure 第一组 MVP 的硬依赖；互联网检索不是 MVP 默认强依赖，不得默认启用。无 RAG、无资产、无历史报告或无历史复盘时，不得阻断基础 Pressure 流程。

Pressure 第一组输出可以保存为开场策略、首题候选、回答质量判断、追问策略候选、validation result、low confidence flag、evidence refs、trace refs、session summary update 输入和 audit event。Pressure 第一组不得直接写入正式 `Weakness`、正式 `Asset`、正式 `TrainingRecommendation`、最终面试报告或整场评分。需要用户确认的 action 必须进入用户确认流。

#### Pressure 第一组公共 Output Schema

`P-PRESSURE-001` 至 `P-PRESSURE-004` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `pressure_session_ref` | 是 | ref | 压力面会话引用 |
| `pressure_turn_ref` | 否 | ref | 当前压力面轮次引用 |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `job_match_refs` | 否 | ref[] | 被消费的岗位匹配结果引用 |
| `polish_refs` | 否 | ref[] | 被消费的 Polish 结果引用 |
| `turn_refs` | 否 | ref[] | 被消费的 Pressure 轮次引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性聚合状态；底层来源状态仍沿用 §6.1 的 `source_*` 枚举 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的 `EvidenceRef` |
| `displayable_evidence_summary` | 否 | object[] | 可展示证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记，必须可追溯到 `P-SHARED-004` |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 `TraceRef` |
| `session_summary_update_ref` | 否 | ref | `P-SHARED-006` 产出的摘要更新引用 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能进入正式回流对象 |

`next_recommended_actions` 只表达建议动作或流程入口，不直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。允许值至少包括 `start_pressure_session`、`ask_first_question`、`submit_answer`、`assess_answer_quality`、`generate_follow_up_strategy`、`generate_follow_up_question`、`continue_pressure_session`、`pause_pressure_session`、`end_pressure_session_later`、`generate_pressure_report_later`、`mark_weakness_candidate`、`mark_asset_candidate`、`enter_polish_mode`、`request_clarification` 和 `provide_more_answer_detail`。其中需要用户确认的 action 必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。

### 13.1 `P-PRESSURE-001` Opening Strategy

- Contract ID: `P-PRESSURE-001`
- Name: Opening Strategy
- Mode: `pressure`
- Trigger:
  - 用户进入压力面模式。
  - 用户选择岗位 / 简历 / Job Match 结果后开始压力面。
  - 用户从 Polish 结果进入压力面。
  - 用户重新开始一场压力面。
  - 系统需要为首题生成提供策略输入。
- Goal: 基于岗位、简历、Job Match、Polish 历史、用户目标和 session 状态生成压力面开场策略；开场策略用于确定起始范围、面试风格、重点能力、压力强度提示和首题方向，不直接生成整场题目列表。
- Required Inputs:
  - `OwnerRef`
  - `pressure_session_ref`
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- Optional Inputs:
  - `JobMatchAnalysis`
  - `ScoreResult` canonical score
  - `MatchPoint`
  - `MismatchPoint`
  - `ImprovementPoint`
  - Polish session summary
  - Polish Weakness Candidate
  - Polish Asset Candidate
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 历史报告 / 复盘摘要
  - RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用岗位、简历和当前 pressure session。
  - 条件检索 Job Match、Polish summary、弱项、资产、历史报告、复盘和知识库。
  - Polish 结果是结构化上游，不是 RAG。
  - 互联网检索不默认启用。
  - 无 Polish 结果或 Job Match 结果时仍可基于岗位与简历开始压力面，但必须标记输入较弱或低置信度。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含岗位摘要、简历摘要、当前压力面目标、pressure session summary、Job Match / Polish 相关 refs 和输出 schema。
  - 不得默认塞入全部 Polish 历史、全部报告、全部资产或全部知识库材料。
  - 上下文过长时优先保留岗位核心要求、简历强相关模块、弱项候选、用户目标和禁止重复方向。
- Excluded Inputs:
  - 全量 Polish 历史、全量报告、全量资产、全量知识库和无关历史会话正文。
  - 被标记为 source deleted / disabled / unavailable 的正文。
  - owner 不一致或未经授权的简历、岗位、会话、资产、弱项、报告和知识库内容。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- Output Schema:
  - 公共字段：必须完整包含 §13.0 的 Pressure 第一组公共 Output Schema。
  - `opening_strategy_id_candidate`
  - `interview_focus_areas`
  - 每个 focus area 的 `focus_area_id_candidate`
  - 每个 focus area 的 `title`
  - 每个 focus area 的 `source_type`
  - 每个 focus area 的 `source_refs`
  - 每个 focus area 的 `evidence_refs`
  - 每个 focus area 的 `priority`
  - 每个 focus area 的 `pressure_intensity_hint`
  - 每个 focus area 的 `difficulty_hint`
  - `opening_tone`
  - `first_question_direction`
  - `forbidden_repeat_topics`
  - `session_goal`
  - `risk_flags`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 开场策略必须与岗位、简历或用户目标相关。
  - 不得生成整场固定题库。
  - 不得把 Polish 的同题打磨逻辑带入压力面。
  - `pressure_intensity_hint` 只是提示，不冻结压力强度算法。
  - `difficulty_hint` 只是提示，不冻结题目难度算法。
  - 不得默认启用互联网检索。
  - 不得承诺面试通过概率或准确预测真实面试结果。
  - 不得生成违法、歧视、隐私侵入或与岗位无关的面试策略。
- Low Confidence Rules:
  - 岗位要求缺失。
  - 简历信息不足。
  - Job Match 缺失。
  - Polish 历史缺失。
  - 用户目标不清。
  - evidence 不足。
  - 历史结果低置信度。
  - 上下文高风险裁剪。
- Evidence Requirements: focus area、priority、压力强度提示、难度提示、首题方向、风险标记和禁止重复方向必须绑定岗位、简历、Job Match、Polish summary、session summary 或其他授权 evidence；证据不足时必须输出低置信度或要求用户补充目标。
- Trace Requirements: 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、开场策略生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `PressureSession` opening strategy 或等价会话内策略对象。
  - `PressureOpeningStrategy` candidate 或等价逻辑对象。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- User Confirmation Requirement:
  - 开场策略可作为压力面启动配置。
  - 用户可以开始、调整方向、切换岗位 / 简历、返回 Polish 或取消。
  - 开场策略不直接创建正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- Retry / Fallback:
  - `OwnerRef`、岗位版本、简历版本或 pressure session 缺失时停止正常生成，返回失败或补充材料路径。
  - Job Match、Polish 历史、资产或历史报告缺失时可降级为基于岗位和简历的基础开场策略，并输出低置信度原因。
  - 重试不得默认启用互联网检索、扩大到全量历史会话或生成整场题库。
- API State Mapping: 只定义状态语义，包括 `opening_strategy_available`、`opening_strategy_partial`、`opening_strategy_low_confidence`、`opening_strategy_validation_failed`、`user_confirmation_required` 和 `input_context_insufficient`；不定义 endpoint 或 schema。
- Security Notes: 开场策略只使用当前 owner 的岗位、简历、pressure session 和授权增强证据；可展示证据摘要不得包含无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖有 Job Match / Polish 上游、无 Job Match、无 Polish、用户目标不清、evidence 不足、禁止整场题库、禁止同题打磨逻辑、禁止互联网默认检索和不得创建正式回流对象。
- Open Questions: 压力强度算法、题目难度算法、首题方向排序算法、输入优先级细则和整场节奏策略仍待后续 contract / API / UX 收敛，不在本 contract 关闭。

### 13.2 `P-PRESSURE-002` First Question Generation

- Contract ID: `P-PRESSURE-002`
- Name: First Question Generation
- Mode: `pressure`
- Trigger:
  - `P-PRESSURE-001` Opening Strategy 完成后。
  - 用户确认开始压力面。
  - 用户跳过首题并请求新首题。
  - 系统需要根据开场策略启动第一轮 Pressure turn。
- Goal: 基于开场策略、岗位、简历、Job Match / Polish 上游和 session 状态生成首题；首题用于启动真实面试节奏，不是 Polish 同题打磨题，也不是整场题目列表。
- Required Inputs:
  - `OwnerRef`
  - `pressure_session_ref`
  - `P-PRESSURE-001` Opening Strategy 结果
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- Optional Inputs:
  - Job Match points
  - Polish 已问问题列表
  - Pressure 已问问题列表
  - 禁止重复问题列表
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用开场策略、岗位、简历和 pressure session summary。
  - 条件检索 Job Match、Polish 已问问题、Pressure 已问问题、弱项、资产和知识库。
  - 知识库 / RAG 可用于题目素材增强，但不是必需输入。
  - 互联网检索不默认启用。
  - 无 RAG 时仍必须可以生成基础首题。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 opening strategy、岗位要求、简历相关模块、已问问题、禁止重复列表、当前压力面目标和输出 schema。
  - 不得默认塞入全部 Polish 历史或全部知识库材料。
  - 上下文过长时优先保留 opening strategy、禁止重复问题、岗位核心要求、简历模块和 evidence refs。
- Excluded Inputs:
  - Polish 同题打磨题作为首题直接复用。
  - 整场题库、连续追问题目列表或报告评分输入。
  - 全量 Polish 历史、全量知识库、无关历史回答全文和默认互联网检索结果。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §13.0 的 Pressure 第一组公共 Output Schema。
  - `first_question_id_candidate`
  - `question_text`
  - `question_type`
  - `pressure_focus_area_ref`
  - `difficulty_hint`
  - `pressure_intensity_hint`
  - `expected_answer_signals`
  - `related_job_requirements`
  - `related_resume_modules`
  - `source_refs`
  - `evidence_refs`
  - `anti_repeat_refs`
  - `time_box_hint`
  - `follow_up_strategy_required`
  - `polish_mode_hint_visibility`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 首题必须与 opening strategy、岗位要求或简历模块相关。
  - 首题不得重复最近 Polish 或 Pressure 已问问题。
  - 首题不得直接泄露参考答案。
  - 首题不得被写成 Polish 同题打磨题。
  - `question_type` 必须使用稳定枚举或等价描述。
  - `pressure_intensity_hint` 只是提示，不冻结压力强度算法。
  - 不得生成违法、隐私侵入、歧视或与岗位无关题目。
- Low Confidence Rules:
  - opening strategy 缺失或低置信度。
  - 岗位或简历证据不足。
  - 禁止重复列表缺失。
  - 首题与岗位 / 简历关联弱。
  - RAG evidence 不可用但题目需要知识补充。
  - 输出题目过泛。
  - 无法判断是否重复。
- Evidence Requirements: 首题文本、题型、focus area、难度提示、压力强度提示、预期回答信号、岗位要求和简历模块关联必须绑定 opening strategy、岗位、简历、已问问题、禁止重复列表或授权 evidence；无法判断重复时必须低置信度。
- Trace Requirements: 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、首题生成、去重检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、PressureTurn 初始化 handoff、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `PressureQuestion` candidate 或等价会话内题目对象。
  - `PressureTurn` 初始化输入。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- User Confirmation Requirement:
  - 生成首题可以直接进入压力面答题流程。
  - 用户可跳过、换题、暂停、退出或返回 Polish。
  - 首题生成不得直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- Retry / Fallback:
  - opening strategy、岗位版本、简历版本或 pressure session 缺失时停止正常生成，返回失败或补充材料路径。
  - 已问问题或禁止重复列表缺失时可生成低置信度首题，并要求后续去重补检或用户确认。
  - RAG 不可用时降级为岗位 / 简历 / opening strategy 驱动的基础首题；不得默认启用互联网检索。
- API State Mapping: 只定义状态语义，包括 `first_question_available`、`first_question_partial`、`first_question_low_confidence`、`first_question_validation_failed`、`duplicate_risk_detected` 和 `question_skip_available`；不定义 endpoint 或 schema。
- Security Notes: 首题生成只使用当前 owner 的开场策略、岗位、简历、session summary 和授权增强证据；不得暴露参考答案、无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖 opening strategy 后生成、用户跳过换题、无 RAG、重复 Polish 题拦截、重复 Pressure 题拦截、题目过泛低置信度、参考答案不泄露、不得生成整场题库和不得创建正式回流对象。
- Open Questions: 首题推荐排序、题型枚举全集、难度算法、压力强度算法和时间盒提示规则仍待后续 contract / API / UX 收敛，不在本 contract 关闭。

### 13.3 `P-PRESSURE-003` Answer Quality Assessment

- Contract ID: `P-PRESSURE-003`
- Name: Answer Quality Assessment
- Mode: `pressure`
- Trigger:
  - 用户提交压力面当前题目的回答。
  - 用户补充回答后重新评估。
  - `P-PRESSURE-004` Follow-up Strategy 需要回答质量输入。
  - 系统需要决定继续追问、澄清、切换方向或结束后续流程。
- Goal: 判断用户对当前压力面题目的回答是否充分、是否跑题、是否可追问、是否需要澄清、是否暴露明显风险，并为追问策略提供输入。
- Required Inputs:
  - `OwnerRef`
  - `pressure_session_ref`
  - `pressure_turn_ref`
  - 当前 Pressure 问题引用
  - 用户当前回答引用
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - Opening Strategy
  - 当前 focus area
  - Job Match points
  - Polish diagnosis / loss points / weakness candidates
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 最近若干 Pressure turns
  - 题目相关知识库 / RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用当前问题、当前回答、岗位、简历和 session summary。
  - 条件检索 opening strategy、Job Match points、Polish 诊断、历史 Pressure turns、资产、薄弱项和知识库。
  - 如果需要判断技术准确性或补充考点，可经过 `P-SHARED-002` 使用知识库 / RAG。
  - 不得默认启用互联网检索。
  - 无知识库时仍可基于题目、岗位、简历和回答进行基础质量判断，但技术准确性判断应标记证据弱或低置信度。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则；条件检索时必须继承 `P-SHARED-002`。
  - 上下文至少包含当前问题、用户回答、岗位相关要求、简历相关模块、opening strategy、最近相关 Pressure turn 和输出 schema。
  - 对长回答必须优先保留用户原始回答、问题要求、岗位证据和质量评估目标。
  - 不得默认塞入全部历史回答、全部 Polish 历史或全部知识库材料。
- Excluded Inputs:
  - 用户未表达经历、事实、数据或职责作为质量判断事实。
  - 岗位不匹配结论作为用户能力缺陷的直接替代。
  - 正式 Weakness、Asset 或 TrainingRecommendation 写入指令。
  - 全量历史回答、全量 Polish 历史、全量知识库、默认互联网检索结果、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §13.0 的 Pressure 第一组公共 Output Schema。
  - `answer_quality_assessment_id_candidate`
  - `question_ref`
  - `answer_ref`
  - `answer_summary`
  - `quality_level`
  - `sufficiency_status`
  - `relevance_status`
  - `depth_status`
  - `technical_accuracy_status`
  - `structure_status`
  - `communication_status`
  - `risk_signals`
  - `missing_points`
  - `unclear_points`
  - `off_topic_segments`
  - `follow_up_needed`
  - `clarification_needed`
  - `score_input_refs`
  - `evidence_refs`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 质量判断必须基于当前问题和当前回答。
  - 不得虚构用户未表达经历。
  - 不得把岗位不匹配直接包装为用户能力缺陷。
  - 不得静默创建正式 `Weakness`。
  - 技术准确性判断如缺少知识证据，应触发低置信度。
  - `quality_level`、`sufficiency_status`、`relevance_status`、`depth_status` 等必须使用稳定枚举或等价描述。
  - `follow_up_needed` 只是策略输入，不等于已经生成追问题目。
  - `clarification_needed` 只是策略输入，不等于用户失败。
- Low Confidence Rules:
  - 用户回答过短。
  - 用户回答明显跑题。
  - 当前问题缺失。
  - 岗位 / 简历证据不足。
  - 技术判断缺少知识证据。
  - 回答中存在自相矛盾内容。
  - 上下文裁剪影响评估。
  - 模型无法区分事实、推测和建议。
- Evidence Requirements: 回答摘要、质量等级、充分性、相关性、深度、技术准确性、结构、沟通、风险信号、缺失点、模糊点和跑题片段必须绑定当前问题、用户回答、岗位要求、简历模块、知识 evidence 或 session summary；无法绑定时必须输出低置信度。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、回答质量评估、技术准确性证据检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `PressureAnswerQualityAssessment` 或等价会话内评估对象。
  - `PressureTurn` answer quality result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- User Confirmation Requirement:
  - 回答质量判断可作为内部策略和必要反馈展示。
  - 派生的弱项、资产或训练方向只能作为候选或后续 contract 输入。
  - 用户可补充回答、请求澄清、暂停或继续。
- Retry / Fallback:
  - 当前问题、当前回答、pressure turn、岗位版本、简历版本或 owner 校验缺失时停止正常评估，返回失败或补充材料路径。
  - 回答过短、技术证据不足或上下文裁剪影响判断时可保存低置信度评估，要求用户补充回答或降级为基础质量判断。
  - 重试不得默认启用互联网检索、虚构用户经历或创建正式 `Weakness`。
- API State Mapping: 只定义状态语义，包括 `answer_quality_available`、`answer_quality_partial`、`answer_quality_low_confidence`、`answer_quality_validation_failed`、`clarification_needed` 和 `follow_up_strategy_input_ready`；不定义 endpoint 或 schema。
- Security Notes: 回答质量判断只使用当前 owner 的问题、回答、岗位、简历、session summary 和授权 evidence；展示摘要不得泄露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖充分回答、过短回答、跑题回答、技术证据缺失、当前问题缺失、回答矛盾、岗位证据不足、follow_up_needed 只作为策略输入、不得虚构用户经历和不得静默创建正式弱项。
- Open Questions: 回答质量枚举全集、评分映射、技术准确性证据阈值、稳定能力缺陷判定和整场评分输入聚合仍待后续 contract / API / UX 收敛，不在本 contract 关闭。

### 13.4 `P-PRESSURE-004` Follow-up Strategy

- Contract ID: `P-PRESSURE-004`
- Name: Follow-up Strategy
- Mode: `pressure`
- Trigger:
  - `P-PRESSURE-003` Answer Quality Assessment 完成后。
  - 用户回答质量不足、过泛、跑题、缺少细节或暴露风险。
  - 用户回答质量较好，需要加深或换方向。
  - 系统需要决定继续追问、澄清、换题、暂停或准备结束。
- Goal: 基于当前问题、用户回答、回答质量判断、opening strategy、历史 turns 和 session summary 选择追问策略；本 contract 只选择追问策略，不生成具体追问题目，具体追问题目由后续 `P-PRESSURE-005` 负责。
- Required Inputs:
  - `OwnerRef`
  - `pressure_session_ref`
  - `pressure_turn_ref`
  - 当前问题引用
  - 当前回答引用
  - `P-PRESSURE-003` Answer Quality Assessment 结果
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- Optional Inputs:
  - `P-SHARED-002` Retrieval Planning 结果
  - Opening Strategy
  - First Question
  - Job Match points
  - Polish weakness candidates
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 最近若干 Pressure turns
  - 已问问题列表
  - 禁止重复追问列表
  - 知识库 / RAG evidence
  - 公共参考材料
- Retrieval Sources:
  - 默认使用当前问题、当前回答、质量评估、opening strategy 和 session summary。
  - 条件读取历史 Pressure turns、已问问题、禁止重复追问、Job Match / Polish 上游、弱项、资产和知识库。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG、无资产、无历史 Pressure turns 时仍可生成基础追问策略。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则；条件读取时必须继承 `P-SHARED-002`。
  - 上下文至少包含当前问题、当前回答、质量评估、opening strategy、已问问题、禁止重复追问、session summary 和输出 schema。
  - 上下文过长时优先保留当前轮质量判断、风险信号、未覆盖点、禁止重复列表和 pressure focus。
  - 不得默认塞入全部历史回答、全部 Polish 历史、全部知识库或全部资产。
- Excluded Inputs:
  - 具体追问题目正文、连续追问题目列表或整场题库。
  - Polish 同题打磨建议作为 Pressure 追问策略的直接替代。
  - 单次回答不足作为稳定能力缺陷的确定事实。
  - 整场结束条件阈值、整场评分公式或正式报告生成指令。
  - 全量历史回答、全量 Polish 历史、全量知识库、全量资产、默认互联网检索结果、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §13.0 的 Pressure 第一组公共 Output Schema。
  - `follow_up_strategy_id_candidate`
  - `strategy_type`
  - `strategy_reason`
  - `target_gap_refs`
  - `target_risk_signal_refs`
  - `target_missing_point_refs`
  - `pressure_intensity_adjustment`
  - `follow_up_depth_hint`
  - `clarification_needed`
  - `switch_topic_hint`
  - `pause_or_end_hint`
  - `forbidden_repeat_follow_up_refs`
  - `next_question_generation_requirements`
  - `blocked_by_low_confidence`
  - `user_visible_summary`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 策略必须基于当前回答质量判断、当前问题、opening strategy 或 session summary。
  - 不得直接生成具体追问题目。
  - 不得把 Polish 同题打磨建议当成 Pressure 追问策略。
  - 不得把一次回答不足直接包装成稳定能力缺陷。
  - `pressure_intensity_adjustment` 只是提示，不冻结压力强度算法。
  - `follow_up_depth_hint` 只是提示，不冻结追问深度算法。
  - `pause_or_end_hint` 只是提示，不关闭结束条件 UNKNOWN。
  - 策略不得绕过用户暂停、退出或模式切换选择。
  - 不得生成违法、歧视、隐私侵入或攻击性策略。
- Low Confidence Rules:
  - 回答质量判断缺失或低置信度。
  - 当前问题或回答缺失。
  - opening strategy 缺失。
  - 已问问题或禁止重复列表缺失。
  - 质量判断与 evidence 不一致。
  - 上下文裁剪影响策略选择。
  - 关键 risk signals 无法绑定证据。
  - 用户目标不清。
- Evidence Requirements: 策略类型、策略原因、目标 gap、风险信号、缺失点、压力强度调整、追问深度提示、澄清、换题、暂停或稍后结束提示必须绑定回答质量判断、当前问题、当前回答、opening strategy、session summary、已问问题或授权 evidence；无法绑定时必须输出 `blocked_by_low_confidence` 或要求澄清。
- Trace Requirements: 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、追问策略选择、重复追问约束检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、`P-PRESSURE-005` handoff、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `PressureFollowUpStrategy` 或等价会话内策略对象。
  - `PressureTurn` follow-up strategy result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- User Confirmation Requirement:
  - 追问策略可作为内部编排依据。
  - 用户可以继续、暂停、退出、切换主题或返回 Polish。
  - 本 contract 不创建正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
  - 本 contract 不生成具体追问题目；具体题目由后续 contract 生成。
- Retry / Fallback:
  - 回答质量判断、当前问题、当前回答、pressure turn、岗位版本、简历版本或 owner 校验缺失时停止正常策略选择，返回失败或补充材料路径。
  - 已问问题、禁止重复追问或 evidence 不足时可保存低置信度策略，要求澄清或降级为基础策略。
  - 重试不得默认启用互联网检索、生成具体追问题目、关闭整场结束条件或创建正式回流对象。
- API State Mapping: 只定义状态语义，包括 `follow_up_strategy_available`、`follow_up_strategy_partial`、`follow_up_strategy_low_confidence`、`follow_up_strategy_validation_failed`、`blocked_by_low_confidence`、`clarification_needed` 和 `follow_up_question_generation_ready`；不定义 endpoint 或 schema。
- Security Notes: 追问策略只使用当前 owner 的问题、回答、质量评估、opening strategy、session summary 和授权 evidence；用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖质量不足追问策略、回答较好加深策略、跑题澄清策略、换方向策略、暂停提示、禁止生成具体追问题目、不得关闭结束条件 UNKNOWN、低置信度阻塞、禁止同题打磨逻辑和不得创建正式回流对象。
- Open Questions: 追问深度算法、压力强度调整算法、切换主题策略、暂停 / 结束条件阈值、整场节奏控制和 `P-PRESSURE-005` 具体题目生成规则仍待后续 contract / API / UX 收敛，不在本 contract 关闭。

### 13.5 Pressure 第一组 Contract 关系

- `P-PRESSURE-001` 负责压力面开场策略。
- `P-PRESSURE-002` 基于开场策略生成首题。
- `P-PRESSURE-003` 基于当前问题和用户回答生成回答质量判断。
- `P-PRESSURE-004` 基于回答质量判断选择追问策略。
- `P-PRESSURE-004` 的输出应作为 `P-PRESSURE-005` Follow-up Question Generation 的上游输入。
- 四个 contract 都必须引用 Shared Contracts，并至少交接 validation、Low Confidence、EvidenceRef、TraceRef 和 session summary update 输入。
- Pressure 第一组可以消费 Job Match 与 Polish 输出，但不依赖 RAG、互联网检索或复杂工作流引擎才能工作。
- Pressure 第一组不得直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- Pressure 第一组不得生成最终面试报告或整场评分。
- Pressure 第一组每轮结束后应为 `P-SHARED-006` Session Summary Update 提供输入。
- `P-PRESSURE-005` 至 `P-PRESSURE-009` 仍保持 Stub，等待后续阶段授权填充。
- Report / Review / Weakness / Asset / Training contracts 仍保持 Stub，等待后续阶段授权填充。

## 14. `P-PRESSURE-005` 至 `P-PRESSURE-009` Stub 摘要

以下 contract 仍保持 Stub，只同步主 catalog 摘要，后续授权前不得填充详细正文。

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-PRESSURE-005` | Follow-up Question Generation | 生成连续追问 | Stub |
| `P-PRESSURE-006` | Pace Control | 控制节奏与压力强度 | Stub |
| `P-PRESSURE-007` | End Condition Check | 判断是否结束整场 | Stub |
| `P-PRESSURE-008` | Session Score | 生成整场评分 | Stub |
| `P-PRESSURE-009` | Report Input Assembly | 组装报告输入 | Stub |
