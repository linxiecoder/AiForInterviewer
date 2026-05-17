---
title: SHARED_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/shared-contracts
---

# SHARED_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件遵守 `PROMPT_SPEC.md` §13 的 `AR-F4-FULL-001` 处置口径；复杂参数和实现细节按 deferred_non_blocking 承接。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 适用范围

本文件承载主 catalog 中 `P-SHARED-001` 至 `P-SHARED-006` 的详细 contract 正文。Shared contracts 是跨模式公共规则，供 Job Match、Polish、Pressure 以及后续 Stub contract 引用。

## 10. Shared Contract 细则

本节只填充可被后续业务 contract 引用的公共规则，不写完整生产 Prompt 文案，不选择 provider、向量数据库、embedding 模型或互联网检索服务。

### 10.0 Shared Contract 推荐调用顺序

后续业务 AI Task 可按任务需要裁剪步骤，但 Shared Contract 的默认推荐顺序如下，用于避免 Evidence / Validation / Low Confidence 之间的输入依赖循环：

1. `P-SHARED-002` Retrieval Planning。
2. `P-SHARED-005` Evidence Binding 的 Input Evidence Selection 子步骤，输出 `selected_input_evidence_refs`。
3. `P-SHARED-001` Context Assembly。
4. 业务 AI Task / LLM generation。
5. `P-SHARED-005` Evidence Binding 的 Output Evidence Binding 子步骤，输出 `bound_output_evidence_refs`、`missing_evidence` 和 `conflicting_evidence`。
6. `P-SHARED-003` Output Validation。
7. `P-SHARED-004` Low Confidence Classification。
8. `P-SHARED-006` Session Summary Update。
9. Persistence / candidate write / user confirmation flow。

其中 Input Evidence Selection 发生在 Retrieval Planning / Context Assembly 之前或过程中，用于选择允许进入上下文的证据；Output Evidence Binding 发生在模型输出或业务结果生成之后，用于把评分、建议、弱项、资产候选和报告结论绑定到证据。`P-SHARED-003` 只校验上游已经声明或绑定的证据引用，不创建 evidence binding；`P-SHARED-004` 只消费 validation、retrieval、context 和 evidence binding 的 failure signal，不重复执行 validation。

### 10.1 `P-SHARED-001` 上下文装配（Context Assembly）

- Contract ID： `P-SHARED-001`
- 名称（Name）： Context Assembly
- 模式（Mode）： `shared`
- 触发条件（Trigger）： 任一 AI 子任务在调用模型、生成结构化结果或进入业务校验前，需要组装当前任务上下文时触发。
- 目标（Goal）： 形成最小必要、可追踪、已完成 owner / scope 校验的 `context_bundle`，供后续 contract 使用。
- 必需输入（Required Inputs）：
  - 当前用户 / owner / role scope。
  - 当前 `contract_id`、业务模式和任务目标。
  - 当前任务必需的业务对象 `VersionRef` / `SnapshotRef`，按业务模式条件包含适用的 `ResumeVersion`、`JobVersion`、会话或题答引用。
  - 当前会话状态、当前题目、当前回答、最近若干轮问答和已问问题列表；初始轮次可只包含当前会话、题目或任务目标。
  - `session_summary` 为条件必需：已有可用摘要时必须传入；初始轮次可使用 `session_summary.status = empty_initial`；无可用摘要时可使用 `session_summary.status = not_available`。
  - `retrieval_plan` 为条件必需：当前 task 需要检索时必须传入；不需要检索时使用 `retrieval_plan.status = retrieval_not_required`。
  - `retrieval_results` 为条件必需：已执行检索时必须传入；无命中时使用 `retrieval_results.status = retrieval_empty`；来源不可用时使用 `retrieval_results.status = source_unavailable` 且只保留 ref / status。
  - 输出 schema 和 validation requirement。
  - 当前上下文预算或大小约束的语义状态。
- 可选输入（Optional Inputs）：
  - 资产命中、薄弱项命中、历史报告 / 复盘命中、RAG evidence、用户确认记录和禁止重复追问列表。
  - 长历史压缩摘要、暂停恢复快照摘要、低置信度或失败状态继承信息。
- 检索来源（Retrieval Sources）： 不适用为主动检索；本 contract 只消费 `P-SHARED-002` 产出的 `retrieval_plan` 和 `retrieval_results`。
- 上下文装配（Context Assembly）：
  - 上下文层级按固定系统规则、模式规则、当前任务目标、简历版本摘要、岗位版本摘要、当前题目、当前回答、最近轮次、session summary、已问问题、禁止重复追问、资产命中、薄弱项命中、历史报告 / 复盘命中、RAG evidence、输出 schema、validation rules 组织。
  - 不默认塞入全部简历、全部岗位、全部历史会话或全部资产；只选择当前 contract 必需片段和摘要。
  - 上下文超长时，优先保留当前轮、当前题目、当前回答、显式证据、版本引用、输出 schema 和 validation rules。
  - 长历史优先压缩为 `session_summary`；被裁剪内容必须通过 `omitted_refs`、裁剪原因或 trace 表达。
  - 前端传入内容只能作为用户输入材料，不能作为已验证 prompt 或系统规则。
  - system rules、business refs、RAG evidence、用户回答和外部材料必须分区处理；前端传入内容默认不可信，不得直接作为 system instruction。
