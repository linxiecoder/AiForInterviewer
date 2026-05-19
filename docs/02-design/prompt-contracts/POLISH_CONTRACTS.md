---
title: POLISH_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/polish-contracts
---

# POLISH_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件遵守 `PROMPT_SPEC.md` §13 的 `AR-F4-FULL-001` 处置口径；复杂算法和实现细节按 deferred_non_blocking 承接。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 适用范围

本文件承载主 catalog 中 `P-POLISH-001` 至 `P-POLISH-011` 的详细 contract 正文，包括 Polish 通用 Schema 索引（Polish Common Schema Index）、公共字段与边界、各 contract 细则和 Polish Contract 关系。

## 12. Polish Contract 细则

本节填充打磨模式主链路的 AI 子任务 contract。Polish contracts 只定义主题规划、题目生成或选择、回答诊断、每轮 0-100 得分、反馈解释链路和回流候选链路的输入输出、检索依赖、上下文装配、校验、低置信度、证据、trace、持久化交接和安全边界；不写完整生产 Prompt 文案，不暴露隐藏评分规则、完整内部权重表、复杂阈值、内部校准细节、模型供应商、模型参数、RAG 实现、API endpoint 或物理数据库 schema。`P-POLISH-004` 的 MVP 评分 contract 已冻结 0-100 产品刻度、rubric / rule version、版本字段、证据、置信度、校验和 trace；真实招聘结果长期校准和复杂调参为 LATER / SHOULD。

### 12.0 打磨模式通用 Schema 索引（Polish Common Schema Index）

Polish 001-004、005-008、009-011 分别处于不同生命周期阶段，公共字段差异是生命周期差异，不是 contract 冲突。

| Contract 范围 | 生命周期阶段 | 公共字段差异说明 |
|---|---|---|
| `P-POLISH-001` 至 `P-POLISH-004` | 规划、出题、诊断、评分 | 以主题、题目、回答诊断和本轮评分为核心，可包含 topic / question / diagnosis / score 相关专属字段。 |
| `P-POLISH-005` 至 `P-POLISH-008` | 反馈解释、参考回答、考点、技术原理 | 以当前题目、当前回答、诊断、得分、失分点和解释证据为核心，可包含 loss point / reference answer / knowledge point / principle 相关专属字段。 |
| `P-POLISH-009` 至 `P-POLISH-011` | 下一步建议、资产候选、薄弱项候选 | 以回流候选和用户确认为核心，可包含 asset candidate / weakness candidate / merge suggestion 相关专属字段。 |

三组公共 schema 都必须保留以下核心通用字段：`status`、`contract_id`、`polish_session_ref`、`source_refs`、`source_availability`、`evidence_refs`、`displayable_evidence_summary`、`low_confidence_flags`、`validation_result_ref`、`trace_refs`、`session_summary_update_ref`、`next_recommended_actions`、`user_confirmation_required`。生命周期相关字段可以不同，但不得语义冲突；后续 `API_SPEC` 可以基于本 index 收敛统一 response envelope，本任务不定义 API endpoint。

#### 打磨进展树运行时 LLM task_type

进展树生成属于 `P-POLISH-001` 主题规划链路的运行时拆分，不新增新的 `P-POLISH-*` contract ID。当前实现登记两个 LLM task_type：

| task_type | prompt version | schema id | 输入上下文 | 输出 | 失败状态 |
|---|---|---|---|---|---|
| `polish_progress_tree_plan` | `polish_progress_tree_plan_prompt_v1` | `llm_progress_tree_plan_v1` | `job_snapshot`、`resume_snapshot`、`match_context`、`weakness_context`、`asset_context`、session topic / custom target | `ProgressTreePlan`、initial `ProgressTreeState` | `insufficient_context`、`failed` |
| `polish_progress_tree_state` | `polish_progress_tree_state_prompt_v1` | `llm_progress_tree_state_v1` | existing plan、existing state、`job_snapshot`、`resume_snapshot`、turns、feedback | refreshed `ProgressTreeState` | `refresh_failed` |

进展树 prompt 必须基于岗位版本内容、简历版本内容、岗位匹配分析、薄弱项、资产摘要和历史 turns；岗位名、公司名、简历名只用于展示或弱提示，不能作为主要语义依据。`polish_progress_tree_state` 只刷新状态，不重建 plan nodes，不删除已有 `node_ref`，`current_priority` 必须引用 existing plan 中存在的节点。provider adapter 只承载通用 JSON transport、provider request / response parse 和错误处理，不维护进展树业务 prompt 正文。

#### `next_recommended_actions` 统一枚举索引

`next_recommended_actions` 统一表达建议动作或用户动作入口，不直接写入正式 `Weakness`、正式 `Asset` 或正式 `TrainingRecommendation`。`confirm_*`、`edit_*`、`skip_*` 和 `merge_*` 类动作必须进入用户确认流；`enter_pressure_mode` 只能作为入口建议，不得自动切换模式；`generate_review_later` 只能作为后续复盘入口建议，不得生成正式 `Review`。

| Action | 适用阶段 | 语义 | 是否直接写入正式对象 | 是否需要用户确认 |
|---|---|---|---|---|
| `answer_again` | 001-011 | 用户围绕当前题目再次作答。 | 否 | 否 |
| `continue_same_question` | 001-011 | 继续同一道题的打磨。 | 否 | 否 |
| `switch_topic` | 001-011 | 切换到另一个打磨主题。 | 否 | 否 |
| `generate_next_question` | 001-011 | 生成或选择下一道打磨题。 | 否 | 否 |
| `generate_reference_answer` | 001-011 | 进入参考回答生成。 | 否 | 否 |
| `explain_knowledge_point` | 001-011 | 进入考点解析。 | 否 | 否 |
| `expand_technical_principle` | 001-011 | 进入技术原理扩展。 | 否 | 否 |
| `mark_weakness_candidate` | 001-008 | 标记可能进入薄弱项候选链路的入口。 | 否 | 是 |
| `mark_asset_candidate` | 001-008 | 标记可能进入资产候选链路的入口。 | 否 | 是 |
| `generate_next_round_suggestion` | 005-011 | 生成下一轮打磨建议。 | 否 | 否 |
| `confirm_asset_candidate` | 009-011 | 请求用户确认资产候选。 | 否 | 是 |
| `edit_asset_candidate` | 009-011 | 请求用户编辑资产候选。 | 否 | 是 |
| `skip_asset_candidate` | 009-011 | 请求用户跳过资产候选。 | 否 | 是 |
| `confirm_weakness_candidate` | 009-011 | 请求用户确认薄弱项候选。 | 否 | 是 |
| `edit_weakness_candidate` | 009-011 | 请求用户编辑薄弱项候选。 | 否 | 是 |
| `skip_weakness_candidate` | 009-011 | 请求用户跳过薄弱项候选。 | 否 | 是 |
| `merge_weakness_candidate` | 009-011 | 请求用户确认候选薄弱项合并。 | 否 | 是 |
| `enter_pressure_mode` | 001-011 | 建议进入压力面入口。 | 否 | 是 |
| `generate_review_later` | 001-011 | 建议后续进入复盘入口。 | 否 | 否 |
| `provide_more_answer_detail` | 001-008 | 请求用户补充当前回答细节。 | 否 | 是 |
| `provide_more_resume_evidence` | 001-011 | 请求用户补充简历或经历证据。 | 否 | 是 |
| `skip_current_question` | 001-011 | 用户跳过当前题。 | 否 | 是 |

### 12.1 Polish 第一组公共字段与边界

#### 模式边界

- Polish 是打磨模式，不是压力面模式；允许用户围绕同一题多轮改进。
- Polish 第一组可以给出诊断、评分、改进方向和后续建议，但不生成最终面试报告。
- Polish 第一组不生成正式薄弱项、正式资产或正式训练计划。
- Polish 第一组不负责连续压力追问、整场压力评分或压力面节奏控制。
- 同题打磨结束建议阈值属于下一轮题目策略问题，按 LATER / SHOULD 后续收敛；不得影响 `P-POLISH-004` 已冻结的评分、证据、版本、置信度、校验和低置信度降级口径。
- 四个 contract 都必须引用 Shared Contracts，默认按 `P-SHARED-002`、`P-SHARED-005` Input Evidence Selection、`P-SHARED-001`、业务生成、`P-SHARED-005` Output Evidence Binding、`P-SHARED-003`、`P-SHARED-004`、`P-SHARED-006` 和持久化 / 用户确认链路交接。

#### 上游输入边界

Polish 第一组可以条件消费 `JobMatchAnalysis`、`ScoreResult` canonical score、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、`Weakness` candidate refs、`JobVersion`、`ResumeVersion`、derived `ResumeMarkdownOutline` / Markdown 位置范围、`PolishTopicRef`、`PolishSubtopicRef`、`AssetVersion`、`Weakness`、`SessionSummary`、最近若干轮 Polish turns、当前题目、当前用户回答、RAG evidence 和公共参考材料。

这些输入不得默认全部进入上下文：不得默认塞入全部简历、全部岗位、全部历史会话、全部资产或全部知识库材料。`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG；Job Match 结果是结构化上游，不是 RAG。

`PolishTopicRef` / `PolishSubtopicRef` 来自 API 受控选项，只用于上下文装配、题目生成和 trace；它们不是正式业务对象，也不产生独立 CRUD。`custom_topic_text` 是用户输入标签，必须经过长度限制、敏感信息裁剪和 prompt injection 防护；不得把其中的命令式文本当作系统指令。

#### 检索边界

- 默认基础流程只要求岗位、简历、当前打磨会话和必要 session summary。
- 资产库、薄弱项、历史 Polish turns、Job Match 结果、历史报告 / 复盘摘要和知识库都是条件检索来源。
- RAG / 知识库可用于考点、技术原理或参考依据增强，但不是 Polish 第一组 MVP 的硬依赖。
- 互联网检索不是 MVP 默认强依赖，不得默认启用。
- 条件检索必须经过 `P-SHARED-002`，并沿用 owner / source availability / evidence / trace 过滤规则。
- 无 RAG、无资产、无历史报告、无历史复盘时不得阻断基础 Polish 流程；需要时应输出低置信度或资料不足状态。

#### Polish 第一组输出 Schema（Output Schema）公共字段

四个 Polish 第一组 contract 的 Output Schema 都必须包含以下公共字段；各 contract 可增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `polish_session_ref` | 是 | ref | 打磨会话引用 |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `job_match_refs` | 否 | ref[] | 被消费的岗位匹配结果引用 |
| `turn_refs` | 否 | ref[] | 被消费的打磨轮次引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性聚合状态；底层来源状态仍沿用 §6.1 的 `source_*` 枚举 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的 `EvidenceRef` |
| `displayable_evidence_summary` | 否 | object[] | 可展示证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记，必须可追溯到 `P-SHARED-004` |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 `TraceRef` |
| `session_summary_update_ref` | 否 | ref | `P-SHARED-006` 产出的摘要更新引用 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议，允许值见本节下方 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能回流正式对象 |

`next_recommended_actions` 只表达建议动作，不直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。允许值至少包括 `answer_again`、`generate_reference_answer`、`explain_knowledge_point`、`expand_technical_principle`、`continue_same_question`、`switch_topic`、`generate_next_question`、`mark_weakness_candidate`、`mark_asset_candidate`、`enter_pressure_mode`、`generate_review_later`、`provide_more_answer_detail`、`provide_more_resume_evidence` 和 `skip_current_question`。其中需要用户确认的动作必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。

#### 输出和持久化边界

Polish 第一组输出可以保存为题目规划候选、打磨题目、回答诊断、每轮得分、validation result、low confidence flag、evidence refs、trace refs 和 session summary update 输入。

Polish 第一组不得直接写入正式 `Weakness`、正式 `Asset`、正式 `TrainingRecommendation`、最终面试报告或压力面整场评分。如需要产生弱项、资产、失分点、参考答案、知识点解析、技术原理扩展或训练方向，只能输出候选引用、后续 contract 入口建议或用户确认入口。

### 12.2 `P-POLISH-001` 主题规划（Topic Planning）

- Contract ID： `P-POLISH-001`
- 名称（Name）： Topic Planning
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - 用户进入打磨模式。
  - 用户选择岗位、简历或 Job Match 结果后开始打磨。
  - 用户完成一轮打磨后请求下一主题。
  - `SessionSummary` 显示当前主题已完成、需要切换或存在未完成主题。
  - 用户手动选择关注方向。
- 目标（Goal）： 规划当前或下一组打磨主题，决定本轮应围绕哪些岗位要求、简历 Markdown 片段 / derived outline、匹配缺口、薄弱项候选或用户目标展开；不生成正式训练计划；同题打磨结束建议的长期调参仅为 LATER / SHOULD，不在本 contract 冻结为自动关闭条件。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
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
  - 已确认 `AssetVersion`
  - 既有 `Weakness`
  - `Weakness` candidate refs
  - 最近若干轮 Polish turns
  - 历史报告 / 复盘摘要
  - 公共参考材料
  - 知识库 / RAG evidence
- 检索来源（Retrieval Sources）：
  - 默认使用 `JobVersion`、`ResumeVersion` 和当前 `SessionSummary`。
  - 条件检索 Job Match 结果、资产、薄弱项、历史打磨轮次、报告、复盘和知识库。
  - Job Match 结果是结构化上游，不是 RAG；`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG。
  - 知识库 / RAG 只作为考点或背景依据增强，不作为基础主题规划的硬依赖。
  - 互联网检索不默认启用。
  - 无 Job Match 结果时可以基于岗位与简历直接规划主题，但必须标记输入较弱、`job_match_refs` 为空或触发低置信度。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的 owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含岗位摘要、简历摘要、当前打磨目标、session summary、已问主题、禁止重复主题、Job Match 相关 refs 和输出 schema。
  - 不得默认塞入全部历史会话、全部资产、全部复盘或全部知识库材料。
  - 上下文过长时优先保留当前目标、未完成主题、mismatch / improvement points、用户显式选择方向、禁止重复列表和输出 schema。
