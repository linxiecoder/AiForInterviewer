---
title: JOB_MATCH_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/job-match-contracts
---

# JOB_MATCH_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件遵守 `PROMPT_SPEC.md` §13 的 `AR-F4-FULL-001` 处置口径；复杂算法和实现细节按 deferred_non_blocking 承接。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 适用范围

本文件承载主 catalog 中 `P-JOBMATCH-001` 至 `P-JOBMATCH-004` 的详细 contract 正文。Job Match contracts 只描述岗位匹配分析链路，不写完整 Prompt 文案。

## 11. Job Match Contract 细则

本节填充岗位匹配分析链路的 AI 子任务 contract。四个 contract 只定义输入、检索依赖、上下文装配、输出结构、校验、低置信度、证据、trace、持久化交接和安全边界；不写完整生产 Prompt 文案，不暴露隐藏评分公式、完整内部权重表、复杂阈值、模型供应商、模型参数、向量数据库、embedding 模型、API endpoint 或物理数据库 schema。`AR-F4-FULL-003` 范围内的 0-100 产品刻度、rubric / rule version、最小权重策略、禁止精确概率、低置信度降级和 MVP fixture 校准策略以本文件、`PROMPT_SPEC.md`、`DATA_MODEL.md` 与 `API_SPEC.md` 的当前规则为准。

### 11.0 Job Match Output Schema 公共字段

四个 Job Match contract 的 Output Schema 都必须包含以下公共字段；各 contract 可在此基础上增加专属字段，但不得删除公共字段或改变字段语义。

| 字段 | 必填 | 类型 / 枚举 | 说明 |
|---|---|---|---|
| `status` | 是 | `success` / `partial` / `low_confidence` / `validation_failed` / `generation_failed` | 子任务结果状态 |
| `contract_id` | 是 | string | 当前 contract id |
| `job_version_ref` | 是 | ref | 生成时岗位版本或快照引用 |
| `resume_version_ref` | 是 | ref | 生成时简历版本或快照引用 |
| `source_refs` | 是 | ref[] | 被消费的来源引用 |
| `source_availability` | 是 | `available` / `partial` / `unavailable` / `mixed` | 来源可用性聚合状态；底层来源状态仍沿用 §6.1 的 `source_*` 枚举 |
| `evidence_refs` | 是 | ref[] | 支撑关键结论的证据 |
| `displayable_evidence_summary` | 否 | object[] | 可展示给前端的证据摘要，不等于原始敏感正文 |
| `low_confidence_flags` | 是 | object[] | 低置信度标记，必须可追溯到 `P-SHARED-004` |
| `validation_result_ref` | 是 | ref | `P-SHARED-003` 校验结果引用 |
| `trace_refs` | 是 | ref[] | 检索、上下文装配、模型调用、校验、低置信度和持久化交接等过程引用 |
| `next_recommended_actions` | 否 | enum[] | 非写入动作建议，允许值见本节下方 |
| `user_confirmation_required` | 是 | boolean | 是否需要用户确认后才能回流正式对象 |

`next_recommended_actions` 只表达建议动作，不直接写入正式 `Weakness`、`Asset` 或 `TrainingRecommendation`。允许值包括 `polish_entry`、`pressure_entry`、`review_later`、`confirm_weakness_candidate`、`edit_weakness_candidate`、`skip_weakness_candidate`、`merge_weakness_candidate`、`regenerate_job_match`、`provide_more_resume_evidence` 和 `provide_more_job_evidence`。其中需要用户确认的动作必须进入用户确认流，并形成 `UserConfirmationRef` 或等价记录。映射语义：`polish_entry` / `pressure_entry` 只表示后续 Polish / Pressure contract 入口建议；`regenerate_job_match` 映射为重新触发 Job Match contract；`confirm_weakness_candidate`、`edit_weakness_candidate`、`skip_weakness_candidate` 和 `merge_weakness_candidate` 映射为候选薄弱项确认流；补充证据类 action 只要求用户补充材料。

### 11.1 `P-JOBMATCH-001` Match Analysis

- Contract ID: `P-JOBMATCH-001`
- Name: Match Analysis
- Mode: `job_match`
- Trigger:
  - 用户在岗位与简历存在、已通过 owner / scope 校验且可访问时发起岗位匹配分析。
  - 用户主动重新生成岗位匹配分析。
  - 后续模拟面试前需要刷新匹配分析输入时，由应用编排层触发。
