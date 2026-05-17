---
title: REPORT_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/report-contracts
---

# REPORT_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件遵守 `PROMPT_SPEC.md` §13 的 `AR-F4-FULL-001` 处置口径；复杂算法和实现细节按 deferred_non_blocking 承接。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 当前状态

Report contracts 已按主 catalog 更新为 Draft。本文只承载 `P-REPORT-001` 至 `P-REPORT-004` 的详细 contract 正文，不新增未登记 ID，不改变 contract ID、名称、目标或状态。

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-REPORT-001` | Interview Report Generation | 生成面试报告 | Draft |
| `P-REPORT-002` | Section Score Explanation | 生成分项评分解释 | Draft |
| `P-REPORT-003` | Risk and Pass Tendency Wording | 生成风险提示和通过倾向表达 | Draft |
| `P-REPORT-004` | Copyable Content Assembly | 生成可复制内容结构 | Draft |

## 3. Report Contract 细则

### 3.0 Report 公共字段与边界

#### Report 公共职责

Report contracts 只负责生成面试报告结构、解释分项评分、表达风险提示和通过倾向，以及组装可复制内容。Report contracts 不负责继续提问、重新评分 Pressure session、生成真实面试复盘、正式创建 Weakness、正式创建 Asset、正式创建 TrainingRecommendation 或实现 RAG / 检索底层能力；评分、通过倾向、风险提示和校准必须遵守 `PROMPT_SPEC.md` §7.2 的 `AR-F4-FULL-003` 全局口径。

MVP 只允许报告内容复制 / copy content。Report contracts 不生成文件，不生成 PDF、Markdown 文件、Word / docx 文件或批量文件，不提供文件生成类动作，也不把 `CopyableReportContent` 解释为外部文件产物。

#### Report 公共上游输入

Report contracts 可以消费 `P-PRESSURE-009` Report Input Assembly 输出、Pressure session summary、Pressure question / answer refs、Answer Quality Assessment refs、Follow-up chain refs、Pace Control refs、End Condition refs、Session Score refs、`ScoreResult` canonical score、evidence bundle refs、low confidence bundle、risk signal refs、weakness candidate refs、asset candidate refs、copyable content source refs、Job Match summary、Polish summary、RAG evidence 和用户报告偏好。上述输入必须按任务最小必要装配，不得默认塞入全部简历、全部岗位、全部原始回答全文、全部 Polish 历史、全部知识库或全部历史报告。

#### Report 公共检索边界

- `JobVersion` 和 `ResumeVersion` 是核心输入，不是 RAG。
- Pressure report input package 是结构化上游，不是 RAG。
- Job Match、Polish、Pressure outputs 是结构化上游，不是 RAG。
- RAG / 知识库可以用于技术解释、风险证据和考点引用增强，但不是 Report MVP 硬依赖。
- 互联网检索不是 MVP 默认强依赖，不得默认启用。
- 条件检索必须经过 `P-SHARED-002` Retrieval Planning。
- 无 RAG、无历史报告、无 Polish summary 时不得阻断基础报告生成。

#### Report 公共输出边界

Report 输出可以保存为面试报告、报告分项评分解释、风险提示文本、通过倾向表达、可复制内容结构、validation result、low confidence flag、evidence refs、trace refs 和 audit event。Report 输出不得直接写入正式 Weakness、正式 Asset、正式 TrainingRecommendation、真实面试复盘或压力面后续题目。如需产生弱项、资产或训练方向，只能输出候选引用、后续 contract 入口建议或用户确认入口。

#### Report 公共输出 Schema（Output Schema）

`P-REPORT-001` 至 `P-REPORT-004` 的 Output Schema 都必须包含以下公共字段；各 contract 可以增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `report_ref` | 否 | ref | 报告结果引用 |
| `report_input_package_ref` | 是 | ref | `P-PRESSURE-009` 生成的报告输入包引用 |
| `pressure_session_ref` | 是 | ref | 压力面会话引用 |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `score_result_refs` | 否 | ref[] | 评分结果引用 |
| `question_answer_refs` | 否 | ref[] | 题答引用 |
| `answer_quality_refs` | 否 | ref[] | 回答质量引用 |
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

`next_recommended_actions` 允许值至少包括 `view_report`、`copy_report_content`、`copy_report_section`、`start_review`、`mark_weakness_candidate`、`mark_asset_candidate`、`enter_polish_mode`、`enter_pressure_mode`、`generate_review_later`、`provide_more_evidence` 和 `manual_check_required`。这些 action 只是建议动作或流程入口，不得生成文件，不得直接写入正式 Weakness、正式 Asset 或 TrainingRecommendation；需要用户确认的 action 必须进入用户确认流。

#### Report 公共校验与失败边界

- 必须引用 `P-SHARED-001` Context Assembly、`P-SHARED-002` Retrieval Planning、`P-SHARED-003` Output Validation、`P-SHARED-004` Low Confidence Classification 和 `P-SHARED-005` Evidence Binding 中与当前任务相关的规则。
- 必须保留 validation、Low Confidence、EvidenceRef、TraceRef 和 AuditEvent 交接。
- 不得生成完整生产 Prompt 文案、原始 Prompt、completion 或 provider payload。
- 不得定义 API endpoint、物理数据库 schema、LLM provider、模型参数、向量数据库、embedding 模型或搜索服务。
- 不得承诺精确通过概率，不得输出“必过”“必挂”等确定性预测。
- 不得暴露隐藏评分规则、完整内部权重表、校准样例正文、系统 Prompt、completion 或 provider payload。

### 3.1 P-REPORT-001 面试报告生成（Interview Report Generation）

- Contract ID： `P-REPORT-001`
- 名称（Name）： Interview Report Generation
- 模式（Mode）： `report`
- 触发条件（Trigger）：
  - `P-PRESSURE-009` Report Input Assembly 完成后。
  - 用户请求生成压力面报告。
  - 用户重新生成报告。
  - 系统需要基于 Pressure session 产出展示报告。
- 目标（Goal）： 基于 `P-PRESSURE-009` Report Input Assembly 生成结构化面试报告；本 contract 生成报告结构和报告正文草案，但不生成独立正式复盘，不自动创建正式 Weakness、正式 Asset 或 TrainingRecommendation。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `report_input_package_ref`
  - `pressure_session_ref`
  - `JobVersion`
  - `ResumeVersion`
  - Pressure session summary
  - question / answer refs
  - answer quality refs
  - session score ref
  - evidence bundle refs
  - low confidence bundle
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- 可选输入（Optional Inputs）：
  - `P-SHARED-002` Retrieval Planning 结果
  - Job Match summary
  - Polish summary
  - weakness candidate refs
  - asset candidate refs
  - RAG evidence
  - 公共参考材料
  - user report preferences
- 检索来源（Retrieval Sources）：
  - 默认使用 Report Input Package、Pressure session summary、session score、question / answer refs、quality refs 和 evidence refs。
  - 条件读取 Job Match、Polish、候选弱项、候选资产、知识库 evidence 和用户报告偏好。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 无 RAG 或历史报告时仍可生成基础报告，但涉及技术事实或复杂风险解释时需低置信度。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001`。
  - 上下文至少包含 report input package、session summary、session score、分项证据、低置信度标记、source availability 和输出 schema。
  - 上下文过长时优先保留结构化摘要、评分解释、关键证据、风险信号、低置信度和报告必要 refs。
  - 不得默认塞入全部原始回答全文、全部 Polish 历史、全部知识库或全部历史报告。