- 排除输入（Excluded Inputs）：
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 未经用户确认的资产候选、薄弱项候选或训练建议作为已确认事实。
  - 全量无关历史会话、全量资产库、无关知识库材料、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
  - 默认互联网检索结果和无法形成 `EvidenceRef` 的材料。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.1 的 Polish 第一组公共字段。
  - `topic_plan_id_candidate`
  - `topic_candidates`
  - 每个 topic 的 `topic_id_candidate`
  - 每个 topic 的 `title`
  - 每个 topic 的 `focus_area`
  - 每个 topic 的 `source_type`
  - 每个 topic 的 `source_refs`
  - 每个 topic 的 `evidence_refs`
  - 每个 topic 的 `priority`
  - 每个 topic 的 `difficulty_hint`
  - 每个 topic 的 `reason`
  - 每个 topic 的 `related_job_requirements`
  - 每个 topic 的 `related_resume_outline_refs`
  - 每个 topic 的 `related_match_or_mismatch_refs`
  - `selected_topic_ref`，可包含 `PolishTopicRef`、`PolishSubtopicRef` 和安全处理后的 `custom_topic_text_summary`
  - `forbidden_repeat_topics`
  - `topic_ordering`
  - `max_topics_hint`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 每个 topic 必须绑定岗位要求、简历 Markdown 片段 / derived outline 或 Job Match evidence。
  - 主题不得完全脱离岗位与简历。
  - 主题不得重复最近已完成主题，除非明确是同题继续打磨或用户手动选择重复。
  - `difficulty_hint` 只能是建议，不冻结题目难度算法。
  - `max_topics_hint` 是展示和成本控制提示，不冻结最终算法。
  - 不得把 topic candidate 直接写成正式训练计划、正式薄弱项或正式资产。
- 低置信度规则（Low Confidence Rules）：
  - 无 Job Match 结果。
  - 岗位要求过短或模糊。
  - 简历 Markdown 片段或 derived outline 不足。
  - session summary 缺失。
  - evidence 不足。
  - 已问主题无法确认。
  - 用户目标过泛。
  - 上下文高风险裁剪。
  - 低置信度分类必须交给 `P-SHARED-004` 消费 validation、retrieval、context 和 evidence failure signals，不在本 contract 重复定义公共分类枚举。
- 证据要求（Evidence Requirements）： 每个 topic 的来源、优先级原因、岗位要求、简历 Markdown 片段 / derived outline 和 Job Match 引用必须绑定 `EvidenceRef`、`SourceRef`、`VersionRef` / `SnapshotRef`；证据不足时必须输出 `evidence_missing` 或等价低置信度标记。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、主题生成或选择、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PolishSession` topic plan candidate 或等价会话内结果。
  - `selected_topic_ref` / `PolishTopicRef` / `PolishSubtopicRef` 会话内引用；不得写成正式业务对象。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 用户可以接受、切换、跳过或手动选择 topic。
  - topic plan 不直接创建正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
  - 如果后续根据 topic 派生弱项或资产，必须进入对应候选 / 确认链路。
- 重试 / 兜底（Retry / Fallback）：
  - 必需版本缺失、owner mismatch 或 session 不可访问时停止正常生成，返回失败或补充材料路径。
  - Job Match 不存在、历史主题不可确认或 RAG 为空时可保存低置信度主题候选，不阻断基础打磨。
  - 重试不得扩大输入范围、默认启用互联网检索或记录原始 Prompt / completion。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `topic_plan_available`、`topic_plan_partial`、`topic_plan_low_confidence`、`topic_plan_validation_failed`、`insufficient_input`、`anti_repeat_unknown` 和 `source_unavailable`；endpoint 与 request / response schema 以 `API_SPEC.md` 的 `GET /api/v1/polish-topics` 和 `CreatePolishSessionRequest` 为准。
- 安全说明（Security Notes）： 所有输入必须通过 owner / scope 校验和最小必要裁剪；`custom_topic_text` 必须进行 prompt injection 防护和指令中和；前端只可见结构化主题候选、状态、可展示证据摘要和必要 trace id，不暴露原始 Prompt、completion、provider payload 或无权限来源正文。
- 测试策略（Test Strategy）： 使用确定性 fixture 覆盖有 Job Match、无 Job Match、岗位模糊、简历 Markdown 片段不足、session summary 缺失、重复主题、用户手动选择方向、invalid topic/subtopic、cross-owner binding、custom topic injection 文本、RAG 为空、上下文高风险裁剪和不得写入正式训练计划。
- 开放问题（Open Questions）： 主题排序算法、主题数量上限、同题打磨结束建议阈值和 topic 与后续训练计划的映射仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。进展树初始生成和状态刷新已按 `polish_progress_tree_plan` / `polish_progress_tree_state` runtime task_type 登记，后续只保留节点推荐策略细化为 deferred_non_blocking。

### 12.3 `P-POLISH-002` 题目生成（Question Generation）

- Contract ID： `P-POLISH-002`
- 名称（Name）： Question Generation
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - `P-POLISH-001` 选定 topic 后。
  - 用户请求生成题目。
  - 用户跳过当前题目并请求新题。
  - 用户要求继续同一主题但换题。
  - `SessionSummary` 显示需要补充某类题目。
- 目标（Goal）： 基于选定主题、岗位、简历、Job Match 结果、session summary 和必要证据生成或选择打磨题目；不生成完整参考答案，不冻结题目推荐算法。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `selected_topic_ref` 或等价 topic context；可包含 `PolishTopicRef`、`PolishSubtopicRef` 和安全处理后的 `custom_topic_text_summary`
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
  - `MismatchPoint`
  - `ImprovementPoint`
  - `MatchPoint`
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 最近若干轮 Polish turns
  - 已问问题列表
  - 禁止重复问题列表
  - 公共参考材料
  - 知识库 / RAG evidence
- 检索来源（Retrieval Sources）：
  - 默认使用 selected topic、`JobVersion`、`ResumeVersion` 和 `SessionSummary`。
  - 条件检索 Job Match points、资产、薄弱项、历史题目和知识库。
  - 知识库 / RAG 可用于考点覆盖或题目素材增强，不是必需输入。
  - 互联网检索不默认启用。
  - 无 RAG 时仍必须可以生成基础题目；如技术原理题缺少知识证据，应传递低置信度或资料不足状态。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含 selected topic、岗位要求、简历 Markdown 相关片段 / derived outline、已问问题、禁止重复列表、当前打磨目标和输出 schema。
  - 不得默认塞入全部知识库材料、全部历史会话、全部资产或全部弱项。
  - 上下文过长时优先保留 selected topic、禁止重复问题、相关岗位要求、简历 Markdown 片段 / derived outline、evidence refs 和输出 schema。
- 排除输入（Excluded Inputs）：
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 完整参考答案、未校验知识库原文、无 evidence ref 的题目素材。
  - 无关历史问答全文、全量资产库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
  - 默认互联网检索结果、违法或隐私侵入材料。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.1 的 Polish 第一组公共字段。
  - `question_id_candidate`
  - `topic_ref`
  - `question_text`
  - `question_type`
  - `difficulty_hint`
  - `expected_focus_points`
  - `related_job_requirements`
  - `related_resume_outline_refs`
  - `source_refs`
  - `evidence_refs`
  - `anti_repeat_refs`
  - `answer_guidance_visibility`
  - `time_box_hint`
  - `follow_up_allowed`
  - `same_question_polish_allowed`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 题目必须与 selected topic、岗位要求或简历 Markdown 片段 / derived outline 有关。
  - 题目不得重复最近已问问题；无法判断重复时必须触发低置信度。
  - 题目不得直接泄露完整参考答案。
  - `difficulty_hint` 只是建议，不冻结题目推荐算法。
  - `question_type` 必须使用稳定枚举，例如 `experience` / `project_deep_dive` / `technical_principle` / `scenario` / `behavioral` / `system_design` / `coding_discussion` 或后续等价枚举。
  - `answer_guidance_visibility` 必须区分用户答题前是否展示提示。
  - 不得生成违法、隐私侵入或与岗位无关题目。
- 低置信度规则（Low Confidence Rules）：
  - selected topic 缺失。
  - 岗位或简历证据不足。
  - 禁止重复列表缺失。
  - 题目与岗位 / 简历关联弱。
  - RAG evidence 不可用但题目需要知识补充。
  - 输出题目过泛。
  - 无法判断是否重复。
  - 上下文高风险裁剪。
- 证据要求（Evidence Requirements）： 题目、预期考察点、岗位要求、简历 Markdown 片段 / derived outline 和去重依据必须绑定 `EvidenceRef` 或 `anti_repeat_refs`；缺少证据时不得伪装成高置信题目。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、题目生成或选择、去重检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PolishQuestion` candidate 或等价会话内题目对象。
  - `PolishTurn` 初始化输入。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 生成题目可以直接进入答题流程。
  - 用户可跳过、换题、继续同主题或切换主题。
  - 题目生成不得直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- 重试 / 兜底（Retry / Fallback）：
  - selected topic 缺失、owner mismatch 或必需版本缺失时停止正常生成，返回失败或补充材料路径。
  - RAG 为空、历史题目不可确认或题目过泛时可重试、降级为基础题目或要求用户补充方向。
  - 重试不得默认启用互联网检索、扩大到全量历史会话或泄露完整参考答案。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `question_available`、`question_partial`、`question_low_confidence`、`question_validation_failed`、`duplicate_risk`、`topic_missing` 和 `source_unavailable`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 题目生成只使用当前 owner 的必要岗位、简历、topic、session summary 和已授权增强材料；日志不记录原始 Prompt、completion、provider payload 或隐私正文。