- Goal: 基于 `JobResumeBinding`、`JobVersion`、`ResumeVersion` 和必要 `ResumeModule` 生成可解释、可追踪、可进入后续打磨模式、压力面模式、报告、复盘、薄弱项、资产和训练建议的岗位匹配分析结构。
- Required Inputs:
  - `OwnerRef`
  - `JobResumeBinding`
  - `JobVersion`
  - `ResumeVersion`
  - 必要的 `ResumeModule`
  - 当前 `contract_id`
  - 目标输出 schema
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - 用户已确认的 `AssetVersion`
  - 已存在的 `Weakness`
  - 历史 `JobMatchAnalysis`
  - 历史 `InterviewReport`
  - 历史 `MockInterviewReview`
  - 历史 `RealInterviewReview`
  - 公共参考材料
  - 知识库 / RAG evidence
- Retrieval Sources:
  - 默认使用 `ResumeVersion` 和 `JobVersion` 作为核心输入，不把它们误写成 RAG。
  - 条件检索用户已确认资产、既有薄弱项、历史报告、模拟复盘和真实复盘。
  - 知识库 / RAG 仅用于证据增强或通用岗位能力解释，不作为默认必需输入。
  - 互联网检索不是 MVP 默认强依赖，不在本 contract 默认启用。
- Context Assembly:
  - 必须消费 `P-SHARED-001` 产出的 `context_bundle`，并继承其 owner 校验、来源可用性、裁剪和 trace 规则。
  - 上下文至少包含岗位摘要、简历摘要、关键简历模块、绑定关系、当前分析目标、必要证据和输出 schema。
  - 不得默认塞入全部历史会话、全部资产、全部复盘或无关知识库材料。
  - 上下文过长时，优先保留岗位要求、简历中与岗位强相关模块、证据引用和输出 schema；被裁剪内容必须进入 omitted refs 或风险标记。
- Excluded Inputs:
  - owner 不一致、source deleted / disabled / unavailable 的正文。
  - 未经用户确认的资产候选、薄弱项候选或训练建议作为已确认事实。
  - 无关历史会话全文、无关用户数据、原始 Prompt、原始 completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
  - 默认互联网检索结果、无法形成 `EvidenceRef` 的材料和要求覆盖系统规则的用户 / RAG 指令。
- Output Schema:
  - 公共字段：必须完整包含 §11.0 的 Job Match 公共字段。
  - 本 contract 是 orchestration / result aggregate，只汇总子 contract 结果和引用，不直接生成或写入正式 `Weakness`。
  - `analysis_id_candidate`
  - `binding_ref`
  - `analysis_summary`
  - `match_score_ref`
  - `match_points_ref`
  - `mismatch_points_ref`
  - `improvement_points_ref`
  - `weakness_candidate_refs`：只能引用 `P-JOBMATCH-004` 的候选结果；如果 `P-JOBMATCH-004` 未触发，可以为空数组。
  - `aggregate_result_refs`
- Validation Rules:
  - 必须引用 `P-SHARED-003`，并把结构化校验和业务语义校验结果写入 validation trace。
  - 检查 `JobVersion`、`ResumeVersion` 和 `JobResumeBinding` 的 owner 一致。
  - 检查输出引用生成时版本或快照，不得隐式绑定到当前最新对象。
  - 检查所有关键结论绑定 `EvidenceRef` 或明确标记证据不足。
  - 检查不能承诺精确通过概率，不能输出确定的真实面试结果预测。
  - 检查不能把匹配分析直接写成最终面试结果预测。
  - 检查不能把候选薄弱项静默写入正式薄弱项。
- Low Confidence Rules:
  - 简历过短。
  - 岗位职责或岗位要求缺失。
  - 绑定关系不可用。
  - 关键简历模块缺失。
  - 证据冲突。
  - 检索结果为空但本 contract 需要增强输入。
  - 上下文被高风险裁剪。
  - 输出无法解释主要分数或主要结论。
  - 低置信度分类必须交给 `P-SHARED-004` 消费 validation、retrieval、context 和 evidence failure signals，不在本 contract 重复定义公共分类枚举。