- 排除输入（Excluded Inputs）：
  - 无权限来源正文、source deleted / disabled / unavailable 的正文和不可展示敏感原文。
  - 全部简历、全部岗位、全部原始回答全文、全部 Polish 历史、全部知识库、全部历史报告和默认互联网检索结果。
  - 正式 Weakness、正式 Asset 或 TrainingRecommendation 写入动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §3.0 的 Report 公共 Output Schema。
  - `interview_report_id_candidate`
  - `report_title`
  - `report_summary`
  - `overall_score_ref`
  - `section_summaries`
  - `strengths_summary`
  - `weakness_candidate_refs`
  - `asset_candidate_refs`
  - `risk_summary_refs`
  - `low_confidence_summary`
  - `evidence_summary_refs`
  - `next_recommended_actions`
  - `report_sections`
  - `excluded_sources`
  - `source_availability_summary`
- 校验规则（Validation Rules）：
  - 报告必须基于 Report Input Package。
  - 报告不得虚构题目、回答、评分或证据。
  - 报告不得承诺精确通过概率。
  - 报告不得输出“必过”“必挂”等确定性预测。
  - 报告不得把低置信度内容包装成高置信结论。
  - 报告不得把候选 Weakness / Asset 写成正式对象。
  - 报告必须保留 source availability、evidence refs、trace refs 和 validation result refs。
  - 报告不得包含无权限来源正文。
