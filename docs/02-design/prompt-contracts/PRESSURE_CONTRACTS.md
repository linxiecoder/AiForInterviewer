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
- 本文件遵守 `PROMPT_SPEC.md` §13 的 `AR-F4-FULL-001` 处置口径；复杂算法和实现细节按 deferred_non_blocking 承接。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 适用范围

本文件承载主 catalog 中 `P-PRESSURE-001` 至 `P-PRESSURE-009` 的详细 contract 正文。

## 13. Pressure Contract 细则

### 13.0 Pressure 第一组公共字段与边界

#### Pressure 第一组公共边界

Pressure 是压力面模式，不是打磨模式。Pressure 侧重真实面试节奏、连续追问、回答质量判断和面试状态推进，不允许像 Polish 一样围绕同一道题无限打磨。

Pressure 第一组只负责开场策略、首题生成、回答质量判断和追问策略选择。第一组不直接生成连续追问题目，不直接控制整场节奏，不直接判断整场结束，不生成整场评分，不生成最终面试报告，也不直接写入正式 `Weakness`、正式 `Asset` 或正式 `TrainingRecommendation`。如需产生弱项、资产、报告或训练方向，只能输出后续 contract 入口建议、候选引用或 session summary update 输入。

压力强度、追问深度和结束条件细节按后续 LATER / SHOULD 收敛；`P-PRESSURE-008` 的整场评分 contract 已冻结 0-100 产品刻度、rubric / rule version、版本字段、证据、风险、置信度、校验和 trace，不得再把评分公式或通过倾向边界作为阻断 MVP 的开放项。Pressure 第一组也不得退化为一次 LLM 调用；应用编排层必须串联 Shared Contracts、会话状态、用户动作、校验、证据绑定、trace 和持久化交接。

Pressure 第一组可以条件消费 `JobVersion`、`ResumeVersion`、`JobMatchAnalysis`、`ScoreResult` canonical score、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、Polish session summary、Polish 已问问题、Polish 诊断 / 得分 / 失分点 / 弱项候选 / 资产候选、既有 `Weakness`、已确认 `AssetVersion`、历史模拟面试报告 / 复盘、当前 Pressure session summary、最近若干 Pressure turns、RAG evidence 和公共参考材料。上述输入必须按任务最小必要裁剪，不得默认塞入全部简历、全部岗位、全部历史会话、全部资产、全部 Polish 记录、全部知识库材料或全部报告。

`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG；Job Match 和 Polish 输出是结构化上游，不是 RAG。资产库、薄弱项、历史 Polish turns、历史 Pressure turns、历史报告、复盘和知识库是条件检索来源；条件检索必须经过 `P-SHARED-002`。RAG / 知识库可用于问题素材、技术准确性和考点评估增强，但不是 Pressure 第一组 MVP 的硬依赖；互联网检索不是 MVP 默认强依赖，不得默认启用。无 RAG、无资产、无历史报告或无历史复盘时，不得阻断基础 Pressure 流程。

Pressure 第一组输出可以保存为开场策略、首题候选、回答质量判断、追问策略候选、validation result、low confidence flag、evidence refs、trace refs、session summary update 输入和 audit event。Pressure 第一组不得直接写入正式 `Weakness`、正式 `Asset`、正式 `TrainingRecommendation`、最终面试报告或整场评分。需要用户确认的 action 必须进入用户确认流。

#### Pressure 第一组公共输出 Schema（Output Schema）

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

### 13.1 `P-PRESSURE-001` 开场策略（Opening Strategy）

- Contract ID： `P-PRESSURE-001`
- 名称（Name）： Opening Strategy
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - 用户进入压力面模式。
  - 用户选择岗位 / 简历 / Job Match 结果后开始压力面。
  - 用户从 Polish 结果进入压力面。
  - 用户重新开始一场压力面。
  - 系统需要为首题生成提供策略输入。
- 目标（Goal）： 基于岗位、简历、Job Match、Polish 历史、用户目标和 session 状态生成压力面开场策略；开场策略用于确定起始范围、面试风格、重点能力、压力强度提示和首题方向，不直接生成整场题目列表。
- 必需输入（Required Inputs）：
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
- 可选输入（Optional Inputs）：
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
- 检索来源（Retrieval Sources）：
  - 默认使用岗位、简历和当前 pressure session。
  - 条件检索 Job Match、Polish summary、弱项、资产、历史报告、复盘和知识库。
  - Polish 结果是结构化上游，不是 RAG。
  - 互联网检索不默认启用。
  - 无 Polish 结果或 Job Match 结果时仍可基于岗位与简历开始压力面，但必须标记输入较弱或低置信度。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含岗位摘要、简历摘要、当前压力面目标、pressure session summary、Job Match / Polish 相关 refs 和输出 schema。
  - 不得默认塞入全部 Polish 历史、全部报告、全部资产或全部知识库材料。
  - 上下文过长时优先保留岗位核心要求、简历强相关模块、弱项候选、用户目标和禁止重复方向。
- 排除输入（Excluded Inputs）：
  - 全量 Polish 历史、全量报告、全量资产、全量知识库和无关历史会话正文。
  - 被标记为 source deleted / disabled / unavailable 的正文。
  - owner 不一致或未经授权的简历、岗位、会话、资产、弱项、报告和知识库内容。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- 输出 Schema（Output Schema）：
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
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 开场策略必须与岗位、简历或用户目标相关。
  - 不得生成整场固定题库。
  - 不得把 Polish 的同题打磨逻辑带入压力面。
  - `pressure_intensity_hint` 只是提示，不冻结压力强度算法。
  - `difficulty_hint` 只是提示，不冻结题目难度算法。
  - 不得默认启用互联网检索。
  - 不得承诺面试通过概率或准确预测真实面试结果。
  - 不得生成违法、歧视、隐私侵入或与岗位无关的面试策略。
- 低置信度规则（Low Confidence Rules）：
  - 岗位要求缺失。
  - 简历信息不足。
  - Job Match 缺失。
  - Polish 历史缺失。
  - 用户目标不清。
  - evidence 不足。
  - 历史结果低置信度。
  - 上下文高风险裁剪。
- 证据要求（Evidence Requirements）： focus area、priority、压力强度提示、难度提示、首题方向、风险标记和禁止重复方向必须绑定岗位、简历、Job Match、Polish summary、session summary 或其他授权 evidence；证据不足时必须输出低置信度或要求用户补充目标。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、开场策略生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressureSession` opening strategy 或等价会话内策略对象。
  - `PressureOpeningStrategy` candidate 或等价逻辑对象。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 开场策略可作为压力面启动配置。
  - 用户可以开始、调整方向、切换岗位 / 简历、返回 Polish 或取消。
  - 开场策略不直接创建正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- 重试 / 兜底（Retry / Fallback）：
  - `OwnerRef`、岗位版本、简历版本或 pressure session 缺失时停止正常生成，返回失败或补充材料路径。
  - Job Match、Polish 历史、资产或历史报告缺失时可降级为基于岗位和简历的基础开场策略，并输出低置信度原因。
  - 重试不得默认启用互联网检索、扩大到全量历史会话或生成整场题库。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `opening_strategy_available`、`opening_strategy_partial`、`opening_strategy_low_confidence`、`opening_strategy_validation_failed`、`user_confirmation_required` 和 `input_context_insufficient`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 开场策略只使用当前 owner 的岗位、简历、pressure session 和授权增强证据；可展示证据摘要不得包含无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖有 Job Match / Polish 上游、无 Job Match、无 Polish、用户目标不清、evidence 不足、禁止整场题库、禁止同题打磨逻辑、禁止互联网默认检索和不得创建正式回流对象。