- Evidence Requirements: 分析摘要、主要匹配 / 不匹配 / 加强结论、匹配分引用和薄弱项候选引用必须绑定 `EvidenceRef`、`SourceRef`、`VersionRef` / `SnapshotRef`；证据不足时必须输出 `evidence_missing` 或等价低置信度标记。
- Trace Requirements: 必须记录 `TraceRef`，覆盖 Retrieval Planning、Input Evidence Selection、Context Assembly、生成、Output Evidence Binding、Output Validation、Low Confidence Classification、Persistence handoff 和 AuditEvent。
- Persistence Targets:
  - `JobMatchAnalysis` aggregate / result envelope。
  - `match_score_ref`、`match_points_ref`、`mismatch_points_ref`、`improvement_points_ref` 和 `weakness_candidate_refs` 等子结果引用。
  - `LlmValidationResult`
  - `LowConfidenceFlag`
  - `TraceRef`
  - `AuditEvent`
  - 不直接持久化薄弱项候选详情，不创建正式 `Weakness`；候选详情由 `P-JOBMATCH-004` 负责。
- User Confirmation Requirement:
  - 匹配分析结果可以作为分析结果保存。
  - 薄弱项候选、资产候选或训练建议不得绕过用户确认直接写入正式对象。
  - 如果产品后续定义自动创建候选薄弱项，也必须保留待确认状态和证据引用。
- Retry / Fallback:
  - owner mismatch、绑定关系不可用或必需版本缺失时停止正常生成，返回失败或补充材料路径。
  - 证据不足、检索为空或上下文高风险裁剪时可保存低置信度 / 部分可用结果，或要求用户补充岗位、简历或模块信息。
  - 重试不得扩大输入范围、启用默认互联网检索或记录原始 Prompt / completion。
- API State Mapping: 只定义状态语义，包括 `not_generated`、`generating`、`generated`、`failed`、`low_confidence`、`partial`、`insufficient_input`、`owner_mismatch` 和 `source_unavailable`；不定义 endpoint 或 request / response schema。
- Security Notes: 所有输入必须通过 owner / scope 校验和最小必要裁剪；前端只可见结构化分析、风险状态、可展示证据摘要和必要 trace id，不暴露原始 Prompt、completion、provider payload 或无权限来源正文。
- Test Strategy: 使用确定性 fixture 覆盖正常匹配分析、owner mismatch、岗位缺失、简历过短、绑定关系不可用、证据冲突、检索为空、上下文高风险裁剪、候选薄弱项不转正式对象和不可承诺精确通过概率。
- Open Questions: 隐藏评分公式实现细节、复杂阈值、真实结果校准、薄弱项合并规则、上下文预算数值和 API 具体状态字段仍为后续设计问题，为 deferred_non_blocking；通过倾向展示边界已收敛为分档表达和低置信度降级，不再作为本 contract 的开放问题。

### 11.2 `P-JOBMATCH-002` Match Score

- Contract ID: `P-JOBMATCH-002`
- Name: Match Score
- Mode: `job_match`
- Trigger:
  - `P-JOBMATCH-001` 需要生成或刷新匹配分。
  - 用户重新生成匹配分析。
  - 后续报告或训练建议需要读取已有匹配分时，不重新生成，只引用已保存结果。
- Goal: 定义岗位匹配 0-100 产品评分刻度与解释的输出 contract；冻结 `AR-F4-FULL-003` 所需的 rubric / rule version、版本追踪、证据、低置信度、禁止精确概率和降级边界。该分数不是精确通过概率，也不是真实面试结果预测。
- Required Inputs:
  - `JobVersion`
  - `ResumeVersion`
  - `JobResumeBinding`
  - `EvidenceRef`
  - `ScoreRuleVersion`
  - `rubric_version`
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - `MatchPoint`
  - `MismatchPoint`
  - `ImprovementPoint`
  - 历史匹配分析
  - 公共评分口径
  - 用户已确认资产
  - 薄弱项证据
- Retrieval Sources:
  - 默认使用 `JobVersion`、`ResumeVersion`、`JobResumeBinding` 和已选择 evidence refs。
  - 条件读取 match / mismatch / improvement points、历史匹配分析、公共评分口径、用户已确认资产和薄弱项证据。
  - 条件读取必须经过 `P-SHARED-002`；如果没有条件检索结果，不阻断基础评分。
  - 基础评分仍可仅基于 `JobVersion`、`ResumeVersion`、`JobResumeBinding` 和已选 evidence 运行，并把检索为空或未使用增强证据传递给低置信度分类。
  - 知识库 / RAG 只作为证据增强或公共评分口径来源，不替代核心岗位与简历输入。
  - 互联网检索不作为默认评分输入。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的上下文分区、裁剪和 trace 规则。
  - 上下文至少包含岗位要求摘要、简历证据摘要、绑定关系、评分目标、评分规则版本、rubric version、正负证据和输出 schema。
  - 上下文过长时，优先保留评分所需证据、岗位关键要求、简历对应片段、评分规则引用和 validation 要求。