- 低置信度规则（Low Confidence Rules）：
  - report input package 缺失。
  - session score 缺失或低置信度。
  - question / answer refs 不足。
  - answer quality refs 不足。
  - evidence refs 不足。
  - source unavailable。
  - 关键输入被裁剪。
  - 低置信度占比过高。
  - 技术解释需要 RAG evidence 但不可用。
- 证据要求（Evidence Requirements）： 报告摘要、分项总结、优势摘要、候选 Weakness / Asset、风险摘要、低置信度摘要和 excluded sources 必须绑定 source refs、evidence refs、validation result refs 和 trace refs；证据不足或来源不可用时必须保留低置信度和 source availability。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、报告结构生成、报告正文草案生成、source availability 聚合、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `InterviewReport` 或等价报告对象。
  - `ReportSection` 或等价报告章节对象。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 报告可直接展示给用户。
  - 用户可以复制报告内容、进入复盘、回到 Polish、重新生成或手动校对。
  - 由报告派生的正式 Weakness、Asset 或 TrainingRecommendation 必须进入后续候选 / 确认链路。
  - 本 contract 不创建正式 Weakness、Asset 或 TrainingRecommendation。
- 重试 / 兜底（Retry / Fallback）：
  - report input package、pressure session、岗位版本、简历版本或 owner 校验缺失时停止正常报告生成，返回失败或补充材料路径。
  - RAG、历史报告、Polish summary 或用户报告偏好缺失时可生成基础报告，并标记缺失输入、excluded sources 和低置信度。
  - 重试不得默认启用互联网检索、虚构题答 / 评分 / 证据、输出精确通过概率或创建正式回流对象。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `report_available`、`report_partial`、`report_low_confidence`、`report_validation_failed` 和 `report_generation_failed`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 报告只使用当前 owner 的授权 refs、摘要和可展示证据摘要；不得暴露无权限来源正文、原始 Prompt、completion 或 provider payload，不得绕过用户确认写入正式回流对象。
- 测试策略（Test Strategy）： 使用 fixture 覆盖完整报告、缺少 report input package、缺少 session score、source unavailable、低置信度占比过高、禁止虚构题答 / 评分 / 证据、禁止精确通过概率、禁止必过 / 必挂、无 RAG 降级和不得创建正式 Weakness / Asset / TrainingRecommendation。
- 开放问题（Open Questions）： 隐藏评分公式实现细节、复杂分项权重调参、RAG 实现、报告生成 readiness 阈值和最终 UX 文案润色仍待后续 contract / API / UX 收敛，为 deferred_non_blocking；通过倾向展示已收敛为分档表达，风险提示已收敛为 `risk_level` / `risk_reason` / evidence / confidence / validation 绑定，不再作为本 contract 的开放问题。

### 3.2 P-REPORT-002 分项评分解释（Section Score Explanation）

- Contract ID： `P-REPORT-002`
- 名称（Name）： Section Score Explanation
- 模式（Mode）： `report`
- 触发条件（Trigger）：
  - `P-REPORT-001` 需要生成 section score explanation。
  - `P-PRESSURE-008` Session Score 已生成，需要报告分项解释。
  - 用户请求解释某个分项得分。
  - 用户重新生成报告或评分解释。