- 测试策略（Test Strategy）： 使用 fixture 覆盖有 topic、无 topic、禁止重复列表缺失、重复题、无 RAG、技术题缺证据、过泛题、答题前提示可见性、违法 / 隐私题拒绝和题目不转正式弱项 / 资产 / 训练建议。
- 开放问题（Open Questions）： 题目推荐算法、难度排序、题目数量控制、time box 默认值和后续题目 API 字段仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。进展树 plan/state prompt contract 已登记，题目如何利用 `current_priority.progress_node_ref` 深挖仍按后续策略细化处理。

### 12.4 `P-POLISH-003` 回答诊断（Answer Diagnosis）

- Contract ID： `P-POLISH-003`
- 名称（Name）： Answer Diagnosis
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - 用户提交当前题目的回答。
  - 用户修改回答后重新诊断。
  - 用户请求解释回答问题。
  - `P-POLISH-004` 评分前需要诊断输入。
- 目标（Goal）： 诊断用户对当前题目的回答，输出结构化反馈、优点、不足、缺失信息、追问线索和后续评分输入；不静默创建正式薄弱项、资产或训练建议。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `PolishQuestion` 或当前题目引用
  - 用户当前回答
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
  - selected topic
  - Job Match points
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 最近若干轮回答
  - 题目相关知识库 / RAG evidence
  - 公共参考材料
- 检索来源（Retrieval Sources）：
  - 默认使用当前题目、当前回答、`JobVersion`、`ResumeVersion` 和 `SessionSummary`。
  - 条件检索 Job Match points、资产、薄弱项、知识库和历史回答。
  - 如果需要判断技术准确性或补充考点，可经过 `P-SHARED-002` 使用知识库 / RAG。
  - 不得默认启用互联网检索。
  - 无知识库时仍可基于题目、岗位、简历和回答进行基础诊断；技术原理类判断应标记证据弱或低置信度。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、裁剪、omitted refs 和 trace 规则；条件检索时必须继承 `P-SHARED-002`。
  - 上下文至少包含当前题目、用户回答、岗位相关要求、简历相关模块、selected topic、最近相关 turn 和输出 schema。
  - 对长回答必须优先保留用户原始回答、问题要求、岗位证据和诊断目标。
  - 不得默认塞入全部历史回答、全部知识库材料、全部资产或全部薄弱项。
- 排除输入（Excluded Inputs）：
  - 用户未表达的经历、无证据的能力判断、未确认候选对象作为正式事实。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 无关历史回答全文、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
  - 默认互联网检索结果和无法形成 `EvidenceRef` 的技术断言。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.1 的 Polish 第一组公共字段。
  - `diagnosis_id_candidate`
  - `question_ref`
  - `answer_ref`
  - `answer_summary`
  - `strengths`
  - `weaknesses`
  - `missing_points`
  - `unclear_points`
  - `off_topic_segments`
  - `technical_accuracy_notes`
  - `structure_notes`
  - `communication_notes`
  - `evidence_refs`
  - `score_input_refs`
  - `suggested_follow_up_questions`
  - `candidate_loss_points`
  - `candidate_improvement_actions`
  - `requires_user_clarification`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 诊断必须基于当前题目和当前回答。
  - 不得把用户未表达的经历虚构为事实。
  - 不得把岗位不匹配直接包装为用户能力缺陷。
  - 不得静默创建正式 `Weakness`。
  - 技术准确性判断如缺少知识证据，应触发低置信度。
  - 诊断输出必须能作为 `P-POLISH-004` 的评分输入。
  - `suggested_follow_up_questions` 只是候选，不等同于压力面连续追问。
- 低置信度规则（Low Confidence Rules）：
  - 用户回答过短。
  - 用户回答明显跑题。
  - 当前题目缺失。
  - 岗位 / 简历证据不足。
  - 技术判断缺少知识证据。
  - 回答中存在自相矛盾内容。
  - 上下文裁剪影响诊断。
  - 模型无法区分事实、推测和建议。
  - 诊断输出无法绑定证据或无法作为评分输入。
- 证据要求（Evidence Requirements）： strengths、weaknesses、missing points、technical accuracy notes、candidate loss points 和 improvement actions 必须绑定当前题目、当前回答、岗位 / 简历 evidence 或知识库 `EvidenceRef`；证据不足时必须显式标记。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖 Context Assembly、条件 Retrieval Planning、Input Evidence Selection、回答诊断、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PolishAnswerDiagnosis` 或等价会话内诊断对象。
  - `PolishTurn` 诊断结果。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 诊断结果可作为本轮反馈展示。
  - 派生的弱项、资产或训练方向只能作为候选或后续 contract 输入。
  - 用户可补充回答、重新诊断或继续评分。
- 重试 / 兜底（Retry / Fallback）：
  - 当前题目或当前回答缺失、owner mismatch 或必需版本缺失时停止正常诊断，返回失败或补充材料路径。
  - 回答过短、证据不足或技术判断缺证据时可保存低置信度诊断、要求用户补充回答或跳过技术准确性判断。
  - 重试不得默认启用互联网检索、虚构用户经历或把建议写成事实。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `diagnosis_available`、`diagnosis_partial`、`diagnosis_low_confidence`、`diagnosis_validation_failed`、`answer_too_short`、`clarification_required` 和 `technical_evidence_missing`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 诊断只使用当前 owner 的题目、回答、岗位、简历和授权增强证据；可展示结果不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖正常回答、过短回答、跑题回答、题目缺失、岗位 / 简历证据不足、技术判断缺 RAG、回答自相矛盾、虚构经历防护、岗位不匹配不包装成能力缺陷和不静默创建正式 `Weakness`。
- 开放问题（Open Questions）： 失分点归因细则、参考答案生成、考点解析、技术原理扩展、压力面追问策略和正式弱项候选生成仍交给后续 Polish / Pressure / Weakness contracts，为 deferred_non_blocking。

### 12.5 `P-POLISH-004` 单轮评分（Round Score）

- Contract ID： `P-POLISH-004`
- 名称（Name）： Round Score
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - `P-POLISH-003` 完成回答诊断后。
  - 用户提交回答并请求评分。
  - 用户修改回答后重新评分。
  - 系统需要决定是否建议继续同题打磨。
- 目标（Goal）： 基于当前题目、用户回答和诊断结果生成每轮 0-100 产品评分 candidate / draft 与解释；本 contract 只输出单轮 polish scoring candidate，不直接生成通过倾向或整场风险提示，不直接形成最终报告评分。其输出必须提供后续 report / review / scoring 汇总所需的 `score_version`、`rubric_version` / `rule_version`、证据、置信度、校验结果和 trace。
  - 评分 score type、默认维度、权重、公式、缺失维度处理和 F7 scoring fixture 以 `../SCORING_SPEC.md` 的 `polish_answer` 规则为 canonical；打磨报告总评分必须使用 `polish_report`，不得直接复用本轮回答分。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - 当前题目引用
  - 用户当前回答引用
  - `P-POLISH-003` Answer Diagnosis 结果或等价诊断输入
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
  - `JobMatchAnalysis`
  - `ScoreResult` canonical score from Job Match
  - selected topic
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 历史同题打磨轮次
  - 知识库 / RAG evidence
  - 公共评分口径
- 检索来源（Retrieval Sources）：
  - 默认使用当前题目、当前回答、回答诊断、`JobVersion`、`ResumeVersion` 和 `SessionSummary`。
  - 条件读取 Job Match canonical score、历史同题轮次、公共评分口径和知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG 或公共评分口径时仍可按已登记 `ScoreRuleVersion` 生成基础评分 candidate；证据不足、来源不可用或校验失败必须进入低置信度、partial、manual review 或 validation failed。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、裁剪、omitted refs 和 trace 规则；条件读取时必须继承 `P-SHARED-002`。
  - 上下文至少包含当前题目、用户回答、诊断结果、岗位要求、简历相关模块、评分目标、`ScoreRuleVersion`、`score_version`、`rubric_version` / `rule_version` 和输出 schema。
  - 上下文过长时优先保留当前题目、当前回答、诊断结果、评分证据、输出 schema 和 validation 要求。
  - 不得默认塞入全部历史回答、全部资产、全部知识库或全部复盘。
- 排除输入（Excluded Inputs）：
  - LLM 单次输出临时发明的评分公式、权重、阈值或校准方法。
  - 精确通过概率、录取概率、offer 概率、通过率百分比或等价措辞。
  - 隐藏评分规则、完整内部权重表、校准样例正文、系统 Prompt 或内部校准细节。
  - Job Match 分数作为本轮回答分的直接替代。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 无关历史回答全文、全量资产、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.1 的 Polish 第一组公共字段。
  - `round_score_ref`
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
  - `positive_evidence_refs`
  - `negative_evidence_refs`
  - `diagnosis_refs`
  - `loss_point_candidate_refs`
  - `improvement_action_refs`
  - `score_rule_version_ref`
  - `risk_level=not_applicable`
  - `risk_reason=not_applicable`
  - `pass_tendency_level=not_applicable`
  - `uncertainty_reasons`
  - `same_question_continue_hint`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - `score_value` 必须在 0-100 范围内。
  - `score_scale` 必须表明是 `0_100_product_scale` 产品展示刻度，不是精确通过概率。
  - `score_version`、`rubric_version` / `rule_version`、`score_rule_version_ref`、`confidence_level`、`validation_status`、`generated_by_task_id`、`evidence_refs` 和 `trace_refs` 必须存在。
  - 不得输出精确通过概率。
  - 不得输出录取概率、offer 概率、通过率百分比或“你有 73% 概率通过”等等价措辞。
  - 不得输出“必过”“必挂”等确定性预测。
  - 不得把岗位匹配分直接当成本轮回答分。
  - 分数解释必须绑定当前题目、当前回答和诊断证据。
  - 低分和高分都必须有解释。
  - `P-POLISH-004` 不直接生成通过倾向；如后续汇总需要通过倾向，只能由 report / job match / review 相关 contract 按分档表达承接。低置信度、证据不足、source unavailable 或 validation failed 时，后续消费方必须降级为“证据不足，无法判断倾向”或等价安全措辞。
  - validation failed、评分版本缺失、rubric / rule version 缺失、evidence binding failed 或 source unavailable 时，不得落正式 `ScoreResult`，也不得把 scoring candidate 作为正式报告评分展示。
  - scoring candidate / draft 必须经过结构化 schema 校验和业务规则校验后才可进入持久化交接；未通过校验时只能进入 repair、retry、manual review 或 failure 状态。
  - `same_question_continue_hint` 只是建议，不影响本 contract 已冻结的评分版本、rubric / rule version、证据、置信度和校验口径；同题结束建议策略按 LATER / SHOULD 后续收敛。
- 低置信度规则（Low Confidence Rules）：
  - 用户回答过短。
  - 诊断结果缺失或低置信度。
  - 当前题目缺失。
  - `score_version`、`rubric_version` / `rule_version` 或 `score_rule_version_ref` 缺失。
  - 证据不足。
  - 分数与解释不一致。
  - 只有分数没有解释。
  - 上下文裁剪影响评分依据。
  - 技术准确性需要知识证据但 RAG 不可用。
- 证据要求（Evidence Requirements）： `score_explanation`、正向证据、负向证据、dimension scores、诊断引用、失分点候选、改进动作、`score_version`、`rubric_version` / `rule_version`、`confidence_level` 和 `validation_status` 必须绑定当前题目、当前回答、诊断结果、`EvidenceRef`、`ScoreRuleVersion` 和 `TraceRef`；证据不足时必须进入低置信度、manual review 或 validation failed。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖 Context Assembly、条件 Retrieval Planning、Input Evidence Selection、评分生成、评分规则引用、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- `canonical` score 关系:
  - `ScoreResult` 是统一评分承载对象，保存 score value、score type、explanation、rule version、evidence refs、validation result 和 trace refs。
  - `PolishRoundScore` 是打磨轮次场景下的视图、引用或领域包装，用于从 `PolishTurn` 指向对应 `ScoreResult`。
  - 不允许 `ScoreResult` 与 `PolishRoundScore` 分别保存两份不一致的分数、解释或证据。
  - Job Match canonical score 可作为上游参考，但不得直接替代本轮回答分。
  - 历史回看、校准和报告复用应引用 canonical score。
- 持久化目标（Persistence Targets）：
  - `PolishRoundScore` 或等价会话内得分对象。
  - `ScoreResult` canonical score。
  - `ScoreExplanation`
  - `ScoreEvidenceLink`
  - `PolishTurn` scoring result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 本轮得分可直接作为打磨反馈展示。
  - 由得分派生的正式 `Weakness`、`Asset` 或 `TrainingRecommendation` 必须进入后续候选 / 确认链路。
  - 用户可以重新回答、继续同题打磨、换题或进入后续解释 / 参考答案 contract。
- 重试 / 兜底（Retry / Fallback）：
  - 分数越界、缺少解释、缺 evidence refs 或诊断引用缺失时进入 repair / retry / validation failed。
  - 评分版本缺失、rubric / rule version 缺失、证据不足或 RAG 不可用时可保存低置信度 candidate、部分可用解释或要求用户补充回答；不得落正式报告评分，不得输出确定性通过倾向。
  - 重试不得默认启用互联网检索、虚构评分公式或把 Job Match 分数当成本轮回答分。
  - API 状态映射（API State Mapping）： 只定义状态语义，包括 `round_score_available`、`round_score_partial`、`round_score_low_confidence`、`round_score_validation_failed`、`score_rule_version_missing`、`score_out_of_range`、`evidence_missing` 和 `same_question_continue_suggested`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 评分上下文只能包含当前 owner 的题目、回答、诊断、岗位、简历、证据和授权增强材料；日志不得记录原始 Prompt、completion、provider payload、隐藏评分规则、内部权重细节、内部校准细节或隐私正文；前端只可见结构化分数、解释、状态、可展示证据摘要和必要 trace id。
- 测试策略（Test Strategy）： 使用 fixture 覆盖 0、100、中间分、分数越界、只有分数无解释、解释无证据、诊断缺失、score version 缺失、rubric / rule version 缺失、Job Match 分数不可直接复用、本轮高分 / 低分均有解释、低置信度不产生确定性通过倾向、不得输出精确通过概率、不得暴露隐藏评分规则和 same question continue hint 不自动结束同题策略。
- 开放问题（Open Questions）：
  - 真实招聘结果长期校准、复杂算法调参、版本发布审批和运营治理流程为 LATER / SHOULD，不阻断 MVP。
  - 同题打磨结束建议策略仍由后续 Polish / UX / F7 收敛；不得重新打开评分、通过倾向或风险提示边界。

### 12.6 `P-POLISH-005` 失分点分析（Loss Point Analysis）

#### Polish 6A 公共边界

Polish 6A 只负责反馈解释链路：失分点分析、参考回答、考点解析和技术原理扩展。6A 不负责下一轮建议、正式资产候选生成、正式薄弱项候选生成、训练计划生成、压力面追问、最终面试报告或真实面试复盘；不暴露隐藏评分规则、完整内部权重表、复杂阈值或内部校准细节。题目推荐算法和同题结束建议策略为后续 Polish / UX / F7 收敛项，不影响 `P-POLISH-004` 已冻结的评分版本、证据、置信度和校验口径。

Polish 6A 可以消费 `P-POLISH-001` 至 `P-POLISH-004` 的输出、当前题目、当前用户回答、当前诊断、当前本轮得分、Job Match 输出、`ScoreResult` canonical score、`MatchPoint` / `MismatchPoint` / `ImprovementPoint`、既有 `Weakness`、已确认 `AssetVersion`、RAG evidence、公共参考材料、session summary 和最近若干轮 Polish turns。上述输入必须按任务最小必要裁剪，不得默认塞入全部简历、全部岗位、全部历史会话、全部资产、全部知识库材料或全部复盘。

`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG；当前题目、当前回答、诊断和评分是 Polish 6A 的核心输入。资产库、薄弱项、历史 Polish turns、Job Match 结果、公共参考材料和知识库是条件检索来源；条件检索必须经过 `P-SHARED-002`。RAG / 知识库可以用于考点、技术原理、参考回答和技术准确性增强，但不是 6A 的硬依赖；互联网检索不是 MVP 默认强依赖，不得默认启用。无 RAG、无资产、无历史报告或无历史复盘时不得阻断基础 6A 流程；技术原理、考点解析或参考答案缺少知识证据时必须进入 Low Confidence 表达，不得伪造确定结论。