- Excluded Inputs:
  - LLM 单次输出临时发明的评分公式、权重、阈值或校准方法。
  - 精确通过概率、录取概率、offer 概率、通过率百分比或等价措辞。
  - 隐藏评分规则、完整内部权重表、校准样例正文、系统 Prompt 或内部校准细节。
  - 与评分无关的完整历史会话、全部资产、全部复盘、原始 Prompt、completion、provider payload、密钥、token 和日志正文。
  - source unavailable 正文、无 evidence ref 的材料和无 owner 校验数据。
- Output Schema:
  - 公共字段：必须完整包含 §11.0 的 Job Match 公共字段。
  - `score_result_ref`
  - `match_score_view_ref`
  - `score_value`
  - `score_scale`
  - `score_version`
  - `rubric_version`
  - `score_type`
  - `score_explanation`
  - `dimension_scores`
  - `confidence_level`
  - `validation_status`
  - `generated_by_task_id`
  - `generated_at`
  - `positive_evidence_refs`
  - `negative_evidence_refs`
  - `uncertainty_reasons`
  - `score_rule_version_ref`
  - `non_decision_disclaimer`
- Validation Rules:
  - `score_value` 必须在 0-100 范围内。
  - `score_scale` 必须表明是 `0_100_product_scale` 产品展示刻度，不是精确通过概率。
  - `score_version`、`rubric_version`、`score_rule_version_ref`、`confidence_level`、`validation_status`、`generated_by_task_id`、`evidence_refs` 和 `trace_refs` 必须存在。
  - `dimension_scores` 必须使用 `ScoreRuleVersion` 中已登记的维度，Job Match 默认维度为 `requirement_alignment`、`experience_evidence`、`skill_coverage`、`gap_risk`、`readiness_actions`。
  - 不得输出精确通过概率。
  - 不得输出录取概率、offer 概率、通过率百分比或“你有 73% 概率通过”等等价措辞。
  - 不得输出“必过”“必挂”等确定预测。
  - 分数解释必须引用 evidence refs。
  - 低分和高分都必须有解释。
  - 缺少足够证据时必须触发 low confidence。
  - 评分规则版本缺失、证据缺失、source unavailable 或 validation failed 时，不得落正式 `ScoreResult`，也不得给出确定性通过倾向。
  - 不得暴露隐藏评分规则、完整内部权重表或校准样例正文。
- Low Confidence Rules:
  - 评分证据不足。
  - 分数与解释不一致。
  - 岗位要求缺失。
  - 简历证据缺失。
  - 评分规则版本或 rubric version 缺失。
  - 上下文裁剪影响评分依据。
  - 模型输出只有分数没有解释。
  - 解释无法绑定证据。
- Evidence Requirements: `score_explanation`、正向证据、负向证据、维度分、不确定性原因、规则版本和免责声明必须绑定 `EvidenceRef`、`ScoreRuleVersion` 或 `TraceRef`；证据不足时必须降级为 low confidence 或 manual review。
- Trace Requirements: 必须记录评分生成、评分规则引用、证据绑定、validation、low confidence 和重试 / 降级路径的 `TraceRef`。
- `canonical` score 关系:
  - `ScoreResult` 是统一评分承载对象，保存 score value、score type、explanation、rule version、evidence refs、validation result 和 trace refs。
  - `MatchScore` 是岗位匹配场景下的视图、引用或领域包装，用于从 `JobMatchAnalysis` 指向对应 `ScoreResult`。
  - 不允许 `ScoreResult` 与 `MatchScore` 分别保存两份不一致的分数、解释或证据。
  - 历史回看、校准和报告复用应引用 canonical score。
  - 如果后续 `DATA_MODEL.md` 需要同步命名，应另开数据模型修正任务；本任务不修改 `DATA_MODEL.md`。
- Persistence Targets:
  - `ScoreResult` canonical score。
  - `MatchScore` view / reference wrapper。
  - `ScoreExplanation`
  - `ScoreEvidenceLink`
  - `LowConfidenceFlag`
  - `LlmValidationResult`
  - `TraceRef`