- 开放问题（Open Questions）： 压力强度算法、题目难度算法、首题方向排序算法、输入优先级细则和整场节奏策略仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 13.2 `P-PRESSURE-002` 首题生成（First Question Generation）

- Contract ID： `P-PRESSURE-002`
- 名称（Name）： First Question Generation
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - `P-PRESSURE-001` Opening Strategy 完成后。
  - 用户确认开始压力面。
  - 用户跳过首题并请求新首题。
  - 系统需要根据开场策略启动第一轮 Pressure turn。
- 目标（Goal）： 基于开场策略、岗位、简历、Job Match / Polish 上游和 session 状态生成首题；首题用于启动真实面试节奏，不是 Polish 同题打磨题，也不是整场题目列表。
- 必需输入（Required Inputs）：
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
- 可选输入（Optional Inputs）：
  - Job Match points
  - Polish 已问问题列表
  - Pressure 已问问题列表
  - 禁止重复问题列表
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - RAG evidence
  - 公共参考材料
- 检索来源（Retrieval Sources）：
  - 默认使用开场策略、岗位、简历和 pressure session summary。
  - 条件检索 Job Match、Polish 已问问题、Pressure 已问问题、弱项、资产和知识库。
  - 知识库 / RAG 可用于题目素材增强，但不是必需输入。
  - 互联网检索不默认启用。
  - 无 RAG 时仍必须可以生成基础首题。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 opening strategy、岗位要求、简历相关模块、已问问题、禁止重复列表、当前压力面目标和输出 schema。
  - 不得默认塞入全部 Polish 历史或全部知识库材料。
  - 上下文过长时优先保留 opening strategy、禁止重复问题、岗位核心要求、简历模块和 evidence refs。
- 排除输入（Excluded Inputs）：
  - Polish 同题打磨题作为首题直接复用。
  - 整场题库、连续追问题目列表或报告评分输入。
  - 全量 Polish 历史、全量知识库、无关历史回答全文和默认互联网检索结果。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
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
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 首题必须与 opening strategy、岗位要求或简历模块相关。
  - 首题不得重复最近 Polish 或 Pressure 已问问题。
  - 首题不得直接泄露参考答案。
  - 首题不得被写成 Polish 同题打磨题。
  - `question_type` 必须使用稳定枚举或等价描述。
  - `pressure_intensity_hint` 只是提示，不冻结压力强度算法。
  - 不得生成违法、隐私侵入、歧视或与岗位无关题目。
- 低置信度规则（Low Confidence Rules）：
  - opening strategy 缺失或低置信度。
  - 岗位或简历证据不足。
  - 禁止重复列表缺失。
  - 首题与岗位 / 简历关联弱。
  - RAG evidence 不可用但题目需要知识补充。
  - 输出题目过泛。
  - 无法判断是否重复。
- 证据要求（Evidence Requirements）： 首题文本、题型、focus area、难度提示、压力强度提示、预期回答信号、岗位要求和简历模块关联必须绑定 opening strategy、岗位、简历、已问问题、禁止重复列表或授权 evidence；无法判断重复时必须低置信度。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、首题生成、去重检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、PressureTurn 初始化 handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressureQuestion` candidate 或等价会话内题目对象。
  - `PressureTurn` 初始化输入。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 生成首题可以直接进入压力面答题流程。
  - 用户可跳过、换题、暂停、退出或返回 Polish。
  - 首题生成不得直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- 重试 / 兜底（Retry / Fallback）：
  - opening strategy、岗位版本、简历版本或 pressure session 缺失时停止正常生成，返回失败或补充材料路径。
  - 已问问题或禁止重复列表缺失时可生成低置信度首题，并要求后续去重补检或用户确认。
  - RAG 不可用时降级为岗位 / 简历 / opening strategy 驱动的基础首题；不得默认启用互联网检索。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `first_question_available`、`first_question_partial`、`first_question_low_confidence`、`first_question_validation_failed`、`duplicate_risk_detected` 和 `question_skip_available`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 首题生成只使用当前 owner 的开场策略、岗位、简历、session summary 和授权增强证据；不得暴露参考答案、无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖 opening strategy 后生成、用户跳过换题、无 RAG、重复 Polish 题拦截、重复 Pressure 题拦截、题目过泛低置信度、参考答案不泄露、不得生成整场题库和不得创建正式回流对象。
- 开放问题（Open Questions）： 首题推荐排序、题型枚举全集、难度算法、压力强度算法和时间盒提示规则仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 13.3 `P-PRESSURE-003` 回答质量评估（Answer Quality Assessment）

- Contract ID： `P-PRESSURE-003`
- 名称（Name）： Answer Quality Assessment
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - 用户提交压力面当前题目的回答。
  - 用户补充回答后重新评估。
  - `P-PRESSURE-004` Follow-up Strategy 需要回答质量输入。
  - 系统需要决定继续追问、澄清、切换方向或结束后续流程。
- 目标（Goal）： 判断用户对当前压力面题目的回答是否充分、是否跑题、是否可追问、是否需要澄清、是否暴露明显风险，并为追问策略提供输入。
- 必需输入（Required Inputs）：
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
- 可选输入（Optional Inputs）：
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
- 检索来源（Retrieval Sources）：
  - 默认使用当前问题、当前回答、岗位、简历和 session summary。
  - 条件检索 opening strategy、Job Match points、Polish 诊断、历史 Pressure turns、资产、薄弱项和知识库。
  - 如果需要判断技术准确性或补充考点，可经过 `P-SHARED-002` 使用知识库 / RAG。
  - 不得默认启用互联网检索。
  - 无知识库时仍可基于题目、岗位、简历和回答进行基础质量判断，但技术准确性判断应标记证据弱或低置信度。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则；条件检索时必须继承 `P-SHARED-002`。
  - 上下文至少包含当前问题、用户回答、岗位相关要求、简历相关模块、opening strategy、最近相关 Pressure turn 和输出 schema。
  - 对长回答必须优先保留用户原始回答、问题要求、岗位证据和质量评估目标。
  - 不得默认塞入全部历史回答、全部 Polish 历史或全部知识库材料。
- 排除输入（Excluded Inputs）：
  - 用户未表达经历、事实、数据或职责作为质量判断事实。
  - 岗位不匹配结论作为用户能力缺陷的直接替代。
  - 正式 Weakness、Asset 或 TrainingRecommendation 写入指令。
  - 全量历史回答、全量 Polish 历史、全量知识库、默认互联网检索结果、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
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
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 质量判断必须基于当前问题和当前回答。
  - 不得虚构用户未表达经历。
  - 不得把岗位不匹配直接包装为用户能力缺陷。
  - 不得静默创建正式 `Weakness`。
  - 技术准确性判断如缺少知识证据，应触发低置信度。
  - `quality_level`、`sufficiency_status`、`relevance_status`、`depth_status` 等必须使用稳定枚举或等价描述。
  - `follow_up_needed` 只是策略输入，不等于已经生成追问题目。
  - `clarification_needed` 只是策略输入，不等于用户失败。
- 低置信度规则（Low Confidence Rules）：
  - 用户回答过短。
  - 用户回答明显跑题。
  - 当前问题缺失。
  - 岗位 / 简历证据不足。
  - 技术判断缺少知识证据。
  - 回答中存在自相矛盾内容。
  - 上下文裁剪影响评估。
  - 模型无法区分事实、推测和建议。
- 证据要求（Evidence Requirements）： 回答摘要、质量等级、充分性、相关性、深度、技术准确性、结构、沟通、风险信号、缺失点、模糊点和跑题片段必须绑定当前问题、用户回答、岗位要求、简历模块、知识 evidence 或 session summary；无法绑定时必须输出低置信度。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、回答质量评估、技术准确性证据检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressureAnswerQualityAssessment` 或等价会话内评估对象。
  - `PressureTurn` answer quality result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 回答质量判断可作为内部策略和必要反馈展示。
  - 派生的弱项、资产或训练方向只能作为候选或后续 contract 输入。
  - 用户可补充回答、请求澄清、暂停或继续。