- 目标（Goal）： 解释报告中的分项评分；本 contract 冻结正式报告评分解释必须具备的 0-100 产品刻度、rubric / rule version、证据、低置信度、trace、免责声明和禁止精确概率边界，不暴露隐藏评分规则。
  - 评分 score type、默认维度、权重、公式、缺失维度处理和 F7 scoring fixture 以 `../SCORING_SPEC.md` 的 `report_section` / `polish_report` 规则为 canonical；本 contract 不重复定义内部权重表，也不得暴露隐藏评分规则。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `report_input_package_ref`
  - `pressure_session_ref`
  - `P-PRESSURE-008` Session Score result
  - `ScoreResult` canonical score
  - dimension scores 或等价分项输入
  - answer quality refs
  - evidence refs
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- 可选输入（Optional Inputs）：
  - `P-SHARED-002` Retrieval Planning 结果
  - coverage summary
  - quality trend summary
  - risk signals
  - public scoring rubric 或已登记评分口径
  - RAG evidence
- 检索来源（Retrieval Sources）：
  - 默认使用 Session Score、dimension scores、answer quality refs 和 evidence refs。
  - 条件读取公共评分口径、RAG evidence、Job Match / Polish summary。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
  - 评分规则版本缺失时必须进入 low confidence、validation failed 或 manual review，不得虚构公式。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001`。
  - 上下文至少包含 session score、dimension scores、score explanation、quality trend、coverage、positive / negative evidence 和输出 schema。
  - 上下文过长时优先保留每个分项的分数、解释、证据和低置信度。
  - 不得默认塞入全部原始回答全文或全部知识库材料。
- 排除输入（Excluded Inputs）：
  - LLM 单次输出临时发明的评分公式、权重、阈值或校准方法。
  - 隐藏评分规则、完整内部权重表、校准样例正文和内部校准细节。
  - 全部原始回答全文、全部知识库材料、全部历史报告和默认互联网检索结果。
  - 正式 Weakness、正式 Asset 或 TrainingRecommendation 写入动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §3.0 的 Report 公共 Output Schema。
  - `section_score_explanation_id_candidate`
  - `section_scores`
  - 每个 section 的 `section_id`
  - 每个 section 的 `section_name`
  - 每个 section 的 `score_value`
  - 每个 section 的 `score_scale`
  - 每个 section 的 `score_version`
  - 每个 section 的 `rubric_version`
  - 每个 section 的 `confidence_level`
  - 每个 section 的 `validation_status`
  - 每个 section 的 `score_explanation`
  - 每个 section 的 `positive_evidence_refs`
  - 每个 section 的 `negative_evidence_refs`
  - 每个 section 的 `uncertainty_reasons`
  - `score_rule_version_ref`
  - `non_decision_disclaimer`
- 校验规则（Validation Rules）：
  - `score_value` 必须在 0-100 范围，且 `score_scale` 必须声明为 `0_100_product_scale`。
  - `score_version`、`rubric_version`、`score_rule_version_ref`、`confidence_level`、`validation_status`、`evidence_refs` 和 `trace_refs` 必须存在。
  - 不得虚构评分公式、权重、阈值或校准方法，不得暴露隐藏评分规则。
  - 不得输出精确通过概率。
  - 不得输出录取概率、offer 概率、通过率百分比或等价措辞。
  - 不得输出“必过”“必挂”等确定性预测。
  - 每个分项解释必须绑定 evidence refs 或明确低置信度。
  - 分数解释不得与 Session Score 冲突。
  - 低分和高分都必须有解释。
  - 评分规则版本缺失、source unavailable、evidence missing 或 validation failed 时，不得落正式报告评分。
- 低置信度规则（Low Confidence Rules）：
  - session score 缺失或低置信度。
  - dimension scores 缺失。
  - evidence refs 不足。
  - score explanation 不足。
  - 评分规则版本、rubric version 或 score version 缺失。
  - 分项解释与总分冲突。
  - 上下文裁剪影响评分依据。
- 证据要求（Evidence Requirements）： 每个 section 的分数、解释、positive evidence、negative evidence、uncertainty reasons、规则版本、可信度和免责声明必须绑定 source refs、evidence refs、validation result refs 和 trace refs；证据不足或规则版本缺失时必须保留低置信度。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、分项解释生成、评分一致性检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `ReportSectionScoreExplanation` 或等价报告分项解释对象。
  - `ScoreExplanation`
  - `ScoreEvidenceLink`
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 分项解释可直接展示给用户。
  - 用户可以查看证据、重新生成、进入复盘或手动校对。
  - 本 contract 不创建正式 Weakness、Asset 或 TrainingRecommendation。
- 重试 / 兜底（Retry / Fallback）：
  - session score、dimension scores、岗位版本、简历版本或 owner 校验缺失时停止正常分项解释，返回失败或补充材料路径。
  - 评分规则版本、公共评分口径或 RAG evidence 缺失时可生成低置信度基础解释或进入 manual review，但不得落正式报告评分。
  - 重试不得默认启用互联网检索、虚构评分公式、输出精确通过概率或创建正式回流对象。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `section_score_explanation_available`、`section_score_explanation_partial`、`section_score_explanation_low_confidence`、`section_score_explanation_validation_failed` 和 `score_rule_unknown`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 分项解释只使用当前 owner 的授权评分、题答摘要和可展示证据摘要；不得暴露无权限来源正文、原始 Prompt、completion、provider payload、隐藏评分规则或内部校准细节。
- 测试策略（Test Strategy）： 使用 fixture 覆盖 0-100 范围、分项展示刻度、低分解释、高分解释、评分规则版本缺失、分项与总分冲突、禁止虚构公式 / 权重 / 阈值、禁止精确通过概率、禁止必过 / 必挂、validation failed 不落正式评分和不得创建正式回流对象。
- 开放问题（Open Questions）： 隐藏评分规则实现细节、真实招聘结果校准、复杂调参和运营发布流程仍待后续 API / F5 / F7 收敛；本 contract 已冻结 MVP 可展示分、版本、证据、低置信度和禁止概率边界。

### 3.3 P-REPORT-003 风险与通过倾向措辞（Risk and Pass Tendency Wording）

- Contract ID： `P-REPORT-003`
- 名称（Name）： Risk and Pass Tendency Wording
- 模式（Mode）： `report`
- 触发条件（Trigger）：
  - `P-REPORT-001` 需要生成风险提示。
  - `P-REPORT-002` 生成分项评分解释后需要风险表达。
  - 用户请求查看面试风险和通过倾向。
  - 报告需要展示风险摘要或通过倾向文案。
- 目标（Goal）： 生成风险提示和通过倾向表达；本 contract 不承诺精确通过概率，不输出确定性录用预测，只生成基于证据和低置信度边界的风险表达。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `report_input_package_ref`
  - `pressure_session_ref`
  - session score ref
  - risk signal refs
  - low confidence bundle
  - source availability summary
  - evidence refs
  - `JobVersion`
  - `ResumeVersion`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- 可选输入（Optional Inputs）：
  - `P-SHARED-002` Retrieval Planning 结果
  - section score explanations
  - Job Match mismatch / improvement points
  - Polish weakness candidates
  - user report preferences
  - historical mock interview trends
- 检索来源（Retrieval Sources）：
  - 默认使用 session score、risk signals、low confidence bundle、source availability 和 evidence refs。
  - 条件读取 section score explanations、Job Match / Polish 上游、历史模拟面试趋势。
  - 条件读取必须经过 `P-SHARED-002`。
  - 互联网检索不默认启用。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001`。
  - 上下文至少包含 score、风险信号、低置信度、source availability、关键 evidence 和输出 schema。
  - 上下文过长时优先保留风险信号、低置信度原因、source availability 和评分解释。
  - 不得默认塞入全部原始回答、全部历史报告或全部知识库材料。