- User Confirmation Requirement: 匹配分作为分析结果保存不要求用户逐项确认；若后续根据分数生成正式薄弱项、资产或训练建议，仍必须经过对应 contract 或用户确认。
- Retry / Fallback:
  - 分数越界、缺少解释或缺 evidence refs 时进入 repair / retry / validation failed。
  - 证据不足、source unavailable、评分规则版本缺失或 validation failed 时可保存低置信度候选或仅保存分析摘要，不得伪造公式、不得落正式报告评分、不得输出确定倾向。
  - 后续消费已有匹配分时只引用保存结果，不因报告或训练建议读取而自动重算。
- API State Mapping: 只定义状态语义，包括 `score_available`、`score_low_confidence`、`score_partial`、`score_validation_failed`、`score_rule_unknown`、`score_out_of_range` 和 `evidence_missing`；不定义 endpoint 或 schema。
- Security Notes: 评分上下文只能包含当前 owner 的必要岗位、简历、证据和已授权公共材料；日志不得记录原始 Prompt、completion、provider payload、隐藏评分规则、内部校准细节或隐私正文。
- Test Strategy: 使用确定性输出 fixture 覆盖 0、100、中间分、分数越界、只有分数无解释、解释无证据、评分规则版本缺失、证据不足、source unavailable、validation failed 不落正式评分、高分 / 低分均有解释、不得输出精确通过概率和不得暴露隐藏评分规则。
- Open Questions:
  - 隐藏评分规则的实现细节、真实招聘结果校准、版本发布审批和复杂调参流程仍由后续 API / F5 / F7 收敛；本 contract 已冻结 MVP 可展示分、rubric / rule version、低置信度和禁止概率边界。

### 11.3 `P-JOBMATCH-003` Match / Mismatch / Improvement Points

- Contract ID: `P-JOBMATCH-003`
- Name: Match / Mismatch / Improvement Points
- Mode: `job_match`
- Trigger:
  - `P-JOBMATCH-001` 生成岗位匹配分析时触发。
  - `P-JOBMATCH-002` 评分后需要解释分数构成时触发。
  - 用户重新生成匹配分析时触发。
- Goal: 生成匹配点、不匹配点和加强点，作为匹配分析、后续模拟面试输入、复盘、薄弱项候选和训练建议的结构化上游。
- Required Inputs:
  - `JobVersion`
  - `ResumeVersion`
  - `ResumeModule`
  - `JobResumeBinding`
  - `EvidenceRef`
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - 历史匹配分析。
  - 已确认资产。
  - 已有薄弱项。
  - 历史报告或复盘摘要。
  - 公共参考材料或知识库 evidence。
- Retrieval Sources:
  - 默认使用 `JobVersion`、`ResumeVersion`、`ResumeModule`、`JobResumeBinding` 和 selected evidence refs。
  - 条件检索历史匹配分析、已确认资产、已有薄弱项、历史报告、复盘摘要、公共参考材料或知识库 evidence。
  - 简历和岗位版本是核心输入，不作为 RAG；RAG 仅作为证据增强。
  - 互联网检索不默认启用。
- Context Assembly:
  - 必须继承 `P-SHARED-001`，并使用 `P-SHARED-002` 的检索计划和 `P-SHARED-005` 的 input evidence selection 结果。
  - 上下文至少包含岗位要求、相关简历模块、证据摘要、当前分类目标和输出 schema。
  - 不得默认塞入全部简历、全部岗位、全部资产或全部历史复盘。
  - 上下文过长时，优先保留岗位要求、相关简历模块、可绑定证据、分类规则和输出 schema。
- Excluded Inputs:
  - 无 evidence ref 的泛化判断、owner 不一致来源、source unavailable 正文、未确认候选对象作为事实。
  - 完整无关历史、原始 Prompt、completion、provider payload、密钥、token、cookie、日志正文和原始 embedding 向量。
- Output Schema:
  - 公共字段：必须完整包含 §11.0 的 Job Match 公共字段。
  - `match_points`
  - `mismatch_points`
  - `improvement_points`
  - `point_ordering`
  - `max_points_hint`
  - 每个 point 的 `point_id_candidate`
  - 每个 point 的 `point_type`
  - 每个 point 的 `title`
  - 每个 point 的 `description`
  - 每个 point 的 `impact`
  - 每个 point 的 `priority`
  - 每个 point 的 `confidence`
  - 每个 point 的 `related_resume_modules`
  - 每个 point 的 `related_job_requirements`
  - 每个 point 的 `evidence_refs`
  - 每个 point 的 `source_refs`
  - 每个 point 的 `suggested_next_action`
  - `point_type` 只能是 `match` / `mismatch` / `improvement`。
  - `impact` 和 `priority` 建议使用 `high` / `medium` / `low` 或等价枚举。
  - `max_points_hint` 是 MVP 展示和成本控制提示，不冻结最终算法；默认建议每类 point 不超过 3-5 条，除非后续产品设计另行明确。