- 重试 / 兜底（Retry / Fallback）：
  - 当前问题、当前回答、pressure turn、岗位版本、简历版本或 owner 校验缺失时停止正常评估，返回失败或补充材料路径。
  - 回答过短、技术证据不足或上下文裁剪影响判断时可保存低置信度评估，要求用户补充回答或降级为基础质量判断。
  - 重试不得默认启用互联网检索、虚构用户经历或创建正式 `Weakness`。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `answer_quality_available`、`answer_quality_partial`、`answer_quality_low_confidence`、`answer_quality_validation_failed`、`clarification_needed` 和 `follow_up_strategy_input_ready`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 回答质量判断只使用当前 owner 的问题、回答、岗位、简历、session summary 和授权 evidence；展示摘要不得泄露无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖充分回答、过短回答、跑题回答、技术证据缺失、当前问题缺失、回答矛盾、岗位证据不足、follow_up_needed 只作为策略输入、不得虚构用户经历和不得静默创建正式弱项。
- 开放问题（Open Questions）： 回答质量枚举全集、评分映射、技术准确性证据阈值、稳定能力缺陷判定和整场评分输入聚合仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 13.4 `P-PRESSURE-004` 追问策略（Follow-up Strategy）

- Contract ID： `P-PRESSURE-004`
- 名称（Name）： Follow-up Strategy
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - `P-PRESSURE-003` Answer Quality Assessment 完成后。
  - 用户回答质量不足、过泛、跑题、缺少细节或暴露风险。
  - 用户回答质量较好，需要加深或换方向。
  - 系统需要决定继续追问、澄清、换题、暂停或准备结束。
- 目标（Goal）： 基于当前问题、用户回答、回答质量判断、opening strategy、历史 turns 和 session summary 选择追问策略；本 contract 只选择追问策略，不生成具体追问题目，具体追问题目由后续 `P-PRESSURE-005` 负责。
- 必需输入（Required Inputs）：
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
- 可选输入（Optional Inputs）：
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
- 检索来源（Retrieval Sources）：
  - 默认使用当前问题、当前回答、质量评估、opening strategy 和 session summary。
  - 条件读取历史 Pressure turns、已问问题、禁止重复追问、Job Match / Polish 上游、弱项、资产和知识库。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG、无资产、无历史 Pressure turns 时仍可生成基础追问策略。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则；条件读取时必须继承 `P-SHARED-002`。
  - 上下文至少包含当前问题、当前回答、质量评估、opening strategy、已问问题、禁止重复追问、session summary 和输出 schema。
  - 上下文过长时优先保留当前轮质量判断、风险信号、未覆盖点、禁止重复列表和 pressure focus。
  - 不得默认塞入全部历史回答、全部 Polish 历史、全部知识库或全部资产。
- 排除输入（Excluded Inputs）：
  - 具体追问题目正文、连续追问题目列表或整场题库。
  - Polish 同题打磨建议作为 Pressure 追问策略的直接替代。
  - 单次回答不足作为稳定能力缺陷的确定事实。
  - 整场结束条件阈值、整场评分公式或正式报告生成指令。
  - 全量历史回答、全量 Polish 历史、全量知识库、全量资产、默认互联网检索结果、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
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
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 策略必须基于当前回答质量判断、当前问题、opening strategy 或 session summary。
  - 不得直接生成具体追问题目。
  - 不得把 Polish 同题打磨建议当成 Pressure 追问策略。
  - 不得把一次回答不足直接包装成稳定能力缺陷。
  - `pressure_intensity_adjustment` 只是提示，不冻结压力强度算法。
  - `follow_up_depth_hint` 只是提示，不冻结追问深度算法。
  - `pause_or_end_hint` 只是提示；完整结束阈值为 deferred_non_blocking，不改变本 contract 的策略输出边界。
  - 策略不得绕过用户暂停、退出或模式切换选择。
  - 不得生成违法、歧视、隐私侵入或攻击性策略。
- 低置信度规则（Low Confidence Rules）：
  - 回答质量判断缺失或低置信度。
  - 当前问题或回答缺失。
  - opening strategy 缺失。
  - 已问问题或禁止重复列表缺失。
  - 质量判断与 evidence 不一致。
  - 上下文裁剪影响策略选择。
  - 关键 risk signals 无法绑定证据。
  - 用户目标不清。
- 证据要求（Evidence Requirements）： 策略类型、策略原因、目标 gap、风险信号、缺失点、压力强度调整、追问深度提示、澄清、换题、暂停或稍后结束提示必须绑定回答质量判断、当前问题、当前回答、opening strategy、session summary、已问问题或授权 evidence；无法绑定时必须输出 `blocked_by_low_confidence` 或要求澄清。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、追问策略选择、重复追问约束检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、`P-PRESSURE-005` handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressureFollowUpStrategy` 或等价会话内策略对象。
  - `PressureTurn` follow-up strategy result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 追问策略可作为内部编排依据。
  - 用户可以继续、暂停、退出、切换主题或返回 Polish。
  - 本 contract 不创建正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
  - 本 contract 不生成具体追问题目；具体题目由后续 contract 生成。
- 重试 / 兜底（Retry / Fallback）：
  - 回答质量判断、当前问题、当前回答、pressure turn、岗位版本、简历版本或 owner 校验缺失时停止正常策略选择，返回失败或补充材料路径。
  - 已问问题、禁止重复追问或 evidence 不足时可保存低置信度策略，要求澄清或降级为基础策略。
  - 重试不得默认启用互联网检索、生成具体追问题目、关闭整场结束条件或创建正式回流对象。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `follow_up_strategy_available`、`follow_up_strategy_partial`、`follow_up_strategy_low_confidence`、`follow_up_strategy_validation_failed`、`blocked_by_low_confidence`、`clarification_needed` 和 `follow_up_question_generation_ready`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 追问策略只使用当前 owner 的问题、回答、质量评估、opening strategy、session summary 和授权 evidence；用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖质量不足追问策略、回答较好加深策略、跑题澄清策略、换方向策略、暂停提示、禁止生成具体追问题目、结束阈值后置、低置信度阻塞、禁止同题打磨逻辑和不得创建正式回流对象。
- 开放问题（Open Questions）： 追问深度算法、压力强度调整算法、切换主题策略、暂停 / 结束条件阈值、整场节奏控制和 `P-PRESSURE-005` 具体题目生成规则仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

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
- `P-PRESSURE-005` 至 `P-PRESSURE-009` 已在 Pressure 7B 中补充为 Draft，负责追问题目生成、节奏控制、结束判断、整场评分和报告输入组装。
- Report / Review / Weakness / Asset / Training contracts 当前均已按 `PROMPT_SPEC.md` canonical registry 进入 Draft；Pressure 第一组只向这些 domain 交接候选、建议或输入引用，不自动写正式对象，也不关闭这些 domain 的 deferred_non_blocking 细化项。

## 14. Pressure 7B Contract 细则

### 14.0 Pressure 7B 公共字段与边界

#### Pressure 7B 公共职责

Pressure 7B 只负责生成连续追问题目、控制节奏和压力强度、判断是否建议结束整场、生成整场评分，以及组装报告输入包。Pressure 7B 不生成最终面试报告正文，不生成正式复盘，不正式创建 Weakness，不正式创建 Asset，不正式创建 TrainingRecommendation；压力强度算法、追问深度算法、结束条件和 RAG / 检索实现按后续 LATER / SHOULD 收敛。整场评分和通过倾向边界由 `P-PRESSURE-008`、Report contracts、`PROMPT_SPEC.md` §7.2、`DATA_MODEL.md` 和 `API_SPEC.md` 的已冻结规则承接。

Pressure 7B 可以消费 `P-PRESSURE-001` Opening Strategy、`P-PRESSURE-002` First Question Generation、`P-PRESSURE-003` Answer Quality Assessment、`P-PRESSURE-004` Follow-up Strategy、当前问题、当前回答、最近若干 Pressure turns、已问问题列表、禁止重复追问列表、pressure session summary、Job Match 输出、Polish 输出、既有 Weakness、已确认 AssetVersion、RAG evidence 和公共参考材料。上述输入必须按任务最小必要装配，不得默认塞入全部简历、全部岗位、全部历史会话、全部 Polish 记录、全部资产、全部知识库或全部报告。

`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG。Job Match、Polish 和当前 Pressure turns 是结构化上游，不是 RAG。资产库、薄弱项、历史 Pressure turns、历史报告、复盘和知识库是条件检索来源；条件检索必须经过 `P-SHARED-002`。RAG / 知识库可以用于技术准确性、追问素材、评分解释或证据增强，但不是 7B 的硬依赖；互联网检索不是 MVP 默认强依赖，不得默认启用。无 RAG、无资产、无历史报告或无历史复盘时，不得阻断基础 Pressure 7B 流程。