- 排除输入（Excluded Inputs）：
  - 无 owner / scope 校验的数据、无关用户数据和不需要的完整原文。
  - `source_unavailable`、`source_deleted`、`source_disabled`、已归档且未显式选择的来源正文。
  - 原始密钥、token、cookie、provider payload、日志正文、错误堆栈、原始 embedding 向量。
  - 前端直接传入的未校验 prompt、要求覆盖系统规则的用户内容或 RAG 指令。
- 输出 Schema（Output Schema）：
  - `context_bundle`
  - `context_sections`
  - `section_id`
  - `section_type`
  - `trust_level`
  - `source_type`
  - `owner_scope`
  - `displayability`
  - `included_layers`
  - `included_refs`
  - `omitted_refs`
  - `budget_by_layer`
  - `truncation_reason`
  - `token_or_size_budget_status`
  - `risk_flags`
  - `trace_ref`
  - `section_type` 至少包含 `system_rules`、`mode_rules`、`task_goal`、`business_snapshot`、`user_answer`、`recent_turns`、`session_summary`、`asset_evidence`、`weakness_evidence`、`rag_evidence`、`historical_report_evidence`、`output_schema`、`validation_rules`。
  - `trust_level` 至少包含 `system_trusted`、`owner_verified`、`retrieved_verified`、`user_supplied`、`untrusted_external`、`unavailable_ref_only`。
  - `displayability` 至少包含 `frontend_displayable_summary`、`backend_only`、`ref_only`、`not_displayable`。
- 校验规则（Validation Rules）：
  - `included_refs` 必须全部通过 owner / scope、来源状态和版本引用校验。
  - 必需输入、输出 schema 和 validation requirement 缺失时不得进入正常模型调用。
  - `omitted_refs` 必须说明裁剪原因，不得静默丢弃关键证据。
  - `context_bundle` 不得包含禁止输入、provider payload 或无关用户数据。
  - 无 owner 校验的数据不得进入任何 `context_sections`；`source_unavailable` 内容只能保留 ref / status，不得重新读取正文。
- 低置信度规则（Low Confidence Rules）：
  - `context_too_large`、`required_input_missing`、`evidence_missing`、`source_unavailable` 或 `context_truncated_with_risk` 时标记低置信度并输出 failure signal。
  - 裁剪影响当前结论可靠性时，必须输出 `context_truncated_with_risk` 风险并传递给后续 validation。
- 证据要求（Evidence Requirements）： 当前上下文中的关键业务来源必须保留 `SourceRef`、`EvidenceRef`、`VersionRef` / `SnapshotRef`；若仅使用摘要，应保留摘要来源引用。
- Trace 要求（Trace Requirements）： 必须记录 Context Assembly trace，包括 contract、输入来源、裁剪原因、omitted refs、risk flags、预算状态和低置信度状态。
- 持久化目标（Persistence Targets）： `RAGContextAssembly`、`LlmRequestTrace` 或同等 trace / validation 记录；不直接写入正式业务结果。
- 用户确认要求（User Confirmation Requirement）： 不适用；上下文装配本身不需要用户确认，但其输出不能绕过后续业务 contract 的用户确认要求。
- 重试 / 兜底（Retry / Fallback）：
  - `owner_mismatch`、`required_input_missing`、validation requirement missing 时停止并返回失败分类。
  - 初始轮次使用 `session_summary.status = empty_initial`，不因缺少历史摘要阻断上下文装配。
  - 无检索任务使用 `retrieval_plan.status = retrieval_not_required`，不生成伪造检索结果。
  - 检索为空使用 `retrieval_results.status = retrieval_empty`，可降级为核心业务输入 + 低置信度。
  - 摘要生成失败时保留原始问答和上一版可用摘要，并输出 `summary_generation_failed` failure signal。
  - `source_unavailable` 或 `evidence_missing` 时可降级为低置信度、部分可用或要求用户补充材料。
  - `context_too_large` 时先裁剪长历史和非关键命中，再生成 `omitted_refs`；仍超限则停止或转人工校对。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `context_ready`、`context_partial`、`context_too_large`、`source_unavailable`、`owner_mismatch`、`required_input_missing` 和 `validation_requirement_missing`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 所有输入进入上下文前必须完成 owner / scope 校验和最小必要裁剪；不得保存或返回原始 Prompt、provider payload、密钥、token、cookie 和无关正文。
- 测试策略（Test Strategy）： 使用确定性 fixture 验证上下文层级、裁剪顺序、禁止输入过滤、`owner_mismatch`、`source_unavailable`、omitted refs、trace_ref 和预算状态。
- 开放问题（Open Questions）： 具体 token / size 预算数值、最近轮次数量和暂停恢复快照扩展字段为 deferred_non_blocking；最小上下文分层、裁剪、trace 和低置信度规则已由本 contract 固化。

### 10.2 `P-SHARED-002` 检索规划（Retrieval Planning）