- Point 分类规则:
  - `MatchPoint` 表示简历证据与岗位要求有正向对应。
  - `MismatchPoint` 表示岗位要求中缺少简历证据、证据弱或表达不充分。
  - `ImprovementPoint` 表示可以通过打磨、资产补充、训练或复盘改进的准备方向。
  - 不得把同一证据同时无解释地归入匹配点和不匹配点。
  - 无证据内容不得伪装成匹配点。
- Validation Rules:
  - 每个 point 必须绑定 evidence refs，除非显式标记证据不足。
  - 每个 point 必须关联岗位要求或简历模块。
  - `MismatchPoint` 不得直接等同于失败结论。
  - `ImprovementPoint` 不得直接写入正式训练建议，后续仍需训练建议 contract 或用户确认。
  - 点位数量不得无边界扩张；`max_points_hint` 默认用于 MVP 展示和成本控制，不能被解释为最终评分算法或硬性产品上限。
  - 输出不得绕过 `P-SHARED-005` Evidence Binding。
- Low Confidence Rules:
  - point 缺少证据。
  - 简历模块识别不完整。
  - 岗位要求过短或模糊。
  - 同一证据存在冲突解释。
  - 生成结果无法区分 match / mismatch / improvement。
  - 输出过泛、无法绑定具体岗位或简历片段。
- Evidence Requirements: 每个 point 必须绑定 `EvidenceRef`、相关 `ResumeModule` 或岗位要求引用；证据不足时必须显式输出 `evidence_missing`、`low_confidence_flags` 和受影响 point。
- Trace Requirements: 必须记录分类输入、证据绑定、冲突证据、上下文裁剪、validation 和 low confidence 的 `TraceRef`。
- Persistence Targets:
  - `MatchPoint`
  - `MismatchPoint`
  - `ImprovementPoint`
  - `EvidenceSummary`
  - `ScoreEvidenceLink`
  - `LowConfidenceFlag`
  - `TraceRef`
- User Confirmation Requirement: 保存 points 作为匹配分析结果不要求用户逐项确认；由 points 派生正式薄弱项、资产或训练建议时必须进入对应候选 / 确认链路。
- Retry / Fallback:
  - 无法区分分类、字段缺失或 evidence binding 失败时进入 repair / retry / validation failed。
  - 证据不足时可保留候选 point 和低置信度，不得伪装成高置信匹配点。
  - 上下文过长时先裁剪无关历史和低相关证据，再保留 omitted refs。
- API State Mapping: 只定义状态语义，包括 `points_available`、`points_partial`、`points_low_confidence`、`points_validation_failed`、`evidence_missing` 和 `classification_ambiguous`；不定义 endpoint 或 schema。
- Security Notes: 输出只展示可展示证据摘要和必要引用；不得暴露无权限来源、source unavailable 正文、原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖三类 point、同一证据冲突分类、无证据匹配点、岗位要求模糊、简历模块缺失、数量无边界扩张、improvement 不转正式训练建议和 mismatch 不等同失败结论。
- Open Questions: 最终点位排序策略、产品化硬上限、训练建议映射和点位合并规则仍待后续业务 contract / API / UX 收敛，为 deferred_non_blocking。

### 11.4 `P-JOBMATCH-004` Weakness Candidate from Job Match

- Contract ID: `P-JOBMATCH-004`
- Name: Weakness Candidate from Job Match
- Mode: `job_match`
- Trigger:
  - `P-JOBMATCH-001` 完成后触发。
  - `P-JOBMATCH-003` 生成 mismatch / improvement points 后触发。
  - 用户选择从岗位匹配分析生成薄弱项候选时触发。
- Goal: 从岗位匹配分析、mismatch / improvement points、低分解释或证据不足中提炼薄弱项候选；本 contract 只生成候选，不直接写入正式 `Weakness`，后续进入正式薄弱项生命周期必须经过用户确认流。
- Required Inputs:
  - `JobMatchAnalysis`
  - `MismatchPoint`
  - `ImprovementPoint`
  - `MatchScore` / `score_result_ref` 条件输入；不可用时允许 `score_dependency_status = score_unavailable`
  - `EvidenceRef`
  - `JobVersion`
  - `ResumeVersion`
  - `P-SHARED-001` Context Assembly 结果
  - `P-SHARED-002` Retrieval Planning 结果，或 `retrieval_plan.status = retrieval_not_required`
  - `P-SHARED-003` Output Validation 要求
  - `P-SHARED-004` Low Confidence Classification 要求
  - `P-SHARED-005` Evidence Binding 要求