Polish 6A 输出可以保存为失分点候选、参考回答、考点解析、技术原理扩展、validation result、low confidence flag、EvidenceRef、TraceRef 和 session summary update 输入。Polish 6A 不得直接写入正式 `Weakness`、正式 `Asset`、正式 `TrainingRecommendation`、最终面试报告或压力面整场评分；需要产生弱项、资产或训练方向时，只能输出候选引用、后续 contract 入口建议或非写入动作。

#### Polish 6A 公共输出 Schema（Output Schema）

`P-POLISH-005` 至 `P-POLISH-008` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `polish_session_ref` | 是 | ref | 打磨会话引用 |
| `polish_turn_ref` | 是 | ref | 当前打磨轮次引用 |
| `question_ref` | 是 | ref | 当前题目引用 |
| `answer_ref` | 是 | ref | 当前回答引用 |
| `diagnosis_refs` | 否 | ref[] | 回答诊断引用 |
| `round_score_refs` | 否 | ref[] | 本轮得分引用 |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性聚合状态；底层来源状态仍沿用 §6.1 的 `source_*` 枚举 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的 `EvidenceRef` |
| `displayable_evidence_summary` | 否 | object[] | 可展示证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记，必须可追溯到 `P-SHARED-004` |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 `TraceRef` |
| `session_summary_update_ref` | 否 | ref | `P-SHARED-006` 产出的摘要更新引用 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能回流正式对象 |

`next_recommended_actions` 只表达建议动作，不直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。允许值至少包括 `answer_again`、`generate_reference_answer`、`explain_knowledge_point`、`expand_technical_principle`、`continue_same_question`、`switch_topic`、`generate_next_question`、`mark_weakness_candidate`、`mark_asset_candidate`、`generate_next_round_suggestion`、`provide_more_answer_detail`、`provide_more_resume_evidence` 和 `skip_current_question`。其中需要用户确认的 action 必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。

- Contract ID： `P-POLISH-005`
- 名称（Name）： Loss Point Analysis
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - `P-POLISH-003` Answer Diagnosis 完成后。
  - `P-POLISH-004` Round Score 完成后。
  - 用户请求查看本轮失分原因。
  - 用户修改回答后请求重新分析失分点。
  - 系统需要为参考回答、下一轮建议、弱项候选或资产候选提供输入。
- 目标（Goal）： 基于当前题目、用户回答、回答诊断和本轮得分生成结构化失分点；失分点只作为本轮反馈和后续候选输入，不直接写入正式 `Weakness` 或 `TrainingRecommendation`。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `polish_turn_ref`
  - 当前题目引用
  - 当前用户回答引用
  - `P-POLISH-003` Answer Diagnosis 结果
  - `P-POLISH-004` Round Score 结果或等价评分输入
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
  - selected topic
  - Job Match points
  - `ScoreResult` canonical score
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - 历史同题打磨轮次
  - 知识库 / RAG evidence
  - 公共评分口径
- 检索来源（Retrieval Sources）：
  - 默认使用当前题目、当前回答、诊断和本轮得分。
  - 条件读取 Job Match points、历史同题打磨轮次、既有 `Weakness`、已确认资产、公共评分口径和知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG 或公共评分口径时仍可生成基础失分点；技术准确性或知识性失分应标记低置信度。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前题目、当前回答、诊断结果、本轮得分、评分解释、岗位相关要求、简历相关模块和输出 schema。
  - 上下文过长时优先保留当前回答、诊断中的 missing points / weaknesses、本轮得分解释、负向证据和 validation 要求。
  - 不得默认塞入全部历史回答、全部资产、全部知识库或全部复盘。
- 排除输入（Excluded Inputs）：
  - 岗位匹配缺口作为本轮回答失分点的直接替代。
  - 用户未表达的经历、未确认候选对象作为正式事实、单次输出临时发明评分公式、权重、阈值或精确通过概率。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 无关历史回答全文、全量资产、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含本小节 Polish 6A 公共 Output Schema。
  - `loss_point_analysis_id_candidate`
  - `loss_points`
  - 每个 loss point 的 `loss_point_id_candidate`
  - 每个 loss point 的 `title`
  - 每个 loss point 的 `description`
  - 每个 loss point 的 `loss_type`
  - 每个 loss point 的 `severity_hint`
  - 每个 loss point 的 `score_impact_hint`
  - 每个 loss point 的 `source_diagnosis_refs`
  - 每个 loss point 的 `source_score_refs`
  - 每个 loss point 的 `evidence_refs`
  - 每个 loss point 的 `related_question_requirements`
  - 每个 loss point 的 `related_job_requirements`
  - 每个 loss point 的 `related_resume_outline_refs`
  - 每个 loss point 的 `suggested_repair_direction`
  - `loss_point_ordering`
  - `max_loss_points_hint`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 每个失分点必须基于当前题目、当前回答、诊断或评分解释。
  - 不得把岗位匹配缺口直接当成本轮回答失分点。
  - 不得把用户未表达的经历虚构为失分原因。
  - 技术准确性类失分若缺少知识证据，应触发低置信度。
  - `severity_hint` 和 `score_impact_hint` 只是提示，不冻结评分算法。
  - `max_loss_points_hint` 是展示和成本控制提示，不冻结最终算法。
  - 失分点不得直接写入正式 `Weakness` 或 `TrainingRecommendation`。
- 低置信度规则（Low Confidence Rules）：
  - 诊断结果缺失。
  - 本轮得分缺失或低置信度。
  - 用户回答过短。
  - 题目要求不清。
  - 失分点无法绑定当前回答。
  - 技术判断缺少知识证据。
  - 分数解释和诊断不一致。
  - 上下文裁剪影响失分归因。