- Contract ID： `P-SHARED-002`
- 名称（Name）： Retrieval Planning
- 模式（Mode）： `shared`
- 触发条件（Trigger）： 任一 AI 子任务在需要判断是否检索、选择检索来源、过滤证据或裁剪命中结果时触发。
- 目标（Goal）： 生成可执行的 `retrieval_plan`，明确检索来源、过滤条件、排序、裁剪、证据选择和失败表达。
- 子阶段（Sub-stages）：
  1. `retrieval_need_decision`：判断当前 task 是否需要检索；不需要时输出 `retrieval_not_required`。
  2. `source_filter_planning`：按 owner / scope、source availability、公共材料发布状态和用户确认状态规划来源过滤。
  3. `query_planning`：生成结构化查询、关键词检索或人工维护材料查询的语义计划。
  4. `result_normalization`：把结构化引用、数据库过滤、关键词检索、RAG 命中或人工维护材料统一成候选 evidence refs。
  5. `candidate_ranking`：按任务相关性、最近性、用户确认状态、来源可信度和可用性排序。
  6. `selected_input_evidence_refs`：将候选证据交给 `P-SHARED-005` Input Evidence Selection 子步骤选择，并记录允许进入 Context Assembly 的 refs。
- 必需输入（Required Inputs）：
  - 当前用户 / owner / role scope、当前 `contract_id`、业务模式和任务目标。
  - 当前 `ResumeVersion` / `ResumeMarkdownOutline`、`JobVersion`、会话、题目、回答或报告 / 复盘引用。
  - 当前 source availability、公共材料发布状态、用户确认状态和已知低置信度 / 失败状态。
  - 当前 contract 对 evidence、schema、validation 和上下文预算的要求。
- 可选输入（Optional Inputs）：
  - 资产、资产版本、薄弱项、薄弱项证据、历史报告、模拟复盘、真实复盘、知识库文档、公共参考材料和显式用户选择的来源。
  - 后续明确启用时的互联网检索开关、查询边界和来源可信度要求。
- 检索来源（Retrieval Sources）：
  - `ResumeVersion` / `ResumeMarkdownOutline`
  - `JobVersion`
  - `Asset` / `AssetVersion`
  - `Weakness` / `WeaknessEvidence`
  - `InterviewReport`
  - `MockInterviewReview`
  - `RealInterviewReview`
  - `KnowledgeBase` / `KnowledgeDocument` / `KnowledgeChunk`
  - 公共参考材料
  - 互联网检索，非 MVP 默认强依赖，仅在后续设计明确启用时使用
- 上下文装配（Context Assembly）：
  - 检索计划自身只使用来源元数据、摘要、版本引用、状态和任务目标，不读取未校验正文。
  - 简历和岗位版本是核心输入，不等同于 RAG；资产、薄弱项、历史报告、复盘和知识库是条件检索。
  - 结果进入 `P-SHARED-001` 前必须去重、排序、裁剪并生成 evidence refs。
- 排除输入（Excluded Inputs）：
  - owner 不一致的私有来源、`source_deleted` / `source_disabled` / `source_unavailable` 正文、未发布公共材料、未启用的互联网结果。
  - 无来源、无版本、无维护者边界或无法形成 evidence ref 的材料。
  - provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - `retrieval_plan`
  - `retrieval_need_decision`
  - `source_filters`
  - `retrieval_queries`
  - `retrieval_results`
  - `candidate_evidence_refs`
  - `selected_input_evidence_refs`
  - `excluded_evidence`
  - `citation_or_evidence_refs`
  - `trace_ref`
  - `risk_flags`
- 校验规则（Validation Rules）：
  - 私有来源必须 owner / scope 一致；公共材料必须发布、可用并有维护者边界。
  - 排序至少考虑当前任务相关性、当前题目相关性、当前岗位相关性、当前薄弱项相关性、最近性、用户确认状态、证据完整度、来源可信度和 source availability。
  - 证据过长时必须先生成摘要和裁剪原因，不得把整份原文默认送入上下文。
  - `evidence_conflict` 必须显式进入 `excluded_evidence`、`risk_flags` 或 selected evidence 的冲突标记。
- 低置信度规则（Low Confidence Rules）：
  - 检索为空、检索结果 owner 不一致、`source_disabled` / `source_deleted` / `source_archived`、`evidence_conflict`、evidence too long、`public_material_unpublished` 或 internet retrieval unavailable 时进入低置信度或部分可用。
  - 互联网检索不可用不得阻断 MVP 默认流程，除非后续业务 contract 明确把它设为必需。
- MVP 执行说明（MVP Execution Notes）：
  - MVP 不默认要求向量库、embedding 或 vector index。
  - MVP 可优先使用结构化引用、数据库过滤、关键词检索和人工维护的知识材料。
  - RAG / embedding / vector index 是后续实现选择，不在本阶段冻结。
  - 互联网检索不是 MVP 默认依赖，只能在后续产品、安全和来源治理设计明确启用时使用。
