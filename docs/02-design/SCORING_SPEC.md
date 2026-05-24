---
title: SCORING_SPEC
type: design
status: draft-f4-scoring-spec
owner: 技术架构 / AI 架构
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/scoring-spec
---

# SCORING_SPEC

## 1. 文档状态与治理边界

- 本文件是 F4 评分机制 canonical spec，承接人工审计中“评分机制缺少统一规则、算法、维度、权重、输入输出、落库和 API / Prompt 对应”的整改。
- 本文件定义 MVP 评分的产品刻度、score type、输入、输出、默认 rubric、权重、公式、低置信度降级、持久化和 F7 fixture 要求。
- 本文件不定义生产完整 Prompt 文案，不定义物理 DDL / ORM，不选择模型 provider，不暴露系统 Prompt、provider payload、completion 原文、密钥或隐藏校准样例正文。
- 本文件不把复杂算法、真实招聘结果校准、精确通过概率或通过率预测写成 MVP 必需能力。

## 2. 输入来源与非目标

| 来源 | 使用方式 |
|---|---|
| `TECH_DESIGN.md` | 评分、通过倾向、风险提示和 AI 编排的顶层边界 |
| `DATA_MODEL.md` | `ScoreResult`、`ScoreRuleVersion`、`ScoreDimension`、`ScoreEvidenceLink`、`LowConfidenceFlag`、`EvidenceRef`、`TraceRef` 的逻辑对象 |
| `API_SPEC.md` | 评分 task、评分结果读取、response envelope、错误和 F7 assertion |
| `PROMPT_SPEC.md` / `prompt-contracts/*.md` | scoring candidate、Output Validation、Low Confidence、Evidence Binding 和 P-* contract 映射 |
| `SECURITY_PRIVACY.md` | 隐藏评分规则、LLM payload、copy content 和日志脱敏边界 |

非目标：

- 不输出 `pass_probability`、`offer_probability`、`admission_probability`、`pass_rate_percent` 或等价字段。
- 不输出“你有 73% 概率通过”“必过”“必挂”等精确或确定性预测。
- 不把分数用于自动录用、自动拒绝、自动创建正式弱项、自动创建训练任务或自动发布资产。
- 不要求 MVP 使用真实招聘结果训练或校准评分模型。
- 不要求 F5 暴露完整内部权重表、隐藏评分规则或校准样例正文给 API、前端、copy content 或日志。

## 3. 统一评分原则

1. `score_value` 是 0-100 产品评分刻度，不是通过概率、录取概率、offer 概率或真实面试结果预测。
2. `ScoreRuleVersion` 是评分来源。LLM 可以产出 scoring candidate，但正式 `ScoreResult` 必须经过 schema validation、业务语义校验、evidence binding、low confidence classification 和 persistence handoff。
3. 每个 score type 必须绑定固定 rubric dimensions；默认权重总和必须为 100，LLM 不得在单次输出中临时发明权重。
4. 公式统一为：

```text
score_value = round(sum(dimension_score_i * weight_i) / 100)
```

5. 每个 `dimension_score_i` 必须先 clamp 到 0..100；最终 `score_value` 也必须 clamp 到 0..100。
6. 缺失维度不得按 0 静默吞掉。缺失非关键维度时，允许按已知维度重新归一化生成 candidate，并标记 `validation_status=valid_with_warnings` 与 `confidence_level=low`；缺失关键维度时必须进入 `manual_review_required` 或 `invalid`，不得落正式 `ScoreResult`。
7. 分数、解释、风险提示和通过倾向必须绑定 `EvidenceRef`、`TraceRef`、`ScoreRuleVersion` 和 `LowConfidenceFlag`。
8. 历史评分不随后续简历、岗位、会话、知识库或规则版本变化而改写；重新评分必须生成新的 `ScoreResult` 或新版本结果。

## 4. Canonical score type