Pressure 7B 输出可以保存为追问题目、节奏控制建议、结束条件判断、整场评分、报告输入包、validation result、low confidence flag、evidence refs、trace refs、session summary update 输入和 audit event。Pressure 7B 不得直接写入正式 Weakness、正式 Asset、正式 TrainingRecommendation、最终面试报告正文或真实面试复盘。`P-PRESSURE-009` 只组装报告输入，不生成报告正文；报告正文必须交给 Report contracts。

#### Pressure 7B 公共输出 Schema（Output Schema）

`P-PRESSURE-005` 至 `P-PRESSURE-009` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `pressure_session_ref` | 是 | ref | 压力面会话引用 |
| `pressure_turn_ref` | 否 | ref | 当前压力面轮次引用 |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `opening_strategy_ref` | 否 | ref | 开场策略引用 |
| `question_refs` | 否 | ref[] | 题目引用 |
| `answer_refs` | 否 | ref[] | 回答引用 |
| `answer_quality_refs` | 否 | ref[] | 回答质量判断引用 |
| `follow_up_strategy_refs` | 否 | ref[] | 追问策略引用 |
| `pace_control_refs` | 否 | ref[] | 节奏控制引用 |
| `end_condition_refs` | 否 | ref[] | 结束判断引用 |
| `session_score_refs` | 否 | ref[] | 整场评分引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的证据 |
| `displayable_evidence_summary` | 否 | object[] | 可展示证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记，必须可追溯到 `P-SHARED-004` |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 |
| `session_summary_update_ref` | 否 | ref | `P-SHARED-006` 产出的摘要更新引用 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能进入正式回流对象 |

`next_recommended_actions` 只表达建议动作或流程入口，不直接写入正式 Weakness、正式 Asset 或 TrainingRecommendation。允许值至少包括 `ask_follow_up_question`、`continue_pressure_session`、`adjust_pressure_pace`、`pause_pressure_session`、`resume_pressure_session`、`check_end_condition`、`end_pressure_session`、`generate_session_score`、`assemble_report_input`、`generate_pressure_report_later`、`mark_weakness_candidate`、`mark_asset_candidate`、`enter_polish_mode`、`generate_review_later` 和 `request_clarification`。其中需要用户确认的 action 必须进入用户确认流。

### 14.1 `P-PRESSURE-005` 追问题目生成（Follow-up Question Generation）

- Contract ID： `P-PRESSURE-005`
- 名称（Name）： Follow-up Question Generation
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - `P-PRESSURE-004` Follow-up Strategy 完成后。
  - 回答质量判断显示需要追问、澄清、加深、换方向或验证细节。
  - 用户选择继续压力面。
  - 系统需要启动下一轮 Pressure turn。
- 目标（Goal）： 基于当前问题、用户回答、回答质量判断和追问策略生成具体追问题目；本 contract 生成具体追问题目，但不决定整场节奏、不判断整场结束、不生成整场评分。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `pressure_session_ref`
  - `pressure_turn_ref`
  - 当前问题引用
  - 当前回答引用
  - `P-PRESSURE-003` Answer Quality Assessment 结果
  - `P-PRESSURE-004` Follow-up Strategy 结果
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果或显式 `retrieval_not_required`
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- 可选输入（Optional Inputs）：
  - Opening Strategy
  - First Question
  - target gaps
  - target missing points
  - risk signals
  - forbidden repeat follow-up refs
  - recent Pressure turns
  - Job Match points
  - Polish diagnosis / loss points / weakness candidates
  - 既有 Weakness
  - 已确认 AssetVersion
  - 知识库 / RAG evidence
  - 公共参考材料
- 检索来源（Retrieval Sources）：
  - 默认使用当前问题、当前回答、回答质量判断、追问策略和 session summary。
  - 条件读取历史 Pressure turns、禁止重复追问、Job Match / Polish 上游、弱项、资产和知识库。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG、无资产、无历史 Pressure turns 时仍可生成基础追问题目。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前问题、当前回答、质量判断、追问策略、target gaps、禁止重复追问、pressure focus 和输出 schema。
  - 上下文过长时优先保留当前回答、质量判断、追问目标、风险信号、禁止重复列表和 evidence refs。
  - 不得默认塞入全部历史回答、全部 Polish 历史、全部知识库或全部资产。
- 排除输入（Excluded Inputs）：
  - 追问策略文案作为最终题目直接复用。
  - Polish 同题打磨题、`same_question` 打磨循环或参考回答正文。
  - 全部历史回答、全部 Polish 历史、全部知识库、全部资产和默认互联网检索结果。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §14.0 的 Pressure 7B 公共 Output Schema。
  - `follow_up_question_id_candidate`
  - `question_text`
  - `question_type`
  - `strategy_ref`
  - `follow_up_type`
  - `target_gap_refs`
  - `target_missing_point_refs`
  - `target_risk_signal_refs`
  - `pressure_intensity_hint`
  - `follow_up_depth_hint`
  - `expected_answer_signals`
  - `anti_repeat_refs`
  - `related_job_requirements`
  - `related_resume_modules`
  - `source_refs`
  - `evidence_refs`
  - `time_box_hint`
  - `clarification_mode`
  - `next_turn_initialization_ref`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 追问题目必须基于 `P-PRESSURE-004` 的追问策略。
  - 不得直接复用 strategy 文案当作题目。
  - 不得把 Polish 同题打磨问题当成 Pressure 追问。
  - 不得重复已问问题或禁止重复追问。
  - 不得泄露参考答案。
  - 不得生成违法、歧视、隐私侵入或攻击性问题。
  - `pressure_intensity_hint` 和 `follow_up_depth_hint` 只是提示，不冻结算法。
  - 追问题目不得直接生成正式 Weakness、正式 Asset 或 TrainingRecommendation。