- 证据要求（Evidence Requirements）： `candidate_evidence_refs` 和 `selected_input_evidence_refs` 必须能生成 `EvidenceRef`、`SourceRef`、`VersionRef` / `SnapshotRef` 和 `TraceRef`；被排除证据应保留排除原因。
- Trace 要求（Trace Requirements）： 必须记录查询意图、source filters、排序维度、裁剪原因、selected / excluded evidence、检索为空或冲突状态。
- 持久化目标（Persistence Targets）： `RetrievalQuery`、`RetrievalResult`、`RetrievalEvidence`、`Citation` / `EvidenceRef`、`RAGContextAssembly` 和检索 trace；不直接写入报告、复盘、资产或薄弱项。
- 用户确认要求（User Confirmation Requirement）： 不适用；检索计划不需要用户确认，但使用未确认资产、候选资产或候选薄弱项时必须保留候选状态并交给业务 contract 决定。
- 重试 / 兜底（Retry / Fallback）：
  - 检索为空时可降级为仅核心输入、低置信度或要求补充材料。
  - `owner_mismatch`、`source_disabled` / `source_deleted` / `source_unavailable` 时必须排除来源并记录风险。
  - evidence too long 时裁剪为可展示摘要和 refs；冲突证据保留冲突标记，不静默择一。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `retrieval_not_required`、`retrieval_ready`、`retrieval_empty`、`retrieval_partial`、`evidence_conflict`、`source_unavailable`、`public_material_unpublished` 和 `internet_retrieval_unavailable`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 检索必须在服务端按 owner / public scope 过滤；公共材料未发布不得进入业务生成；互联网检索默认关闭，启用前需补来源治理和隐私边界。
- 测试策略（Test Strategy）： 使用确定性检索 fixture 覆盖 owner 隔离、公共材料发布状态、`source_deleted` / `source_disabled` / `source_archived`、空结果、冲突证据、过长证据裁剪和互联网检索不可用。
- 开放问题（Open Questions）： 具体检索数量、排序权重、公共材料发布流程、互联网检索启用条件和具体索引实现仍为后续设计问题，为 deferred_non_blocking。

### 10.3 `P-SHARED-003` 输出校验（Output Validation）

- Contract ID： `P-SHARED-003`
- 名称（Name）： Output Validation
- 模式（Mode）： `shared`
- 触发条件（Trigger）： 任一 AI 输出准备进入业务对象、候选对象、前端展示或持久化前触发。
- 目标（Goal）： 对候选输出进行结构化校验和业务语义校验，产出可保存、可修复、需重试或需人工校对的状态。
- 必需输入（Required Inputs）：
  - 候选结构化输出、当前 contract 的 output schema、validation requirement 和业务模式。
  - 当前 owner / scope、来源状态、`bound_output_evidence_refs`、`missing_evidence`、`conflicting_evidence`、trace refs、低置信度标记和用户确认要求。
  - 评分、建议、资产候选、薄弱项候选、报告或复盘等目标对象的状态语义。
- 可选输入（Optional Inputs）：
  - 原始模型输出引用、repair candidate、人工校对备注、上游 retrieval / context assembly 风险和历史 validation result。
- 检索来源（Retrieval Sources）： 不适用为主动检索；仅校验候选输出中声明的 evidence refs、`bound_output_evidence_refs` 和 trace refs 是否存在、合法、可追踪。
- 上下文装配（Context Assembly）：
  - 只读取候选输出、schema、validation requirement、来源引用和必要业务对象摘要。
  - 不重新组装生产 Prompt，不读取无关原文，不扩大上游上下文范围。
  - 不负责创建 evidence binding；证据绑定创建或补全由 `P-SHARED-005` 完成。
- 排除输入（Excluded Inputs）：
  - 原始 Prompt、provider payload、未脱敏 completion 原文、无权限来源、`source_unavailable` 正文和前端未校验 prompt。
  - 与当前 validation 无关的完整简历、完整岗位、完整会话历史和无关用户数据。
- 输出 Schema（Output Schema）：
  - `validation_result`
  - `schema_valid`
  - `semantic_valid`
  - `validated_output`
  - `rejected_fields`
  - `repairable_fields`
  - `normalized_failure_signals`
  - `score_validation_status`
  - `probability_forbidden_check`
  - `hidden_rule_exposure_check`
  - `risk_flags`
  - `trace_ref`
- 校验规则（Validation Rules）：
  - 结构化校验必须检查必填字段、字段类型、枚举值、0-100 分值范围、evidence refs、trace refs、confidence / low confidence 字段、next action 和 user confirmation requirement。
  - 业务语义校验必须检查不承诺精确通过概率、不把低置信度伪装成正常结论、不把候选资产写成正式资产、不把候选薄弱项写成正式薄弱项、不绕过用户确认。
  - 业务语义校验还必须检查不引用无权限来源、不引用 `source_unavailable` 正文、不把打磨模式当压力面、不把压力面当同题无限打磨、不生成与岗位 / 简历证据明显冲突的结论。
  - scoring candidate 校验必须检查 `score_value`、`score_scale`、`score_version`、`rubric_version`、`score_rule_version_ref`、`generated_by_task_id`、`confidence_level`、`evidence_refs`、`trace_refs` 和 `validation_status`。
  - scoring candidate 不得包含精确通过概率、录取概率、offer 概率、通过率百分比或等价文案；不得暴露隐藏评分规则、完整内部权重表、校准样例正文、系统 Prompt、completion 或 provider payload。
  - `validation_failed`、`score_out_of_range`、`evidence_missing`、`source_unavailable` 或隐藏规则外泄时，不得写入正式 `ScoreResult`、正式报告评分或确定性通过倾向。
  - 风险提示候选必须校验 `risk_level`、`risk_reason`、`confidence_level`、`evidence_refs`、`score_version`、`rubric_version` 和 disclaimer；缺证据时只能进入低置信度或 manual review。
  - 校验失败字段必须进入 `rejected_fields` 或 `repairable_fields`，不得静默进入 `validated_output`。
  - Validation 失败必须归一化为 §7.1 的 failure signal，例如 `schema_invalid`、`semantic_invalid`、`score_out_of_range`、`evidence_missing`、`evidence_conflict`、`validation_partial`、`output_incomplete` 或 `manual_check_required`。