- 排除输入（Excluded Inputs）：
  - 精确通过概率、确定性录用预测和无证据风险判断。
  - 全部原始回答、全部历史报告、全部知识库材料和默认互联网检索结果。
  - 正式 Weakness、正式 Asset 或 TrainingRecommendation 写入动作。
  - 原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §3.0 的 Report 公共 Output Schema。
  - `risk_wording_id_candidate`
  - `risk_summary`
  - `risk_items`
  - 每个 risk item 的 `risk_type`
  - 每个 risk item 的 `risk_level`
  - 每个 risk item 的 `risk_reason`
  - 每个 risk item 的 `description`
  - 每个 risk item 的 `evidence_refs`
  - 每个 risk item 的 `score_version`
  - 每个 risk item 的 `rubric_version`
  - 每个 risk item 的 `score_rule_version_ref`
  - 每个 risk item 的 `confidence_level`
  - 每个 risk item 的 `validation_status`
  - 每个 risk item 的 `low_confidence_impact`
  - `pass_tendency_wording`
  - `pass_tendency_level_hint`
  - `pass_tendency_confidence_level`
  - `uncertainty_disclaimer`
  - `non_decision_disclaimer`
  - `forbidden_wording_flags`
  - `user_visible_caveats`
- 校验规则（Validation Rules）：
  - 不得输出精确通过概率。
  - 不得输出录取概率、offer 概率、通过率百分比或“你有 73% 概率通过”等等价措辞。
  - 不得输出“必过”“必挂”“稳过”“一定失败”等确定性预测。
  - 风险提示必须绑定 risk signals、evidence refs 或 low confidence flags。
  - `risk_level` 只能使用 `low`、`medium`、`high`、`unknown` 或等价固定枚举。
  - 通过倾向必须使用分档表达：`low` / `medium` / `high` / `caution` / `insufficient_evidence`。
  - 低置信度、source unavailable、证据不足、score rule 缺失或 validation failed 时，必须降级为 `insufficient_evidence` / “证据不足，无法判断倾向”，不得输出确定性通过倾向。
  - 用户可见 caveat 必须包含可信度说明和非决策性免责声明。
  - 不得把候选 Weakness 写成正式诊断。
  - 不得把岗位匹配缺口直接包装成用户能力缺陷。
  - 不得制造恐吓、歧视或攻击性表达。