- 低置信度规则（Low Confidence Rules）：
  - 追问策略缺失或低置信度。
  - 当前问题或回答缺失。
  - 回答质量判断缺失或低置信度。
  - 禁止重复列表缺失。
  - target gaps 无 evidence。
  - 题目与岗位 / 简历关联弱。
  - 技术追问需要知识 evidence 但 RAG 不可用。
  - 上下文裁剪影响追问目标。
- 证据要求（Evidence Requirements）： 题目文本、追问类型、target gaps、target missing points、target risk signals、pressure intensity hint、follow-up depth hint、expected answer signals、anti-repeat 判断和下一轮初始化必须绑定当前问题、当前回答、回答质量判断、追问策略、session summary 或授权 evidence；证据不足时必须输出低置信度或要求澄清。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、追问题目生成、anti-repeat 检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、next turn initialization handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressureQuestion` follow-up candidate 或等价会话内题目对象。
  - `PressureTurn` next turn initialization input。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入。
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 追问题目可以直接进入压力面下一轮答题流程。
  - 用户可以继续、跳过、暂停、退出或返回 Polish。
  - 本 contract 不创建正式 Weakness、正式 Asset 或 TrainingRecommendation。
- 重试 / 兜底（Retry / Fallback）：
  - 当前问题、当前回答、质量判断、追问策略、岗位版本、简历版本或 owner 校验缺失时停止正常生成，返回失败或补充材料路径。
  - 禁止重复列表、target gaps 或 evidence 不足时可降级生成基础追问，并标记低置信度或要求澄清。
  - 重试不得默认启用互联网检索、复用 Polish 同题打磨题、扩大到全量知识库或创建正式回流对象。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `follow_up_question_available`、`follow_up_question_partial`、`follow_up_question_low_confidence`、`follow_up_question_validation_failed`、`blocked_by_anti_repeat`、`clarification_needed` 和 `next_turn_ready`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 追问题目只使用当前 owner 的问题、回答、策略、质量判断、session summary 和授权 evidence；用户可见摘要不得暴露无权限来源正文、参考答案、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖基于策略生成追问、禁止 strategy 原文当题、禁止 Polish same_question 复用、禁止重复追问、无 RAG 降级、RAG 不默认启用、低置信度 target gaps 和不得创建正式回流对象。
- 开放问题（Open Questions）： 追问深度算法、压力强度算法、题目排序、最大连续追问轮数和技术追问知识证据策略仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 14.2 `P-PRESSURE-006` 节奏控制（Pace Control）

- Contract ID： `P-PRESSURE-006`
- 名称（Name）： Pace Control
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - 每轮回答质量判断后。
  - 每次追问策略或追问题目生成后。
  - 连续多轮追问后。
  - 用户暂停、恢复、跳题或请求调整节奏时。
  - 系统需要决定加压、降压、保持节奏、切换方向或准备结束时。
- 目标（Goal）： 根据 opening strategy、回答质量趋势、追问策略、最近 turns、低置信度和 session summary 控制节奏与压力强度；本 contract 只生成节奏控制建议，不冻结压力强度算法，不引入复杂工作流引擎作为 MVP 前置。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `pressure_session_ref`
  - 最近若干 `PressureTurn` refs
  - Opening Strategy
  - 至少一个 Answer Quality Assessment
  - 至少一个 Follow-up Strategy 或 Follow-up Question
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- 可选输入（Optional Inputs）：
  - `P-SHARED-002` Retrieval Planning 结果
  - pressure intensity hint
  - follow-up depth hints
  - recent low confidence flags
  - user pause / resume signals
  - user stress tolerance setting 或等价用户偏好
  - Job Match points
  - Polish session summary
  - 历史模拟面试报告 / 复盘摘要
- 检索来源（Retrieval Sources）：
  - 默认使用当前 Pressure session、recent turns、answer quality trend、follow-up strategy 和 session summary。
  - 条件读取 Job Match、Polish summary、历史报告、复盘和用户偏好。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无历史报告或复盘时仍可基于当前会话控制节奏。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 recent turns、answer quality trend、current pressure intensity hint、follow-up depth hints、pause / resume signals、session summary 和输出 schema。
  - 上下文过长时优先保留最近 turns、质量趋势、压力强度变化、用户暂停信号和低置信度状态。
  - 不得默认塞入全部历史面试、全部 Polish 历史或全部报告。
- 排除输入（Excluded Inputs）：
  - 全部历史面试、全部 Polish 历史、全部报告、全量心理画像和默认互联网检索结果。
  - 过度心理压力策略、攻击性话术、歧视性推断和无证据用户压力标签。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §14.0 的 Pressure 7B 公共 Output Schema。
  - `pace_control_id_candidate`
  - `current_pace_state`
  - `recommended_pace_action`
  - `pressure_intensity_adjustment`
  - `follow_up_depth_adjustment`
  - `topic_switch_recommendation`
  - `pause_recommendation`
  - `resume_recommendation`
  - `risk_flags`
  - `stress_or_fatigue_signals`
  - `low_confidence_impact`
  - `reason`
  - `evidence_refs`
  - `next_action_requirements`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 节奏控制必须基于 recent turns、回答质量趋势、opening strategy 或用户动作。
  - 不得冻结压力强度算法。
  - 不得把单轮差回答直接当成整场失败。
  - 不得忽略用户暂停、退出或模式切换选择。
  - `pressure_intensity_adjustment` 只是建议，不是硬性算法。
  - 不得生成攻击性、歧视性或过度心理压力策略。
  - 不得直接写入正式 Weakness、正式 Asset 或 TrainingRecommendation。
- 低置信度规则（Low Confidence Rules）：
  - recent turns 不足。
  - answer quality trend 不足。
  - opening strategy 缺失。
  - 用户偏好缺失。
  - 压力强度信号不足。
  - 上下文裁剪影响趋势判断。
  - 低置信度结果占比过高。
  - 质量判断之间冲突。
- 证据要求（Evidence Requirements）： 当前节奏状态、推荐节奏动作、压力强度调整、追问深度调整、切换方向、暂停 / 恢复建议、风险标记和低置信度影响必须绑定 recent turns、质量趋势、opening strategy、用户动作、session summary 或授权 evidence；证据不足时必须输出低置信度或要求澄清。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、趋势聚合、节奏控制建议生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressurePaceControl` 或等价会话内节奏控制对象。
  - `PressureSession` pace state。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入。
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 节奏建议可作为内部编排依据。
  - 用户可以暂停、恢复、退出、切换方向或返回 Polish。
  - 本 contract 不创建正式 Weakness、正式 Asset 或 TrainingRecommendation。
- 重试 / 兜底（Retry / Fallback）：
  - pressure session、recent turns、质量判断、岗位版本、简历版本或 owner 校验缺失时停止正常节奏建议，返回失败或补充材料路径。
  - 用户偏好、历史报告或复盘缺失时可降级为基于当前会话的基础节奏建议，并标记低置信度。
  - 重试不得默认启用互联网检索、引入复杂工作流引擎、扩大到全量历史面试或创建正式回流对象。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `pace_control_available`、`pace_control_partial`、`pace_control_low_confidence`、`pace_control_validation_failed`、`pace_adjustment_recommended`、`pause_recommended`、`resume_recommended` 和 `end_check_recommended`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 节奏控制只使用当前 owner 的 pressure session、recent turns、用户动作和授权 evidence；不得推断或展示未经确认的心理健康状态，用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖加压、降压、保持节奏、切换方向、用户暂停、用户恢复、recent turns 不足、低置信度占比过高、禁止单轮失败判定整场失败和不得创建正式回流对象。