- 低置信度规则（Low Confidence Rules）：
  - `validation_partial`、`output_incomplete`、score explanation weak、`evidence_conflict`、`source_unavailable` 或 `context_truncated_with_risk` 时标记低置信度。
  - 低置信度不能被 `schema_valid=true` 覆盖；结构化通过但语义弱通过时必须保留风险。
- 证据要求（Evidence Requirements）： 输出中每个关键结论引用的 evidence refs 必须存在、可访问、来源状态可解释；证据不足时必须显式消费 `missing_evidence`，证据冲突时必须显式消费 `conflicting_evidence`。本 contract 不创建新 evidence binding。
- Trace 要求（Trace Requirements）： 必须记录 validation trace，包含 schema 校验、语义校验、低置信度、rejected / repairable fields、retry / fallback 建议和上游 trace_ref。
- 持久化目标（Persistence Targets）： `LlmValidationResult`、validation trace、failure record、候选业务对象或通过校验的业务结果；正式资产、薄弱项或训练建议仍需业务 contract 和用户确认。
- 用户确认要求（User Confirmation Requirement）： 校验不替代用户确认；凡进入正式资产、正式薄弱项、训练建议确认或用户可见关键回流的结果，必须保留确认要求。
- 重试 / 兜底（Retry / Fallback）：
  - `validation failed` 时不得保存为正常业务事实，可进入 repair、retry、manual review 或 generation failed。
  - `partial usable` 可保存可用片段和风险标记，不能扩大数据范围或隐去失败字段。
  - retry / fallback 不得把原始 Prompt、completion 或 provider payload 写入日志。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `validation_passed`、`validation_failed`、`validation_partial`、`repair_required`、`manual_review_required`、`retry_allowed`、`fallback_allowed` 和 `generation_failed`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 校验层必须阻断无权限来源、`source_unavailable` 正文、未确认候选写正式对象和敏感字段外泄；日志只记录错误分类、trace id 和状态。
- 测试策略（Test Strategy）： 使用确定性输出 fixture 覆盖缺字段、类型错误、非法枚举、分数越界、缺 evidence / trace、低置信度伪装、模式边界错误、用户确认绕过和 `source_unavailable`。
- 开放问题（Open Questions）： 各业务 contract 的详细 output schema 已由对应子文档承接；共享 repair 策略细节、非业务通用阈值和最终调参属于 deferred_non_blocking，不重新打开评分、校验或 failure handling 的 M4 阻断边界。

### 10.4 `P-SHARED-004` 低置信度分类（Low Confidence Classification）

- Contract ID： `P-SHARED-004`
- 名称（Name）： Low Confidence Classification
- 模式（Mode）： `shared`
- 触发条件（Trigger）： 输入不足、检索失败、证据冲突、上下文裁剪、模型输出不完整或 validation 弱通过时触发。
- 目标（Goal）： 生成一致的低置信度分类、影响范围、用户可见提示和推荐动作，避免把风险结果伪装成正常高置信结论。
  - Low Confidence、`confidence_level`、`validation_status`、`source_availability` 和失败状态的 canonical 语义以 `../SEMANTICS_GLOSSARY.md` 为准；本 contract 只定义 Prompt / AI 输出侧分类。
- 必需输入（Required Inputs）：
  - 当前 contract、业务模式、任务目标、`validation_result`、`missing_evidence`、`conflicting_evidence`、`context_risk_flags`、`retrieval_status` 和 `failure_signals`。
  - required inputs 完整性、answer 完整性、resume / job evidence 完整性、source availability 和 `evidence_conflict` 状态。
  - 模型输出完整性、评分解释质量、真实面试输入完整度和 material context truncation 状态。
- 可选输入（Optional Inputs）：
  - 人工校对备注、用户补充材料请求、历史低置信度继承状态和失败恢复记录。
- 检索来源（Retrieval Sources）： 不适用为主动检索；只消费上游 retrieval、context assembly、validation 和 evidence binding 的状态。
- 上下文装配（Context Assembly）：
  - 只需要风险来源、受影响字段、证据摘要和 trace；不读取无关正文。
  - 若风险来源本身被裁剪或不可读，应保留 source availability 状态和 omitted refs。
  - 不重复执行 Output Validation，不重新判断 schema / semantic 是否通过；只消费 validation failure signals 并生成低置信度分类、用户可见提示和 recommended action。
- 排除输入（Excluded Inputs）：
  - 无权限来源正文、`source_unavailable` 正文、原始 Prompt、provider payload、密钥、token、cookie 和无关用户数据。
  - 不能用未校验证据补足低置信度解释。
- 输出 Schema（Output Schema）：
  - `low_confidence_flag`
  - `confidence_level`
  - `failure_signals`
  - `reasons`
  - `affected_sections`
  - `user_visible_message`
  - `recommended_action`
  - `trace_ref`