- 低置信度规则（Low Confidence Rules）：
  - risk signals 缺失。
  - score explanation 缺失或低置信度。
  - evidence refs 不足。
  - source unavailable。
  - session score 低置信度。
  - 用户输入不足。
  - 风险和评分解释冲突。
  - 通过倾向无法从证据支持。
- 证据要求（Evidence Requirements）： 每个 risk item、risk summary、pass tendency wording、uncertainty disclaimer、non decision disclaimer、forbidden wording flags 和 user visible caveats 必须绑定 source refs、evidence refs、validation result refs、score version、rubric version 和 trace refs；证据不足或来源不可用时必须保留低置信度和用户可见 caveat。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖条件 Retrieval Planning、Input Evidence Selection、Context Assembly、风险表达生成、禁止措辞检查、source availability caveat 聚合、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `ReportRiskWording` 或等价风险表达对象。
  - `ReportPassTendencyWording` 或等价通过倾向表达对象。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 风险和通过倾向可展示给用户。
  - 用户可以查看依据、重新生成、进入复盘或手动校对。
  - 本 contract 不创建正式 Weakness、Asset 或 TrainingRecommendation。
- 重试 / 兜底（Retry / Fallback）：
  - risk signals、session score、岗位版本、简历版本或 owner 校验缺失时停止正常风险表达或返回 `low_confidence`。
  - section score explanations、历史模拟面试趋势或用户报告偏好缺失时可生成基础风险表达，并标记缺失输入、source availability 和低置信度。
  - 重试不得默认启用互联网检索、输出精确通过概率、输出确定性预测或创建正式回流对象。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `risk_wording_available`、`risk_wording_partial`、`risk_wording_low_confidence`、`risk_wording_validation_failed`、`pass_tendency_available` 和 `pass_tendency_insufficient_evidence`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 风险和通过倾向表达只使用当前 owner 的授权评分、风险信号和可展示证据摘要；不得暴露无权限来源正文、原始 Prompt、completion、provider payload、隐藏评分规则、内部校准细节、未脱敏第三方公司 / 面试官 / 个人敏感信息，不得输出恐吓、歧视或攻击性表达。
- 测试策略（Test Strategy）： 使用 fixture 覆盖有风险信号、无风险信号、source unavailable、score explanation 缺失、风险和评分解释冲突、低置信度不输出确定倾向、禁止精确通过概率、禁止必过 / 必挂 / 稳过 / 一定失败、候选 Weakness 不得写成正式诊断、risk_level 与 evidence_refs 同步存在、score_version / rubric_version 存在和不得创建正式回流对象。
- 开放问题（Open Questions）： 真实招聘结果校准、复杂风险排序和最终 UX 展示文案润色仍待后续 API / UX / F7 收敛；本 contract 已冻结 MVP 通过倾向分档、风险等级、证据绑定、免责声明和禁止概率边界。