| score_type | 场景 | 与现有命名关系 | 是否 MVP formal `ScoreResult` |
|---|---|---|---|
| `job_match` | 岗位-简历匹配分析 | 对应 `P-JOBMATCH-002 Match Score` 和 `JobMatchSummary.display_score` | 是 |
| `polish_answer` | 打磨模式用户每次回答评分 | 取代旧口语 `polish_round`；若旧 API fixture 出现 `polish_round`，F5 应映射为 `polish_answer` | 是，前提是 validation 通过 |
| `polish_report` | 打磨模式报告总评分 | 不是单轮回答分；汇总一组 Polish turns / feedback / scores / loss points / improvements | 是 |
| `pressure_session` | 压力面整场评分 | 保留现有 `P-PRESSURE-008 Session Score` 语义 | 是 |
| `report_section` | 报告分项评分解释 | 保留现有 `P-REPORT-002 Section Score Explanation` 语义 | 是，作为 report section score |

## 5. 通用输出对象

正式评分输出必须至少包含：

| 字段 | 必填 | 说明 |
|---|---|---|
| `score_result_id` | 是 | `ScoreResult` ID |
| `score_type` | 是 | 使用 §4 canonical score type |
| `target_ref` | 是 | 被评分目标的 typed ref |
| `score_value` | 是 | 0..100 integer |
| `score_scale` | 是 | 固定 `0_100_product_scale` |
| `score_rule_version_ref` | 是 | 指向 `ScoreRuleVersion` |
| `score_version` | 是 | 评分结果版本 |
| `rubric_version` | 是 | rubric 版本 |
| `dimension_scores[]` | 是 | 每个维度分、权重、证据和解释 |
| `validation_status` | 是 | `valid` / `valid_with_warnings` / `invalid` / `manual_review_required` |
| `confidence_level` | 是 | `high` / `medium` / `low` / `insufficient` |
| `low_confidence_flags[]` | 是 | 低置信度原因；无则空数组 |
| `evidence_refs[]` | 是 | `>=1`，除非 `confidence_level=insufficient` |
| `trace_refs[]` | 是 | context、LLM、validation、persistence 和 audit trace |
| `generated_by_task_id` | 是 | `AiTask` ID |
| `generated_at` | 是 | 生成时间 |
| `allowed_as_formal_score` | 是 | 是否允许进入正式 `ScoreResult` |

`allowed_as_formal_score=false` 时，API 只能返回 candidate / validation / manual review 状态，不得把该分数展示为正式评分或写入报告正式评分字段。

## 6. Score type 规则

### 6.1 `job_match`

| 项 | 规则 |
|---|---|
| 使用场景 | 岗位-简历匹配分析、岗位列表 / 详情摘要、进入打磨或压力面前的准备度参考 |
| 输入对象 | `JobResumeBinding`、`JobVersion`、`ResumeVersion`、`JobMatchAnalysis` candidate、`MatchPoint`、`MismatchPoint`、`ImprovementPoint`、必要 `EvidenceRef` |
| 输出对象 | `ScoreResult`、`JobMatchSummary.display_score`、`ScoreEvidenceLink`、`LowConfidenceFlag` |
| ScoreRuleVersion | `score_rule_version_ref` 必填；默认 `job_match.v1` |
| Prompt mapping | `P-JOBMATCH-002 Match Score`；共享 `P-SHARED-003/004/005` |
| API mapping | `POST /api/v1/job-match-analyses`、`GET /api/v1/job-match-analyses/{analysis_id}`、`GET /api/v1/scoring-results/{score_result_id}` |
| F7 fixture | `score.job_match.dimension_weights_total_100`、`score.job_match.no_exact_probability`、`score.job_match.low_confidence_evidence_missing`、`score.job_match.source_unavailable_blocks_formal` |

默认维度：

| 维度 | 权重 | 分范围 | 说明 |
|---|---:|---|---|
| `requirement_alignment` | 30 | 0..100 | 岗位关键要求与简历证据的直接匹配度 |
| `experience_evidence` | 25 | 0..100 | 项目、经历、结果和上下文证据强度 |
| `skill_coverage` | 20 | 0..100 | 技能栈、工具、领域知识覆盖 |
| `gap_risk` | 15 | 0..100 | 缺口风险的反向评分；风险越低分越高 |
| `readiness_actions` | 10 | 0..100 | 下一步准备动作是否清晰、可执行 |