- 校验规则（Validation Rules）：
  - 触发条件至少覆盖 `required_input_missing`、insufficient answer、insufficient resume evidence、insufficient job evidence、`retrieval_empty`、`evidence_conflict`、`source_unavailable`、`validation_partial`、`output_incomplete`、score explanation weak、real interview input incomplete 和 `context_truncated_with_risk`。
  - 低置信度类型只能使用 `insufficient_input`、`insufficient_evidence`、`evidence_conflict`、`source_unavailable`、`validation_partial`、`model_output_incomplete`、`context_truncated`、`manual_check_required` 或后续明确扩展值。
  - `confidence_level` 只能使用 `high`、`medium`、`low`、`insufficient`；`insufficient` 必须阻断确定性通过倾向。
  - 用户可见表达必须说明影响范围，不得使用确定性结论包装低置信度结果。
  - `failure_signals` 是分类输入，不是二次 validation 结果；分类不得把 `schema_invalid`、`semantic_invalid` 或 `evidence_missing` 改写成高置信状态。
- 低置信度规则（Low Confidence Rules）：
  - 低置信度分类失败时，默认进入保守风险提示和 `manual_check_required`。
  - 低置信度不得阻断保存原始用户输入。
  - 低置信度结果不得静默进入正式资产或薄弱项；只能进入候选、待确认、部分可用或人工校对路径。
- 证据要求（Evidence Requirements）： 每个 reason 应关联 evidence ref、source ref、validation trace 或 omitted ref；证据不足本身也必须有 trace_ref。
- Trace 要求（Trace Requirements）： 必须记录触发条件、低置信度类型、受影响区块、推荐动作、用户可见提示和上游 trace。
- 持久化目标（Persistence Targets）： `LowConfidenceFlag`、validation result、业务对象风险标记、failure record、audit event 或候选对象风险字段；不直接创建正式业务结论。
- 用户确认要求（User Confirmation Requirement）： 标记低置信度不需要用户确认；但用户接受、修正、跳过或继续使用低置信度结果时，业务 contract 应记录确认或操作引用。
- 重试 / 兜底（Retry / Fallback）：
  - 推荐动作可以是重新生成、补充材料、人工校对、跳过或仅保存原始输入。
  - 分类失败时使用保守提示；重试不得扩大输入范围或读取不可用来源正文。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `low_confidence`、`partial_usable`、`manual_check_required`、`insufficient_input`、`source_unavailable` 和 `evidence_conflict`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 用户可见提示只展示必要摘要和风险范围，不暴露原始敏感正文、无权限证据或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖每类触发条件、低置信度类型映射、用户可见提示、保存原始输入不被阻断、候选对象不静默转正式对象。
- 开放问题（Open Questions）： `confidence_level` 的具体分级阈值和各业务页面的用户提示文案由后续业务 contract / UX 收敛，为 deferred_non_blocking；低置信度状态、触发条件、recommended actions 和不得转正式对象的边界已冻结。

### 10.5 `P-SHARED-005` 证据绑定（Evidence Binding）

- Contract ID： `P-SHARED-005`
- 名称（Name）： Evidence Binding
- 模式（Mode）： `shared`
- 触发条件（Trigger）： 输入证据准备进入 Context Assembly 前，或评分、建议、薄弱项、资产候选、报告、复盘结论准备进入展示、校验或持久化前触发。
- 目标（Goal）： 分别完成 Input Evidence Selection 与 Output Evidence Binding，确保进入上下文的证据和生成后结论的证据引用都可追踪、可展示范围明确、状态可解释。
- 必需输入（Required Inputs）：
  - Input Evidence Selection：来自简历、岗位、资产、薄弱项、历史报告、复盘、知识库 chunk、公共材料或用户显式选择来源的候选 evidence set。
  - Output Evidence Binding：候选结论、评分、建议、资产候选、薄弱项候选、报告段落或复盘项。
  - 可用 evidence set、source availability、owner / scope、生成时 `VersionRef` / `SnapshotRef` 和上游 trace_ref。
  - 当前业务模式、用户确认状态和输出校验要求。
- 可选输入（Optional Inputs）：
  - RAG 检索证据、历史报告 / 复盘摘要、真实面试补充材料、评分解释、用户确认记录和 displayable evidence summary。
- 检索来源（Retrieval Sources）：
  - 简历版本 / 模块、岗位版本、当前题目、当前回答、历史问答、点评、评分解释、RAG 检索证据。
  - 资产版本、薄弱项证据、模拟面试报告、模拟面试复盘、真实面试输入和用户确认记录。
- 上下文装配（Context Assembly）：
  - Input Evidence Selection 发生在 Retrieval Planning / Context Assembly 之前或过程中，只选择允许进入上下文的证据，不生成 `context_bundle`。
  - Output Evidence Binding 发生在模型输出或业务结果生成之后，只消费候选输出和证据集合，为 `P-SHARED-003` 与业务 contract 提供 evidence 绑定结果。
  - 历史结果必须引用生成时版本或快照，不引用当前最新对象替代历史来源。