- 证据要求（Evidence Requirements）： 每个失分点的标题、描述、严重程度提示、影响提示和修复方向必须绑定当前题目、当前回答、诊断、评分解释或知识库 `EvidenceRef`；无法绑定时不得生成高置信失分点。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、失分点生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PolishLossPointAnalysis` 或等价会话内分析对象。
  - `LossPoint` candidate 或等价逻辑对象。
  - `PolishTurn` loss point result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 失分点可作为本轮反馈展示。
  - 派生正式 `Weakness`、`Asset` 或 `TrainingRecommendation` 必须进入后续候选 / 确认链路。
  - 用户可接受、忽略、补充回答或重新生成失分点。
- 重试 / 兜底（Retry / Fallback）：
  - 当前题目、当前回答、诊断或评分输入缺失时停止正常生成，返回失败或补充材料路径。
  - 诊断低置信度、评分低置信度、证据不足或技术判断缺证据时可保存低置信度失分点或要求用户补充回答。
  - 重试不得默认启用互联网检索、扩大到全量历史会话或虚构评分公式。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `loss_points_available`、`loss_points_partial`、`loss_points_low_confidence`、`loss_points_validation_failed`、`diagnosis_missing`、`score_missing` 和 `technical_evidence_missing`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 失分点分析只使用当前 owner 的题目、回答、诊断、评分、岗位、简历和授权增强证据；可展示结果不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖正常失分归因、诊断缺失、评分缺失、回答过短、岗位匹配缺口不转本轮失分、虚构经历防护、技术判断缺证据、分数解释和诊断不一致、上下文裁剪和不写入正式弱项 / 训练建议。
- 开放问题（Open Questions）： 失分点排序算法、严重程度映射、score impact 计算、展示数量上限、弱项候选生成和训练方向生成仍交给后续 Polish / Weakness / Training contracts，为 deferred_non_blocking。

### 12.7 `P-POLISH-006` 参考回答（Reference Answer）

- Contract ID： `P-POLISH-006`
- 名称（Name）： Reference Answer
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - 用户完成当前回答并请求参考回答。
  - `P-POLISH-003` Answer Diagnosis 完成后。
  - `P-POLISH-005` Loss Point Analysis 完成后。
  - 用户要求基于自己的回答生成改进版。
  - 用户要求查看更结构化、更贴近岗位的表达示例。
- 目标（Goal）： 基于当前题目、岗位、简历、用户回答、诊断和失分点生成参考回答，供用户学习和自我修正；不得伪装成用户真实经历，不得在用户答题前泄露完整答案。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `polish_turn_ref`
  - 当前题目引用
  - 当前用户回答引用
  - `P-POLISH-003` Answer Diagnosis 结果
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
  - `P-POLISH-005` Loss Point Analysis 结果
  - selected topic
  - expected focus points
  - Job Match points
  - 已确认 `AssetVersion`
  - 既有 `Weakness`
  - 知识库 / RAG evidence
  - 公共参考材料
  - 历史同题打磨轮次
- 检索来源（Retrieval Sources）：
  - 默认使用当前题目、当前回答、诊断、岗位、简历和 session summary。
  - 条件读取失分点、Job Match points、已确认资产、历史同题轮次、公共参考材料和知识库 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - RAG / 公共材料可用于技术准确性和表达结构增强，但不是必需输入。
  - 互联网检索不默认启用。
  - 无 RAG 时仍可生成基础参考回答；涉及技术事实时必须标记知识证据弱或低置信度。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前题目、当前回答、诊断、岗位相关要求、简历相关模块、允许使用的用户事实和输出 schema。
  - 对项目经历类题目，必须区分“用户已提供事实”和“建议表达结构”。
  - 不得默认塞入全部简历、全部资产或全部历史回答。
  - 上下文过长时优先保留当前回答、题目要求、用户事实、岗位要求、失分点和 evidence refs。
- 排除输入（Excluded Inputs）：
  - 用户未提供的经历、数据、项目、成果或职责作为事实。
  - 答题前自动展示完整参考答案。
  - 未确认候选资产作为正式事实、owner 不一致或 source unavailable 的正文。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.6 的 Polish 6A 公共 Output Schema。
  - `reference_answer_id_candidate`
  - `answer_style`
  - `reference_answer`
  - `answer_outline`
  - `key_points_covered`
  - `improvements_over_user_answer`
  - `reference_answer_loss_point_mappings`
  - 每个 mapping 的 `loss_point_ref`
  - 每个 mapping 的 `reference_answer_segment_ref`
  - 每个 mapping 的 `covered_issue`
  - 每个 mapping 的 `repair_strategy`
  - 每个 mapping 的 `evidence_refs`
  - 每个 mapping 的 `confidence`
  - 每个 mapping 的 `user_edit_required`
  - 未覆盖高优先级 loss point 时必须给出 `uncovered_reason`
  - `facts_used_from_user`
  - `facts_not_assumed`
  - `evidence_refs`
  - `risk_flags`
  - `adaptation_notes`
  - `user_edit_required`
  - `visibility_policy`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 参考回答必须回答当前题目。
  - 不得虚构用户未提供的经历、数据、项目、成果或职责。
  - 对用户未提供的信息必须使用占位、建议补充或低置信度表达。
  - 不得在用户答题前自动展示完整参考答案。
  - 技术内容缺少知识证据时必须触发低置信度。
  - `reference_answer_loss_point_mappings` 必须说明参考回答中的段落、要点或表达改进分别修复哪些失分点。
  - 每个高优先级 loss point 应至少被参考回答覆盖，或在 mapping 中明确标记未覆盖原因。
  - 映射不得虚构用户事实，也不得把用户未确认经历包装成已发生事实。
  - 如果某段参考回答依赖用户未确认事实，必须标记 `user_edit_required` 或低置信度。
  - 技术性修复缺少知识 evidence 时必须低置信度，不得生成高置信修复映射。
  - 该映射字段只服务前端展示、测试断言和后续 Polish contract 消费，不代表正式 `Asset`、正式 `Weakness` 或正式训练计划。
  - 参考回答不得承诺面试通过结果或精确通过概率。
  - 参考回答不得直接写入正式 `Asset`，除非后续 Asset Candidate contract 和用户确认完成。
  - `answer_style` 必须使用稳定枚举或等价描述，例如 `concise` / `structured` / `star` / `technical_deep_dive` / `project_story`。
- 低置信度规则（Low Confidence Rules）：
  - 用户回答过短。
  - 用户事实不足。
  - 当前题目不清。
  - 简历证据不足。
  - 技术知识证据不足。
  - 参考回答需要假设用户经历。
  - RAG evidence 缺失但题目要求技术准确性。
  - 输出和用户事实存在冲突。
- 证据要求（Evidence Requirements）： `reference_answer`、关键覆盖点、改进点、`reference_answer_loss_point_mappings` 和使用的用户事实必须绑定当前题目、当前回答、诊断、失分点、简历 / 岗位 evidence 或知识库 `EvidenceRef`；`facts_not_assumed` 必须列出未被当作事实使用的信息边界。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、参考回答生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PolishReferenceAnswer` 或等价会话内参考回答对象。
  - `PolishTurn` reference answer result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 参考回答可以展示给用户。
  - 参考回答不得自动变成正式 `Asset`。
  - 用户可复制、编辑、重新生成或选择后续进入 Asset Candidate contract。
  - 如果用户选择归档为资产，必须进入 `P-POLISH-010` 或等价资产候选 / 确认链路。
- 重试 / 兜底（Retry / Fallback）：
  - 当前题目、当前回答、诊断或必需版本缺失时停止正常生成，返回失败或补充材料路径。
  - 用户事实不足、技术证据不足或输出和用户事实冲突时可保存低置信度参考回答、要求用户补充事实或降级为结构化答题提纲。
  - 重试不得默认启用互联网检索、虚构用户经历或把参考回答直接写入资产。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `reference_answer_available`、`reference_answer_partial`、`reference_answer_low_confidence`、`reference_answer_validation_failed`、`user_facts_insufficient` 和 `visibility_restricted`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 参考回答只使用当前 owner 的题目、回答、诊断、岗位、简历、已确认资产和授权证据；前端展示必须遵守 `visibility_policy`，日志不得记录原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖正常参考回答、用户事实不足、项目经历占位、答题前不展示完整答案、参考回答与失分点映射覆盖、未覆盖高优先级失分点原因、技术证据缺失、事实冲突、不得承诺面试通过、不得直接写入正式资产和用户选择进入资产候选链路。
- 开放问题（Open Questions）： 参考回答风格默认值、展示时机细则、资产候选质量判断和资产合并规则仍交给后续 Polish / Asset contracts，为 deferred_non_blocking。

### 12.8 `P-POLISH-007` 考点解析（Knowledge Point Explanation）

- Contract ID： `P-POLISH-007`
- 名称（Name）： Knowledge Point Explanation
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - 用户请求解释题目考点。
  - `P-POLISH-002` 生成题目后需要展示考察方向。
  - `P-POLISH-003` 诊断后需要解释回答问题。
  - `P-POLISH-005` 失分点分析后需要解释失分对应考点。
  - 用户请求了解“这题到底考什么”。
- 目标（Goal）： 基于当前题目、用户回答、诊断、失分点和必要知识证据生成考点解析；考点解析用于解释题目考察点、回答评价依据和知识盲区，不等同于完整技术原理扩展。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `polish_turn_ref`
  - 当前题目引用
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
  - 当前用户回答
  - `P-POLISH-003` Answer Diagnosis 结果
  - `P-POLISH-005` Loss Point Analysis 结果
  - `P-POLISH-006` Reference Answer 结果
  - expected focus points
  - Job Match points
  - 知识库 / RAG evidence
  - 公共参考材料
  - 已确认 `AssetVersion`
  - 既有 `Weakness`
- 检索来源（Retrieval Sources）：
  - 默认使用当前题目、岗位、简历和 expected focus points。
  - 条件读取当前回答、诊断、失分点、参考回答、Job Match points、知识库 / RAG evidence 和公共参考材料。
  - 技术性考点或准确性判断优先使用知识库 / 公共材料 evidence；但 RAG 不是 MVP 硬依赖。
  - 无 RAG 时可以输出基础考点解析，但必须标记知识证据弱或低置信度。
  - 互联网检索不默认启用。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前题目、题目类型、岗位相关要求、expected focus points 和输出 schema。
  - 如果要解释用户回答问题，应包含当前回答、诊断和失分点。
  - 如果要解释技术考点，应包含知识 evidence 或低置信度标记。
  - 不得默认塞入全部知识库、全部历史回答或全部资产。
- 排除输入（Excluded Inputs）：
  - 与当前题目或岗位要求无关的百科材料。
  - 用户未回答内容作为用户错误事实。
  - 未确认候选对象作为正式事实、owner 不一致或 source unavailable 的正文。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.6 的 Polish 6A 公共 Output Schema。
  - `knowledge_explanation_id_candidate`
  - `examined_knowledge_points`
  - 每个 knowledge point 的 `knowledge_point_id_candidate`
  - 每个 knowledge point 的 `title`
  - 每个 knowledge point 的 `description`
  - 每个 knowledge point 的 `why_it_matters`
  - 每个 knowledge point 的 `expected_answer_signals`
  - 每个 knowledge point 的 `common_mistakes`
  - 每个 knowledge point 的 `related_loss_point_refs`
  - 每个 knowledge point 的 `related_job_requirements`
  - 每个 knowledge point 的 `evidence_refs`
  - `knowledge_depth_hint`
  - `prerequisite_notes`
  - `not_covered_scope`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 考点必须与当前题目或岗位要求相关。
  - 不得把考点解析扩展成无边界百科讲解。
  - 技术性考点必须绑定知识 evidence 或触发低置信度。
  - 不得把用户未回答内容当成用户错误事实。
  - `knowledge_depth_hint` 是解释深度提示，不冻结课程体系。
  - 考点解析不得直接写入正式 `Weakness` 或 `TrainingRecommendation`。
  - 如果知识证据不足，应明确说明影响范围。