### 6.2 `polish_answer`

| 项 | 规则 |
|---|---|
| 使用场景 | 用户每次提交打磨回答后的本轮回答评分 |
| 输入对象 | `InterviewSession`、`PolishSessionDetail`、当前 `Question`、当前 `Answer`、`Feedback` / diagnosis candidate、`ResumeVersion`、`JobVersion`、`SessionSummary`、必要 `EvidenceRef` |
| 输出对象 | `ScoreResult`、`Feedback.score_ref`、`ScoreEvidenceLink`、`LossPoint` candidate、`LowConfidenceFlag` |
| ScoreRuleVersion | `score_rule_version_ref` 必填；默认 `polish_answer.v1` |
| Prompt mapping | `P-POLISH-004 Round Score`；可与 `P-POLISH-003/005/009` 在一次 feedback LLM call 中生成候选输出 |
| API mapping | `POST /api/v1/polish-sessions/{session_id}/answers` 只保存回答；`POST /api/v1/polish-sessions/{session_id}/feedback` 创建异步 feedback / scoring task |
| F7 fixture | `score.polish_answer.answer_save_no_llm`、`score.polish_answer.feedback_task_scores_current_answer`、`score.polish_answer.no_job_match_score_reuse`、`score.polish_answer.low_confidence_visible` |

默认维度：

| 维度 | 权重 | 分范围 | 说明 |
|---|---:|---|---|
| `answer_relevance` | 25 | 0..100 | 是否回应当前题目和岗位要求 |
| `technical_depth` | 25 | 0..100 | 技术解释深度和关键原理覆盖 |
| `communication_structure` | 20 | 0..100 | 结构、层次、表达清晰度 |
| `evidence_specificity` | 20 | 0..100 | 是否有具体项目、指标、约束和结果证据 |
| `risk_control` | 10 | 0..100 | 是否避免虚构、跑题、过度承诺和安全风险 |

### 6.3 `polish_report`

`polish_report` 是对一组 Polish turns / feedback / scores / loss points / improvements 的汇总评分，不得直接复用某一轮 `polish_answer` 分数，也不得把最高分、最近一轮分或简单平均分当作总评分。

| 项 | 规则 |
|---|---|
| 使用场景 | 打磨模式阶段报告、阶段性准备度总结、后续复盘输入 |
| 输入对象 | `InterviewSession`、`PolishSessionDetail`、`Question`、`Answer`、`Feedback`、`ScoreResult`、`LossPoint`、`SessionSummary`、必要 `EvidenceRef` |
| 输出对象 | `ScoreResult(score_type=polish_report)`、`InterviewReport` / `ReportSection` 的 `score_ref`、`ScoreEvidenceLink`、`LowConfidenceFlag` |
| ScoreRuleVersion | `score_rule_version_ref` 必填；默认 `polish_report.v1` |
| Prompt mapping | `P-REPORT-001 Interview Report Generation`、`P-REPORT-002 Section Score Explanation`、共享 `P-SHARED-003/004/005` |
| API mapping | `POST /api/v1/reports` with `report_type=polish_summary`、`GET /api/v1/reports/{report_id}`、`GET /api/v1/scoring-results/{score_result_id}` |
| F7 fixture | `score.polish_report.not_single_turn_reuse`、`score.polish_report.input_turn_refs_required`、`score.polish_report.no_precise_pass_probability`、`score.polish_report.low_confidence_no_deterministic_tendency` |

默认维度：

| 维度 | 权重 | 分范围 | 说明 |
|---|---:|---|---|
| `overall_readiness` | 25 | 0..100 | 当前材料和回答的整体准备度 |
| `weakness_resolution` | 20 | 0..100 | 已暴露薄弱点是否被改善或形成行动 |
| `answer_iteration_quality` | 20 | 0..100 | 多轮回答质量是否稳定提升 |
| `evidence_reuse_quality` | 20 | 0..100 | 是否能复用已确认资产、项目证据和反馈 |
| `next_action_clarity` | 15 | 0..100 | 后续动作是否清晰、可执行、可验证 |