- Optional Inputs:
  - 既有 `Weakness`
  - 历史薄弱项状态
  - 历史训练建议
  - 历史报告和复盘
  - 用户已确认资产
  - session summary
- Retrieval Sources:
  - 默认使用当前 `JobMatchAnalysis`、`MismatchPoint`、`ImprovementPoint`、可用的 `MatchScore` / `score_result_ref` 和 evidence refs。
  - 如果只消费 `P-JOBMATCH-001` / `P-JOBMATCH-003` 上游结果且不读取既有 `Weakness`、历史训练建议、历史报告、复盘或 session summary，可使用 `retrieval_not_required`。
  - 如果读取既有 `Weakness`、历史训练建议、历史报告、复盘或 session summary，必须经过 `P-SHARED-002`，并保留 owner / source / evidence 过滤边界与 trace。
  - 条件检索既有 `Weakness`、历史薄弱项状态、历史训练建议、历史报告 / 复盘、用户已确认资产和 session summary。
  - 条件检索必须沿用 `P-SHARED-002` 的来源过滤、排序、裁剪和 source availability 规则。
  - 知识库 / RAG 只作为证据解释补充，不替代岗位匹配分析来源。
  - 互联网检索不默认启用。
- Context Assembly:
  - 必须继承 `P-SHARED-001` 的最小必要上下文、分区、裁剪、omitted refs 和 trace 规则。
  - 使用当前匹配分析结果、mismatch / improvement points、低分解释、证据不足原因，以及经 `P-SHARED-002` 选入的既有薄弱项摘要。
  - 使用 `retrieval_not_required` 时不得读取既有 `Weakness`、历史训练建议、历史报告、复盘或 session summary 的正文或摘要。
  - 不读取无关历史会话全文，不把全部训练建议或全部资产塞入上下文。
  - 上下文过长时，优先保留来源 points、分数解释、证据 refs、既有薄弱项候选合并线索和输出 schema。
- Excluded Inputs:
  - 无来源证据的能力缺陷判断。
  - 未通过 owner 校验的历史弱项、训练建议、报告、复盘或资产。
  - source unavailable 正文、未确认候选对象作为正式事实、原始 Prompt、completion、provider payload、密钥、token、cookie 和日志正文。
- Output Schema:
  - 公共字段：必须完整包含 §11.0 的 Job Match 公共字段。
  - `weakness_candidates`
  - `merge_suggestions`
  - `score_dependency_status`
  - 每个候选的 `candidate_id`
  - 每个候选的 `candidate_status`
  - 每个候选的 `title`
  - 每个候选的 `description`
  - 每个候选的 `source_type`
  - 每个候选的 `source_refs`
  - 每个候选的 `evidence_refs`
  - 每个候选的 `severity_hint`
  - 每个候选的 `suggested_training_direction`
  - 每个候选的 `related_job_requirements`
  - 每个候选的 `related_resume_modules`
  - 每个候选的 `merge_candidate_refs`
  - 每个候选的 `user_confirmation_required`
  - `candidate_status` 建议使用 `weakness_detected` 或等价候选态，不得静默写入正式 `Weakness`。
  - `score_dependency_status` 至少区分 `score_available` / `score_unavailable`；当 score unavailable 时必须触发 low confidence flag。
- Candidate 规则:
  - 薄弱项候选必须来源于 mismatch point、improvement point、低分解释或证据不足。
  - 薄弱项候选必须绑定来源证据。
  - 输出是候选态，不是正式 `Weakness`；用户确认后才可进入正式薄弱项生命周期。
  - 薄弱项候选不得静默覆盖既有薄弱项。
  - 如可能与既有薄弱项重复，应输出 merge suggestion，而不是直接合并或覆盖。
  - 用户可确认、编辑、跳过或合并；确认动作必须形成 `UserConfirmationRef` 或等价记录。
  - `MatchScore` / `score_result_ref` 不可用时，允许以 `score_unavailable` 和低置信度方式基于 mismatch / improvement points 生成候选。
  - `severity_hint` 只是提示，不冻结薄弱项严重度算法。
  - `suggested_training_direction` 只是训练方向，不等同于正式训练任务。