### 3.4 P-REPORT-004 可复制内容装配（Copyable Content Assembly）

- Contract ID： `P-REPORT-004`
- 名称（Name）： Copyable Content Assembly
- 模式（Mode）： `report`
- 触发条件（Trigger）：
  - `P-REPORT-001` 生成报告后。
  - `P-REPORT-002` 和 `P-REPORT-003` 生成分项解释与风险表达后。
  - 用户点击复制整份报告或复制某个 section。
  - 系统需要生成剪贴板可用的报告内容结构。
- 目标（Goal）： 从报告、评分解释、风险提示、证据摘要和用户可见内容中组装可复制内容结构；本 contract 只组装剪贴板可用内容，不改变报告结论，不生成新的评分，不生成新的风险判断，不生成文件。
- 必需输入（Required Inputs）：
  - `OwnerRef`
  - `report_ref`
  - report sections
  - section score explanations
  - risk wording
  - pass tendency wording
  - displayable evidence summary
  - low confidence flags
  - source availability summary
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-005` Evidence Binding 要求
- 可选输入（Optional Inputs）：
  - `P-SHARED-002` Retrieval Planning 结果
  - user copy preferences
  - redaction preferences
  - markdown_copy_format_preference
  - excluded sources
  - copyable content source refs
- 检索来源（Retrieval Sources）：
  - 默认不需要额外检索，优先消费已生成报告和可展示证据摘要。
  - 如需读取额外 source，应经过 `P-SHARED-002`。
  - 不得默认启用互联网检索。
  - 不得为复制内容重新生成报告结论。
- 上下文装配（Context Assembly）：
  - 必须继承 `P-SHARED-001` 的最小化上下文原则。
  - 上下文至少包含报告结构、用户可见 section、风险提示、低置信度、可展示证据摘要、脱敏 / 排除规则和输出 schema。
  - 不得包含无权限来源正文、原始 Prompt、completion 或 provider payload。
  - 不得默认塞入完整原始回答全文，除非报告已明确允许展示并通过隐私边界。
- 排除输入（Excluded Inputs）：
  - 新报告结论、新评分和新风险判断。
  - 无权限来源正文、不可展示敏感原文、原始 Prompt、completion 或 provider payload。
  - 未通过脱敏 / 排除规则的字段。
  - 默认互联网检索结果。
  - 正式 Weakness、正式 Asset 或 TrainingRecommendation 写入动作。
- 输出 Schema（Output Schema）：
  - 公共字段：必须完整包含 §3.0 的 Report 公共 Output Schema。
  - `copyable_content_id_candidate`
  - `content_format`
  - `markdown_content`
  - `section_blocks`
  - 每个 section block 的 `section_id`
  - 每个 section block 的 `title`
  - 每个 section block 的 `body`
  - 每个 section block 的 `source_refs`
  - 每个 section block 的 `evidence_summary_refs`
  - `redacted_fields`
  - `excluded_sections`
  - `copy_safety_notes`
  - `clipboard_format_hint`
  - `content_hash_candidate`
- 校验规则（Validation Rules）：
  - 可复制内容必须来源于已生成报告、分项解释和风险提示。
  - 不得新增报告结论。
  - 不得新增评分。
  - 不得新增风险判断。
  - 不得生成 PDF、Markdown 文件、Word / docx 文件或批量文件。
  - 不得包含无权限来源正文。
  - 不得包含原始 Prompt、completion 或 provider payload。
  - 不得包含隐藏评分规则、完整内部权重表、校准样例正文或内部校准细节。
  - 必须保留低置信度和 source availability caveat。
  - 可复制 Markdown 文本必须保持标题、列表和引用结构稳定，便于剪贴板使用。
  - 如存在敏感字段，应脱敏或排除。
- 低置信度规则（Low Confidence Rules）：
  - report_ref 缺失。
  - section score explanation 缺失。
  - risk wording 缺失。
  - low confidence flags 缺失。
  - source availability summary 缺失。
  - 可复制内容与报告正文不一致。
  - 脱敏规则不完整。
  - 用户复制偏好冲突。
- 证据要求（Evidence Requirements）： 每个 section block、markdown_content、redacted fields、excluded sections、copy safety notes 和 content hash candidate 必须绑定 source refs、evidence refs、validation result refs 和 trace refs；可展示证据摘要不得等同于原始敏感正文。
- Trace 要求（Trace Requirements）： 必须记录 `TraceRef`，覆盖最小 Context Assembly、复制内容组装、脱敏 / 排除检查、Markdown 结构检查、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- 持久化目标（Persistence Targets）：
  - `CopyableReportContent` 或等价可复制内容对象。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
- 用户确认要求（User Confirmation Requirement）：
  - 用户可以复制整份报告、复制单个 section、选择 section 或重新生成可复制内容。
  - 本 contract 不创建正式 Weakness、Asset 或 TrainingRecommendation。
  - 本 contract 不改变报告结论。
- 重试 / 兜底（Retry / Fallback）：
  - report_ref、报告章节或 owner 校验缺失时停止正常复制内容组装，返回失败或补充材料路径。
  - section score explanation、risk wording、low confidence flags 或 source availability summary 缺失时可生成 partial 内容，并标记缺失输入和低置信度。
  - 重试不得默认启用互联网检索、重新生成报告结论、新增评分或新增风险判断。
- API 状态映射（API State Mapping）： 只定义状态语义，包括 `copyable_content_available`、`copyable_content_partial`、`copyable_content_low_confidence`、`copyable_content_validation_failed` 和 `copyable_content_redaction_required`；不定义 endpoint 或 schema。
- 安全说明（Security Notes）： 可复制内容必须遵守当前 owner、展示权限、脱敏和来源可用性边界；不得包含无权限来源正文、`system prompt`、原始 Prompt、completion、provider payload、隐藏评分规则、密钥、token、cookie、未经脱敏的第三方 / 公司 / 个人敏感信息或不可展示敏感原文。
- 测试策略（Test Strategy）： 使用 fixture 覆盖完整报告复制、单 section 复制、缺少分项解释、缺少风险提示、source unavailable、敏感字段脱敏、禁止生成文件、禁止新增报告结论 / 评分 / 风险判断、禁止包含 `system prompt` / 原始 Prompt / completion / provider payload / 隐藏评分规则和用户复制偏好冲突。
- 开放问题（Open Questions）： 复制反馈 UI、脱敏策略细节、剪贴板格式提示和用户设备副本责任边界仍待后续 API / UX / 安全设计收敛，为 deferred_non_blocking。

### 3.5 Report Contract 关系

- `P-REPORT-001` 基于 `P-PRESSURE-009` Report Input Assembly 生成面试报告。
- `P-REPORT-002` 基于 session score、dimension scores、answer quality 和 evidence 生成分项评分解释。
- `P-REPORT-003` 基于 risk signals、low confidence、source availability 和 score explanation 生成风险提示和通过倾向表达。
- `P-REPORT-004` 基于已生成报告、分项解释和风险提示组装可复制内容。
- `P-REPORT-001` 至 `P-REPORT-004` 都必须引用 Shared Contracts，并至少交接 validation、Low Confidence、EvidenceRef、TraceRef 和 AuditEvent。
- Report contracts 可以消费 Pressure 输出，但不得重新执行 Pressure 评分或生成追问。
- Report contracts 不得直接写入正式 Weakness、正式 Asset 或 TrainingRecommendation。
- Report contracts 不实现隐藏评分公式细节、复杂分项权重调参、复杂风险排序或 RAG 底层能力；这些为 deferred_non_blocking。通过倾向分档、风险等级、证据绑定、低置信度降级和禁止精确概率边界必须遵守本文件 §3.0 / §3.2 / §3.3 与 `PROMPT_SPEC.md` §7.2 的已冻结规则。
- Review / Weakness / Asset / Training contracts 当前均已按 `PROMPT_SPEC.md` canonical registry 进入 Draft；Report contracts 只消费其候选、建议或确认后的引用，不自动创建正式 Weakness、Asset 或 TrainingRecommendation，也不关闭这些 domain 的 deferred_non_blocking 细化项。