- 开放问题（Open Questions）： 压力强度算法、压力强度阈值、疲劳信号阈值、追问深度调节和节奏状态机细节仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 14.3 `P-PRESSURE-007` 结束条件检查（End Condition Check）

- Contract ID： `P-PRESSURE-007`
- 名称（Name）： End Condition Check
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - 每轮追问结束后。
  - Pace Control 建议准备结束时。
  - 用户请求结束压力面。
  - 已覆盖主要 focus areas。
  - 连续多轮低置信度或输入不足。
  - 系统需要决定继续、暂停、结束或转入评分。
- 目标（Goal）： 根据 session summary、已问问题、focus coverage、回答质量、追问状态、节奏控制和低置信度判断是否建议结束整场压力面；本 contract 只生成结束建议，不生成最终报告，完整结束阈值为 deferred_non_blocking。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `pressure_session_ref`
  - recent Pressure turns
  - session summary
  - asked questions
  - answered questions
  - Answer Quality Assessment results
  - Follow-up Strategy results
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- 可选输入（Optional Inputs）：
  - `P-SHARED-002` Retrieval Planning 结果
  - Opening Strategy
  - Pace Control result
  - focus areas coverage
  - low confidence flags
  - user requested end signal
  - user pause signal
  - Job Match points
  - Polish weakness candidates
  - historical mock interview summary
- 检索来源（Retrieval Sources）：
  - 默认使用当前 Pressure session、session summary、asked / answered questions、answer quality assessments、follow-up strategies。
  - 条件读取 opening strategy、pace control、Job Match / Polish 上游、历史模拟面试摘要。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无历史记录时仍可基于当前 session 判断是否建议结束。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 session summary、asked questions、answer quality summaries、follow-up strategies、coverage state、pace state、用户结束 / 暂停信号和输出 schema。
  - 上下文过长时优先保留当前 session 的 coverage、质量趋势、未覆盖 focus areas、用户信号和低置信度状态。
  - 不得默认塞入全部题答全文、全部 Polish 历史或全部报告。
- 排除输入（Excluded Inputs）：
  - 全部题答全文、全部 Polish 历史、全部报告、无关历史会话和默认互联网检索结果。
  - 自动结束用户会话的强制动作。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §14.0 的 Pressure 7B 公共 Output Schema。
  - `end_condition_check_id_candidate`
  - `end_recommendation`
  - `end_reason`
  - `coverage_status`
  - `remaining_focus_areas`
  - `quality_trend_summary`
  - `low_confidence_impact`
  - `user_requested_end`
  - `pause_recommended`
  - `continue_recommended`
  - `ready_for_session_score`
  - `ready_for_report_input_assembly`
  - `blocked_by_insufficient_data`
  - `next_required_action`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 结束判断必须基于当前 session evidence、coverage、质量趋势、用户信号或低置信度状态。
  - 不得把结束建议升级为自动结束或正式报告生成指令。
  - 不得把单轮回答不足直接当成整场结束依据。
  - 不得自动结束用户会话而不保留用户选择路径。
  - `ready_for_session_score` 只是状态建议，不等于已生成评分。
  - `ready_for_report_input_assembly` 只是状态建议，不等于已生成报告。
  - 不得生成最终报告正文。
  - 不得直接写入正式 Weakness、正式 Asset 或 TrainingRecommendation。
- 低置信度规则（Low Confidence Rules）：
  - session summary 缺失。
  - asked questions 缺失。
  - answer quality assessments 不足。
  - coverage 不可判断。
  - pace control 缺失。
  - 用户结束信号不明确。
  - 多个关键结果低置信度。
  - 上下文裁剪影响 coverage 判断。