汇总公式仍使用统一公式，但每个维度的 `dimension_score` 必须基于 turn refs、feedback refs、loss point refs 和 improvement refs 计算；不得直接复制单轮分。

low confidence 时：

- 不得给出确定性通过倾向。
- 不得输出“必过 / 必挂”。
- 若关键 turn refs、feedback refs 或 evidence refs 缺失，`allowed_as_formal_score=false`。

### 6.4 `pressure_session`

| 项 | 规则 |
|---|---|
| 使用场景 | 压力面整场表现评分、报告输入包、后续复盘输入 |
| 输入对象 | `InterviewSession`、`PressureSessionDetail`、Pressure turns、`Answer`、`Feedback` / Answer Quality results、`SessionSummary`、`JobVersion`、`ResumeVersion`、必要 `EvidenceRef` |
| 输出对象 | `ScoreResult`、`InterviewReport.score_ref`、`ScoreEvidenceLink`、`LowConfidenceFlag` |
| ScoreRuleVersion | `score_rule_version_ref` 必填；默认 `pressure_session.v1` |
| Prompt mapping | `P-PRESSURE-008 Session Score`、`P-PRESSURE-009 Report Input Assembly`、共享 `P-SHARED-003/004/005` |
| API mapping | `POST /api/v1/scoring-results`、`POST /api/v1/reports`、`GET /api/v1/scoring-results/{score_result_id}` |
| F7 fixture | `score.pressure_session.turn_refs_required`、`score.pressure_session.no_polish_score_reuse`、`score.pressure_session.low_confidence_for_truncated_context` |

默认维度：

| 维度 | 权重 | 分范围 | 说明 |
|---|---:|---|---|
| `answer_quality` | 30 | 0..100 | 回答质量和关键追问响应 |
| `follow_up_resilience` | 20 | 0..100 | 连续追问下的稳定性和应变 |
| `breadth_coverage` | 20 | 0..100 | 覆盖岗位核心能力面 |
| `risk_control` | 15 | 0..100 | 不确定、矛盾、虚构和安全风险控制 |
| `communication_structure` | 15 | 0..100 | 压力情境下表达结构和清晰度 |

### 6.5 `report_section`

| 项 | 规则 |
|---|---|
| 使用场景 | 报告中分项评分解释和分项风险摘要 |
| 输入对象 | `InterviewReport`、`ReportSection`、`ScoreResult`、dimension scores、answer quality refs、risk signal refs、必要 `EvidenceRef` |
| 输出对象 | `ScoreResult(score_type=report_section)` 或 report section score、`ScoreExplanation`、`ScoreEvidenceLink` |
| ScoreRuleVersion | `score_rule_version_ref` 必填；默认 `report_section.v1` |
| Prompt mapping | `P-REPORT-002 Section Score Explanation`、`P-REPORT-003 Risk and Pass Tendency Wording` |
| API mapping | `GET /api/v1/reports/{report_id}` 返回 `data.sections[]` 和 `score_ref`；不得新增未登记 sections endpoint |
| F7 fixture | `score.report_section.score_refs_present`、`score.report_section.validation_failed_not_formal`、`score.report_section.copy_no_hidden_rules` |

默认维度：

| 维度 | 权重 | 分范围 | 说明 |
|---|---:|---|---|
| `section_relevance` | 25 | 0..100 | 分项是否对应报告目标 |
| `evidence_binding` | 25 | 0..100 | 分项证据是否充分、可追溯 |
| `score_explanation_quality` | 20 | 0..100 | 分数解释是否清晰、可验证 |
| `risk_wording_safety` | 15 | 0..100 | 风险表述是否安全、非确定性、非歧视 |
| `actionability` | 15 | 0..100 | 改进动作是否具体可执行 |

## 7. 低置信度与正式落库规则