- 低置信度规则（Low Confidence Rules）：
  - 当前题目过泛。
  - expected focus points 缺失。
  - 技术知识证据不足。
  - RAG unavailable。
  - 诊断或失分点低置信度。
  - 岗位要求和题目关联弱。
  - 输出考点无法绑定 evidence。
  - 上下文裁剪影响考点解释。
- 证据要求（Evidence Requirements）： 每个考点的标题、描述、考察意义、预期回答信号和常见误区必须绑定当前题目、岗位要求、诊断、失分点或知识库 `EvidenceRef`；知识证据不足时必须输出受影响范围和低置信度标记。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、考点解析生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PolishKnowledgePointExplanation` 或等价会话内考点解析对象。
  - `KnowledgePoint` candidate 或等价逻辑对象。
  - `PolishTurn` knowledge explanation result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 考点解析可以展示给用户。
  - 考点解析不得自动创建正式 `Weakness` 或 `TrainingRecommendation`。
  - 用户可继续请求技术原理扩展、参考回答或重新回答。
- 重试 / 兜底（Retry / Fallback）：
  - 当前题目、岗位版本或简历版本缺失时停止正常生成，返回失败或补充材料路径。
  - expected focus points 缺失、RAG 不可用或题目过泛时可保存低置信度考点解析、降级为基础解释或要求用户补充问题范围。
  - 重试不得默认启用互联网检索、扩大为全量知识库讲解或把考点解析写入正式弱项 / 训练建议。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `knowledge_explanation_available`、`knowledge_explanation_partial`、`knowledge_explanation_low_confidence`、`knowledge_explanation_validation_failed`、`expected_focus_missing` 和 `knowledge_evidence_missing`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 考点解析只使用当前 owner 的题目、回答、诊断、岗位、简历和授权证据；可展示 evidence summary 不等于原始敏感正文，日志不得记录原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖正常考点解析、题目过泛、expected focus 缺失、无 RAG、诊断低置信度、岗位关联弱、无边界百科化防护、用户未答内容不当作错误和不写入正式弱项 / 训练建议。
- 开放问题（Open Questions）： 考点粒度、深度默认值、知识体系映射和训练建议生成仍交给后续 contract / API / UX 收敛，为 deferred_non_blocking。

### 12.9 `P-POLISH-008` 技术原理扩展（Technical Principle Expansion）

- Contract ID： `P-POLISH-008`
- 名称（Name）： Technical Principle Expansion
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - 用户请求展开技术原理。
  - `P-POLISH-007` Knowledge Point Explanation 完成后。
  - `P-POLISH-003` 诊断发现技术准确性问题。
  - `P-POLISH-005` 失分点涉及技术原理缺失。
  - 用户请求“讲深一点”“底层原理是什么”“为什么这么答”。
- 目标（Goal）： 基于题目、考点、诊断、失分点和知识证据扩展技术原理，帮助用户理解底层机制、原理、对比、边界条件和面试表达方式；不等同于参考答案，也不等同于完整课程内容。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `polish_turn_ref`
  - 当前题目引用
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
  - `P-POLISH-007` Knowledge Point Explanation 结果
  - `P-POLISH-003` Answer Diagnosis 结果
  - `P-POLISH-005` Loss Point Analysis 结果
  - 当前用户回答
  - 知识库 / RAG evidence
  - 公共参考材料
  - Job Match points
  - 已确认 `AssetVersion`
  - 既有 `Weakness`
- 检索来源（Retrieval Sources）：
  - 默认使用当前题目、考点解析、岗位和简历上下文。
  - 条件读取诊断、失分点、当前回答、知识库 / RAG evidence、公共参考材料和已确认资产。
  - 技术原理扩展优先使用知识库 / 公共材料 evidence；但 RAG 不是 MVP 硬依赖。
  - 无知识 evidence 时，可以输出低置信度、有限深度解释或建议补充知识材料，不得伪造确定技术事实。
  - 互联网检索不默认启用。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前题目、相关考点、用户技术准确性问题、岗位技术要求和输出 schema。
  - 如果引用知识库，必须包含 evidence refs、版本或 chunk refs。
  - 不得默认塞入全部知识库材料、全部历史问答或全部资产。
  - 上下文过长时优先保留当前技术问题、考点、失分点、知识 evidence 和输出 schema。
- 排除输入（Excluded Inputs）：
  - 超出当前题目、考点或失分点范围的完整课程材料。
  - 无 evidence 的技术事实、伪造引用、伪造版本、论文、官方文档或项目经历。
  - 用户未掌握内容作为用户已经掌握的事实。
  - owner 不一致、source unavailable 的正文、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.6 的 Polish 6A 公共 Output Schema。
  - `technical_expansion_id_candidate`
  - `principle_topics`
  - 每个 principle topic 的 `principle_topic_id_candidate`
  - 每个 principle topic 的 `title`
  - 每个 principle topic 的 `core_explanation`
  - 每个 principle topic 的 `mechanism`
  - 每个 principle topic 的 `tradeoffs`
  - 每个 principle topic 的 `boundary_conditions`
  - 每个 principle topic 的 `common_misconceptions`
  - 每个 principle topic 的 `interview_expression_tips`
  - 每个 principle topic 的 `related_knowledge_point_refs`
  - 每个 principle topic 的 `related_loss_point_refs`
  - 每个 principle topic 的 `evidence_refs`
  - `depth_level`
  - `not_covered_scope`
  - `requires_rag_or_manual_check`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 技术原理必须与当前题目、考点或失分点相关。
  - 不得无边界扩展成完整课程。
  - 技术事实必须绑定知识 evidence 或明确低置信度。
  - 不得伪造引用、版本、论文、官方文档或项目经历。
  - 不得把技术解释包装成用户已经掌握的事实。
  - `depth_level` 是展示深度提示，不冻结课程体系。
  - `requires_rag_or_manual_check` 为真时，前端应展示风险提示或要求补充材料。
  - 技术原理扩展不得直接写入正式 `Asset`、`Weakness` 或 `TrainingRecommendation`。
- 低置信度规则（Low Confidence Rules）：
  - 知识 evidence 缺失。
  - RAG unavailable。
  - 当前题目与技术点关联弱。
  - 考点解析缺失或低置信度。
  - 诊断或失分点低置信度。
  - 技术事实无法验证。
  - 输出超出证据范围。
  - 用户请求深度超过当前证据支持。
- 证据要求（Evidence Requirements）： 每个技术原理主题的核心解释、机制、权衡、边界条件和常见误区必须绑定知识库 / 公共材料 `EvidenceRef` 或明确低置信度；`requires_rag_or_manual_check` 为真时必须输出受影响主题和人工检查原因。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、技术原理扩展生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PolishTechnicalPrincipleExpansion` 或等价会话内技术原理扩展对象。
  - `TechnicalPrinciple` candidate 或等价逻辑对象。
  - `PolishTurn` technical expansion result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 技术原理扩展可以展示给用户。
  - 不自动归档为正式 `Asset`。
  - 不自动创建正式 `Weakness`。
  - 用户可以继续要求更深解释、生成参考回答、重新回答或进入 Asset Candidate contract。
  - 如果用户要归档为资产，必须进入 `P-POLISH-010` 或等价资产候选 / 确认链路。
- 重试 / 兜底（Retry / Fallback）：
  - 当前题目、考点上下文或必需版本缺失时停止正常生成，返回失败或补充材料路径。
  - 知识 evidence 缺失、RAG 不可用或用户请求深度超过证据支持时可保存低置信度有限解释、要求补充材料或建议人工检查。
  - 重试不得默认启用互联网检索、伪造技术事实、扩大为完整课程或自动归档为资产。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `technical_expansion_available`、`technical_expansion_partial`、`technical_expansion_low_confidence`、`technical_expansion_validation_failed`、`rag_or_manual_check_required` 和 `technical_evidence_missing`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 技术原理扩展只使用当前 owner 的题目、回答、诊断、考点、岗位、简历和授权知识 evidence；可展示 evidence summary 不等于原始敏感正文，日志不得记录原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖正常技术原理扩展、无知识 evidence、RAG unavailable、题目关联弱、考点低置信度、输出超出证据范围、伪造引用防护、完整课程扩展防护、requires_rag_or_manual_check 展示要求和不自动归档资产 / 弱项 / 训练建议。
- 开放问题（Open Questions）： 技术原理扩展深度、课程体系映射、技术资料治理和资产候选质量判断仍交给后续 contract / API / UX / 内容治理收敛，为 deferred_non_blocking。

### 12.10 Polish 6B 公共边界与输出 Schema（Output Schema）

#### Polish 6B 公共边界

Polish 6B 只负责回流候选链路：下一轮建议、资产候选和薄弱项候选。6B 不负责正式创建 `Asset`、正式创建 `Weakness`、正式创建 `TrainingRecommendation`、压力面追问、最终面试报告、真实面试复盘或训练计划生成；同题结束策略、资产质量算法、薄弱项合并算法、训练推荐算法和 RAG 实现按后续 LATER / SHOULD 收敛。6B 不重新定义 `P-POLISH-004` 的评分版本、rubric / rule version、证据、置信度、校验和禁止精确概率边界。

Polish 6B 可以消费 `P-POLISH-001` 至 `P-POLISH-008` 的输出、当前题目、当前用户回答、session summary、Job Match 输出、`ScoreResult` canonical score、`MatchPoint` / `MismatchPoint` / `ImprovementPoint`、既有 `Weakness`、已确认 `AssetVersion`、RAG evidence、公共参考材料和最近若干轮 Polish turns。上述输入必须按任务最小必要裁剪，不得默认塞入全部简历、全部岗位、全部历史会话、全部资产、全部知识库材料或全部复盘。

`JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG；当前题目、当前回答、诊断、评分、失分点、参考回答、考点解析和技术原理扩展是 Polish 6B 的核心输入。资产库、薄弱项、历史 Polish turns、Job Match 结果、公共参考材料和知识库是条件检索来源；条件检索必须经过 `P-SHARED-002`。RAG / 知识库可以用于证据增强，但不是 6B 的硬依赖；互联网检索不是 MVP 默认强依赖，不得默认启用。无 RAG、无资产、无历史报告或无历史复盘时不得阻断基础 6B 流程。

Polish 6B 输出可以保存为下一轮建议、资产候选、薄弱项候选、validation result、low confidence flag、evidence refs、trace refs、session summary update 输入和 audit event。Polish 6B 不得直接写入正式 `Weakness`、正式 `Asset`、正式 `TrainingRecommendation`、最终面试报告或压力面整场评分。用户确认前，资产与薄弱项只能是候选态或待确认状态。

#### Polish 6B 公共输出 Schema（Output Schema）

`P-POLISH-009` 至 `P-POLISH-011` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `polish_session_ref` | 是 | ref | 打磨会话引用 |
| `polish_turn_ref` | 是 | ref | 当前打磨轮次引用 |
| `question_ref` | 是 | ref | 当前题目引用 |
| `answer_ref` | 是 | ref | 当前回答引用 |
| `diagnosis_refs` | 否 | ref[] | 回答诊断引用 |
| `round_score_refs` | 否 | ref[] | 本轮得分引用 |
| `loss_point_refs` | 否 | ref[] | 失分点引用 |
| `reference_answer_refs` | 否 | ref[] | 参考回答引用 |
| `knowledge_point_refs` | 否 | ref[] | 考点解析引用 |
| `technical_principle_refs` | 否 | ref[] | 技术原理扩展引用 |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性聚合状态；底层来源状态仍沿用 §6.1 的 `source_*` 枚举 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的 `EvidenceRef` |
| `displayable_evidence_summary` | 否 | object[] | 可展示证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记，必须可追溯到 `P-SHARED-004` |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验和持久化交接过程 `TraceRef` |
| `session_summary_update_ref` | 否 | ref | `P-SHARED-006` 产出的摘要更新引用 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能回流正式对象 |

`next_recommended_actions` 只表达建议动作，不直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。允许值至少包括 `answer_again`、`continue_same_question`、`switch_topic`、`generate_next_question`、`generate_reference_answer`、`explain_knowledge_point`、`expand_technical_principle`、`confirm_asset_candidate`、`edit_asset_candidate`、`skip_asset_candidate`、`confirm_weakness_candidate`、`edit_weakness_candidate`、`skip_weakness_candidate`、`merge_weakness_candidate`、`enter_pressure_mode` 和 `generate_review_later`。其中需要用户确认的 action 必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。

### 12.11 `P-POLISH-009` 下一轮建议（Next Round Suggestion）

- Contract ID： `P-POLISH-009`
- 名称（Name）： Next Round Suggestion
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - `P-POLISH-004` Round Score 完成后。
  - `P-POLISH-005` Loss Point Analysis 完成后。
  - `P-POLISH-006` Reference Answer 完成后。
  - `P-POLISH-007` Knowledge Point Explanation 或 `P-POLISH-008` Technical Principle Expansion 完成后。
  - 用户请求“下一步怎么练”。
  - 用户请求继续同题、换题或切换主题。
  - session summary 显示当前题目已多轮打磨或仍有明显缺口。
- 目标（Goal）： 基于当前题目、用户回答、诊断、得分、失分点、参考回答、考点解析、技术原理扩展和 session summary 生成下一轮建议；只生成建议；同题结束策略的长期调参仅为 LATER / SHOULD，不在本 contract 冻结为自动关闭条件；不生成正式训练计划。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `polish_turn_ref`
  - 当前题目引用
  - 当前用户回答引用
  - `P-POLISH-003` Answer Diagnosis 结果
  - `P-POLISH-004` Round Score 结果
  - `P-POLISH-005` Loss Point Analysis 结果或等价失分输入
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
  - `P-POLISH-006` Reference Answer 结果
  - `P-POLISH-007` Knowledge Point Explanation 结果
  - `P-POLISH-008` Technical Principle Expansion 结果
  - selected topic
  - Job Match points
  - 历史同题打磨轮次
  - 既有 `Weakness`
  - 已确认 `AssetVersion`
  - RAG evidence
  - 公共参考材料
- 检索来源（Retrieval Sources）：
  - 默认使用当前题目、当前回答、诊断、得分、失分点和 session summary。
  - 条件读取参考回答、考点解析、技术原理扩展、历史同题打磨轮次、既有 `Weakness` 和已确认资产。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG、无资产、无历史同题轮次时仍可生成基础下一轮建议。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前题目、当前回答、诊断、得分、失分点、session summary、已问问题、禁止重复问题和输出 schema。
  - 上下文过长时优先保留当前轮结果、未修复失分点、低置信度原因、用户当前目标、同题历史摘要和禁止重复列表。
  - 不得默认塞入全部历史回答、全部资产、全部知识库或全部复盘。
- 排除输入（Excluded Inputs）：
  - 压力面连续追问状态作为 Polish 下一轮建议的直接替代。
  - 正式训练计划、训练任务、训练优先级算法或未确认训练推荐。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 无关历史回答全文、全量资产、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.10 的 Polish 6B 公共 Output Schema。
  - `next_round_suggestion_id_candidate`
  - `suggested_next_action`
  - `action_reason`
  - `same_question_continue_hint`
  - `switch_topic_hint`
  - `next_question_generation_hint`
  - `focus_loss_point_refs`
  - `focus_knowledge_point_refs`
  - `focus_principle_refs`
  - `recommended_user_action`
  - `blocked_by_low_confidence`
  - `user_choice_required`
  - `candidate_follow_up_prompt_refs`
  - `suggestion_ordering`
  - `same_question_end_threshold_status`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 建议必须基于当前轮诊断、得分、失分点或 session summary。
  - 不得把同题打磨建议升级为自动关闭条件；`same_question_end_threshold_status` 只能表达 `not_evaluated`、`suggestion_only`、`later_calibration` 或等价非最终状态。
  - 不得把建议动作写成正式训练计划。
  - 不得把低置信度结果包装为确定建议。
  - 不得把压力面连续追问当成 Polish 下一轮建议。
  - `same_question_continue_hint` 只是建议，不是强制流程。
  - `enter_pressure_mode` 只能作为建议入口，不得自动切换模式。
  - 建议不得绕过用户选择或确认。
- 低置信度规则（Low Confidence Rules）：
  - 诊断缺失。
  - 得分缺失或低置信度。
  - 失分点缺失或低置信度。
  - session summary 缺失。
  - 历史同题轮次缺失。
  - 当前用户目标不清。
  - 上下文裁剪影响建议。
  - 关键 evidence 不足。
- 证据要求（Evidence Requirements）： 下一轮动作、排序原因、同题继续提示、换题提示和关注点引用必须绑定当前题目、当前回答、诊断、评分、失分点、session summary 或历史同题 evidence；证据不足时必须输出低置信度或要求用户选择。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、下一轮建议生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `PolishNextRoundSuggestion` 或等价会话内建议对象。
  - `PolishTurn` next action result。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 下一轮建议必须由用户选择或确认后进入具体动作。
  - 用户可以继续同题、换题、切换主题、进入压力面或稍后复盘。
  - 本 contract 不创建正式 `TrainingRecommendation`。
- 重试 / 兜底（Retry / Fallback）：
  - 当前题目、当前回答、诊断、评分或失分输入缺失时停止正常建议，返回失败或补充材料路径。
  - session summary 缺失、历史轮次不足或 evidence 不足时可保存低置信度建议、要求用户选择目标或降级为基础建议。
  - 重试不得默认启用互联网检索、扩大到全量历史会话或自动切换模式。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `next_round_suggestion_available`、`next_round_suggestion_partial`、`next_round_suggestion_low_confidence`、`next_round_suggestion_validation_failed`、`user_choice_required` 和 `same_question_threshold_unknown`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 下一轮建议只使用当前 owner 的题目、回答、诊断、评分、失分点、session summary 和授权增强证据；可展示结果不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖评分后建议、失分后建议、参考回答后建议、考点 / 技术原理后建议、用户请求下一步、继续同题、换题、进入压力面仅作为建议、session summary 缺失、低置信度不包装为确定建议和同题结束策略不被包装为自动关闭条件。
- 开放问题（Open Questions）： 同题结束建议阈值、下一轮推荐算法、建议排序算法和训练计划映射仍待后续 contract / API / UX 收敛，为 deferred_non_blocking。进展树 plan/state 的 runtime task_type 已登记，下一轮建议如何消费进展树状态仍作为后续策略细化项。

### 12.12 `P-POLISH-010` 资产候选（Asset Candidate）

- Contract ID： `P-POLISH-010`
- 名称（Name）： Asset Candidate
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - 用户请求“保存为资产”。
  - 用户对参考回答或改进表达表示满意。
  - `P-POLISH-006` Reference Answer 生成后。
  - `P-POLISH-008` Technical Principle Expansion 生成表达建议后。
  - session summary 显示某段回答具有复用价值。
  - 系统建议用户确认资产候选。
- 目标（Goal）： 从用户回答、参考回答、表达改进、技术表达建议和证据中生成资产候选；只生成候选，不自动归档为正式 `Asset`。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `polish_turn_ref`
  - 当前题目引用
  - 当前用户回答引用
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
  - `P-POLISH-003` Answer Diagnosis 结果
  - `P-POLISH-005` Loss Point Analysis 结果
  - `P-POLISH-006` Reference Answer 结果
  - `P-POLISH-007` Knowledge Point Explanation 结果
  - `P-POLISH-008` Technical Principle Expansion 结果
  - 已确认 `AssetVersion`
  - 历史同题打磨轮次
  - Job Match points
  - RAG evidence
  - 公共参考材料
- 检索来源（Retrieval Sources）：
  - 默认使用当前题目、用户回答、参考回答、诊断、失分点和 session summary。
  - 条件读取已有资产、历史同题轮次、技术原理扩展、Job Match points 和知识 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG 或已有资产时仍可生成基础资产候选。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前题目、用户原始回答、参考回答、用户事实、模型建议表达、证据 refs 和输出 schema。
  - 必须区分用户事实、模型建议表达、待用户编辑内容和不可确认内容。
  - 不得默认塞入全部资产或全部历史回答。
  - 上下文过长时优先保留用户原始回答、用户确认事实、参考回答差异、可复用表达和 evidence refs。
- 排除输入（Excluded Inputs）：
  - 用户未表达或未确认的项目、数据、职责、成果或技术经验作为事实。
  - 未确认资产候选作为正式资产事实。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 全量资产库、无关历史回答全文、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.10 的 Polish 6B 公共 Output Schema。
  - `asset_candidate_id`
  - `candidate_status`
  - `asset_type_hint`
  - `title`
  - `content_draft`
  - `source_answer_refs`
  - `reference_answer_refs`
  - `facts_used_from_user`
  - `model_suggested_phrasing`
  - `facts_requiring_user_confirmation`
  - `not_assumed_facts`
  - `quality_hints`
  - `reuse_scenarios`
  - `related_job_requirements`
  - `related_resume_outline_refs`
  - `related_knowledge_point_refs`
  - `related_principle_refs`
  - `merge_candidate_asset_refs`
  - `user_edit_required`
  - `user_confirmation_required`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 资产候选必须可追溯到用户回答、参考回答或用户确认事实。
  - 不得把模型生成内容伪装成用户真实经历。
  - 不得虚构用户项目、数据、职责、成果或技术经验。
  - 不得自动归档为正式 `Asset`。
  - 如与既有资产重复，应输出 merge suggestion，不得自动覆盖。
  - `content_draft` 必须标记哪些部分来自用户事实，哪些是表达建议。
  - 技术内容缺少 evidence 时必须低置信度或要求用户确认。
  - `asset_type_hint` 只是候选分类，不冻结资产分类算法。
- 低置信度规则（Low Confidence Rules）：
  - 用户回答过短。
  - 用户事实不足。
  - 参考回答低置信度。
  - 技术解释低置信度。
  - 无法区分用户事实和模型建议。
  - 与已有资产冲突。
  - 缺少 evidence refs。
  - 用户确认缺失。
  - 上下文裁剪影响事实边界。
- 证据要求（Evidence Requirements）： `content_draft`、用户事实、模型建议表达、质量提示和复用场景必须绑定当前回答、参考回答、用户确认事实、诊断、失分点、知识 evidence 或已确认资产引用；无法绑定时必须进入低置信度或用户确认路径。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、资产候选生成、重复或合并线索检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `AssetCandidate` 或等价待确认对象。
  - `AssetVersion` candidate 或等价草稿版本。
  - `UserConfirmationRef`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 默认必须用户确认后才能成为正式 `Asset`。
  - 用户可以确认、编辑、跳过、合并或要求重新生成。
  - 用户确认动作必须形成 `UserConfirmationRef` 或等价记录。
  - 回流失败不得影响原始 Polish turn、参考回答或诊断结果。
- 重试 / 兜底（Retry / Fallback）：
  - 当前题目、当前回答、必需版本或 owner 校验缺失时停止正常生成，返回失败或补充材料路径。
  - 用户事实不足、技术证据不足、与已有资产冲突或无法区分事实和建议时可保存低置信度候选、要求用户编辑确认或降级为待补充草稿。
  - 重试不得默认启用互联网检索、虚构用户经历、覆盖既有资产或自动归档为正式资产。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `asset_candidate_available`、`asset_candidate_partial`、`asset_candidate_low_confidence`、`asset_candidate_validation_failed`、`user_confirmation_required`、`merge_candidate_detected` 和 `user_facts_insufficient`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 资产候选只使用当前 owner 的题目、回答、参考回答、诊断、岗位、简历、已确认资产和授权证据；前端只可见结构化候选、可展示证据摘要和必要 trace id，不暴露原始 Prompt、completion、provider payload 或无权限来源正文。
- 测试策略（Test Strategy）： 使用 fixture 覆盖用户主动保存、参考回答转候选、技术表达转候选、用户事实不足、模型建议与用户事实分离、虚构经历防护、重复资产 merge suggestion、技术证据缺失、用户编辑确认和不得自动归档为正式资产。
- 开放问题（Open Questions）： 资产质量算法、资产分类算法、资产合并算法、版本替代规则和正式资产入库 API 字段仍待后续 Asset / API / UX 收敛，为 deferred_non_blocking。

### 12.13 `P-POLISH-011` 薄弱项候选（Weakness Candidate）

- Contract ID： `P-POLISH-011`
- 名称（Name）： Weakness Candidate
- 模式（Mode）： `polish`
- 触发条件（Trigger）：
  - `P-POLISH-003` Answer Diagnosis 发现明显弱点。
  - `P-POLISH-005` Loss Point Analysis 发现稳定失分模式。
  - `P-POLISH-007` Knowledge Point Explanation 发现知识盲区。
  - `P-POLISH-008` Technical Principle Expansion 发现技术原理缺口。
  - 用户请求记录薄弱项。
  - session summary 显示多轮重复失分。
  - 系统建议用户确认薄弱项候选。
- 目标（Goal）： 从诊断、失分点、低置信度原因、知识缺口、技术原理缺口和重复问题中生成薄弱项候选；只生成候选，不自动创建正式 `Weakness`。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `polish_session_ref`
  - `polish_turn_ref`
  - 当前题目引用
  - 当前用户回答引用
  - `P-POLISH-003` Answer Diagnosis 结果
  - `P-POLISH-005` Loss Point Analysis 结果
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
  - `P-POLISH-004` Round Score 结果
  - `P-POLISH-007` Knowledge Point Explanation 结果
  - `P-POLISH-008` Technical Principle Expansion 结果
  - `P-POLISH-009` Next Round Suggestion 结果
  - 既有 `Weakness`
  - 历史薄弱项状态
  - 历史同题打磨轮次
  - Job Match mismatch / improvement points
  - RAG evidence
  - 公共参考材料
- 检索来源（Retrieval Sources）：
  - 默认使用当前诊断、失分点、题目、回答和 session summary。
  - 条件读取既有 `Weakness`、历史薄弱项状态、历史同题轮次、Job Match mismatch / improvement points 和知识 evidence。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG 或历史弱项时仍可生成基础候选，但知识性或技术性薄弱项应标记低置信度。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小必要上下文、owner 校验、来源可用性、裁剪、omitted refs 和 trace 规则。
  - 上下文至少包含当前题目、当前回答、诊断弱点、失分点、低置信度原因、session summary、既有弱项摘要和输出 schema。
  - 不得默认塞入全部历史弱项、全部打磨历史、全部知识库或全部报告。
  - 上下文过长时优先保留当前轮证据、多轮重复信号、既有弱项合并线索和 evidence refs。
- 排除输入（Excluded Inputs）：
  - 单次轻微失误作为稳定能力缺陷的确定事实。
  - 岗位匹配缺口作为用户能力缺陷的直接替代。
  - 未确认候选对象作为正式弱项事实。
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 全量历史弱项、全量打磨历史、全量知识库、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文、原始 embedding 向量和默认互联网检索结果。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §12.10 的 Polish 6B 公共 Output Schema。
  - `weakness_candidates`
  - 每个候选的 `candidate_id`
  - 每个候选的 `candidate_status`
  - 每个候选的 `title`
  - 每个候选的 `description`
  - 每个候选的 `source_type`
  - 每个候选的 `source_refs`
  - 每个候选的 `evidence_refs`
  - 每个候选的 `severity_hint`
  - 每个候选的 `related_loss_point_refs`
  - 每个候选的 `related_diagnosis_refs`
  - 每个候选的 `related_knowledge_point_refs`
  - 每个候选的 `related_principle_refs`
  - 每个候选的 `related_job_requirements`
  - 每个候选的 `related_resume_outline_refs`
  - 每个候选的 `merge_candidate_refs`
  - 每个候选的 `suggested_training_direction`
  - 每个候选的 `user_confirmation_required`
  - `merge_suggestions`
  - `repeat_pattern_refs`
  - `candidate_ordering`
- 校验规则（Validation Rules）：
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 薄弱项候选必须来源于诊断、失分点、知识缺口、技术原理缺口、多轮重复问题或用户明确请求。
  - 不得把单次轻微失误直接包装为稳定能力缺陷，除非标记低置信度。
  - 不得把岗位匹配缺口直接包装为用户能力缺陷。
  - 不得静默覆盖既有 `Weakness`。
  - 如可能与既有 `Weakness` 重复，应输出 merge suggestion，不得自动合并。
  - `severity_hint` 只是提示，不冻结严重度算法。
  - `suggested_training_direction` 只是训练方向，不等同于正式训练任务。
  - 缺少 evidence 时不得生成高置信候选。
  - 不得绕过用户确认写入正式 `Weakness`。
- 低置信度规则（Low Confidence Rules）：
  - 失分点低置信度。
  - 诊断低置信度。
  - 技术证据不足。
  - 单轮证据不足以判断稳定弱项。
  - 既有 `Weakness` 冲突。
  - 合并候选不确定。
  - 用户回答过短。
  - 岗位要求或题目要求模糊。
  - 多轮重复证据缺失。
  - 上下文裁剪影响候选归因。
- 证据要求（Evidence Requirements）： 每个候选的标题、描述、来源类型、严重程度提示、训练方向和合并建议必须绑定诊断、失分点、知识点、技术原理、当前回答、session summary 或历史重复 evidence；缺少 evidence 时不得生成高置信候选。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、薄弱项候选生成、重复或合并线索检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Session Summary Update handoff、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `Weakness` candidate 或等价待确认对象。
  - `WeaknessEvidence`
  - `UserConfirmationRef`
  - `FeedbackLoop`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `SessionSummary` update 输入
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 默认必须用户确认后才能成为正式 `Weakness`。
  - 用户可以确认、编辑、跳过、合并或要求重新生成。
  - 用户确认动作必须形成 `UserConfirmationRef` 或等价记录。
  - 回流失败不得影响原始 Polish turn、诊断、失分点或得分结果。
- 重试 / 兜底（Retry / Fallback）：
  - 当前题目、当前回答、诊断、失分点、必需版本或 owner 校验缺失时停止正常生成，返回失败或补充材料路径。
  - 单轮证据不足、技术证据不足、既有弱项冲突或合并不确定时可保存低置信度候选、要求用户确认或仅输出训练方向建议。
  - 重试不得默认启用互联网检索、把岗位缺口包装成能力缺陷、覆盖既有弱项或自动创建正式弱项。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `weakness_candidate_available`、`weakness_candidate_partial`、`weakness_candidate_low_confidence`、`weakness_candidate_validation_failed`、`user_confirmation_required`、`merge_candidate_detected` 和 `repeat_pattern_missing`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 薄弱项候选只使用当前 owner 的题目、回答、诊断、失分点、session summary、既有弱项摘要和授权证据；可展示 evidence summary 不等于原始敏感正文，日志不得记录原始 Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖诊断弱点、失分点稳定模式、知识盲区、技术原理缺口、用户主动记录、多轮重复信号、单次轻微失误低置信度、岗位缺口不转能力缺陷、重复弱项 merge suggestion、用户确认 / 编辑 / 跳过 / 合并和不得自动创建正式弱项。
- 开放问题（Open Questions）： 薄弱项合并算法、严重度算法、状态生命周期、自动消减规则、训练推荐算法和正式 Weakness API 字段仍待后续 Weakness / Training / API / UX 收敛，为 deferred_non_blocking。

### 12.14 Polish Contract 关系

- `P-POLISH-001` 负责规划打磨主题。
- `P-POLISH-002` 基于选定主题生成或选择题目。
- `P-POLISH-003` 基于当前题目和用户回答生成诊断。
- `P-POLISH-004` 基于当前题目、用户回答和诊断生成本轮 0-100 得分。
- `P-POLISH-005` 基于 `P-POLISH-003` 诊断和 `P-POLISH-004` 得分生成失分点。
- `P-POLISH-006` 基于当前题目、用户回答、诊断和失分点生成参考回答。
- `P-POLISH-007` 基于当前题目、诊断、失分点和知识 evidence 生成考点解析。
- `P-POLISH-008` 基于考点解析、技术诊断、失分点和知识 evidence 扩展技术原理。
- `P-POLISH-009` 基于当前轮诊断、得分、失分点、参考回答、考点解析、技术原理扩展和 session summary 生成下一轮建议。
- `P-POLISH-010` 基于用户回答、参考回答、表达改进、技术表达建议和证据生成资产候选。
- `P-POLISH-011` 基于诊断、失分点、知识缺口、技术原理缺口、低置信度原因和多轮重复信号生成薄弱项候选。
- `P-POLISH-006` 不得在用户答题前泄露完整参考答案。
- `P-POLISH-007` 不得无边界扩展成百科讲解。
- `P-POLISH-008` 不得无证据伪造技术事实。
- `P-POLISH-009` 不得把同题结束策略包装为自动关闭条件，不得生成正式训练计划。
- `P-POLISH-010` 不得把参考回答自动变成正式资产。
- `P-POLISH-011` 不得把失分点自动变成正式薄弱项。
- `P-POLISH-010` 和 `P-POLISH-011` 都必须保留用户确认、编辑、跳过和合并路径。
- `P-POLISH-001` 至 `P-POLISH-011` 都必须引用 Shared Contracts，并至少交接 validation、Low Confidence、EvidenceRef、TraceRef 和 session summary update 输入。
- `P-POLISH-001` 和 `P-POLISH-002` 可以消费 Job Match 输出作为上游参考。
- `P-POLISH-003` 至 `P-POLISH-011` 必须绑定当前题目；涉及用户回答时必须绑定当前回答。
- `P-POLISH-004` 不得把 Job Match 分数直接当成本轮回答分。
- `P-POLISH-005` 至 `P-POLISH-011` 都不得直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。
- `P-POLISH-005` 至 `P-POLISH-008` 产生的解释结果，可作为 `P-POLISH-009`、`P-POLISH-010`、`P-POLISH-011` 的上游输入。
- 6B 产生的候选可作为后续 Asset / Weakness / Training contracts 的上游，但不替代这些 contract。
- 每个 contract 都必须为 `P-SHARED-006` Session Summary Update 提供输入。
- 6B 完成后，Pressure、Report、Review、Weakness、Asset、Training contracts 均已按 `PROMPT_SPEC.md` canonical registry 进入 Draft；Polish 输出只作为这些 domain 的候选、建议或输入引用，不自动写正式对象，也不关闭这些 domain 的 deferred_non_blocking 细化项。