- 证据要求（Evidence Requirements）： 结束建议、结束原因、coverage 状态、剩余 focus areas、质量趋势、低置信度影响、暂停 / 继续建议和评分 / 报告输入准备状态必须绑定当前 session evidence、session summary、题目、回答质量判断、追问策略、pace control、用户信号或授权 evidence；证据不足时必须输出低置信度或继续收集输入。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、coverage 聚合、结束条件判断、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressureEndConditionCheck` 或等价会话内结束判断对象。
  - `PressureSession` end state candidate。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入。
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 结束建议必须保留用户选择路径。
  - 用户可以继续、暂停、结束、生成整场评分或稍后复盘。
  - 本 contract 不生成报告正文，不创建正式 Weakness、正式 Asset 或 TrainingRecommendation。
- 重试 / 兜底（Retry / Fallback）：
  - pressure session、session summary、asked questions、质量判断、岗位版本、简历版本或 owner 校验缺失时停止正常结束判断，返回失败或补充材料路径。
  - coverage、pace control 或用户结束信号不明确时可输出低置信度判断，并建议继续、暂停或澄清。
  - 重试不得默认启用互联网检索、自动结束会话、生成报告正文或创建正式回流对象。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `end_condition_available`、`end_condition_partial`、`end_condition_low_confidence`、`end_condition_validation_failed`、`continue_recommended`、`pause_recommended`、`ready_for_session_score` 和 `ready_for_report_input_assembly`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 结束判断只使用当前 owner 的 pressure session、用户信号和授权 evidence；用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖继续、暂停、结束、用户请求结束、coverage 不足、低置信度过高、单轮差回答不结束、报告未生成状态和不得创建正式回流对象。
- 开放问题（Open Questions）： 结束条件阈值、最小题量、coverage 计算、低置信度占比阈值和自动结束策略仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 14.4 `P-PRESSURE-008` 会话评分（Session Score）

- Contract ID： `P-PRESSURE-008`
- 名称（Name）： Session Score
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - `P-PRESSURE-007` End Condition Check 显示 `ready_for_session_score`。
  - 用户结束压力面并请求整场评分。
  - 系统需要为报告输入组装提供 session score。
  - 用户重新生成整场评分。
- 目标（Goal）： 基于整场 Pressure turns、回答质量、追问过程、风险信号、coverage 和 evidence 生成 pressure session scoring candidate / draft；输出只能使用 0-100 产品评分刻度，不是精确通过概率。最终报告展示仍由 Report contracts / API / Data Model 的正式报告状态承接，但本 contract 必须提供后续正式报告所需的 `score_version`、`rubric_version` / `rule_version`、`confidence_level`、`evidence_refs`、`risk_level`、`risk_reason`、validation result 和 trace。
  - 评分 score type、默认维度、权重、公式、缺失维度处理和 F7 scoring fixture 以 `../SCORING_SPEC.md` 的 `pressure_session` 规则为 canonical；不得把 Job Match 或 Polish 单轮分直接复用为整场压力面分。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `pressure_session_ref`
  - Pressure turns
  - Answer Quality Assessment results
  - Follow-up Strategy / Question results
  - End Condition Check result 或等价结束状态
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - `ScoreRuleVersion`
  - `score_version`
  - `rubric_version` 或 `rule_version`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- 可选输入（Optional Inputs）：
  - `P-SHARED-002` Retrieval Planning 结果
  - Opening Strategy
  - Pace Control result
  - Job Match canonical score
  - Polish Round Scores
  - weakness candidates
  - asset candidates
  - RAG evidence
  - 公共评分口径
  - historical mock interview score
- 检索来源（Retrieval Sources）：
  - 默认使用当前 Pressure turns、回答质量判断、追问过程、session summary 和 end condition result。
  - 条件读取 opening strategy、pace control、Job Match / Polish 上游、公共评分口径、知识 evidence、历史评分摘要。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无公共评分口径或 RAG 时仍可按已登记 `ScoreRuleVersion` 生成基础整场 scoring candidate；证据不足、来源不可用或校验失败必须进入低置信度、partial、manual review 或 validation failed。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含整场 turns 摘要、answer quality summaries、追问链路、coverage、risk signals、end condition、评分目标、`ScoreRuleVersion`、`score_version`、`rubric_version` / `rule_version` 和输出 schema。
  - 上下文过长时优先保留每轮质量摘要、关键回答证据、追问链路、风险信号、coverage 和 validation 要求。
  - 不得默认塞入全部回答全文、全部 Polish 历史、全部知识库或全部报告。
- 排除输入（Excluded Inputs）：
  - Job Match Score 或 Polish Round Score 作为 Pressure Session Score 直接复用。
  - 精确通过概率、必过 / 必挂预测、确定性通过倾向文案和真实面试结果预测。
  - 全部回答全文、全部 Polish 历史、全部知识库、全部报告和默认互联网检索结果。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §14.0 的 Pressure 7B 公共 Output Schema。
  - `pressure_session_score_id_candidate`
  - `score_result_ref`
  - `score_value`
  - `score_scale`
  - `score_version`
  - `rubric_version` 或 `rule_version`
  - `score_type`
  - `score_explanation`
  - `dimension_scores`
  - `confidence_level`
  - `validation_status`
  - `generated_by_task_id`
  - `quality_trend_summary`
  - `coverage_summary`
  - `positive_evidence_refs`
  - `negative_evidence_refs`
  - `risk_signal_refs`
  - `risk_level`
  - `risk_reason`
  - `pass_tendency_level`
  - `low_confidence_impact`
  - `score_rule_version_ref`
  - `uncertainty_reasons`
  - `report_input_readiness`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - `score_value` 必须在 0-100 范围内。
  - `score_scale` 必须表明是 `0_100_product_scale` 产品展示刻度，不是精确通过概率。
  - `score_version`、`rubric_version` / `rule_version`、`score_rule_version_ref`、`confidence_level`、`validation_status`、`generated_by_task_id`、`risk_level`、`risk_reason`、`evidence_refs` 和 `trace_refs` 必须存在。
  - 不得输出精确通过概率。
  - 不得输出录取概率、offer 概率、通过率百分比或“你有 73% 概率通过”等等价措辞。
  - 不得输出“必过”“必挂”等确定性预测。
  - 不得把 Job Match Score 或 Polish Round Score 直接当成 Pressure Session Score。
  - 分数解释必须绑定整场题目、回答、质量判断、追问过程和 evidence。
  - 低分和高分都必须有解释。
  - 通过倾向只能使用分档表达：`low` / `medium` / `high` / `caution` / `insufficient_evidence`；低置信度、证据不足、source unavailable 或 validation failed 时不得输出确定性通过倾向，必须降级为“证据不足，无法判断倾向”或等价安全措辞。
  - `risk_level` / `risk_reason` 必须绑定 `evidence_refs`、`confidence_level`、`score_version`、`rubric_version` / `rule_version`、`validation_status` 和 `score_rule_version_ref`。
  - validation failed、评分版本缺失、rubric / rule version 缺失、evidence binding failed 或 source unavailable 时，不得落正式 `ScoreResult`，也不得把 scoring candidate 作为正式报告评分展示。
  - scoring candidate / draft 必须经过结构化 schema 校验和业务规则校验后才可进入持久化交接；未通过校验时只能进入 repair、retry、manual review 或 failure 状态。
  - `report_input_readiness` 只是报告输入准备状态，不等于报告已生成。
- 低置信度规则（Low Confidence Rules）：
  - Pressure turns 不足。
  - Answer Quality Assessment 不足。
  - End Condition 缺失或低置信度。
  - scoring evidence 不足。
  - `score_version`、`rubric_version` / `rule_version` 或 `score_rule_version_ref` 缺失。
  - 分数与解释不一致。
  - 只有分数没有解释。
  - 上下文裁剪影响评分依据。
  - 技术准确性需要知识 evidence 但 RAG 不可用。
- 证据要求（Evidence Requirements）： 分数、维度分、正向证据、负向证据、风险信号、风险等级、风险原因、质量趋势、coverage、低置信度影响、不确定性原因、`score_version`、`rubric_version` / `rule_version`、`confidence_level` 和 `validation_status` 必须绑定整场题目、回答、回答质量判断、追问链路、end condition、session summary、授权 evidence、`ScoreRuleVersion` 或 `TraceRef`；证据不足时必须输出低置信度、manual review 或 validation failed。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、评分规则版本选择、整场评分生成、风险字段生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、ScoreResult handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressureSessionScore` 或等价整场得分对象。
  - `ScoreResult` canonical score。
  - `ScoreExplanation`
  - `ScoreEvidenceLink`
  - `PressureSession` scoring state。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入。
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 整场评分可以作为压力面反馈展示。
  - 由评分派生的正式 Weakness、正式 Asset 或 TrainingRecommendation 必须进入后续候选 / 确认链路。
  - 用户可以查看报告、进入复盘、返回 Polish 或重新生成评分。
  - 本 contract 不生成最终报告正文。
- 重试 / 兜底（Retry / Fallback）：
  - pressure session、Pressure turns、质量判断、结束状态、岗位版本、简历版本或 owner 校验缺失时停止正常评分，返回失败或补充材料路径。
  - 评分版本缺失、rubric / rule version 缺失、公共评分口径缺失或证据不足时，可保存低置信度 candidate、部分可用解释或要求用户补充输入；不得落正式报告评分，不得输出确定性通过倾向。
  - 重试不得默认启用互联网检索、虚构评分公式、输出精确通过概率或创建正式回流对象。
  - API 状态映射（API State Mapping）： 只定义状态语义，包括 `session_score_available`、`session_score_partial`、`session_score_low_confidence`、`session_score_validation_failed`、`score_rule_version_missing`、`risk_evidence_missing` 和 `report_input_ready`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 整场评分只使用当前 owner 的 pressure session、评分规则引用和授权 evidence；用户可见摘要不得暴露无权限来源正文、原始 Prompt、completion、provider payload、system prompt、隐藏评分规则、内部权重细节或内部校准细节，不得包装出未验证的通过倾向。
- 测试策略（Test Strategy）： 使用 fixture 覆盖 0-100 范围、低分解释、高分解释、score version 缺失、rubric / rule version 缺失、risk_level 与 evidence_refs 同步存在、低置信度不输出确定性通过倾向、source unavailable 降级、validation failed 不落正式评分、禁止精确通过概率、禁止必过 / 必挂、禁止复用 Job Match / Polish score、无 RAG 降级、不暴露隐藏评分规则和不得创建正式回流对象。
- 开放问题（Open Questions）： 真实招聘结果长期校准、复杂算法调参、版本发布审批、运营治理流程和最终 UX 文案润色为 LATER / SHOULD；本 contract 已冻结 MVP 0-100 产品刻度、rubric / rule version、风险字段、通过倾向分档、证据、置信度、校验和禁止概率边界。

### 14.5 `P-PRESSURE-009` 报告输入装配（Report Input Assembly）

- Contract ID： `P-PRESSURE-009`
- 名称（Name）： Report Input Assembly
- 模式（Mode）： `pressure`
- 触发条件（Trigger）：
  - `P-PRESSURE-008` Session Score 完成后。
  - `P-PRESSURE-007` End Condition Check 显示 `ready_for_report_input_assembly`。
  - 用户请求生成压力面报告。
  - 系统需要把 Pressure session 交给 Report contracts。