| 条件 | validation_status | confidence_level | 是否允许 formal `ScoreResult` | API / UI 行为 |
|---|---|---|---|---|
| schema 和语义均通过，证据充分 | `valid` | `high` / `medium` | 是 | 正常展示评分、证据和免责声明 |
| 非关键维度缺失或证据偏弱 | `valid_with_warnings` | `low` | 条件允许 | 展示低置信提示、`low_confidence_flags` 和 `next_actions` |
| 关键维度、规则版本或 evidence 缺失 | `manual_review_required` | `insufficient` | 否 | 返回 manual review / 补充材料 / retry |
| schema invalid、分数越界、来源不可用正文被引用 | `invalid` | `insufficient` | 否 | `validation_failed` 或 `source_unavailable`，不展示正式分 |
| 分数解释与证据冲突 | `manual_review_required` | `low` / `insufficient` | 否 | 进入人工校对或重新生成 |

低置信度不得被 `status=success` 吞掉。API 必须返回 `status=low_confidence` / `partial` / `validation_failed` 或在 success envelope 中显式返回 `low_confidence_flags[]`、`confidence_level`、`validation_status` 和 `next_actions[]`。

## 8. 对象关系

| 对象 | 关系 |
|---|---|
| `ScoreRuleVersion` | 记录 score type、rubric version、维度集合、默认权重、启用状态和变更原因 |
| `ScoreDimension` | 属于一个 `ScoreRuleVersion`；包含 `dimension_key`、`weight`、分范围和可展示解释摘要 |
| `ScoreResult` | 指向目标对象、`ScoreRuleVersion`、`generated_by_task_id`、`TraceRef`、`EvidenceRef` 和 `LowConfidenceFlag` |
| `ScoreEvidenceLink` | 连接 `ScoreResult`、dimension、`EvidenceRef` 和 evidence role |
| `LowConfidenceFlag` | 连接 scoring candidate / `ScoreResult`、validation result、source availability 和用户可见影响 |
| `TraceRef` | 指向 context assembly、LLM request、validation、low confidence classification、persistence handoff 和 audit |
| `EvidenceRef` | 指向题目、回答、反馈、RAG evidence、用户确认、生成时版本或快照 |
| `SkillToScoreDimension` | 由 `SKILL_MODEL_SPEC.md` 定义，用于把 stable `Skill` 映射到 score type / dimension key；不改变 `ScoreDimension` 的评分职责，也不允许把 `ScoreDimension` 当作 Skill |

## 9. 版本变更与校准边界

- `ScoreRuleVersion` 发布后不得原地改写语义。维度、权重、公式、低置信处理或 validation 规则变化必须发布新版本。
- 历史 `ScoreResult` 继续引用生成时的 `ScoreRuleVersion`、`score_version` 和 `rubric_version`。
- 重新评分生成新 `ScoreResult`；不得覆盖历史分数。
- MVP 校准只要求固定 rule version、人工验收样例、F7 fixture 和回归样例。不要求真实招聘结果校准。
- 若后续引入真实结果校准，必须另行设计隐私、偏差、样本代表性、用户授权和版本迁移规则。
- 跨模式能力语义以 `SKILL_MODEL_SPEC.md` 为 canonical；评分只能通过 `SkillToScoreDimension` 引用 Skill，不得在 LLM 输出中临时发明 skill key 或把低分维度直接写成正式 `Weakness`。

## 10. F7 fixture 最小要求

F7 至少覆盖：

- 每个 score type 的权重总和为 100。
- 维度分和总分 clamp 到 0..100。
- 缺失关键维度不落 formal `ScoreResult`。
- `validation_failed` 不写正式报告评分。
- `low_confidence` 不被普通 success 吞掉。
- `source_unavailable` 不读取正文，不给确定倾向。
- 不出现 `pass_probability`、`offer_probability`、`admission_probability`、`pass_rate_percent`、“你有 73% 概率通过”、“必过”或“必挂”。
- API 返回 `score_rule_version_ref`、`score_version`、`rubric_version`、`confidence_level`、`validation_status`、`evidence_refs` 和 `trace_refs`。
- copy content 不包含隐藏评分规则、完整内部权重表、校准样例正文、system prompt、provider payload 或 completion 原文。

## 11. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-17 | 初始化评分 canonical spec | 新增 score type、rubric dimensions、权重、公式、低置信度、API / Prompt / persistence 映射和 F7 fixture 要求 |