- 排除输入（Excluded Inputs）：
  - owner 不一致、`source_deleted` / `source_disabled` / `source_unavailable` 正文、无 evidence ref 能力的材料。
  - 原始敏感正文默认展示、provider payload、原始 Prompt、密钥、token、cookie 和无关用户数据。
- 输出 Schema（Output Schema）：
  - `evidence_binding_result`
  - `selected_input_evidence_refs`
  - `bound_output_evidence_refs`
  - `missing_evidence`
  - `conflicting_evidence`
  - `displayable_evidence_summary`
  - `failure_signals`
  - `trace_ref`
- 校验规则（Validation Rules）：
  - Input Evidence Selection 必须排除 `owner_mismatch`、`source_unavailable`、`source_deleted`、`source_disabled`、`source_archived` 默认不可用正文、`public_material_unpublished` 和不可形成 evidence ref 的材料。
  - Output Evidence Binding 中每个关键结论至少应绑定一个 evidence ref，除非明确标记证据不足或不适用。
  - 评分必须绑定评分依据或评分解释；薄弱项必须绑定来源证据；资产候选必须绑定来源内容。
  - 通过倾向和风险提示必须绑定评分版本、规则版本、低置信度状态和 evidence refs；没有 evidence refs 时不得输出确定倾向或高置信风险提示。
  - 参考回答和技术解释如使用知识库，应绑定 RAG evidence。
  - 证据冲突、缺失或不可展示必须显式进入输出，不得静默删除。
  - Evidence Binding 失败时必须输出可被 Validation 和 Low Confidence 消费的 failure signals，例如 `evidence_missing`、`evidence_conflict`、`source_unavailable`、`owner_mismatch`、`snapshot_missing` 或 `manual_check_required`。
- 低置信度规则（Low Confidence Rules）：
  - `evidence_missing`、`evidence_conflict`、`source_unavailable`、`snapshot_missing` 或 evidence not displayable 时触发低置信度或 manual check。
  - 证据不足的关键结论不得升级为高置信正式结论。
- 证据要求（Evidence Requirements）：
  - `selected_input_evidence_refs` 只表示允许进入 Context Assembly 的证据，不等于生成后结论已经完成 evidence binding。
  - `bound_output_evidence_refs` 表示业务输出或候选输出已经绑定的证据，供 `P-SHARED-003` 校验。
  - evidence summary 可以展示给前端，但原始敏感正文不默认展示。
  - 无权限证据不得进入业务结果。
  - `source_deleted` / `source_disabled` / `source_unavailable` 时，应保留历史引用状态，但不得重新读取不可用正文。
- Trace 要求（Trace Requirements）： 必须记录候选结论、绑定证据、缺失证据、冲突证据、displayable summary 生成来源和 source availability。
- 持久化目标（Persistence Targets）： `EvidenceRef`、`Citation`、`ScoreEvidenceLink`、`SourceRef`、`VersionRef` / `SnapshotRef`、`TraceRef`、业务对象 evidence 字段或候选对象 evidence 字段。
- 用户确认要求（User Confirmation Requirement）： 证据绑定本身不需要用户确认；资产候选入库、薄弱项正式化、训练建议采纳或用户修正证据时仍需业务 contract 记录确认。
- 重试 / 兜底（Retry / Fallback）：
  - `evidence_missing` 时可回退为证据不足、要求补充材料或转人工校对。
  - `evidence_conflict` 时保留冲突双方摘要和 refs，不静默择一。
  - owner mismatch 或 evidence not displayable 时排除证据并记录风险。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `evidence_bound`、`missing_evidence`、`evidence_conflict`、`source_unavailable`、`evidence_not_displayable` 和 `snapshot_missing`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 前端只接收可展示证据摘要和必要引用；日志、trace 和错误不记录原始敏感正文、Prompt、completion 或 provider payload。
- 测试策略（Test Strategy）： 使用 fixture 覆盖评分证据、薄弱项证据、资产候选来源、RAG evidence、历史版本引用、`source_unavailable`、`owner_mismatch`、不可展示证据和冲突证据。
- 开放问题（Open Questions）： 证据摘要展示粒度、snapshot 缺失时的恢复策略和各业务 contract 的关键结论清单仍由后续设计收敛，为 deferred_non_blocking；证据绑定、source availability 和 trace 边界已冻结。

### 10.6 `P-SHARED-006` 会话摘要更新（Session Summary Update）

- Contract ID： `P-SHARED-006`
- 名称（Name）： Session Summary Update
- 模式（Mode）： `shared`
- 触发条件（Trigger）： 每轮用户回答后、每轮点评后、追问生成后、主题切换时、暂停前、恢复后、报告生成前、复盘生成前或会话结束时触发。
- 目标（Goal）： 更新可回溯到 `covered_turn_refs` 的 `SessionSummary`，减少后续 Context Assembly 对完整历史的依赖，同时不替代原始问答和 evidence refs。
- 必需输入（Required Inputs）：
  - 当前用户 / owner / role scope、会话 id、当前模式、会话状态和当前 `ResumeVersion` / `JobVersion`。
  - 当前题目、回答、点评、评分、追问、当前进展树位置、`covered_turn_refs` 和上一版 summary。
  - 已问问题、禁止重复追问列表、已暴露薄弱项、资产候选、低置信度和失败状态。