- Validation Rules:
  - 缺少来源证据时不得生成正式候选，只能标记证据不足。
  - 候选必须关联岗位要求或简历模块。
  - 候选必须保留来源类型和来源引用。
  - 不得把岗位不匹配直接包装为用户能力缺陷。
  - 不得生成无法训练、无法行动或过泛的薄弱项。
  - 不得绕过用户确认写入正式 `Weakness`。
- Low Confidence Rules:
  - mismatch / improvement points 本身低置信度。
  - 来源证据不足。
  - 既有薄弱项冲突。
  - `score_unavailable` 但仍基于 mismatch / improvement points 生成候选。
  - 薄弱项粒度过粗或过细。
  - 训练方向无法从证据推出。
  - 用户简历信息不足以判断真实能力。
- Evidence Requirements: 每个候选必须绑定来源 point、低分解释或证据不足记录的 `EvidenceRef`；无法绑定时不得生成高置信候选，更不得写入正式 `Weakness`，只能输出证据不足和 `manual_check_required`。
- Trace Requirements: 必须记录来源匹配分析、来源 point、分数解释、证据绑定、重复候选判断、validation、low confidence、用户确认状态和回流失败的 `TraceRef`。
- Persistence Targets:
  - `Weakness` candidate result，状态为 `weakness_detected` 或等价候选态。
  - `WeaknessEvidence` candidate evidence。
  - `merge_suggestions`，只表达合并建议，不自动覆盖既有 `Weakness`。
  - `UserConfirmationRef` 或等价确认记录。
  - `FeedbackLoop` candidate / confirmation flow。
  - `LowConfidenceFlag`
  - `LlmValidationResult`
  - `TraceRef`
  - `AuditEvent`
  - 正式 `Weakness` 只能在用户确认后由后续确认流写入；候选结果、正式对象、用户确认记录、trace、validation result 和 audit event 不得混写。
- User Confirmation Requirement:
  - 默认需要用户确认后才能成为正式薄弱项。
  - 用户可以确认、编辑、跳过或合并。
  - 用户确认动作必须进入 `UserConfirmationRef` 或等价记录。
  - 回流失败不得影响原始岗位匹配分析结果。
- Retry / Fallback:
  - 来源证据不足、重复关系冲突或粒度不可用时输出低置信度候选、merge suggestion 或 manual check。
  - validation failed 时不得写入正式 `Weakness`，只能保留候选、失败记录或用户校对路径。
  - 回流失败只影响候选确认流程，不得覆盖原始 `JobMatchAnalysis`、points 或 score。
- API State Mapping: 只定义状态语义，包括 `candidate_generated`、`candidate_low_confidence`、`candidate_partial`、`candidate_validation_failed`、`confirmation_required`、`merge_suggested`、`feedback_loop_failed` 和 `formal_weakness_not_written`；不定义 endpoint 或 schema。
- Security Notes: 候选生成只使用当前 owner 的匹配分析、points、分数解释和授权历史摘要；不得把无权限历史弱项或 source unavailable 正文纳入 Prompt；日志不记录原始 Prompt、completion 或 provider payload。
- Test Strategy: 使用 fixture 覆盖从 mismatch、improvement、低分解释和证据不足生成候选、候选缺证据、既有薄弱项冲突、merge suggestion、不把岗位不匹配包装成能力缺陷、粒度过粗 / 过细、用户确认 required 和回流失败不影响原始分析。
- Open Questions: 薄弱项严重度算法、合并规则、自动消减规则、训练任务生成规则、正式 `Weakness` 状态流和用户确认 API 字段仍待后续 Weakness / Training / API contract 收敛，为 deferred_non_blocking。

### 11.5 Job Match Contract 关系

- `P-JOBMATCH-001` 是岗位匹配分析总控 contract。
- `P-JOBMATCH-002` 负责 0-100 匹配分和解释。
- `P-JOBMATCH-003` 负责匹配点、不匹配点和加强点。
- `P-JOBMATCH-004` 负责从分析结果中生成薄弱项候选。
- 4 个 contract 都必须引用 Shared Contracts，且默认按 `P-SHARED-002`、`P-SHARED-005` Input Evidence Selection、`P-SHARED-001`、业务生成、`P-SHARED-005` Output Evidence Binding、`P-SHARED-003`、`P-SHARED-004` 和持久化 / 用户确认链路交接。
- 4 个 contract 的结果都不得承诺精确通过概率或确定预测真实面试结果。
- `P-JOBMATCH-004` 的输出不得绕过用户确认写入正式薄弱项。