- 目标（Goal）： 组装 Report contracts 所需输入包；本 contract 只组装报告输入，不生成报告正文，不生成报告结论，不生成通过倾向文案。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `pressure_session_ref`
  - Pressure turns
  - Opening Strategy
  - First Question and follow-up questions
  - User answers
  - Answer Quality Assessment results
  - Follow-up Strategy results
  - End Condition Check result
  - Session Score result
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
  - `P-SHARED-006` Session Summary Update 要求或现有 session summary
- 可选输入（Optional Inputs）：
  - `P-SHARED-002` Retrieval Planning 结果
  - Pace Control result
  - Job Match summary
  - Polish summary
  - weakness candidates
  - asset candidates
  - RAG evidence
  - historical report / review summaries
  - user report preferences
- 检索来源（Retrieval Sources）：
  - 默认使用当前 Pressure session、questions、answers、quality assessments、follow-up strategies、end condition、session score 和 session summary。
  - 条件读取 pace control、Job Match、Polish、weakness / asset candidates、RAG evidence、历史报告 / 复盘摘要和用户报告偏好。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG、无历史报告或无 Polish summary 时仍可组装基础报告输入包。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 session summary、questions、answers summary、answer quality summaries、follow-up chain、session score、end condition、low confidence flags、evidence refs 和输出 schema。
  - 上下文过长时优先保留结构化摘要、评分解释、关键证据、低置信度、未覆盖项和报告所需 refs。
  - 不得默认塞入全部原始回答全文、全部 Polish 历史、全部知识库或全部历史报告。
- 排除输入（Excluded Inputs）：
  - 最终报告正文、报告结论、通过倾向文案和真实面试结果预测。
  - 无权限来源正文、source deleted / disabled / unavailable 的正文和不可展示敏感原文。
  - 全部原始回答全文、全部 Polish 历史、全部知识库、全部历史报告和默认互联网检索结果。
  - 候选 Weakness / Asset 的正式写入动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §14.0 的 Pressure 7B 公共 Output Schema。
  - `report_input_package_id_candidate`
  - `report_contract_target_refs`
  - `pressure_session_summary_ref`
  - `question_answer_refs`
  - `answer_quality_refs`
  - `follow_up_chain_refs`
  - `pace_control_refs`
  - `end_condition_ref`
  - `session_score_ref`
  - `score_result_ref`
  - `evidence_bundle_refs`
  - `low_confidence_bundle`
  - `risk_signal_refs`
  - `weakness_candidate_refs`
  - `asset_candidate_refs`
  - `copyable_content_source_refs`
  - `report_generation_readiness`
  - `missing_inputs`
  - `excluded_sources`
  - `source_availability_summary`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 报告输入包必须只组装输入，不生成报告正文。
  - 不得生成通过倾向文案。
  - 不得生成最终面试结论。
  - 不得把低置信度内容包装为高置信报告依据。
  - 必须保留 source availability、evidence refs、trace refs 和 validation result refs。
  - 不得包含无权限来源正文。
  - 不得把候选 Weakness / Asset 写成正式对象。
  - `report_generation_readiness` 只是准备状态，不代表 Report 已生成。
- 低置信度规则（Low Confidence Rules）：
  - questions / answers 缺失。
  - Answer Quality results 缺失。
  - Session Score 缺失或低置信度。
  - End Condition 缺失或低置信度。
  - evidence refs 不足。
  - source unavailable。
  - 关键输入被裁剪。
  - 用户报告偏好缺失但被要求使用。
  - report input package 不完整。
- 证据要求（Evidence Requirements）： 报告输入包中的 session summary、题答引用、质量判断、追问链路、节奏控制、结束判断、评分、风险信号、候选 Weakness / Asset、可复制内容来源和 excluded sources 必须绑定 source refs、evidence refs、validation result refs 和 trace refs；证据不足或来源不可用时必须保留低置信度和 source availability。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、报告输入组装、source availability 聚合、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Report contract handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PressureReportInputPackage` 或等价报告输入包对象。
  - `ReportInputAssembly` trace。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入。
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 用户可以确认生成报告、稍后生成报告、进入复盘或返回 Polish。
  - 本 contract 不生成报告正文。
  - 本 contract 不创建正式 Weakness、正式 Asset 或 TrainingRecommendation。
  - Report contracts 后续负责正式报告生成、分项解释、风险提示和可复制内容组装。
- 重试 / 兜底（Retry / Fallback）：
  - pressure session、questions / answers、质量判断、结束状态、整场评分、岗位版本、简历版本或 owner 校验缺失时停止正常报告输入组装，返回失败或补充材料路径。
  - 用户报告偏好、RAG、历史报告或 Polish summary 缺失时可组装基础输入包，并标记缺失输入、excluded sources 和低置信度。
  - 重试不得默认启用互联网检索、生成报告正文、生成通过倾向文案或创建正式回流对象。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `report_input_available`、`report_input_partial`、`report_input_low_confidence`、`report_input_validation_failed`、`report_generation_ready` 和 `report_generation_blocked_by_missing_inputs`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 报告输入包只包含当前 owner 的授权 refs、摘要和可展示证据摘要；不得包含无权限来源正文、原始 Prompt、completion 或 provider payload，不得绕过用户确认写入候选回流对象。
- 测试策略（Test Strategy）： 使用 fixture 覆盖完整输入包、缺少 session score、缺少 end condition、source unavailable、低置信度 bundle、禁止生成报告正文、禁止通过倾向文案、禁止正式 Weakness / Asset 写入、无 RAG 降级和 Report handoff。
- 开放问题（Open Questions）： Report contracts 的正式报告结构、分项解释、风险提示、通过倾向表达、复制内容结构和报告生成 readiness 阈值仍待后续授权填充，为 deferred_non_blocking。

### 14.6 Pressure 7B Contract 关系

- `P-PRESSURE-001` 负责压力面开场策略。
- `P-PRESSURE-002` 基于开场策略生成首题。
- `P-PRESSURE-003` 基于当前问题和用户回答生成回答质量判断。
- `P-PRESSURE-004` 基于回答质量判断选择追问策略。
- `P-PRESSURE-005` 基于追问策略生成具体追问题目。
- `P-PRESSURE-006` 基于最近 turns、质量趋势和策略输出控制节奏。
- `P-PRESSURE-007` 基于 session summary、coverage、质量趋势和用户信号判断是否建议结束。
- `P-PRESSURE-008` 基于整场 turns、质量判断、追问链路和证据生成整场评分。
- `P-PRESSURE-009` 基于整场结构化结果组装报告输入包。
- Pressure `P-PRESSURE-001` 至 `P-PRESSURE-009` 都必须引用 Shared Contracts，并至少交接 validation、Low Confidence、EvidenceRef、TraceRef 和 session summary update 输入。
- `P-PRESSURE-009` 的输出是 Report contracts 的上游输入，不是报告正文。
- Pressure `P-PRESSURE-001` 至 `P-PRESSURE-009` 不得直接写入正式 Weakness、正式 Asset 或 TrainingRecommendation。
- Pressure `P-PRESSURE-001` 至 `P-PRESSURE-009` 不直接关闭压力强度、追问深度、结束条件或 RAG 实现的复杂策略；这些内容按 LATER / SHOULD 后续收敛。整场评分和通过倾向边界已由 `P-PRESSURE-008` 与 Report handoff 的版本、证据、风险、置信度和校验字段承接。
- Report / Review / Weakness / Asset / Training contracts 当前均已按 `PROMPT_SPEC.md` canonical registry 进入 Draft；Pressure 7B 只向这些 domain 交接报告输入、候选、建议或引用，不生成报告正文、不自动写正式对象，也不关闭这些 domain 的 deferred_non_blocking 细化项。