- 可选输入（Optional Inputs）：
  - 已生成参考回答要点、重要失分点、下一步建议、暂停恢复快照、报告 / 复盘生成前输入摘要和用户确认记录。
- 检索来源（Retrieval Sources）： 不适用为主动检索；仅消费当前会话内题答、点评、评分、追问、报告前输入和复盘前输入。
- 上下文装配（Context Assembly）：
  - 摘要内容应覆盖当前模式、当前岗位 / 简历版本、已问问题、用户回答要点、已暴露薄弱项、已确认资产候选、参考回答要点、重要失分点、禁止重复追问列表、当前进展树位置、下一步建议、低置信度和失败状态。
  - 压力面摘要应保留连续追问链路和节奏状态；打磨模式摘要应保留同题多轮改进过程。
  - 摘要服务后续 Context Assembly，但不得替代 evidence refs、`covered_turn_refs` 或原始问答记录。
- MVP Execution Policy:
  - MVP 默认优先使用 deterministic delta summary，而不是每轮强制 LLM summary。
  - 每轮更新只写入轻量结构化摘要字段，例如 asked question refs、answer key points、exposed weakness candidate refs、asset candidate refs、open threads、closed threads、forbidden repeat refs 和 risk flags。
  - LLM compression summary 不是每轮强制步骤；只作为历史过长、报告生成前、复盘生成前、暂停前或会话结束时的可选后处理。
  - 长耗时 summary 可异步或降级；summary 失败不得阻断保存原始问答。
  - summary 失败时必须产生 `summary_generation_failed` failure signal，并保留上一版可用 summary 或 `summary_status = summary_failed`。
- 排除输入（Excluded Inputs）：
  - 与当前会话无关的历史会话全文、无 owner 校验数据、`source_unavailable` 正文、provider payload、原始 Prompt、密钥、token、cookie 和无关用户数据。
  - 未通过业务校验的候选资产或候选薄弱项不得写成已确认事实。
- 输出 Schema（Output Schema）：
  - `SessionSummary`
  - `session_summary.status`
  - `summary_version`
  - `covered_turn_refs`
  - `source_session_snapshot_ref`
  - `asked_question_refs`
  - `answer_key_points`
  - `open_threads`
  - `closed_threads`
  - `forbidden_repeat_refs`
  - `weakness_candidate_refs`
  - `asset_candidate_refs`
  - `risk_flags`
  - `low_confidence_flags`
  - `trace_ref`
- 校验规则（Validation Rules）：
  - 摘要不能覆盖原始问答记录，不能成为唯一事实源，必须能回溯到 `covered_turn_refs`。
  - `covered_turn_refs` 必须存在且与 summary_version 连续；open / closed threads、forbidden repeat refs 和进展树位置必须一致。
  - 摘要中出现低置信度内容时必须保留风险标记。
  - 候选资产、候选薄弱项和训练建议不得因摘要更新而静默转正式对象。
- 低置信度规则（Low Confidence Rules）：
  - `summary_generation_failed`、covered turn refs missing、context conflict、low confidence inherited、resume failed 或 pause snapshot unavailable 时标记低置信度或失败。
  - 摘要低置信度不得阻断原始用户输入保存，但应影响后续上下文使用和用户提示。
- 证据要求（Evidence Requirements）： 摘要条目应引用 `covered_turn_refs`、题目、回答、点评、评分、用户确认或上游 evidence refs；摘要本身不替代 EvidenceRef。
- Trace 要求（Trace Requirements）： 必须记录 summary_version、`covered_turn_refs`、变更原因、风险继承、暂停 / 恢复状态和上游 trace。
- 持久化目标（Persistence Targets）： `SessionSummary`、summary version、session trace、risk flags、forbidden repeat refs、weakness candidate refs、asset candidate refs 和必要 audit event；不覆盖原始题答、点评或评分记录。
- 用户确认要求（User Confirmation Requirement）： 常规摘要更新不需要用户确认；若用户编辑、确认或拒绝摘要中的资产候选、薄弱项或下一步建议，应由业务 contract 记录 `UserConfirmationRef`。
- 重试 / 兜底（Retry / Fallback）：
  - `summary_generation_failed` 时保留上一版 summary 和失败状态，不阻断原始问答保存。
  - covered turn refs missing 或 pause snapshot unavailable 时停止使用该摘要作为高置信上下文，并要求恢复或人工校对。
  - context conflict 时保留冲突标记，不静默覆盖旧摘要。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `summary_updated`、`summary_partial`、`summary_failed`、`covered_turn_refs_missing`、`pause_snapshot_unavailable`、`resume_failed` 和 `low_confidence_inherited`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 摘要仍属于 owner 私有会话数据；前端展示只返回可展示摘要和风险状态，不暴露 Prompt、provider payload、原始敏感正文或无关会话内容。
- 测试策略（Test Strategy）： 使用多轮会话 fixture 覆盖回答后、点评后、追问后、主题切换、暂停、恢复、报告前、复盘前和结束时更新；验证 `covered_turn_refs`、禁止重复追问、低置信度继承和候选不转正式对象。
- 开放问题（Open Questions）： summary 扩展字段、压缩策略、暂停恢复快照扩展字段和同题多轮结束阈值为 deferred_non_blocking；MVP summary 最小字段、失败状态、trace 和候选不转正式对象边界已冻结。
